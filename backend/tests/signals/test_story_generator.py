"""
Tests for Story Arc Generator
Validates pattern detection, narrative generation, and confidence scoring.

Author: @franklin (CTO)
Sprint 5 - Micro-Tarea 4: Story Arc Generator Tests
"""
import pytest
import numpy as np
from backend.signals.story_generator import (
    StoryPattern,
    ConfidenceLevel,
    StoryArc,
    StoryGenerator,
    STORY_TEMPLATES
)


class TestStoryPatternDetection:
    """Test pattern detection logic (5 patterns)"""

    def test_acceleration_pattern(self):
        """Should detect ACCELERATION for strong positive CAGR"""
        generator = StoryGenerator()

        # Strong positive trend (CAGR > 5%)
        values = [10.0, 12.0, 15.0, 20.0]
        cagr = generator.calculate_cagr(values)
        r_squared = generator.calculate_r_squared(values)

        pattern = generator.detect_pattern(values, cagr, r_squared)

        assert pattern == StoryPattern.ACCELERATION
        assert cagr > 5.0
        assert r_squared > 0.4  # Strong linear fit

    def test_turnaround_pattern(self):
        """Should detect TURNAROUND for negative → positive transition"""
        generator = StoryGenerator()

        # Recovery story
        values = [-5.0, -2.0, 3.0, 8.0]
        cagr = generator.calculate_cagr(values)
        r_squared = generator.calculate_r_squared(values)

        pattern = generator.detect_pattern(values, cagr, r_squared)

        assert pattern == StoryPattern.TURNAROUND
        assert values[0] < 0
        assert values[-1] > 0

    def test_plateau_pattern(self):
        """Should detect PLATEAU for stable performance (±2% CAGR)"""
        generator = StoryGenerator()

        # Stable around 15
        values = [15.0, 14.5, 15.2, 15.8]
        cagr = generator.calculate_cagr(values)
        r_squared = generator.calculate_r_squared(values)

        pattern = generator.detect_pattern(values, cagr, r_squared)

        assert pattern == StoryPattern.PLATEAU
        assert -2.0 <= cagr <= 2.0

    def test_deterioration_pattern(self):
        """Should detect DETERIORATION for strong negative CAGR"""
        generator = StoryGenerator()

        # Strong negative trend (CAGR < -5%)
        values = [20.0, 17.0, 13.0, 10.0]
        cagr = generator.calculate_cagr(values)
        r_squared = generator.calculate_r_squared(values)

        pattern = generator.detect_pattern(values, cagr, r_squared)

        assert pattern == StoryPattern.DETERIORATION
        assert cagr < -5.0
        assert r_squared > 0.4  # Strong linear fit

    def test_volatile_pattern(self):
        """Should detect VOLATILE for high variance (R² < 0.4)"""
        generator = StoryGenerator()

        # High volatility, no clear trend
        values = [10.0, 20.0, 8.0, 18.0]
        cagr = generator.calculate_cagr(values)
        r_squared = generator.calculate_r_squared(values)

        pattern = generator.detect_pattern(values, cagr, r_squared)

        assert pattern == StoryPattern.VOLATILE
        assert r_squared < 0.4  # Poor linear fit


class TestCAGRCalculation:
    """Test CAGR calculation accuracy"""

    def test_cagr_positive_growth(self):
        """Should calculate positive CAGR correctly"""
        generator = StoryGenerator()

        # 10% annual growth
        values = [100.0, 110.0, 121.0, 133.1]
        cagr = generator.calculate_cagr(values)

        assert 9.9 < cagr < 10.1  # ~10% CAGR

    def test_cagr_negative_growth(self):
        """Should calculate negative CAGR correctly"""
        generator = StoryGenerator()

        # -10% annual decline
        values = [100.0, 90.0, 81.0, 72.9]
        cagr = generator.calculate_cagr(values)

        assert -10.1 < cagr < -9.9  # ~-10% CAGR

    def test_cagr_zero_start_value(self):
        """Should handle zero/negative start values gracefully"""
        generator = StoryGenerator()

        values = [0.0, 10.0, 20.0]
        cagr = generator.calculate_cagr(values)

        assert cagr == 0.0  # Fallback for invalid start

    def test_cagr_single_value(self):
        """Should return 0 for single value"""
        generator = StoryGenerator()

        values = [100.0]
        cagr = generator.calculate_cagr(values)

        assert cagr == 0.0


