"""
Entry point for HK Traffic Monitoring System.

Supports modes: realtime (fetch → publish → subscribe → store), import (historical).
"""

import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.pipeline.runner import PipelineRunner

# Configure logging: console + logs/pipeline.log
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "pipeline.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Parse CLI args and run appropriate mode."""
    parser = argparse.ArgumentParser(description="HK Traffic Monitoring Pipeline")
    parser.add_argument(
        "--mode",
        choices=["realtime", "import"],
        default="realtime",
        help="realtime: fetch → publish → subscribe → store; import: historical data",
    )
    args = parser.parse_args()

    if args.mode == "realtime":
        logger.info("Starting real-time pipeline...")
        runner = PipelineRunner()
        try:
            runner.run_realtime()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            runner.stop()
    elif args.mode == "import":
        logger.info("Import mode: run scripts/import_historical_data.py")
        # TODO: Call import script or integrate here


if __name__ == "__main__":
    main()
