"""
Test Suite - TaxonomyResolver
Sprint 3 - Refinamiento 2: Taxonomy Mapping Layer

Valida:
1. Carga correcta de taxonomy_map.json
2. Resolución de conceptos a tags XBRL
3. Fallback graceful si tag no existe
4. Cross-company compatibility (Apple, Microsoft, Berkshire)
"""

import pytest
from pathlib import Path
from backend.parsers.taxonomy_resolver import TaxonomyResolver
from backend.parsers.xbrl_parser import XBRLParser


DATA_DIR = Path(__file__).parent.parent.parent / "data"


class TestTaxonomyResolver:
    """Test suite para TaxonomyResolver"""

    def test_load_taxonomy_map(self):
        """Verify: taxonomy_map.json se carga correctamente"""
        resolver = TaxonomyResolver()

        # Should have at least 5 core concepts
        concepts = resolver.list_concepts()
        assert len(concepts) >= 5

        # Core concepts must exist
        required = ["NetIncome", "Equity", "Assets", "Revenue"]
        for concept in required:
            assert concept in concepts, f"Missing required concept: {concept}"

    def test_resolve_apple_concepts(self):
        """Verify: Resuelve conceptos para Apple XBRL"""
        filepath = DATA_DIR / "apple_10k_xbrl.xml"
        if not filepath.exists():
            pytest.skip("Apple XBRL file not found")

        parser = XBRLParser(str(filepath))
        parser.load()

        resolver = TaxonomyResolver()

        # Test individual resolution
        tag = resolver.resolve("NetIncome", parser.tree)
        assert tag == "NetIncomeLoss"

        tag = resolver.resolve("Equity", parser.tree)
        assert tag == "StockholdersEquity"

        tag = resolver.resolve("Assets", parser.tree)
        assert tag == "Assets"

    def test_resolve_all_concepts(self):
        """Verify: resolve_all() retorna dict completo"""
        filepath = DATA_DIR / "apple_10k_xbrl.xml"
        if not filepath.exists():
            pytest.skip("Apple XBRL file not found")

        parser = XBRLParser(str(filepath))
        parser.load()

        resolver = TaxonomyResolver()

        concepts = ["NetIncome", "Equity", "Assets", "Revenue"]
        results = resolver.resolve_all(concepts, parser.tree)

        # Should resolve all concepts
        assert len(results) == len(concepts)

        # All should be found (not None)
        for concept in concepts:
            assert results[concept] is not None, f"{concept} not resolved"

    def test_concept_not_in_taxonomy(self):
        """Verify: ValueError si concepto no existe en taxonomy_map"""
        filepath = DATA_DIR / "apple_10k_xbrl.xml"
        if not filepath.exists():
            pytest.skip("Apple XBRL file not found")

        parser = XBRLParser(str(filepath))
        parser.load()

        resolver = TaxonomyResolver()

        # Should raise ValueError for unknown concept
        with pytest.raises(ValueError, match="not found in taxonomy map"):
            resolver.resolve("NonExistentConcept", parser.tree)

    def test_concept_not_in_document(self):
        """Verify: ValueError si ningún alias existe en documento"""
        filepath = DATA_DIR / "apple_10k_xbrl.xml"
        if not filepath.exists():
            pytest.skip("Apple XBRL file not found")

        parser = XBRLParser(str(filepath))
        parser.load()

        resolver = TaxonomyResolver()

        # Add a fake concept to taxonomy for testing
        resolver.taxonomy_map["FakeConcept"] = {
            "primary": "FakeTag",
            "aliases": ["AlsoFakeTag"],
            "description": "Test concept"
        }

        # Should raise ValueError because tag doesn't exist in document
        with pytest.raises(ValueError, match="not found in XBRL document"):
            resolver.resolve("FakeConcept", parser.tree)

    def test_get_concept_info(self):
        """Verify: get_concept_info() retorna metadata completa"""
        resolver = TaxonomyResolver()

        info = resolver.get_concept_info("NetIncome")

        assert "primary" in info
        assert "aliases" in info
        assert "description" in info

        assert info["primary"] == "NetIncomeLoss"
        assert isinstance(info["aliases"], list)
        assert len(info["aliases"]) > 0

    def test_cross_company_compatibility_microsoft(self):
        """Verify: Funciona con Microsoft XBRL (diferentes tags)"""
        filepath = DATA_DIR / "msft_10k_xbrl.xml"
        if not filepath.exists():
            pytest.skip("Microsoft XBRL file not found")

        parser = XBRLParser(str(filepath))
        parser.load()

        resolver = TaxonomyResolver()

        # Should resolve core concepts
        concepts = ["NetIncome", "Equity", "Assets"]
        results = resolver.resolve_all(concepts, parser.tree)

        # At least 2/3 should resolve (tolerance for different taxonomies)
        resolved_count = sum(1 for v in results.values() if v is not None)
        assert resolved_count >= 2, f"Only {resolved_count}/3 concepts resolved for Microsoft"

    def test_cross_company_compatibility_berkshire(self):
        """Verify: Funciona con Berkshire Hathaway XBRL"""
        filepath = DATA_DIR / "brk_10k_xbrl.xml"
        if not filepath.exists():
            pytest.skip("Berkshire XBRL file not found")

        parser = XBRLParser(str(filepath))
        parser.load()

        resolver = TaxonomyResolver()

        # Should resolve core concepts
        concepts = ["NetIncome", "Equity", "Assets"]
        results = resolver.resolve_all(concepts, parser.tree)

        # At least 2/3 should resolve
        resolved_count = sum(1 for v in results.values() if v is not None)
        assert resolved_count >= 2, f"Only {resolved_count}/3 concepts resolved for Berkshire"

    def test_alias_fallback_priority(self):
        """Verify: Busca primary primero, luego aliases en orden"""
        filepath = DATA_DIR / "apple_10k_xbrl.xml"
        if not filepath.exists():
            pytest.skip("Apple XBRL file not found")

        parser = XBRLParser(str(filepath))
        parser.load()

        resolver = TaxonomyResolver()

        # Revenue tiene múltiples aliases
        # Debería encontrar el primary o el primer alias que existe
        tag = resolver.resolve("Revenue", parser.tree)

        # Should be one of the valid aliases
        revenue_def = resolver.get_concept_info("Revenue")
        valid_tags = [revenue_def["primary"]] + revenue_def["aliases"]

        assert tag in valid_tags, f"Resolved tag {tag} not in valid aliases"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
