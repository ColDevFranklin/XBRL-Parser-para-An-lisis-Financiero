"""
TEST DE DEMOSTRACIÓN: Audit Trail para Fuzzy Mapper

Este test muestra cómo funcionará el sistema de audit trail ANTES de
modificar el código de producción.

Objetivo:
- Demostrar estructura de FuzzyMatchResult
- Validar metadatos de auditoría
- Verificar backward compatibility
- Mostrar reportes CTO-friendly

Sprint: 3 Día 5 - Audit Trail Micro-Task
Author: @franklin
"""

import pytest
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
import time


# ============================================================================
# MOCK IMPLEMENTATION - Lo que SERÁ fuzzy_mapper.py después del cambio
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


class MockFuzzyMapper:
    """
    Mock del FuzzyMapper CON audit trail.

    Simula el comportamiento que tendrá fuzzy_mapper.py después del cambio.
    """

    def __init__(self, similarity_threshold: float = 0.75):
        self.similarity_threshold = similarity_threshold
        self.mapping_gaps: List[Dict[str, str]] = []

    def fuzzy_match_alias(
        self,
        concept: str,
        available_tags: List[str],
        aliases: List[str]
    ) -> Optional[FuzzyMatchResult]:
        """
        Fuzzy matching CON audit trail.

        CAMBIO: Retorna FuzzyMatchResult en lugar de str
        """
        start_time = time.time()

        # Simular fuzzy matching (versión simplificada)
        best_match = None
        best_ratio = 0.0
        best_alias = None

        for tag in available_tags:
            local_name = tag.split(':')[-1] if ':' in tag else tag

            for alias in aliases:
                # Simulación de similarity (en real usa SequenceMatcher)
                ratio = self._mock_similarity(local_name, alias)

                if ratio > best_ratio and ratio >= self.similarity_threshold:
                    best_ratio = ratio
                    best_match = tag
                    best_alias = alias

        processing_time = (time.time() - start_time) * 1000  # ms

        if best_match:
            # Crear resultado CON audit trail
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
        Fuzzy matching con tie-breaking CON audit trail.

        CAMBIO: Retorna List[FuzzyMatchResult] en lugar de List[Tuple[str, float]]
        """
        start_time = time.time()
        candidates: List[FuzzyMatchResult] = []

        for tag in available_tags:
            local_name = tag.split(':')[-1] if ':' in tag else tag

            best_ratio = 0.0
            best_alias = None

            for alias in aliases:
                ratio = self._mock_similarity(local_name, alias)
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_alias = alias

            if best_ratio >= self.similarity_threshold:
                processing_time = (time.time() - start_time) * 1000

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
                        'candidate_rank': len(candidates) + 1
                    }
                )
                candidates.append(result)

        # Sort by similarity DESC
        candidates.sort(key=lambda x: x.audit['similarity_score'], reverse=True)

        # Update ranks after sorting
        for idx, candidate in enumerate(candidates, 1):
            candidate.audit['candidate_rank'] = idx

        return candidates

    def _mock_similarity(self, str1: str, str2: str) -> float:
        """Mock de similarity (versión simplificada)."""
        s1 = str1.lower()
        s2 = str2.lower()

        if s1 == s2:
            return 1.0
        elif s2 in s1 or s1 in s2:
            return 0.85
        elif s1[:3] == s2[:3]:  # Primeros 3 chars iguales
            return 0.70
        else:
            return 0.50

    def _get_confidence_tier(self, score: float) -> str:
        """Determina tier de confianza basado en score."""
        if score >= 0.90:
            return 'high'
        elif score >= 0.75:
            return 'medium'
        else:
            return 'low'


# ============================================================================
# TESTS - Validación del sistema de audit trail
# ============================================================================

class TestFuzzyAuditTrail:
    """Tests del sistema de audit trail."""

    def test_fuzzy_match_returns_result_with_audit(self):
        """
        CORE TEST: fuzzy_match_alias retorna FuzzyMatchResult con audit trail.
        """
        mapper = MockFuzzyMapper(similarity_threshold=0.75)

        tags = ['us-gaap:Revenues', 'us-gaap:Assets']
        aliases = ['Revenues', 'NetSales']

        result = mapper.fuzzy_match_alias('Revenue', tags, aliases)

        # Validar estructura
        assert result is not None
        assert isinstance(result, FuzzyMatchResult)

        # Validar valor
        assert result.value == 'us-gaap:Revenues'

        # Validar audit trail
        assert 'source_concept' in result.audit
        assert result.audit['source_concept'] == 'Revenue'

        assert 'matched_tag' in result.audit
        assert result.audit['matched_tag'] == 'us-gaap:Revenues'

        assert 'similarity_score' in result.audit
        assert result.audit['similarity_score'] == 1.0  # Match exacto

        assert 'confidence_tier' in result.audit
        assert result.audit['confidence_tier'] == 'high'

        assert 'match_method' in result.audit
        assert result.audit['match_method'] == 'fuzzy_alias'

        assert 'validation_equation' in result.audit
        assert 'SequenceMatcher' in result.audit['validation_equation']

        assert 'timestamp' in result.audit
        assert 'processing_time_ms' in result.audit

    def test_backward_compatibility_string_behavior(self):
        """
        CRÍTICO: FuzzyMatchResult actúa como string para backward compatibility.

        Código antiguo que espera str seguirá funcionando:
            tag = mapper.fuzzy_match_alias(...)
            if tag:
                print(tag)  # Debe funcionar
        """
        mapper = MockFuzzyMapper()

        tags = ['us-gaap:Revenues']
        aliases = ['Revenues']

        result = mapper.fuzzy_match_alias('Revenue', tags, aliases)

        # Test 1: str() funciona
        assert str(result) == 'us-gaap:Revenues'

        # Test 2: Comparación con string
        assert result.value == 'us-gaap:Revenues'

        # Test 3: String formatting
        formatted = f"Tag encontrado: {result}"
        assert formatted == "Tag encontrado: us-gaap:Revenues"

        # Test 4: Boolean truthiness
        assert bool(result)  # Result es truthy

    def test_confidence_tiers(self):
        """
        Test de clasificación de confianza.

        - high: score >= 0.90
        - medium: score 0.75-0.89
        - low: score < 0.75
        """
        mapper = MockFuzzyMapper(similarity_threshold=0.60)  # Bajo threshold para testing

        # High confidence (match exacto)
        tags_high = ['us-gaap:Revenues']
        aliases_high = ['Revenues']
        result_high = mapper.fuzzy_match_alias('Revenue', tags_high, aliases_high)
        assert result_high.audit['confidence_tier'] == 'high'
        assert result_high.audit['similarity_score'] >= 0.90

        # Medium confidence (match parcial)
        tags_med = ['us-gaap:RevenuesFromSales']
        aliases_med = ['Revenues']
        result_med = mapper.fuzzy_match_alias('Revenue', tags_med, aliases_med)
        assert result_med.audit['confidence_tier'] == 'medium'
        assert 0.75 <= result_med.audit['similarity_score'] < 0.90

    def test_tiebreaker_returns_multiple_results_with_audit(self):
        """
        Test de tie-breaking con múltiples candidatos CON audit trail.
        """
        mapper = MockFuzzyMapper(similarity_threshold=0.75)

        tags = [
            'us-gaap:NetIncome',
            'us-gaap:NetIncomeAvailableToCommonStockholders',
            'us-gaap:NetIncomeLoss'
        ]
        aliases = ['NetIncome', 'NetIncomeLoss']

        results = mapper.fuzzy_match_with_tiebreaker('NetIncome', tags, aliases)

        # Validar estructura
        assert len(results) >= 2  # Debe haber múltiples candidatos
        assert all(isinstance(r, FuzzyMatchResult) for r in results)

        # Validar ordenamiento DESC por similarity
        scores = [r.audit['similarity_score'] for r in results]
        assert scores == sorted(scores, reverse=True)

        # Validar ranking
        for idx, result in enumerate(results, 1):
            assert result.audit['candidate_rank'] == idx

        # Validar que TODOS tienen audit trail
        for result in results:
            assert 'source_concept' in result.audit
            assert 'similarity_score' in result.audit
            assert 'confidence_tier' in result.audit
            assert 'match_method' in result.audit
            assert result.audit['match_method'] == 'fuzzy_tiebreaker'

    def test_audit_trail_serialization_to_json(self):
        """
        Test de serialización a JSON (para reportes).
        """
        import json

        mapper = MockFuzzyMapper()

        tags = ['us-gaap:Revenues']
        aliases = ['Revenues']

        result = mapper.fuzzy_match_alias('Revenue', tags, aliases)

        # Serializar a dict
        result_dict = result.to_dict()

        # Validar estructura
        assert 'matched_tag' in result_dict
        assert 'source_concept' in result_dict
        assert 'similarity_score' in result_dict

        # Validar que es JSON-serializable
        json_str = json.dumps(result_dict, indent=2)
        assert json_str is not None
        assert 'matched_tag' in json_str

        # Validar que puede deserializarse
        deserialized = json.loads(json_str)
        assert deserialized['matched_tag'] == 'us-gaap:Revenues'

    def test_audit_trail_includes_attempted_aliases(self):
        """
        Test de trazabilidad: registra TODOS los aliases intentados.

        Crítico para debugging: "¿Por qué no matcheó con X alias?"
        """
        mapper = MockFuzzyMapper()

        tags = ['us-gaap:Revenues']
        aliases = ['Revenues', 'NetSales', 'SalesRevenue', 'TotalRevenue']

        result = mapper.fuzzy_match_alias('Revenue', tags, aliases)

        # Validar que registra TODOS los aliases intentados
        assert 'attempted_aliases' in result.audit
        assert result.audit['attempted_aliases'] == aliases

        # Validar que registra el alias que ganó
        assert 'best_alias_used' in result.audit
        assert result.audit['best_alias_used'] in aliases

    def test_audit_trail_includes_performance_metrics(self):
        """
        Test de métricas de performance.

        Útil para optimización: "¿Qué tan rápido fue el matching?"
        """
        mapper = MockFuzzyMapper()

        tags = ['us-gaap:Revenues']
        aliases = ['Revenues']

        result = mapper.fuzzy_match_alias('Revenue', tags, aliases)

        # Validar métricas de performance
        assert 'processing_time_ms' in result.audit
        assert result.audit['processing_time_ms'] >= 0

        assert 'timestamp' in result.audit
        # Validar formato ISO
        timestamp = result.audit['timestamp']
        datetime.fromisoformat(timestamp)  # Debe parsear sin error

    def test_no_match_returns_none(self):
        """
        Test de caso negativo: cuando NO hay match.

        Backward compatibility: debe retornar None (igual que antes).
        """
        mapper = MockFuzzyMapper(similarity_threshold=0.90)  # Threshold alto

        tags = ['us-gaap:Assets']
        aliases = ['Revenues']  # No matchea con Assets

        result = mapper.fuzzy_match_alias('Revenue', tags, aliases)

        assert result is None  # Mismo comportamiento que antes


# ============================================================================
# TEST DE INTEGRACIÓN - Reporte CTO-Friendly
# ============================================================================

class TestAuditReporting:
    """Tests de reportes de auditoría para CTO."""

    def test_generate_audit_report_from_results(self):
        """
        Test de generación de reporte de auditoría.

        Simula cómo el CTO vería los resultados de matching.
        """
        mapper = MockFuzzyMapper()

        # Simular múltiples matches
        concepts = [
            ('Revenue', ['us-gaap:Revenues'], ['Revenues', 'NetSales']),
            ('Assets', ['us-gaap:Assets'], ['Assets', 'TotalAssets']),
            ('NetIncome', ['us-gaap:NetIncome', 'us-gaap:NetIncomeLoss'], ['NetIncome'])
        ]

        audit_log = []

        for concept, tags, aliases in concepts:
            result = mapper.fuzzy_match_alias(concept, tags, aliases)
            if result:
                audit_log.append(result.to_dict())

        # Validar estructura del log
        assert len(audit_log) == 3

        # Generar reporte
        report = self._generate_report(audit_log)

        print("\n" + "="*70)
        print("AUDIT TRAIL REPORT - FUZZY MAPPING")
        print("="*70)
        print(report)
        print("="*70)

        # Validar contenido del reporte
        assert 'Revenue' in report
        assert 'Assets' in report
        assert 'NetIncome' in report
        assert 'HIGH' in report  # Debe mostrar confidence tiers (uppercase en reporte)

    def _generate_report(self, audit_log: List[Dict[str, Any]]) -> str:
        """Helper para generar reporte CTO-friendly."""
        lines = []

        for idx, entry in enumerate(audit_log, 1):
            lines.append(f"\n{idx}. Concept: {entry['source_concept']}")
            lines.append(f"   Matched Tag: {entry['matched_tag']}")
            lines.append(f"   Confidence: {entry['confidence_tier'].upper()} ({entry['similarity_score']:.3f})")
            lines.append(f"   Method: {entry['match_method']}")
            lines.append(f"   Validation: {entry['validation_equation']}")
            lines.append(f"   Processing Time: {entry['processing_time_ms']:.2f} ms")
            lines.append(f"   Attempted Aliases: {', '.join(entry['attempted_aliases'])}")
            lines.append(f"   Best Alias Used: {entry['best_alias_used']}")

        return "\n".join(lines)


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
