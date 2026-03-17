"""
Test the XML parser against a real sample from the strategic roads API.
Run: python -m pytest tests/test_xml_fetcher.py -v
  or: python tests/test_xml_fetcher.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from src.fetcher.xml_fetcher import parse_xml, TrafficReading, _parse_int, _parse_float

# ---- Real XML sample (trimmed from actual API response 2026-03-17) ----
SAMPLE_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<raw_speed_volume_list>
  <date>2026-03-17</date>
  <periods>
    <period>
      <period_from>23:16:00</period_from>
      <period_to>23:16:30</period_to>
      <detectors>
        <detector>
          <detector_id>AID01101</detector_id>
          <direction>South East</direction>
          <lanes>
            <lane>
              <lane_id>Fast Lane</lane_id>
              <speed>67</speed>
              <occupancy>2</occupancy>
              <volume>4</volume>
              <s.d.>14.6</s.d.>
              <valid>Y</valid>
            </lane>
            <lane>
              <lane_id>Middle Lane</lane_id>
              <speed>68</speed>
              <occupancy>4</occupancy>
              <volume>3</volume>
              <s.d.>16</s.d.>
              <valid>Y</valid>
            </lane>
            <lane>
              <lane_id>Slow Lane</lane_id>
              <speed>70</speed>
              <occupancy>0</occupancy>
              <volume>0</volume>
              <s.d.>0</s.d.>
              <valid>Y</valid>
            </lane>
          </lanes>
        </detector>
        <detector>
          <detector_id>AID01104</detector_id>
          <direction>North East</direction>
          <lanes>
            <lane>
              <lane_id>Fast Lane</lane_id>
              <speed>50</speed>
              <occupancy>0</occupancy>
              <volume>0</volume>
              <s.d.>0</s.d.>
              <valid>Y</valid>
            </lane>
            <lane>
              <lane_id>Slow Lane</lane_id>
              <speed>69</speed>
              <occupancy>1</occupancy>
              <volume>3</volume>
              <s.d.>4.5</s.d.>
              <valid>Y</valid>
            </lane>
          </lanes>
        </detector>
      </detectors>
    </period>
    <period>
      <period_from>23:16:30</period_from>
      <period_to>23:17:00</period_to>
      <detectors>
        <detector>
          <detector_id>AID01101</detector_id>
          <direction>South East</direction>
          <lanes>
            <lane>
              <lane_id>Fast Lane</lane_id>
              <speed>72</speed>
              <occupancy>3</occupancy>
              <volume>5</volume>
              <s.d.>8.1</s.d.>
              <valid>Y</valid>
            </lane>
            <lane>
              <lane_id>Middle Lane</lane_id>
              <speed>0</speed>
              <occupancy>0</occupancy>
              <volume>0</volume>
              <s.d.>0</s.d.>
              <valid>N</valid>
            </lane>
            <lane>
              <lane_id>Slow Lane</lane_id>
              <speed>55</speed>
              <occupancy>1</occupancy>
              <volume>2</volume>
              <s.d.>3.2</s.d.>
              <valid>Y</valid>
            </lane>
          </lanes>
        </detector>
      </detectors>
    </period>
  </periods>
</raw_speed_volume_list>
"""

# XML with 4-lane detector (Middle Lane 1 + Middle Lane 2)
SAMPLE_4LANE_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<raw_speed_volume_list>
  <date>2026-03-17</date>
  <periods>
    <period>
      <period_from>10:00:00</period_from>
      <period_to>10:00:30</period_to>
      <detectors>
        <detector>
          <detector_id>AID01111</detector_id>
          <direction>North East</direction>
          <lanes>
            <lane>
              <lane_id>Fast Lane</lane_id>
              <speed>72</speed><occupancy>6</occupancy><volume>10</volume>
              <s.d.>7.1</s.d.><valid>Y</valid>
            </lane>
            <lane>
              <lane_id>Middle Lane 1</lane_id>
              <speed>57</speed><occupancy>7</occupancy><volume>9</volume>
              <s.d.>4.8</s.d.><valid>Y</valid>
            </lane>
            <lane>
              <lane_id>Middle Lane 2</lane_id>
              <speed>54</speed><occupancy>2</occupancy><volume>4</volume>
              <s.d.>12.4</s.d.><valid>Y</valid>
            </lane>
            <lane>
              <lane_id>Slow Lane</lane_id>
              <speed>39</speed><occupancy>1</occupancy><volume>3</volume>
              <s.d.>4</s.d.><valid>Y</valid>
            </lane>
          </lanes>
        </detector>
      </detectors>
    </period>
  </periods>
