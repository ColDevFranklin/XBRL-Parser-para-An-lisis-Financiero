"""
Tests for StatisticalBenchmarkEngine - Franklin Framework Layer 2

Tests dynamic benchmark calculation from real sector data.
"""

import pytest
import numpy as np
from backend.signals.statistical_engine import (
    IndustryBenchmark,
    StatisticalBenchmarkEngine,
)


@pytest.fixture
def mock_sector_data():
    """
    Mock sector data for testing (5 tech companies)

    Simulates output from generate_sector_benchmarks()
    """
    return {
        'AAPL': {
            'profitability': {
                'ROE': np.array([151.9, 164.6, 156.1, 197.0]),
                'NetMargin': np.array([26.9, 24.0, 25.3, 25.3]),
                'ROIC': np.array([45.2, 43.8, 41.7, 48.1]),
            },
            'liquidity': {
                'CurrentRatio': np.array([0.89, 1.07, 0.94, 1.07]),
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
        'META': {
            'profitability': {
                'ROE': np.array([24.1, 23.1, 31.3, 36.7]),
                'NetMargin': np.array([29.1, 20.2, 23.2, 35.3]),
                'ROIC': np.array([19.2, 17.8, 24.3, 29.8]),
            },
            'liquidity': {
                'CurrentRatio': np.array([2.45, 2.89, 3.12, 3.45]),
            },
            'leverage': {
                'DebtToEquity': np.array([0.00, 0.00, 0.00, 0.00]),
            },
        },
        'NVDA': {
            'profitability': {
                'ROE': np.array([35.6, 45.8, 74.2, 123.8]),
                'NetMargin': np.array([30.2, 36.2, 49.8, 55.0]),
                'ROIC': np.array([27.1, 35.4, 58.9, 98.7]),
            },
            'liquidity': {
                'CurrentRatio': np.array([4.89, 5.12, 3.89, 4.56]),
            },
            'leverage': {
                'DebtToEquity': np.array([0.34, 0.31, 0.23, 0.18]),
            },
        },
    }


class TestIndustryBenchmark:
    """Test IndustryBenchmark dataclass"""

    def test_benchmark_initialization(self):
        """Test creating IndustryBenchmark"""
        benchmark = IndustryBenchmark(
            metric_name='ROE',
            p10=10.0,
            p25=20.0,
            p50=30.0,
            p75=40.0,
            p90=50.0,
            mean=32.5,
            std=12.3,
            sample_size=20
        )

        assert benchmark.metric_name == 'ROE'
        assert benchmark.p50 == 30.0
        assert benchmark.p75 == 40.0
        assert benchmark.sample_size == 20

    def test_benchmark_repr(self):
        """Test string representation"""
        benchmark = IndustryBenchmark(
            metric_name='NetMargin',
            p10=5.0, p25=10.0, p50=20.0, p75=30.0, p90=40.0,
            mean=22.0, std=8.5, sample_size=15
        )

        repr_str = repr(benchmark)
        assert 'NetMargin' in repr_str
        assert 'P50=20.0' in repr_str
        assert 'n=15' in repr_str


class TestStatisticalBenchmarkEngine:
    """Test StatisticalBenchmarkEngine"""

    def test_initialization(self, mock_sector_data):
        """Test engine initialization"""
        engine = StatisticalBenchmarkEngine(mock_sector_data)

        assert engine.sector_data == mock_sector_data
        assert engine._benchmarks_cache == {}

    def test_calculate_benchmarks_roe(self, mock_sector_data):
        """Test ROE benchmark calculation"""
        engine = StatisticalBenchmarkEngine(mock_sector_data)

        benchmark = engine.calculate_benchmarks('profitability', 'ROE')

        # Should get benchmark from 5 companies (latest year values)
        # AAPL: 197.0, MSFT: 32.8, GOOGL: 29.2, META: 36.7, NVDA: 123.8
        assert benchmark is not None
        assert benchmark.metric_name == 'ROE'
        assert benchmark.sample_size == 5

        # Check percentiles are calculated
        assert benchmark.p10 < benchmark.p25 < benchmark.p50 < benchmark.p75 < benchmark.p90

        # P50 should be around median of [29.2, 32.8, 36.7, 123.8, 197.0] = 36.7
        assert 30.0 < benchmark.p50 < 40.0

    def test_calculate_benchmarks_net_margin(self, mock_sector_data):
        """Test NetMargin benchmark calculation"""
        engine = StatisticalBenchmarkEngine(mock_sector_data)

        benchmark = engine.calculate_benchmarks('profitability', 'NetMargin')

        # Latest year: AAPL: 25.3, MSFT: 36.0, GOOGL: 27.6, META: 35.3, NVDA: 55.0
        assert benchmark is not None
        assert benchmark.sample_size == 5

        # P50 should be around 35.3
        assert 30.0 < benchmark.p50 < 40.0

    def test_calculate_benchmarks_caching(self, mock_sector_data):
        """Test that results are cached"""
        engine = StatisticalBenchmarkEngine(mock_sector_data)

        # First call
        benchmark1 = engine.calculate_benchmarks('profitability', 'ROE')

        # Second call (should use cache)
        benchmark2 = engine.calculate_benchmarks('profitability', 'ROE')

        # Should be the same object
        assert benchmark1 is benchmark2

        # Check cache
        assert 'profitability:ROE' in engine._benchmarks_cache

    def test_calculate_benchmarks_insufficient_data(self, mock_sector_data):
        """Test with insufficient companies"""
        # Create minimal data (only 2 companies)
        minimal_data = {
            'AAPL': mock_sector_data['AAPL'],
            'MSFT': mock_sector_data['MSFT'],
        }

        engine = StatisticalBenchmarkEngine(minimal_data)
        benchmark = engine.calculate_benchmarks('profitability', 'ROE')

        # Should return None (< 3 companies required)
        assert benchmark is None

    def test_calculate_benchmarks_missing_metric(self, mock_sector_data):
        """Test metric that doesn't exist"""
        engine = StatisticalBenchmarkEngine(mock_sector_data)

        benchmark = engine.calculate_benchmarks('profitability', 'NonExistentMetric')

        assert benchmark is None

    def test_calculate_benchmarks_nan_handling(self):
        """Test that NaN values are filtered out"""
        data_with_nan = {
            'AAPL': {
                'profitability': {
                    'ROE': np.array([10.0, 20.0, 30.0, 40.0]),
                }
            },
            'MSFT': {
                'profitability': {
                    'ROE': np.array([15.0, 25.0, 35.0, np.nan]),  # NaN in latest
                }
            },
            'GOOGL': {
                'profitability': {
                    'ROE': np.array([12.0, 22.0, 32.0, 42.0]),
                }
            },
            'META': {
                'profitability': {
                    'ROE': np.array([14.0, 24.0, 34.0, 44.0]),
                }
            },
        }

        engine = StatisticalBenchmarkEngine(data_with_nan)
        benchmark = engine.calculate_benchmarks('profitability', 'ROE')

        # Should use AAPL (40.0), GOOGL (42.0), META (44.0), excluding MSFT's NaN
        assert benchmark is not None
        assert benchmark.sample_size == 3  # 3 valid values (MSFT excluded due to NaN)

    def test_calculate_all_benchmarks(self, mock_sector_data):
        """Test calculating all benchmarks at once"""
        engine = StatisticalBenchmarkEngine(mock_sector_data)

        all_benchmarks = engine.calculate_all_benchmarks()

        # Should have benchmarks for all categories
        assert 'profitability' in all_benchmarks
        assert 'liquidity' in all_benchmarks
        assert 'leverage' in all_benchmarks

        # Check profitability metrics
        assert 'ROE' in all_benchmarks['profitability']
        assert 'NetMargin' in all_benchmarks['profitability']
        assert 'ROIC' in all_benchmarks['profitability']

        # Check that each is an IndustryBenchmark
        roe_bench = all_benchmarks['profitability']['ROE']
        assert isinstance(roe_bench, IndustryBenchmark)
        assert roe_bench.sample_size == 5

    def test_get_signal_threshold_buy(self, mock_sector_data):
        """Test getting BUY threshold (P75)"""
        engine = StatisticalBenchmarkEngine(mock_sector_data)

        threshold = engine.get_signal_threshold('profitability', 'ROE', 'BUY')

        # Should return P75
        benchmark = engine.calculate_benchmarks('profitability', 'ROE')
        assert threshold == benchmark.p75

    def test_get_signal_threshold_watch(self, mock_sector_data):
        """Test getting WATCH threshold (P50)"""
        engine = StatisticalBenchmarkEngine(mock_sector_data)

        threshold = engine.get_signal_threshold('profitability', 'ROE', 'WATCH')

        # Should return P50
        benchmark = engine.calculate_benchmarks('profitability', 'ROE')
        assert threshold == benchmark.p50

    def test_get_signal_threshold_red_flag(self, mock_sector_data):
        """Test getting RED_FLAG threshold (P25)"""
        engine = StatisticalBenchmarkEngine(mock_sector_data)

        threshold = engine.get_signal_threshold('profitability', 'ROE', 'RED_FLAG')

        # Should return P25
        benchmark = engine.calculate_benchmarks('profitability', 'ROE')
        assert threshold == benchmark.p25

    def test_get_signal_threshold_invalid_type(self, mock_sector_data):
        """Test invalid signal type"""
        engine = StatisticalBenchmarkEngine(mock_sector_data)

        threshold = engine.get_signal_threshold('profitability', 'ROE', 'INVALID')

        assert threshold is None


class TestStatisticalEngineEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_sector_data(self):
        """Test with empty sector data"""
        engine = StatisticalBenchmarkEngine({})

        benchmark = engine.calculate_benchmarks('profitability', 'ROE')
        assert benchmark is None

        all_benchmarks = engine.calculate_all_benchmarks()
        assert all_benchmarks == {}

    def test_single_company(self):
        """Test with only one company (should fail min requirement)"""
        single_company = {
            'AAPL': {
                'profitability': {
                    'ROE': np.array([10.0, 20.0, 30.0, 40.0]),
                }
            }
        }

        engine = StatisticalBenchmarkEngine(single_company)
        benchmark = engine.calculate_benchmarks('profitability', 'ROE')

        # Should return None (< 3 companies)
        assert benchmark is None

    def test_all_nan_values(self):
        """Test when all companies have NaN for a metric"""
        all_nan_data = {
            'AAPL': {
                'profitability': {
                    'ROE': np.array([10.0, 20.0, 30.0, np.nan]),
                }
            },
            'MSFT': {
                'profitability': {
                    'ROE': np.array([15.0, 25.0, 35.0, np.nan]),
                }
            },
            'GOOGL': {
                'profitability': {
                    'ROE': np.array([12.0, 22.0, 32.0, np.nan]),
                }
            },
        }

        engine = StatisticalBenchmarkEngine(all_nan_data)
        benchmark = engine.calculate_benchmarks('profitability', 'ROE')

        # Should return None (no valid values)
        assert benchmark is None


def test_benchmark_calculation_performance(mock_sector_data):
    """Test that benchmark calculation is fast"""
    import time

    engine = StatisticalBenchmarkEngine(mock_sector_data)

    start = time.time()
    all_benchmarks = engine.calculate_all_benchmarks()
    elapsed = time.time() - start

    # Should complete in < 100ms
    assert elapsed < 0.1
    assert len(all_benchmarks) > 0
