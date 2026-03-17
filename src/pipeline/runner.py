"""
Pipeline Runner — orchestrates the full data flow:

    XML API  →  Fetcher  →  MQTT Publisher  →  Broker  →  MQTT Subscriber  →  MySQL

Run this script to start the complete real-time data pipeline.
The fetcher runs on a configurable interval (default 60s, matching API update frequency).

Usage:
    python -m src.pipeline.runner                     # uses .env defaults
    python -m src.pipeline.runner --interval 60       # custom interval
    python -m src.pipeline.runner --no-mqtt           # skip MQTT, write directly to DB
"""

import argparse
import logging
import signal
import sys
import time
import threading

logger = logging.getLogger(__name__)


def run_pipeline(
    broker_host: str = "localhost",
    broker_port: int = 1883,
    db_url: str = "",
    strategic_url: str = "",
    lamppost_url: str = "",
    fetch_interval: int = 60,
    use_mqtt: bool = True,
):
    """
    Start the full pipeline. Blocks until Ctrl+C.

    Parameters
    ----------
    broker_host, broker_port : MQTT broker settings
    db_url : SQLAlchemy connection string for MySQL
    strategic_url, lamppost_url : XML API endpoints (empty = use defaults)
    fetch_interval : seconds between fetch cycles
    use_mqtt : if False, skip MQTT and write directly to DB
    """
    # Lazy imports so module-level import doesn't fail
    from src.fetcher.xml_fetcher import TrafficDataFetcher
    from src.mqtt.publisher import TrafficMqttPublisher
    from src.mqtt.subscriber import TrafficMqttSubscriber

    # --- Initialize components ---

    fetcher_kwargs = {}
    if strategic_url:
        fetcher_kwargs["strategic_url"] = strategic_url
    if lamppost_url:
        fetcher_kwargs["lamppost_url"] = lamppost_url
    fetcher = TrafficDataFetcher(**fetcher_kwargs)

    publisher = None
    subscriber = None

    if use_mqtt:
        publisher = TrafficMqttPublisher(
            broker_host=broker_host,
            broker_port=broker_port,
        )
        subscriber = TrafficMqttSubscriber(
            broker_host=broker_host,
            broker_port=broker_port,
            db_url=db_url,
            batch_size=100,
            flush_interval=5.0,
        )

        # Start subscriber first (so it's ready when publisher sends)
        logger.info("Starting MQTT subscriber...")
        if not subscriber.start():
            logger.error("Failed to start subscriber, exiting")
            return

        # Then connect publisher
        logger.info("Connecting MQTT publisher...")
        if not publisher.connect():
            logger.error("Failed to connect publisher, exiting")
            subscriber.stop()
            return

        logger.info("MQTT pipeline ready")
    else:
        # Direct-to-DB mode: init a simple DB writer
        logger.info("Running in direct-to-DB mode (no MQTT)")
        from src.mqtt.subscriber import TrafficMqttSubscriber
        # Reuse subscriber's DB logic without MQTT
        subscriber = TrafficMqttSubscriber(db_url=db_url)
        subscriber._init_db()

    # --- Graceful shutdown ---

    shutdown_event = threading.Event()

    def signal_handler(sig, frame):
        logger.info("Shutdown signal received, stopping...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # --- Main fetch loop ---

    cycle = 0
    logger.info(
        "Pipeline started. Fetching every %ds. Press Ctrl+C to stop.", fetch_interval
    )

    while not shutdown_event.is_set():
        cycle += 1
        cycle_start = time.time()

        try:
            # Fetch from both APIs
            readings = fetcher.fetch_all()
            logger.info("Cycle %d: fetched %d readings", cycle, len(readings))

            if readings:
                if use_mqtt and publisher:
                    # Publish to MQTT (subscriber will persist to DB)
                    result = publisher.publish_readings(readings)
                    logger.info(
                        "Cycle %d: published %d/%d",
                        cycle, result["published"], result["total"],
                    )
                else:
                    # Direct-to-DB: batch insert using subscriber's DB logic
                    for r in readings:
                        row = {
                            "detector_id": r.detector_id,
                            "source_type": r.source_type,
                            "timestamp": r.timestamp.isoformat(),
                            "lane_id": r.lane_id,
                            "speed": r.speed,
                            "volume": r.volume,
                            "occupancy": r.occupancy,
                            "speed_sd": r.speed_sd,
                            "valid": r.valid,
                        }
                        subscriber._buffer.append(row)
                    subscriber._flush_buffer()
                    logger.info("Cycle %d: wrote %d readings to DB", cycle, len(readings))

        except Exception as e:
            logger.error("Cycle %d error: %s", cycle, e, exc_info=True)

        # Print periodic stats
        if use_mqtt and subscriber:
            stats = subscriber.stats
            logger.info(
                "Cycle %d stats: received=%d saved=%d errors=%d",
                cycle, stats["received"], stats["saved"], stats["errors"],
            )

        # Wait for next cycle
        elapsed = time.time() - cycle_start
        wait_time = max(0, fetch_interval - elapsed)
        if wait_time > 0:
            shutdown_event.wait(wait_time)

    # --- Cleanup ---

    logger.info("Shutting down pipeline...")
    fetcher.close()
    if publisher:
        publisher.disconnect()
    if subscriber:
        subscriber.stop()
    logger.info("Pipeline stopped.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="HK Traffic Data Pipeline Runner"
    )
    parser.add_argument(
        "--interval", type=int, default=60,
        help="Fetch interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--no-mqtt", action="store_true",
        help="Skip MQTT, write directly to MySQL",
    )
    parser.add_argument(
        "--broker-host", default="localhost",
        help="MQTT broker host (default: localhost)",
    )
    parser.add_argument(
        "--broker-port", type=int, default=1883,
        help="MQTT broker port (default: 1883)",
    )
    parser.add_argument(
        "--db-url",
        default="mysql+pymysql://traffic_user:Traffic2025!@localhost:3306/hk_traffic?charset=utf8mb4",
        help="MySQL connection URL",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/pipeline.log", encoding="utf-8"),
        ],
    )

    run_pipeline(
        broker_host=args.broker_host,
        broker_port=args.broker_port,
        db_url=args.db_url,
        fetch_interval=args.interval,
        use_mqtt=not args.no_mqtt,
    )


if __name__ == "__main__":
    main()