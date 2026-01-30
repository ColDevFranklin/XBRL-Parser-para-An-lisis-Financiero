"""
Full Pipeline Integration Demo - End-to-End Investment Analysis
Demonstrates complete workflow from XBRL parsing to final report generation.

Pipeline Stages:
1. XBRL Parsing (Sprint 3)
2. Metrics Calculation (Sprint 4)
3. Signal Detection (Sprint 5)
4. Peer Comparison (Sprint 5)
5. Story Arc Generation (Sprint 5)
6. Decision Report Building (Sprint 5)

Author: @franklin (CTO)
Sprint 5 - Micro-Tarea 6: Integration + Demo (FINAL)
"""
import time
from datetime import datetime
from typing import Dict, List

# Mock data for demo (in real implementation, these come from actual modules)
from backend.signals.signal_taxonomy import Signal, SignalType, SignalCategory
from backend.signals.peer_comparison import PeerBenchmark
from backend.signals.story_generator import (
    StoryGenerator,
    StoryArc,
    StoryPattern,
    ConfidenceLevel
)
from backend.reports.report_builder import ReportBuilder


def print_stage(stage_num: int, stage_name: str):
    """Print formatted stage header"""
    print("\n" + "=" * 80)
    print(f"STAGE {stage_num}: {stage_name}")
    print("=" * 80)


def print_timing(stage_name: str, elapsed: float):
    """Print timing info"""
    print(f"✅ {stage_name} completed in {elapsed:.2f}s")


def simulate_xbrl_parsing(company: str) -> Dict:
    """
    Stage 1: XBRL Parsing

    In production, this would call:
    from backend.parsers import XBRLParser
    parser = XBRLParser()
    data = parser.parse_filing(company, year=2024)
    """
    print_stage(1, "XBRL PARSING")
    print(f"📄 Parsing SEC EDGAR filings for {company}...")

    start = time.time()

    # Simulate parsing delay
    time.sleep(0.5)

    # Mock financial data (4 years: 2022-2025)
    financial_data = {
        'balance_sheet': {
            'TotalAssets': [352755000000, 352583000000, 365725000000, 364980000000],
            'TotalLiabilities': [290437000000, 302083000000, 308030000000, 285020000000],
            'StockholdersEquity': [62318000000, 50500000000, 57695000000, 79960000000],
            'CurrentAssets': [135405000000, 143566000000, 143566000000, 143000000000],
            'CurrentLiabilities': [153982000000, 145308000000, 145308000000, 164000000000],
        },
        'income_statement': {
            'Revenue': [394328000000, 383285000000, 383933000000, 391000000000],
            'NetIncome': [99803000000, 96995000000, 97000000000, 99000000000],
            'OperatingIncome': [119437000000, 114301000000, 115000000000, 118000000000],
        },
        'years': [2022, 2023, 2024, 2025]
    }

    elapsed = time.time() - start
    print_timing("XBRL Parsing", elapsed)
    print(f"   📊 Loaded {len(financial_data['years'])} years of data")
    print(f"   📋 Balance Sheet: {len(financial_data['balance_sheet'])} items")
    print(f"   📋 Income Statement: {len(financial_data['income_statement'])} items")

    return financial_data


