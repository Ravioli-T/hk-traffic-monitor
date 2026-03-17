"""
Prophet-based traffic prediction.

Trains Prophet models for speed/volume forecasting per detector.
Placeholder for ML teammate (Yuxin LIU).
"""

import logging

logger = logging.getLogger(__name__)


def train_prophet_model(historical_data, target_column: str):
    """
    Train Prophet model for time series forecasting.

    Args:
        historical_data: DataFrame with ds (datetime) and target column.
        target_column: Column to predict (e.g., 'speed', 'volume').

    Returns:
        Trained Prophet model.
    """
    # TODO: Implement Prophet training
    raise NotImplementedError


def forecast(model, periods: int):
    """
    Generate forecasts for future periods.

    Args:
        model: Trained Prophet model.
        periods: Number of periods to forecast.

    Returns:
        DataFrame with forecasted values.
    """
    # TODO: Implement forecasting
    raise NotImplementedError
