"""
Tests for database models and CRUD operations.

Uses SQLite in-memory database for test isolation — no MySQL needed.
Run: python tests/test_database.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, TrafficReading, DetectorInfo


def _get_test_session():
    """Create a fresh in-memory SQLite database with all tables."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


# =====================================================================
# Model tests
# =====================================================================

def test_traffic_reading_model():
    """TrafficReading ORM model can be created and queried."""
    session = _get_test_session()

    reading = TrafficReading(
        detector_id="AID01101",
        source_type="strategic",
        timestamp=datetime(2026, 3, 18, 8, 30, 0),
        lane_id="Fast Lane",
        speed=67,
        volume=4,
        occupancy=2,
        speed_sd=14.6,
        valid="Y",
    )
    session.add(reading)
    session.commit()

    result = session.query(TrafficReading).first()
    assert result.detector_id == "AID01101"
    assert result.speed == 67
    assert result.lane_id == "Fast Lane"
    session.close()


def test_detector_info_model():
    """DetectorInfo ORM model works correctly."""
    session = _get_test_session()

    detector = DetectorInfo(
        detector_id="AID01101",
        district="Kowloon City",
        road_name_en="Lion Rock Tunnel Road",
        road_name_tc="獅子山隧道公路",
        latitude=22.3456,
        longitude=114.1789,
        direction="South East",
        source_type="strategic",
    )
    session.add(detector)
    session.commit()

    result = session.query(DetectorInfo).first()
    assert result.detector_id == "AID01101"
    assert result.district == "Kowloon City"
    session.close()


def test_to_dict():
    """to_dict() returns JSON-serializable dict."""
    session = _get_test_session()

    reading = TrafficReading(
        detector_id="AID01101",
        source_type="strategic",
        timestamp=datetime(2026, 3, 18, 8, 30, 0),
        lane_id="Fast Lane",
        speed=67, volume=4, occupancy=2, speed_sd=14.6, valid="Y",
    )
    session.add(reading)
    session.commit()

    result = session.query(TrafficReading).first()
    d = result.to_dict()
    assert isinstance(d, dict)
    assert d["detector_id"] == "AID01101"
    assert d["timestamp"] == "2026-03-18T08:30:00"
    session.close()


# =====================================================================
# CRUD tests
# =====================================================================

def test_bulk_insert_readings():
    """bulk_insert_readings inserts multiple rows in one call."""
    from src.database.crud import bulk_insert_readings

    session = _get_test_session()

    rows = [
        {
            "detector_id": f"AID{i:05d}",
            "source_type": "strategic",
            "timestamp": "2026-03-18T08:30:00",
            "lane_id": "Fast Lane",
            "speed": 60 + i,
            "volume": 5,
            "occupancy": 3,
            "speed_sd": 2.0,
            "valid": "Y",
        }
        for i in range(10)
    ]

    count = bulk_insert_readings(session, rows)
    session.commit()

    assert count == 10
    total = session.query(TrafficReading).count()
    assert total == 10
    session.close()


def test_bulk_insert_empty():
    """bulk_insert_readings with empty list returns 0."""
    from src.database.crud import bulk_insert_readings

    session = _get_test_session()
    count = bulk_insert_readings(session, [])
    assert count == 0
    session.close()


def test_get_readings_by_detector():
    """Query readings filtered by detector_id and time range."""
    from src.database.crud import get_readings_by_detector

    session = _get_test_session()

    # Insert test data: 2 detectors, 3 readings each
    for det_id in ["AID01101", "AID01102"]:
        for hour in [8, 9, 10]:
            session.add(TrafficReading(
                detector_id=det_id,
                source_type="strategic",
                timestamp=datetime(2026, 3, 18, hour, 0, 0),
                lane_id="Fast Lane",
                speed=60, volume=5, occupancy=3, speed_sd=2.0, valid="Y",
            ))
    session.commit()

    # Query one detector
    results = get_readings_by_detector(session, "AID01101")
    assert len(results) == 3

    # Query with time range
    results = get_readings_by_detector(
        session, "AID01101",
        start_time=datetime(2026, 3, 18, 8, 30, 0),
        end_time=datetime(2026, 3, 18, 9, 30, 0),
    )
    assert len(results) == 1  # only the 9:00 reading
    assert results[0].timestamp == datetime(2026, 3, 18, 9, 0, 0)

    session.close()


