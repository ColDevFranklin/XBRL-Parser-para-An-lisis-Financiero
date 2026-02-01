"""
Sector Benchmark Loader - Franklin Framework Integration

Converts XBRL pipeline output to sector_data format for StatisticalBenchmarkEngine.

Workflow:
1. Auto-discover archivos XBRL por ticker (multi-file)
2. Parse XBRL multi-año via MultiFileXBRLParser
3. Calculate metrics (25 ratios via MetricsCalculator)
4. Convert to sector_data format
5. Initialize StatisticalBenchmarkEngine

FIX SPRINT 6:
- Reemplazó SECDownloader + XBRLParser por MultiFileXBRLParser
- MultiFileXBRLParser auto-discover todos los archivos del ticker
- Extrae cada año de su archivo correspondiente
- Resultado: timeseries completo de 3+ años por empresa

Author: @franklin
Sprint 6 - Multi-Sector Expansion
"""

from typing import Dict, List, Optional
import numpy as np
from backend.config import get_sector_companies
from backend.parsers.multi_file_xbrl_parser import MultiFileXBRLParser
from backend.metrics import calculate_metrics
from backend.signals.statistical_engine import StatisticalBenchmarkEngine


# ============================================================================
# EMPRESA DISPONIBLE EN data/ - Auto-detectado del directorio
# ============================================================================

def discover_available_tickers(data_dir: str = 'data') -> List[str]:
    """
    Descubre qué tickers tienen archivos XBRL en data/.

    Busca patrones: {ticker}_10k_{year}_xbrl.xml
    Retorna tickers únicos que tienen al menos 1 archivo.

    Args:
        data_dir: Directorio con archivos XBRL

    Returns:
        Lista de tickers disponibles (uppercase)
    """
    import re
    from pathlib import Path

    data_path = Path(data_dir)
    if not data_path.exists():
        return []

    tickers = set()
    pattern = re.compile(r'^([a-zA-Z]+)_10k_\d{4}_xbrl\.xml$')

    for filepath in data_path.glob('*.xml'):
        match = pattern.match(filepath.name)
        if match:
            tickers.add(match.group(1).upper())

    return sorted(tickers)


def convert_metrics_to_sector_data(
    ticker: str,
    metrics: Dict[str, Dict[str, np.ndarray]]
) -> Dict[str, Dict[str, np.ndarray]]:
    """
    Convert MetricsCalculator output to sector_data format.

    Note: Formato compatible directo - existe para extensibilidad futura.

    Args:
        ticker: Stock ticker (for logging)
        metrics: Output from calculate_metrics()

    Returns:
        sector_data format for one company
    """
    return metrics


