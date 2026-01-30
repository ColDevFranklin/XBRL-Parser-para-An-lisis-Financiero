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

from backend.signals.signal_detector import SignalDetector

from backend.signals.peer_comparison import (
    PeerBenchmark,
    PeerComparison,
    calculate_percentile,
    compare_to_peers
)

__all__ = [
    # Signal taxonomy
    'SignalType',
    'SignalCategory',
    'Signal',
    'SignalThreshold',
    'SIGNAL_THRESHOLDS',
    'get_threshold',
    'list_thresholds_by_category',

    # Signal detector
    'SignalDetector',

    # Peer comparison
    'PeerBenchmark',
    'PeerComparison',
    'calculate_percentile',
    'compare_to_peers',
]