class TestConfidenceScoring:
    """Test confidence level calculation"""

    def test_high_confidence(self):
        """Should assign HIGH confidence for R² > 0.7"""
        generator = StoryGenerator()

        confidence = generator.get_confidence(0.85)

        assert confidence == ConfidenceLevel.HIGH

    def test_medium_confidence(self):
        """Should assign MEDIUM confidence for 0.4 < R² < 0.7"""
        generator = StoryGenerator()

        confidence = generator.get_confidence(0.55)

        assert confidence == ConfidenceLevel.MEDIUM

    def test_low_confidence(self):
        """Should assign LOW confidence for R² < 0.4"""
        generator = StoryGenerator()

        confidence = generator.get_confidence(0.25)

        assert confidence == ConfidenceLevel.LOW


class TestNarrativeGeneration:
    """Test narrative template generation"""

    def test_acceleration_narrative_profitability(self):
        """Should generate acceleration narrative for profitability metrics"""
        generator = StoryGenerator()

        narrative = generator.generate_narrative(
            metric_name='ROE',
            pattern=StoryPattern.ACCELERATION,
            cagr=9.1,
            start_value=151.9,
            end_value=197.0,
            category='profitability'
        )

        assert 'ROE' in narrative
        assert '151.9%' in narrative
        assert '197.0%' in narrative
        assert '+9.1%' in narrative
        assert 'accelerated' in narrative.lower()

    def test_turnaround_narrative_liquidity(self):
        """Should generate turnaround narrative for liquidity metrics"""
        generator = StoryGenerator()

        narrative = generator.generate_narrative(
            metric_name='CurrentRatio',
            pattern=StoryPattern.TURNAROUND,
            cagr=25.0,
            start_value=0.8,
            end_value=1.5,
            category='liquidity'
        )

        assert 'CurrentRatio' in narrative
        assert '0.80' in narrative
        assert '1.50' in narrative
        assert 'turnaround' in narrative.lower() or 'recovered' in narrative.lower()

    def test_deterioration_narrative_leverage(self):
        """Should generate deterioration narrative for leverage metrics"""
        generator = StoryGenerator()

        narrative = generator.generate_narrative(
            metric_name='DebtToEquity',
            pattern=StoryPattern.DETERIORATION,
            cagr=-15.0,
            start_value=0.5,
            end_value=1.8,
            category='leverage'
        )

        assert 'DebtToEquity' in narrative
        assert '0.50' in narrative
        assert '1.80' in narrative
        assert '-15.0%' in narrative
        assert 'worsened' in narrative.lower() or 'deteriorat' in narrative.lower()

    def test_narrative_without_category(self):
        """Should use default template when category not provided"""
        generator = StoryGenerator()

        narrative = generator.generate_narrative(
            metric_name='CustomMetric',
            pattern=StoryPattern.ACCELERATION,
            cagr=10.0,
            start_value=100.0,
            end_value=150.0,
            category=None
        )

        assert 'CustomMetric' in narrative
        assert '100.0' in narrative
        assert '150.0' in narrative
        assert len(narrative) > 50  # Non-empty narrative


