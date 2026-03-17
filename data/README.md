# Data Directory

This directory stores local data files for the HK Traffic Monitoring System.

## Structure

- **`raw/`** — Raw downloaded historical files from DATA.GOV.HK
  - XML files (traffic speed/volume data)
  - CSV files (detector info, bulk exports)

- **`processed/`** — Cleaned and transformed data files
  - Intermediate outputs for analysis or import

## Usage

1. Download historical CSV/XML files from DATA.GOV.HK and place them in `raw/`
2. Run `scripts/import_historical_data.py` to bulk-load into MySQL
3. Run `scripts/import_detector_info.py` to load detector metadata (CSV)

## Data Sources

- **Strategic Roads:** [Traffic Data - Strategic Major Roads](https://data.gov.hk/en-data/dataset/hk-td-tis_33-traffic-data-traffic-detectors-installed-at-smart-lampposts)
- **Smart Lampposts:** [Traffic Detectors at Smart Lampposts](https://data.gov.hk/en-data/dataset/hk-td-tis_33-traffic-data-traffic-detectors-installed-at-smart-lampposts)
