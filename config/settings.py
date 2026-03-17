"""
Central configuration for HK Traffic Monitoring System.

Loads environment variables via python-dotenv and defines all constants.
Sensitive values (DB password, etc.) come from environment variables with
sensible defaults for local development.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# --- API URLs ---
STRATEGIC_API_URL: str = os.getenv(
    "STRATEGIC_API_URL",
    "https://resource.data.one.gov.hk/td/traffic-detectors/rawSpeedVol-all.xml",
)
LAMPPOST_API_URL: str = os.getenv(
    "LAMPPOST_API_URL",
    "",  # TODO: Set from data.gov.hk portal when available
)
STRATEGIC_CSV_URL: str = os.getenv(
    "STRATEGIC_CSV_URL",
    "https://static.data.gov.hk/td/traffic-data-strategic-major-roads/info/traffic_speed_volume_occ_info.csv",
)
LAMPPOST_CSV_URL: str = os.getenv(
    "LAMPPOST_CSV_URL",
    "",  # TODO: Set from data.gov.hk portal when available
)

# --- MQTT ---
MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_TOPIC_PREFIX: str = os.getenv("MQTT_TOPIC_PREFIX", "hk-traffic")
MQTT_QOS: int = int(os.getenv("MQTT_QOS", "1"))

# --- Database ---
DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
DB_NAME: str = os.getenv("DB_NAME", "hk_traffic")
DB_USER: str = os.getenv("DB_USER", "root")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "your_password_here")

DB_URL: str = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# --- Fetch interval ---
FETCH_INTERVAL_SECONDS: int = int(os.getenv("FETCH_INTERVAL_SECONDS", "60"))

# --- Network timeout ---
REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))
