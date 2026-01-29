# backend/tests/signals/test_signal_thresholds.py
"""Tests for signal threshold definitions and helper functions"""

import pytest
from backend.signals.signal_taxonomy import (
    SignalType,
    SignalCategory,
    SIGNAL_THRESHOLDS,
    get_threshold,
    list_thresholds_by_category
)


def test_threshold_count():
    """Verify we have exactly 15 thresholds defined"""
    assert len(SIGNAL_THRESHOLDS) == 15, "Should have 15 signal thresholds"


def test_buy_signals_count():
    """Verify 5 BUY signal thresholds"""
    buy_thresholds = [
        t for t in SIGNAL_THRESHOLDS.values()
        if t.buy_threshold is not None
    ]
    assert len(buy_thresholds) == 5, "Should have 5 BUY signal thresholds"


def test_watch_signals_count():
    """Verify 5 WATCH signal thresholds"""
    watch_thresholds = [
        t for t in SIGNAL_THRESHOLDS.values()
        if t.watch_threshold is not None
    ]
    assert len(watch_thresholds) == 5, "Should have 5 WATCH signal thresholds"


def test_red_flag_signals_count():
    """Verify 5 RED_FLAG signal thresholds"""
    red_flag_thresholds = [
        t for t in SIGNAL_THRESHOLDS.values()
        if t.red_flag_threshold is not None
    ]
    assert len(red_flag_thresholds) == 5, "Should have 5 RED_FLAG signal thresholds"


def test_all_thresholds_have_justification():
    """Verify every threshold has a non-empty justification"""
    for key, threshold in SIGNAL_THRESHOLDS.items():
        assert threshold.justification, f"Threshold {key} missing justification"
        assert len(threshold.justification) > 20, f"Threshold {key} justification too short"


def test_get_threshold_buy_signal():
    """Test get_threshold for BUY signal"""
    threshold = get_threshold("ROE", SignalType.BUY)
    assert threshold is not None
    assert threshold.metric_name == "ROE"
    assert threshold.buy_threshold == 15.0
    assert "Graham" in threshold.justification


def test_get_threshold_watch_signal():
    """Test get_threshold for WATCH signal"""
    threshold = get_threshold("CurrentRatio", SignalType.WATCH)
    assert threshold is not None
    assert threshold.metric_name == "CurrentRatio"
    assert threshold.watch_threshold == 1.0


def test_get_threshold_red_flag_signal():
    """Test get_threshold for RED_FLAG signal"""
    threshold = get_threshold("InterestCoverage", SignalType.RED_FLAG)
    assert threshold is not None
    assert threshold.metric_name == "InterestCoverage"
    assert threshold.red_flag_threshold == 3.0


def test_get_threshold_not_found():
    """Test get_threshold returns None for non-existent metric"""
    threshold = get_threshold("FakeMetric", SignalType.BUY)
    assert threshold is None


def test_list_thresholds_profitability():
    """Test listing thresholds for profitability category"""
    thresholds = list_thresholds_by_category(SignalCategory.PROFITABILITY)
    assert len(thresholds) >= 3, "Should have at least 3 profitability thresholds"

    metric_names = [t.metric_name for t in thresholds]
    assert "ROE" in metric_names
    assert "NetMargin" in metric_names or "GrossMargin" in metric_names


def test_list_thresholds_liquidity():
    """Test listing thresholds for liquidity category"""
    thresholds = list_thresholds_by_category(SignalCategory.LIQUIDITY)
    assert len(thresholds) >= 1, "Should have at least 1 liquidity threshold"

    metric_names = [t.metric_name for t in thresholds]
    assert "CurrentRatio" in metric_names


def test_list_thresholds_efficiency():
    """Test listing thresholds for efficiency category"""
    thresholds = list_thresholds_by_category(SignalCategory.EFFICIENCY)
    assert len(thresholds) >= 1, "Should have at least 1 efficiency threshold"


def test_list_thresholds_leverage():
    """Test listing thresholds for leverage category"""
    thresholds = list_thresholds_by_category(SignalCategory.LEVERAGE)
    assert len(thresholds) >= 2, "Should have at least 2 leverage thresholds"

    metric_names = [t.metric_name for t in thresholds]
    assert "DebtToEquity" in metric_names or "InterestCoverage" in metric_names


def test_threshold_comparison_operators():
    """Verify comparison operators are valid"""
    valid_operators = [">", "<", "between", ">=", "<="]

    for key, threshold in SIGNAL_THRESHOLDS.items():
        assert threshold.comparison in valid_operators, \
            f"Threshold {key} has invalid comparison operator: {threshold.comparison}"


def test_roe_strong_threshold_details():
    """Detailed test for ROE strong buy signal"""
    threshold = SIGNAL_THRESHOLDS["roe_strong"]

    assert threshold.metric_name == "ROE"
    assert threshold.buy_threshold == 15.0
    assert threshold.comparison == ">"
    assert "Graham" in threshold.justification
    assert "moat" in threshold.justification.lower()
