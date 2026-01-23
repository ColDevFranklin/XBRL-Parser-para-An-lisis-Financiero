# backend/tests/test_microsoft.py
"""
Test de regresión: Microsoft 10-K
Validación Sprint 2: Context filtering mejora precisión
Validación Transparency: SourceTrace con metadata completa
"""
import sys
sys.path.insert(0, '/home/h4ckio/Documentos/projects')
from backend.parsers.xbrl_parser import XBRLParser
from backend.engines.tracked_metric import SourceTrace


def test_microsoft_parsing_succeeds():
    """Test básico: El parser no debe crashear"""
    parser = XBRLParser('data/msft_10k_xbrl.xml')
    assert parser.load() == True

    # Sprint 2: Validar ContextManager
    assert parser.context_mgr is not None
    assert parser.context_mgr.fiscal_year == 2025

    data = parser.extract_all()
    assert data is not None


def test_microsoft_balance_sheet_equation():
    """
    Validación contable crítica:
    Assets = Liabilities + Equity (±1%)
    Transparency: Usa SourceTrace.raw_value
    """
    parser = XBRLParser('data/msft_10k_xbrl.xml')
    parser.load()
    data = parser.extract_all()

    balance = data['balance_sheet']
    assets_trace = balance.get('Assets')
    liabilities_trace = balance.get('Liabilities')
    equity_trace = balance.get('StockholdersEquity')

    assert assets_trace is not None, "Assets no extraído"
    assert liabilities_trace is not None, "Liabilities no extraído"
    assert equity_trace is not None, "Equity no extraído"

    # CAMBIO: Extraer raw_value de SourceTrace
    assets = assets_trace.raw_value
    liabilities = liabilities_trace.raw_value
    equity = equity_trace.raw_value

    left_side = assets
    right_side = liabilities + equity
    diff_pct = abs(left_side - right_side) / left_side * 100

    print(f"\n--- Microsoft Balance Sheet (Sprint 2 + Transparency) ---")
    print(f"Assets:      ${assets:>15,.0f}")
    print(f"Liabilities: ${liabilities:>15,.0f}")
    print(f"Equity:      ${equity:>15,.0f}")
    print(f"Diferencia:  {diff_pct:>15.4f}%")

    assert diff_pct < 1.0, f"Balance sheet no cuadra: {diff_pct:.4f}%"


def test_microsoft_15_fields():
    """
    Verificar extracción de 15 campos core.
    Transparency: Validar que todos son SourceTrace.
    """
    parser = XBRLParser('data/msft_10k_xbrl.xml')
    parser.load()
    data = parser.extract_all()

    required_fields = [
        'Assets', 'Liabilities', 'StockholdersEquity',
        'CurrentAssets', 'CashAndEquivalents', 'LongTermDebt', 'CurrentLiabilities',
        'Revenues', 'NetIncomeLoss', 'CostOfRevenue',
        'GrossProfit', 'OperatingIncomeLoss', 'InterestExpense',
        'OperatingCashFlow', 'CapitalExpenditures'
    ]

    all_data = {
        **data['balance_sheet'],
        **data['income_statement'],
        **data['cash_flow']
    }

    extracted = [f for f in required_fields if all_data.get(f) is not None]
    missing = [f for f in required_fields if all_data.get(f) is None]

    print(f"\n--- Microsoft: Campos (Sprint 2 + Transparency) ---")
    print(f"Extraídos: {len(extracted)}/15")
    if missing:
        print(f"Faltantes: {missing}")

    # NUEVO: Validar que son SourceTrace
    for field in extracted:
        value = all_data[field]
        assert isinstance(value, SourceTrace), \
            f"{field} debe ser SourceTrace, no {type(value)}"

    assert len(extracted) >= 14, f"Muy pocos campos: {len(extracted)}/15"


# ============================================================================
# NUEVOS TESTS: Transparency Engine
# ============================================================================

def test_microsoft_source_trace_metadata():
    """
    NUEVO: Validar metadata completa en Microsoft data.
    """
    parser = XBRLParser('data/msft_10k_xbrl.xml')
    parser.load()

    income = parser.extract_income_statement()
    revenue_trace = income['Revenues']

    print(f"\n--- Microsoft Revenues SourceTrace ---")
    print(f"XBRL Tag:    {revenue_trace.xbrl_tag}")
    print(f"Raw Value:   ${revenue_trace.raw_value:,.0f}")
    print(f"Context ID:  {revenue_trace.context_id}")
    print(f"Section:     {revenue_trace.section}")

    # Validar campos
    assert revenue_trace.xbrl_tag is not None
    assert revenue_trace.raw_value > 0
    assert revenue_trace.context_id is not None
    assert revenue_trace.section == 'income_statement'


def test_microsoft_trace_serialization():
    """
    NUEVO: Validar serialización para Microsoft.
    """
    parser = XBRLParser('data/msft_10k_xbrl.xml')
    parser.load()

    balance = parser.extract_balance_sheet()
    assets_trace = balance['Assets']

    # Serializar
    data = assets_trace.to_dict()

    # Validar estructura
    assert 'xbrl_tag' in data
    assert 'raw_value' in data
    assert 'context_id' in data
    assert 'section' in data
    assert data['section'] == 'balance_sheet'
