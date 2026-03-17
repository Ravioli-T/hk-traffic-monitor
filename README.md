# Hong Kong Smart Traffic Monitoring System

A real-time traffic data pipeline for Hong Kong, built for SDSC6004 — AI for Smart Cities.

## Group

- **Course:** SDSC6004 — AI for Smart Cities
- **Group:** [GroupName]
- **Members:** [Add member names]

## Architecture Overview

The system is organized into four main layers:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Layer 1: Ingestion                                                          │
│  Fetch XML from HK Gov APIs (Strategic Roads + Smart Lampposts)               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Layer 2: MQTT Broker (Eclipse Mosquitto, localhost:1883)                     │
│  Publish parsed data → Subscribe & persist                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Layer 3: MySQL 8.0                                                          │
│  Store real-time + historical traffic readings, detector metadata            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Layer 4: ML API + Frontend                                                  │
│  FastAPI (Isolation Forest, Prophet) → React + Leaflet + ECharts              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- MySQL 8.0
- Eclipse Mosquitto 2.x (MQTT broker on `localhost:1883`)

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

1. Copy `.env.example` to `.env`
2. Set database credentials and other environment variables

### Database Setup

```bash
python scripts/init_db.py
python scripts/import_detector_info.py
```

### Run the Pipeline

```bash
# Real-time mode: fetch → publish → subscribe → store
python main.py --mode realtime

# Import historical data (after placing files in data/raw/)
python main.py --mode import
```

## Folder Structure

| Directory | Purpose |
|-----------|---------|
| `config/` | Central configuration (settings, env loading) |
| `data/` | Local data storage (raw downloads, processed files) |
| `scripts/` | One-off scripts (DB init, detector import, historical import) |
| `src/` | Core application code (fetcher, mqtt, database, pipeline, ml) |
| `frontend/` | React app (separate teammate responsibility) |
| `notebooks/` | Jupyter notebooks for EDA |
| `tests/` | Pytest test suite |
| `logs/` | Runtime log files |

## License

[Add license if applicable]
