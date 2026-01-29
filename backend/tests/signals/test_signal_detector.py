# backend/tests/signals/test_signal_detector.py
"""Tests for SignalDetector core logic"""

import pytest
import numpy as np
from backend.signals.signal_detector import SignalDetector
from backend.signals.signal_taxonomy import SignalType, SignalCategory


@pytest.fixture
def mock_metrics_strong():
    """Mock metrics showing strong company (Apple-like)"""
    return {
        'profitability': {
            'ROE': np.array([151.9, 164.6, 156.1, 196.9]),  # Strong, above 15%
            'NetMargin': np.array([26.9, 24.0, 25.3, 25.3]),  # Above 20%
            'ROIC': np.array([45.2, 42.1, 40.3, 38.9]),  # Well above 12%
            'OCFMargin': np.array([31.5, 30.2, 29.8, 28.5]),  # Above 25%
            'GrossMargin': np.array([46.9, 46.2, 44.1, 43.3])  # Above 30%
        },
        'liquidity': {
            'CurrentRatio': np.array([0.89, 0.87, 0.99, 0.88])  # Below 1.0 (WATCH)
        },
        'efficiency': {
            'AssetTurnover': np.array([1.16, 1.07, 1.09, 1.12]),  # Above 1.0
            'InventoryTurnover': np.array([40.5, 38.2, 36.8, 35.1]),  # High
            'DSO': np.array([35.2, 31.4, 28.1, 26.3])  # Below 60
        },
        'leverage': {
            'DebtToEquity': np.array([1.23, 1.70, 1.69, 1.95]),  # Above 1.5 (WATCH)
            'DebtToAssets': np.array([0.32, 0.35, 0.34, 0.36]),  # Below 0.7
            'InterestCoverage': np.array([25.3, 29.1, 40.8, 45.2])  # Above 3.0
        }
    }


@pytest.fixture
def mock_metrics_distressed():
    """Mock metrics showing distressed company"""
    return {
        'profitability': {
            'ROE': np.array([5.2, 6.1, 7.8, 9.2]),  # Below 8% (RED_FLAG)
            'NetMargin': np.array([3.5, 4.2, 5.1, 6.8]),  # Below 20%
            'OCFMargin': np.array([-2.1, -1.5, 0.5, 1.2])  # Negative (RED_FLAG)
        },
        'liquidity': {
            'CurrentRatio': np.array([0.45, 0.52, 0.61, 0.73])  # Below 0.5 (RED_FLAG)
        },
        'leverage': {
            'DebtToEquity': np.array([3.5, 3.2, 2.8, 2.5]),  # High
            'DebtToAssets': np.array([0.75, 0.72, 0.68, 0.65]),  # Above 0.7 (RED_FLAG)
            'InterestCoverage': np.array([1.8, 2.1, 2.5, 2.9])  # Below 3.0 (RED_FLAG)
        }
    }


def test_detector_initialization():
    """Test SignalDetector initialization"""
    metrics = {'profitability': {'ROE': np.array([15.0])}}
    detector = SignalDetector(metrics, company="TEST")

    assert detector.company == "TEST"
    assert detector.metrics == metrics
    assert detector._signals_cache is None


def test_detect_all_strong_company(mock_metrics_strong):
    """Test detect_all with strong company metrics (Apple-like)"""
    detector = SignalDetector(mock_metrics_strong, company="AAPL")
    signals = detector.detect_all()

    # Should have BUY signals
    assert len(signals['buy']) >= 5, "Strong company should have multiple BUY signals"

    # Should have some WATCH signals (CurrentRatio, DebtToEquity)
    assert len(signals['watch']) >= 1, "Should have at least 1 WATCH signal"

    # Should have NO red flags
    assert len(signals['red_flag']) == 0, "Strong company should have no RED_FLAG signals"


def test_detect_all_distressed_company(mock_metrics_distressed):
    """Test detect_all with distressed company metrics"""
    detector = SignalDetector(mock_metrics_distressed, company="DIST")
    signals = detector.detect_all()

    # Should have RED_FLAG signals
    assert len(signals['red_flag']) >= 3, "Distressed company should have multiple RED_FLAGS"

    # Should have NO buy signals
    assert len(signals['buy']) == 0, "Distressed company should have no BUY signals"


