"""
FastAPI app serving ML results.

Endpoints: anomalies, predictions, health.
Placeholder for ML teammate (Yuxin LIU).
"""

import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)

app = FastAPI(
    title="HK Traffic ML API",
    description="ML analysis layer for anomaly detection and traffic prediction",
)


@app.get("/api/health")
def health():
    """Health check endpoint."""
    # TODO: Return {"status": "ok"} or similar
    return {"status": "ok"}


@app.get("/api/anomalies")
def get_anomalies():
    """
    Return anomaly detection results.

    Query params: detector_id, start_time, end_time (optional).
    """
    # TODO: Load model, query data, run inference, return anomalies
    raise NotImplementedError


@app.get("/api/predictions/{detector_id}")
def get_predictions(detector_id: str):
    """
    Return Prophet forecasts for a detector.

    Query params: periods (optional, default 24).
    """
    # TODO: Load model for detector, generate forecast, return
    raise NotImplementedError
