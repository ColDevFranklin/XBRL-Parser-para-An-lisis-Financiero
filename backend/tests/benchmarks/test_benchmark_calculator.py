"""
Tests for Benchmark Calculator

Validates statistical calculation engine for industry benchmarks.

Usage:
    python3 -m pytest backend/tests/benchmarks/test_benchmark_calculator.py -v
"""

import pytest
import numpy as np
from pathlib import Path
import json

from backend.benchmarks.benchmark_calculator import (
    BenchmarkCalculator,
    MetricBenchmark,
    calculate_percentile
)


class TestMetricBenchmark:
    """Test MetricBenchmark dataclass"""

    def test_metric_benchmark_creation(self):
        """Should create MetricBenchmark with all fields"""
        benchmark = MetricBenchmark(
            metric_name="ROE",
            avg=42.3,
            median=38.5,
            stddev=15.1,
            p25=28.2,
            p75=52.8,
            p10=18.5,
            p90=68.2,
            sample_size=74,
            min_value=5.2,
            max_value=195.3
        )

        assert benchmark.metric_name == "ROE"
        assert benchmark.avg == 42.3
        assert benchmark.median == 38.5
        assert benchmark.sample_size == 74


class TestCalculatePercentile:
    """Test percentile calculation logic"""

    @pytest.fixture
    def sample_benchmark(self):
        """Sample benchmark for testing"""
        return MetricBenchmark(
            metric_name="ROE",
            avg=42.3,
            median=50.0,  # p50
            stddev=15.1,
            p25=30.0,
            p75=60.0,
            p10=20.0,
            p90=80.0,
            sample_size=100,
            min_value=10.0,
            max_value=150.0
        )

    def test_percentile_at_median(self, sample_benchmark):
        """Value at median should return ~50th percentile"""
        percentile = calculate_percentile(50.0, sample_benchmark)
        assert 48 <= percentile <= 52  # Allow small margin

    def test_percentile_at_p25(self, sample_benchmark):
        """Value at p25 should return ~25th percentile"""
        percentile = calculate_percentile(30.0, sample_benchmark)
        assert 23 <= percentile <= 27

    def test_percentile_at_p75(self, sample_benchmark):
        """Value at p75 should return ~75th percentile"""
        percentile = calculate_percentile(60.0, sample_benchmark)
        assert 73 <= percentile <= 77

    def test_percentile_below_p10(self, sample_benchmark):
        """Value below p10 should return 10"""
        percentile = calculate_percentile(15.0, sample_benchmark)
        assert percentile == 10

    def test_percentile_above_p90(self, sample_benchmark):
        """Value above p90 should return 90"""
        percentile = calculate_percentile(100.0, sample_benchmark)
        assert percentile == 90

    def test_percentile_interpolation(self, sample_benchmark):
        """Value between percentiles should interpolate"""
        # 40 is between p25 (30) and median (50)
        percentile = calculate_percentile(40.0, sample_benchmark)
        assert 35 <= percentile <= 45


class TestBenchmarkCalculator:
    """Test BenchmarkCalculator class"""

    def test_calculator_initialization(self):
        """Should initialize with data_dir and years"""
        calculator = BenchmarkCalculator(data_dir='data', years=4)

        assert calculator.data_dir == Path('data')
        assert calculator.years == 4
        assert calculator._metrics_cache == {}

    def test_calculate_company_metrics_apple(self):
        """Should calculate metrics for Apple (if data available)"""
        calculator = BenchmarkCalculator(data_dir='data', years=4)

        # This will only pass if Apple XBRL data exists
        try:
            metrics = calculator._calculate_company_metrics('AAPL')

            if metrics is not None:
                assert 'profitability' in metrics
                assert 'liquidity' in metrics
                assert 'ROE' in metrics['profitability']

                # Should cache result
                assert 'AAPL' in calculator._metrics_cache
        except FileNotFoundError:
            pytest.skip("Apple XBRL data not available")

    def test_calculate_company_metrics_invalid(self):
        """Should return None for non-existent ticker"""
        calculator = BenchmarkCalculator(data_dir='data', years=4)

        metrics = calculator._calculate_company_metrics('INVALID')
        assert metrics is None

    def test_aggregate_statistics_empty(self):
        """Should handle empty metrics list"""
        calculator = BenchmarkCalculator()

        benchmarks = calculator._aggregate_statistics([])
        assert benchmarks == {}

    def test_aggregate_statistics_mock_data(self):
        """Should aggregate statistics from mock data"""
        calculator = BenchmarkCalculator()

        # Mock metrics for 3 companies
        mock_metrics = [
            {
                'profitability': {
                    'ROE': np.array([30.0, 28.0, 27.0, 26.0]),
                    'NetMargin': np.array([15.0, 14.5, 14.0, 13.5])
                }
            },
            {
                'profitability': {
                    'ROE': np.array([50.0, 48.0, 47.0, 46.0]),
                    'NetMargin': np.array([25.0, 24.5, 24.0, 23.5])
                }
            },
            {
                'profitability': {
                    'ROE': np.array([40.0, 38.0, 37.0, 36.0]),
                    'NetMargin': np.array([20.0, 19.5, 19.0, 18.5])
                }
            }
        ]

        benchmarks = calculator._aggregate_statistics(mock_metrics)

        # Check ROE benchmark
        assert 'ROE' in benchmarks
        roe = benchmarks['ROE']

        assert roe.median == 40.0  # Middle value
        assert roe.avg == 40.0  # (30 + 50 + 40) / 3
        assert roe.min_value == 30.0
        assert roe.max_value == 50.0
        assert roe.sample_size == 3


