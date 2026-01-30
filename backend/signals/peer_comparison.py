"""
Peer Comparison Engine - Dynamic benchmarking using real company data

Features:
- Calculate percentiles from real peer distributions (no hardcoded benchmarks)
- Compare company metrics against peer group medians/means
- Generate human-readable interpretations (Top Decile, Above Average, etc.)
- Count "beats peers" metrics
- Handle edge cases (NaN values, single peer, missing metrics)

Usage:
    from backend.signals.peer_comparison import compare_to_peers

    # Load metrics for company and peers
    company_metrics = calculate_metrics(company_timeseries)
    peer_metrics = {
        'MSFT': calculate_metrics(msft_timeseries),
        'GOOGL': calculate_metrics(googl_timeseries),
        # ... more peers
    }

    # Compare
    benchmarks = compare_to_peers(company_metrics, peer_metrics, 'AAPL')
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np


@dataclass
class PeerBenchmark:
    """
    Benchmark result for a single metric compared against peers

    Attributes:
        metric_name: Name of the financial metric (e.g., 'ROE', 'NetMargin')
        company_value: Company's metric value (latest year)
        peer_median: Median value across peer group
        peer_mean: Mean value across peer group
        percentile: Company's percentile rank (0-100)
        beats_peers: True if company_value > peer_median
        peer_count: Number of peers in comparison
        interpretation: Human-readable interpretation (e.g., "Top Decile ↗️")
    """
    metric_name: str
    company_value: float
    peer_median: float
    peer_mean: float
    percentile: int
    beats_peers: bool
    peer_count: int
    interpretation: str


def calculate_percentile(value: float, peer_values: np.ndarray) -> int:
    """
    Calculate percentile rank of a value within a peer distribution

    Uses NumPy's percentile ranking where:
    - 0th percentile = value is at/below all peers
    - 50th percentile = value is at median
    - 100th percentile = value is at/above all peers

    Args:
        value: The value to rank
        peer_values: Array of peer values (may contain NaN)

    Returns:
        Percentile rank (0-100)

    Examples:
        >>> calculate_percentile(30, np.array([10, 20, 30, 40, 50]))
        50  # At median

        >>> calculate_percentile(60, np.array([10, 20, 30, 40, 50]))
        100  # Above all peers
    """
    # Remove NaN values
    valid_peers = peer_values[~np.isnan(peer_values)]

    if len(valid_peers) == 0:
        return 50  # Default to median if no valid peers

    # Count how many peers are below this value
    below_count = np.sum(valid_peers < value)
    total_count = len(valid_peers)

    # Calculate percentile
    percentile = int((below_count / total_count) * 100)

    return percentile


def _generate_interpretation(percentile: int, beats_peers: bool) -> str:
    """
    Generate human-readable interpretation from percentile rank

    Args:
        percentile: Percentile rank (0-100)
        beats_peers: Whether value beats peer median

    Returns:
        Interpretation string with emoji

    Examples:
        >>> _generate_interpretation(95, True)
        'Top Decile ↗️'

        >>> _generate_interpretation(20, False)
        'Below Average ↘️'
    """
    if percentile >= 90:
        return "Top Decile ↗️"
    elif percentile >= 75:
        return "Top Quartile ↗️"
    elif percentile >= 60:
        return "Above Average ↗️"
    elif percentile >= 40:
        return "Average →"
    elif percentile >= 25:
        return "Below Average ↘️"
    else:
        return "Bottom Quartile ↘️"


class PeerComparison:
    """
    Compare company metrics against a peer group using real data

    Features:
    - Dynamic benchmark calculation (no hardcoded values)
    - Percentile ranking across peer distribution
    - Human-readable interpretations
    - NaN-safe operations

    Attributes:
        company_metrics: Metrics dict from calculate_metrics()
        peer_metrics: Dict of {ticker: metrics} for peer group
        company_name: Company ticker for reference
    """

    def __init__(
        self,
        company_metrics: Dict,
        peer_metrics: Dict[str, Dict],
        company_name: str
    ):
        """
        Initialize peer comparison engine

        Args:
            company_metrics: Output from calculate_metrics() for target company
            peer_metrics: Dict of {ticker: calculate_metrics() output} for peers
            company_name: Ticker symbol of target company

        Example:
            >>> comparison = PeerComparison(
            ...     company_metrics=aapl_metrics,
            ...     peer_metrics={'MSFT': msft_metrics, 'GOOGL': googl_metrics},
            ...     company_name='AAPL'
            ... )
        """
        self.company_metrics = company_metrics
        self.peer_metrics = peer_metrics
        self.company_name = company_name

    def compare_metric(self, metric_name: str, category: str) -> Optional[PeerBenchmark]:
        """
        Compare a single metric against peer group

        Args:
            metric_name: Name of metric to compare (e.g., 'ROE')
            category: Category of metric (e.g., 'profitability')

        Returns:
            PeerBenchmark object or None if metric not available

        Example:
            >>> benchmark = comparison.compare_metric('ROE', 'profitability')
            >>> print(f"ROE: {benchmark.percentile}th percentile")
        """
        # Get company's metric value (latest year)
        if category not in self.company_metrics:
            return None

        if metric_name not in self.company_metrics[category]:
            return None

        company_values = self.company_metrics[category][metric_name]
        if len(company_values) == 0:
            return None

        # Use latest year value (index -1)
        company_value = float(company_values[-1])

        # Collect peer values (latest year for each peer)
        peer_values_list = []
        for peer_ticker, peer_metric_dict in self.peer_metrics.items():
            if category in peer_metric_dict and metric_name in peer_metric_dict[category]:
                peer_vals = peer_metric_dict[category][metric_name]
                if len(peer_vals) > 0:
                    peer_values_list.append(float(peer_vals[-1]))

        if len(peer_values_list) == 0:
            return None

        peer_values = np.array(peer_values_list)
        # Remove NaN values before calculating statistics
        valid_peer_values = peer_values[~np.isnan(peer_values)]

        if len(valid_peer_values) == 0:
        # No valid peer data for this metric
            return None


        # Calculate statistics
        peer_median = float(np.nanmedian(peer_values))
        peer_mean = float(np.nanmean(peer_values))


        percentile = calculate_percentile(company_value, peer_values)
        beats_peers = company_value > peer_median
        peer_count = len(peer_values_list)
        interpretation = _generate_interpretation(percentile, beats_peers)

        return PeerBenchmark(
            metric_name=metric_name,
            company_value=company_value,
            peer_median=peer_median,
            peer_mean=peer_mean,
            percentile=percentile,
            beats_peers=beats_peers,
            peer_count=peer_count,
            interpretation=interpretation
        )

    def compare_all(self) -> Dict[str, List[PeerBenchmark]]:
        """
        Compare all available metrics against peers

        Returns:
            Dict of {category: [PeerBenchmark, ...]} for all categories

        Example:
            >>> benchmarks = comparison.compare_all()
            >>> for category, benchmark_list in benchmarks.items():
            ...     print(f"{category}: {len(benchmark_list)} metrics compared")
        """
        results = {}

        for category, metrics_dict in self.company_metrics.items():
            category_benchmarks = []

            for metric_name in metrics_dict.keys():
                benchmark = self.compare_metric(metric_name, category)
                if benchmark is not None:
                    category_benchmarks.append(benchmark)

            if len(category_benchmarks) > 0:
                results[category] = category_benchmarks

        return results

    def count_beats_peers(self) -> int:
        """
        Count how many metrics beat peer median

        Returns:
            Number of metrics where company > peer_median

        Example:
            >>> beats_count = comparison.count_beats_peers()
            >>> print(f"Beats peers on {beats_count} metrics")
        """
        all_benchmarks = self.compare_all()

        total_beats = 0
        for category_benchmarks in all_benchmarks.values():
            for benchmark in category_benchmarks:
                if benchmark.beats_peers:
                    total_beats += 1

        return total_beats


def compare_to_peers(
    company_metrics: Dict,
    peer_metrics: Dict[str, Dict],
    company_name: str
) -> Dict[str, List[PeerBenchmark]]:
    """
    High-level function to compare company metrics against peer group

    This is the main public API for peer comparison.

    Args:
        company_metrics: Output from calculate_metrics() for target company
        peer_metrics: Dict of {ticker: metrics} for peer companies
        company_name: Ticker symbol of target company

    Returns:
        Dict of {category: [PeerBenchmark, ...]}

    Example:
        >>> from backend.metrics import calculate_metrics
        >>> from backend.parsers import MultiFileXBRLParser
        >>>
        >>> # Load company data
        >>> aapl_parser = MultiFileXBRLParser('AAPL', 'data')
        >>> aapl_ts = aapl_parser.extract_timeseries(years=4)
        >>> aapl_metrics = calculate_metrics(aapl_ts)
        >>>
        >>> # Load peer data
        >>> msft_parser = MultiFileXBRLParser('MSFT', 'data')
        >>> msft_ts = msft_parser.extract_timeseries(years=4)
        >>> msft_metrics = calculate_metrics(msft_ts)
        >>>
        >>> # Compare
        >>> benchmarks = compare_to_peers(
        ...     company_metrics=aapl_metrics,
        ...     peer_metrics={'MSFT': msft_metrics},
        ...     company_name='AAPL'
        ... )
        >>>
        >>> # Print results
        >>> for category, benchmark_list in benchmarks.items():
        ...     print(f"\n{category.upper()}:")
        ...     for b in benchmark_list:
        ...         print(f"  {b.metric_name}: {b.percentile}th %ile - {b.interpretation}")
    """
    comparison = PeerComparison(company_metrics, peer_metrics, company_name)
    return comparison.compare_all()
