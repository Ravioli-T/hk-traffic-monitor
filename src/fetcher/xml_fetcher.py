"""
XML Fetcher for Hong Kong Traffic Data APIs.

Fetches real-time traffic speed/volume/occupancy data from two DATA.GOV.HK endpoints:
  1. Strategic / Major Roads
  2. Smart Lampposts

Both APIs return XML with identical schema, updated every ~1 minute.
Each response contains 2 x 30-second periods, each with hundreds of detectors.
"""

import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
from xml.etree import ElementTree as ET

import requests

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TrafficReading:
    """One row in the traffic_readings table: a single lane measurement."""
    detector_id: str
    source_type: str          # 'strategic' or 'lamppost'
    timestamp: datetime       # period midpoint (period_from)
    lane_id: str
    speed: Optional[int]
    volume: Optional[int]
    occupancy: Optional[int]
    speed_sd: Optional[float]
    valid: str                # 'Y' or 'N'
    direction: str = ""       # detector direction, useful metadata

    def to_dict(self) -> dict:
        """Convert to a plain dict (for JSON serialization / DB insert)."""
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d


# ---------------------------------------------------------------------------
# XML Parser
# ---------------------------------------------------------------------------

def parse_xml(xml_text: str, source_type: str) -> list[TrafficReading]:
    """
    Parse the raw XML response into a list of TrafficReading objects.

    Parameters
    ----------
    xml_text : str
        Raw XML string from the API.
    source_type : str
        'strategic' or 'lamppost' — injected because the XML itself
        does not indicate which dataset it comes from.

    Returns
    -------
    list[TrafficReading]
        One entry per lane per detector per period.
    """
    readings: list[TrafficReading] = []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.error("XML parse error (%s): %s", source_type, e)
        return readings

    # <date>2026-03-17</date>
    date_str = root.findtext("date", "").strip()
    if not date_str:
        logger.warning("Missing <date> element in %s XML", source_type)
        return readings

    for period in root.findall(".//period"):
        # <period_from>23:16:00</period_from>
        period_from = period.findtext("period_from", "").strip()
        if not period_from:
            logger.warning("Missing <period_from> in a period, skipping")
            continue

        # Combine date + period_from → datetime
        try:
            timestamp = datetime.strptime(
                f"{date_str} {period_from}", "%Y-%m-%d %H:%M:%S"
            )
        except ValueError as e:
            logger.warning("Bad timestamp '%s %s': %s", date_str, period_from, e)
            continue

        for detector in period.findall(".//detector"):
            detector_id = detector.findtext("detector_id", "").strip()
            direction = detector.findtext("direction", "").strip()

            if not detector_id:
                continue

            for lane in detector.findall(".//lane"):
                lane_id = lane.findtext("lane_id", "").strip()
                if not lane_id:
                    continue

                reading = TrafficReading(
                    detector_id=detector_id,
                    source_type=source_type,
                    timestamp=timestamp,
                    lane_id=lane_id,
                    speed=_parse_int(lane.findtext("speed")),
                    volume=_parse_int(lane.findtext("volume")),
                    occupancy=_parse_int(lane.findtext("occupancy")),
                    speed_sd=_parse_float(lane.findtext("s.d.")),
                    valid=lane.findtext("valid", "N").strip(),
                    direction=direction,
                )
                readings.append(reading)

    logger.info(
        "Parsed %d readings from %s XML (date=%s, periods=%d)",
        len(readings),
        source_type,
        date_str,
        len(root.findall(".//period")),
    )
    return readings


# ---------------------------------------------------------------------------
# HTTP Fetcher
# ---------------------------------------------------------------------------

