# HK Traffic Monitoring — Frontend

React 18 + Leaflet + ECharts frontend for the HK Smart Traffic Monitoring System.

**Owner:** Yunhua WU

## Setup

```bash
# From project root
cd frontend
npm install
npm run dev
```

## Tech Stack

- React 18
- Leaflet (map visualization)
- ECharts (charts and time series)
- [Add other dependencies]

## API Integration

The frontend consumes the ML API (FastAPI) for:

- Anomaly detection results: `GET /api/anomalies`
- Predictions per detector: `GET /api/predictions/{detector_id}`
- Health check: `GET /api/health`

Configure the API base URL in environment variables (e.g., `VITE_API_URL`).

## Structure

```
frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   └── ...
├── package.json
└── ...
```

Create the React app scaffold when ready.