</raw_speed_volume_list>
"""


def test_parse_basic():
    """Parser returns correct number of readings from sample XML."""
    readings = parse_xml(SAMPLE_XML, source_type="strategic")
    # Period 1: AID01101 (3 lanes) + AID01104 (2 lanes) = 5
    # Period 2: AID01101 (3 lanes) = 3
    # Total = 8
    assert len(readings) == 8, f"Expected 8 readings, got {len(readings)}"


def test_field_values():
    """Spot-check field values for the first reading."""
    readings = parse_xml(SAMPLE_XML, source_type="strategic")
    r = readings[0]
    assert r.detector_id == "AID01101"
    assert r.source_type == "strategic"
    assert r.timestamp == datetime(2026, 3, 17, 23, 16, 0)
    assert r.lane_id == "Fast Lane"
    assert r.speed == 67
    assert r.volume == 4
    assert r.occupancy == 2
    assert r.speed_sd == 14.6
    assert r.valid == "Y"
    assert r.direction == "South East"


def test_two_lane_detector():
    """AID01104 has only 2 lanes (Fast + Slow)."""
    readings = parse_xml(SAMPLE_XML, source_type="strategic")
    aid01104 = [r for r in readings if r.detector_id == "AID01104"]
    assert len(aid01104) == 2
    lane_ids = {r.lane_id for r in aid01104}
    assert lane_ids == {"Fast Lane", "Slow Lane"}


def test_four_lane_detector():
    """AID01111 has 4 lanes including Middle Lane 1 and Middle Lane 2."""
    readings = parse_xml(SAMPLE_4LANE_XML, source_type="strategic")
    assert len(readings) == 4
    lane_ids = [r.lane_id for r in readings]
    assert lane_ids == ["Fast Lane", "Middle Lane 1", "Middle Lane 2", "Slow Lane"]


def test_two_periods():
    """Each API response has 2 periods with different timestamps."""
    readings = parse_xml(SAMPLE_XML, source_type="strategic")
    timestamps = sorted(set(r.timestamp for r in readings))
    assert len(timestamps) == 2
    assert timestamps[0] == datetime(2026, 3, 17, 23, 16, 0)
    assert timestamps[1] == datetime(2026, 3, 17, 23, 16, 30)


def test_invalid_reading():
    """A lane with valid='N' is still parsed (we keep it for analysis)."""
    readings = parse_xml(SAMPLE_XML, source_type="strategic")
    invalid = [r for r in readings if r.valid == "N"]
    assert len(invalid) == 1
    assert invalid[0].detector_id == "AID01101"
    assert invalid[0].lane_id == "Middle Lane"
    assert invalid[0].speed == 0


def test_source_type_propagation():
    """source_type is correctly set for all readings."""
    for src in ("strategic", "lamppost"):
        readings = parse_xml(SAMPLE_XML, source_type=src)
        assert all(r.source_type == src for r in readings)


def test_to_dict():
    """to_dict() produces JSON-serializable output."""
    readings = parse_xml(SAMPLE_XML, source_type="strategic")
    d = readings[0].to_dict()
    assert isinstance(d, dict)
    assert isinstance(d["timestamp"], str)  # ISO format string
    assert d["detector_id"] == "AID01101"


def test_malformed_xml():
    """Malformed XML returns empty list, no crash."""
    readings = parse_xml("<not>valid xml<broken", source_type="strategic")
    assert readings == []


def test_empty_xml():
    """Empty date element returns empty list."""
    readings = parse_xml(
        '<?xml version="1.0"?><raw_speed_volume_list><date></date></raw_speed_volume_list>',
        source_type="strategic",
    )
    assert readings == []


def test_parse_int_helper():
    assert _parse_int("42") == 42
    assert _parse_int("  67  ") == 67
    assert _parse_int("") is None
    assert _parse_int(None) is None
    assert _parse_int("abc") is None


def test_parse_float_helper():
    assert _parse_float("14.6") == 14.6
    assert _parse_float("0") == 0.0
    assert _parse_float("") is None
    assert _parse_float(None) is None
    assert _parse_float("xyz") is None


# ---------------------------------------------------------------------------
# Run all tests if executed directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import traceback

    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    passed = failed = 0

    for test_fn in tests:
        try:
            test_fn()
            print(f"  PASS  {test_fn.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {test_fn.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed, {passed+failed} total")
    if failed:
        sys.exit(1)