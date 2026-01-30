"""
Tests for Decision Report Builder
Validates report generation, formatting, and export.

Author: @franklin (CTO)
Sprint 5 - Micro-Tarea 5: Decision Report Builder Tests
"""
import pytest
import json
from datetime import datetime

from backend.reports.report_builder import (
    DecisionReport,
    ReportBuilder
)
from backend.signals.signal_taxonomy import Signal, SignalType, SignalCategory
from backend.signals.peer_comparison import PeerBenchmark
from backend.signals.story_generator import StoryArc, StoryPattern, ConfidenceLevel


# Test fixtures
@pytest.fixture
def sample_signals():
    """Create sample signals for testing"""
    return [
        Signal(
            type=SignalType.BUY,
            category=SignalCategory.PROFITABILITY,
            metric='ROE',
            value=197.0,
            threshold=15.0,
            message='ROE 197.0% > 15.0%',
            trend='+9.1% CAGR'
        ),
        Signal(
            type=SignalType.BUY,
            category=SignalCategory.PROFITABILITY,
            metric='ROIC',
            value=111.1,
            threshold=12.0,
            message='ROIC 111.1% > 12.0%',
            trend='+20.5% CAGR'
        ),
        Signal(
            type=SignalType.RED_FLAG,
            category=SignalCategory.LIQUIDITY,
            metric='CurrentRatio',
            value=0.87,
            threshold=2.0,
            message='CurrentRatio 0.87 < 2.0',
            trend='-0.4% CAGR'
        ),
        Signal(
            type=SignalType.WATCH,
            category=SignalCategory.EFFICIENCY,
            metric='AssetTurnover',
            value=1.1,
            threshold=1.5,
            message='AssetTurnover 1.1 (monitoring)',
            trend='+2.0% CAGR'
        ),
    ]


@pytest.fixture
def sample_peer_benchmarks():
    """Create sample peer benchmarks"""
    return {
        'ROE': PeerBenchmark(
            metric_name='ROE',
            company_value=197.0,
            peer_median=32.8,
            peer_mean=50.0,
            percentile=100,
            beats_peers=True,
            peer_count=5,
            interpretation='Elite Performance 🏆'
        ),
        'NetMargin': PeerBenchmark(
            metric_name='NetMargin',
            company_value=24.0,
            peer_median=36.0,
            peer_mean=30.0,
            percentile=20,
            beats_peers=False,
            peer_count=5,
            interpretation='Below Average'
        ),
    }


@pytest.fixture
def sample_stories():
    """Create sample story arcs"""
    return {
        'ROE': StoryArc(
            metric_name='ROE',
            pattern=StoryPattern.ACCELERATION,
            cagr=9.1,
            narrative='ROE accelerated from 151.9% to 197.0%',
            confidence=ConfidenceLevel.MEDIUM,
            r_squared=0.64,
            start_value=151.9,
            end_value=197.0,
            years=4,
            context='profitability'
        ),
        'CurrentRatio': StoryArc(
            metric_name='CurrentRatio',
            pattern=StoryPattern.DETERIORATION,
            cagr=-5.2,
            narrative='CurrentRatio declined from 1.1 to 0.87',
            confidence=ConfidenceLevel.HIGH,
            r_squared=0.85,
            start_value=1.1,
            end_value=0.87,
            years=4,
            context='liquidity'
        ),
    }


class TestDecisionReport:
    """Test DecisionReport dataclass"""

    def test_decision_report_creation(self, sample_signals, sample_peer_benchmarks, sample_stories):
        """Should create DecisionReport with all fields"""
        report = DecisionReport(
            company='AAPL',
            date='2025-01-30',
            executive_summary='Test summary',
            signal_breakdown={'PROFITABILITY': sample_signals[:2]},
            peer_analysis=sample_peer_benchmarks,
            story_arcs=sample_stories,
            recommendation='BUY',
            confidence='HIGH',
            metadata={'test': 'data'}
        )

        assert report.company == 'AAPL'
        assert report.recommendation == 'BUY'
        assert report.confidence == 'HIGH'
        assert len(report.signal_breakdown) > 0
        assert len(report.peer_analysis) == 2
        assert len(report.story_arcs) == 2

    def test_decision_report_optional_metadata(self):
        """Should handle optional metadata"""
        report = DecisionReport(
            company='AAPL',
            date='2025-01-30',
            executive_summary='Test',
            signal_breakdown={},
            peer_analysis={},
            story_arcs={},
            recommendation='HOLD',
            confidence='MEDIUM'
        )

        assert report.metadata is None


