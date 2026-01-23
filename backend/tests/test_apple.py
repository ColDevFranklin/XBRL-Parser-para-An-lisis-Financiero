# backend/tests/test_apple.py

"""
Test de regresión: Apple 10-K
Validación Sprint 2: ContextManager elimina duplicados
Validación Transparency: SourceTrace con metadata completa
"""
import sys
sys.path.insert(0, '/home/h4ckio/Documentos/projects')
from backend.parsers.xbrl_parser import XBRLParser
from backend.engines.tracked_metric import SourceTrace


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
    Transparency: Usa SourceTrace.raw_value
    """
    parser = XBRLParser('data/apple_10k_xbrl.xml')
    parser.load()
    data = parser.extract_all()

    balance = data['balance_sheet']
    assets_trace = balance.get('Assets')
    liabilities_trace = balance.get('Liabilities')
    equity_trace = balance.get('StockholdersEquity')

    # Validar que campos existen
    assert assets_trace is not None, "Assets no extraído"
    assert liabilities_trace is not None, "Liabilities no extraído"
    assert equity_trace is not None, "Equity no extraído"

    # CAMBIO: Extraer raw_value de SourceTrace
    assets = assets_trace.raw_value
    liabilities = liabilities_trace.raw_value
    equity = equity_trace.raw_value

    # Validar ecuación contable
    left_side = assets
    right_side = liabilities + equity
    diff_pct = abs(left_side - right_side) / left_side * 100

    print(f"\n--- Apple Balance Sheet (Sprint 2 + Transparency) ---")
    print(f"Assets:      ${assets:>15,.0f}")
    print(f"Liabilities: ${liabilities:>15,.0f}")
    print(f"Equity:      ${equity:>15,.0f}")
    print(f"Diferencia:  {diff_pct:>15.4f}%")

    # Sprint 2: Criterio más estricto (debe ser casi perfecto)
    assert diff_pct < 0.5, f"Balance sheet no cuadra: {diff_pct:.4f}%"


def test_apple_no_duplicate_values():
    """
    NUEVO Sprint 2: Validar que NO hay valores duplicados.
    NUEVO Transparency: Validar que son SourceTrace (no floats)

    Con ContextManager, cada campo debe tener UN SOLO valor
    (del contexto consolidado) encapsulado en SourceTrace.
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

    # Extraer valores - deben ser SourceTrace (no listas ni floats)
    data = parser.extract_all()

    # CAMBIO: Todos los valores deben ser SourceTrace
    for section_name, section_data in data.items():
        for field_name, value in section_data.items():
            if value is not None:
                assert isinstance(value, SourceTrace), \
                    f"{section_name}.{field_name} debe ser SourceTrace, no {type(value)}"


def test_apple_15_fields():
    """
    Verificar extracción de 15 campos core.
    Transparency: Validar que todos tienen metadata completa.
    """
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

    print(f"\n--- Apple: Extracción de Campos (Sprint 2 + Transparency) ---")
    print(f"Extraídos: {len(extracted)}/15")
    if missing:
        print(f"Faltantes: {missing}")

    assert len(extracted) >= 14, f"Muy pocos campos: {len(extracted)}/15"


# ============================================================================
# NUEVOS TESTS: Transparency Engine
# ============================================================================

def test_apple_source_trace_metadata():
    """
    NUEVO: Validar que SourceTrace contiene metadata completa.

    Cada campo extraído debe tener:
    - xbrl_tag
    - raw_value
    - context_id
    - extracted_at
    - section
    """
    parser = XBRLParser('data/apple_10k_xbrl.xml')
    parser.load()

    balance = parser.extract_balance_sheet()
    assets_trace = balance['Assets']

    print(f"\n--- Apple Assets SourceTrace ---")
    print(f"XBRL Tag:    {assets_trace.xbrl_tag}")
    print(f"Raw Value:   ${assets_trace.raw_value:,.0f}")
    print(f"Context ID:  {assets_trace.context_id}")
    print(f"Extracted:   {assets_trace.extracted_at.isoformat()}")
    print(f"Section:     {assets_trace.section}")

    # Validar todos los campos
    assert assets_trace.xbrl_tag is not None
    assert assets_trace.raw_value > 0
    assert assets_trace.context_id == 'c-20'
    assert assets_trace.extracted_at is not None
    assert assets_trace.section == 'balance_sheet'