def test_get_readings_valid_only():
    """valid_only filter excludes N readings."""
    from src.database.crud import get_readings_by_detector

    session = _get_test_session()

    session.add(TrafficReading(
        detector_id="AID01101", source_type="strategic",
        timestamp=datetime(2026, 3, 18, 8, 0, 0),
        lane_id="Fast Lane", speed=60, volume=5, occupancy=3,
        speed_sd=2.0, valid="Y",
    ))
    session.add(TrafficReading(
        detector_id="AID01101", source_type="strategic",
        timestamp=datetime(2026, 3, 18, 8, 0, 30),
        lane_id="Fast Lane", speed=0, volume=0, occupancy=0,
        speed_sd=0, valid="N",
    ))
    session.commit()

    valid = get_readings_by_detector(session, "AID01101", valid_only=True)
    assert len(valid) == 1

    all_readings = get_readings_by_detector(session, "AID01101", valid_only=False)
    assert len(all_readings) == 2

    session.close()


def test_get_latest_readings():
    """get_latest_readings returns most recent N readings."""
    from src.database.crud import get_latest_readings

    session = _get_test_session()

    for i in range(5):
        session.add(TrafficReading(
            detector_id="AID01101", source_type="strategic",
            timestamp=datetime(2026, 3, 18, 8, i, 0),
            lane_id="Fast Lane", speed=60, volume=5, occupancy=3,
            speed_sd=2.0, valid="Y",
        ))
    session.commit()

    latest = get_latest_readings(session, "AID01101", limit=3)
    assert len(latest) == 3
    # Should be in descending order
    assert latest[0].timestamp > latest[1].timestamp > latest[2].timestamp

    session.close()


def test_get_all_detectors():
    """get_all_detectors returns all, or filtered by source_type."""
    from src.database.crud import get_all_detectors

    session = _get_test_session()

    session.add(DetectorInfo(
        detector_id="AID01101", district="Kowloon City",
        source_type="strategic",
    ))
    session.add(DetectorInfo(
        detector_id="AID20051", district="Wan Chai",
        source_type="lamppost",
    ))
    session.commit()

    all_det = get_all_detectors(session)
    assert len(all_det) == 2

    strategic = get_all_detectors(session, source_type="strategic")
    assert len(strategic) == 1
    assert strategic[0].detector_id == "AID01101"

    lamppost = get_all_detectors(session, source_type="lamppost")
    assert len(lamppost) == 1
    assert lamppost[0].detector_id == "AID20051"

    session.close()


def test_get_reading_count():
    """get_reading_count returns correct totals."""
    from src.database.crud import get_reading_count

    session = _get_test_session()

    for i in range(3):
        session.add(TrafficReading(
            detector_id="AID01101", source_type="strategic",
            timestamp=datetime(2026, 3, 18, 8, i, 0),
            lane_id="Fast Lane", speed=60, volume=5, occupancy=3,
            speed_sd=2.0, valid="Y",
        ))
    for i in range(2):
        session.add(TrafficReading(
            detector_id="AID20051", source_type="lamppost",
            timestamp=datetime(2026, 3, 18, 8, i, 0),
            lane_id="Fast Lane", speed=50, volume=3, occupancy=1,
            speed_sd=1.0, valid="Y",
        ))
    session.commit()

    assert get_reading_count(session) == 5
    assert get_reading_count(session, source_type="strategic") == 3
    assert get_reading_count(session, source_type="lamppost") == 2

    session.close()


def test_get_time_range():
    """get_time_range returns earliest and latest timestamps."""
    from src.database.crud import get_time_range

    session = _get_test_session()

    for hour in [8, 12, 20]:
        session.add(TrafficReading(
            detector_id="AID01101", source_type="strategic",
            timestamp=datetime(2026, 3, 18, hour, 0, 0),
            lane_id="Fast Lane", speed=60, volume=5, occupancy=3,
            speed_sd=2.0, valid="Y",
        ))
    session.commit()

    tr = get_time_range(session)
    assert tr["earliest"] == datetime(2026, 3, 18, 8, 0, 0)
    assert tr["latest"] == datetime(2026, 3, 18, 20, 0, 0)

    session.close()


# =====================================================================
# Run all
# =====================================================================

if __name__ == "__main__":
    import traceback

    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    passed = failed = 0

    for fn in tests:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {fn.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed, {passed+failed} total")
    if failed:
        sys.exit(1)