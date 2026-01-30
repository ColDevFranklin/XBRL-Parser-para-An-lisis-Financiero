"""
Demo: Decision Report Builder - Complete Apple Investment Report
Shows end-to-end report generation with real Apple data.

Author: @franklin (CTO)
Sprint 5 - Micro-Tarea 5: Decision Report Builder Demo
"""
from backend.reports.report_builder import ReportBuilder
from backend.signals.signal_taxonomy import Signal, SignalType, SignalCategory
from backend.signals.peer_comparison import PeerBenchmark
from backend.signals.story_generator import StoryArc, StoryPattern, ConfidenceLevel


def create_apple_signals():
    """Create sample Apple signals (simplified for demo)"""
    return [
        # PROFITABILITY - Strong BUY signals
        Signal(
            type=SignalType.BUY,
            category=SignalCategory.PROFITABILITY,
            metric='ROE',
            value=197.0,
            threshold=15.0,
            message='ROE 197.0% > 15.0% - Exceptional capital efficiency',
            trend='+9.1% CAGR'
        ),
        Signal(
            type=SignalType.BUY,
            category=SignalCategory.PROFITABILITY,
            metric='ROIC',
            value=111.1,
            threshold=12.0,
            message='ROIC 111.1% > 12.0% - Superior returns on invested capital',
            trend='+20.5% CAGR'
        ),
        Signal(
            type=SignalType.WATCH,
            category=SignalCategory.PROFITABILITY,
            metric='NetMargin',
            value=24.0,
            threshold=20.0,
            message='NetMargin 24.0% (monitoring for expansion)',
            trend='-2.0% CAGR'
        ),

        # LIQUIDITY - Mixed signals
        Signal(
            type=SignalType.RED_FLAG,
            category=SignalCategory.LIQUIDITY,
            metric='CurrentRatio',
            value=0.87,
            threshold=2.0,
            message='CurrentRatio 0.87 < 2.0 - Below safety threshold',
            trend='-0.4% CAGR'
        ),
        Signal(
            type=SignalType.WATCH,
            category=SignalCategory.LIQUIDITY,
            metric='QuickRatio',
            value=0.82,
            threshold=1.0,
            message='QuickRatio 0.82 (monitoring)',
            trend='+1.2% CAGR'
        ),

        # EFFICIENCY - Positive
        Signal(
            type=SignalType.BUY,
            category=SignalCategory.EFFICIENCY,
            metric='AssetTurnover',
            value=1.15,
            threshold=0.8,
            message='AssetTurnover 1.15 > 0.8 - Efficient asset utilization',
            trend='+3.5% CAGR'
        ),
        Signal(
            type=SignalType.WATCH,
            category=SignalCategory.EFFICIENCY,
            metric='InventoryTurnover',
            value=35.2,
            threshold=30.0,
            message='InventoryTurnover 35.2 (strong)',
            trend='+5.1% CAGR'
        ),

        # LEVERAGE - Good control
        Signal(
            type=SignalType.BUY,
            category=SignalCategory.LEVERAGE,
            metric='DebtToEquity',
            value=-4.81,
            threshold=0.5,
            message='DebtToEquity -4.81 - Net cash position',
            trend='Improving deleveraging'
        ),
        Signal(
            type=SignalType.BUY,
            category=SignalCategory.LEVERAGE,
            metric='InterestCoverage',
            value=85.3,
            threshold=3.0,
            message='InterestCoverage 85.3 > 3.0 - Excellent coverage',
            trend='+12.0% CAGR'
        ),
    ]


def create_apple_peer_benchmarks():
    """Create Apple peer comparison data"""
    return {
        'ROE': PeerBenchmark(
            metric_name='ROE',
            company_value=197.0,
            peer_median=32.8,
            peer_mean=50.0,
            percentile=100,
            beats_peers=True,
            peer_count=20,
            interpretation='Elite Performance 🏆'
        ),
        'ROIC': PeerBenchmark(
            metric_name='ROIC',
            company_value=111.1,
            peer_median=34.9,
            peer_mean=45.2,
            percentile=100,
            beats_peers=True,
            peer_count=20,
            interpretation='Elite Performance 🏆'
        ),
        'NetMargin': PeerBenchmark(
            metric_name='NetMargin',
            company_value=24.0,
            peer_median=36.0,
            peer_mean=30.5,
            percentile=35,
            beats_peers=False,
            peer_count=20,
            interpretation='Below Median ↘️'
        ),
        'CurrentRatio': PeerBenchmark(
            metric_name='CurrentRatio',
            company_value=0.87,
            peer_median=1.27,
            peer_mean=1.35,
            percentile=15,
            beats_peers=False,
            peer_count=20,
            interpretation='Bottom Quartile 🔻'
        ),
        'AssetTurnover': PeerBenchmark(
            metric_name='AssetTurnover',
            company_value=1.15,
            peer_median=0.85,
            peer_mean=0.92,
            percentile=80,
            beats_peers=True,
            peer_count=20,
            interpretation='Top Quartile ↗️'
        ),
    }