def test_detect_profitability_buy_signals(mock_metrics_strong):
    """Test profitability BUY signal detection"""
    detector = SignalDetector(mock_metrics_strong, company="AAPL")
    signals = detector.detect_profitability_signals(SignalType.BUY)

    # Should detect ROE, NetMargin, ROIC, OCFMargin
    assert len(signals) >= 4

    metric_names = [s.metric for s in signals]
    assert 'ROE' in metric_names
    assert 'NetMargin' in metric_names
    assert 'ROIC' in metric_names


def test_detect_liquidity_watch_signals(mock_metrics_strong):
    """Test liquidity WATCH signal detection"""
    detector = SignalDetector(mock_metrics_strong, company="AAPL")
    signals = detector.detect_liquidity_signals(SignalType.WATCH)

    # CurrentRatio 0.89 < 1.0 should trigger WATCH
    assert len(signals) == 1
    assert signals[0].metric == 'CurrentRatio'
    assert signals[0].type == SignalType.WATCH


def test_detect_leverage_red_flags(mock_metrics_distressed):
    """Test leverage RED_FLAG signal detection"""
    detector = SignalDetector(mock_metrics_distressed, company="DIST")
    signals = detector.detect_leverage_signals(SignalType.RED_FLAG)

    # Should detect DebtToAssets and InterestCoverage red flags
    assert len(signals) >= 2

    metric_names = [s.metric for s in signals]
    assert 'DebtToAssets' in metric_names or 'InterestCoverage' in metric_names


def test_signal_contains_trend():
    """Test that signals include trend calculation"""
    metrics = {
        'profitability': {
            'ROE': np.array([20.0, 18.0, 16.0, 15.0])  # Declining but above threshold
        }
    }

    detector = SignalDetector(metrics, company="TEST")
    signals = detector.detect_profitability_signals(SignalType.BUY)

    assert len(signals) == 1
    assert signals[0].trend is not None
    assert "CAGR" in signals[0].trend


def test_calculate_trend_positive():
    """Test CAGR calculation for positive trend"""
    metrics = {'profitability': {'ROE': np.array([100.0])}}
    detector = SignalDetector(metrics, company="TEST")

    values = np.array([120.0, 110.0, 100.0])  # +10% annual growth
    trend = detector._calculate_trend(values)

    assert "+9" in trend or "+10" in trend  # ~9.5% CAGR
    assert "CAGR" in trend


def test_calculate_trend_negative():
    """Test CAGR calculation for negative trend"""
    metrics = {'profitability': {'ROE': np.array([100.0])}}
    detector = SignalDetector(metrics, company="TEST")

    values = np.array([80.0, 90.0, 100.0])  # -10% annual decline
    trend = detector._calculate_trend(values)

    assert "-" in trend
    assert "CAGR" in trend


def test_generate_message_buy_signal():
    """Test message generation for BUY signal"""
    metrics = {'profitability': {'ROE': np.array([100.0])}}
    detector = SignalDetector(metrics, company="TEST")

    message = detector._generate_message(
        metric_name="ROE",
        current_value=25.5,
        threshold=15.0,
        comparison=">",
        signal_type=SignalType.BUY
    )

    assert "ROE" in message
    assert "25.5%" in message
    assert "15.0%" in message
    assert "positive" in message.lower()


def test_cache_functionality(mock_metrics_strong):
    """Test that detect_all caches results"""
    detector = SignalDetector(mock_metrics_strong, company="AAPL")

    # First call
    signals1 = detector.detect_all()
    assert detector._signals_cache is not None

    # Second call should return cached version
    signals2 = detector.detect_all()
    assert signals1 is signals2  # Same object reference


def test_empty_metrics():
    """Test detector with empty metrics"""
    detector = SignalDetector({}, company="EMPTY")
    signals = detector.detect_all()

    assert len(signals['buy']) == 0
    assert len(signals['watch']) == 0
    assert len(signals['red_flag']) == 0


def test_nan_values_ignored():
    """Test that NaN values don't trigger signals"""
    metrics = {
        'profitability': {
            'ROE': np.array([np.nan, 20.0, 18.0])  # NaN should be ignored
        }
    }

    detector = SignalDetector(metrics, company="TEST")
    signals = detector.detect_profitability_signals(SignalType.BUY)

    assert len(signals) == 0  # NaN value should not trigger signal