class TestStoryGeneratorIntegration:
    """Test end-to-end story generation"""

    def test_generate_story_apple_roe(self):
        """Should generate complete story for Apple ROE 2022-2025"""
        generator = StoryGenerator()

        # Apple ROE: Strong acceleration
        values = [151.9, 164.6, 156.1, 197.0]

        story = generator.generate_story(
            metric_name='ROE',
            values=values,
            category='profitability'
        )

        # Validate StoryArc structure
        assert story.metric_name == 'ROE'
        assert story.pattern == StoryPattern.ACCELERATION
        assert story.years == 4
        assert story.start_value == 151.9
        assert story.end_value == 197.0
        assert story.cagr > 0  # Positive growth
        assert story.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]
        assert len(story.narrative) > 100  # Meaningful narrative
        assert 'ROE' in story.narrative

    def test_generate_story_insufficient_data(self):
        """Should raise ValueError for insufficient data (<2 years)"""
        generator = StoryGenerator()

        with pytest.raises(ValueError, match="Need at least 2 years"):
            generator.generate_story('ROE', [100.0])

    def test_generate_stories_batch(self):
        """Should generate multiple stories in batch"""
        generator = StoryGenerator()

        metrics_data = {
            'ROE': [151.9, 164.6, 156.1, 197.0],
            'NetMargin': [26.9, 24.0, 25.3, 25.3],
            'CurrentRatio': [0.88, 0.93, 0.98, 0.87]
        }

        categories = {
            'ROE': 'profitability',
            'NetMargin': 'profitability',
            'CurrentRatio': 'liquidity'
        }

        stories = generator.generate_stories_batch(metrics_data, categories)

        # Should generate 3 stories
        assert len(stories) == 3
        assert 'ROE' in stories
        assert 'NetMargin' in stories
        assert 'CurrentRatio' in stories

        # Each story should be valid
        for metric, story in stories.items():
            assert isinstance(story, StoryArc)
            assert story.metric_name == metric
            assert len(story.narrative) > 50

    def test_story_arc_dataclass(self):
        """Should validate StoryArc dataclass structure"""
        story = StoryArc(
            metric_name='ROE',
            pattern=StoryPattern.ACCELERATION,
            cagr=9.1,
            narrative='Test narrative',
            confidence=ConfidenceLevel.HIGH,
            r_squared=0.85,
            start_value=151.9,
            end_value=197.0,
            years=4,
            context='profitability'
        )

        assert story.metric_name == 'ROE'
        assert story.pattern == StoryPattern.ACCELERATION
        assert story.cagr == 9.1
        assert story.confidence == ConfidenceLevel.HIGH
        assert story.r_squared == 0.85
        assert story.context == 'profitability'


class TestRSquaredCalculation:
    """Test R² calculation accuracy"""

    def test_r_squared_perfect_linear(self):
        """Should return R² ≈ 1.0 for perfect linear trend"""
        generator = StoryGenerator()

        # Perfect linear: y = x
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        r_squared = generator.calculate_r_squared(values)

        assert r_squared > 0.99  # Near perfect fit

    def test_r_squared_volatile(self):
        """Should return low R² for volatile data"""
        generator = StoryGenerator()

        # High volatility
        values = [10.0, 5.0, 15.0, 3.0, 20.0]
        r_squared = generator.calculate_r_squared(values)

        assert r_squared < 0.5  # Poor linear fit

    def test_r_squared_single_value(self):
        """Should handle single value gracefully"""
        generator = StoryGenerator()

        values = [100.0]
        r_squared = generator.calculate_r_squared(values)

        assert r_squared == 0.0


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_all_zero_values(self):
        """Should handle all-zero values"""
        generator = StoryGenerator()

        values = [0.0, 0.0, 0.0, 0.0]
        cagr = generator.calculate_cagr(values)

        assert cagr == 0.0

    def test_negative_values(self):
        """Should handle negative values (loss-making companies)"""
        generator = StoryGenerator()

        values = [-10.0, -8.0, -5.0, -3.0]

        # Should not crash
        story = generator.generate_story('NetMargin', values, 'profitability')

        assert story.metric_name == 'NetMargin'
        assert story.start_value == -10.0
        assert story.end_value == -3.0

    def test_very_short_time_series(self):
        """Should handle minimum viable time series (2 values)"""
        generator = StoryGenerator()

        values = [100.0, 110.0]

        story = generator.generate_story('ROE', values)

        assert story.years == 2
        assert story.cagr > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
