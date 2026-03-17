"""
CRUD operations for the hk_traffic database.

Provides functions for:
  - Bulk inserting traffic readings (used by MQTT subscriber and direct import)
  - Bulk inserting/updating detector metadata (used by CSV import script)
  - Query helpers for ML models, API endpoints, and EDA notebooks

All functions accept a SQLAlchemy Session and do NOT commit —
the caller controls the transaction boundary.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import text, func, distinct
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert as mysql_insert

from src.database.models import TrafficReading, DetectorInfo

logger = logging.getLogger(__name__)


# =====================================================================
# WRITE operations
# =====================================================================

def bulk_insert_readings(session: Session, rows: list[dict]) -> int:
    """
    Batch-insert traffic readings using raw SQL for best performance.

    Parameters
    ----------
    session : Session
        Active SQLAlchemy session.
    rows : list[dict]
        Each dict must have keys: detector_id, source_type, timestamp,
        lane_id, speed, volume, occupancy, speed_sd, valid.

    Returns
    -------
    int
        Number of rows inserted.
    """
    if not rows:
        return 0

    insert_sql = text("""
        INSERT INTO traffic_readings
            (detector_id, source_type, timestamp, lane_id,
             speed, volume, occupancy, speed_sd, valid)
        VALUES
            (:detector_id, :source_type, :timestamp, :lane_id,
             :speed, :volume, :occupancy, :speed_sd, :valid)
    """)

    session.execute(insert_sql, rows)
    logger.debug("Bulk inserted %d traffic readings", len(rows))
    return len(rows)


def upsert_detector_info(session: Session, detectors: list[dict]) -> int:
    """
    Insert or update detector metadata.

    Uses MySQL INSERT ... ON DUPLICATE KEY UPDATE so re-importing
    the CSV won't create duplicates.

    Parameters
    ----------
    session : Session
        Active SQLAlchemy session.
    detectors : list[dict]
        Each dict should have keys matching DetectorInfo columns.

    Returns
    -------
    int
        Number of rows affected.
    """
    if not detectors:
        return 0

    stmt = mysql_insert(DetectorInfo).values(detectors)
    update_cols = {
        "district": stmt.inserted.district,
        "road_name_en": stmt.inserted.road_name_en,
        "road_name_tc": stmt.inserted.road_name_tc,
        "latitude": stmt.inserted.latitude,
        "longitude": stmt.inserted.longitude,
        "direction": stmt.inserted.direction,
        "easting": stmt.inserted.easting,
        "northing": stmt.inserted.northing,
        "source_type": stmt.inserted.source_type,
    }
    stmt = stmt.on_duplicate_key_update(**update_cols)
    result = session.execute(stmt)
    logger.debug("Upserted %d detector records", len(detectors))
    return result.rowcount


# =====================================================================
# READ operations — for ML, API, and EDA
# =====================================================================

def get_readings_by_detector(
    session: Session,
    detector_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    lane_id: Optional[str] = None,
    valid_only: bool = True,
) -> list[TrafficReading]:
    """
    Query traffic readings for a specific detector.

    This is the primary query for ML model training (Prophet, Isolation Forest).

    Parameters
    ----------
    detector_id : str
        e.g. "AID01101"
    start_time, end_time : datetime, optional
        Time range filter.
    lane_id : str, optional
        Filter by specific lane (e.g. "Fast Lane").
    valid_only : bool
        If True, only return readings where valid='Y'.
    """
    query = session.query(TrafficReading).filter(
        TrafficReading.detector_id == detector_id
    )

    if start_time:
        query = query.filter(TrafficReading.timestamp >= start_time)
    if end_time:
        query = query.filter(TrafficReading.timestamp <= end_time)
    if lane_id:
        query = query.filter(TrafficReading.lane_id == lane_id)
    if valid_only:
        query = query.filter(TrafficReading.valid == "Y")

    return query.order_by(TrafficReading.timestamp).all()


def get_readings_by_time_range(
    session: Session,
    start_time: datetime,
    end_time: datetime,
    source_type: Optional[str] = None,
    valid_only: bool = True,
) -> list[TrafficReading]:
    """
    Query all readings in a time range. Used for anomaly detection across all detectors.
    """
    query = session.query(TrafficReading).filter(
        TrafficReading.timestamp >= start_time,
        TrafficReading.timestamp <= end_time,
    )

    if source_type:
        query = query.filter(TrafficReading.source_type == source_type)
    if valid_only:
        query = query.filter(TrafficReading.valid == "Y")

    return query.order_by(TrafficReading.timestamp).all()


def get_latest_readings(
    session: Session,
    detector_id: str,
    limit: int = 10,
) -> list[TrafficReading]:
    """
    Get the most recent N readings for a detector.
    Used by the frontend dashboard for real-time display.
    """
    return (
        session.query(TrafficReading)
        .filter(TrafficReading.detector_id == detector_id)
        .order_by(TrafficReading.timestamp.desc())
        .limit(limit)
        .all()
    )


def get_all_detectors(
    session: Session,
    source_type: Optional[str] = None,
) -> list[DetectorInfo]:
    """
    Return all detector metadata. Used for map display and dropdown lists.
    """
    query = session.query(DetectorInfo)
    if source_type:
        query = query.filter(DetectorInfo.source_type == source_type)
    return query.order_by(DetectorInfo.detector_id).all()


def get_detector_by_id(
    session: Session,
    detector_id: str,
) -> Optional[DetectorInfo]:
    """Look up a single detector's metadata."""
    return session.query(DetectorInfo).filter(
        DetectorInfo.detector_id == detector_id
    ).first()


