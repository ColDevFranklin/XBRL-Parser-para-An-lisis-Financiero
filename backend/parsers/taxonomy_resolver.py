"""
Taxonomy Resolver - Sprint 3 Refinamiento 2

Resuelve conceptos contables abstractos a tags XBRL específicos.

Problema:
- Apple usa: us-gaap:NetIncomeLoss
- Otra empresa: us-gaap:ProfitLoss
- Otra empresa: us-gaap:NetIncome

Solución:
- Mapping layer con primary + aliases
- Búsqueda en orden de prioridad
- Fallback graceful si ninguno existe

Author: @franklin
Sprint: 3 - Taxonomy Mapping Layer
"""

import json
from pathlib import Path
from typing import Optional, Dict, List
from lxml import etree


class TaxonomyResolver:
    """
    Resuelve conceptos contables a tags XBRL específicos del documento.

    Usage:
        resolver = TaxonomyResolver()

        # Buscar NetIncome en el XBRL tree
        tag = resolver.resolve("NetIncome", xbrl_tree)
        # Returns: "NetIncomeLoss" (sin namespace prefix)

        # Si ningún alias existe
        tag = resolver.resolve("NonExistentConcept", xbrl_tree)
        # Raises: ValueError
    """

    def __init__(self, taxonomy_path: Optional[str] = None):
        """
        Args:
            taxonomy_path: Ruta al taxonomy_map.json
                          (default: backend/config/taxonomy_map.json)
        """
        if taxonomy_path is None:
            # Auto-detect path relativo a este archivo
            current_dir = Path(__file__).parent
            taxonomy_path = current_dir.parent / "config" / "taxonomy_map.json"

        self.taxonomy_path = Path(taxonomy_path)
        self.taxonomy_map = self._load_taxonomy()

    def _load_taxonomy(self) -> Dict:
        """
        Carga el taxonomy map desde JSON.

        Returns:
            Dict con estructura:
            {
                "NetIncome": {
                    "primary": "NetIncomeLoss",
                    "aliases": ["ProfitLoss", ...],
                    ...
                }
            }

        Raises:
            FileNotFoundError: Si taxonomy_map.json no existe
            json.JSONDecodeError: Si JSON inválido
        """
        if not self.taxonomy_path.exists():
            raise FileNotFoundError(
                f"Taxonomy map not found: {self.taxonomy_path}\n"
                f"Expected location: backend/config/taxonomy_map.json"
            )

        with open(self.taxonomy_path, 'r') as f:
            taxonomy = json.load(f)

        print(f"✓ Taxonomy map loaded: {len(taxonomy)} concepts")
        return taxonomy

    def resolve(
        self,
        concept: str,
        xbrl_tree: etree._ElementTree,
        namespace: str = "us-gaap"
    ) -> str:
        """
        Resuelve un concepto contable a un tag XBRL existente en el documento.

        Búsqueda en orden:
        1. Tag primario (e.g., "NetIncomeLoss")
        2. Aliases en orden de prioridad
        3. Raise ValueError si ninguno existe

        Args:
            concept: Concepto contable (e.g., "NetIncome", "Equity")
            xbrl_tree: Árbol XBRL parseado
            namespace: Namespace prefix (default: "us-gaap")

        Returns:
            Tag name sin namespace (e.g., "NetIncomeLoss")

        Raises:
            ValueError: Si concepto no existe en taxonomy_map
            ValueError: Si ningún tag existe en el documento XBRL

        Example:
            >>> resolver = TaxonomyResolver()
            >>> tag = resolver.resolve("NetIncome", tree)
            >>> print(tag)
            "NetIncomeLoss"

            >>> # Usar en xpath
            >>> xpath = f".//*[local-name()='{tag}']"
        """
        # 1. Validar que concepto existe en taxonomy
        if concept not in self.taxonomy_map:
            available = list(self.taxonomy_map.keys())
            raise ValueError(
                f"Concept '{concept}' not found in taxonomy map.\n"
                f"Available concepts: {available}"
            )

        concept_def = self.taxonomy_map[concept]
        primary = concept_def["primary"]
        aliases = concept_def.get("aliases", [])

        # 2. Construir lista de candidatos (primary first)
        candidates = [primary] + aliases

        # 3. Buscar en orden hasta encontrar el primero que existe
        root = xbrl_tree.getroot()

        for tag_name in candidates:
            # Buscar sin namespace (más robusto)
            xpath = f".//*[local-name()='{tag_name}']"
            elements = root.xpath(xpath)

            if elements:
                # Tag encontrado en documento
                return tag_name

        # 4. Ningún tag encontrado → Error
        raise ValueError(
            f"Concept '{concept}' not found in XBRL document.\n"
            f"Tried tags: {candidates}\n"
            f"Tip: Check if company uses different taxonomy or extension tags."
        )

    def resolve_all(
        self,
        concepts: List[str],
        xbrl_tree: etree._ElementTree,
        namespace: str = "us-gaap"
    ) -> Dict[str, Optional[str]]:
        """
        Resuelve múltiples conceptos de una vez.

        Args:
            concepts: Lista de conceptos (e.g., ["NetIncome", "Equity"])
            xbrl_tree: Árbol XBRL
            namespace: Namespace prefix

        Returns:
            Dict: {concept: resolved_tag or None}

        Example:
            >>> tags = resolver.resolve_all(
            ...     ["NetIncome", "Equity", "Revenue"],
            ...     tree
            ... )
            >>> print(tags)
            {
                "NetIncome": "NetIncomeLoss",
                "Equity": "StockholdersEquity",
                "Revenue": "Revenues"
            }
        """
        results = {}

        for concept in concepts:
            try:
                tag = self.resolve(concept, xbrl_tree, namespace)
                results[concept] = tag
            except ValueError:
                # Concepto no encontrado → None
                results[concept] = None

        return results

    def get_concept_info(self, concept: str) -> Dict:
        """
        Obtiene metadata de un concepto.

        Args:
            concept: Nombre del concepto

        Returns:
            Dict con primary, aliases, description, etc.

        Raises:
            ValueError: Si concepto no existe
        """
        if concept not in self.taxonomy_map:
            raise ValueError(f"Concept '{concept}' not in taxonomy map")

        return self.taxonomy_map[concept]

    def list_concepts(self) -> List[str]:
        """
        Lista todos los conceptos disponibles.

        Returns:
            Lista de nombres de conceptos
        """
        return list(self.taxonomy_map.keys())


