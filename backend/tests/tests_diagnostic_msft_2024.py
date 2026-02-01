"""
Diagnostic - MSFT 2024 Missing Assets/Equity
Ejecutar: python3 -m backend.tests.diagnostic_msft_2024

Author: @franklin
Sprint: 6 - Multi-Sector Expansion
"""

from backend.parsers.xbrl_parser import XBRLParser

print("=" * 80)
print("DIAGNOSTIC - MSFT 2024 MISSING ASSETS/EQUITY")
print("=" * 80)

# Parse MSFT XBRL
print("\n📂 Cargando XBRL de Microsoft 2024...")
parser = XBRLParser('data/msft_10k_2024_xbrl.xml')
parser.load()

print("\n" + "=" * 80)
print("TEST 1: Verificar Años Disponibles")
print("=" * 80)

available_years = parser.context_mgr.get_available_years()
print(f"\nAños detectados: {available_years}")

print("\n" + "=" * 80)
print("TEST 2: Extraer Año 2024 Específicamente")
print("=" * 80)

try:
    # Get contexts for 2024
    balance_ctx = parser.context_mgr.get_balance_context(year=2024)
    print(f"\nBalance context 2024: {balance_ctx}")

    try:
        income_ctx = parser.context_mgr.get_income_context(year=2024)
        print(f"Income context 2024:  {income_ctx}")
    except ValueError as e:
        print(f"Income context 2024:  ERROR - {e}")
        income_ctx = None

    # Intentar extraer Assets
    print("\n--- Buscando Assets ---")
    assets = parser._get_value_by_context('Assets', balance_ctx, 'balance_sheet')
    if assets:
        print(f"✓ Assets encontrado: ${assets.raw_value:,.0f}")
    else:
        print("✗ Assets NO encontrado")

        # Debug: ver qué tags están disponibles
        available_tags = parser._get_available_tags()
        assets_tags = [t for t in available_tags if 'asset' in t.lower()]
        print(f"\n  Tags con 'asset' disponibles ({len(assets_tags)}):")
        for tag in assets_tags[:10]:
            print(f"    - {tag}")

    # Intentar extraer Equity
    print("\n--- Buscando Equity ---")
    equity = parser._get_value_by_context('Equity', balance_ctx, 'balance_sheet')
    if equity:
        print(f"✓ Equity encontrado: ${equity.raw_value:,.0f}")
    else:
        print("✗ Equity NO encontrado")

        # Debug: ver qué tags están disponibles
        available_tags = parser._get_available_tags()
        equity_tags = [t for t in available_tags if 'equity' in t.lower() or 'stockholder' in t.lower()]
        print(f"\n  Tags con 'equity/stockholder' disponibles ({len(equity_tags)}):")
        for tag in equity_tags[:10]:
            print(f"    - {tag}")

    # Intentar extraer Revenue (que sí funciona)
    print("\n--- Buscando Revenue (control) ---")
    if income_ctx:
        revenue = parser._get_value_by_context('Revenue', income_ctx, 'income_statement')
        if revenue:
            print(f"✓ Revenue encontrado: ${revenue.raw_value:,.0f}")
        else:
            print("✗ Revenue NO encontrado")

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("TEST 3: Full Year Data Extraction")
print("=" * 80)

try:
    year_data = parser._extract_year_data(2024)

    print(f"\nTotal campos extraídos: {len(year_data)}")

    core_fields = ['Assets', 'Revenue', 'NetIncome', 'Equity']
    for field in core_fields:
        if field in year_data:
            print(f"  ✓ {field}: ${year_data[field].raw_value:,.0f}")
        else:
            print(f"  ✗ {field}: NO ENCONTRADO")

    print(f"\nOtros campos extraídos:")
    other_fields = [k for k in year_data.keys() if k not in core_fields]
    for field in other_fields[:10]:
        print(f"  - {field}: ${year_data[field].raw_value:,.0f}")

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("TEST 4: Mapping Gaps Report")
print("=" * 80)

gaps_report = parser.get_mapping_gaps_report()
print(gaps_report)

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
