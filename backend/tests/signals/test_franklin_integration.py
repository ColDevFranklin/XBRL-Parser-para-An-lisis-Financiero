"""
Integration Tests for Franklin Framework

Tests complete flow: sector data → benchmarks → signals/peers
"""

import pytest
import numpy as np
from backend.signals.statistical_engine import StatisticalBenchmarkEngine
from backend.signals.franklin_interpretation import FranklinInterpretation
from backend.signals.signal_detector import SignalDetector
from backend.signals.peer_comparison import compare_to_peers


@pytest.fixture
def tech_sector_data():
    """Real-ish tech sector data for integration testing"""
    return {
        'AAPL': {
            'profitability': {
                'ROE': np.array([151.9, 164.6, 156.1, 197.0]),
                'NetMargin': np.array([26.9, 24.0, 25.3, 25.3]),
                'ROIC': np.array([45.2, 43.8, 41.7, 80.2]),
            },
            'liquidity': {
                'CurrentRatio': np.array([0.89, 1.07, 0.94, 0.87]),
            },
            'leverage': {
                'DebtToEquity': np.array([1.78, 1.96, 1.73, 1.55]),
            },
        },
        'MSFT': {
            'profitability': {
                'ROE': np.array([42.6, 43.0, 38.3, 32.8]),
                'NetMargin': np.array([31.6, 36.7, 34.1, 36.0]),
                'ROIC': np.array([28.4, 30.2, 27.9, 34.9]),
            },
            'liquidity': {
                'CurrentRatio': np.array([2.23, 1.78, 1.77, 1.27]),
            },
            'leverage': {
                'DebtToEquity': np.array([0.45, 0.41, 0.35, 0.29]),
            },
        },
        'GOOGL': {
            'profitability': {
                'ROE': np.array([18.2, 20.6, 26.3, 29.2]),
                'NetMargin': np.array([21.2, 21.1, 20.6, 27.6]),
                'ROIC': np.array([14.5, 16.2, 20.1, 23.4]),
            },
            'liquidity': {
                'CurrentRatio': np.array([3.01, 2.93, 2.51, 2.89]),
            },
            'leverage': {
                'DebtToEquity': np.array([0.08, 0.07, 0.05, 0.04]),
            },
        },
    }


class TestFranklinFrameworkIntegration:
    """Integration tests for complete Franklin Framework"""

    def test_end_to_end_benchmark_calculation(self, tech_sector_data):
        """Test complete flow: data → engine → benchmarks"""
        engine = StatisticalBenchmarkEngine(tech_sector_data)
        all_benchmarks = engine.calculate_all_benchmarks()

        assert 'profitability' in all_benchmarks
        assert 'ROE' in all_benchmarks['profitability']

        roe_bench = all_benchmarks['profitability']['ROE']
        assert roe_bench.sample_size == 3
        assert roe_bench.p25 < roe_bench.p50 < roe_bench.p75

    def test_signal_detection_with_franklin(self, tech_sector_data):
        """Test SignalDetector using Franklin Framework"""
        engine = StatisticalBenchmarkEngine(tech_sector_data)
        aapl_metrics = tech_sector_data['AAPL']

        detector = SignalDetector(
            metrics=aapl_metrics,
            company='AAPL',
            benchmark_engine=engine
        )

        signals = detector.detect_all()

        assert 'buy' in signals
        assert 'watch' in signals
        assert 'red_flag' in signals

        # AAPL ROE first value is 151.9 (signals use index 0)
        buy_signals = signals['buy']
        roe_signals = [s for s in buy_signals if s.metric == 'ROE']

        # Should have ROE signal (151.9 is still strong vs sector)
        assert len(roe_signals) > 0
        assert roe_signals[0].value == 151.9  # First element of array

    def test_peer_comparison_with_franklin(self, tech_sector_data):
        """Test peer comparison using Franklin Framework"""
        engine = StatisticalBenchmarkEngine(tech_sector_data)

        aapl_metrics = tech_sector_data['AAPL']
        peer_metrics = {
            'MSFT': tech_sector_data['MSFT'],
            'GOOGL': tech_sector_data['GOOGL'],
        }

        benchmarks = compare_to_peers(
            company_metrics=aapl_metrics,
            peer_metrics=peer_metrics,
            company_name='AAPL',
            benchmark_engine=engine
        )

        assert 'profitability' in benchmarks

        roe_bench = next(
            b for b in benchmarks['profitability']
            if b.metric_name == 'ROE'
        )

        # AAPL ROE (197.0 - latest year) should beat peers
        assert roe_bench.beats_peers is True
        assert roe_bench.percentile >= 50
        assert roe_bench.sector_benchmark is not None


def test_franklin_framework_performance(tech_sector_data):
    """Test that Franklin Framework maintains good performance"""
    import time

    engine = StatisticalBenchmarkEngine(tech_sector_data)

    start = time.time()

    all_benchmarks = engine.calculate_all_benchmarks()

    detector = SignalDetector(
        metrics=tech_sector_data['AAPL'],
        company='AAPL',
        benchmark_engine=engine
    )
    signals = detector.detect_all()

    benchmarks = compare_to_peers(
        company_metrics=tech_sector_data['AAPL'],
        peer_metrics={'MSFT': tech_sector_data['MSFT']},
        company_name='AAPL',
        benchmark_engine=engine
    )

    elapsed = time.time() - start

    # Should complete in < 500ms
    assert elapsed < 0.5
    assert len(all_benchmarks) > 0
    assert len(signals['buy']) + len(signals['watch']) + len(signals['red_flag']) > 0
    assert len(benchmarks) > 0
