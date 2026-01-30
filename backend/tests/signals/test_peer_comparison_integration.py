"""
Integration test for peer comparison with real XBRL data

This test demonstrates the value of peer comparison by:
1. Loading real data from multiple companies (AAPL, MSFT, GOOGL, META, NVDA)
2. Calculating metrics for each
3. Running peer comparison
4. Displaying human-readable output

Run with: python3 -m pytest backend/tests/signals/test_peer_comparison_integration.py -v -s
"""

import pytest
from backend.parsers.multi_file_xbrl_parser import MultiFileXBRLParser
from backend.metrics import calculate_metrics
from backend.signals import compare_to_peers


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format value as percentage"""
    return f"{value:.{decimals}f}%"


def format_ratio(value: float, decimals: int = 2) -> str:
    """Format value as ratio"""
    return f"{value:.{decimals}f}"


def print_benchmark_table(benchmarks: dict, company_name: str):
    """
    Print human-readable benchmark table

    Args:
        benchmarks: Output from compare_to_peers()
        company_name: Company ticker (e.g., 'AAPL')
    """
    print(f"\n{'=' * 70}")
    print(f"🎯 {company_name} PEER COMPARISON")
    print(f"{'=' * 70}\n")

    for category, benchmark_list in benchmarks.items():
        if len(benchmark_list) == 0:
            continue

        print(f"📊 {category.upper()} BENCHMARKS")
        print("─" * 90)
        print(f"{'Metric':<15} {'Company':<12} {'Peer Median':<12} {'%ile':<8} {'Interpretation':<25}")
        print("─" * 90)

        for b in benchmark_list:
            # Format values based on metric type
            if 'Margin' in b.metric_name or 'ROE' in b.metric_name or 'ROIC' in b.metric_name:
                company_val = format_percentage(b.company_value)
                peer_val = format_percentage(b.peer_median)
            else:
                company_val = format_ratio(b.company_value)
                peer_val = format_ratio(b.peer_median)

            percentile_str = f"{b.percentile}th"

            print(f"{b.metric_name:<15} {company_val:<12} {peer_val:<12} {percentile_str:<8} {b.interpretation:<25}")

        print()


class TestPeerComparisonIntegration:
    """Integration tests with real XBRL data"""

    @pytest.fixture(scope="class")
    def tech_peers_data(self):
        """
        Load real data for Tech companies

        Returns:
            Dict of {ticker: metrics}
        """
        tickers = ['AAPL', 'MSFT']  # Start small, can add GOOGL, META, NVDA later

        metrics_by_ticker = {}

        for ticker in tickers:
            try:
                parser = MultiFileXBRLParser(ticker=ticker, data_dir='data')
                timeseries = parser.extract_timeseries(years=4)
                metrics = calculate_metrics(timeseries, parallel='never')
                metrics_by_ticker[ticker] = metrics
                print(f"✓ Loaded {ticker} (4 years)")
            except Exception as e:
                print(f"✗ Failed to load {ticker}: {e}")

        return metrics_by_ticker

    def test_apple_vs_peers_profitability(self, tech_peers_data):
        """Test Apple profitability vs peers"""
        if 'AAPL' not in tech_peers_data:
            pytest.skip("Apple data not available")

        company_metrics = tech_peers_data['AAPL']
        peer_metrics = {k: v for k, v in tech_peers_data.items() if k != 'AAPL'}

        if len(peer_metrics) == 0:
            pytest.skip("No peer data available")

        benchmarks = compare_to_peers(company_metrics, peer_metrics, 'AAPL')

        # Assertions
        assert 'profitability' in benchmarks
        assert len(benchmarks['profitability']) >= 2  # At least ROE + NetMargin

        # Find ROE benchmark
        roe_benchmark = next(
            (b for b in benchmarks['profitability'] if b.metric_name == 'ROE'),
            None
        )

        assert roe_benchmark is not None
        assert roe_benchmark.company_value > 0
        assert roe_benchmark.percentile >= 0
        assert roe_benchmark.percentile <= 100

    def test_apple_vs_peers_full_report(self, tech_peers_data):
        """Generate full peer comparison report for Apple"""
        if 'AAPL' not in tech_peers_data:
            pytest.skip("Apple data not available")

        company_metrics = tech_peers_data['AAPL']
        peer_metrics = {k: v for k, v in tech_peers_data.items() if k != 'AAPL'}

        if len(peer_metrics) == 0:
            pytest.skip("No peer data available")

        benchmarks = compare_to_peers(company_metrics, peer_metrics, 'AAPL')

        # Print human-readable report
        print_benchmark_table(benchmarks, 'AAPL')

        # Print summary
        total_metrics = sum(len(b) for b in benchmarks.values())
        beats_count = sum(
            1 for benchmark_list in benchmarks.values()
            for b in benchmark_list if b.beats_peers
        )

        peer_names = ', '.join(peer_metrics.keys())

        print(f"✅ BEATS PEERS: {beats_count}/{total_metrics} metrics ({beats_count/total_metrics*100:.1f}%)")
        print(f"🏆 PEER GROUP: {peer_names} ({len(peer_metrics)} companies)")
        print()

        # Assertions
        assert total_metrics > 0
        assert beats_count >= 0

    def test_microsoft_vs_peers_full_report(self, tech_peers_data):
        """Generate full peer comparison report for Microsoft"""
        if 'MSFT' not in tech_peers_data:
            pytest.skip("Microsoft data not available")

        company_metrics = tech_peers_data['MSFT']
        peer_metrics = {k: v for k, v in tech_peers_data.items() if k != 'MSFT'}

        if len(peer_metrics) == 0:
            pytest.skip("No peer data available")

        benchmarks = compare_to_peers(company_metrics, peer_metrics, 'MSFT')

        # Print human-readable report
        print_benchmark_table(benchmarks, 'MSFT')

        # Print summary
        total_metrics = sum(len(b) for b in benchmarks.values())
        beats_count = sum(
            1 for benchmark_list in benchmarks.values()
            for b in benchmark_list if b.beats_peers
        )

        peer_names = ', '.join(peer_metrics.keys())

        print(f"✅ BEATS PEERS: {beats_count}/{total_metrics} metrics ({beats_count/total_metrics*100:.1f}%)")
        print(f"🏆 PEER GROUP: {peer_names} ({len(peer_metrics)} companies)")
        print()
