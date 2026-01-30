"""
Statistical Benchmark Engine - Franklin Framework Layer 2

Calculates dynamic thresholds from real sector data (no hardcoding).
Provides industry benchmarks based on actual peer distributions.

Features:
- Dynamic percentile calculation (P10, P25, P50, P75, P90)
- Industry averages and standard deviations
- Sector-specific benchmarks
- NaN-safe operations
- Caching for performance

Author: @franklin (CTO)
Sprint 5 - Franklin Framework
"""

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np


@dataclass
class IndustryBenchmark:
    """
    Industry benchmark calculated from real sector data

    Attributes:
        metric_name: Name of metric (e.g., 'ROE', 'NetMargin')
        p10: 10th percentile (bottom threshold)
        p25: 25th percentile (lower quartile)
        p50: 50th percentile (median)
        p75: 75th percentile (upper quartile)
        p90: 90th percentile (top threshold)
        mean: Industry average
        std: Standard deviation
        sample_size: Number of companies in calculation

    Example:
        >>> benchmark = IndustryBenchmark(
        ...     metric_name='ROE',
        ...     p10=8.2, p25=15.3, p50=28.5, p75=45.7, p90=98.3,
        ...     mean=35.6, std=25.4, sample_size=20
        ... )
        >>> print(f"ROE Top Quartile threshold: {benchmark.p75:.1f}%")
        ROE Top Quartile threshold: 45.7%
    """
    metric_name: str
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float
    mean: float
    std: float
    sample_size: int

    def __repr__(self) -> str:
        return (
            f"IndustryBenchmark({self.metric_name}: "
            f"P50={self.p50:.1f}, P75={self.p75:.1f}, P90={self.p90:.1f}, "
            f"n={self.sample_size})"
        )


