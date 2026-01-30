"""
Signal Detector - Dynamic Detection Using Franklin Framework

Compares financial metrics against REAL sector benchmarks (no hardcoded thresholds).
Uses StatisticalBenchmarkEngine for dynamic threshold calculation.

Author: @franklin (CTO)
Sprint 5 - Franklin Framework Refactor
"""

import numpy as np
from typing import Dict, List, Optional
from backend.signals.signal_taxonomy import Signal, SignalType, SignalCategory
from backend.signals.statistical_engine import StatisticalBenchmarkEngine
from backend.signals.franklin_interpretation import FranklinInterpretation


# Metric configuration: which metrics use inverse logic (lower is better)
INVERSE_METRICS = {
    'DebtToEquity', 'DebtToAssets', 'DSO'  # Lower debt/DSO is better
}


class SignalDetector:
    """
    Detects investment signals using dynamic sector benchmarks

    CHANGE FROM PREVIOUS VERSION:
    - ❌ REMOVED: Hardcoded SIGNAL_THRESHOLDS dict
    - ✅ ADDED: StatisticalBenchmarkEngine integration
    - ✅ ADDED: Dynamic threshold calculation from real data

    Attributes:
        metrics: Dict of calculated metrics from MetricsCalculator
        company: Company ticker symbol
        benchmark_engine: Engine with sector benchmarks
    """

    def __init__(
        self,
        metrics: Dict[str, Dict[str, np.ndarray]],
        company: str,
        benchmark_engine: StatisticalBenchmarkEngine
    ):
        """
        Initialize signal detector with dynamic benchmarks

        Args:
            metrics: Nested dict of calculated metrics by category
            company: Company ticker (e.g., "AAPL")
            benchmark_engine: Initialized StatisticalBenchmarkEngine

        Example:
            >>> from backend.parsers.sec_downloader import load_json
            >>>
            >>> # Load sector data
            >>> sector_data = load_json('outputs/sector_benchmarks_tech.json')
            >>> engine = StatisticalBenchmarkEngine(sector_data)
            >>>
            >>> # Initialize detector
            >>> detector = SignalDetector(
            ...     metrics=aapl_metrics,
            ...     company='AAPL',
            ...     benchmark_engine=engine
            ... )
        """
        self.metrics = metrics
        self.company = company
        self.benchmark_engine = benchmark_engine
        self._signals_cache: Optional[Dict[str, List[Signal]]] = None

    def detect_all(self) -> Dict[str, List[Signal]]:
        """
        Detect all signals across all categories using dynamic thresholds

        Returns:
            Dict with keys: 'buy', 'watch', 'red_flag'
            Each containing list of Signal objects
        """
        if self._signals_cache is not None:
            return self._signals_cache

        all_signals = {
            'buy': [],
            'watch': [],
            'red_flag': []
        }

        # Detect signals for each category
        for category, metrics_dict in self.metrics.items():
            for metric_name, values in metrics_dict.items():
                signals = self._detect_metric_signals(
                    category=category,
                    metric_name=metric_name,
                    values=values
                )

                # Categorize signals by type
                for signal in signals:
                    if signal.type == SignalType.BUY:
                        all_signals['buy'].append(signal)
                    elif signal.type == SignalType.WATCH:
                        all_signals['watch'].append(signal)
                    elif signal.type == SignalType.RED_FLAG:
                        all_signals['red_flag'].append(signal)

        self._signals_cache = all_signals
        return all_signals

    def _detect_metric_signals(
        self,
        category: str,
        metric_name: str,
        values: np.ndarray
    ) -> List[Signal]:
        """
        Detect signals for a single metric using dynamic benchmarks

        Args:
            category: Financial category (e.g., 'profitability')
            metric_name: Metric name (e.g., 'ROE')
            values: Time-series values (latest first at index 0)

        Returns:
            List of Signal objects (empty if no benchmark available)
        """
        # Get industry benchmark (dynamic thresholds)
        benchmark = self.benchmark_engine.calculate_benchmarks(category, metric_name)
        if not benchmark:
            return []  # No benchmark available for this metric

        # Get latest value
        if len(values) == 0 or np.isnan(values[0]):
            return []

        current_value = float(values[0])

        # Determine if metric uses inverse logic (lower is better)
        is_inverse = metric_name in INVERSE_METRICS

        # Get signal type using Franklin Framework
        signal_type_str = FranklinInterpretation.get_signal_type(
            value=current_value,
            benchmark=benchmark,
            inverse=is_inverse
        )

        # Map string to SignalType enum
        signal_type = {
            'BUY': SignalType.BUY,
            'WATCH': SignalType.WATCH,
            'RED_FLAG': SignalType.RED_FLAG
        }[signal_type_str]

        # Map category string to SignalCategory enum
        category_enum = self._get_category_enum(category)

        # Get appropriate threshold based on signal type
        if signal_type == SignalType.BUY:
            threshold = benchmark.p75
        elif signal_type == SignalType.WATCH:
            threshold = benchmark.p50
        else:  # RED_FLAG
            threshold = benchmark.p25

        # Calculate trend if multi-year data available
        trend_str = None
        if len(values) >= 2:
            trend_str = self._calculate_trend(values)

        # Generate message with context
        message = self._generate_message(
            metric_name=metric_name,
            current_value=current_value,
            benchmark=benchmark,
            signal_type=signal_type,
            is_inverse=is_inverse
        )

        # Create Signal object
        signal = Signal(
            signal_type,
            category_enum,
            metric_name,
            current_value,
            threshold,
            message,
            trend_str
        )

        return [signal]

    def _get_category_enum(self, category: str) -> SignalCategory:
        """Map category string to SignalCategory enum"""
        mapping = {
            'profitability': SignalCategory.PROFITABILITY,
            'liquidity': SignalCategory.LIQUIDITY,
            'efficiency': SignalCategory.EFFICIENCY,
            'leverage': SignalCategory.LEVERAGE,
        }
        # Default to PROFITABILITY if category not found
        return mapping.get(category, SignalCategory.PROFITABILITY)

    def _calculate_trend(self, values: np.ndarray) -> str:
        """
        Calculate YoY trend from time-series values

        Args:
            values: Array of values (most recent first)

        Returns:
            Trend string (e.g., "+5.8% CAGR" or "-3.2% CAGR")
        """
        if len(values) < 2:
            return ""

        # Remove NaN values
        clean_values = values[~np.isnan(values)]
        if len(clean_values) < 2:
            return ""

        # CAGR calculation: (ending_value / beginning_value)^(1/years) - 1
        most_recent = clean_values[0]
        oldest = clean_values[-1]
        years = len(clean_values) - 1

        if oldest <= 0:  # Avoid division by zero or negative base
            return ""

        cagr = (np.power(most_recent / oldest, 1 / years) - 1) * 100

        if cagr > 0:
            return f"+{cagr:.1f}% CAGR"
        else:
            return f"{cagr:.1f}% CAGR"

    def _generate_message(
        self,
        metric_name: str,
        current_value: float,
        benchmark,
        signal_type: SignalType,
        is_inverse: bool
    ) -> str:
        """
        Generate human-readable signal message with sector context

        Args:
            metric_name: Name of metric
            current_value: Company's value
            benchmark: IndustryBenchmark with sector stats
            signal_type: BUY/WATCH/RED_FLAG
            is_inverse: Whether lower is better

        Returns:
            Contextualized message string
        """
        # Format percentage metrics
        if metric_name in ['ROE', 'NetMargin', 'GrossMargin', 'OCFMargin', 'ROIC']:
            value_str = f"{current_value:.1f}%"
            p50_str = f"{benchmark.p50:.1f}%"
            p75_str = f"{benchmark.p75:.1f}%"
            p25_str = f"{benchmark.p25:.1f}%"
        else:
            value_str = f"{current_value:.2f}"
            p50_str = f"{benchmark.p50:.2f}"
            p75_str = f"{benchmark.p75:.2f}"
            p25_str = f"{benchmark.p25:.2f}"

        if signal_type == SignalType.BUY:
            if is_inverse:
                return (
                    f"{metric_name} {value_str} < sector P25 ({p25_str}) - "
                    f"Top quartile (low is good), n={benchmark.sample_size}"
                )
            else:
                return (
                    f"{metric_name} {value_str} > sector P75 ({p75_str}) - "
                    f"Top quartile, n={benchmark.sample_size}"
                )

        elif signal_type == SignalType.WATCH:
            return (
                f"{metric_name} {value_str} near sector median ({p50_str}) - "
                f"Middle 50%, requires monitoring, n={benchmark.sample_size}"
            )

        else:  # RED_FLAG
            if is_inverse:
                return (
                    f"{metric_name} {value_str} > sector P75 ({p75_str}) - "
                    f"Bottom quartile (high is concerning), n={benchmark.sample_size}"
                )
            else:
                return (
                    f"{metric_name} {value_str} < sector P25 ({p25_str}) - "
                    f"Bottom quartile, n={benchmark.sample_size}"
                )

    # Legacy methods (kept for backward compatibility, now use detect_all)
    def detect_profitability_signals(self, signal_type: SignalType) -> List[Signal]:
        """DEPRECATED: Use detect_all() instead"""
        all_signals = self.detect_all()
        return [s for s in all_signals[signal_type.value.lower()]
                if s.category == SignalCategory.PROFITABILITY]

    def detect_liquidity_signals(self, signal_type: SignalType) -> List[Signal]:
        """DEPRECATED: Use detect_all() instead"""
        all_signals = self.detect_all()
        return [s for s in all_signals[signal_type.value.lower()]
                if s.category == SignalCategory.LIQUIDITY]

    def detect_efficiency_signals(self, signal_type: SignalType) -> List[Signal]:
        """DEPRECATED: Use detect_all() instead"""
        all_signals = self.detect_all()
        return [s for s in all_signals[signal_type.value.lower()]
                if s.category == SignalCategory.EFFICIENCY]

    def detect_leverage_signals(self, signal_type: SignalType) -> List[Signal]:
        """DEPRECATED: Use detect_all() instead"""
        all_signals = self.detect_all()
        return [s for s in all_signals[signal_type.value.lower()]
                if s.category == SignalCategory.LEVERAGE]
