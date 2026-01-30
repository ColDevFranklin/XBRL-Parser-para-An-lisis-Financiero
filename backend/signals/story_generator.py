"""
Story Arc Generator - Narrative Intelligence Layer
Converts multi-year financial trends into human-readable investment narratives.

This module detects patterns in time-series data and generates contextual
stories that help investors understand the "why" behind the numbers.

Author: @franklin (CTO)
Sprint 5 - Micro-Tarea 4: Story Arc Generator
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict
import numpy as np
from scipy import stats


class StoryPattern(Enum):
    """
    Pattern types detected in multi-year financial trends.

    Attributes:
        ACCELERATION: Strong positive CAGR (>5%) - improving trend
        TURNAROUND: Negative to positive transition - recovery story
        PLATEAU: Stable performance (±2% CAGR) - consistency
        DETERIORATION: Strong negative CAGR (<-5%) - declining trend
        VOLATILE: High variance - inconsistent performance
    """
    ACCELERATION = "ACCELERATION"
    TURNAROUND = "TURNAROUND"
    PLATEAU = "PLATEAU"
    DETERIORATION = "DETERIORATION"
    VOLATILE = "VOLATILE"


class ConfidenceLevel(Enum):
    """
    Statistical confidence in pattern detection.

    Based on R² (coefficient of determination):
    - HIGH: R² > 0.7 (linear trend, predictable)
    - MEDIUM: R² 0.4-0.7 (some noise, moderate confidence)
    - LOW: R² < 0.4 (volatile, low predictability)
    """
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class StoryArc:
    """
    Complete narrative for a financial metric's multi-year trend.

    Attributes:
        metric_name: Name of the financial metric (e.g., 'ROE', 'NetMargin')
        pattern: Detected pattern type (ACCELERATION, TURNAROUND, etc.)
        cagr: Compound Annual Growth Rate (%)
        narrative: Human-readable story (2-3 sentences)
        confidence: Statistical confidence in pattern (HIGH/MEDIUM/LOW)
        r_squared: R² value (goodness of fit)
        start_value: First year value
        end_value: Latest year value
        years: Number of years analyzed
        context: Optional business context (category-specific)
    """
    metric_name: str
    pattern: StoryPattern
    cagr: float
    narrative: str
    confidence: ConfidenceLevel
    r_squared: float
    start_value: float
    end_value: float
    years: int
    context: Optional[str] = None


# Story Templates - Pattern-Specific Narratives
STORY_TEMPLATES = {
    StoryPattern.ACCELERATION: {
        'profitability': (
            "{metric} accelerated from {start:.1f}% to {end:.1f}% ({cagr:+.1f}% CAGR), "
            "demonstrating exceptional operational improvement and margin expansion. "
            "This sustained growth trajectory suggests strong competitive positioning."
        ),
        'liquidity': (
            "{metric} strengthened from {start:.2f} to {end:.2f} ({cagr:+.1f}% CAGR), "
            "reflecting improved working capital management and financial flexibility. "
            "Rising liquidity reduces default risk and enables strategic investments."
        ),
        'efficiency': (
            "{metric} improved from {start:.2f} to {end:.2f} ({cagr:+.1f}% CAGR), "
            "indicating enhanced asset utilization and operational efficiency. "
            "Better efficiency ratios typically drive margin expansion and cash generation."
        ),
        'leverage': (
            "{metric} improved from {start:.2f} to {end:.2f} ({cagr:+.1f}% CAGR), "
            "demonstrating proactive balance sheet optimization and reduced financial risk. "
            "Lower leverage enhances financial stability and strategic optionality."
        ),
        'default': (
            "{metric} grew from {start:.1f} to {end:.1f} ({cagr:+.1f}% CAGR), "
            "showing consistent improvement across the analysis period. "
            "This positive momentum suggests operational strength."
        )
    },

    StoryPattern.TURNAROUND: {
        'profitability': (
            "{metric} executed a dramatic turnaround from {start:.1f}% to {end:.1f}%, "
            "reversing earlier weakness and returning to profitability. "
            "This recovery demonstrates management's ability to restructure operations and restore margins."
        ),
        'liquidity': (
            "{metric} recovered from stressed levels ({start:.2f}) to healthy territory ({end:.2f}), "
            "indicating successful working capital optimization. "
            "The turnaround reduces liquidity risk and improves credit profile."
        ),
        'efficiency': (
            "{metric} rebounded from {start:.2f} to {end:.2f}, "
            "suggesting operational fixes are taking hold and asset productivity is improving. "
            "Continued execution will be critical to sustain this momentum."
        ),
        'leverage': (
            "{metric} improved from elevated levels ({start:.2f}) to safer territory ({end:.2f}), "
            "reflecting aggressive deleveraging and balance sheet repair. "
            "Reduced debt burden enhances financial flexibility."
        ),
        'default': (
            "{metric} recovered from {start:.1f} to {end:.1f}, "
            "demonstrating a successful turnaround in this key financial indicator. "
            "Monitor sustainability of this improvement."
        )
    },

    StoryPattern.PLATEAU: {
        'profitability': (
            "{metric} remained stable at ~{start:.1f}% ({cagr:+.1f}% CAGR), "
            "demonstrating consistent but not expanding margins. "
            "Stability is positive, but lack of growth may indicate competitive pressures or market maturity."
        ),
        'liquidity': (
            "{metric} held steady around {start:.2f} ({cagr:+.1f}% CAGR), "
            "maintaining adequate but not improving liquidity buffers. "
            "Stable liquidity is acceptable but offers limited upside."
        ),
        'efficiency': (
            "{metric} plateaued near {start:.2f} ({cagr:+.1f}% CAGR), "
            "suggesting efficiency gains have stalled. "
            "Further optimization may be difficult without operational restructuring."
        ),
        'leverage': (
            "{metric} remained flat around {start:.2f} ({cagr:+.1f}% CAGR), "
            "indicating stable but not improving balance sheet health. "
            "Monitor for signs of renewed deleveraging or deterioration."
        ),
        'default': (
            "{metric} stabilized around {start:.1f} ({cagr:+.1f}% CAGR), "
            "showing consistency but limited momentum. "
            "Evaluate whether stability reflects maturity or operational stagnation."
        )
    },

    StoryPattern.DETERIORATION: {
        'profitability': (
            "{metric} declined from {start:.1f}% to {end:.1f}% ({cagr:.1f}% CAGR), "
            "signaling margin compression and operational challenges. "
            "This deterioration raises concerns about competitive positioning and pricing power."
        ),
        'liquidity': (
            "{metric} weakened from {start:.2f} to {end:.2f} ({cagr:.1f}% CAGR), "
            "indicating deteriorating working capital and rising liquidity risk. "
            "Declining liquidity may constrain strategic flexibility and increase refinancing risk."
        ),
        'efficiency': (
            "{metric} deteriorated from {start:.2f} to {end:.2f} ({cagr:.1f}% CAGR), "
            "suggesting declining asset productivity and operational inefficiencies. "
            "Poor efficiency trends typically pressure margins and cash flow."
        ),
        'leverage': (
            "{metric} worsened from {start:.2f} to {end:.2f} ({cagr:.1f}% CAGR), "
            "reflecting rising financial risk and balance sheet deterioration. "
            "Increasing leverage limits strategic options and raises credit concerns."
        ),
        'default': (
            "{metric} declined from {start:.1f} to {end:.1f} ({cagr:.1f}% CAGR), "
            "showing concerning deterioration in this key metric. "
            "Investigate root causes and assess management's turnaround plan."
        )
    },

    StoryPattern.VOLATILE: {
        'profitability': (
            "{metric} fluctuated between {start:.1f}% and {end:.1f}% with high variability, "
            "indicating inconsistent operational execution or cyclical business dynamics. "
            "Volatility complicates valuation and suggests higher business risk."
        ),
        'liquidity': (
            "{metric} oscillated between {start:.2f} and {end:.2f} with significant volatility, "
            "reflecting unstable working capital management. "
            "Inconsistent liquidity increases refinancing risk and limits strategic predictability."
        ),
        'efficiency': (
            "{metric} varied between {start:.2f} and {end:.2f} without clear trend, "
            "suggesting inconsistent asset utilization. "
            "High volatility may indicate operational instability or lumpy business model."
        ),
        'leverage': (
            "{metric} swung between {start:.2f} and {end:.2f} with high variability, "
            "reflecting unstable balance sheet management. "
            "Leverage volatility complicates credit assessment and risk pricing."
        ),
        'default': (
            "{metric} varied between {start:.1f} and {end:.1f} with high volatility, "
            "showing inconsistent performance without clear direction. "
            "High variability suggests unpredictable business dynamics."
        )
    }
}


class StoryGenerator:
    """
    Generates investment narratives from multi-year financial trends.

    This class detects patterns (ACCELERATION, TURNAROUND, etc.) and
    generates human-readable stories that contextualize the numbers.

    Example:
        >>> generator = StoryGenerator()
        >>> values = [151.9, 164.6, 156.1, 197.0]  # Apple ROE 2022-2025
        >>> story = generator.generate_story('ROE', values, category='profitability')
        >>> print(story.narrative)
        "ROE accelerated from 151.9% to 197.0% (+9.1% CAGR), demonstrating
         exceptional operational improvement..."
    """

    def __init__(self):
        """Initialize Story Generator."""
        self.templates = STORY_TEMPLATES

    def calculate_cagr(self, values: List[float]) -> float:
        """
        Calculate Compound Annual Growth Rate.

        Args:
            values: Time-series values (oldest to newest)

        Returns:
            CAGR as percentage

        Example:
            >>> calculate_cagr([100, 110, 121, 133])
            10.0  # 10% CAGR
        """
        if len(values) < 2:
            return 0.0

        start = values[0]
        end = values[-1]
        years = len(values) - 1

        if start <= 0:
            # Handle negative/zero start values
            return 0.0

        cagr = (((end / start) ** (1 / years)) - 1) * 100
        return cagr

    def calculate_r_squared(self, values: List[float]) -> float:
        """
        Calculate R² (coefficient of determination) for linear trend.

        R² measures how well a linear trend fits the data:
        - R² = 1.0: Perfect linear fit
        - R² = 0.5: Moderate fit (some noise)
        - R² = 0.0: No linear relationship

        Args:
            values: Time-series values

        Returns:
            R² value (0.0 to 1.0)
        """
        if len(values) < 2:
            return 0.0

        x = np.arange(len(values))
        y = np.array(values)

        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        r_squared = r_value ** 2

        return r_squared

    def detect_pattern(
        self,
        values: List[float],
        cagr: float,
        r_squared: float
    ) -> StoryPattern:
        """
        Detect story pattern from time-series data.

        Pattern Logic:
        - ACCELERATION: CAGR > 5% and R² > 0.4 (strong positive trend)
        - TURNAROUND: Negative → Positive (recovery)
        - PLATEAU: -2% < CAGR < 2% (stable)
        - DETERIORATION: CAGR < -5% and R² > 0.4 (strong negative trend)
        - VOLATILE: R² < 0.4 (inconsistent, no clear trend)

        Args:
            values: Time-series values
            cagr: Compound Annual Growth Rate (%)
            r_squared: R² coefficient

        Returns:
            Detected StoryPattern
        """
        # Check for turnaround (negative → positive)
        if values[0] < 0 and values[-1] > 0:
            return StoryPattern.TURNAROUND

        # Check for volatile (low R²)
        if r_squared < 0.4:
            return StoryPattern.VOLATILE

        # Check for acceleration (strong positive trend)
        if cagr > 5.0:
            return StoryPattern.ACCELERATION

        # Check for deterioration (strong negative trend)
        if cagr < -5.0:
            return StoryPattern.DETERIORATION

        # Default: plateau (stable)
        return StoryPattern.PLATEAU

    def get_confidence(self, r_squared: float) -> ConfidenceLevel:
        """
        Determine confidence level from R².

        Args:
            r_squared: R² coefficient (0.0 to 1.0)

        Returns:
            Confidence level (HIGH/MEDIUM/LOW)
        """
        if r_squared >= 0.7:
            return ConfidenceLevel.HIGH
        elif r_squared >= 0.4:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def generate_narrative(
        self,
        metric_name: str,
        pattern: StoryPattern,
        cagr: float,
        start_value: float,
        end_value: float,
        category: Optional[str] = None
    ) -> str:
        """
        Generate human-readable narrative from template.

        Args:
            metric_name: Name of metric (e.g., 'ROE')
            pattern: Detected pattern type
            cagr: CAGR percentage
            start_value: First year value
            end_value: Latest year value
            category: Optional category ('profitability', 'liquidity', etc.)

        Returns:
            Formatted narrative string
        """
        # Get template for pattern + category
        templates = self.templates.get(pattern, {})

        # Try category-specific template first, fallback to default
        if category and category.lower() in templates:
            template = templates[category.lower()]
        else:
            template = templates.get('default', templates.get('profitability', ''))

        # Format template with values
        narrative = template.format(
            metric=metric_name,
            start=start_value,
            end=end_value,
            cagr=cagr
        )

        return narrative

    def generate_story(
        self,
        metric_name: str,
        values: List[float],
        category: Optional[str] = None
    ) -> StoryArc:
        """
        Generate complete story arc for a metric's trend.

        This is the main public API for story generation.

        Args:
            metric_name: Name of metric (e.g., 'ROE', 'CurrentRatio')
            values: Time-series values (oldest to newest)
            category: Optional category for context ('profitability', 'liquidity', etc.)

        Returns:
            Complete StoryArc with pattern, narrative, and metadata

        Raises:
            ValueError: If values list is too short (< 2 years)

        Example:
            >>> generator = StoryGenerator()
            >>> story = generator.generate_story(
            ...     'ROE',
            ...     [151.9, 164.6, 156.1, 197.0],
            ...     category='profitability'
            ... )
            >>> print(f"{story.pattern.value}: {story.narrative}")
        """
        if len(values) < 2:
            raise ValueError(f"Need at least 2 years of data, got {len(values)}")

        # Calculate metrics
        cagr = self.calculate_cagr(values)
        r_squared = self.calculate_r_squared(values)

        # Detect pattern
        pattern = self.detect_pattern(values, cagr, r_squared)

        # Get confidence
        confidence = self.get_confidence(r_squared)

        # Generate narrative
        narrative = self.generate_narrative(
            metric_name=metric_name,
            pattern=pattern,
            cagr=cagr,
            start_value=values[0],
            end_value=values[-1],
            category=category
        )

        # Build story arc
        story = StoryArc(
            metric_name=metric_name,
            pattern=pattern,
            cagr=cagr,
            narrative=narrative,
            confidence=confidence,
            r_squared=r_squared,
            start_value=values[0],
            end_value=values[-1],
            years=len(values),
            context=category
        )

        return story

    def generate_stories_batch(
        self,
        metrics_data: Dict[str, List[float]],
        categories: Optional[Dict[str, str]] = None
    ) -> Dict[str, StoryArc]:
        """
        Generate stories for multiple metrics in batch.

        Args:
            metrics_data: Dict mapping metric names to value lists
            categories: Optional dict mapping metric names to categories

        Returns:
            Dict mapping metric names to StoryArcs

        Example:
            >>> data = {
            ...     'ROE': [151.9, 164.6, 156.1, 197.0],
            ...     'NetMargin': [26.9, 24.0, 25.3, 25.3]
            ... }
            >>> cats = {'ROE': 'profitability', 'NetMargin': 'profitability'}
            >>> stories = generator.generate_stories_batch(data, cats)
        """
        stories = {}
        categories = categories or {}

        for metric_name, values in metrics_data.items():
            if len(values) < 2:
                continue  # Skip metrics with insufficient data

            category = categories.get(metric_name)
            story = self.generate_story(metric_name, values, category)
            stories[metric_name] = story

        return stories
