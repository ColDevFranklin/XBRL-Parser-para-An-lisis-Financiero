"""
Diagnostic Script - Issue #001: Missing Assets in Historical Years
Ejecutar: python3 diagnostic_issue_001.py
"""

from backend.parsers.xbrl_parser import XBRLParser
from datetime import datetime

print("=" * 80)
print("DIAGNOSTIC SCRIPT - ISSUE #001: Missing Assets in Historical Years")
print("=" * 80)

# Inicializar parser con Apple 2024 10-K
parser = XBRLParser('data/aapl_10k_2024_xbrl.xml')
parser.load()

print("\n" + "=" * 80)
print("STEP 1: Verificar años disponibles")
print("=" * 80)

available_years = parser.context_mgr.get_available_years()
print(f"\nAños detectados: {available_years}")
print(f"Total años: {len(available_years)}")

print("\n" + "=" * 80)
print("STEP 2: Verificar contextos por año")
print("=" * 80)

for year in available_years:
    print(f"\n--- AÑO {year} ---")
    try:
        balance_ctx = parser.context_mgr.get_balance_context(year=year)
        print(f"  Balance context: {balance_ctx} ✓")
    except ValueError as e:
        print(f"  Balance context: ERROR - {e}")
        balance_ctx = None

    try:
        income_ctx = parser.context_mgr.get_income_context(year=year)
        print(f"  Income context:  {income_ctx} ✓")
    except ValueError as e:
        print(f"  Income context:  ERROR - {e}")
        income_ctx = None

print("\n" + "=" * 80)
print("STEP 3: Intentar extraer Assets para cada año")
print("=" * 80)

for year in available_years:
    print(f"\n--- AÑO {year} - Assets Extraction ---")

    try:
        balance_ctx = parser.context_mgr.get_balance_context(year=year)

        # Intentar extraer Assets
        assets_trace = parser._get_value_by_context(
            'Assets',
            balance_ctx,
            'balance_sheet'
        )

        if assets_trace:
            print(f"  ✓ Assets encontrado: ${assets_trace.raw_value:,.0f}")
            print(f"    Tag XBRL: {assets_trace.xbrl_tag}")
            print(f"    Context: {assets_trace.context_id}")
        else:
            print(f"  ✗ Assets NO encontrado")
            print(f"    Context usado: {balance_ctx}")

            # DEBUG: Ver qué otros campos SÍ se extraen
            print(f"\n    DEBUG - Intentando otros campos del Balance Sheet:")
            test_fields = ['Equity', 'Liabilities', 'Revenue', 'NetIncome']
            for field in test_fields:
                # Revenue y NetIncome usan income_ctx
                if field in ['Revenue', 'NetIncome']:
                    try:
                        income_ctx = parser.context_mgr.get_income_context(year=year)
                        val = parser._get_value_by_context(field, income_ctx, 'income_statement')
                    except:
                        val = None
                else:
                    val = parser._get_value_by_context(field, balance_ctx, 'balance_sheet')

                if val:
                    print(f"      ✓ {field}: ${val.raw_value:,.0f}")
                else:
                    print(f"      ✗ {field}: NO encontrado")

    except ValueError as e:
        print(f"  ✗ ERROR: {e}")

print("\n" + "=" * 80)
print("STEP 4: Extraer datos completos por año (extract_year_data)")
print("=" * 80)

for year in available_years:
    print(f"\n--- AÑO {year} - Full Extraction ---")

    try:
        year_data = parser._extract_year_data(year)

        # Contar campos extraídos
        total_fields = len(year_data)
        core_fields = ['Assets', 'Revenue', 'NetIncome', 'Equity']
        core_found = sum(1 for f in core_fields if f in year_data)

        print(f"  Total campos extraídos: {total_fields}")
        print(f"  Core fields (4): {core_found}/4")
        print(f"  Core fields encontrados: {[f for f in core_fields if f in year_data]}")
        print(f"  Core fields faltantes: {[f for f in core_fields if f not in year_data]}")

        # Validación actual del sistema
        if year_data.get('Assets') and year_data.get('Revenue'):
            print(f"  ✓ ACEPTADO por validación actual (Assets AND Revenue)")
        else:
            print(f"  ✗ RECHAZADO por validación actual (falta Assets o Revenue)")

        # Validación propuesta (Approach A)
        if core_found >= 3:
            print(f"  ✓ SERÍA ACEPTADO con Approach A (3/4 core fields)")
        else:
            print(f"  ✗ SERÍA RECHAZADO con Approach A (solo {core_found}/4 core fields)")

    except Exception as e:
        print(f"  ✗ ERROR en extracción: {e}")

print("\n" + "=" * 80)
print("STEP 5: Mapping Gaps Report")
print("=" * 80)

gaps_report = parser.get_mapping_gaps_report()
print(gaps_report)

print("\n" + "=" * 80)
print("STEP 6: Extraer time-series completo (método actual)")
print("=" * 80)

try:
    timeseries = parser.extract_timeseries(years=4)

    print(f"\nAños extraídos exitosamente: {len(timeseries)}/{len(available_years)}")
    print(f"Años aceptados: {list(timeseries.keys())}")
    print(f"Años rechazados: {[y for y in available_years if y not in timeseries]}")

    # Impacto en sector benchmarking
    if len(timeseries) >= 3:
        print(f"\n✓ Sector benchmarking FUNCIONAL (n={len(timeseries)} >= 3)")
    else:
        print(f"\n✗ Sector benchmarking BLOQUEADO (n={len(timeseries)} < 3)")

except Exception as e:
    print(f"✗ ERROR en extract_timeseries: {e}")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
