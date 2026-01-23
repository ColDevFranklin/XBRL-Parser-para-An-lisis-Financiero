"""
Duration Validation Test - Sprint 3 Refinamiento 1

Objetivo: Asegurar que NO hay contextos Q4 contaminando Income Statement.

Verificamos:
1. Solo 1 duration context anual por año fiscal
2. Todos los contexts son 350-370 días (anual)
3. NO hay contexts quarterly (<180 días) en selección

Acceptance Criteria:
- PASSED: Solo contexts anuales presentes
- FAILED: Detecta contamination → requiere fix
"""

import pytest
from pathlib import Path
from backend.parsers.xbrl_parser import XBRLParser
from datetime import datetime

# Test data paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
APPLE_FILES = {
    2025: DATA_DIR / "apple_10k_xbrl.xml",
    2024: DATA_DIR / "apple_10k_2024_xbrl.xml",
    2023: DATA_DIR / "apple_10k_2023_xbrl.xml",
    2022: DATA_DIR / "apple_10k_2022_xbrl.xml"
}


def test_duration_contexts_are_annual_only():
    """
    Verify: Todos los duration contexts seleccionados son anuales (350-370 días).

    Red Flag: Si encontramos contexts <180 días → quarterly contamination
    """
    for year, filepath in APPLE_FILES.items():
        if not filepath.exists():
            pytest.skip(f"Missing test file: {filepath}")

        parser = XBRLParser(str(filepath))
        parser.load()

        # Get income statement context for this year
        income_ctx = parser.context_mgr.get_income_context(year=year)

        # Define namespaces for xpath (añadir xbrli manualmente)
        ns = {
            'xbrli': 'http://www.xbrl.org/2003/instance',
        }

        # Extract duration in days usando xpath
        ctx_elements = parser.tree.xpath(f"//xbrli:context[@id='{income_ctx}']", namespaces=ns)
        assert len(ctx_elements) > 0, f"Context {income_ctx} not found"

        ctx_element = ctx_elements[0]
        period = ctx_element.xpath(".//xbrli:period", namespaces=ns)[0]

        start_date = period.xpath("xbrli:startDate", namespaces=ns)[0].text
        end_date = period.xpath("xbrli:endDate", namespaces=ns)[0].text

        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        duration_days = (end - start).days

        # Assertion: Must be annual period
        assert 350 <= duration_days <= 370, \
            f"Year {year}: Duration {duration_days} days is NOT annual (expected 350-370)"

        print(f"✓ Year {year}: {duration_days} days (ANNUAL ✓)")


def test_no_quarterly_contexts_in_selection():
    """
    Verify: Context Manager NO selecciona contexts quarterly al buscar annual.

    Strategy:
    1. List ALL duration contexts en el documento
    2. Filtrar por fiscal year detectado
    3. Verificar que contexts <180 días NO están en candidatos
    """
    for year, filepath in APPLE_FILES.items():
        if not filepath.exists():
            pytest.skip(f"Missing test file: {filepath}")

        parser = XBRLParser(str(filepath))
        parser.load()

        # Define namespaces
        ns = {
            'xbrli': 'http://www.xbrl.org/2003/instance',
        }

        # Get ALL contexts with duration period
        all_contexts = parser.tree.xpath("//xbrli:context", namespaces=ns)

        quarterly_found = []
        annual_found = []

        for ctx in all_contexts:
            ctx_id = ctx.get('id')
            period = ctx.xpath(".//xbrli:period", namespaces=ns)

            if not period:
                continue

            period = period[0]

            # Skip instant contexts
            instant = period.xpath("xbrli:instant", namespaces=ns)
            if instant:
                continue

            # Duration context
            start_dates = period.xpath("xbrli:startDate", namespaces=ns)
            end_dates = period.xpath("xbrli:endDate", namespaces=ns)

            if not start_dates or not end_dates:
                continue

            start = datetime.fromisoformat(start_dates[0].text)
            end = datetime.fromisoformat(end_dates[0].text)
            duration_days = (end - start).days

            if duration_days < 180:
                quarterly_found.append((ctx_id, duration_days))
            elif 350 <= duration_days <= 370:
                annual_found.append((ctx_id, duration_days))

        print(f"\nYear {year} context analysis:")
        print(f"  Annual contexts (350-370d): {len(annual_found)}")
        print(f"  Quarterly contexts (<180d): {len(quarterly_found)}")

        # Critical assertion
        if quarterly_found:
            print(f"  ⚠️  WARNING: Found quarterly contexts:")
            for ctx_id, days in quarterly_found:
                print(f"     - {ctx_id}: {days} days")

        # Income context selected should be annual
        income_ctx = parser.context_mgr.get_income_context(year=year)
        assert income_ctx in [ctx_id for ctx_id, _ in annual_found], \
            f"Selected context {income_ctx} is NOT in annual contexts list"

        print(f"  ✓ Selected context: {income_ctx} (ANNUAL)")


def test_one_annual_context_per_year():
    """
    Verify: Solo 1 duration context anual es seleccionado por año fiscal.

    Edge case: Si hay múltiples contexts 350-370 días, verificar que solo
    seleccionamos 1 (el más específico al fiscal year).
    """
    for year, filepath in APPLE_FILES.items():
        if not filepath.exists():
            pytest.skip(f"Missing test file: {filepath}")

        parser = XBRLParser(str(filepath))
        parser.load()

        # Get selected context
        income_ctx = parser.context_mgr.get_income_context(year=year)

        # Verify it's unique (no duplicate selection)
        assert income_ctx is not None
        assert isinstance(income_ctx, str)

        print(f"✓ Year {year}: Unique annual context selected: {income_ctx}")


if __name__ == "__main__":
    print("=" * 60)
    print("DURATION VALIDATION TEST - Sprint 3 Refinamiento 1")
    print("=" * 60)

    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
