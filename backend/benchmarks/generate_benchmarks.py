#!/usr/bin/env python3
"""
Generate Tech Benchmarks from SEC Data

Batch processes S&P 500 Tech sector companies to calculate
statistical benchmarks for all financial metrics.

Usage:
    python3 backend/benchmarks/generate_benchmarks.py

Output:
    backend/benchmarks/tech_benchmarks_2025Q4.json

Author: @franklin
Sprint 5: Micro-Tarea 3 - Peer Comparison Engine
"""

import time
from pathlib import Path

from backend.benchmarks.benchmark_calculator import BenchmarkCalculator
from backend.benchmarks.company_universe import get_tech_universe


def progress_callback(ticker: str, current: int, total: int):
    """Print progress during calculation"""
    percentage = (current / total) * 100
    print(f"[{current:3d}/{total:3d}] ({percentage:5.1f}%) Processing {ticker:6s}...")


def main():
    """Main execution"""
    print("=" * 70)
    print("📊 TECH SECTOR BENCHMARK CALCULATOR")
    print("=" * 70)

    # Configuration
    data_dir = 'data'
    years = 4
    output_file = 'backend/benchmarks/tech_benchmarks_2025Q4.json'

    # Universe info
    universe = get_tech_universe()
    print(f"\n📁 Configuration:")
    print(f"   Data directory: {data_dir}")
    print(f"   Years analyzed: {years}")
    print(f"   Universe size: {len(universe)} companies")
    print(f"   Output file: {output_file}")

    # Verify data directory exists
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"\n❌ ERROR: Data directory '{data_dir}' not found")
        print(f"   Please ensure XBRL files are downloaded")
        return 1

    # Initialize calculator
    print(f"\n⚙️  Initializing calculator...")
    calculator = BenchmarkCalculator(data_dir=data_dir, years=years)

    # Calculate benchmarks
    print(f"\n🔄 Processing companies...\n")
    start_time = time.time()

    benchmarks = calculator.calculate_tech_benchmarks(
        progress_callback=progress_callback
    )

    elapsed = time.time() - start_time

    # Summary statistics
    print(f"\n" + "=" * 70)
    print(f"📈 BENCHMARK SUMMARY")
    print(f"=" * 70)
    print(f"   Metrics calculated: {len(benchmarks)}")
    print(f"   Processing time: {elapsed:.1f}s")
    print(f"   Avg time per company: {elapsed/len(universe):.2f}s")

    # Show sample benchmarks
    if benchmarks:
        print(f"\n📊 Sample Benchmarks:")
        for metric_name in ['ROE', 'NetMargin', 'CurrentRatio', 'DebtToEquity']:
            if metric_name in benchmarks:
                b = benchmarks[metric_name]
                print(f"\n   {metric_name}:")
                print(f"      Median: {b.median:.2f}")
                print(f"      Average: {b.avg:.2f}")
                print(f"      P25-P75: [{b.p25:.2f}, {b.p75:.2f}]")
                print(f"      Sample: {b.sample_size} companies")

    # Export to JSON
    print(f"\n💾 Exporting benchmarks...")
    calculator.export_to_json(benchmarks, output_file)

    print(f"\n" + "=" * 70)
    print(f"✅ BENCHMARK GENERATION COMPLETE")
    print(f"=" * 70)
    print(f"\n📄 Output file: {output_file}")
    print(f"   You can now use these benchmarks for peer comparison\n")

    return 0


if __name__ == "__main__":
    exit(main())