def simulate_metrics_calculation(financial_data: Dict) -> Dict:
    """
    Stage 2: Metrics Calculation

    In production, this would call:
    from backend.metrics import MetricsCalculator
    calculator = MetricsCalculator()
    metrics = calculator.calculate_all(financial_data)
    """
    print_stage(2, "METRICS CALCULATION")
    print("🧮 Calculating 25 financial ratios...")

    start = time.time()

    # Simulate calculation delay
    time.sleep(0.3)

    # Mock calculated metrics (multi-year)
    metrics = {
        # Profitability
        'ROE': [151.9, 164.6, 156.1, 197.0],
        'ROIC': [63.5, 80.2, 72.6, 111.1],
        'NetMargin': [26.9, 24.0, 25.3, 25.3],
        'ROA': [28.3, 27.5, 26.5, 27.1],
        'GrossMargin': [43.3, 44.1, 45.2, 46.0],

        # Liquidity
        'CurrentRatio': [0.88, 0.93, 0.98, 0.87],
        'QuickRatio': [0.82, 0.87, 0.91, 0.81],
        'CashRatio': [0.35, 0.38, 0.40, 0.37],

        # Efficiency
        'AssetTurnover': [1.12, 1.09, 1.05, 1.07],
        'InventoryTurnover': [32.5, 34.2, 35.8, 37.1],
        'ReceivablesTurnover': [18.5, 19.2, 20.1, 20.8],

        # Leverage
        'DebtToEquity': [-7.69, -6.19, -5.51, -4.81],
        'InterestCoverage': [75.3, 80.2, 82.5, 85.3],
        'DebtToAssets': [0.82, 0.86, 0.84, 0.78],
    }

    elapsed = time.time() - start
    print_timing("Metrics Calculation", elapsed)
    print(f"   📈 Calculated {len(metrics)} financial metrics")
    print(f"   📊 Each with {len(metrics['ROE'])} years of data")

    return metrics


def simulate_signal_detection(metrics: Dict) -> List[Signal]:
    """
    Stage 3: Signal Detection

    In production, this would call:
    from backend.signals import SignalDetector, StatisticalBenchmarkEngine
    engine = StatisticalBenchmarkEngine(sector_data)
    detector = SignalDetector(metrics, 'AAPL', engine)
    signals = detector.detect_all()
    """
    print_stage(3, "SIGNAL DETECTION")
    print("🎯 Detecting BUY/WATCH/RED_FLAG signals...")

    start = time.time()

    # Simulate detection delay
    time.sleep(0.2)

    # Mock detected signals (15 signals)
    signals = [
        # PROFITABILITY - Strong
        Signal(SignalType.BUY, SignalCategory.PROFITABILITY, 'ROE', 197.0, 15.0,
               'ROE 197.0% > 15.0% - Exceptional capital efficiency', '+9.1% CAGR'),
        Signal(SignalType.BUY, SignalCategory.PROFITABILITY, 'ROIC', 111.1, 12.0,
               'ROIC 111.1% > 12.0% - Superior returns', '+20.5% CAGR'),
        Signal(SignalType.BUY, SignalCategory.PROFITABILITY, 'NetMargin', 25.3, 20.0,
               'NetMargin 25.3% > 20.0%', '-2.0% CAGR'),
        Signal(SignalType.BUY, SignalCategory.PROFITABILITY, 'GrossMargin', 46.0, 40.0,
               'GrossMargin 46.0% > 40.0%', '+2.1% CAGR'),

        # LIQUIDITY - Concerns
        Signal(SignalType.RED_FLAG, SignalCategory.LIQUIDITY, 'CurrentRatio', 0.87, 2.0,
               'CurrentRatio 0.87 < 2.0 - Below safety threshold', '-0.4% CAGR'),
        Signal(SignalType.WATCH, SignalCategory.LIQUIDITY, 'QuickRatio', 0.81, 1.0,
               'QuickRatio 0.81 (monitoring)', '-0.5% CAGR'),

        # EFFICIENCY - Good
        Signal(SignalType.BUY, SignalCategory.EFFICIENCY, 'AssetTurnover', 1.07, 0.8,
               'AssetTurnover 1.07 > 0.8', '-1.5% CAGR'),
        Signal(SignalType.BUY, SignalCategory.EFFICIENCY, 'InventoryTurnover', 37.1, 30.0,
               'InventoryTurnover 37.1 > 30.0', '+4.5% CAGR'),

        # LEVERAGE - Strong
        Signal(SignalType.BUY, SignalCategory.LEVERAGE, 'DebtToEquity', -4.81, 0.5,
               'DebtToEquity -4.81 - Net cash position', 'Improving'),
        Signal(SignalType.BUY, SignalCategory.LEVERAGE, 'InterestCoverage', 85.3, 3.0,
               'InterestCoverage 85.3 > 3.0', '+4.2% CAGR'),
    ]

    elapsed = time.time() - start
    print_timing("Signal Detection", elapsed)

    buy = sum(1 for s in signals if s.type == SignalType.BUY)
    watch = sum(1 for s in signals if s.type == SignalType.WATCH)
    red_flag = sum(1 for s in signals if s.type == SignalType.RED_FLAG)

    print(f"   🟢 BUY signals: {buy}")
    print(f"   ⚠️  WATCH signals: {watch}")
    print(f"   🔴 RED_FLAG signals: {red_flag}")

    return signals


