"""
Sprint 3 Día 4 - Paso 1: Validar Taxonomy Map Expandido
Test: Verificar que 33 conceptos se cargan correctamente

Ejecutar:
    python3 -m pytest backend/tests/test_taxonomy_33_concepts.py -v
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.parsers.taxonomy_resolver import TaxonomyResolver
import pytest


class TestTaxonomy33Concepts:
    """Validar expansión de 15 a 33 conceptos"""

    @pytest.fixture
    def resolver(self):
        return TaxonomyResolver()

    def test_taxonomy_loads(self, resolver):
        """Taxonomy map se carga sin errores"""
        assert resolver is not None
        concepts = resolver.list_concepts()
        assert len(concepts) > 0

    def test_has_33_concepts(self, resolver):
        """Debe tener exactamente 33 conceptos (sin contar metadata)"""
        concepts = resolver.list_concepts()

        # Filtrar metadata
        real_concepts = [c for c in concepts if not c.startswith('_')]

        print(f"\n✓ Total concepts: {len(real_concepts)}")
        assert len(real_concepts) == 33, f"Expected 33, got {len(real_concepts)}"

    def test_core_15_still_exist(self, resolver):
        """Los 15 conceptos originales siguen existiendo"""
        core_15 = [
            'Assets', 'Liabilities', 'Equity',
            'CurrentAssets', 'CurrentLiabilities',
            'CashAndEquivalents', 'LongTermDebt',
            'Revenue', 'NetIncome',
            'CostOfRevenue', 'GrossProfit', 'OperatingIncome',
            'InterestExpense',
            'OperatingCashFlow', 'CapitalExpenditures'
        ]

        concepts = resolver.list_concepts()

        for concept in core_15:
            assert concept in concepts, f"Core concept missing: {concept}"

        print(f"\n✓ All 15 core concepts present")

    def test_new_18_concepts_exist(self, resolver):
        """Los 18 conceptos nuevos existen"""
        new_18 = [
            'Inventory', 'AccountsReceivable', 'ShortTermDebt',
            'OperatingLeaseLiability', 'Goodwill', 'IntangibleAssets',
            'PropertyPlantEquipment', 'AccumulatedDepreciation',
            'RetainedEarnings', 'TreasuryStock', 'OtherCurrentAssets',
            'ResearchAndDevelopment', 'SellingGeneralAdmin',
            'TaxExpense', 'DepreciationAmortization',
            'NonOperatingIncome', 'AssetImpairment', 'RestructuringCharges'
        ]

        concepts = resolver.list_concepts()
        missing = []

        for concept in new_18:
            if concept not in concepts:
                missing.append(concept)

        if missing:
            print(f"\n✗ Missing concepts: {missing}")
            pytest.fail(f"Missing {len(missing)} new concepts: {missing}")

        print(f"\n✓ All 18 new concepts present")

    def test_concepts_have_primary_tag(self, resolver):
        """Todos los conceptos tienen primary tag definido"""
        concepts = resolver.list_concepts()
        real_concepts = [c for c in concepts if not c.startswith('_')]

        for concept in real_concepts:
            info = resolver.get_concept_info(concept)
            assert 'primary' in info, f"{concept} missing 'primary' tag"
            assert info['primary'], f"{concept} has empty 'primary' tag"

        print(f"\n✓ All {len(real_concepts)} concepts have primary tags")

    def test_concepts_have_aliases(self, resolver):
        """Todos los conceptos tienen aliases (puede ser lista vacía)"""
        concepts = resolver.list_concepts()
        real_concepts = [c for c in concepts if not c.startswith('_')]

        for concept in real_concepts:
            info = resolver.get_concept_info(concept)
            assert 'aliases' in info, f"{concept} missing 'aliases' field"
            assert isinstance(info['aliases'], list), f"{concept} aliases not a list"

        print(f"\n✓ All {len(real_concepts)} concepts have aliases field")

    def test_print_summary(self, resolver):
        """Imprimir resumen de conceptos por categoría"""
        concepts = resolver.list_concepts()
        real_concepts = [c for c in concepts if not c.startswith('_')]

        # Categorizar
        balance_sheet = [
            'Assets', 'Liabilities', 'Equity',
            'CurrentAssets', 'CurrentLiabilities',
            'CashAndEquivalents', 'LongTermDebt', 'ShortTermDebt',
            'Inventory', 'AccountsReceivable',
            'PropertyPlantEquipment', 'AccumulatedDepreciation',
            'Goodwill', 'IntangibleAssets',
            'RetainedEarnings', 'TreasuryStock',
            'OtherCurrentAssets', 'OperatingLeaseLiability'
        ]

        income_statement = [
            'Revenue', 'NetIncome',
            'CostOfRevenue', 'GrossProfit', 'OperatingIncome',
            'ResearchAndDevelopment', 'SellingGeneralAdmin',
            'InterestExpense', 'TaxExpense',
            'DepreciationAmortization', 'NonOperatingIncome',
            'AssetImpairment', 'RestructuringCharges'
        ]

        cash_flow = [
            'OperatingCashFlow', 'CapitalExpenditures'
        ]

        print("\n" + "="*60)
        print("TAXONOMY MAP - 33 CONCEPTS")
        print("="*60)

        print(f"\nBALANCE SHEET: {len(balance_sheet)} concepts")
        for c in balance_sheet:
            status = "✓" if c in concepts else "✗"
            print(f"  {status} {c}")

        print(f"\nINCOME STATEMENT: {len(income_statement)} concepts")
        for c in income_statement:
            status = "✓" if c in concepts else "✗"
            print(f"  {status} {c}")

        print(f"\nCASH FLOW: {len(cash_flow)} concepts")
        for c in cash_flow:
            status = "✓" if c in concepts else "✗"
            print(f"  {status} {c}")

        print("\n" + "="*60)
        print(f"TOTAL: {len(real_concepts)} concepts")
        print("="*60)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
