"""
Import detector metadata from CSV files into the detector_info table.

Downloads CSVs from DATA.GOV.HK (or reads from local data/raw/ directory),
parses them with pandas, and upserts into MySQL.

Usage:
    python scripts/import_detector_info.py              # download + import
    python scripts/import_detector_info.py --local      # use local CSV files

CSV columns (both datasets):
    AID_ID_Number, District, Road_EN, Road_TC, Road_SC,
    Easting, Northing, Latitude, Longitude, Direction, Rotation
"""

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import requests

from src.database.connection import get_session_factory

logger = logging.getLogger(__name__)

# CSV download URLs
STRATEGIC_CSV_URL = (
    "https://static.data.gov.hk/td/traffic-data-strategic-major-roads/"
    "info/traffic_speed_volume_occ_info.csv"
)
# TODO: Update with actual lamppost CSV URL from DATA.GOV.HK portal
LAMPPOST_CSV_URL = ""

# Local file paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def download_csv(url: str, save_path: str) -> str | None:
    """Download a CSV file and save locally. Returns path or None."""
    if not url:
        logger.warning("No URL provided, skipping download")
        return None

    try:
        logger.info("Downloading %s", url)
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(resp.content)

        logger.info("Saved to %s (%d bytes)", save_path, len(resp.content))
        return save_path
    except Exception as e:
        logger.error("Download failed: %s", e)
        return None


def parse_csv(csv_path: str, source_type: str) -> list[dict]:
    """
    Parse a detector locations CSV into a list of dicts for DB upsert.

    Handles the column name mapping:
        CSV column        → DB column
        AID_ID_Number     → detector_id
        District          → district
        Road_EN           → road_name_en
        Road_TC           → road_name_tc
        Easting           → easting
        Northing          → northing
        Latitude          → latitude
        Longitude         → longitude
        Direction         → direction
    """
    logger.info("Parsing %s (source_type=%s)", csv_path, source_type)

    # Try different encodings (HK gov CSVs sometimes use Big5 for Chinese)
    for encoding in ["utf-8", "utf-8-sig", "big5", "cp950"]:
        try:
            df = pd.read_csv(csv_path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        logger.error("Failed to read CSV with any encoding: %s", csv_path)
        return []

    # Normalize column names (strip whitespace, handle variations)
    df.columns = df.columns.str.strip()

    # Log actual columns for debugging
    logger.info("CSV columns: %s", list(df.columns))
    logger.info("CSV rows: %d", len(df))

    # Map CSV columns to DB columns
    # The CSV might have slightly different column names, so we try common variants
    column_map = {}
    for csv_col in df.columns:
        col_lower = csv_col.lower().replace(" ", "_")
        if "aid" in col_lower or "id_number" in col_lower or "device_id" in col_lower:
            column_map[csv_col] = "detector_id"
        elif col_lower == "district":
            column_map[csv_col] = "district"
        elif col_lower in ("road_en", "road_name_en"):
            column_map[csv_col] = "road_name_en"
        elif col_lower in ("road_tc", "road_name_tc"):
            column_map[csv_col] = "road_name_tc"
        elif col_lower == "easting":
            column_map[csv_col] = "easting"
        elif col_lower == "northing":
            column_map[csv_col] = "northing"
        elif col_lower == "latitude":
            column_map[csv_col] = "latitude"
        elif col_lower == "longitude":
            column_map[csv_col] = "longitude"
        elif col_lower == "direction":
            column_map[csv_col] = "direction"

    df = df.rename(columns=column_map)
    logger.info("Mapped columns: %s", column_map)

    # Keep only the columns we need
    keep_cols = [
        "detector_id", "district", "road_name_en", "road_name_tc",
        "latitude", "longitude", "direction", "easting", "northing",
    ]
    available = [c for c in keep_cols if c in df.columns]
    df = df[available].copy()

    # Add source_type
    df["source_type"] = source_type

    # Clean up
    if "detector_id" in df.columns:
        df["detector_id"] = df["detector_id"].astype(str).str.strip()
        df = df[df["detector_id"].str.len() > 0]  # drop empty IDs
        df = df.drop_duplicates(subset=["detector_id"])

    # Convert to list of dicts
    records = df.to_dict("records")

    # Replace NaN with None for SQL compatibility
    for record in records:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None

    logger.info("Parsed %d detector records", len(records))
    return records


def import_detectors(records: list[dict], db_url: str | None = None):
    """Upsert detector records into the database."""
    if not records:
        logger.warning("No records to import")
        return

    from src.database.crud import upsert_detector_info

    session_factory = get_session_factory(db_url)
    session = session_factory()
    try:
        count = upsert_detector_info(session, records)
        session.commit()
        logger.info("Upserted %d detector records", count)
    except Exception as e:
        session.rollback()
        logger.error("Import failed: %s", e)
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Import detector metadata CSVs")
    parser.add_argument(
        "--local", action="store_true",
        help="Use local CSV files from data/raw/ instead of downloading",
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help="MySQL connection URL (default: from .env)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    all_records = []

    # --- Strategic roads CSV ---
    strategic_path = os.path.join(DATA_DIR, "strategic_detector_info.csv")
    if args.local:
        if os.path.exists(strategic_path):
            records = parse_csv(strategic_path, "strategic")
            all_records.extend(records)
        else:
            logger.warning("Local file not found: %s", strategic_path)
    else:
        path = download_csv(STRATEGIC_CSV_URL, strategic_path)
        if path:
            records = parse_csv(path, "strategic")
            all_records.extend(records)

    # --- Lamppost CSV ---
    lamppost_path = os.path.join(DATA_DIR, "lamppost_detector_info.csv")
    if args.local:
        if os.path.exists(lamppost_path):
            records = parse_csv(lamppost_path, "lamppost")
            all_records.extend(records)
        else:
            logger.warning("Local file not found: %s", lamppost_path)
    else:
        if LAMPPOST_CSV_URL:
            path = download_csv(LAMPPOST_CSV_URL, lamppost_path)
            if path:
                records = parse_csv(path, "lamppost")
                all_records.extend(records)
        else:
            logger.warning("Lamppost CSV URL not configured, skipping")

    # --- Import to database ---
    if all_records:
        print(f"\nReady to import {len(all_records)} detectors to database")
        import_detectors(all_records, args.db_url)
        print("Import complete!")
    else:
        print("No records to import")


if __name__ == "__main__":
    main()