def create_apple_stories():
    """Create Apple story arcs"""
    return {
        'ROE': StoryArc(
            metric_name='ROE',
            pattern=StoryPattern.ACCELERATION,
            cagr=9.1,
            narrative='ROE accelerated from 151.9% to 197.0% (+9.1% CAGR), '
                     'demonstrating exceptional operational improvement and margin expansion. '
                     'This sustained growth trajectory suggests strong competitive positioning.',
            confidence=ConfidenceLevel.MEDIUM,
            r_squared=0.64,
            start_value=151.9,
            end_value=197.0,
            years=4,
            context='profitability'
        ),
        'ROIC': StoryArc(
            metric_name='ROIC',
            pattern=StoryPattern.ACCELERATION,
            cagr=20.5,
            narrative='ROIC accelerated from 63.5% to 111.1% (+20.5% CAGR), '
                     'demonstrating exceptional operational improvement and margin expansion. '
                     'This sustained growth trajectory suggests strong competitive positioning.',
            confidence=ConfidenceLevel.HIGH,
            r_squared=0.71,
            start_value=63.5,
            end_value=111.1,
            years=4,
            context='profitability'
        ),
        'NetMargin': StoryArc(
            metric_name='NetMargin',
            pattern=StoryPattern.VOLATILE,
            cagr=-2.0,
            narrative='NetMargin fluctuated between 26.9% and 25.3% with high variability, '
                     'indicating inconsistent operational execution or cyclical business dynamics. '
                     'Volatility complicates valuation and suggests higher business risk.',
            confidence=ConfidenceLevel.LOW,
            r_squared=0.14,
            start_value=26.9,
            end_value=25.3,
            years=4,
            context='profitability'
        ),
        'CurrentRatio': StoryArc(
            metric_name='CurrentRatio',
            pattern=StoryPattern.PLATEAU,
            cagr=-0.4,
            narrative='CurrentRatio held steady around 0.88 (-0.4% CAGR), '
                     'maintaining adequate but not improving liquidity buffers. '
                     'Stable liquidity is acceptable but offers limited upside.',
            confidence=ConfidenceLevel.LOW,
            r_squared=0.00,
            start_value=0.88,
            end_value=0.87,
            years=4,
            context='liquidity'
        ),
    }


def demo_apple_report():
    """Generate complete Apple investment report"""

    print("\n" + "=" * 80)
    print("🎯 GENERATING APPLE INVESTMENT DECISION REPORT")
    print("=" * 80 + "\n")

    # Create data
    signals = create_apple_signals()
    peer_benchmarks = create_apple_peer_benchmarks()
    stories = create_apple_stories()

    print(f"📊 Data Loaded:")
    print(f"   - Signals: {len(signals)}")
    print(f"   - Peer Benchmarks: {len(peer_benchmarks)}")
    print(f"   - Story Arcs: {len(stories)}")
    print()

    # Build report
    builder = ReportBuilder()

    print("🔨 Building report...")
    report = builder.build_report(
        company='AAPL',
        signals=signals,
        peer_benchmarks=peer_benchmarks,
        stories=stories,
        metadata={
            'analyst': 'Franklin Framework',
            'methodology': 'Graham/Buffett/Munger',
            'data_source': 'SEC EDGAR XBRL'
        }
    )
    print("✅ Report built successfully\n")

    # Display summary
    print("=" * 80)
    print("📋 REPORT SUMMARY")
    print("=" * 80)
    print(f"Company:        {report.company}")
    print(f"Date:           {report.date[:10]}")
    print(f"Recommendation: {report.recommendation}")
    print(f"Confidence:     {report.confidence}")
    print()

    # Export to markdown
    print("📝 Exporting to Markdown...")
    markdown = builder.export_markdown(report)
    print("✅ Markdown export complete\n")

    # Display markdown report
    print("=" * 80)
    print("📄 FULL REPORT (Markdown)")
    print("=" * 80)
    print(markdown)
    print()

    # Export to JSON
    print("=" * 80)
    print("💾 EXPORTING TO FORMATS")
    print("=" * 80)

    json_output = builder.export_json(report)
    text_output = builder.export_text(report)

    print(f"✅ JSON export: {len(json_output)} characters")
    print(f"✅ Text export: {len(text_output)} characters")
    print(f"✅ Markdown export: {len(markdown)} characters")
    print()

    # Save to files (optional)
    try:
        with open('/tmp/apple_report.md', 'w') as f:
            f.write(markdown)
        print("💾 Saved to: /tmp/apple_report.md")

        with open('/tmp/apple_report.json', 'w') as f:
            f.write(json_output)
        print("💾 Saved to: /tmp/apple_report.json")

        with open('/tmp/apple_report.txt', 'w') as f:
            f.write(text_output)
        print("💾 Saved to: /tmp/apple_report.txt")
    except Exception as e:
        print(f"⚠️  Could not save files: {e}")

    print()
    print("=" * 80)
    print("✅ DEMO COMPLETED - Decision Report Builder Working!")
    print("=" * 80)
    print()


if __name__ == '__main__':
    demo_apple_report()
