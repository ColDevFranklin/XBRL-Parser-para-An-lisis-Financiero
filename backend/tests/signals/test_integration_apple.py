# backend/tests/signals/test_integration_apple.py
"""
Integration test: XBRL → Metrics → Signals with real Apple data
"""

import pytest
from backend.parsers.multi_file_xbrl_parser import MultiFileXBRLParser
from backend.metrics import calculate_metrics
from backend.signals.signal_detector import SignalDetector


@pytest.fixture
def apple_signals():
    """Load Apple data and generate signals"""
    # Load XBRL data
    parser = MultiFileXBRLParser(ticker='AAPL', data_dir='data')
    timeseries = parser.extract_timeseries(years=4)

    # Calculate metrics
    metrics = calculate_metrics(timeseries, parallel='never')

    # Detect signals
    detector = SignalDetector(metrics, company="AAPL")
    signals = detector.detect_all()

    return signals


def test_apple_has_buy_signals(apple_signals):
    """Apple should have multiple BUY signals (strong company)"""
    buy_signals = apple_signals['buy']

    assert len(buy_signals) >= 3, "Apple should have at least 3 BUY signals"

    # Print for debugging
    print("\n🟢 APPLE BUY SIGNALS:")
    for signal in buy_signals:
        print(f"  - {signal.metric}: {signal.value:.1f} (threshold: {signal.threshold:.1f})")
        if signal.trend:
            print(f"    Trend: {signal.trend}")


def test_apple_has_watch_signals(apple_signals):
    """Apple should have 1-2 WATCH signals (CurrentRatio, possibly DebtToEquity)"""
    watch_signals = apple_signals['watch']

    assert len(watch_signals) >= 1, "Apple should have at least 1 WATCH signal"

    print("\n🟡 APPLE WATCH SIGNALS:")
    for signal in watch_signals:
        print(f"  - {signal.metric}: {signal.value:.2f} (threshold: {signal.threshold:.2f})")
        print(f"    Message: {signal.message}")


def test_apple_no_red_flags(apple_signals):
    """Apple should have ZERO red flags (healthy company)"""
    red_flags = apple_signals['red_flag']

    assert len(red_flags) == 0, f"Apple should have 0 RED_FLAGs, found {len(red_flags)}"


def test_signal_contains_trends(apple_signals):
    """Signals should include trend data for multi-year metrics"""
    all_signals = (
        apple_signals['buy'] +
        apple_signals['watch'] +
        apple_signals['red_flag']
    )

    signals_with_trend = [s for s in all_signals if s.trend is not None]

    assert len(signals_with_trend) >= 3, "Most signals should have trend data"

    print("\n📈 SIGNALS WITH TRENDS:")
    for signal in signals_with_trend[:5]:  # Show first 5
        print(f"  - {signal.metric}: {signal.trend}")


def test_roe_signal_details(apple_signals):
    """Detailed test for ROE signal (Apple's strongest metric)"""
    buy_signals = apple_signals['buy']

    roe_signals = [s for s in buy_signals if s.metric == 'ROE']

    assert len(roe_signals) == 1, "Should have exactly 1 ROE BUY signal"

    roe_signal = roe_signals[0]
    assert roe_signal.value > 100.0, "Apple's ROE should be >100%"
    assert roe_signal.threshold == 15.0, "ROE threshold should be 15%"
    assert roe_signal.trend is not None, "ROE should have trend data"

    print(f"\n✨ APPLE ROE SIGNAL:")
    print(f"  Value: {roe_signal.value:.1f}%")
    print(f"  Threshold: {roe_signal.threshold:.1f}%")
    print(f"  Trend: {roe_signal.trend}")
    print(f"  Message: {roe_signal.message}")


def test_signal_categories(apple_signals):
    """Test that signals span multiple categories"""
    all_signals = (
        apple_signals['buy'] +
        apple_signals['watch'] +
        apple_signals['red_flag']
    )

    categories = set(s.category for s in all_signals)

    assert len(categories) >= 2, "Signals should span at least 2 categories"

    print("\n📊 SIGNAL CATEGORIES:")
    for category in categories:
        count = sum(1 for s in all_signals if s.category == category)
        print(f"  - {category.value}: {count} signals")


def test_full_pipeline_performance(apple_signals):
    """Test that full pipeline completes in reasonable time"""
    import time

    start = time.time()

    # Re-run full pipeline
    parser = MultiFileXBRLParser(ticker='AAPL', data_dir='data')
    timeseries = parser.extract_timeseries(years=4)
    metrics = calculate_metrics(timeseries, parallel='never')
    detector = SignalDetector(metrics, company="AAPL")
    signals = detector.detect_all()

    elapsed = time.time() - start

    print(f"\n⏱️  Full Pipeline Time: {elapsed:.2f}s")
    print(f"  - XBRL Parsing: included")
    print(f"  - Metrics Calculation: included")
    print(f"  - Signal Detection: included")

    assert elapsed < 10.0, f"Pipeline too slow: {elapsed:.2f}s"