# ============================================================================
# TESTING STANDALONE
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TAXONOMY RESOLVER - STANDALONE TEST")
    print("=" * 60)

    from backend.parsers.xbrl_parser import XBRLParser

    # Test 1: Load taxonomy
    print("\n--- TEST 1: Load Taxonomy ---")
    try:
        resolver = TaxonomyResolver()
        print(f"✓ Taxonomy loaded with {len(resolver.list_concepts())} concepts")
        print(f"  Concepts: {resolver.list_concepts()}")
    except Exception as e:
        print(f"✗ Error: {e}")
        exit(1)

    # Test 2: Resolve concepts for Apple
    print("\n--- TEST 2: Resolve Apple XBRL ---")
    parser = XBRLParser("data/apple_10k_xbrl.xml")
    parser.load()

    test_concepts = ["NetIncome", "Equity", "Assets", "Revenue"]

    for concept in test_concepts:
        try:
            tag = resolver.resolve(concept, parser.tree)
            print(f"✓ {concept} → {tag}")
        except ValueError as e:
            print(f"✗ {concept} → NOT FOUND")
            print(f"  Error: {e}")

    # Test 3: Resolve all
    print("\n--- TEST 3: Resolve All Concepts ---")
    all_tags = resolver.resolve_all(test_concepts, parser.tree)

    found = sum(1 for v in all_tags.values() if v is not None)
    print(f"✓ Resolved {found}/{len(test_concepts)} concepts")

    for concept, tag in all_tags.items():
        status = "✓" if tag else "✗"
        print(f"  {status} {concept}: {tag}")

    # Test 4: Get concept info
    print("\n--- TEST 4: Concept Metadata ---")
    info = resolver.get_concept_info("NetIncome")
    print(f"NetIncome metadata:")
    print(f"  Primary: {info['primary']}")
    print(f"  Aliases: {info['aliases']}")
    print(f"  Description: {info['description']}")

    print("\n" + "=" * 60)
    print("✅ TAXONOMY RESOLVER TESTS COMPLETE")
    print("=" * 60)
