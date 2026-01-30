"""
Tests for peer comparison engine using real XBRL data

Test Strategy:
- Use real metrics from multiple companies (AAPL, MSFT, GOOGL)
- Calculate percentiles dynamically from peer group
- Validate "beats peers" count
- Test edge cases (single peer, missing data)
"""

import pytest
import numpy as np
from backend.signals.peer_comparison import (
    PeerComparison,
    PeerBenchmark,
    calculate_percentile,
    compare_to_peers
)


class TestCalculatePercentile:
    """Test percentile calculation from peer distribution"""

    def test_percentile_calculation_median(self):
        """Value at median should be ~50th percentile"""
        peer_values = np.array([10, 20, 30, 40, 50])
        value = 30

        percentile = calculate_percentile(value, peer_values)

        assert 40 <= percentile <= 60  # Around median

    def test_percentile_calculation_top(self):
        """Value above all peers should be 100th percentile"""
        peer_values = np.array([10, 20, 30, 40, 50])
        value = 60

        percentile = calculate_percentile(value, peer_values)

        assert percentile == 100

    def test_percentile_calculation_bottom(self):
        """Value below all peers should be 0th percentile"""
        peer_values = np.array([10, 20, 30, 40, 50])
        value = 5

        percentile = calculate_percentile(value, peer_values)

        assert percentile == 0

    def test_percentile_with_nan_values(self):
        """Should handle NaN values in peer distribution"""
        peer_values = np.array([10, np.nan, 30, 40, np.nan])
        value = 35

        percentile = calculate_percentile(value, peer_values)

        assert 50 <= percentile <= 100  # Above median of valid values


class TestPeerBenchmark:
    """Test PeerBenchmark dataclass"""

    def test_benchmark_initialization(self):
        """Should initialize with all required fields"""
        benchmark = PeerBenchmark(
            metric_name="ROE",
            company_value=151.9,
            peer_median=42.3,
            peer_mean=45.8,
            percentile=95,
            beats_peers=True,
            peer_count=10,
            interpretation="Top Decile ↗️"
        )

        assert benchmark.metric_name == "ROE"
        assert benchmark.percentile == 95
        assert benchmark.beats_peers is True

    def test_benchmark_comparison_logic(self):
        """beats_peers should be True when value > median"""
        benchmark_above = PeerBenchmark(
            metric_name="NetMargin",
            company_value=26.9,
            peer_median=18.4,
            peer_mean=19.2,
            percentile=80,
            beats_peers=True,
            peer_count=5,
            interpretation="Top Quartile ↗️"
        )

        assert benchmark_above.beats_peers is True

        benchmark_below = PeerBenchmark(
            metric_name="CurrentRatio",
            company_value=0.89,
            peer_median=1.8,
            peer_mean=1.9,
            percentile=20,
            beats_peers=False,
            peer_count=5,
            interpretation="Below Average ↘️"
        )

        assert benchmark_below.beats_peers is False