class StatisticalBenchmarkEngine:
    """
    Calculate dynamic benchmarks from real sector data

    Replaces hardcoded thresholds with percentiles calculated from
    actual peer company distributions.

    Features:
    - Automatic percentile calculation (P10-P90)
    - Latest year focus (most recent data)
    - NaN-safe operations
    - Result caching for performance
    - Statistical rigor (min 3 companies required)

    Usage:
        >>> from backend.parsers.sec_downloader import load_json
        >>> sector_data = load_json('outputs/sector_benchmarks_tech.json')
        >>>
        >>> engine = StatisticalBenchmarkEngine(sector_data)
        >>> roe_bench = engine.calculate_benchmarks('profitability', 'ROE')
        >>>
        >>> print(f"Tech Sector ROE Benchmarks:")
        >>> print(f"  P75 (BUY threshold): {roe_bench.p75:.1f}%")
        >>> print(f"  P50 (Median): {roe_bench.p50:.1f}%")
        >>> print(f"  P25 (RED_FLAG threshold): {roe_bench.p25:.1f}%")
    """

    def __init__(self, sector_data: Dict[str, Dict]):
        """
        Initialize engine with sector benchmark data

        Args:
            sector_data: Dict from generate_sector_benchmarks()
                         Format: {ticker: {category: {metric: np.array}}}

        Example:
            >>> sector_data = {
            ...     'AAPL': {
            ...         'profitability': {
            ...             'ROE': np.array([151.9, 164.6, 156.1, 197.0]),
            ...             'NetMargin': np.array([26.9, 24.0, 25.3, 25.3])
            ...         }
            ...     },
            ...     'MSFT': {...}
            ... }
            >>> engine = StatisticalBenchmarkEngine(sector_data)
        """
        self.sector_data = sector_data
        self._benchmarks_cache: Dict[str, IndustryBenchmark] = {}

    def calculate_benchmarks(
        self,
        category: str,
        metric: str
    ) -> Optional[IndustryBenchmark]:
        """
        Calculate industry benchmark for a specific metric

        Uses latest year data from all companies to compute percentiles.
        Requires minimum 3 companies for statistical significance.

        Args:
            category: Metric category (e.g., 'profitability', 'liquidity')
            metric: Metric name (e.g., 'ROE', 'CurrentRatio')

        Returns:
            IndustryBenchmark object or None if insufficient data

        Example:
            >>> benchmark = engine.calculate_benchmarks('profitability', 'ROE')
            >>> if benchmark:
            ...     print(f"ROE P90: {benchmark.p90:.1f}%")
            ...     print(f"Sample size: {benchmark.sample_size} companies")
        """
        # Check cache
        cache_key = f"{category}:{metric}"
        if cache_key in self._benchmarks_cache:
            return self._benchmarks_cache[cache_key]

        # Extract latest year values from all companies
        values = []
        for ticker, data in self.sector_data.items():
            if category in data and metric in data[category]:
                metric_values = data[category][metric]
                if len(metric_values) > 0:
                    latest = metric_values[-1]  # Latest year (index -1)
                    if not np.isnan(latest):
                        values.append(latest)

        # Require minimum 3 companies for statistical validity
        if len(values) < 3:
            return None

        values_arr = np.array(values)

        # Calculate benchmark
        benchmark = IndustryBenchmark(
            metric_name=metric,
            p10=float(np.percentile(values_arr, 10)),
            p25=float(np.percentile(values_arr, 25)),
            p50=float(np.percentile(values_arr, 50)),
            p75=float(np.percentile(values_arr, 75)),
            p90=float(np.percentile(values_arr, 90)),
            mean=float(np.mean(values_arr)),
            std=float(np.std(values_arr)),
            sample_size=len(values)
        )

        # Cache result
        self._benchmarks_cache[cache_key] = benchmark
        return benchmark

    def calculate_all_benchmarks(self) -> Dict[str, Dict[str, IndustryBenchmark]]:
        """
        Calculate benchmarks for ALL metrics in sector data

        Returns:
            Nested dict: {category: {metric_name: IndustryBenchmark}}

        Example:
            >>> all_benchmarks = engine.calculate_all_benchmarks()
            >>>
            >>> for category, metrics in all_benchmarks.items():
            ...     print(f"\n{category.upper()}:")
            ...     for metric_name, benchmark in metrics.items():
            ...         print(f"  {metric_name}: P50={benchmark.p50:.1f}")
        """
        all_benchmarks = {}

        # Iterate through first company to get structure
        if not self.sector_data:
            return all_benchmarks

        sample_ticker = next(iter(self.sector_data.keys()))
        sample_data = self.sector_data[sample_ticker]

        for category, metrics_dict in sample_data.items():
            all_benchmarks[category] = {}

            for metric_name in metrics_dict.keys():
                benchmark = self.calculate_benchmarks(category, metric_name)
                if benchmark:
                    all_benchmarks[category][metric_name] = benchmark

        return all_benchmarks

    def get_signal_threshold(
        self,
        category: str,
        metric: str,
        signal_type: str
    ) -> Optional[float]:
        """
        Get dynamic threshold for signal detection

        Thresholds based on quartile analysis:
        - BUY: P75 (top quartile)
        - WATCH: P50 (median)
        - RED_FLAG: P25 (bottom quartile)

        Args:
            category: Metric category
            metric: Metric name
            signal_type: 'BUY', 'WATCH', or 'RED_FLAG'

        Returns:
            Threshold value or None if benchmark unavailable

        Example:
            >>> buy_threshold = engine.get_signal_threshold(
            ...     'profitability', 'ROE', 'BUY'
            ... )
            >>> print(f"ROE BUY threshold (P75): {buy_threshold:.1f}%")
        """
        benchmark = self.calculate_benchmarks(category, metric)
        if not benchmark:
            return None

        if signal_type == 'BUY':
            return benchmark.p75  # Top quartile
        elif signal_type == 'WATCH':
            return benchmark.p50  # Median
        elif signal_type == 'RED_FLAG':
            return benchmark.p25  # Bottom quartile
        else:
            return None
