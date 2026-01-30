"""
Decision Report Builder - Investment Report Generation
Integrates signals, peer comparison, and story arcs into formatted investment reports.

This module generates comprehensive investment analysis reports combining:
- Signal detection (BUY/WATCH/RED_FLAG)
- Peer comparison benchmarks
- Multi-year story arcs
- Executive summary
- Investment recommendation

Author: @franklin (CTO)
Sprint 5 - Micro-Tarea 5: Decision Report Builder
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime
import json

from backend.signals.signal_taxonomy import Signal, SignalType, SignalCategory
from backend.signals.peer_comparison import PeerBenchmark
from backend.signals.story_generator import StoryArc, StoryPattern


@dataclass
class DecisionReport:
    """
    Complete investment decision report.

    Attributes:
        company: Ticker symbol (e.g., 'AAPL')
        date: Report generation date (ISO format)
        executive_summary: 3-5 sentence overview
        signal_breakdown: Signals grouped by category
        peer_analysis: Peer benchmarks by metric
        story_arcs: Narrative arcs by metric
        recommendation: BUY/HOLD/SELL
        confidence: HIGH/MEDIUM/LOW
        metadata: Additional context (optional)
    """
    company: str
    date: str
    executive_summary: str
    signal_breakdown: Dict[str, List[Signal]]
    peer_analysis: Dict[str, PeerBenchmark]
    story_arcs: Dict[str, StoryArc]
    recommendation: str
    confidence: str
    metadata: Optional[Dict] = None


class ReportBuilder:
    """
    Builds comprehensive investment decision reports.

    Integrates multiple analysis layers into human-readable reports
    with clear recommendations.

    Example:
        >>> builder = ReportBuilder()
        >>> report = builder.build_report(
        ...     company='AAPL',
        ...     signals=signals_list,
        ...     peer_benchmarks=peer_dict,
        ...     stories=story_dict
        ... )
        >>> markdown = builder.export_markdown(report)
    """

    def __init__(self):
        """Initialize Report Builder."""
        pass

    def generate_executive_summary(
        self,
        company: str,
        signals: List[Signal],
        peer_benchmarks: Dict[str, PeerBenchmark],
        stories: Dict[str, StoryArc]
    ) -> str:
        """
        Generate 3-5 sentence executive summary.

        Summary includes:
        - Top 2-3 strengths (BUY signals or elite performance)
        - Top 1-2 concerns (RED_FLAG or underperformance)
        - Overall trajectory (from strongest story arc)

        Args:
            company: Company ticker
            signals: List of all signals
            peer_benchmarks: Peer comparison results
            stories: Story arcs

        Returns:
            Executive summary text
        """
        # Count signals by type
        buy_count = sum(1 for s in signals if s.type == SignalType.BUY)
        watch_count = sum(1 for s in signals if s.type == SignalType.WATCH)
        red_flag_count = sum(1 for s in signals if s.type == SignalType.RED_FLAG)
        total = len(signals)

        # Find elite performance metrics (top percentile)
        elite_metrics = [
            name for name, bench in peer_benchmarks.items()
            if bench.percentile >= 90
        ]

        # Find strongest story (highest absolute CAGR)
        strongest_story = None
        if stories:
            strongest_story = max(stories.values(), key=lambda s: abs(s.cagr))

        # Find concerns (RED_FLAG signals)
        concerns = [s for s in signals if s.type == SignalType.RED_FLAG]

        # Build summary
        summary_parts = []

        # Strengths
        if elite_metrics:
            top_metrics = ', '.join(elite_metrics[:2])
            summary_parts.append(
                f"{company} demonstrates exceptional performance in {top_metrics} "
                f"(top decile vs peers)"
            )
        elif buy_count > 0:
            summary_parts.append(
                f"{company} shows {buy_count} strong buy signals out of {total} metrics analyzed"
            )

        # Trajectory
        if strongest_story and abs(strongest_story.cagr) > 5:
            direction = "improving" if strongest_story.cagr > 0 else "declining"
            summary_parts.append(
                f"{strongest_story.metric_name} {direction} at {abs(strongest_story.cagr):.1f}% CAGR, "
                f"indicating {strongest_story.pattern.value.lower()} momentum"
            )

        # Concerns
        if concerns:
            concern_metrics = ', '.join([c.metric for c in concerns[:2]])
            summary_parts.append(
                f"Watch areas include {concern_metrics}"
            )
        elif watch_count > total * 0.3:
            summary_parts.append(
                f"{watch_count} metrics require monitoring for potential deterioration"
            )

        # Peer performance
        beats_peers = sum(1 for b in peer_benchmarks.values() if b.beats_peers)
        peer_pct = (beats_peers / len(peer_benchmarks) * 100) if peer_benchmarks else 0
        summary_parts.append(
            f"Company beats peers in {beats_peers}/{len(peer_benchmarks)} metrics ({peer_pct:.0f}%)"
        )

        return '. '.join(summary_parts) + '.'

    def calculate_recommendation(
        self,
        signals: List[Signal],
        peer_benchmarks: Dict[str, PeerBenchmark],
        stories: Dict[str, StoryArc]
    ) -> tuple[str, str]:
        """
        Calculate investment recommendation and confidence.

        Logic:
        - BUY: >50% BUY signals AND (>50% beats peers OR strong acceleration)
        - SELL: >40% RED_FLAG OR (deterioration pattern AND <30% beats peers)
        - HOLD: Everything else

        Confidence:
        - HIGH: Clear majority (>70% agreement across signals/peers/stories)
        - MEDIUM: Moderate agreement (50-70%)
        - LOW: Mixed signals (<50%)

        Args:
            signals: List of all signals
            peer_benchmarks: Peer comparison results
            stories: Story arcs

        Returns:
            Tuple of (recommendation, confidence)
        """
        # Signal distribution
        buy_count = sum(1 for s in signals if s.type == SignalType.BUY)
        red_flag_count = sum(1 for s in signals if s.type == SignalType.RED_FLAG)
        total = len(signals)

        buy_pct = buy_count / total if total > 0 else 0
        red_flag_pct = red_flag_count / total if total > 0 else 0

        # Peer performance
        beats_peers = sum(1 for b in peer_benchmarks.values() if b.beats_peers)
        peer_pct = beats_peers / len(peer_benchmarks) if peer_benchmarks else 0

        # Story momentum (count acceleration vs deterioration)
        acceleration_count = sum(
            1 for s in stories.values()
            if s.pattern == StoryPattern.ACCELERATION
        )
        deterioration_count = sum(
            1 for s in stories.values()
            if s.pattern == StoryPattern.DETERIORATION
        )
        story_count = len(stories)

        # Recommendation logic
        recommendation = "HOLD"

        # BUY conditions
        if buy_pct > 0.5 and (peer_pct > 0.5 or acceleration_count > deterioration_count):
            recommendation = "BUY"
        # SELL conditions
        elif red_flag_pct > 0.4 or (deterioration_count > acceleration_count and peer_pct < 0.3):
            recommendation = "SELL"

        # Confidence calculation
        # High: Strong agreement (>70% signals align + peer/story support)
        # Medium: Moderate agreement (50-70%)
        # Low: Mixed signals (<50%)

        dominant_pct = max(buy_pct, red_flag_pct, 1 - buy_pct - red_flag_pct)

        if dominant_pct > 0.7 and abs(peer_pct - 0.5) > 0.2:
            confidence = "HIGH"
        elif dominant_pct > 0.5:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return recommendation, confidence

    def group_signals_by_category(
        self,
        signals: List[Signal]
    ) -> Dict[str, List[Signal]]:
        """
        Group signals by category for breakdown table.

        Args:
            signals: List of all signals

        Returns:
            Dict mapping category names to signal lists
        """
        grouped = {}

        for signal in signals:
            category = signal.category.value
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(signal)

        return grouped

    def format_signal_breakdown(
        self,
        signal_breakdown: Dict[str, List[Signal]]
    ) -> str:
        """
        Format signal breakdown as markdown table.

        Args:
            signal_breakdown: Signals grouped by category

        Returns:
            Markdown table string
        """
        lines = []
        lines.append("| Category       | BUY | WATCH | RED_FLAG |")
        lines.append("|----------------|-----|-------|----------|")

        total_buy = 0
        total_watch = 0
        total_red_flag = 0

        for category in sorted(signal_breakdown.keys()):
            signals = signal_breakdown[category]
            buy = sum(1 for s in signals if s.type == SignalType.BUY)
            watch = sum(1 for s in signals if s.type == SignalType.WATCH)
            red_flag = sum(1 for s in signals if s.type == SignalType.RED_FLAG)

            total_buy += buy
            total_watch += watch
            total_red_flag += red_flag

            lines.append(f"| {category:14} | {buy:3} | {watch:5} | {red_flag:8} |")

        # Total row
        total = total_buy + total_watch + total_red_flag
        lines.append(f"| **TOTAL**      | **{total_buy}/{total}** | **{total_watch}/{total}** | **{total_red_flag}/{total}** |")

        return '\n'.join(lines)

    def format_peer_analysis(
        self,
        peer_benchmarks: Dict[str, PeerBenchmark]
    ) -> str:
        """
        Format peer comparison analysis.

        Args:
            peer_benchmarks: Peer comparison results

        Returns:
            Formatted text summary
        """
        if not peer_benchmarks:
            return "No peer comparison data available."

        beats_peers = sum(1 for b in peer_benchmarks.values() if b.beats_peers)
        total = len(peer_benchmarks)
        pct = beats_peers / total * 100 if total > 0 else 0

        # Find elite performance (>90th percentile)
        elite = [
            name for name, bench in peer_benchmarks.items()
            if bench.percentile >= 90
        ]

        # Find above average (50-90th percentile)
        above_avg = [
            name for name, bench in peer_benchmarks.items()
            if 50 <= bench.percentile < 90
        ]

        # Find below average (<50th percentile)
        below_avg = [
            name for name, bench in peer_benchmarks.items()
            if bench.percentile < 50
        ]

        lines = []
        lines.append(f"Beats peers in {beats_peers}/{total} metrics ({pct:.0f}%)")

        if elite:
            lines.append(f"- Elite Performance (>90th percentile): {', '.join(elite)}")

        if above_avg:
            lines.append(f"- Above Average (50-90th percentile): {len(above_avg)} metrics")

        if below_avg:
            lines.append(f"- Below Average (<50th percentile): {len(below_avg)} metrics")

        return '\n'.join(lines)

    def format_story_section(
        self,
        stories: Dict[str, StoryArc],
        max_stories: int = 3
    ) -> str:
        """
        Format top story arcs for report.

        Args:
            stories: All story arcs
            max_stories: Maximum stories to include

        Returns:
            Formatted story section
        """
        if not stories:
            return "No multi-year trend data available."

        # Sort by absolute CAGR (strongest trends first)
        sorted_stories = sorted(
            stories.values(),
            key=lambda s: abs(s.cagr),
            reverse=True
        )

        lines = []

        for i, story in enumerate(sorted_stories[:max_stories], 1):
            emoji = {
                StoryPattern.ACCELERATION: "📈",
                StoryPattern.TURNAROUND: "🔄",
                StoryPattern.PLATEAU: "➡️",
                StoryPattern.DETERIORATION: "📉",
                StoryPattern.VOLATILE: "〰️"
            }.get(story.pattern, "📊")

            lines.append(f"\n**{emoji} {story.metric_name} - {story.pattern.value}**")
            lines.append(f"{story.narrative}")
            lines.append(f"*(CAGR: {story.cagr:+.1f}%, Confidence: {story.confidence.value})*")

        return '\n'.join(lines)

    def build_report(
        self,
        company: str,
        signals: List[Signal],
        peer_benchmarks: Dict[str, PeerBenchmark],
        stories: Dict[str, StoryArc],
        metadata: Optional[Dict] = None
    ) -> DecisionReport:
        """
        Build complete decision report.

        Args:
            company: Company ticker
            signals: All detected signals
            peer_benchmarks: Peer comparison results
            stories: Story arcs
            metadata: Optional additional context

        Returns:
            Complete DecisionReport object
        """
        # Generate executive summary
        executive_summary = self.generate_executive_summary(
            company, signals, peer_benchmarks, stories
        )

        # Calculate recommendation
        recommendation, confidence = self.calculate_recommendation(
            signals, peer_benchmarks, stories
        )

        # Group signals by category
        signal_breakdown = self.group_signals_by_category(signals)

        # Build report
        report = DecisionReport(
            company=company,
            date=datetime.now().isoformat(),
            executive_summary=executive_summary,
            signal_breakdown=signal_breakdown,
            peer_analysis=peer_benchmarks,
            story_arcs=stories,
            recommendation=recommendation,
            confidence=confidence,
            metadata=metadata or {}
        )

        return report

    def export_markdown(self, report: DecisionReport) -> str:
        """
        Export report as markdown format.

        Args:
            report: DecisionReport object

        Returns:
            Markdown formatted report
        """
        md = []

        # Header
        md.append(f"# 📊 INVESTMENT DECISION REPORT - {report.company}")
        md.append(f"*Generated: {report.date[:10]}*\n")

        # Executive Summary
        md.append("## 🎯 EXECUTIVE SUMMARY\n")
        md.append(report.executive_summary)
        md.append(f"\n**RECOMMENDATION: {report.recommendation}** (Confidence: {report.confidence})\n")

        # Signal Analysis
        md.append("## 📈 SIGNAL ANALYSIS\n")
        md.append(self.format_signal_breakdown(report.signal_breakdown))
        md.append("")

        # Peer Comparison
        md.append("## 🏆 PEER COMPARISON\n")
        md.append(self.format_peer_analysis(report.peer_analysis))
        md.append("")

        # Story Arcs
        md.append("## 📖 STORY ARCS")
        md.append(self.format_story_section(report.story_arcs))
        md.append("")

        # Footer
        md.append("---")
        md.append("*Report generated by XBRL Financial Analyzer*")
        md.append("*Methodology: Graham/Buffett/Munger + Franklin Framework*")

        return '\n'.join(md)

    def export_text(self, report: DecisionReport) -> str:
        """
        Export report as plain text format.

        Args:
            report: DecisionReport object

        Returns:
            Plain text formatted report
        """
        # Convert markdown to plain text (remove formatting)
        markdown = self.export_markdown(report)

        # Simple conversions
        text = markdown.replace('#', '')
        text = text.replace('*', '')
        text = text.replace('|', ' ')
        text = text.replace('-' * 10, '-' * 50)

        return text

    def export_json(self, report: DecisionReport) -> str:
        """
        Export report as JSON format.

        Args:
            report: DecisionReport object

        Returns:
            JSON formatted report
        """
        # Convert dataclass to dict
        report_dict = {
            'company': report.company,
            'date': report.date,
            'executive_summary': report.executive_summary,
            'recommendation': report.recommendation,
            'confidence': report.confidence,
            'signal_breakdown': {
                category: [
                    {
                        'type': s.type.value,
                        'category': s.category.value,
                        'metric': s.metric,
                        'value': s.value,
                        'threshold': s.threshold,
                        'message': s.message
                    }
                    for s in signals
                ]
                for category, signals in report.signal_breakdown.items()
            },
            'peer_analysis': {
                metric: {
                    'company_value': b.company_value,
                    'peer_median': b.peer_median,
                    'percentile': b.percentile,
                    'beats_peers': b.beats_peers,
                    'interpretation': b.interpretation
                }
                for metric, b in report.peer_analysis.items()
            },
            'story_arcs': {
                metric: {
                    'pattern': s.pattern.value,
                    'cagr': s.cagr,
                    'narrative': s.narrative,
                    'confidence': s.confidence.value
                }
                for metric, s in report.story_arcs.items()
            },
            'metadata': report.metadata
        }

        return json.dumps(report_dict, indent=2)
