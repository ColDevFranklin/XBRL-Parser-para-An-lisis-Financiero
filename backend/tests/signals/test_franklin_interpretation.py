"""
Tests for FranklinInterpretation - Franklin Framework Layer 3

Tests dynamic performance zone interpretation.
"""

import pytest
from backend.signals.statistical_engine import IndustryBenchmark
from backend.signals.franklin_interpretation import (
    PerformanceZone,
    FranklinInterpretation,
)


@pytest.fixture
def mock_roe_benchmark():
    """Mock ROE benchmark for Tech sector"""
    return IndustryBenchmark(
        metric_name='ROE',
        p10=15.0,
        p25=25.0,
        p50=35.0,
        p75=50.0,
        p90=100.0,
        mean=45.0,
        std=28.0,
        sample_size=20
    )


@pytest.fixture
def mock_debt_benchmark():
    """Mock DebtToEquity benchmark (inverse metric)"""
    return IndustryBenchmark(
        metric_name='DebtToEquity',
        p10=0.05,
        p25=0.15,
        p50=0.35,
        p75=0.65,
        p90=1.20,
        mean=0.45,
        std=0.35,
        sample_size=20
    )


class TestPerformanceZone:
    """Test PerformanceZone dataclass"""

    def test_zone_initialization(self):
        """Test creating PerformanceZone"""
        zone = PerformanceZone(
            name="Elite Performance",
            icon="🏆",
            description="Top 10% of sector",
            relative_position="top",
            percentile_range="P90-P100"
        )

        assert zone.name == "Elite Performance"
        assert zone.icon == "🏆"
        assert zone.relative_position == "top"


class TestFranklinInterpretation:
    """Test FranklinInterpretation static methods"""

    def test_interpret_value_elite(self, mock_roe_benchmark):
        """Test Elite Performance zone (>= P90)"""
        zone = FranklinInterpretation.interpret_value(
            value=150.0,
            benchmark=mock_roe_benchmark,
            metric_name='ROE'
        )

        assert zone.name == "Elite Performance"
        assert zone.icon == "🏆"
        assert zone.relative_position == "top"
        assert "top 10%" in zone.description.lower()
        assert zone.percentile_range == "P90-P100"

    def test_interpret_value_strong(self, mock_roe_benchmark):
        """Test Strong Performance zone (P75-P90)"""
        zone = FranklinInterpretation.interpret_value(
            value=75.0,
            benchmark=mock_roe_benchmark,
            metric_name='ROE'
        )

        assert zone.name == "Strong Performance"
        assert zone.icon == "↗️"
        assert zone.relative_position == "above_avg"
        assert "top quartile" in zone.description.lower()
        assert zone.percentile_range == "P75-P89"

    def test_interpret_value_above_median(self, mock_roe_benchmark):
        """Test Above Median zone (P50-P75)"""
        zone = FranklinInterpretation.interpret_value(
            value=40.0,
            benchmark=mock_roe_benchmark,
            metric_name='ROE'
        )

        assert zone.name == "Above Median"
        assert zone.icon == "✅"
        assert zone.relative_position == "avg"
        assert "above sector median" in zone.description.lower()
        assert zone.percentile_range == "P50-P74"

    def test_interpret_value_below_median(self, mock_roe_benchmark):
        """Test Below Median zone (P25-P50)"""
        zone = FranklinInterpretation.interpret_value(
            value=30.0,
            benchmark=mock_roe_benchmark,
            metric_name='ROE'
        )

        assert zone.name == "Below Median"
        assert zone.icon == "↘️"
        assert zone.relative_position == "below_avg"
        assert "below sector median" in zone.description.lower()
        assert zone.percentile_range == "P25-P49"

    def test_interpret_value_underperformance(self, mock_roe_benchmark):
        """Test Underperformance zone (< P25)"""
        zone = FranklinInterpretation.interpret_value(
            value=10.0,
            benchmark=mock_roe_benchmark,
            metric_name='ROE'
        )

        assert zone.name == "Underperformance"
        assert zone.icon == "🔻"
        assert zone.relative_position == "bottom"
        assert "bottom quartile" in zone.description.lower()
        assert zone.percentile_range == "P0-P24"

    def test_interpret_percentile_elite(self, mock_roe_benchmark):
        """Test 95th percentile"""
        zone = FranklinInterpretation.interpret_percentile(
            percentile=95,
            benchmark=mock_roe_benchmark,
            metric_name='ROE'
        )

        assert zone.name == "Elite Performance"
        assert "95th percentile" in zone.description

    def test_get_signal_buy_normal(self, mock_roe_benchmark):
        """Test BUY signal for high ROE"""
        signal = FranklinInterpretation.get_signal_type(
            value=60.0,
            benchmark=mock_roe_benchmark,
            inverse=False
        )

        assert signal == 'BUY'

    def test_get_signal_watch_normal(self, mock_roe_benchmark):
        """Test WATCH signal for mid-range ROE"""
        signal = FranklinInterpretation.get_signal_type(
            value=40.0,
            benchmark=mock_roe_benchmark,
            inverse=False
        )

        assert signal == 'WATCH'

    def test_get_signal_red_flag_normal(self, mock_roe_benchmark):
        """Test RED_FLAG signal for low ROE"""
        signal = FranklinInterpretation.get_signal_type(
            value=20.0,
            benchmark=mock_roe_benchmark,
            inverse=False
        )

        assert signal == 'RED_FLAG'

    def test_get_signal_buy_inverse(self, mock_debt_benchmark):
        """Test BUY signal for low debt (inverse logic)"""
        signal = FranklinInterpretation.get_signal_type(
            value=0.10,
            benchmark=mock_debt_benchmark,
            inverse=True
        )

        assert signal == 'BUY'

    def test_get_signal_red_flag_inverse(self, mock_debt_benchmark):
        """Test RED_FLAG signal for high debt (inverse logic)"""
        signal = FranklinInterpretation.get_signal_type(
            value=0.80,
            benchmark=mock_debt_benchmark,
            inverse=True
        )

        assert signal == 'RED_FLAG'