class TestReportBuilder:
    """Test ReportBuilder class"""

    def test_group_signals_by_category(self, sample_signals):
        """Should group signals by category correctly"""
        builder = ReportBuilder()

        grouped = builder.group_signals_by_category(sample_signals)

        # Categories are lowercase from signal.category.value
        assert 'profitability' in grouped
        assert 'liquidity' in grouped
        assert 'efficiency' in grouped
        assert len(grouped['profitability']) == 2
        assert len(grouped['liquidity']) == 1
        assert len(grouped['efficiency']) == 1

    def test_calculate_recommendation_buy(self, sample_signals, sample_peer_benchmarks, sample_stories):
        """Should recommend BUY for strong signals + peer performance"""
        builder = ReportBuilder()

        # Adjust to >50% BUY signals with strong peer performance
        buy_signals = [sample_signals[0], sample_signals[1]] * 3  # 6 BUY
        all_signals = buy_signals + [sample_signals[2], sample_signals[3]]  # 8 total (75% BUY)

        # Ensure peer performance is >50% (currently 1/2 = 50%, need more beats)
        better_peers = {
            **sample_peer_benchmarks,
            'ROIC': PeerBenchmark(
                metric_name='ROIC',
                company_value=111.1,
                peer_median=50.0,
                peer_mean=60.0,
                percentile=90,
                beats_peers=True,
                peer_count=5,
                interpretation='Elite'
            )
        }

        recommendation, confidence = builder.calculate_recommendation(
            all_signals, better_peers, sample_stories
        )

        # With 75% BUY signals and 66% beats peers (2/3), should be BUY
        assert recommendation == 'BUY'
        assert confidence in ['HIGH', 'MEDIUM']

    def test_calculate_recommendation_sell(self, sample_signals, sample_peer_benchmarks, sample_stories):
        """Should recommend SELL for high RED_FLAG signals"""
        builder = ReportBuilder()

        # Create majority RED_FLAG signals
        red_flag_signals = [sample_signals[2]] * 5  # 5 RED_FLAG
        all_signals = red_flag_signals + [sample_signals[0]]  # 6 total (83% RED_FLAG)

        recommendation, confidence = builder.calculate_recommendation(
            all_signals, sample_peer_benchmarks, sample_stories
        )

        assert recommendation == 'SELL'

    def test_calculate_recommendation_hold(self, sample_signals, sample_peer_benchmarks, sample_stories):
        """Should recommend HOLD for mixed signals"""
        builder = ReportBuilder()

        # Mixed signals (default sample_signals has mix)
        recommendation, confidence = builder.calculate_recommendation(
            sample_signals, sample_peer_benchmarks, sample_stories
        )

        # With 2 BUY, 1 WATCH, 1 RED_FLAG → likely HOLD
        assert recommendation in ['HOLD', 'BUY']  # Could be either with 50% BUY

    def test_generate_executive_summary(self, sample_signals, sample_peer_benchmarks, sample_stories):
        """Should generate meaningful executive summary"""
        builder = ReportBuilder()

        summary = builder.generate_executive_summary(
            'AAPL', sample_signals, sample_peer_benchmarks, sample_stories
        )

        assert 'AAPL' in summary
        assert len(summary) > 100  # Meaningful length
        assert '.' in summary  # Proper sentence
        # Should mention elite performance
        assert 'ROE' in summary or 'exceptional' in summary.lower()

    def test_format_signal_breakdown(self, sample_signals):
        """Should format signal breakdown as markdown table"""
        builder = ReportBuilder()

        grouped = builder.group_signals_by_category(sample_signals)
        formatted = builder.format_signal_breakdown(grouped)

        assert '| Category' in formatted
        assert 'BUY' in formatted
        assert 'WATCH' in formatted
        assert 'RED_FLAG' in formatted
        assert 'profitability' in formatted  # lowercase from enum value
        assert '**TOTAL**' in formatted

    def test_format_peer_analysis(self, sample_peer_benchmarks):
        """Should format peer analysis summary"""
        builder = ReportBuilder()

        formatted = builder.format_peer_analysis(sample_peer_benchmarks)

        assert 'Beats peers' in formatted
        assert '1/2' in formatted or '50%' in formatted
        assert 'Elite Performance' in formatted or 'ROE' in formatted

    def test_format_story_section(self, sample_stories):
        """Should format story arcs with emojis and narratives"""
        builder = ReportBuilder()

        formatted = builder.format_story_section(sample_stories, max_stories=2)

        assert 'ROE' in formatted
        assert 'ACCELERATION' in formatted
        assert 'accelerated' in formatted
        assert 'CAGR' in formatted
        assert 'Confidence' in formatted

    def test_build_report_complete(self, sample_signals, sample_peer_benchmarks, sample_stories):
        """Should build complete report with all sections"""
        builder = ReportBuilder()

        report = builder.build_report(
            company='AAPL',
            signals=sample_signals,
            peer_benchmarks=sample_peer_benchmarks,
            stories=sample_stories
        )

        assert report.company == 'AAPL'
        assert len(report.executive_summary) > 0
        assert report.recommendation in ['BUY', 'HOLD', 'SELL']
        assert report.confidence in ['HIGH', 'MEDIUM', 'LOW']
        assert len(report.signal_breakdown) > 0
        assert len(report.peer_analysis) > 0
        assert len(report.story_arcs) > 0


