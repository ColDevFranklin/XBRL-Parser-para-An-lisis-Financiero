
import sys
sys.path.insert(0, '/home/h4ckio/Documentos/projects')

from backend.parsers.xbrl_parser import XBRLParser


def test_apple_parsing_succeeds():
    """Test básico: El parser no debe crashear"""
    parser = XBRLParser('data/apple_10k_xbrl.xml')

    assert parser.load() == True
    data = parser.extract_all()

    assert data is not None
    assert 'balance_sheet' in data
    assert 'income_statement' in data
    assert 'cash_flow' in data


def test_apple_balance_sheet_equation():
    """
    Validación contable crítica:
    Assets = Liabilities + Equity (±1%)
    """
    parser = XBRLParser('data/apple_10k_xbrl.xml')
    parser.load()
    data = parser.extract_all()

    balance = data['balance_sheet']

    assets = balance.get('Assets')
    liabilities = balance.get('Liabilities')
    equity = balance.get('StockholdersEquity')

    # Validar que campos existen
    assert assets is not None, "Assets no extraído"
    assert liabilities is not None, "Liabilities no extraído"
    assert equity is not None, "Equity no extraído"

    # Validar ecuación contable
    left_side = assets
    right_side = liabilities + equity
    diff_pct = abs(left_side - right_side) / left_side * 100

    print(f"\n--- Apple Balance Sheet ---")
    print(f"Assets:      ${assets:>15,.0f}")
    print(f"Liabilities: ${liabilities:>15,.0f}")
    print(f"Equity:      ${equity:>15,.0f}")
    print(f"Diferencia:  {diff_pct:>15.4f}%")

    assert diff_pct < 1.0, f"Balance sheet no cuadra: {diff_pct:.4f}%"


def test_apple_15_fields():
    """Verificar extracción de 15 campos core"""
    parser = XBRLParser('data/apple_10k_xbrl.xml')
    parser.load()
    data = parser.extract_all()

    required_fields = [
        # Balance Sheet (7)
        'Assets', 'Liabilities', 'StockholdersEquity',
        'CurrentAssets', 'CashAndEquivalents', 'LongTermDebt', 'CurrentLiabilities',
        # Income Statement (5)
        'Revenues', 'NetIncomeLoss', 'CostOfRevenue', 'GrossProfit', 'OperatingIncomeLoss',
        # Cash Flow (2)
        'OperatingCashFlow', 'CapitalExpenditures',
        # Adicional (1)
        'InterestExpense'
    ]

    all_data = {
        **data['balance_sheet'],
        **data['income_statement'],
        **data['cash_flow']
    }

    extracted = []
    missing = []

    for field in required_fields:
        if all_data.get(field) is not None:
            extracted.append(field)
        else:
            missing.append(field)

    print(f"\n--- Apple: Extracción de Campos ---")
    print(f"Extraídos: {len(extracted)}/15")
    if missing:
        print(f"Faltantes: {missing}")

    assert len(extracted) >= 14, f"Muy pocos campos: {len(extracted)}/15"