class TestBenchmarkExportImport:
    """Test JSON export/import functionality"""

    def test_export_and_load_benchmarks(self, tmp_path):
        """Should export and reload benchmarks correctly"""
        # Create sample benchmarks
        benchmarks = {
            'ROE': MetricBenchmark(
                metric_name='ROE',
                avg=42.3,
                median=38.5,
                stddev=15.1,
                p25=28.2,
                p75=52.8,
                p10=18.5,
                p90=68.2,
                sample_size=74,
                min_value=5.2,
                max_value=195.3
            ),
            'NetMargin': MetricBenchmark(
                metric_name='NetMargin',
                avg=18.4,
                median=16.2,
                stddev=8.2,
                p25=11.5,
                p75=24.1,
                p10=6.8,
                p90=32.5,
                sample_size=74,
                min_value=-5.2,
                max_value=45.8
            )
        }

        # Export to temp file
        calculator = BenchmarkCalculator()
        output_file = tmp_path / "test_benchmarks.json"
        calculator.export_to_json(benchmarks, str(output_file))

        # Verify file exists
        assert output_file.exists()

        # Load back
        loaded_benchmarks = BenchmarkCalculator.load_from_json(str(output_file))

        # Verify data integrity
        assert 'ROE' in loaded_benchmarks
        assert loaded_benchmarks['ROE'].avg == 42.3
        assert loaded_benchmarks['ROE'].median == 38.5
        assert loaded_benchmarks['ROE'].sample_size == 74

        assert 'NetMargin' in loaded_benchmarks
        assert loaded_benchmarks['NetMargin'].avg == 18.4

    def test_json_structure(self, tmp_path):
        """JSON should have correct structure"""
        benchmarks = {
            'ROE': MetricBenchmark(
                metric_name='ROE',
                avg=42.3,
                median=38.5,
                stddev=15.1,
                p25=28.2,
                p75=52.8,
                p10=18.5,
                p90=68.2,
                sample_size=74,
                min_value=5.2,
                max_value=195.3
            )
        }

        calculator = BenchmarkCalculator()
        output_file = tmp_path / "test_benchmarks.json"
        calculator.export_to_json(benchmarks, str(output_file))

        # Load and verify structure
        with open(output_file, 'r') as f:
            data = json.load(f)

        assert 'metadata' in data
        assert 'benchmarks' in data
        assert 'generated_date' in data['metadata']
        assert 'industry' in data['metadata']
        assert 'ROE' in data['benchmarks']

        roe_data = data['benchmarks']['ROE']
        assert 'avg' in roe_data
        assert 'median' in roe_data
        assert 'stddev' in roe_data
        assert 'p25' in roe_data
        assert 'p75' in roe_data


class TestBenchmarkCalculatorIntegration:
    """Integration tests (requires real data)"""

    @pytest.mark.slow
    def test_calculate_tech_benchmarks_subset(self):
        """
        Test benchmark calculation with small subset

        NOTE: This test requires XBRL data for AAPL, MSFT, NVDA
        Mark as @pytest.mark.slow to skip in quick tests
        """
        pytest.skip("Requires full XBRL dataset - run manually")

        calculator = BenchmarkCalculator(data_dir='data', years=4)

        # Mock progress callback
        progress_log = []
        def log_progress(ticker, current, total):
            progress_log.append(f"{current}/{total}: {ticker}")

        benchmarks = calculator.calculate_tech_benchmarks(
            progress_callback=log_progress
        )

        # Verify benchmarks were calculated
        assert len(benchmarks) > 0
        assert 'ROE' in benchmarks
        assert benchmarks['ROE'].sample_size > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
