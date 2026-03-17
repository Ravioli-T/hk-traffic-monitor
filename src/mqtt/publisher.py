"""
MQTT Publisher for Hong Kong Traffic Data.

Receives TrafficReading objects from the XML fetcher and publishes them
as JSON messages to the Mosquitto broker.

Topic structure (adapted from thesis pattern vehicle/{id}/sensor):
    hk-traffic/{source_type}/{detector_id}

    Examples:
        hk-traffic/strategic/AID01101
        hk-traffic/lamppost/AID20051

    Subscribe all: hk-traffic/#
"""

import json
import logging
import time

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class TrafficMqttPublisher:
    """
    Publishes TrafficReading data to MQTT broker.

    Usage
    -----
    >>> pub = TrafficMqttPublisher(broker_host="localhost")
    >>> pub.connect()
    >>> pub.publish_readings(readings)   # list of TrafficReading
    >>> pub.disconnect()
    """

    TOPIC_PREFIX = "hk-traffic"

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        client_id: str = "hk-traffic-publisher",
        qos: int = 1,
        keepalive: int = 60,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.qos = qos
        self.keepalive = keepalive
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # paho-mqtt 2.x requires CallbackAPIVersion
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
            clean_session=True,
        )

        # Register callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish

        # Reconnect settings (paho built-in)
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)

        self._connected = False
        self._publish_count = 0

    # ------------------------------------------------------------------
    # Callbacks (paho-mqtt 2.x signature: 5 parameters)
    # ------------------------------------------------------------------

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self._connected = True
            logger.info(
                "Publisher connected to %s:%d",
                self.broker_host, self.broker_port,
            )
        else:
            self._connected = False
            logger.error("Publisher connect failed: %s", reason_code)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        self._connected = False
        if reason_code == 0:
            logger.info("Publisher disconnected cleanly")
        else:
            logger.warning("Publisher disconnected unexpectedly: %s", reason_code)

    def _on_publish(self, client, userdata, mid, reason_code, properties):
        self._publish_count += 1

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Connect to the MQTT broker with retries."""
        for attempt in range(1, self.max_retries + 1):
            try:
                self.client.connect(
                    self.broker_host,
                    self.broker_port,
                    keepalive=self.keepalive,
                )
                # Start the network loop in a background thread
                self.client.loop_start()

                # Wait briefly for the on_connect callback
                for _ in range(10):
                    if self._connected:
                        return True
                    time.sleep(0.1)

                if self._connected:
                    return True

                logger.warning(
                    "Connect attempt %d/%d: waiting for on_connect timed out",
                    attempt, self.max_retries,
                )
            except Exception as e:
                logger.error(
                    "Connect attempt %d/%d failed: %s",
                    attempt, self.max_retries, e,
                )

            if attempt < self.max_retries:
                time.sleep(self.retry_delay * attempt)

        logger.error("All %d connect attempts failed", self.max_retries)
        return False

    def disconnect(self):
        """Disconnect from the broker and stop the network loop."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            logger.error("Error during disconnect: %s", e)

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def publish_count(self) -> int:
        return self._publish_count

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------

    def _build_topic(self, source_type: str, detector_id: str) -> str:
        """
        Build MQTT topic string.

        Format: hk-traffic/{source_type}/{detector_id}
        Example: hk-traffic/strategic/AID01101

        Note: We dropped {district} from the original design because
        the XML response doesn't include district info. District can be
        looked up from detector_info table when needed.
        """
        return f"{self.TOPIC_PREFIX}/{source_type}/{detector_id}"

    def publish_reading(self, reading) -> bool:
        """
        Publish a single TrafficReading to MQTT.

        Parameters
        ----------
        reading : TrafficReading
            A single lane measurement from the XML fetcher.

        Returns
        -------
        bool
            True if the message was queued successfully.
        """
        if not self._connected:
            logger.warning("Not connected, cannot publish")
            return False

        topic = self._build_topic(reading.source_type, reading.detector_id)
        payload = json.dumps(reading.to_dict(), ensure_ascii=False)

        try:
            result = self.client.publish(topic, payload, qos=self.qos)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.warning(
                    "Publish to %s returned rc=%d", topic, result.rc
                )
                return False
            return True
        except Exception as e:
            logger.error("Publish error on %s: %s", topic, e)
            return False

    def publish_readings(self, readings: list) -> dict:
        """
        Publish a batch of TrafficReading objects.

        Parameters
        ----------
        readings : list[TrafficReading]
            Batch of readings from one fetch cycle.

        Returns
        -------
        dict
            Summary: {"total": N, "published": M, "failed": F}
        """
        published = 0
        failed = 0

        for reading in readings:
            if self.publish_reading(reading):
                published += 1
            else:
                failed += 1

        logger.info(
            "Published %d/%d readings (%d failed)",
            published, len(readings), failed,
        )
        return {
            "total": len(readings),
            "published": published,
            "failed": failed,
        }


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    from src.fetcher.xml_fetcher import TrafficDataFetcher

    # 1. Fetch a batch of real data
    fetcher = TrafficDataFetcher()
    readings = fetcher.fetch_strategic()
    fetcher.close()

    if not readings:
        print("No readings fetched, exiting")
        sys.exit(1)

    print(f"\nFetched {len(readings)} readings, publishing to MQTT...\n")

    # 2. Publish to MQTT
    pub = TrafficMqttPublisher(broker_host="localhost", broker_port=1883)

    if not pub.connect():
        print("Failed to connect to MQTT broker")
        print("Make sure Mosquitto is running: net start mosquitto")
        sys.exit(1)

    result = pub.publish_readings(readings)
    print(f"\nResult: {result}")

    # Wait for all messages to be delivered
    time.sleep(1)
    print(f"Total published (confirmed): {pub.publish_count}")

    pub.disconnect()