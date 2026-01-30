"""
Peer Comparison Engine - Dynamic Benchmarking (Franklin Framework)

Uses StatisticalBenchmarkEngine and FranklinInterpretation for context-aware
peer comparison without hardcoded percentile cuts.

Author: @franklin (CTO)
Sprint 5 - Franklin Framework Refactor
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
from backend.signals.statistical_engine import StatisticalBenchmarkEngine, IndustryBenchmark
from backend.signals.franklin_interpretation import FranklinInterpretation


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
        interpretation: Dynamic interpretation from Franklin Framework
        sector_benchmark: Optional IndustryBenchmark for full sector context
    """
    metric_name: str
    company_value: float
    peer_median: float
    peer_mean: float
    percentile: int
    beats_peers: bool
    peer_count: int
    interpretation: str
    sector_benchmark: Optional[IndustryBenchmark] = None


def calculate_percentile(value: float, peer_values: np.ndarray) -> int:
    """
    Calculate percentile rank of a value within a peer distribution

    Args:
        value: The value to rank
        peer_values: Array of peer values (may contain NaN)

    Returns:
        Percentile rank (0-100)
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


class PeerComparison:
    """
    Compare company metrics against peer group using Franklin Framework

    CHANGES FROM PREVIOUS VERSION:
    - ❌ REMOVED: _generate_interpretation() with hardcoded cuts
    - ✅ ADDED: StatisticalBenchmarkEngine integration
    - ✅ ADDED: FranklinInterpretation for dynamic zones
    - ✅ ADDED: Full sector context (not just peer group)

    Attributes:
        company_metrics: Metrics dict from calculate_metrics()
        peer_metrics: Dict of {ticker: metrics} for peer group
        company_name: Company ticker
        benchmark_engine: Optional engine for full sector benchmarks
    """

    def __init__(
        self,
        company_metrics: Dict,
        peer_metrics: Dict[str, Dict],
        company_name: str,
        benchmark_engine: Optional[StatisticalBenchmarkEngine] = None
    ):
        """
        Initialize peer comparison with optional sector benchmarks

        Args:
            company_metrics: Output from calculate_metrics()
            peer_metrics: Dict of {ticker: metrics}
            company_name: Ticker symbol
            benchmark_engine: Optional StatisticalBenchmarkEngine for sector context

        Example:
            >>> # With sector benchmarks (Franklin Framework)
            >>> comparison = PeerComparison(
            ...     company_metrics=aapl_metrics,
            ...     peer_metrics={'MSFT': msft_metrics, 'GOOGL': googl_metrics},
            ...     company_name='AAPL',
            ...     benchmark_engine=engine  # Full sector context
            ... )

            >>> # Without sector benchmarks (legacy mode)
            >>> comparison = PeerComparison(
            ...     company_metrics=aapl_metrics,
            ...     peer_metrics={'MSFT': msft_metrics},
            ...     company_name='AAPL'
            ... )
        """
        self.company_metrics = company_metrics
        self.peer_metrics = peer_metrics
        self.company_name = company_name
        self.benchmark_engine = benchmark_engine

    def compare_metric(
        self,
        metric_name: str,
        category: str
    ) -> Optional[PeerBenchmark]:
        """
        Compare a single metric against peer group with dynamic interpretation

        Args:
            metric_name: Name of metric to compare (e.g., 'ROE')
            category: Category of metric (e.g., 'profitability')

        Returns:
            PeerBenchmark object with Franklin interpretation or None
        """
        # Get company's metric value (latest year)
        if category not in self.company_metrics:
            return None

        if metric_name not in self.company_metrics[category]:
            return None

        company_values = self.company_metrics[category][metric_name]
        if len(company_values) == 0:
            return None

        company_value = float(company_values[-1])  # Latest year

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
            return None

        # Calculate peer statistics
        peer_median = float(np.median(valid_peer_values))
        peer_mean = float(np.mean(valid_peer_values))
        percentile = calculate_percentile(company_value, peer_values)
        beats_peers = company_value > peer_median
        peer_count = len(peer_values_list)

        # Get sector benchmark if engine available
        sector_benchmark = None
        if self.benchmark_engine:
            sector_benchmark = self.benchmark_engine.calculate_benchmarks(
                category, metric_name
            )

        # Generate interpretation using Franklin Framework
        if sector_benchmark:
            # Use full sector context
            zone = FranklinInterpretation.interpret_value(
                value=company_value,
                benchmark=sector_benchmark,
                metric_name=metric_name
            )
            interpretation = f"{zone.name} {zone.icon}"
        else:
            # Fallback to percentile interpretation
            zone = FranklinInterpretation.interpret_percentile(
                percentile=percentile,
                benchmark=None,  # Will use percentile-only logic
                metric_name=metric_name
            )
            interpretation = f"{zone.name} {zone.icon}"

        return PeerBenchmark(
            metric_name=metric_name,
            company_value=company_value,
            peer_median=peer_median,
            peer_mean=peer_mean,
            percentile=percentile,
            beats_peers=beats_peers,
            peer_count=peer_count,
            interpretation=interpretation,
            sector_benchmark=sector_benchmark
        )

    def compare_all(self) -> Dict[str, List[PeerBenchmark]]:
        """
        Compare all available metrics against peers

        Returns:
            Dict of {category: [PeerBenchmark, ...]}
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
    company_name: str,
    benchmark_engine: Optional[StatisticalBenchmarkEngine] = None
) -> Dict[str, List[PeerBenchmark]]:
    """
    High-level API for peer comparison with Franklin Framework

    Args:
        company_metrics: Output from calculate_metrics()
        peer_metrics: Dict of {ticker: metrics}
        company_name: Ticker symbol
        benchmark_engine: Optional StatisticalBenchmarkEngine for sector context

    Returns:
        Dict of {category: [PeerBenchmark, ...]}

    Example:
        >>> # With Franklin Framework (sector context)
        >>> from backend.parsers.sec_downloader import load_json
        >>> from backend.signals.statistical_engine import StatisticalBenchmarkEngine
        >>>
        >>> sector_data = load_json('outputs/sector_benchmarks_tech.json')
        >>> engine = StatisticalBenchmarkEngine(sector_data)
        >>>
        >>> benchmarks = compare_to_peers(
        ...     company_metrics=aapl_metrics,
        ...     peer_metrics={'MSFT': msft_metrics, 'GOOGL': googl_metrics},
        ...     company_name='AAPL',
        ...     benchmark_engine=engine  # Full sector context
        ... )
    """
    comparison = PeerComparison(
        company_metrics,
        peer_metrics,
        company_name,
        benchmark_engine
    )
    return comparison.compare_all()
