"""
Feature engineering for ML models.

Rolling statistics, cross-lane features, temporal features.
Placeholder for ML teammate (Yuxin LIU).
"""

import logging

logger = logging.getLogger(__name__)


def compute_rolling_stats(df, window: int):
    """
    Compute rolling mean, std for speed, volume, occupancy.

    Args:
        df: DataFrame with traffic readings.
        window: Rolling window size.

    Returns:
        DataFrame with additional rolling feature columns.
    """
    # TODO: Implement rolling stats
    raise NotImplementedError


def add_cross_lane_features(df):
    """
    Add features derived from multiple lanes (e.g., lane ratio, variance).

    Args:
        df: DataFrame with lane-level data.

    Returns:
        DataFrame with cross-lane features.
    """
    # TODO: Implement cross-lane features
    raise NotImplementedError
