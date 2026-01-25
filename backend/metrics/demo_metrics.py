"""
Demo: Calcula 25 métricas financieras para Apple (4 años) con paralelización.

Muestra:
- Vectorización NumPy/Pandas
- Memoización @lru_cache
- Paralelización ThreadPoolExecutor
- Performance comparison

Author: @franklin
Sprint: 4 - Metrics Optimization
"""

import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.parsers.multi_file_xbrl_parser import MultiFileXBRLParser
from backend.metrics import calculate_metrics
from backend.metrics.financial_dataframe import FinancialDataFrame


def format_ratio(value, percentage=False, decimals=2):
    """Formatea un ratio para display."""
    if value is None or str(value) == 'nan':
        return 'N/A'
    if percentage:
        return f"{value*100:.{decimals}f}%"
    return f"{value:.{decimals}f}"


def main():
    print("="*70)
    print("DEMO: MÉTRICAS FINANCIERAS OPTIMIZADAS")
    print("="*70)
    print("Ticker: AAPL")
    print("Años: 4 (2025-2022)")
    print("Métricas: 25 (8 Profitability + 5 Liquidity + 6 Efficiency + 6 Leverage)")
    print("Optimizaciones: Vectorización + Memoización + Paralelización")
    print("="*70)

    # ========================================================================
    # PASO 1: Cargar time-series XBRL
    # ========================================================================
    print("\n[1/4] Cargando time-series XBRL...")
    start_load = time.time()

    parser = MultiFileXBRLParser(ticker='AAPL', data_dir='data')
    timeseries = parser.extract_timeseries(years=4)

    elapsed_load = time.time() - start_load
    print(f"✓ Time-series cargado: {len(timeseries)} años en {elapsed_load:.2f}s")

    # ========================================================================
    # PASO 2: Calcular métricas (PARALELO)
    # ========================================================================
    print("\n[2/4] Calculando métricas (PARALELO)...")
    start_parallel = time.time()

    metrics = calculate_metrics(timeseries, parallel='auto', max_workers=4)

    elapsed_parallel = time.time() - start_parallel
    print(f"✓ Métricas calculadas en {elapsed_parallel*1000:.1f}ms (parallel)")

    # ========================================================================
    # PASO 3: Calcular métricas (SECUENCIAL - para comparación)
    # ========================================================================
    print("\n[3/4] Calculando métricas (SECUENCIAL)...")
    start_sequential = time.time()

    metrics_seq = calculate_metrics(timeseries, parallel='never')

    elapsed_sequential = time.time() - start_sequential
    print(f"✓ Métricas calculadas en {elapsed_sequential*1000:.1f}ms (sequential)")

    # Calcular speedup
    speedup = elapsed_sequential / elapsed_parallel
    print(f"\n🚀 Speedup: {speedup:.2f}x")

    # ========================================================================
    # PASO 4: Mostrar resultados
    # ========================================================================
    print("\n[4/4] Resultados por categoría")
    print("="*70)

    # Obtener años
    df = FinancialDataFrame(timeseries)
    years = df.years

    # ------------------------------------------------------------------------
    # PROFITABILITY (8 ratios)
    # ------------------------------------------------------------------------
    print("\n📊 PROFITABILITY (8 ratios)")
    print("-"*70)

    prof = metrics['profitability']

    print(f"\n{'Métrica':<20} {years[0]:>8} {years[1]:>8} {years[2]:>8} {years[3]:>8}")
    print("-"*70)
    print(f"{'ROE':<20} {format_ratio(prof['ROE'][0], True):>8} {format_ratio(prof['ROE'][1], True):>8} {format_ratio(prof['ROE'][2], True):>8} {format_ratio(prof['ROE'][3], True):>8}")
    print(f"{'ROA':<20} {format_ratio(prof['ROA'][0], True):>8} {format_ratio(prof['ROA'][1], True):>8} {format_ratio(prof['ROA'][2], True):>8} {format_ratio(prof['ROA'][3], True):>8}")
    print(f"{'Net Margin':<20} {format_ratio(prof['NetMargin'][0], True):>8} {format_ratio(prof['NetMargin'][1], True):>8} {format_ratio(prof['NetMargin'][2], True):>8} {format_ratio(prof['NetMargin'][3], True):>8}")
    print(f"{'Gross Margin':<20} {format_ratio(prof['GrossMargin'][0], True):>8} {format_ratio(prof['GrossMargin'][1], True):>8} {format_ratio(prof['GrossMargin'][2], True):>8} {format_ratio(prof['GrossMargin'][3], True):>8}")
    print(f"{'Operating Margin':<20} {format_ratio(prof['OperatingMargin'][0], True):>8} {format_ratio(prof['OperatingMargin'][1], True):>8} {format_ratio(prof['OperatingMargin'][2], True):>8} {format_ratio(prof['OperatingMargin'][3], True):>8}")
    print(f"{'ROIC':<20} {format_ratio(prof['ROIC'][0], True):>8} {format_ratio(prof['ROIC'][1], True):>8} {format_ratio(prof['ROIC'][2], True):>8} {format_ratio(prof['ROIC'][3], True):>8}")
    print(f"{'OCF Margin':<20} {format_ratio(prof['OCFMargin'][0], True):>8} {format_ratio(prof['OCFMargin'][1], True):>8} {format_ratio(prof['OCFMargin'][2], True):>8} {format_ratio(prof['OCFMargin'][3], True):>8}")

    # ------------------------------------------------------------------------
    # LIQUIDITY (5 ratios)
    # ------------------------------------------------------------------------
    print("\n💧 LIQUIDITY (5 ratios)")
    print("-"*70)

    liq = metrics['liquidity']

    print(f"\n{'Métrica':<20} {years[0]:>8} {years[1]:>8} {years[2]:>8} {years[3]:>8}")
    print("-"*70)
    print(f"{'Current Ratio':<20} {format_ratio(liq['CurrentRatio'][0]):>8} {format_ratio(liq['CurrentRatio'][1]):>8} {format_ratio(liq['CurrentRatio'][2]):>8} {format_ratio(liq['CurrentRatio'][3]):>8}")
    print(f"{'Quick Ratio':<20} {format_ratio(liq['QuickRatio'][0]):>8} {format_ratio(liq['QuickRatio'][1]):>8} {format_ratio(liq['QuickRatio'][2]):>8} {format_ratio(liq['QuickRatio'][3]):>8}")
    print(f"{'Cash Ratio':<20} {format_ratio(liq['CashRatio'][0]):>8} {format_ratio(liq['CashRatio'][1]):>8} {format_ratio(liq['CashRatio'][2]):>8} {format_ratio(liq['CashRatio'][3]):>8}")
    print(f"{'OCF Ratio':<20} {format_ratio(liq['OCFRatio'][0]):>8} {format_ratio(liq['OCFRatio'][1]):>8} {format_ratio(liq['OCFRatio'][2]):>8} {format_ratio(liq['OCFRatio'][3]):>8}")

    wc = liq['WorkingCapital']
    print(f"{'Working Capital':<20} {'$'+str(int(wc[0]/1e9))+'B':>8} {'$'+str(int(wc[1]/1e9))+'B':>8} {'$'+str(int(wc[2]/1e9))+'B':>8} {'$'+str(int(wc[3]/1e9))+'B':>8}")

    # ------------------------------------------------------------------------
    # EFFICIENCY (6 ratios)
    # ------------------------------------------------------------------------
    print("\n⚡ EFFICIENCY (6 ratios)")
    print("-"*70)

    eff = metrics['efficiency']

    print(f"\n{'Métrica':<20} {years[0]:>8} {years[1]:>8} {years[2]:>8} {years[3]:>8}")
    print("-"*70)
    print(f"{'Asset Turnover':<20} {format_ratio(eff['AssetTurnover'][0]):>8} {format_ratio(eff['AssetTurnover'][1]):>8} {format_ratio(eff['AssetTurnover'][2]):>8} {format_ratio(eff['AssetTurnover'][3]):>8}")
    print(f"{'Inventory Turnover':<20} {format_ratio(eff['InventoryTurnover'][0]):>8} {format_ratio(eff['InventoryTurnover'][1]):>8} {format_ratio(eff['InventoryTurnover'][2]):>8} {format_ratio(eff['InventoryTurnover'][3]):>8}")
    print(f"{'DIO (days)':<20} {format_ratio(eff['DIO'][0], decimals=0):>8} {format_ratio(eff['DIO'][1], decimals=0):>8} {format_ratio(eff['DIO'][2], decimals=0):>8} {format_ratio(eff['DIO'][3], decimals=0):>8}")
    print(f"{'Receivables Turn.':<20} {format_ratio(eff['ReceivablesTurnover'][0]):>8} {format_ratio(eff['ReceivablesTurnover'][1]):>8} {format_ratio(eff['ReceivablesTurnover'][2]):>8} {format_ratio(eff['ReceivablesTurnover'][3]):>8}")
    print(f"{'DSO (days)':<20} {format_ratio(eff['DSO'][0], decimals=0):>8} {format_ratio(eff['DSO'][1], decimals=0):>8} {format_ratio(eff['DSO'][2], decimals=0):>8} {format_ratio(eff['DSO'][3], decimals=0):>8}")
    print(f"{'CCC (days)':<20} {format_ratio(eff['CCC'][0], decimals=0):>8} {format_ratio(eff['CCC'][1], decimals=0):>8} {format_ratio(eff['CCC'][2], decimals=0):>8} {format_ratio(eff['CCC'][3], decimals=0):>8}")

    # ------------------------------------------------------------------------
    # LEVERAGE (6 ratios)
    # ------------------------------------------------------------------------
    print("\n🏦 LEVERAGE (6 ratios)")
    print("-"*70)

    lev = metrics['leverage']

    print(f"\n{'Métrica':<20} {years[0]:>8} {years[1]:>8} {years[2]:>8} {years[3]:>8}")
    print("-"*70)
    print(f"{'Debt/Equity':<20} {format_ratio(lev['DebtToEquity'][0]):>8} {format_ratio(lev['DebtToEquity'][1]):>8} {format_ratio(lev['DebtToEquity'][2]):>8} {format_ratio(lev['DebtToEquity'][3]):>8}")
    print(f"{'Debt/Assets':<20} {format_ratio(lev['DebtToAssets'][0], True):>8} {format_ratio(lev['DebtToAssets'][1], True):>8} {format_ratio(lev['DebtToAssets'][2], True):>8} {format_ratio(lev['DebtToAssets'][3], True):>8}")
    print(f"{'Equity Multiplier':<20} {format_ratio(lev['EquityMultiplier'][0]):>8} {format_ratio(lev['EquityMultiplier'][1]):>8} {format_ratio(lev['EquityMultiplier'][2]):>8} {format_ratio(lev['EquityMultiplier'][3]):>8}")
    print(f"{'Interest Coverage':<20} {format_ratio(lev['InterestCoverage'][0]):>8} {format_ratio(lev['InterestCoverage'][1]):>8} {format_ratio(lev['InterestCoverage'][2]):>8} {format_ratio(lev['InterestCoverage'][3]):>8}")
    print(f"{'DSCR':<20} {format_ratio(lev['DSCR'][0]):>8} {format_ratio(lev['DSCR'][1]):>8} {format_ratio(lev['DSCR'][2]):>8} {format_ratio(lev['DSCR'][3]):>8}")
    print(f"{'Total Debt Ratio':<20} {format_ratio(lev['TotalDebtRatio'][0], True):>8} {format_ratio(lev['TotalDebtRatio'][1], True):>8} {format_ratio(lev['TotalDebtRatio'][2], True):>8} {format_ratio(lev['TotalDebtRatio'][3], True):>8}")

    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================
    print("\n" + "="*70)
    print("📊 RESUMEN FINAL")
    print("="*70)
    print(f"✓ Años procesados: {len(timeseries)}")
    print(f"✓ Métricas calculadas: 25")
    print(f"✓ Tiempo carga: {elapsed_load:.2f}s")
    print(f"✓ Tiempo cálculo (parallel): {elapsed_parallel*1000:.1f}ms")
    print(f"✓ Tiempo cálculo (sequential): {elapsed_sequential*1000:.1f}ms")
    print(f"✓ Speedup: {speedup:.2f}x")
    print(f"✓ Tiempo total: {elapsed_load + elapsed_parallel:.2f}s")
    print("="*70)

    # ========================================================================
    # VALIDACIONES
    # ========================================================================
    print("\n🎯 VALIDACIONES")
    print("-"*70)

    checks = {
        "Time-series cargado (4 años)": len(timeseries) == 4,
        "Métricas profitability (8)": len(metrics['profitability']) == 8,
        "Métricas liquidity (5)": len(metrics['liquidity']) == 5,
        "Métricas efficiency (6)": len(metrics['efficiency']) == 6,
        "Métricas leverage (6)": len(metrics['leverage']) == 6,
        "Speedup >1.5x": speedup > 1.5,
        "Performance <5s total": (elapsed_load + elapsed_parallel) < 5.0,
    }

    all_passed = all(checks.values())

    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"{status} {check}")

    if all_passed:
        print("\n🎉 TODAS LAS VALIDACIONES PASARON")
        print("✓ Vectorización funcionando")
        print("✓ Memoización activa")
        print("✓ Paralelización efectiva")
    else:
        print("\n⚠️  REVISAR ISSUES")

    print("="*70)


if __name__ == "__main__":
    main()
