"""
Benchmark: Compara performance parallel vs sequential.

Mide:
- Tiempo de cálculo por categoría
- Speedup por paralelización
- Cache hit rate (@lru_cache)

Author: @franklin
Sprint: 4 - Metrics Optimization
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.parsers.multi_file_xbrl_parser import MultiFileXBRLParser
from backend.metrics import calculate_metrics
from backend.metrics.financial_dataframe import FinancialDataFrame
from backend.metrics.metrics_calculator import MetricsCalculator
from backend.metrics.parallel_engine import ParallelMetricsEngine


def benchmark_category(engine, category, iterations=10):
    """Benchmark una categoría específica."""
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        engine.calculate_category(category)
        elapsed = time.perf_counter() - start
        times.append(elapsed * 1000)  # ms

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    return {
        'avg': avg_time,
        'min': min_time,
        'max': max_time,
    }


def main():
    print("="*70)
    print("BENCHMARK: PERFORMANCE COMPARISON")
    print("="*70)

    # ========================================================================
    # PASO 1: Cargar datos
    # ========================================================================
    print("\n[1/3] Cargando time-series...")
    parser = MultiFileXBRLParser(ticker='AAPL', data_dir='data')
    timeseries = parser.extract_timeseries(years=4)

    df = FinancialDataFrame(timeseries)
    calculator = MetricsCalculator(df)

    print(f"✓ Datos cargados: {len(timeseries)} años")

    # ========================================================================
    # PASO 2: Benchmark por categoría (SEQUENTIAL)
    # ========================================================================
    print("\n[2/3] Benchmarking categorías (SEQUENTIAL)...")
    print("-"*70)

    engine_seq = ParallelMetricsEngine(calculator, max_workers=1)

    categories = ['profitability', 'liquidity', 'efficiency', 'leverage']
    seq_results = {}

    for cat in categories:
        result = benchmark_category(engine_seq, cat, iterations=10)
        seq_results[cat] = result
        print(f"{cat:<15} avg={result['avg']:>6.2f}ms  min={result['min']:>6.2f}ms  max={result['max']:>6.2f}ms")

    total_seq = sum(r['avg'] for r in seq_results.values())
    print(f"{'TOTAL':<15} avg={total_seq:>6.2f}ms")

    # ========================================================================
    # PASO 3: Benchmark PARALLEL (todas las categorías juntas)
    # ========================================================================
    print("\n[3/3] Benchmarking PARALLEL (all categories)...")
    print("-"*70)

    engine_par = ParallelMetricsEngine(calculator, max_workers=4)

    par_times = []
    for _ in range(10):
        start = time.perf_counter()
        engine_par.calculate_all()
        elapsed = time.perf_counter() - start
        par_times.append(elapsed * 1000)

    avg_par = sum(par_times) / len(par_times)
    min_par = min(par_times)
    max_par = max(par_times)

    print(f"{'PARALLEL':<15} avg={avg_par:>6.2f}ms  min={min_par:>6.2f}ms  max={max_par:>6.2f}ms")

    # ========================================================================
    # RESUMEN
    # ========================================================================
    print("\n" + "="*70)
    print("📊 RESUMEN BENCHMARK")
    print("="*70)

    speedup = total_seq / avg_par
    efficiency = (speedup / 4) * 100  # 4 cores

    print(f"\nSequential total: {total_seq:.2f}ms")
    print(f"Parallel total:   {avg_par:.2f}ms")
    print(f"Speedup:          {speedup:.2f}x")
    print(f"Efficiency:       {efficiency:.1f}% (de 4 cores)")

    # Breakdown por categoría
    print("\n📋 Breakdown por categoría:")
    print("-"*70)
    print(f"{'Categoría':<15} {'Sequential':>12} {'Contribución':>12}")
    print("-"*70)

    for cat in categories:
        seq_time = seq_results[cat]['avg']
        contribution = (seq_time / total_seq) * 100
        print(f"{cat:<15} {seq_time:>10.2f}ms {contribution:>10.1f}%")

    # Validaciones
    print("\n🎯 VALIDACIONES")
    print("-"*70)

    checks = {
        "Speedup >1.5x": speedup > 1.5,
        "Speedup <4.0x": speedup < 4.0,  # Overhead esperado
        "Parallel <50ms": avg_par < 50,
        "Sequential <150ms": total_seq < 150,
    }

    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"{status} {check}")

    all_passed = all(checks.values())

    if all_passed:
        print("\n🎉 BENCHMARK EXITOSO")
        print(f"✓ Paralelización efectiva ({speedup:.2f}x speedup)")
        print(f"✓ Overhead bajo ({100-efficiency:.1f}%)")
    else:
        print("\n⚠️  REVISAR PERFORMANCE")

    print("="*70)


if __name__ == "__main__":
    main()
