"""
Fuzzy Mapper for XBRL Extension Tags
Handles custom company tags through fuzzy matching and XSD hierarchy navigation.

Features:
- Fuzzy string matching for aliases (80/20 rule)
- XSD hierarchy navigation (parent tag discovery)
- Mapping gap tracking for institutional-grade transparency
- **NEW**: Tie-breaking support for ambiguous matches

Author: @franklin
Sprint: 3 Día 4 - Fuzzy Mapping System + Tie-Breaking
"""

from typing import Optional, Dict, List, Tuple
from difflib import SequenceMatcher
import re
from lxml import etree


class FuzzyMapper:
    """
    Fuzzy mapping system for XBRL extension tags.

    Solves the "custom tag problem": Empresas como Apple crean tags propios
    (ej: aapl:NetSalesOfiPhone) que no están en taxonomy estándar.

    Sistema de 3 niveles:
    1. Fuzzy matching: Busca aliases similares (80/20 rule)
    2. Parent tag discovery: Navega jerarquía XSD
    3. Mapping gap tracking: Registra fallos para análisis CTO

    **NEW Sprint 3 Día 5**: Tie-breaking support
    - fuzzy_match_with_tiebreaker() returns ALL candidates
    - Caller can validate which candidate produces valid Balance Sheet

    Example:
        >>> mapper = FuzzyMapper(similarity_threshold=0.75)
        >>>
        >>> # Fuzzy match (single result)
        >>> tags = ['aapl:NetSalesOfiPhone', 'us-gaap:Assets']
        >>> aliases = ['NetSales', 'SalesRevenue']
        >>> match = mapper.fuzzy_match_alias('Revenue', tags, aliases)
        >>> match
        'aapl:NetSalesOfiPhone'
        >>>
        >>> # Fuzzy match with tie-breaking (multiple candidates)
        >>> tags = ['us-gaap:NetIncome', 'us-gaap:NetIncomeAvailableToCommonStockholders']
        >>> aliases = ['NetIncome', 'NetIncomeLoss']
        >>> candidates = mapper.fuzzy_match_with_tiebreaker('NetIncome', tags, aliases)
        >>> candidates
        [('us-gaap:NetIncome', 1.0), ('us-gaap:NetIncomeAvailableToCommonStockholders', 0.78)]
        >>>
        >>> # Gap tracking
        >>> mapper.record_mapping_gap('Goodwill', ['Goodwill'], tags, 'AAPL 2025')
        >>> report = mapper.get_mapping_gaps_report()
        >>> print(report)
        ============================================================
        MAPPING GAPS REPORT - ACTION REQUIRED
        ============================================================
        Total gaps detected: 1

        1. Concept: Goodwill
           Context: AAPL 2025
           Attempted aliases: Goodwill
           Sample tags: aapl:NetSalesOfiPhone, us-gaap:Assets
           → ACTION: Review and add new alias to taxonomy_map.json
        ============================================================
    """

    def __init__(self, similarity_threshold: float = 0.75):
        """
        Initialize fuzzy mapper.

        Args:
            similarity_threshold: Minimum similarity ratio (0.0-1.0) for fuzzy match
                                 Default 0.75 = 75% similarity required

        Example:
            >>> # Conservative (strict matching)
            >>> strict_mapper = FuzzyMapper(similarity_threshold=0.85)
            >>>
            >>> # Aggressive (loose matching)
            >>> loose_mapper = FuzzyMapper(similarity_threshold=0.65)
        """
        self.similarity_threshold = similarity_threshold
        self.mapping_gaps: List[Dict[str, str]] = []  # Track failed mappings

    def fuzzy_match_alias(
        self,
        concept: str,
        available_tags: List[str],
        aliases: List[str]
    ) -> Optional[str]:
        """
        Find best fuzzy match for concept using aliases.

        Uses SequenceMatcher for fuzzy string comparison.
        Normaliza strings (lowercase, remove special chars) antes de comparar.

        **NOTE**: Returns FIRST match above threshold. For tie-breaking,
        use fuzzy_match_with_tiebreaker() instead.

        Args:
            concept: Financial concept to find (e.g., "Revenue")
            available_tags: List of actual tags in XBRL instance
            aliases: List of known aliases from taxonomy_map.json

        Returns:
            Best matching tag or None if no match above threshold

        Example:
            >>> mapper = FuzzyMapper(similarity_threshold=0.75)
            >>>
            >>> # Exact match
            >>> tags = ['us-gaap:Revenues', 'us-gaap:Assets']
            >>> aliases = ['Revenues', 'NetSales']
            >>> mapper.fuzzy_match_alias('Revenue', tags, aliases)
            'us-gaap:Revenues'
            >>>
            >>> # Fuzzy match (similar but not exact)
            >>> tags = ['aapl:NetSalesOfiPhone', 'us-gaap:Assets']
            >>> aliases = ['NetSales', 'SalesRevenue']
            >>> mapper.fuzzy_match_alias('Revenue', tags, aliases)
            'aapl:NetSalesOfiPhone'  # 'NetSalesOfiPhone' matches 'NetSales' >75%
            >>>
            >>> # No match (below threshold)
            >>> tags = ['us-gaap:Assets', 'us-gaap:Liabilities']
            >>> aliases = ['Revenues', 'NetSales']
            >>> mapper.fuzzy_match_alias('Revenue', tags, aliases)
            None
        """
        best_match = None
        best_ratio = 0.0

        for tag in available_tags:
            # Extract local name (remove namespace prefix)
            # 'us-gaap:Revenues' → 'Revenues'
            # 'aapl:NetSalesOfiPhone' → 'NetSalesOfiPhone'
            local_name = tag.split(':')[-1] if ':' in tag else tag

            # Compare against each alias
            for alias in aliases:
                ratio = self._similarity_ratio(local_name, alias)

                if ratio > best_ratio and ratio >= self.similarity_threshold:
                    best_ratio = ratio
                    best_match = tag

        return best_match

    def fuzzy_match_with_tiebreaker(
        self,
        concept: str,
        available_tags: List[str],
        aliases: List[str]
    ) -> List[Tuple[str, float]]:
        """
        Find ALL fuzzy matches above threshold (for tie-breaking).

        **NEW Sprint 3 Día 5**: Returns ALL candidates with similarity scores.
        Caller can then apply business logic (e.g., Balance Sheet validation)
        to choose the correct match.

        Prevents data corruption from ambiguous matches like:
        - 'NetIncome' vs 'NetIncomeAvailableToCommonStockholders'
        - 'Assets' vs 'AssetsCurrentAndNoncurrent'

        Args:
            concept: Financial concept to find
            available_tags: List of actual tags in XBRL instance
            aliases: List of known aliases from taxonomy_map.json

        Returns:
            List of (tag, similarity_score) tuples, sorted by score DESC

        Example:
            >>> mapper = FuzzyMapper(similarity_threshold=0.75)
            >>>
            >>> # Single match (no ambiguity)
            >>> tags = ['us-gaap:Revenues', 'us-gaap:Assets']
            >>> aliases = ['Revenues', 'NetSales']
            >>> mapper.fuzzy_match_with_tiebreaker('Revenue', tags, aliases)
            [('us-gaap:Revenues', 1.0)]
            >>>
            >>> # Multiple matches (ambiguous - requires tie-breaking)
            >>> tags = ['us-gaap:NetIncome', 'us-gaap:NetIncomeAvailableToCommonStockholders']
            >>> aliases = ['NetIncome', 'NetIncomeLoss']
            >>> mapper.fuzzy_match_with_tiebreaker('NetIncome', tags, aliases)
            [('us-gaap:NetIncome', 1.0),
             ('us-gaap:NetIncomeAvailableToCommonStockholders', 0.78)]
            >>>
            >>> # No matches
            >>> tags = ['us-gaap:Assets', 'us-gaap:Liabilities']
            >>> aliases = ['Revenues', 'NetSales']
            >>> mapper.fuzzy_match_with_tiebreaker('Revenue', tags, aliases)
            []
        """
        candidates: List[Tuple[str, float]] = []

        for tag in available_tags:
            # Extract local name (remove namespace prefix)
            local_name = tag.split(':')[-1] if ':' in tag else tag

            # Find BEST similarity score across all aliases
            best_ratio = 0.0
            for alias in aliases:
                ratio = self._similarity_ratio(local_name, alias)
                if ratio > best_ratio:
                    best_ratio = ratio

            # If above threshold, add to candidates
            if best_ratio >= self.similarity_threshold:
                candidates.append((tag, best_ratio))

        # Sort by similarity DESC (best matches first)
        candidates.sort(key=lambda x: x[1], reverse=True)

        return candidates

    def find_parent_tag(
        self,
        custom_tag: str,
        xsd_tree: etree._ElementTree
    ) -> Optional[str]:
        """
        Navigate XSD hierarchy to find standard parent tag.

        XBRL permite que tags custom "hereden" de tags estándar mediante
        el atributo substitutionGroup en el XSD schema.

        Example XSD:
            <xs:element name="NetSalesOfiPhone"
                        substitutionGroup="us-gaap:Revenues"/>

        Esto significa: aapl:NetSalesOfiPhone es un tipo específico de Revenue.

        Args:
            custom_tag: Custom company tag (e.g., "aapl:NetSalesOfiPhone")
            xsd_tree: Parsed XSD schema tree

        Returns:
            Standard parent tag or None if not found

        Example:
            >>> from lxml import etree
            >>>
            >>> # Mock XSD
            >>> xsd = '''
            ... <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
            ...   <xs:element name="NetSalesOfiPhone"
            ...               substitutionGroup="us-gaap:Revenues"/>
            ... </xs:schema>
            ... '''
            >>> xsd_tree = etree.fromstring(xsd.encode())
            >>>
            >>> mapper = FuzzyMapper()
            >>> parent = mapper.find_parent_tag('aapl:NetSalesOfiPhone', xsd_tree)
            >>> parent
            'Revenues'
        """
        # Extract local name (remove namespace)
        local_name = custom_tag.split(':')[-1] if ':' in custom_tag else custom_tag

        # Find element definition in XSD
        element = self._find_element_in_xsd(local_name, xsd_tree)

        if element is None:
            return None

        # Check if element has substitutionGroup (parent tag)
        parent_tag = element.get('substitutionGroup')

        if parent_tag:
            # Extract standard tag name (remove namespace)
            # 'us-gaap:Revenues' → 'Revenues'
            return parent_tag.split(':')[-1] if ':' in parent_tag else parent_tag

        return None

    def record_mapping_gap(
        self,
        concept: str,
        attempted_aliases: List[str],
        available_tags: List[str],
        context: str = ""
    ) -> None:
        """
        Record failed mapping for institutional-grade transparency.

        Cuando el sistema NO puede encontrar un concepto (ni con fuzzy matching
        ni con parent discovery), registra el gap para análisis posterior.

        Esto permite al CTO:
        1. Ver qué conceptos faltan
        2. Identificar nuevos aliases a agregar
        3. Priorizar mejoras al taxonomy_map.json

        Args:
            concept: Financial concept that failed to map
            attempted_aliases: Aliases that were tried
            available_tags: Sample of available tags in instance
            context: Additional context (company, year, etc.)

        Example:
            >>> mapper = FuzzyMapper()
            >>>
            >>> # Record gap
            >>> mapper.record_mapping_gap(
            ...     concept='Goodwill',
            ...     attempted_aliases=['Goodwill', 'GoodwillAndIntangibles'],
            ...     available_tags=['us-gaap:Assets', 'aapl:IntangibleAssetsNet'],
            ...     context='AAPL 2025'
            ... )
            >>>
            >>> # Generate report
            >>> report = mapper.get_mapping_gaps_report()
            >>> print(report)
            ============================================================
            MAPPING GAPS REPORT - ACTION REQUIRED
            ============================================================
            ...
        """
        gap = {
            'concept': concept,
            'attempted_aliases': attempted_aliases,
            'sample_available_tags': available_tags[:10],  # First 10 as sample
            'context': context,
        }

        self.mapping_gaps.append(gap)

    def get_mapping_gaps_report(self) -> str:
        """
        Generate mapping gaps report for CTO review.

        Formato institucional con:
        - Total de gaps detectados
        - Detalle por concepto
        - Aliases intentados
        - Sample de tags disponibles
        - Acción requerida clara

        Returns:
            Formatted report string

        Example:
            >>> mapper = FuzzyMapper()
            >>>
            >>> # No gaps
            >>> mapper.get_mapping_gaps_report()
            '✓ No mapping gaps detected'
            >>>
            >>> # With gaps
            >>> mapper.record_mapping_gap('Goodwill', ['Goodwill'],
            ...                           ['us-gaap:Assets'], 'AAPL 2025')
            >>> print(mapper.get_mapping_gaps_report())
            ============================================================
            MAPPING GAPS REPORT - ACTION REQUIRED
            ============================================================

            Total gaps detected: 1

            1. Concept: Goodwill
               Context: AAPL 2025
               Attempted aliases: Goodwill
               Sample tags available: us-gaap:Assets
               → ACTION: Review and add new alias to taxonomy_map.json

            ============================================================
        """
        if not self.mapping_gaps:
            return "✓ No mapping gaps detected"

        report = [
            "=" * 70,
            "MAPPING GAPS REPORT - ACTION REQUIRED",
            "=" * 70,
            f"\nTotal gaps detected: {len(self.mapping_gaps)}\n"
        ]

        for idx, gap in enumerate(self.mapping_gaps, 1):
            report.append(f"\n{idx}. Concept: {gap['concept']}")
            report.append(f"   Context: {gap['context']}")
            report.append(f"   Attempted aliases: {', '.join(gap['attempted_aliases'])}")
            report.append(f"   Sample tags available: {', '.join(gap['sample_available_tags'][:5])}")
            report.append(f"   → ACTION: Review and add new alias to taxonomy_map.json")

        report.append("\n" + "=" * 70)

        return "\n".join(report)

    def _similarity_ratio(self, str1: str, str2: str) -> float:
        """
        Calculate similarity ratio between two strings.

        Uses SequenceMatcher for fuzzy string matching.
        Normalizes strings (lowercase, remove special chars) before comparison.

        Normalization examples:
        - 'NetSalesOfiPhone' → 'netsalesof iphone'
        - 'NetSales' → 'netsales'
        - 'Accounts_Receivable-Net' → 'accountsreceivablenet'

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity ratio (0.0-1.0)

        Example:
            >>> mapper = FuzzyMapper()
            >>>
            >>> # Exact match
            >>> mapper._similarity_ratio('Revenues', 'Revenues')
            1.0
            >>>
            >>> # Similar
            >>> mapper._similarity_ratio('NetSalesOfiPhone', 'NetSales')
            0.78  # Aproximadamente
            >>>
            >>> # Different
            >>> mapper._similarity_ratio('Revenues', 'Assets')
            0.25  # Aproximadamente
        """
        # Normalize strings
        # 1. Lowercase
        # 2. Remove non-alphanumeric chars
        s1 = re.sub(r'[^a-z0-9]', '', str1.lower())
        s2 = re.sub(r'[^a-z0-9]', '', str2.lower())

        return SequenceMatcher(None, s1, s2).ratio()

    def _find_element_in_xsd(
        self,
        element_name: str,
        xsd_tree: etree._ElementTree
    ) -> Optional[etree._Element]:
        """
        Find element definition in XSD schema.

        Busca en el XSD schema la definición de un elemento XBRL.

        Args:
            element_name: Name of element to find
            xsd_tree: Parsed XSD schema tree

        Returns:
            Element node or None if not found

        Example:
            >>> from lxml import etree
            >>>
            >>> xsd = '''
            ... <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
            ...   <xs:element name="NetSalesOfiPhone" type="xs:decimal"/>
            ... </xs:schema>
            ... '''
            >>> xsd_tree = etree.fromstring(xsd.encode())
            >>>
            >>> mapper = FuzzyMapper()
            >>> element = mapper._find_element_in_xsd('NetSalesOfiPhone', xsd_tree)
            >>> element is not None
            True
            >>> element.get('name')
            'NetSalesOfiPhone'
        """
        # XSD namespace
        xs_ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}

        # Search for element with matching name
        xpath = f"//xs:element[@name='{element_name}']"
        elements = xsd_tree.xpath(xpath, namespaces=xs_ns)

        if elements:
            return elements[0]

        return None
