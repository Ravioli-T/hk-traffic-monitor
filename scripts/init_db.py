"""
One-time script to create all database tables.

Run this before starting the pipeline or importing data.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.connection import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """Create all tables in the database."""
    logger.info("Initializing database tables...")
    init_db()
    logger.info("Database initialization complete.")


if __name__ == "__main__":
    main()
