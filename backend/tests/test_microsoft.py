# backend/tests/test_microsoft.py

"""
Test de regresión: Microsoft 10-K
Validación Sprint 2: Context filtering mejora precisión
"""
import sys
sys.path.insert(0, '/home/h4ckio/Documentos/projects')
from backend.parsers.xbrl_parser import XBRLParser


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
    """
    parser = XBRLParser('data/msft_10k_xbrl.xml')
    parser.load()
    data = parser.extract_all()

    balance = data['balance_sheet']
    assets = balance.get('Assets')
    liabilities = balance.get('Liabilities')
    equity = balance.get('StockholdersEquity')

    assert assets is not None, "Assets no extraído"
    assert liabilities is not None, "Liabilities no extraído"
    assert equity is not None, "Equity no extraído"

    left_side = assets
    right_side = liabilities + equity
    diff_pct = abs(left_side - right_side) / left_side * 100

    print(f"\n--- Microsoft Balance Sheet (Sprint 2) ---")
    print(f"Assets:      ${assets:>15,.0f}")
    print(f"Liabilities: ${liabilities:>15,.0f}")
    print(f"Equity:      ${equity:>15,.0f}")
    print(f"Diferencia:  {diff_pct:>15.4f}%")

    assert diff_pct < 1.0, f"Balance sheet no cuadra: {diff_pct:.4f}%"


def test_microsoft_15_fields():
    """Verificar extracción de 15 campos core"""
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

    print(f"\n--- Microsoft: Campos (Sprint 2) ---")
    print(f"Extraídos: {len(extracted)}/15")
    if missing:
        print(f"Faltantes: {missing}")

    assert len(extracted) >= 14, f"Muy pocos campos: {len(extracted)}/15"