# =====================================================================
# STATS — for EDA and data quality analysis
# =====================================================================

def get_reading_count(
    session: Session,
    source_type: Optional[str] = None,
) -> int:
    """Total number of traffic readings in the database."""
    query = session.query(func.count(TrafficReading.id))
    if source_type:
        query = query.filter(TrafficReading.source_type == source_type)
    return query.scalar()


def get_detector_count(
    session: Session,
    source_type: Optional[str] = None,
) -> int:
    """Number of unique detectors that have sent data."""
    query = session.query(func.count(distinct(TrafficReading.detector_id)))
    if source_type:
        query = query.filter(TrafficReading.source_type == source_type)
    return query.scalar()


def get_time_range(session: Session) -> dict:
    """
    Get the earliest and latest timestamps in the database.
    Useful for EDA to confirm data coverage.
    """
    result = session.query(
        func.min(TrafficReading.timestamp),
        func.max(TrafficReading.timestamp),
    ).first()
    return {
        "earliest": result[0],
        "latest": result[1],
    }


def get_valid_rate_by_source(session: Session) -> list[dict]:
    """
    Data quality: percentage of valid readings per source type.
    Used for RQ3 comparison analysis.
    """
    results = (
        session.query(
            TrafficReading.source_type,
            func.count(TrafficReading.id).label("total"),
            func.sum(func.IF(TrafficReading.valid == "Y", 1, 0)).label("valid"),
        )
        .group_by(TrafficReading.source_type)
        .all()
    )
    return [
        {
            "source_type": r.source_type,
            "total": r.total,
            "valid": int(r.valid),
            "valid_rate": round(int(r.valid) / r.total * 100, 2) if r.total > 0 else 0,
        }
        for r in results
    ]


def get_readings_as_dataframe(
    session: Session,
    detector_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    """
    Return readings as a pandas DataFrame.
    Convenience function for EDA notebooks and ML feature engineering.

    Returns None if pandas is not installed.
    """
    try:
        import pandas as pd
    except ImportError:
        logger.warning("pandas not installed, cannot return DataFrame")
        return None

    readings = get_readings_by_detector(
        session, detector_id, start_time, end_time
    )
    if not readings:
        return pd.DataFrame()

    data = [r.to_dict() for r in readings]
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df