class TrafficDataFetcher:
    """
    Fetches XML data from one or both HK traffic APIs.

    Usage
    -----
    >>> fetcher = TrafficDataFetcher()
    >>> readings = fetcher.fetch_all()          # both APIs
    >>> readings = fetcher.fetch_strategic()     # strategic roads only
    >>> readings = fetcher.fetch_lamppost()      # smart lampposts only
    """

    # Default API endpoints
    STRATEGIC_URL = (
        "https://resource.data.one.gov.hk/td/traffic-detectors/rawSpeedVol-all.xml"
    )
    LAMPPOST_URL = "https://resource.data.one.gov.hk/td/traffic-detectors/rawSpeedVol_SLP-all.xml"

    def __init__(
        self,
        strategic_url: str | None = None,
        lamppost_url: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        self.strategic_url = strategic_url or self.STRATEGIC_URL
        self.lamppost_url = lamppost_url or self.LAMPPOST_URL
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Reuse session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "HK-Traffic-Monitor/1.0",
            "Accept": "application/xml",
        })

    def fetch_strategic(self) -> list[TrafficReading]:
        """Fetch and parse strategic / major roads data."""
        xml_text = self._fetch_url(self.strategic_url, "strategic")
        if xml_text is None:
            return []
        return parse_xml(xml_text, source_type="strategic")

    def fetch_lamppost(self) -> list[TrafficReading]:
        """Fetch and parse smart lamppost data."""
        if not self.lamppost_url:
            logger.warning("Lamppost URL not configured, skipping")
            return []
        xml_text = self._fetch_url(self.lamppost_url, "lamppost")
        if xml_text is None:
            return []
        return parse_xml(xml_text, source_type="lamppost")

    def fetch_all(self) -> list[TrafficReading]:
        """Fetch both APIs and return combined readings."""
        readings = self.fetch_strategic()
        readings.extend(self.fetch_lamppost())
        return readings

    def _fetch_url(self, url: str, label: str) -> str | None:
        """
        GET the URL with retries. Returns raw text or None on failure.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                resp.raise_for_status()

                # Sanity check: response should be XML
                content_type = resp.headers.get("Content-Type", "")
                if "xml" not in content_type and not resp.text.strip().startswith("<?xml"):
                    logger.warning(
                        "[%s] Unexpected content type: %s (attempt %d/%d)",
                        label, content_type, attempt, self.max_retries,
                    )

                logger.debug(
                    "[%s] Fetched %d bytes (attempt %d)",
                    label, len(resp.text), attempt,
                )
                return resp.text

            except requests.exceptions.Timeout:
                logger.warning(
                    "[%s] Timeout (attempt %d/%d)",
                    label, attempt, self.max_retries,
                )
            except requests.exceptions.ConnectionError as e:
                logger.warning(
                    "[%s] Connection error (attempt %d/%d): %s",
                    label, attempt, self.max_retries, e,
                )
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response else "?"
                logger.error(
                    "[%s] HTTP %s (attempt %d/%d): %s",
                    label, status, attempt, self.max_retries, e,
                )
                # Don't retry on 4xx client errors
                if e.response is not None and 400 <= e.response.status_code < 500:
                    return None
            except requests.exceptions.RequestException as e:
                logger.error(
                    "[%s] Request error (attempt %d/%d): %s",
                    label, attempt, self.max_retries, e,
                )

            if attempt < self.max_retries:
                time.sleep(self.retry_delay * attempt)  # linear backoff

        logger.error("[%s] All %d attempts failed", label, self.max_retries)
        return None

    def close(self):
        """Close the underlying HTTP session."""
        self.session.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_int(text: str | None) -> int | None:
    """Safely parse an integer from XML text."""
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _parse_float(text: str | None) -> float | None:
    """Safely parse a float from XML text."""
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Quick test (run this file directly)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    fetcher = TrafficDataFetcher()

    for source, fetch_fn in [
        ("strategic", fetcher.fetch_strategic),
        ("lamppost", fetcher.fetch_lamppost),
    ]:
        print(f"\n{'='*50}")
        print(f"--- Fetching {source} ---")
        readings = fetch_fn()
        print(f"Total readings: {len(readings)}")

        if readings:
            for r in readings[:3]:
                print(f"  {r.detector_id} | {r.lane_id:15s} | "
                      f"speed={r.speed} vol={r.volume} occ={r.occupancy} "
                      f"sd={r.speed_sd} valid={r.valid} | {r.timestamp}")

            detectors = set(r.detector_id for r in readings)
            valid_count = sum(1 for r in readings if r.valid == "Y")
            print(f"Unique detectors: {len(detectors)}")
            print(f"Valid readings: {valid_count}/{len(readings)} "
                  f"({100*valid_count/len(readings):.1f}%)")
        else:
            print("  ⚠ No readings returned — check URL and network")

    fetcher.close()