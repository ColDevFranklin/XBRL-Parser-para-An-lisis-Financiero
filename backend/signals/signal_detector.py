# backend/signals/signal_detector.py
"""
Signal Detector - Core Detection Logic

Compares calculated financial metrics against defined thresholds to generate
actionable investment signals (BUY, WATCH, RED_FLAG).
"""

import numpy as np
from typing import Dict, List, Optional
from backend.signals.signal_taxonomy import (
    Signal,
    SignalType,
    SignalCategory,
    SIGNAL_THRESHOLDS
)


class SignalDetector:
    """
    Detects investment signals by comparing metrics against thresholds.

    Attributes:
        metrics: Dict of calculated metrics from MetricsCalculator
                 Format: {'profitability': {'ROE': array([...]), ...}, ...}
        company: Company ticker symbol for context
    """

    def __init__(self, metrics: Dict[str, Dict[str, np.ndarray]], company: str):
        """
        Initialize signal detector.

        Args:
            metrics: Nested dict of calculated metrics by category
            company: Company ticker (e.g., "AAPL")
        """
        self.metrics = metrics
        self.company = company
        self._signals_cache: Optional[Dict[str, List[Signal]]] = None

    def detect_all(self) -> Dict[str, List[Signal]]:
        """
        Detect all signals across all categories.

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

        # Detect signals by category
        all_signals['buy'].extend(self.detect_profitability_signals(SignalType.BUY))
        all_signals['buy'].extend(self.detect_liquidity_signals(SignalType.BUY))
        all_signals['buy'].extend(self.detect_efficiency_signals(SignalType.BUY))
        all_signals['buy'].extend(self.detect_leverage_signals(SignalType.BUY))

        all_signals['watch'].extend(self.detect_profitability_signals(SignalType.WATCH))
        all_signals['watch'].extend(self.detect_liquidity_signals(SignalType.WATCH))
        all_signals['watch'].extend(self.detect_efficiency_signals(SignalType.WATCH))
        all_signals['watch'].extend(self.detect_leverage_signals(SignalType.WATCH))

        all_signals['red_flag'].extend(self.detect_profitability_signals(SignalType.RED_FLAG))
        all_signals['red_flag'].extend(self.detect_liquidity_signals(SignalType.RED_FLAG))
        all_signals['red_flag'].extend(self.detect_efficiency_signals(SignalType.RED_FLAG))
        all_signals['red_flag'].extend(self.detect_leverage_signals(SignalType.RED_FLAG))

        self._signals_cache = all_signals
        return all_signals

    def detect_profitability_signals(self, signal_type: SignalType) -> List[Signal]:
        """Detect profitability-related signals"""
        signals = []
        category_metrics = self.metrics.get('profitability', {})

        # ROE signals
        if 'ROE' in category_metrics:
            roe_signals = self._check_threshold(
                metric_name='ROE',
                values=category_metrics['ROE'],
                signal_type=signal_type,
                category=SignalCategory.PROFITABILITY
            )
            signals.extend(roe_signals)

        # Net Margin signals
        if 'NetMargin' in category_metrics:
            margin_signals = self._check_threshold(
                metric_name='NetMargin',
                values=category_metrics['NetMargin'],
                signal_type=signal_type,
                category=SignalCategory.PROFITABILITY
            )
            signals.extend(margin_signals)

        # ROIC signals
        if 'ROIC' in category_metrics:
            roic_signals = self._check_threshold(
                metric_name='ROIC',
                values=category_metrics['ROIC'],
                signal_type=signal_type,
                category=SignalCategory.PROFITABILITY
            )
            signals.extend(roic_signals)

        # OCF Margin signals
        if 'OCFMargin' in category_metrics:
            ocf_signals = self._check_threshold(
                metric_name='OCFMargin',
                values=category_metrics['OCFMargin'],
                signal_type=signal_type,
                category=SignalCategory.PROFITABILITY
            )
            signals.extend(ocf_signals)

        # Gross Margin signals
        if 'GrossMargin' in category_metrics:
            gross_signals = self._check_threshold(
                metric_name='GrossMargin',
                values=category_metrics['GrossMargin'],
                signal_type=signal_type,
                category=SignalCategory.PROFITABILITY
            )
            signals.extend(gross_signals)

        return signals

    def detect_liquidity_signals(self, signal_type: SignalType) -> List[Signal]:
        """Detect liquidity-related signals"""
        signals = []
        category_metrics = self.metrics.get('liquidity', {})

        # Current Ratio signals
        if 'CurrentRatio' in category_metrics:
            current_signals = self._check_threshold(
                metric_name='CurrentRatio',
                values=category_metrics['CurrentRatio'],
                signal_type=signal_type,
                category=SignalCategory.LIQUIDITY
            )
            signals.extend(current_signals)

        return signals

    def detect_efficiency_signals(self, signal_type: SignalType) -> List[Signal]:
        """Detect efficiency-related signals"""
        signals = []
        category_metrics = self.metrics.get('efficiency', {})

        # Asset Turnover signals
        if 'AssetTurnover' in category_metrics:
            turnover_signals = self._check_threshold(
                metric_name='AssetTurnover',
                values=category_metrics['AssetTurnover'],
                signal_type=signal_type,
                category=SignalCategory.EFFICIENCY
            )
            signals.extend(turnover_signals)

        # Inventory Turnover signals
        if 'InventoryTurnover' in category_metrics:
            inv_signals = self._check_threshold(
                metric_name='InventoryTurnover',
                values=category_metrics['InventoryTurnover'],
                signal_type=signal_type,
                category=SignalCategory.EFFICIENCY
            )
            signals.extend(inv_signals)

        # DSO signals
        if 'DSO' in category_metrics:
            dso_signals = self._check_threshold(
                metric_name='DSO',
                values=category_metrics['DSO'],
                signal_type=signal_type,
                category=SignalCategory.EFFICIENCY
            )
            signals.extend(dso_signals)

        return signals

    def detect_leverage_signals(self, signal_type: SignalType) -> List[Signal]:
        """Detect leverage-related signals"""
        signals = []
        category_metrics = self.metrics.get('leverage', {})

        # Debt to Equity signals
        if 'DebtToEquity' in category_metrics:
            dte_signals = self._check_threshold(
                metric_name='DebtToEquity',
                values=category_metrics['DebtToEquity'],
                signal_type=signal_type,
                category=SignalCategory.LEVERAGE
            )
            signals.extend(dte_signals)

        # Debt to Assets signals
        if 'DebtToAssets' in category_metrics:
            dta_signals = self._check_threshold(
                metric_name='DebtToAssets',
                values=category_metrics['DebtToAssets'],
                signal_type=signal_type,
                category=SignalCategory.LEVERAGE
            )
            signals.extend(dta_signals)

        # Interest Coverage signals
        if 'InterestCoverage' in category_metrics:
            ic_signals = self._check_threshold(
                metric_name='InterestCoverage',
                values=category_metrics['InterestCoverage'],
                signal_type=signal_type,
                category=SignalCategory.LEVERAGE
            )
            signals.extend(ic_signals)

        return signals

    def _check_threshold(
        self,
        metric_name: str,
        values: np.ndarray,
        signal_type: SignalType,
        category: SignalCategory
    ) -> List[Signal]:
        """
        Check if metric values cross threshold for given signal type.

        Args:
            metric_name: Name of metric to check
            values: Array of metric values (most recent first)
            signal_type: BUY, WATCH, or RED_FLAG
            category: Financial category

        Returns:
            List of Signal objects (empty if no threshold crossed)
        """
        # Find matching threshold
        threshold_obj = None
        for threshold_key, threshold in SIGNAL_THRESHOLDS.items():
            if threshold.metric_name == metric_name:
                # Check if this threshold has the signal type we're looking for
                if signal_type == SignalType.BUY and threshold.buy_threshold is not None:
                    threshold_obj = threshold
                    target_threshold = threshold.buy_threshold
                    break
                elif signal_type == SignalType.WATCH and threshold.watch_threshold is not None:
                    threshold_obj = threshold
                    target_threshold = threshold.watch_threshold
                    break
                elif signal_type == SignalType.RED_FLAG and threshold.red_flag_threshold is not None:
                    threshold_obj = threshold
                    target_threshold = threshold.red_flag_threshold
                    break

        if threshold_obj is None:
            return []  # No threshold defined for this metric + signal type

        # Get most recent value (first element)
        if len(values) == 0 or np.isnan(values[0]):
            return []

        current_value = values[0]

        # Check if threshold is crossed
        threshold_crossed = False
        if threshold_obj.comparison == '>':
            threshold_crossed = current_value > target_threshold
        elif threshold_obj.comparison == '<':
            threshold_crossed = current_value < target_threshold
        elif threshold_obj.comparison == '>=':
            threshold_crossed = current_value >= target_threshold
        elif threshold_obj.comparison == '<=':
            threshold_crossed = current_value <= target_threshold

        if not threshold_crossed:
            return []

        # Calculate trend if we have multi-year data
        trend_str = None
        if len(values) >= 2:
            trend_str = self._calculate_trend(values)

        # Generate message
        message = self._generate_message(
            metric_name=metric_name,
            current_value=current_value,
            threshold=target_threshold,
            comparison=threshold_obj.comparison,
            signal_type=signal_type
        )

        # FIX: Use positional arguments matching dataclass field order
        signal = Signal(
            signal_type,      # type: SignalType
            category,         # category: SignalCategory
            metric_name,      # metric: str
            current_value,    # value: float
            target_threshold, # threshold: float
            message,          # message: str
            trend_str         # trend: Optional[str]
        )

        return [signal]

    def _calculate_trend(self, values: np.ndarray) -> str:
        """
        Calculate YoY trend from time-series values.

        Args:
            values: Array of values (most recent first)

        Returns:
            Trend string (e.g., "+5.8% CAGR" or "declining -3.2% CAGR")
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
        threshold: float,
        comparison: str,
        signal_type: SignalType
    ) -> str:
        """Generate human-readable signal message"""

        # Format percentage metrics
        if metric_name in ['ROE', 'NetMargin', 'GrossMargin', 'OCFMargin', 'ROIC']:
            value_str = f"{current_value:.1f}%"
            threshold_str = f"{threshold:.1f}%"
        else:
            value_str = f"{current_value:.2f}"
            threshold_str = f"{threshold:.2f}"

        if signal_type == SignalType.BUY:
            return f"{metric_name} {value_str} {comparison} {threshold_str} threshold - Strong positive indicator"
        elif signal_type == SignalType.WATCH:
            return f"{metric_name} {value_str} {comparison} {threshold_str} - Requires monitoring"
        else:  # RED_FLAG
            return f"{metric_name} {value_str} {comparison} {threshold_str} - Concerning metric"
