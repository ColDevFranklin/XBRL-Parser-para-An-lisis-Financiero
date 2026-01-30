"""
Franklin Interpretation Engine - Franklin Framework Layer 3

Dynamic performance interpretation based on real sector benchmarks.
Replaces hardcoded percentile cuts with context-aware zones.

Features:
- Performance zones calculated from actual distributions
- Context-aware interpretations
- Sector-relative scoring
- Human-readable messages

Author: @franklin (CTO)
Sprint 5 - Franklin Framework
"""

from dataclasses import dataclass
from typing import Optional
from backend.signals.statistical_engine import IndustryBenchmark


@dataclass
class PerformanceZone:
    """
    Performance zone based on real sector distribution

    Attributes:
        name: Zone name (e.g., "Elite Performance")
        icon: Visual indicator emoji
        description: Human-readable explanation with context
        relative_position: Position in distribution (top/above_avg/avg/below_avg/bottom)
        percentile_range: Actual percentile range for this zone

    Example:
        >>> zone = PerformanceZone(
        ...     name="Elite Performance",
        ...     icon="🏆",
        ...     description="Top 10% of Tech sector (P90: 98.3%)",
        ...     relative_position="top",
        ...     percentile_range="P90-P100"
        ... )
    """
    name: str
    icon: str
    description: str
    relative_position: str
    percentile_range: str


