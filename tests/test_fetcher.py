"""
Tests for XML fetcher and parser.

Uses a hardcoded sample XML string to test parsing logic.
"""

import pytest

# Sample XML matching raw_speed_volume_list schema (minimal)
SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<raw_speed_volume_list>
  <date>2025-03-15</date>
  <periods>
    <period>
      <period_from>08:30:00</period_from>
      <period_to>09:00:00</period_to>
      <detectors>
        <detector>
          <detector_id>AID01101</detector_id>
          <direction>South East</direction>
          <lanes>
            <lane>
              <lane_id>Fast Lane</lane_id>
              <speed>65</speed>
              <occupancy>12</occupancy>
              <volume>8</volume>
              <s.d.>5.2</s.d.>
              <valid>Y</valid>
            </lane>
          </lanes>
        </detector>
      </detectors>
    </period>
  </periods>
</raw_speed_volume_list>
"""


def test_parse_xml_returns_list():
    """Test that _parse_xml returns a list of dicts."""
    # TODO: Import TrafficDataFetcher, call _parse_xml(SAMPLE_XML, "strategic")
    # TODO: Assert result is list, has at least one item
    # TODO: Assert first item has detector_id, source_type, timestamp, lanes
    pytest.skip("Implementation pending")


def test_parse_xml_extracts_lane_data():
    """Test that lane data (speed, volume, occupancy) is correctly extracted."""
    # TODO: Parse SAMPLE_XML, assert lane values match
    pytest.skip("Implementation pending")


def test_parse_xml_handles_malformed():
    """Test that malformed XML returns empty list without crashing."""
    # TODO: Call _parse_xml with invalid XML, assert [] returned
    pytest.skip("Implementation pending")
