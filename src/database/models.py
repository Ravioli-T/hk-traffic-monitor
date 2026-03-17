"""
SQLAlchemy ORM models for the hk_traffic database.

Maps to the two tables already created in MySQL:
  - detector_info   : detector metadata (location, district, road name)
  - traffic_readings : per-lane traffic measurements (speed, volume, occupancy)

These models are used for:
  1. Table creation via init_db() (if tables don't exist yet)
  2. ORM queries in crud.py and ML modules
  3. Schema documentation (single source of truth)
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, BigInteger, DateTime, DECIMAL,
    Enum, CHAR, TIMESTAMP, Index, func,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DetectorInfo(Base):
    """Detector metadata — one row per physical detector."""

    __tablename__ = "detector_info"

    detector_id = Column(String(20), primary_key=True)
    district = Column(String(50))
    road_name_en = Column(String(200))
    road_name_tc = Column(String(200))
    latitude = Column(DECIMAL(9, 6))
    longitude = Column(DECIMAL(9, 6))
    direction = Column(String(50))
    easting = Column(DECIMAL(12, 2))
    northing = Column(DECIMAL(12, 2))
    source_type = Column(Enum("strategic", "lamppost"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return (
            f"<DetectorInfo {self.detector_id} "
            f"district={self.district} source={self.source_type}>"
        )

    def to_dict(self) -> dict:
        return {
            "detector_id": self.detector_id,
            "district": self.district,
            "road_name_en": self.road_name_en,
            "road_name_tc": self.road_name_tc,
            "latitude": float(self.latitude) if self.latitude else None,
            "longitude": float(self.longitude) if self.longitude else None,
            "direction": self.direction,
            "source_type": self.source_type,
        }


class TrafficReading(Base):
    """Traffic measurement — one row per lane per detector per 30s period."""

    __tablename__ = "traffic_readings"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    detector_id = Column(String(20), nullable=False)
    source_type = Column(Enum("strategic", "lamppost"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    lane_id = Column(String(30), nullable=False)
    speed = Column(Integer)
    volume = Column(Integer)
    occupancy = Column(Integer)
    speed_sd = Column(DECIMAL(5, 2))
    valid = Column(CHAR(1), default="Y")
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Indexes (match the ones already in your MySQL schema)
    __table_args__ = (
        Index("idx_detector_time", "detector_id", "timestamp"),
        Index("idx_timestamp", "timestamp"),
        Index("idx_source_type", "source_type"),
    )

    def __repr__(self):
        return (
            f"<TrafficReading {self.detector_id}/{self.lane_id} "
            f"@ {self.timestamp} speed={self.speed}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "detector_id": self.detector_id,
            "source_type": self.source_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "lane_id": self.lane_id,
            "speed": self.speed,
            "volume": self.volume,
            "occupancy": self.occupancy,
            "speed_sd": float(self.speed_sd) if self.speed_sd else None,
            "valid": self.valid,
        }