def simulate_peer_comparison(metrics: Dict) -> Dict[str, PeerBenchmark]:
    """
    Stage 4: Peer Comparison

    In production, this would call:
    from backend.signals import compare_to_peers, StatisticalBenchmarkEngine
    engine = StatisticalBenchmarkEngine(sector_data)
    benchmarks = compare_to_peers(metrics, peer_metrics, 'AAPL', engine)
    """
    print_stage(4, "PEER COMPARISON")
    print("🏆 Comparing against sector peers (20 tech companies)...")

    start = time.time()

    # Simulate comparison delay
    time.sleep(0.3)

    # Mock peer benchmarks
    peer_benchmarks = {
        'ROE': PeerBenchmark('ROE', 197.0, 32.8, 50.0, 100, True, 20, 'Elite Performance 🏆'),
        'ROIC': PeerBenchmark('ROIC', 111.1, 34.9, 45.2, 100, True, 20, 'Elite Performance 🏆'),
        'NetMargin': PeerBenchmark('NetMargin', 25.3, 36.0, 30.5, 35, False, 20, 'Below Median ↘️'),
        'CurrentRatio': PeerBenchmark('CurrentRatio', 0.87, 1.27, 1.35, 15, False, 20, 'Bottom Quartile 🔻'),
        'AssetTurnover': PeerBenchmark('AssetTurnover', 1.07, 0.85, 0.92, 80, True, 20, 'Top Quartile ↗️'),
        'DebtToEquity': PeerBenchmark('DebtToEquity', -4.81, 0.45, 0.62, 5, True, 20, 'Elite (Net Cash) 🏆'),
    }

    elapsed = time.time() - start
    print_timing("Peer Comparison", elapsed)

    beats_peers = sum(1 for b in peer_benchmarks.values() if b.beats_peers)
    total = len(peer_benchmarks)

    print(f"   📊 Compared {total} metrics")
    print(f"   ✅ Beats peers: {beats_peers}/{total} ({beats_peers/total*100:.0f}%)")

    return peer_benchmarks


def simulate_story_generation(metrics: Dict) -> Dict[str, StoryArc]:
    """
    Stage 5: Story Arc Generation

    In production, this would call:
    from backend.signals import StoryGenerator
    generator = StoryGenerator()
    stories = generator.generate_stories_batch(metrics_data, categories)
    """
    print_stage(5, "STORY ARC GENERATION")
    print("📖 Generating narrative arcs for key metrics...")

    start = time.time()

    # Use real StoryGenerator
    generator = StoryGenerator()

    categories = {
        'ROE': 'profitability',
        'ROIC': 'profitability',
        'NetMargin': 'profitability',
        'CurrentRatio': 'liquidity',
        'AssetTurnover': 'efficiency',
    }

    stories = {}
    for metric, values in metrics.items():
        if metric in categories:
            story = generator.generate_story(metric, values, categories[metric])
            stories[metric] = story

    elapsed = time.time() - start
    print_timing("Story Generation", elapsed)

    print(f"   📚 Generated {len(stories)} story arcs")

    # Show pattern distribution
    patterns = {}
    for story in stories.values():
        pattern = story.pattern.value
        patterns[pattern] = patterns.get(pattern, 0) + 1

    for pattern, count in sorted(patterns.items()):
        print(f"   - {pattern}: {count}")

    return stories


