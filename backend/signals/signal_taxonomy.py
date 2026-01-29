# backend/signals/signal_taxonomy.py
"""
Signal Taxonomy - Investment Signal Classification System

Defines the vocabulary and thresholds for detecting buy/watch/red_flag signals
based on value investing principles (Graham, Buffett, Munger).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SignalType(Enum):
    """Investment signal classification"""
    BUY = "buy"           # Strong positive indicator
    WATCH = "watch"       # Neutral/mixed signal requiring context
    RED_FLAG = "red_flag" # Concerning metric that needs investigation


class SignalCategory(Enum):
    """Financial statement category"""
    PROFITABILITY = "profitability"
    LIQUIDITY = "liquidity"
    EFFICIENCY = "efficiency"
    LEVERAGE = "leverage"


@dataclass
class SignalThreshold:
    """
    Threshold definition for a specific metric.

    Attributes:
        metric_name: Name of the financial metric (e.g., "ROE")
        buy_threshold: Value above which generates BUY signal
        watch_threshold: Value that triggers WATCH (can be above or below)
        red_flag_threshold: Value that triggers RED_FLAG
        comparison: Direction of comparison ('>', '<', 'between')
        justification: Theory-based reason (Graham/Buffett quote or principle)
    """
    metric_name: str
    buy_threshold: Optional[float]
    watch_threshold: Optional[float]
    red_flag_threshold: Optional[float]
    comparison: str  # '>', '<', 'between'
    justification: str


@dataclass
class Signal:
    """
    Detected investment signal with context.

    Attributes:
        type: BUY, WATCH, or RED_FLAG
        category: Which financial statement category
        metric: Metric name that triggered signal
        value: Actual metric value
        threshold: Threshold that was crossed
        message: Human-readable explanation
        trend: Optional YoY trend context (e.g., "+5.8% CAGR")
    """
    type: SignalType
    category: SignalCategory
    metric: str
    value: float
    threshold: float
    message: str
    trend: Optional[str] = None

    def __repr__(self) -> str:
        trend_str = f" [{self.trend}]" if self.trend else ""
        return (
            f"Signal({self.type.value.upper()}: {self.metric} = {self.value:.1f} "
            f"vs {self.threshold:.1f}{trend_str})"
        )


# ============================================================================
# SIGNAL THRESHOLDS - Graham/Buffett/Munger Methodology
# ============================================================================

SIGNAL_THRESHOLDS = {
    # ========================================================================
    # BUY SIGNALS (5) - Strong positive indicators
    # ========================================================================
    "roe_strong": SignalThreshold(
        metric_name="ROE",
        buy_threshold=15.0,
        watch_threshold=None,
        red_flag_threshold=None,
        comparison=">",
        justification=(
            "Graham: ROE >15% indicates sustainable competitive advantage (moat). "
            "Buffett seeks companies that can reinvest earnings at high rates."
        )
    ),

    "net_margin_premium": SignalThreshold(
        metric_name="NetMargin",
        buy_threshold=20.0,
        watch_threshold=None,
        red_flag_threshold=None,
        comparison=">",
        justification=(
            "Munger: 'Show me the incentive and I show you the outcome.' "
            "Net margins >20% suggest pricing power and operational excellence."
        )
    ),

    "roic_capital_efficient": SignalThreshold(
        metric_name="ROIC",
        buy_threshold=12.0,
        watch_threshold=None,
        red_flag_threshold=None,
        comparison=">",
        justification=(
            "Buffett: ROIC >12% (cost of capital proxy) creates shareholder value. "
            "Companies earning above their cost of capital compound wealth."
        )
    ),

    "cash_flow_margin_strong": SignalThreshold(
        metric_name="OCFMargin",
        buy_threshold=25.0,
        watch_threshold=None,
        red_flag_threshold=None,
        comparison=">",
        justification=(
            "Buffett: 'Cash is king.' OCF margin >25% indicates real earnings quality, "
            "not just accounting profits. Strong free cash flow generation."
        )
    ),

    "asset_turnover_efficient": SignalThreshold(
        metric_name="AssetTurnover",
        buy_threshold=1.0,
        watch_threshold=None,
        red_flag_threshold=None,
        comparison=">",
        justification=(
            "DuPont Analysis: Asset turnover >1.0 shows efficient asset utilization. "
            "Companies generate $1+ revenue per $1 of assets (capital-light models)."
        )
    ),

    # ========================================================================
    # WATCH SIGNALS (5) - Neutral/mixed indicators requiring context
    # ========================================================================
    "current_ratio_tight": SignalThreshold(
        metric_name="CurrentRatio",
        buy_threshold=None,
        watch_threshold=1.0,
        red_flag_threshold=None,
        comparison="<",
        justification=(
            "Traditional threshold: Current ratio <1.0 suggests tight liquidity. "
            "Context matters: Apple/MSFT manage this well, but watch for deterioration."
        )
    ),

    "debt_to_equity_moderate": SignalThreshold(
        metric_name="DebtToEquity",
        buy_threshold=None,
        watch_threshold=1.5,
        red_flag_threshold=None,
        comparison=">",
        justification=(
            "Buffett: Moderate leverage (1.5-2.5x) acceptable if interest coverage strong. "
            "Watch for increasing leverage trend - potential risk if business slows."
        )
    ),

    "inventory_turnover_slow": SignalThreshold(
        metric_name="InventoryTurnover",
        buy_threshold=None,
        watch_threshold=4.0,
        red_flag_threshold=None,
        comparison="<",
        justification=(
            "Inventory turnover <4x (90+ days) may indicate obsolescence risk or "
            "demand weakness. Context: Tech hardware vs. luxury goods differ."
        )
    ),

    "gross_margin_compression": SignalThreshold(
        metric_name="GrossMargin",
        buy_threshold=None,
        watch_threshold=30.0,
        red_flag_threshold=None,
        comparison="<",
        justification=(
            "Munger: Gross margin <30% in previously high-margin business signals "
            "competitive pressure or pricing power loss. Watch trend direction."
        )
    ),

    "days_sales_outstanding_high": SignalThreshold(
        metric_name="DSO",
        buy_threshold=None,
        watch_threshold=60.0,
        red_flag_threshold=None,
        comparison=">",
        justification=(
            "DSO >60 days suggests customers delaying payment (potential credit issues) "
            "or aggressive revenue recognition. Monitor for accounts receivable quality."
        )
    ),

    # ========================================================================
    # RED_FLAG SIGNALS (5) - Concerning metrics needing investigation
    # ========================================================================
    "roe_declining": SignalThreshold(
        metric_name="ROE",
        buy_threshold=None,
        watch_threshold=None,
        red_flag_threshold=8.0,
        comparison="<",
        justification=(
            "Graham: ROE <8% signals capital allocation problem. "
            "Company destroying value - earns less than Treasury yields historically."
        )
    ),

    "interest_coverage_weak": SignalThreshold(
        metric_name="InterestCoverage",
        buy_threshold=None,
        watch_threshold=None,
        red_flag_threshold=3.0,
        comparison="<",
        justification=(
            "Buffett: Interest coverage <3x means company vulnerable to rate hikes or "
            "earnings decline. Distress risk if coverage drops below 2x."
        )
    ),

    "current_ratio_distress": SignalThreshold(
        metric_name="CurrentRatio",
        buy_threshold=None,
        watch_threshold=None,
        red_flag_threshold=0.5,
        comparison="<",
        justification=(
            "Current ratio <0.5 signals severe liquidity crisis. "
            "Company may struggle to meet short-term obligations (bankruptcy risk)."
        )
    ),

    "debt_to_assets_overleveraged": SignalThreshold(
        metric_name="DebtToAssets",
        buy_threshold=None,
        watch_threshold=None,
        red_flag_threshold=0.7,
        comparison=">",
        justification=(
            "Graham: Debt/Assets >70% leaves little equity cushion. "
            "High financial risk - vulnerable to asset write-downs or recession."
        )
    ),

    "negative_operating_cash_flow": SignalThreshold(
        metric_name="OCFMargin",
        buy_threshold=None,
        watch_threshold=None,
        red_flag_threshold=0.0,
        comparison="<",
        justification=(
            "Buffett: Negative operating cash flow means burning cash to operate. "
            "Unsustainable unless startup/turnaround. Validate business model viability."
        )
    ),
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_threshold(metric_name: str, signal_type: SignalType) -> Optional[SignalThreshold]:
    """
    Retrieve threshold configuration for a specific metric and signal type.

    Args:
        metric_name: Name of metric (e.g., "ROE", "CurrentRatio")
        signal_type: BUY, WATCH, or RED_FLAG

    Returns:
        SignalThreshold if found, None otherwise
    """
    for threshold_key, threshold in SIGNAL_THRESHOLDS.items():
        if threshold.metric_name != metric_name:
            continue

        if signal_type == SignalType.BUY and threshold.buy_threshold is not None:
            return threshold
        elif signal_type == SignalType.WATCH and threshold.watch_threshold is not None:
            return threshold
        elif signal_type == SignalType.RED_FLAG and threshold.red_flag_threshold is not None:
            return threshold

    return None


def list_thresholds_by_category(category: SignalCategory) -> list[SignalThreshold]:
    """
    List all thresholds for a specific financial category.

    Args:
        category: PROFITABILITY, LIQUIDITY, EFFICIENCY, or LEVERAGE

    Returns:
        List of SignalThreshold objects for that category
    """
    # Mapping metrics to categories
    category_metrics = {
        SignalCategory.PROFITABILITY: ["ROE", "NetMargin", "ROIC", "OCFMargin", "GrossMargin"],
        SignalCategory.LIQUIDITY: ["CurrentRatio", "QuickRatio", "CashRatio"],
        SignalCategory.EFFICIENCY: ["AssetTurnover", "InventoryTurnover", "DSO"],
        SignalCategory.LEVERAGE: ["DebtToEquity", "DebtToAssets", "InterestCoverage"],
    }

    relevant_metrics = category_metrics.get(category, [])
    return [
        threshold for threshold in SIGNAL_THRESHOLDS.values()
        if threshold.metric_name in relevant_metrics
    ]
