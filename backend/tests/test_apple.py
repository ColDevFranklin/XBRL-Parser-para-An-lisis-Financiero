# backend/tests/test_apple.py

"""
Test de regresión: Apple 10-K
Validación Sprint 2: ContextManager elimina duplicados
"""
import sys
sys.path.insert(0, '/home/h4ckio/Documentos/projects')
from backend.parsers.xbrl_parser import XBRLParser


def test_apple_parsing_succeeds():
    """Test básico: El parser no debe crashear"""
    parser = XBRLParser('data/apple_10k_xbrl.xml')
    assert parser.load() == True

    # Sprint 2: Validar ContextManager inicializado
    assert parser.context_mgr is not None
    assert parser.context_mgr.fiscal_year == 2025

    data = parser.extract_all()
    assert data is not None
    assert 'balance_sheet' in data
    assert 'income_statement' in data
    assert 'cash_flow' in data


def test_apple_balance_sheet_equation():
    """
    Validación contable crítica:
    Assets = Liabilities + Equity (±1%)

    Sprint 2: Debe mejorar precisión vs Sprint 1
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

    print(f"\n--- Apple Balance Sheet (Sprint 2) ---")
    print(f"Assets:      ${assets:>15,.0f}")
    print(f"Liabilities: ${liabilities:>15,.0f}")
    print(f"Equity:      ${equity:>15,.0f}")
    print(f"Diferencia:  {diff_pct:>15.4f}%")

    # Sprint 2: Criterio más estricto (debe ser casi perfecto)
    assert diff_pct < 0.5, f"Balance sheet no cuadra: {diff_pct:.4f}%"


def test_apple_no_duplicate_values():
    """
    NUEVO Sprint 2: Validar que NO hay valores duplicados.

    Con ContextManager, cada campo debe tener UN SOLO valor
    (del contexto consolidado).
    """
    parser = XBRLParser('data/apple_10k_xbrl.xml')
    parser.load()

    # Verificar que usa contexto correcto
    balance_ctx = parser.context_mgr.get_balance_context()
    income_ctx = parser.context_mgr.get_income_context()

    print(f"\n--- Apple Context Validation ---")
    print(f"Balance context: {balance_ctx}")
    print(f"Income context: {income_ctx}")

    assert balance_ctx == 'c-20'  # Dato real del diagnóstico
    assert income_ctx == 'c-1'

    # Extraer valores - deben ser únicos
    data = parser.extract_all()

    # Todos los valores deben ser float (no listas)
    for section_name, section_data in data.items():
        for field_name, value in section_data.items():
            if value is not None:
                assert isinstance(value, float), \
                    f"{section_name}.{field_name} debe ser float, no {type(value)}"


def test_apple_15_fields():
    """Verificar extracción de 15 campos core"""
    parser = XBRLParser('data/apple_10k_xbrl.xml')
    parser.load()
    data = parser.extract_all()

    required_fields = [
        # Balance Sheet (7)
        'Assets', 'Liabilities', 'StockholdersEquity',
        'CurrentAssets', 'CashAndEquivalents', 'LongTermDebt', 'CurrentLiabilities',
        # Income Statement (6)
        'Revenues', 'NetIncomeLoss', 'CostOfRevenue',
        'GrossProfit', 'OperatingIncomeLoss', 'InterestExpense',
        # Cash Flow (2)
        'OperatingCashFlow', 'CapitalExpenditures'
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

    print(f"\n--- Apple: Extracción de Campos (Sprint 2) ---")
    print(f"Extraídos: {len(extracted)}/15")
    if missing:
        print(f"Faltantes: {missing}")

    assert len(extracted) >= 14, f"Muy pocos campos: {len(extracted)}/15"
