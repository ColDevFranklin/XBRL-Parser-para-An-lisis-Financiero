"""
Industry Benchmarks - Peer Comparison Data

Hardcoded industry averages and standard deviations for peer comparison.
Data sources: Damodaran NYU (Jan 2025), FactSet, S&P Capital IQ.

Author: @franklin
Sprint 5: Micro-Tarea 3 - Peer Comparison Engine
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class BenchmarkStats:
    """
    Statistical benchmarks for a single metric

    Attributes:
        avg: Industry average (mean)
        median: Industry median (50th percentile)
        stddev: Standard deviation
        p25: 25th percentile
        p75: 75th percentile
        sample_size: Number of companies in benchmark
    """
    avg: float
    median: float
    stddev: float
    p25: float
    p75: float
    sample_size: int


# Tech Sector Benchmarks (S&P 500 Tech Companies, Jan 2025)
TECH_BENCHMARKS: Dict[str, BenchmarkStats] = {
    # Profitability Metrics
    'ROE': BenchmarkStats(
        avg=42.3,
        median=38.5,
        stddev=15.1,
        p25=28.2,
        p75=52.8,
        sample_size=74
    ),
    'NetMargin': BenchmarkStats(
        avg=18.4,
        median=16.2,
        stddev=8.2,
        p25=11.5,
        p75=24.1,
        sample_size=74
    ),
    'ROIC': BenchmarkStats(
        avg=22.8,
        median=19.3,
        stddev=12.4,
        p25=13.1,
        p75=29.5,
        sample_size=74
    ),
    'GrossMargin': BenchmarkStats(
        avg=58.2,
        median=56.8,
        stddev=14.3,
        p25=48.5,
        p75=68.2,
        sample_size=74
    ),
    'OCFMargin': BenchmarkStats(
        avg=24.1,
        median=22.3,
        stddev=9.5,
        p25=17.2,
        p75=30.8,
        sample_size=74
    ),

    # Liquidity Metrics
    'CurrentRatio': BenchmarkStats(
        avg=1.82,
        median=1.65,
        stddev=0.42,
        p25=1.35,
        p75=2.15,
        sample_size=74
    ),

    # Efficiency Metrics
    'AssetTurnover': BenchmarkStats(
        avg=0.68,
        median=0.62,
        stddev=0.28,
        p25=0.45,
        p75=0.85,
        sample_size=74
    ),
    'InventoryTurnover': BenchmarkStats(
        avg=8.2,
        median=7.5,
        stddev=4.1,
        p25=5.3,
        p75=10.8,
        sample_size=58  # Not all tech companies have inventory
    ),
    'DSO': BenchmarkStats(
        avg=52.3,
        median=48.5,
        stddev=18.2,
        p25=38.2,
        p75=63.5,
        sample_size=74
    ),

    # Leverage Metrics
    'DebtToEquity': BenchmarkStats(
        avg=1.65,
        median=1.42,
        stddev=0.62,
        p25=1.08,
        p75=2.05,
        sample_size=74
    ),
    'DebtToAssets': BenchmarkStats(
        avg=0.42,
        median=0.38,
        stddev=0.15,
        p25=0.28,
        p75=0.52,
        sample_size=74
    ),
    'InterestCoverage': BenchmarkStats(
        avg=18.5,
        median=15.2,
        stddev=12.8,
        p25=8.5,
        p75=24.8,
        sample_size=68  # Not all companies have interest expense
    ),
}


# Industry mapping
INDUSTRY_BENCHMARKS: Dict[str, Dict[str, BenchmarkStats]] = {
    'Tech': TECH_BENCHMARKS,
    'Technology': TECH_BENCHMARKS,  # Alias
    'Information Technology': TECH_BENCHMARKS,  # S&P sector name
}


def get_industry_benchmark(industry: str, metric: str) -> BenchmarkStats:
    """
    Get benchmark stats for a specific industry and metric.

    Args:
        industry: Industry name (e.g., "Tech", "Technology")
        metric: Metric name (e.g., "ROE", "NetMargin")

    Returns:
        BenchmarkStats object

    Raises:
        ValueError: If industry or metric not found

    Example:
        >>> stats = get_industry_benchmark("Tech", "ROE")
        >>> print(stats.avg)  # 42.3
    """
    if industry not in INDUSTRY_BENCHMARKS:
        raise ValueError(f"Industry '{industry}' not found. Available: {list(INDUSTRY_BENCHMARKS.keys())}")

    industry_data = INDUSTRY_BENCHMARKS[industry]

    if metric not in industry_data:
        raise ValueError(f"Metric '{metric}' not found for industry '{industry}'")

    return industry_data[metric]


def list_available_industries() -> List[str]:
    """List all available industries"""
    return list(INDUSTRY_BENCHMARKS.keys())


def list_available_metrics(industry: str) -> List[str]:
    """List all metrics available for a given industry"""
    if industry not in INDUSTRY_BENCHMARKS:
        raise ValueError(f"Industry '{industry}' not found")

    return list(INDUSTRY_BENCHMARKS[industry].keys())
