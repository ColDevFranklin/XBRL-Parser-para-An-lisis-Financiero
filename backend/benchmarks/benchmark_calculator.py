"""
Benchmark Calculator - Statistical Analysis Engine

Calculates industry benchmarks from real SEC XBRL data.
Computes avg, median, stddev, percentiles across peer universe.

Author: @franklin
Sprint 5: Micro-Tarea 3 - Peer Comparison Engine
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
from pathlib import Path

from backend.benchmarks.company_universe import get_tech_universe, CompanyInfo
from backend.parsers.multi_file_xbrl_parser import MultiFileXBRLParser
from backend.metrics import calculate_metrics


@dataclass
class MetricBenchmark:
    """
    Statistical benchmark for a single metric

    Attributes:
        metric_name: Name of the financial metric
        avg: Mean value across universe
        median: 50th percentile
        stddev: Standard deviation
        p25: 25th percentile
        p75: 75th percentile
        p10: 10th percentile
        p90: 90th percentile
        sample_size: Number of companies with valid data
        min_value: Minimum observed value
        max_value: Maximum observed value
    """
    metric_name: str
    avg: float
    median: float
    stddev: float
    p25: float
    p75: float
    p10: float
    p90: float
    sample_size: int
    min_value: float
    max_value: float


class BenchmarkCalculator:
    """
    Calculates statistical benchmarks from SEC XBRL data

    Process:
    1. Load XBRL data for all companies in universe
    2. Calculate metrics using MetricsCalculator
    3. Aggregate statistics (avg, median, percentiles)
    4. Export to JSON for reuse

    Usage:
        calculator = BenchmarkCalculator(data_dir='data', years=4)
        benchmarks = calculator.calculate_tech_benchmarks()
        calculator.export_to_json(benchmarks, 'tech_benchmarks_2025Q4.json')
    """

    def __init__(self, data_dir: str = 'data', years: int = 4):
        """
        Initialize benchmark calculator

        Args:
            data_dir: Directory containing XBRL files
            years: Number of years to analyze (default 4)
        """
        self.data_dir = Path(data_dir)
        self.years = years
        self._metrics_cache: Dict[str, Dict] = {}

    def calculate_tech_benchmarks(
        self,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, MetricBenchmark]:
        """
        Calculate benchmarks for S&P 500 Tech sector

        Args:
            progress_callback: Optional callback(ticker, current, total)

        Returns:
            Dict mapping metric names to MetricBenchmark objects

        Example:
            >>> calculator = BenchmarkCalculator()
            >>> benchmarks = calculator.calculate_tech_benchmarks(
            ...     progress_callback=lambda t, c, total: print(f"{c}/{total}: {t}")
            ... )
            >>> print(benchmarks['ROE'].median)  # 38.5
        """
        universe = get_tech_universe()
        total_companies = len(universe)

        # Step 1: Calculate metrics for all companies
        all_metrics = []
        successful_tickers = []
        failed_tickers = []

        for idx, company in enumerate(universe, 1):
            if progress_callback:
                progress_callback(company.ticker, idx, total_companies)

            try:
                metrics = self._calculate_company_metrics(company.ticker)
                if metrics is not None:
                    all_metrics.append(metrics)
                    successful_tickers.append(company.ticker)
                else:
                    failed_tickers.append(company.ticker)
            except Exception as e:
                print(f"⚠️  Failed to process {company.ticker}: {e}")
                failed_tickers.append(company.ticker)

        # Step 2: Aggregate statistics
        benchmarks = self._aggregate_statistics(all_metrics)

        # Step 3: Add metadata
        for benchmark in benchmarks.values():
            benchmark.sample_size = len(successful_tickers)

        print(f"\n✅ Benchmarks calculated:")
        print(f"   Successful: {len(successful_tickers)}/{total_companies}")
        print(f"   Failed: {len(failed_tickers)}")
        if failed_tickers:
            print(f"   Failed tickers: {failed_tickers[:10]}...")

        return benchmarks

    def _calculate_company_metrics(self, ticker: str) -> Optional[Dict]:
        """
        Calculate metrics for a single company

        Args:
            ticker: Company ticker symbol

        Returns:
            Dict of metrics or None if data unavailable
        """
        # Check cache
        if ticker in self._metrics_cache:
            return self._metrics_cache[ticker]

        try:
            # Parse XBRL data
            parser = MultiFileXBRLParser(ticker=ticker, data_dir=str(self.data_dir))
            timeseries = parser.extract_timeseries(years=self.years)

            # Calculate metrics
            metrics = calculate_metrics(timeseries, parallel='never')

            # Cache result
            self._metrics_cache[ticker] = metrics

            return metrics

        except FileNotFoundError:
            print(f"⚠️  No XBRL data for {ticker}")
            return None
        except Exception as e:
            print(f"⚠️  Error processing {ticker}: {e}")
            return None

    def _aggregate_statistics(
        self,
        all_metrics: List[Dict]
    ) -> Dict[str, MetricBenchmark]:
        """
        Aggregate statistics across all companies

        Args:
            all_metrics: List of metrics dicts from all companies

        Returns:
            Dict mapping metric names to MetricBenchmark objects
        """
        benchmarks = {}

        # Get all metric names from first company
        if not all_metrics:
            return benchmarks

        # Iterate through categories and metrics
        for category in all_metrics[0].keys():
            for metric_name in all_metrics[0][category].keys():

                # Collect values across all companies (most recent year only)
                values = []
                for company_metrics in all_metrics:
                    metric_array = company_metrics[category][metric_name]

                    # Use most recent value (index 0)
                    if len(metric_array) > 0 and not np.isnan(metric_array[0]):
                        values.append(metric_array[0])

                # Skip if insufficient data
                if len(values) < 3:  # Require at least 3 companies for statistics
                    continue

                values_array = np.array(values)

                # Calculate statistics
                benchmark = MetricBenchmark(
                    metric_name=metric_name,
                    avg=float(np.mean(values_array)),
                    median=float(np.median(values_array)),
                    stddev=float(np.std(values_array)),
                    p25=float(np.percentile(values_array, 25)),
                    p75=float(np.percentile(values_array, 75)),
                    p10=float(np.percentile(values_array, 10)),
                    p90=float(np.percentile(values_array, 90)),
                    sample_size=len(values),
                    min_value=float(np.min(values_array)),
                    max_value=float(np.max(values_array))
                )

                benchmarks[metric_name] = benchmark

        return benchmarks

    def export_to_json(
        self,
        benchmarks: Dict[str, MetricBenchmark],
        output_path: str
    ) -> None:
        """
        Export benchmarks to JSON file

        Args:
            benchmarks: Dict of MetricBenchmark objects
            output_path: Path to output JSON file

        Example:
            >>> calculator.export_to_json(
            ...     benchmarks,
            ...     'backend/benchmarks/tech_benchmarks_2025Q4.json'
            ... )
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to serializable dict
        data = {
            'metadata': {
                'generated_date': '2025-01-29',
                'industry': 'Information Technology',
                'universe': 'S&P 500 Tech Sector',
                'years_analyzed': self.years,
                'sample_size': next(iter(benchmarks.values())).sample_size if benchmarks else 0
            },
            'benchmarks': {
                name: {
                    'avg': b.avg,
                    'median': b.median,
                    'stddev': b.stddev,
                    'p25': b.p25,
                    'p75': b.p75,
                    'p10': b.p10,
                    'p90': b.p90,
                    'sample_size': b.sample_size,
                    'min': b.min_value,
                    'max': b.max_value
                }
                for name, b in benchmarks.items()
            }
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ Benchmarks exported to: {output_file}")

    @staticmethod
    def load_from_json(json_path: str) -> Dict[str, MetricBenchmark]:
        """
        Load benchmarks from JSON file

        Args:
            json_path: Path to JSON file

        Returns:
            Dict of MetricBenchmark objects

        Example:
            >>> benchmarks = BenchmarkCalculator.load_from_json(
            ...     'backend/benchmarks/tech_benchmarks_2025Q4.json'
            ... )
        """
        with open(json_path, 'r') as f:
            data = json.load(f)

        benchmarks = {}
        for name, values in data['benchmarks'].items():
            benchmarks[name] = MetricBenchmark(
                metric_name=name,
                avg=values['avg'],
                median=values['median'],
                stddev=values['stddev'],
                p25=values['p25'],
                p75=values['p75'],
                p10=values['p10'],
                p90=values['p90'],
                sample_size=values['sample_size'],
                min_value=values['min'],
                max_value=values['max']
            )

        return benchmarks


def calculate_percentile(value: float, benchmark: MetricBenchmark) -> int:
    """
    Calculate percentile rank of a value against benchmark

    Uses linear interpolation between known percentiles.

    Args:
        value: Value to rank
        benchmark: MetricBenchmark object with statistics

    Returns:
        Percentile rank (0-100)

    Example:
        >>> benchmark = MetricBenchmark(...)
        >>> percentile = calculate_percentile(45.2, benchmark)
        >>> print(percentile)  # 85
    """
    # Handle edge cases
    if value <= benchmark.p10:
        return 10
    if value >= benchmark.p90:
        return 90

    # Linear interpolation between known percentiles
    if value <= benchmark.p25:
        # Between p10 and p25
        ratio = (value - benchmark.p10) / (benchmark.p25 - benchmark.p10)
        return int(10 + ratio * 15)
    elif value <= benchmark.median:
        # Between p25 and p50
        ratio = (value - benchmark.p25) / (benchmark.median - benchmark.p25)
        return int(25 + ratio * 25)
    elif value <= benchmark.p75:
        # Between p50 and p75
        ratio = (value - benchmark.median) / (benchmark.p75 - benchmark.median)
        return int(50 + ratio * 25)
    else:
        # Between p75 and p90
        ratio = (value - benchmark.p75) / (benchmark.p90 - benchmark.p75)
        return int(75 + ratio * 15)