def test_apple_source_trace_serialization():
    """
    NUEVO: Validar que SourceTrace puede serializarse a dict.

    Esto es crítico para APIs y almacenamiento.
    """
    parser = XBRLParser('data/apple_10k_xbrl.xml')
    parser.load()

    income = parser.extract_income_statement()
    revenue_trace = income['Revenues']

    # Serializar
    data = revenue_trace.to_dict()

    print(f"\n--- Apple Revenues Serialized ---")
    import json
    print(json.dumps(data, indent=2))

    # Validar estructura
    assert 'xbrl_tag' in data
    assert 'raw_value' in data
    assert 'context_id' in data
    assert 'extracted_at' in data
    assert 'section' in data

    # Validar valores
    assert data['section'] == 'income_statement'
    assert data['context_id'] == 'c-1'
    assert data['raw_value'] > 0


def test_apple_trace_consistency_across_sections():
    """
    NUEVO: Validar que contextos son consistentes por sección.

    - Balance Sheet → instant context (c-20)
    - Income Statement → duration context (c-1)
    - Cash Flow → duration context (c-1)
    """
    parser = XBRLParser('data/apple_10k_xbrl.xml')
    parser.load()

    data = parser.extract_all()

    # Balance Sheet: instant context
    balance = data['balance_sheet']
    for field_name, trace in balance.items():
        if trace is not None:
            assert trace.context_id == 'c-20', \
                f"Balance field {field_name} usa contexto incorrecto: {trace.context_id}"
            assert trace.section == 'balance_sheet'

    # Income Statement: duration context
    income = data['income_statement']
    for field_name, trace in income.items():
        if trace is not None:
            assert trace.context_id == 'c-1', \
                f"Income field {field_name} usa contexto incorrecto: {trace.context_id}"
            assert trace.section == 'income_statement'

    # Cash Flow: duration context (mismo que income)
    cf = data['cash_flow']
    for field_name, trace in cf.items():
        if trace is not None:
            assert trace.context_id == 'c-1', \
                f"Cash flow field {field_name} usa contexto incorrecto: {trace.context_id}"
            assert trace.section == 'cash_flow'

    print(f"\n✓ Contextos consistentes por sección")


def test_apple_full_traceability_example():
    """
    NUEVO: Demo completo de trazabilidad end-to-end.

    Muestra cómo un analista puede rastrear cada valor
    de vuelta al XBRL original.
    """
    parser = XBRLParser('data/apple_10k_xbrl.xml')
    parser.load()

    data = parser.extract_all()

    # Ejemplo: Rastrear NetIncomeLoss
    net_income_trace = data['income_statement']['NetIncomeLoss']

    print(f"\n{'='*60}")
    print(f"APPLE NET INCOME - FULL TRACEABILITY")
    print(f"{'='*60}")
    print(f"Value:        ${net_income_trace.raw_value:,.0f}")
    print(f"XBRL Tag:     {net_income_trace.xbrl_tag}")
    print(f"Context:      {net_income_trace.context_id}")
    print(f"Section:      {net_income_trace.section}")
    print(f"Extracted:    {net_income_trace.extracted_at.isoformat()}")
    print(f"\nTo verify in source file:")
    print(f"  1. Open: data/apple_10k_xbrl.xml")
    print(f"  2. Search: <{net_income_trace.xbrl_tag} contextRef=\"{net_income_trace.context_id}\">")
    print(f"  3. Compare: {net_income_trace.raw_value}")
    print(f"{'='*60}\n")

    # Este test siempre pasa - es para demostración
    assert True
