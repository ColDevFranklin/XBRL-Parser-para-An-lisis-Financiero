"""
backend/signals/_init_.py
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
# Franklin Framework - Statistical Engine
from backend.signals.statistical_engine import (
    IndustryBenchmark,
    StatisticalBenchmarkEngine,
)
# Franklin Framework - Interpretation Engine
from backend.signals.franklin_interpretation import (
    PerformanceZone,
    FranklinInterpretation,
)
# Story Arc Generator - Narrative Intelligence
from backend.signals.story_generator import (
    StoryPattern,
    ConfidenceLevel,
    StoryArc,
    StoryGenerator,
    STORY_TEMPLATES,
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
    # Franklin Framework - Statistical
    'IndustryBenchmark',
    'StatisticalBenchmarkEngine',
    # Franklin Framework - Interpretation
    'PerformanceZone',
    'FranklinInterpretation',
    # Story Arc Generator
    'StoryPattern',
    'ConfidenceLevel',
    'StoryArc',
    'StoryGenerator',
    'STORY_TEMPLATES',
]