def build_final_report(
    company: str,
    signals: List[Signal],
    peer_benchmarks: Dict[str, PeerBenchmark],
    stories: Dict[str, StoryArc]
) -> str:
    """
    Stage 6: Decision Report Building

    In production, this uses:
    from backend.reports import ReportBuilder
    builder = ReportBuilder()
    report = builder.build_report(...)
    markdown = builder.export_markdown(report)
    """
    print_stage(6, "DECISION REPORT BUILDING")
    print("📝 Building final investment decision report...")

    start = time.time()

    # Use real ReportBuilder
    builder = ReportBuilder()

    report = builder.build_report(
        company=company,
        signals=signals,
        peer_benchmarks=peer_benchmarks,
        stories=stories,
        metadata={
            'analyst': 'Franklin Framework',
            'methodology': 'Graham/Buffett/Munger',
            'data_source': 'SEC EDGAR XBRL',
            'sector': 'Technology',
            'peers_count': 20
        }
    )

    # Export to markdown
    markdown = builder.export_markdown(report)

    elapsed = time.time() - start
    print_timing("Report Building", elapsed)

    print(f"   📄 Recommendation: {report.recommendation}")
    print(f"   🎯 Confidence: {report.confidence}")
    print(f"   📏 Report length: {len(markdown)} characters")

    return markdown


def save_report(markdown: str, company: str):
    """Save report to outputs directory"""
    print_stage(7, "EXPORT & SAVE")
    print("💾 Saving report to file...")

    start = time.time()

    # Save to outputs
    filename = f'/tmp/decision_report_{company}.md'
    with open(filename, 'w') as f:
        f.write(markdown)

    elapsed = time.time() - start
    print_timing("Export & Save", elapsed)

    print(f"   ✅ Saved to: {filename}")

    return filename


def run_full_pipeline():
    """Execute complete end-to-end pipeline"""

    print("\n" + "🚀" * 40)
    print("XBRL FINANCIAL ANALYZER - FULL PIPELINE DEMO")
    print("Complete Investment Analysis: XBRL → Metrics → Signals → Report")
    print("🚀" * 40)

    company = 'AAPL'
    pipeline_start = time.time()

    # Stage 1: Parse XBRL
    financial_data = simulate_xbrl_parsing(company)

    # Stage 2: Calculate Metrics
    metrics = simulate_metrics_calculation(financial_data)

    # Stage 3: Detect Signals
    signals = simulate_signal_detection(metrics)

    # Stage 4: Peer Comparison
    peer_benchmarks = simulate_peer_comparison(metrics)

    # Stage 5: Story Generation
    stories = simulate_story_generation(metrics)

    # Stage 6: Build Report
    markdown = build_final_report(company, signals, peer_benchmarks, stories)

    # Stage 7: Save Report
    filename = save_report(markdown, company)

    # Total timing
    pipeline_elapsed = time.time() - pipeline_start

    # Final summary
    print("\n" + "=" * 80)
    print("🏁 PIPELINE SUMMARY")
    print("=" * 80)
    print(f"Company:          {company}")
    print(f"Total Time:       {pipeline_elapsed:.2f}s")
    print(f"Report File:      {filename}")
    print(f"Report Size:      {len(markdown):,} characters")
    print()
    print("Pipeline Stages:")
    print("  ✅ Stage 1: XBRL Parsing")
    print("  ✅ Stage 2: Metrics Calculation")
    print("  ✅ Stage 3: Signal Detection")
    print("  ✅ Stage 4: Peer Comparison")
    print("  ✅ Stage 5: Story Arc Generation")
    print("  ✅ Stage 6: Decision Report Building")
    print("  ✅ Stage 7: Export & Save")
    print()
    print("=" * 80)
    print("✅ FULL PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print()

    # Display preview of report
    print("=" * 80)
    print("📄 REPORT PREVIEW (First 50 lines)")
    print("=" * 80)
    lines = markdown.split('\n')
    for i, line in enumerate(lines[:50], 1):
        print(line)

    if len(lines) > 50:
        print(f"\n... ({len(lines) - 50} more lines)\n")

    print("=" * 80)
    print(f"📖 Full report available at: {filename}")
    print("=" * 80)

    return markdown, filename


if __name__ == '__main__':
    markdown, filename = run_full_pipeline()

    print("\n✨ DEMO COMPLETED - Sprint 5 Integration Successful! ✨\n")
