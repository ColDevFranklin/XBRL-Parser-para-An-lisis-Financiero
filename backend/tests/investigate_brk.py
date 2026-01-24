"""
Sprint 3 Paso 3.2 - Diagnóstico BRK.A
Análisis profundo de por qué Berkshire falla

Ejecutar desde raíz del proyecto:
    python3 -m backend.tests.investigate_brk
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.parsers.xbrl_parser import XBRLParser
from lxml import etree


def analyze_brk_structure(xml_path: str):
    """Análisis profundo XBRL de BRK.A"""

    print("=" * 80)
    print("DIAGNÓSTICO - BERKSHIRE HATHAWAY XBRL")
    print("=" * 80)
    print()

    tree = etree.parse(xml_path)
    root = tree.getroot()
    namespaces = root.nsmap

    # Namespace correcto para XBRL
    ns = {'xbrli': 'http://www.xbrl.org/2003/instance'}

    print("1. ESTRUCTURA DEL ARCHIVO")
    print("-" * 80)
    print(f"Root tag: {root.tag}")
    print(f"Namespaces: {len(namespaces)}")
    for prefix, uri in list(namespaces.items())[:5]:
        print(f"  {prefix or '(default)'}: {uri}")
    print()

    print("2. ANÁLISIS DE CONTEXTS")
    print("-" * 80)

    contexts = root.findall('.//xbrli:context', ns)
    print(f"Total contexts: {len(contexts)}")

    instant_contexts = []
    duration_contexts = []

    for ctx in contexts:
        ctx_id = ctx.get('id')
        instant = ctx.find('.//xbrli:instant', ns)

        if instant is not None:
            instant_contexts.append((ctx_id, instant.text))
        else:
            start = ctx.find('.//xbrli:startDate', ns)
            end = ctx.find('.//xbrli:endDate', ns)
            duration_contexts.append((ctx_id,
                start.text if start is not None else None,
                end.text if end is not None else None))

    print(f"  Instant: {len(instant_contexts)}")
    print(f"  Duration: {len(duration_contexts)}")

    print("\nPrimeros 10 instant:")
    for ctx_id, date in instant_contexts[:10]:
        print(f"  {ctx_id}: {date}")

    print("\nPrimeros 10 duration:")
    for ctx_id, start, end in duration_contexts[:10]:
        print(f"  {ctx_id}: {start} → {end}")
    print()

    print("3. FISCAL YEAR END")
    print("-" * 80)

    doc_period_end = root.find('.//dei:DocumentPeriodEndDate', namespaces)
    if doc_period_end is not None:
        print(f"✓ DocumentPeriodEndDate: {doc_period_end.text}")
    else:
        print("⚠️  DocumentPeriodEndDate NO ENCONTRADO")

    fiscal_year_end = root.find('.//dei:CurrentFiscalYearEndDate', namespaces)
    if fiscal_year_end is not None:
        print(f"✓ CurrentFiscalYearEndDate: {fiscal_year_end.text}")
    else:
        print("⚠️  CurrentFiscalYearEndDate NO ENCONTRADO")
    print()

    print("4. CONCEPTOS CLAVE")
    print("-" * 80)

    # Balance Sheet
    balance_concepts = [
        'Assets',
        'Liabilities',
        'StockholdersEquity',
        'AssetsCurrent',
        'LiabilitiesCurrent',
        'CashAndCashEquivalentsAtCarryingValue',
        'Cash',
        'LongTermDebt',
        'LongTermDebtNoncurrent'
    ]

    # Income Statement - EXPANDIDO
    income_concepts = [
        'Revenues',
        'Revenue',
        'NetIncome',
        'NetIncomeLoss',
        'ProfitLoss',
        'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',
        'CostOfRevenue',
        'CostOfGoodsAndServicesSold',
        'GrossProfit',
        'OperatingIncomeLoss',
        'OperatingIncome',
        'InterestExpense',
        'InterestExpenseDebt'
    ]

    # Cash Flow
    cashflow_concepts = [
        'NetCashProvidedByUsedInOperatingActivities',
        'PaymentsToAcquirePropertyPlantAndEquipment'
    ]

    print("\n=== BALANCE SHEET ===")
    for concept in balance_concepts:
        elements = root.findall(f'.//us-gaap:{concept}', namespaces)
        if elements:
            print(f"✓ {concept}: {len(elements)} ocurrencias")
            for elem in elements[:2]:
                ctx_ref = elem.get('contextRef')
                value = elem.text
                print(f"    contextRef: {ctx_ref}, valor: {value}")
        else:
            print(f"✗ {concept}")

    print("\n=== INCOME STATEMENT ===")
    for concept in income_concepts:
        elements = root.findall(f'.//us-gaap:{concept}', namespaces)
        if elements:
            print(f"✓ {concept}: {len(elements)} ocurrencias")
            for elem in elements[:2]:
                ctx_ref = elem.get('contextRef')
                value = elem.text
                print(f"    contextRef: {ctx_ref}, valor: {value}")
        else:
            print(f"✗ {concept}")

    print("\n=== CASH FLOW ===")
    for concept in cashflow_concepts:
        elements = root.findall(f'.//us-gaap:{concept}', namespaces)
        if elements:
            print(f"✓ {concept}: {len(elements)} ocurrencias")
            for elem in elements[:2]:
                ctx_ref = elem.get('contextRef')
                value = elem.text
                print(f"    contextRef: {ctx_ref}, valor: {value}")
        else:
            print(f"✗ {concept}")
    print()

    print("5. TEST XBRL PARSER")
    print("-" * 80)

    parser = XBRLParser(xml_path)
    if parser.load():
        print("✓ Parser loaded")
        print(f"  Fiscal year-end: {parser.fiscal_year_end}")
        print(f"  Year: {parser.year}")

        print(f"\n  ContextManager:")
        print(f"    Balance: {parser.context_manager.balance_context}")
        print(f"    Income: {parser.context_manager.income_context}")

        try:
            data = parser.extract_all()
            print("\n  Extracción:")
            for section, fields in data.items():
                found = sum(1 for v in fields.values() if v)
                total = len(fields)
                print(f"    {section}: {found}/{total}")

                if found > 0:
                    for field, value in fields.items():
                        if value:
                            print(f"      • {field}: {value.raw_value}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("✗ Parser FAILED")

    print()
    print("=" * 80)


if __name__ == '__main__':
    xml_path = project_root / 'data' / 'brk_10k_xbrl.xml'
    analyze_brk_structure(str(xml_path))
