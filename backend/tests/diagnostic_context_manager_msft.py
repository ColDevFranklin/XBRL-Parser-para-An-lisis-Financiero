"""
Context Manager Diagnostic - MSFT 2024
Investigar por qué retorna C_ea3864ea... en lugar de C_f6acec30...

Ejecutar: python3 -m backend.tests.diagnostic_context_manager_msft

Author: @franklin
Sprint: 6 - Multi-Sector Expansion
"""

from backend.parsers.xbrl_parser import XBRLParser
from lxml import etree

def run_diagnostic():
    print("=" * 80)
    print("CONTEXT MANAGER DIAGNOSTIC - MSFT 2024")
    print("=" * 80)

    # Parse MSFT
    parser = XBRLParser('data/msft_10k_2024_xbrl.xml')
    parser.load()

    print("\n" + "=" * 80)
    print("PASO 1: Ver qué contextos detecta el Context Manager")
    print("=" * 80)

    available_years = parser.context_mgr.get_available_years()
    print(f"\nAños detectados: {available_years}")

    print("\n" + "=" * 80)
    print("PASO 2: Ver contexto que retorna para año 2024")
    print("=" * 80)

    balance_ctx_2024 = parser.context_mgr.get_balance_context(year=2024)
    print(f"\nBalance context 2024 retornado: {balance_ctx_2024}")

    print("\n" + "=" * 80)
    print("PASO 3: Analizar TODOS los contexts en el XML")
    print("=" * 80)

    tree = etree.parse('data/msft_10k_2024_xbrl.xml')
    root = tree.getroot()

    # Buscar TODOS los contexts
    contexts = root.xpath(".//xbrli:context", namespaces={'xbrli': 'http://www.xbrl.org/2003/instance'})
    print(f"\nTotal contexts en XML: {len(contexts)}")

    # Filtrar contexts de tipo 'instant' (balance sheet)
    instant_contexts = []
    for ctx in contexts:
        ctx_id = ctx.get('id')

        # Buscar period/instant
        instant = ctx.xpath(".//xbrli:instant", namespaces={'xbrli': 'http://www.xbrl.org/2003/instance'})

        if instant:
            instant_date = instant[0].text
            instant_contexts.append({
                'id': ctx_id,
                'date': instant_date
            })

    print(f"Contexts tipo 'instant': {len(instant_contexts)}")

    # Agrupar por fecha
    from collections import defaultdict
    by_date = defaultdict(list)
    for ctx in instant_contexts:
        by_date[ctx['date']].append(ctx['id'])

    print(f"\nContexts agrupados por fecha:")
    for date in sorted(by_date.keys(), reverse=True)[:10]:
        ctx_ids = by_date[date]
        print(f"  {date}: {len(ctx_ids)} contexts")
        for ctx_id in ctx_ids[:3]:
            print(f"    - {ctx_id}")
        if len(ctx_ids) > 3:
            print(f"    ... y {len(ctx_ids) - 3} más")

    print("\n" + "=" * 80)
    print("PASO 4: Verificar cuál tiene Assets/Equity")
    print("=" * 80)

    # Contextos candidatos para 2024
    target_date_2024 = '2024-06-30'  # Fiscal year end de MSFT

    print(f"\nBuscando contexts para fecha {target_date_2024}:")

    if target_date_2024 in by_date:
        candidate_contexts = by_date[target_date_2024]
        print(f"Encontrados: {len(candidate_contexts)} contexts")

        for ctx_id in candidate_contexts[:5]:
            print(f"\n--- Context: {ctx_id} ---")

            # Buscar Assets
            assets = root.xpath(f".//*[local-name()='Assets'][@contextRef='{ctx_id}']")
            if assets:
                print(f"  ✓ Assets: ${assets[0].text}")
            else:
                print(f"  ✗ Assets: NO")

            # Buscar Equity
            equity = root.xpath(f".//*[local-name()='StockholdersEquity'][@contextRef='{ctx_id}']")
            if equity:
                print(f"  ✓ Equity: ${equity[0].text}")
            else:
                print(f"  ✗ Equity: NO")

            # Contar total elementos
            total_elements = root.xpath(f".//*[@contextRef='{ctx_id}']")
            print(f"  Total elementos: {len(total_elements)}")

    print("\n" + "=" * 80)
    print("PASO 5: Comparar con contexto retornado por Context Manager")
    print("=" * 80)

    print(f"\nContext Manager retornó: {balance_ctx_2024}")

    # Analizar ese contexto
    elements_in_returned = root.xpath(f".//*[@contextRef='{balance_ctx_2024}']")
    print(f"Total elementos en contexto retornado: {len(elements_in_returned)}")

    assets_in_returned = root.xpath(f".//*[local-name()='Assets'][@contextRef='{balance_ctx_2024}']")
    equity_in_returned = root.xpath(f".//*[local-name()='StockholdersEquity'][@contextRef='{balance_ctx_2024}']")

    print(f"Assets en contexto retornado: {len(assets_in_returned)}")
    print(f"Equity en contexto retornado: {len(equity_in_returned)}")

    if len(elements_in_returned) == 1:
        print("\n⚠️  PROBLEMA DETECTADO:")
        print("   Context Manager retornó contexto con solo 1 elemento")
        print("   Debería retornar contexto con 50+ elementos")

    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

    print("\n🎯 CONCLUSIÓN:")
    print("   Context Manager tiene bug en filtrado de contexts")
    print("   Retorna contexto incorrecto para MSFT 2024")
    print("   Necesita fix en backend/engines/context_manager.py")

if __name__ == "__main__":
    run_diagnostic()
