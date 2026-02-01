"""
Deep Diagnostic - Buscar Assets/Equity directamente en MSFT XML
Ejecutar: python3 -m backend.tests.deep_diagnostic_msft

Author: @franklin
Sprint: 6 - Multi-Sector Expansion
"""

from lxml import etree

def run_deep_diagnostic():
    print("=" * 80)
    print("DEEP DIAGNOSTIC - MSFT 2024 ASSETS/EQUITY XML SEARCH")
    print("=" * 80)

    # Cargar XML directamente
    print("\n📂 Cargando XML...")
    tree = etree.parse('data/msft_10k_2024_xbrl.xml')
    root = tree.getroot()

    print(f"✓ XML cargado")
    print(f"  Root tag: {root.tag}")
    print(f"  Namespaces: {len(root.nsmap)}")

    print("\n" + "=" * 80)
    print("BÚSQUEDA 1: Encontrar TODOS los tags con 'Assets' (sin filtro)")
    print("=" * 80)

    # Buscar TODOS los elementos con 'Assets' en el nombre
    assets_elements = root.xpath(".//*[contains(local-name(), 'Assets')]")
    print(f"\nTotal elementos con 'Assets': {len(assets_elements)}")

    # Filtrar solo los que tienen contextRef
    assets_with_context = [e for e in assets_elements if e.get('contextRef')]
    print(f"Con contextRef: {len(assets_with_context)}")

    # Mostrar los primeros 20
    print(f"\nPrimeros 20 tags 'Assets':")
    seen = set()
    for i, elem in enumerate(assets_with_context[:50], 1):
        tag_name = elem.tag.split('}')[-1]
        if tag_name not in seen:
            context = elem.get('contextRef')
            value = elem.text.strip() if elem.text else "N/A"
            print(f"  {i:2d}. {tag_name}")
            print(f"      Context: {context}")
            print(f"      Value: {value[:50]}")
            seen.add(tag_name)

            if len(seen) >= 20:
                break

    print("\n" + "=" * 80)
    print("BÚSQUEDA 2: Encontrar TODOS los tags con 'Equity' (sin filtro)")
    print("=" * 80)

    # Buscar TODOS los elementos con 'Equity' en el nombre
    equity_elements = root.xpath(".//*[contains(local-name(), 'Equity') or contains(local-name(), 'Stockholder')]")
    print(f"\nTotal elementos con 'Equity/Stockholder': {len(equity_elements)}")

    # Filtrar solo los que tienen contextRef
    equity_with_context = [e for e in equity_elements if e.get('contextRef')]
    print(f"Con contextRef: {len(equity_with_context)}")

    # Mostrar los primeros 20
    print(f"\nPrimeros 20 tags 'Equity/Stockholder':")
    seen = set()
    for i, elem in enumerate(equity_with_context[:50], 1):
        tag_name = elem.tag.split('}')[-1]
        if tag_name not in seen:
            context = elem.get('contextRef')
            value = elem.text.strip() if elem.text else "N/A"
            print(f"  {i:2d}. {tag_name}")
            print(f"      Context: {context}")
            print(f"      Value: {value[:50]}")
            seen.add(tag_name)

            if len(seen) >= 20:
                break

    print("\n" + "=" * 80)
    print("BÚSQUEDA 3: Buscar contexto específico C_ea3864ea-2797-4beb-9b69-8584b28e9669")
    print("=" * 80)

    target_context = "C_ea3864ea-2797-4beb-9b69-8584b28e9669"

    # Todos los elementos en ese contexto
    elements_in_context = root.xpath(f".//*[@contextRef='{target_context}']")
    print(f"\nTotal elementos en contexto {target_context}: {len(elements_in_context)}")

    # Buscar Assets específicamente
    assets_in_context = [e for e in elements_in_context if 'asset' in e.tag.lower()]
    print(f"Assets en este contexto: {len(assets_in_context)}")

    if assets_in_context:
        print("\nAssets encontrados:")
        for elem in assets_in_context[:10]:
            tag_name = elem.tag.split('}')[-1]
            value = elem.text.strip() if elem.text else "N/A"
            print(f"  - {tag_name}: {value}")

    # Buscar Equity específicamente
    equity_in_context = [e for e in elements_in_context if 'equity' in e.tag.lower() or 'stockholder' in e.tag.lower()]
    print(f"\nEquity en este contexto: {len(equity_in_context)}")

    if equity_in_context:
        print("\nEquity encontrados:")
        for elem in equity_in_context[:10]:
            tag_name = elem.tag.split('}')[-1]
            value = elem.text.strip() if elem.text else "N/A"
            print(f"  - {tag_name}: {value}")

    print("\n" + "=" * 80)
    print("BÚSQUEDA 4: Buscar tags EXACTOS que buscamos")
    print("=" * 80)

    # Buscar us-gaap:Assets exacto
    print("\nBuscando us-gaap:Assets exacto...")
    assets_exact = root.xpath(".//*[local-name()='Assets']")
    print(f"Total encontrados: {len(assets_exact)}")

    if assets_exact:
        print("\nPrimeros 5:")
        for i, elem in enumerate(assets_exact[:5], 1):
            context = elem.get('contextRef', 'NO CONTEXT')
            value = elem.text.strip() if elem.text else "N/A"
            print(f"  {i}. Context: {context}")
            print(f"     Value: {value}")

    # Buscar us-gaap:StockholdersEquity exacto
    print("\nBuscando us-gaap:StockholdersEquity exacto...")
    equity_exact = root.xpath(".//*[local-name()='StockholdersEquity']")
    print(f"Total encontrados: {len(equity_exact)}")

    if equity_exact:
        print("\nPrimeros 5:")
        for i, elem in enumerate(equity_exact[:5], 1):
            context = elem.get('contextRef', 'NO CONTEXT')
            value = elem.text.strip() if elem.text else "N/A"
            print(f"  {i}. Context: {context}")
            print(f"     Value: {value}")

    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_deep_diagnostic()