def load_sector_benchmarks(
    sector_code: str,
    year: int = 2024,
    max_companies: Optional[int] = None,
    verbose: bool = True,
    min_years: int = 3
) -> StatisticalBenchmarkEngine:
    """
    Load sector benchmarks and create StatisticalBenchmarkEngine.

    FIX SPRINT 6: Usa MultiFileXBRLParser para extraer timeseries
    completo de todos los archivos disponibles por empresa.

    Workflow:
    1. Get companies para el sector
    2. Filtrar por empresas que tienen archivos en data/
    3. Para cada empresa: MultiFileXBRLParser → timeseries completo
    4. Calculate metrics (25 ratios)
    5. Crear StatisticalBenchmarkEngine

    Args:
        sector_code: 'TECH', 'MINING', 'OIL_GAS', 'RETAIL'
        year: Fiscal year (not used directamente, MultiFileXBRLParser auto-discover)
        max_companies: Limit number of companies (for testing)
        verbose: Print progress
        min_years: Mínimo años requeridos para incluir empresa (default: 3)

    Returns:
        Configured StatisticalBenchmarkEngine with sector benchmarks
    """
    if verbose:
        print(f"\n{'=' * 70}")
        print(f"📊 LOADING SECTOR BENCHMARKS - {sector_code}")
        print(f"{'=' * 70}")

    # Step 1: Get companies para el sector
    sector_companies = get_sector_companies(sector_code)

    # Step 2: Filtrar por empresas que tienen archivos disponibles
    available_tickers = discover_available_tickers('data')
    companies = [t for t in sector_companies if t in available_tickers]

    # Empresas en el sector pero sin archivos
    missing = [t for t in sector_companies if t not in available_tickers]

    if max_companies:
        companies = companies[:max_companies]

    if verbose:
        print(f"Sector companies: {len(sector_companies)}")
        print(f"Available in data/: {len(companies)}")
        if missing:
            print(f"Missing (skipped): {len(missing)} → {', '.join(missing[:10])}"
                  + (f" +{len(missing) - 10} more" if len(missing) > 10 else ""))
        print(f"Min years required: {min_years}")
        print(f"Processing: {len(companies)} companies")
        print()

    # Step 3: Process each company con MultiFileXBRLParser
    sector_data = {}
    failed = []
    skipped_insufficient_years = []

    for i, ticker in enumerate(companies, 1):
        if verbose:
            print(f"[{i}/{len(companies)}] {ticker}")

        try:
            # 3a. MultiFileXBRLParser auto-discover + extract timeseries
            multi_parser = MultiFileXBRLParser(ticker=ticker, data_dir='data')
            timeseries = multi_parser.extract_timeseries(years=4)

            if not timeseries:
                if verbose:
                    print(f"  ✗ No timeseries data extracted")
                failed.append(ticker)
                continue

            # 3b. Validar mínimo de años
            years_extracted = len(timeseries)
            if years_extracted < min_years:
                if verbose:
                    print(f"  ⚠️  Solo {years_extracted} años (requiere {min_years}), skipped")
                skipped_insufficient_years.append((ticker, years_extracted))
                continue

            # 3c. Calculate metrics (25 ratios)
            metrics = calculate_metrics(timeseries, parallel='never')

            # 3d. Convert to sector_data format
            company_data = convert_metrics_to_sector_data(ticker, metrics)

            # 3e. Store
            sector_data[ticker] = company_data

            if verbose:
                metrics_count = sum(len(m) for m in metrics.values())
                print(f"  ✓ {years_extracted} years, {metrics_count} metrics")

        except Exception as e:
            if verbose:
                print(f"  ✗ Error: {e}")
            failed.append(ticker)
            continue

    # Step 4: Summary
    if verbose:
        print(f"\n{'=' * 70}")
        print(f"✅ SECTOR DATA LOADED")
        print(f"{'=' * 70}")
        print(f"Successful: {len(sector_data)}/{len(companies)} "
              f"({len(sector_data) / len(companies) * 100:.1f}%)")

        if skipped_insufficient_years:
            print(f"Skipped (insufficient years):")
            for ticker, years in skipped_insufficient_years:
                print(f"  - {ticker}: {years} years")

        if failed:
            print(f"Failed: {len(failed)} → {', '.join(failed)}")

    if not sector_data:
        raise ValueError(f"No data loaded for sector {sector_code}")

    # Step 5: Create StatisticalBenchmarkEngine
    engine = StatisticalBenchmarkEngine(
        sector_data=sector_data,
        sector_code=sector_code
    )

    if verbose:
        print(f"\n🎯 StatisticalBenchmarkEngine initialized")
        print(f"   Sector: {sector_code}")
        print(f"   Companies: {len(sector_data)}")
        print(f"   Tickers: {', '.join(sector_data.keys())}")
        print(f"{'=' * 70}\n")

    return engine


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def quick_benchmark(
    sector_code: str,
    category: str,
    metric: str,
    year: int = 2024,
    max_companies: Optional[int] = None
) -> Optional[Dict]:
    """
    Quick one-liner to get benchmark for a specific metric.

    Args:
        sector_code: Sector code
        category: Metric category (e.g., 'profitability')
        metric: Metric name (e.g., 'ROE')
        year: Fiscal year
        max_companies: Limit companies (for testing)

    Returns:
        Dict with benchmark stats or None
    """
    engine = load_sector_benchmarks(
        sector_code=sector_code,
        year=year,
        max_companies=max_companies,
        verbose=False
    )

    benchmark = engine.calculate_benchmarks(category, metric)

    if not benchmark:
        return None

    return {
        'metric': benchmark.metric_name,
        'sector': benchmark.sector,
        'p10': benchmark.p10,
        'p25': benchmark.p25,
        'p50': benchmark.p50,
        'p75': benchmark.p75,
        'p90': benchmark.p90,
        'mean': benchmark.mean,
        'std': benchmark.std,
        'sample_size': benchmark.sample_size
    }


# ============================================================================
# DEMO
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SECTOR BENCHMARK LOADER - DEMO")
    print("=" * 70)

    # Descubre qué tickers están disponibles
    available = discover_available_tickers('data')
    print(f"\n📂 Tickers disponibles en data/: {len(available)}")
    print(f"   {', '.join(available)}")

    # Load TECH sector - todas las empresas disponibles
    engine = load_sector_benchmarks(
        sector_code='TECH',
        year=2024,
        max_companies=None,  # Todas las disponibles
        verbose=True,
        min_years=3
    )

    # Calculate ROE benchmark
    print("\n--- ROE Benchmark (TECH Sector) ---")
    roe_bench = engine.calculate_benchmarks('profitability', 'ROE')

    if roe_bench:
        print(f"Metric: {roe_bench.metric_name}")
        print(f"Sector: {roe_bench.sector}")
        print(f"P25: {roe_bench.p25:.1f}%")
        print(f"P50: {roe_bench.p50:.1f}%")
        print(f"P75: {roe_bench.p75:.1f}%")
        print(f"P90: {roe_bench.p90:.1f}%")
        print(f"Sample: {roe_bench.sample_size} companies")
    else:
        print("✗ Insufficient data for ROE benchmark")

    # Calculate all benchmarks
    print("\n--- All Benchmarks ---")
    all_benchmarks = engine.calculate_all_benchmarks()

    for category, metrics in all_benchmarks.items():
        print(f"\n{category.upper()}:")
        for metric_name, benchmark in metrics.items():
            print(f"  {metric_name}: P50={benchmark.p50:.1f}, "
                  f"P75={benchmark.p75:.1f}, n={benchmark.sample_size}")

    print("\n" + "=" * 70)