class FranklinInterpretation:
    """
    Dynamic interpretation engine using real sector benchmarks

    Philosophy:
    - "Elite" = Above sector P90 (not arbitrary 90%)
    - "Below Average" = Below sector P50 (not hardcoded median)
    - Adapts to market conditions (bear vs bull markets)

    Usage:
        >>> from backend.signals.statistical_engine import StatisticalBenchmarkEngine
        >>>
        >>> engine = StatisticalBenchmarkEngine(sector_data)
        >>> benchmark = engine.calculate_benchmarks('profitability', 'ROE')
        >>>
        >>> zone = FranklinInterpretation.interpret_value(
        ...     value=150.0,
        ...     benchmark=benchmark
        ... )
        >>> print(f"{zone.name} {zone.icon}: {zone.description}")
    """

    @staticmethod
    def interpret_value(
        value: float,
        benchmark: IndustryBenchmark,
        metric_name: Optional[str] = None
    ) -> PerformanceZone:
        """
        Interpret performance based on sector distribution

        Zones are dynamic - calculated from actual P10, P25, P50, P75, P90
        of current sector data.

        Args:
            value: Company's metric value
            benchmark: IndustryBenchmark with calculated percentiles
            metric_name: Optional metric name for context

        Returns:
            PerformanceZone with interpretation

        Example:
            >>> # Apple ROE = 164.6%, Sector P90 = 98.3%
            >>> zone = FranklinInterpretation.interpret_value(
            ...     value=164.6,
            ...     benchmark=roe_benchmark,
            ...     metric_name='ROE'
            ... )
            >>> print(zone.name)  # "Elite Performance"
            >>> print(zone.description)  # "Top 10% of sector (P90: 98.3%)"
        """
        metric_str = f"{metric_name} " if metric_name else ""

        # Elite Performance: Above P90
        if value >= benchmark.p90:
            return PerformanceZone(
                name="Elite Performance",
                icon="🏆",
                description=(
                    f"{metric_str}in top 10% of sector "
                    f"(P90: {benchmark.p90:.1f}, n={benchmark.sample_size})"
                ),
                relative_position="top",
                percentile_range="P90-P100"
            )

        # Strong Performance: P75-P90
        elif value >= benchmark.p75:
            return PerformanceZone(
                name="Strong Performance",
                icon="↗️",
                description=(
                    f"{metric_str}in top quartile "
                    f"(P75: {benchmark.p75:.1f}, P90: {benchmark.p90:.1f})"
                ),
                relative_position="above_avg",
                percentile_range="P75-P89"
            )

        # Above Median: P50-P75
        elif value >= benchmark.p50:
            return PerformanceZone(
                name="Above Median",
                icon="✅",
                description=(
                    f"{metric_str}above sector median "
                    f"(P50: {benchmark.p50:.1f}, P75: {benchmark.p75:.1f})"
                ),
                relative_position="avg",
                percentile_range="P50-P74"
            )

        # Below Median: P25-P50
        elif value >= benchmark.p25:
            return PerformanceZone(
                name="Below Median",
                icon="↘️",
                description=(
                    f"{metric_str}below sector median "
                    f"(P25: {benchmark.p25:.1f}, P50: {benchmark.p50:.1f})"
                ),
                relative_position="below_avg",
                percentile_range="P25-P49"
            )

        # Underperformance: Below P25
        else:
            return PerformanceZone(
                name="Underperformance",
                icon="🔻",
                description=(
                    f"{metric_str}in bottom quartile "
                    f"(P10: {benchmark.p10:.1f}, P25: {benchmark.p25:.1f})"
                ),
                relative_position="bottom",
                percentile_range="P0-P24"
            )

    @staticmethod
    def interpret_percentile(
        percentile: int,
        benchmark: IndustryBenchmark,
        metric_name: Optional[str] = None
    ) -> PerformanceZone:
        """
        Interpret performance from pre-calculated percentile

        Args:
            percentile: Percentile rank (0-100)
            benchmark: IndustryBenchmark for context
            metric_name: Optional metric name

        Returns:
            PerformanceZone

        Example:
            >>> zone = FranklinInterpretation.interpret_percentile(
            ...     percentile=95,
            ...     benchmark=roe_benchmark,
            ...     metric_name='ROE'
            ... )
            >>> print(zone.icon)  # "🏆"
        """
        metric_str = f"{metric_name} " if metric_name else ""

        if percentile >= 90:
            return PerformanceZone(
                name="Elite Performance",
                icon="🏆",
                description=f"{metric_str}in top 10% ({percentile}th percentile)",
                relative_position="top",
                percentile_range="P90-P100"
            )
        elif percentile >= 75:
            return PerformanceZone(
                name="Strong Performance",
                icon="↗️",
                description=f"{metric_str}in top quartile ({percentile}th percentile)",
                relative_position="above_avg",
                percentile_range="P75-P89"
            )
        elif percentile >= 50:
            return PerformanceZone(
                name="Above Median",
                icon="✅",
                description=f"{metric_str}above median ({percentile}th percentile)",
                relative_position="avg",
                percentile_range="P50-P74"
            )
        elif percentile >= 25:
            return PerformanceZone(
                name="Below Median",
                icon="↘️",
                description=f"{metric_str}below median ({percentile}th percentile)",
                relative_position="below_avg",
                percentile_range="P25-P49"
            )
        else:
            return PerformanceZone(
                name="Underperformance",
                icon="🔻",
                description=f"{metric_str}in bottom quartile ({percentile}th percentile)",
                relative_position="bottom",
                percentile_range="P0-P24"
            )

    @staticmethod
    def get_signal_type(
        value: float,
        benchmark: IndustryBenchmark,
        inverse: bool = False
    ) -> str:
        """
        Determine signal type (BUY/WATCH/RED_FLAG) from benchmark

        Logic:
        - BUY: Top quartile (>= P75)
        - WATCH: Middle 50% (P25-P75)
        - RED_FLAG: Bottom quartile (< P25)

        Args:
            value: Company's metric value
            benchmark: IndustryBenchmark with thresholds
            inverse: If True, reverse logic (for debt metrics)

        Returns:
            'BUY', 'WATCH', or 'RED_FLAG'

        Example:
            >>> # ROE = 150%, P75 = 45.7%
            >>> signal = FranklinInterpretation.get_signal_type(
            ...     value=150.0,
            ...     benchmark=roe_benchmark
            ... )
            >>> print(signal)  # "BUY"

            >>> # DebtToEquity = 2.5, P75 = 0.8 (inverse logic)
            >>> signal = FranklinInterpretation.get_signal_type(
            ...     value=2.5,
            ...     benchmark=debt_benchmark,
            ...     inverse=True
            ... )
            >>> print(signal)  # "RED_FLAG" (high debt is bad)
        """
        if not inverse:
            # Higher is better (ROE, margins, etc.)
            if value >= benchmark.p75:
                return 'BUY'
            elif value >= benchmark.p25:
                return 'WATCH'
            else:
                return 'RED_FLAG'
        else:
            # Lower is better (debt ratios, etc.)
            if value <= benchmark.p25:
                return 'BUY'
            elif value <= benchmark.p75:
                return 'WATCH'
            else:
                return 'RED_FLAG'