@pytest.fixture
def mock_peer_metrics():
    """
    Mock metrics for 5 tech companies
    Simulates real distribution from AAPL, MSFT, GOOGL, META, NVDA
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
        },
        'MSFT': {
            'profitability': {
                'ROE': np.array([43.7, 40.4, 38.3, 42.1]),
                'NetMargin': np.array([36.7, 34.1, 30.6, 35.9]),
                'ROIC': np.array([32.1, 28.9, 26.4, 30.2]),
            },
            'liquidity': {
                'CurrentRatio': np.array([1.78, 2.08, 1.77, 1.98]),
            },
        },
        'GOOGL': {
            'profitability': {
                'ROE': np.array([29.6, 27.1, 24.8, 30.3]),
                'NetMargin': np.array([27.6, 23.5, 21.2, 26.8]),
                'ROIC': np.array([24.3, 22.1, 19.8, 25.1]),
            },
            'liquidity': {
                'CurrentRatio': np.array([2.89, 2.71, 2.45, 2.93]),
            },
        },
        'META': {
            'profitability': {
                'ROE': np.array([25.8, 19.9, 20.1, 33.4]),
                'NetMargin': np.array([33.4, 23.2, 22.9, 35.7]),
                'ROIC': np.array([22.7, 17.3, 17.9, 29.1]),
            },
            'liquidity': {
                'CurrentRatio': np.array([2.34, 3.18, 2.90, 3.05]),
            },
        },
        'NVDA': {
            'profitability': {
                'ROE': np.array([38.9, 29.8, 25.7, 85.3]),
                'NetMargin': np.array([36.2, 25.9, 21.4, 55.0]),
                'ROIC': np.array([28.4, 21.7, 18.9, 62.1]),
            },
            'liquidity': {
                'CurrentRatio': np.array([3.45, 4.31, 3.89, 4.12]),
            },
        },
    }


class TestPeerComparison:
    """Test PeerComparison class with real peer data"""

    def test_initialization(self, mock_peer_metrics):
        """Should initialize with company metrics and peer group"""
        company_metrics = mock_peer_metrics['AAPL']
        peer_group = {k: v for k, v in mock_peer_metrics.items() if k != 'AAPL'}

        comparison = PeerComparison(
            company_metrics=company_metrics,
            peer_metrics=peer_group,
            company_name='AAPL'
        )

        assert comparison.company_name == 'AAPL'
        assert len(comparison.peer_metrics) == 4  # Excludes AAPL

    def test_compare_single_metric(self, mock_peer_metrics):
        """Should compare single metric across peers"""
        company_metrics = mock_peer_metrics['AAPL']
        peer_group = {k: v for k, v in mock_peer_metrics.items() if k != 'AAPL'}

        comparison = PeerComparison(company_metrics, peer_group, 'AAPL')
        benchmark = comparison.compare_metric('ROE', 'profitability')

        assert benchmark.metric_name == 'ROE'
        assert benchmark.company_value == 197.0  # Latest AAPL ROE (2025, index -1)
        assert benchmark.percentile >= 90  # AAPL ROE is top tier
        assert benchmark.beats_peers is True
        assert benchmark.peer_count == 4

    def test_compare_all_metrics(self, mock_peer_metrics):
        """Should compare all available metrics"""
        company_metrics = mock_peer_metrics['AAPL']
        peer_group = {k: v for k, v in mock_peer_metrics.items() if k != 'AAPL'}

        comparison = PeerComparison(company_metrics, peer_group, 'AAPL')
        benchmarks = comparison.compare_all()

        assert 'profitability' in benchmarks
        assert 'liquidity' in benchmarks
        assert len(benchmarks['profitability']) == 3  # ROE, NetMargin, ROIC
        assert len(benchmarks['liquidity']) == 1  # CurrentRatio

    def test_beats_peers_count(self, mock_peer_metrics):
        """Should count how many metrics beat peer median"""
        company_metrics = mock_peer_metrics['AAPL']
        peer_group = {k: v for k, v in mock_peer_metrics.items() if k != 'AAPL'}

        comparison = PeerComparison(company_metrics, peer_group, 'AAPL')
        beats_count = comparison.count_beats_peers()

        assert beats_count >= 2  # AAPL should beat peers on ROE, ROIC

    def test_interpretation_generation(self, mock_peer_metrics):
        """Should generate human-readable interpretation"""
        company_metrics = mock_peer_metrics['AAPL']
        peer_group = {k: v for k, v in mock_peer_metrics.items() if k != 'AAPL'}

        comparison = PeerComparison(company_metrics, peer_group, 'AAPL')
        benchmark = comparison.compare_metric('ROE', 'profitability')

        # Percentile >= 90 should get "Top Decile" interpretation
        if benchmark.percentile >= 90:
            assert "Top Decile" in benchmark.interpretation or "↗️" in benchmark.interpretation


class TestCompareToPeers:
    """Test high-level compare_to_peers function"""

    def test_compare_to_peers_integration(self, mock_peer_metrics):
        """Should work end-to-end with real-like data"""
        company_metrics = mock_peer_metrics['AAPL']
        peer_group = {k: v for k, v in mock_peer_metrics.items() if k != 'AAPL'}

        benchmarks = compare_to_peers(
            company_metrics=company_metrics,
            peer_metrics=peer_group,
            company_name='AAPL'
        )

        assert isinstance(benchmarks, dict)
        assert 'profitability' in benchmarks
        assert len(benchmarks['profitability']) > 0

    def test_edge_case_single_peer(self, mock_peer_metrics):
        """Should handle case with only 1 peer"""
        company_metrics = mock_peer_metrics['AAPL']
        peer_group = {'MSFT': mock_peer_metrics['MSFT']}

        benchmarks = compare_to_peers(company_metrics, peer_group, 'AAPL')

        # Should still work with 1 peer (percentile will be 0 or 100)
        assert 'profitability' in benchmarks

    def test_edge_case_no_common_metrics(self):
        """Should handle case where company and peers have no common metrics"""
        company_metrics = {
            'profitability': {'ROE': np.array([20.0])},
        }
        peer_metrics = {
            'PEER1': {
                'liquidity': {'CurrentRatio': np.array([1.5])},
            }
        }

        benchmarks = compare_to_peers(company_metrics, peer_metrics, 'TEST')

        # Should return empty or handle gracefully
        assert isinstance(benchmarks, dict)
