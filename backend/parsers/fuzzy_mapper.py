"""
Fuzzy Mapper for XBRL Extension Tags
Handles custom company tags through fuzzy matching and XSD hierarchy navigation.

Features:
- Fuzzy string matching for aliases (80/20 rule)
- XSD hierarchy navigation (parent tag discovery)
- Mapping gap tracking for institutional-grade transparency
- **NEW**: Tie-breaking support for ambiguous matches
- **NEW Sprint 3 Día 5**: Audit trail with complete metadata

Author: @franklin
Sprint: 3 Día 5 - Audit Trail Implementation
"""

from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from difflib import SequenceMatcher
from datetime import datetime
import time
import re
from lxml import etree


# ============================================================================
# AUDIT TRAIL - Sprint 3 Día 5
# ============================================================================

@dataclass
class FuzzyMatchResult:
    """
    Resultado de fuzzy matching con audit trail completo.

    Attributes:
        value: Tag XBRL mapeado (ej: 'us-gaap:Revenues')
        audit: Metadatos de trazabilidad

    Features:
        - Backward compatible (actúa como string cuando se necesita)
        - Serializable a JSON
        - CTO-friendly reporting

    Example:
        >>> result = FuzzyMatchResult(
        ...     value='us-gaap:Revenues',
        ...     audit={
        ...         'source_concept': 'Revenue',
        ...         'similarity_score': 0.92,
        ...         'confidence_tier': 'high'
        ...     }
        ... )
        >>> str(result)
        'us-gaap:Revenues'
        >>> result.audit['confidence_tier']
        'high'
    """
    value: str
    audit: Dict[str, Any]

    def __str__(self) -> str:
        """Backward compatibility: actúa como string."""
        return self.value

    def __repr__(self) -> str:
        """Dev-friendly representation."""
        return f"FuzzyMatchResult(value='{self.value}', confidence={self.audit.get('confidence_tier', 'unknown')})"

    def to_dict(self) -> Dict[str, Any]:
        """Serialización a dict (para JSON reports)."""
        return {
            'matched_tag': self.value,
            **self.audit
        }

    def get_confidence_tier(self) -> str:
        """Helper para acceder al tier de confianza."""
        score = self.audit.get('similarity_score', 0.0)
        if score >= 0.90:
            return 'high'
        elif score >= 0.75:
            return 'medium'
        else:
            return 'low'


# ============================================================================
# FUZZY MAPPER - Main Class
# ============================================================================

