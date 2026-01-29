# backend/signals/__init__.py
"""
Signal Detection Layer - Decision Enablement

Converts raw financial metrics into actionable investment signals
based on Graham/Buffett/Munger methodologies.
"""

from backend.signals.signal_taxonomy import (
    SignalType,
    SignalCategory,
    Signal,
    SignalThreshold,
    SIGNAL_THRESHOLDS,
    get_threshold,
    list_thresholds_by_category
)

__all__ = [
    'SignalType',
    'SignalCategory',
    'Signal',
    'SignalThreshold',
    'SIGNAL_THRESHOLDS',
    'get_threshold',
    'list_thresholds_by_category'
]
