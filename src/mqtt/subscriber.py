"""
MQTT Subscriber for Hong Kong Traffic Data.

Subscribes to hk-traffic/# topics, parses incoming JSON messages,
and persists them to the MySQL traffic_readings table.

Adapted from thesis pattern: MqttClientService → parse → save,
rewritten in Python with paho-mqtt 2.x.

Database operations are delegated to src.database (connection + crud).
"""

import json
import logging
import threading
import time
from datetime import datetime

import paho.mqtt.client as mqtt
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class TrafficMqttSubscriber:
    """
    Subscribes to MQTT traffic topics and writes to MySQL.

    Usage
    -----
    >>> sub = TrafficMqttSubscriber(
    ...     broker_host="localhost",
    ...     db_url="mysql+pymysql://traffic_user:Traffic2025!@localhost:3306/hk_traffic",
    ... )
    >>> sub.start()       # connect + subscribe, runs in background
    >>> # ... let it run ...
    >>> sub.stop()        # disconnect + cleanup
    """

    SUBSCRIBE_TOPIC = "hk-traffic/#"

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        client_id: str = "hk-traffic-subscriber",
        qos: int = 1,
        keepalive: int = 60,
        db_url: str = "",
        batch_size: int = 100,
        flush_interval: float = 5.0,
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.qos = qos
        self.keepalive = keepalive
        self.db_url = db_url
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        # MQTT client
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
            clean_session=True,
        )
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)

        # Database (initialized in start())
        self._session_factory = None

        # Message buffer for batch inserts
        self._buffer: list[dict] = []
        self._buffer_lock = threading.Lock()
        self._flush_timer = None

        # Stats
        self._msg_received = 0
        self._msg_saved = 0
        self._msg_errors = 0
        self._connected = False
        self._running = False

    # ------------------------------------------------------------------
    # MQTT Callbacks (paho-mqtt 2.x: 5 parameters)
    # ------------------------------------------------------------------

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self._connected = True
            logger.info(
                "Subscriber connected to %s:%d",
                self.broker_host, self.broker_port,
            )
            # Subscribe (or re-subscribe after reconnect)
            client.subscribe(self.SUBSCRIBE_TOPIC, qos=self.qos)
            logger.info("Subscribed to %s", self.SUBSCRIBE_TOPIC)
        else:
            self._connected = False
            logger.error("Subscriber connect failed: %s", reason_code)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        self._connected = False
        if reason_code == 0:
            logger.info("Subscriber disconnected cleanly")
        else:
            logger.warning("Subscriber disconnected unexpectedly: %s", reason_code)

    def _on_message(self, client, userdata, message):
        """
        Handle incoming MQTT message.

        Topic format: hk-traffic/{source_type}/{detector_id}
        Payload: JSON dict from TrafficReading.to_dict()
        """
        self._msg_received += 1

        try:
            # Parse topic to extract source_type and detector_id
            topic_parts = message.topic.split("/")
            # Expected: ["hk-traffic", source_type, detector_id]
            if len(topic_parts) < 3:
                logger.warning("Unexpected topic format: %s", message.topic)
                self._msg_errors += 1
                return

            source_type = topic_parts[1]
            detector_id_from_topic = topic_parts[2]

            # Parse JSON payload
            payload = json.loads(message.payload.decode("utf-8"))

            # Build a row dict for DB insertion
            row = {
                "detector_id": payload.get("detector_id", detector_id_from_topic),
                "source_type": source_type,
                "timestamp": payload.get("timestamp", ""),
                "lane_id": payload.get("lane_id", ""),
                "speed": payload.get("speed"),
                "volume": payload.get("volume"),
                "occupancy": payload.get("occupancy"),
                "speed_sd": payload.get("speed_sd"),
                "valid": payload.get("valid", "N"),
            }

            # Add to buffer
            should_flush = False
            with self._buffer_lock:
                self._buffer.append(row)
                if len(self._buffer) >= self.batch_size:
                    should_flush = True

            # Flush outside the lock to avoid deadlock
            if should_flush:
                self._flush_buffer()

        except json.JSONDecodeError as e:
            logger.error("JSON decode error on %s: %s", message.topic, e)
            self._msg_errors += 1
        except Exception as e:
            logger.error("Error processing message from %s: %s", message.topic, e)
            self._msg_errors += 1

    # ------------------------------------------------------------------
    # Database operations (using src.database module)
    # ------------------------------------------------------------------

    def _init_db(self):
        """Initialize database connection via centralized connection module."""
        from src.database.connection import get_session_factory
        self._session_factory = get_session_factory(self.db_url)
        logger.info("Database connection initialized via connection module")

    def _flush_buffer(self):
        """
        Batch-insert buffered messages into MySQL.

        Uses crud.bulk_insert_readings for performance.
        Called when buffer reaches batch_size or on timer.
        """
        with self._buffer_lock:
            if not self._buffer:
                return
            batch = self._buffer.copy()
            self._buffer.clear()

        if not self._session_factory:
            logger.error("Database not initialized, dropping %d messages", len(batch))
            self._msg_errors += len(batch)
            return

        try:
            from src.database.crud import bulk_insert_readings
            session = self._session_factory()
            try:
                bulk_insert_readings(session, batch)
                session.commit()
                self._msg_saved += len(batch)
                logger.debug("Flushed %d readings to database", len(batch))
            except SQLAlchemyError as e:
                session.rollback()
                logger.error("DB insert failed (%d rows): %s", len(batch), e)
                self._msg_errors += len(batch)
            finally:
                session.close()
        except Exception as e:
            logger.error("DB session error: %s", e)
            self._msg_errors += len(batch)

    def _start_flush_timer(self):
        """Periodically flush buffer even if batch_size not reached."""
        if not self._running:
            return
        self._flush_buffer()
        self._flush_timer = threading.Timer(
            self.flush_interval, self._start_flush_timer
        )
        self._flush_timer.daemon = True
        self._flush_timer.start()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> bool:
        """
        Connect to MQTT broker and database, start receiving messages.

        Returns True if both connections succeed.
        """
        # Init database
        try:
            self._init_db()
        except Exception as e:
            logger.error("Database init failed: %s", e)
            return False

        # Connect to MQTT
        try:
            self.client.connect(
                self.broker_host,
                self.broker_port,
                keepalive=self.keepalive,
            )
        except Exception as e:
            logger.error("MQTT connect failed: %s", e)
            return False

        self._running = True

        # Start network loop in background thread
        self.client.loop_start()

        # Wait for connection
        for _ in range(10):
            if self._connected:
                break
            time.sleep(0.1)

        if not self._connected:
            logger.error("MQTT connection timed out")
            self.stop()
            return False

        # Start periodic flush timer
        self._start_flush_timer()

        logger.info("Subscriber started successfully")
        return True

    def stop(self):
        """Stop the subscriber, flush remaining data, and disconnect."""
        self._running = False

        # Cancel flush timer
        if self._flush_timer:
            self._flush_timer.cancel()

        # Flush any remaining buffered messages
        self._flush_buffer()

        # Disconnect MQTT
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            logger.error("Error during MQTT disconnect: %s", e)

        # Close database engine
        from src.database.connection import dispose
        dispose()

        logger.info(
            "Subscriber stopped. Stats: received=%d, saved=%d, errors=%d",
            self._msg_received, self._msg_saved, self._msg_errors,
        )

    @property
    def stats(self) -> dict:
        """Return current statistics."""
        return {
            "connected": self._connected,
            "received": self._msg_received,
            "saved": self._msg_saved,
            "errors": self._msg_errors,
            "buffer_size": len(self._buffer),
        }


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    # Default local dev settings (match your .env)
    DB_URL = "mysql+pymysql://traffic_user:Traffic2025!@localhost:3306/hk_traffic?charset=utf8mb4"
    BROKER_HOST = "localhost"
    BROKER_PORT = 1883

    sub = TrafficMqttSubscriber(
        broker_host=BROKER_HOST,
        broker_port=BROKER_PORT,
        db_url=DB_URL,
        batch_size=50,        # flush every 50 messages
        flush_interval=3.0,   # or every 3 seconds
    )

    if not sub.start():
        print("Failed to start subscriber")
        exit(1)

    print("Subscriber running. Waiting for messages...")
    print("(Start the publisher in another terminal to send data)")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(5)
            stats = sub.stats
            print(
                f"  [stats] received={stats['received']} "
                f"saved={stats['saved']} errors={stats['errors']} "
                f"buffer={stats['buffer_size']}"
            )
    except KeyboardInterrupt:
        print("\nStopping subscriber...")

    sub.stop()
    print("Done.")