class FuzzyMapper:
    """
    Fuzzy mapping system for XBRL extension tags.

    Solves the "custom tag problem": Empresas como Apple crean tags propios
    (ej: aapl:NetSalesOfiPhone) que no están en taxonomy estándar.

    Sistema de 3 niveles:
    1. Fuzzy matching: Busca aliases similares (80/20 rule)
    2. Parent tag discovery: Navega jerarquía XSD
    3. Mapping gap tracking: Registra fallos para análisis CTO

    **NEW Sprint 3 Día 5**: Audit trail support
    - fuzzy_match_alias() returns FuzzyMatchResult with metadata
    - fuzzy_match_with_tiebreaker() returns List[FuzzyMatchResult]
    - Complete traceability for institutional-grade transparency

    Example:
        >>> mapper = FuzzyMapper(similarity_threshold=0.75)
        >>>
        >>> # Fuzzy match with audit trail
        >>> tags = ['aapl:NetSalesOfiPhone', 'us-gaap:Assets']
        >>> aliases = ['NetSales', 'SalesRevenue']
        >>> result = mapper.fuzzy_match_alias('Revenue', tags, aliases)
        >>> result.value
        'aapl:NetSalesOfiPhone'
        >>> result.audit['similarity_score']
        0.85
        >>> result.audit['confidence_tier']
        'medium'
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
    ) -> Optional[FuzzyMatchResult]:
        """
        Find best fuzzy match for concept using aliases WITH AUDIT TRAIL.

        Uses SequenceMatcher for fuzzy string comparison.
        Normaliza strings (lowercase, remove special chars) antes de comparar.

        **CAMBIO Sprint 3 Día 5**: Returns FuzzyMatchResult instead of str
        - Backward compatible via __str__() method
        - Includes complete audit metadata

        Args:
            concept: Financial concept to find (e.g., "Revenue")
            available_tags: List of actual tags in XBRL instance
            aliases: List of known aliases from taxonomy_map.json

        Returns:
            FuzzyMatchResult with value + audit trail, or None if no match

        Example:
            >>> mapper = FuzzyMapper(similarity_threshold=0.75)
            >>>
            >>> # Exact match
            >>> tags = ['us-gaap:Revenues', 'us-gaap:Assets']
            >>> aliases = ['Revenues', 'NetSales']
            >>> result = mapper.fuzzy_match_alias('Revenue', tags, aliases)
            >>> str(result)  # Backward compatible
            'us-gaap:Revenues'
            >>> result.audit['similarity_score']
            1.0
            >>> result.audit['confidence_tier']
            'high'
        """
        start_time = time.perf_counter()

        best_match = None
        best_ratio = 0.0
        best_alias = None

        for tag in available_tags:
            # Extract local name (remove namespace prefix)
            local_name = tag.split(':')[-1] if ':' in tag else tag

            # Compare against each alias
            for alias in aliases:
                ratio = self._similarity_ratio(local_name, alias)

                if ratio > best_ratio and ratio >= self.similarity_threshold:
                    best_ratio = ratio
                    best_match = tag
                    best_alias = alias

        processing_time = (time.perf_counter() - start_time) * 1000  # ms

        if best_match:
            # Create result WITH audit trail
            return FuzzyMatchResult(
                value=best_match,
                audit={
                    'source_concept': concept,
                    'matched_tag': best_match,
                    'similarity_score': round(best_ratio, 3),
                    'confidence_tier': self._get_confidence_tier(best_ratio),
                    'match_method': 'fuzzy_alias',
                    'attempted_aliases': aliases,
                    'best_alias_used': best_alias,
                    'validation_equation': f"SequenceMatcher({best_match.split(':')[-1]}, {best_alias}) = {best_ratio:.3f}",
                    'timestamp': datetime.now().isoformat(),
                    'processing_time_ms': round(processing_time, 2),
                    'threshold_used': self.similarity_threshold
                }
            )

        return None

    def fuzzy_match_with_tiebreaker(
        self,
        concept: str,
        available_tags: List[str],
        aliases: List[str]
    ) -> List[FuzzyMatchResult]:
        """
        Find ALL fuzzy matches above threshold WITH AUDIT TRAIL (for tie-breaking).

        **CAMBIO Sprint 3 Día 5**: Returns List[FuzzyMatchResult] instead of List[Tuple]
        - Each result includes complete audit metadata
        - Backward compatible via value attribute

        Args:
            concept: Financial concept to find
            available_tags: List of actual tags in XBRL instance
            aliases: List of known aliases from taxonomy_map.json

        Returns:
            List of FuzzyMatchResult objects, sorted by similarity DESC

        Example:
            >>> mapper = FuzzyMapper(similarity_threshold=0.75)
            >>>
            >>> # Multiple matches with audit trail
            >>> tags = ['us-gaap:NetIncome', 'us-gaap:NetIncomeAvailableToCommonStockholders']
            >>> aliases = ['NetIncome', 'NetIncomeLoss']
            >>> results = mapper.fuzzy_match_with_tiebreaker('NetIncome', tags, aliases)
            >>> len(results)
            2
            >>> results[0].value
            'us-gaap:NetIncome'
            >>> results[0].audit['similarity_score']
            1.0
            >>> results[0].audit['candidate_rank']
            1
        """
        start_time = time.perf_counter()
        candidates: List[FuzzyMatchResult] = []

        for tag in available_tags:
            # Extract local name (remove namespace prefix)
            local_name = tag.split(':')[-1] if ':' in tag else tag

            # Find BEST similarity score across all aliases
            best_ratio = 0.0
            best_alias = None

            for alias in aliases:
                ratio = self._similarity_ratio(local_name, alias)
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_alias = alias

            # If above threshold, add to candidates WITH audit trail
            if best_ratio >= self.similarity_threshold:
                processing_time = (time.perf_counter() - start_time) * 1000

                result = FuzzyMatchResult(
                    value=tag,
                    audit={
                        'source_concept': concept,
                        'matched_tag': tag,
                        'similarity_score': round(best_ratio, 3),
                        'confidence_tier': self._get_confidence_tier(best_ratio),
                        'match_method': 'fuzzy_tiebreaker',
                        'attempted_aliases': aliases,
                        'best_alias_used': best_alias,
                        'validation_equation': f"SequenceMatcher({local_name}, {best_alias}) = {best_ratio:.3f}",
                        'timestamp': datetime.now().isoformat(),
                        'processing_time_ms': round(processing_time, 2),
                        'threshold_used': self.similarity_threshold,
                        'candidate_rank': len(candidates) + 1  # Temporary rank
                    }
                )
                candidates.append(result)

        # Sort by similarity DESC (best matches first)
        candidates.sort(key=lambda x: x.audit['similarity_score'], reverse=True)

        # Update ranks after sorting
        for idx, candidate in enumerate(candidates, 1):
            candidate.audit['candidate_rank'] = idx

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

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _get_confidence_tier(self, score: float) -> str:
        """
        Determina tier de confianza basado en similarity score.

        Args:
            score: Similarity ratio (0.0-1.0)

        Returns:
            'high' (>= 0.90), 'medium' (0.75-0.89), or 'low' (< 0.75)
        """
        if score >= 0.90:
            return 'high'
        elif score >= 0.75:
            return 'medium'
        else:
            return 'low'

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