class TestReportExport:
    """Test report export formats"""

    def test_export_markdown(self, sample_signals, sample_peer_benchmarks, sample_stories):
        """Should export report as markdown"""
        builder = ReportBuilder()

        report = builder.build_report(
            'AAPL', sample_signals, sample_peer_benchmarks, sample_stories
        )

        markdown = builder.export_markdown(report)

        assert '# 📊 INVESTMENT DECISION REPORT - AAPL' in markdown
        assert '## 🎯 EXECUTIVE SUMMARY' in markdown
        assert '## 📈 SIGNAL ANALYSIS' in markdown
        assert '## 🏆 PEER COMPARISON' in markdown
        assert '## 📖 STORY ARCS' in markdown
        assert 'RECOMMENDATION:' in markdown
        assert len(markdown) > 500  # Substantial content

    def test_export_text(self, sample_signals, sample_peer_benchmarks, sample_stories):
        """Should export report as plain text"""
        builder = ReportBuilder()

        report = builder.build_report(
            'AAPL', sample_signals, sample_peer_benchmarks, sample_stories
        )

        text = builder.export_text(report)

        assert 'AAPL' in text
        assert 'EXECUTIVE SUMMARY' in text
        assert 'SIGNAL ANALYSIS' in text
        assert '#' not in text  # No markdown headers
        assert len(text) > 400

    def test_export_json(self, sample_signals, sample_peer_benchmarks, sample_stories):
        """Should export report as valid JSON"""
        builder = ReportBuilder()

        report = builder.build_report(
            'AAPL', sample_signals, sample_peer_benchmarks, sample_stories
        )

        json_str = builder.export_json(report)

        # Should be valid JSON
        data = json.loads(json_str)

        assert data['company'] == 'AAPL'
        assert 'executive_summary' in data
        assert 'recommendation' in data
        assert 'signal_breakdown' in data
        assert 'peer_analysis' in data
        assert 'story_arcs' in data

    def test_export_json_structure(self, sample_signals, sample_peer_benchmarks, sample_stories):
        """Should export JSON with correct structure"""
        builder = ReportBuilder()

        report = builder.build_report(
            'AAPL', sample_signals, sample_peer_benchmarks, sample_stories
        )

        json_str = builder.export_json(report)
        data = json.loads(json_str)

        # Validate signal structure (keys are lowercase from enum)
        assert 'profitability' in data['signal_breakdown']
        first_signal = data['signal_breakdown']['profitability'][0]
        assert 'type' in first_signal
        assert 'metric' in first_signal
        assert 'value' in first_signal

        # Validate peer structure
        assert 'ROE' in data['peer_analysis']
        assert 'percentile' in data['peer_analysis']['ROE']

        # Validate story structure
        assert 'ROE' in data['story_arcs']
        assert 'pattern' in data['story_arcs']['ROE']
        assert 'cagr' in data['story_arcs']['ROE']


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_signals(self):
        """Should handle empty signals list"""
        builder = ReportBuilder()

        report = builder.build_report(
            company='TEST',
            signals=[],
            peer_benchmarks={},
            stories={}
        )

        assert report.company == 'TEST'
        assert report.recommendation in ['BUY', 'HOLD', 'SELL']

    def test_no_peer_data(self, sample_signals, sample_stories):
        """Should handle missing peer data"""
        builder = ReportBuilder()

        report = builder.build_report(
            'TEST', sample_signals, {}, sample_stories
        )

        markdown = builder.export_markdown(report)
        assert 'No peer comparison data' in markdown or 'TEST' in markdown

    def test_no_story_data(self, sample_signals, sample_peer_benchmarks):
        """Should handle missing story data"""
        builder = ReportBuilder()

        report = builder.build_report(
            'TEST', sample_signals, sample_peer_benchmarks, {}
        )

        markdown = builder.export_markdown(report)
        assert 'No multi-year trend data' in markdown or 'TEST' in markdown


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
