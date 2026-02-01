"""
Context Manager para filtrar contextos XBRL relevantes con soporte multi-year.

Problema: Un 10-K contiene múltiples contextos:
- Años comparativos (2025, 2024, 2023)
- Segmentos (por país, producto)
- Escenarios (ajustes, reclasificaciones)
- Períodos quarterly vs anuales

Solución Sprint 2: Identificar el contexto consolidado del año fiscal más reciente.
Solución Time-Series: Identificar TODOS los años fiscales disponibles (3-5 años).

FIX SPRINT 6 - ISSUE MSFT:
- Corregido: Detección de fiscal year end usando contextos en lugar de filing date
- Nuevo: Validación de balance sheet contexts con criterio de "riqueza de datos"
- Nuevo: Logging detallado para debugging
- Nuevo: Validation layer para detectar contextos incorrectos

Author: @franklin
Sprint: 2 - Context Management
Sprint: Pre-Sprint 3 - Time-Series Analysis
Sprint: 3 Paso 3.2 - BRK.A Fix (DocumentPeriodEndDate)
Sprint: 6 - MSFT Assets/Equity Fix
"""

from lxml import etree
from datetime import date, datetime
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Gestiona la identificación de contextos XBRL relevantes con soporte multi-year.

    ARQUITECTURA ROBUSTA (Sprint 6):
    - Validación de "riqueza de datos" en contextos
    - Detección automática de fiscal year-end correcto
    - Logging detallado para debugging
    - Fallback hierarchy para casos edge

    Uso básico (Sprint 2 - backwards compatible):
        mgr = ContextManager(xbrl_tree)
        balance_ctx = mgr.get_balance_context()  # Año más reciente
        income_ctx = mgr.get_income_context()

    Uso multi-year (Time-Series):
        mgr = ContextManager(xbrl_tree)
        years = mgr.get_available_years()  # [2025, 2024, 2023]
        ctx_2024 = mgr.get_balance_context(year=2024)
        ctx_2023 = mgr.get_income_context(year=2023)
    """

    # Namespaces XBRL estándar
    NS = {
        'xbrli': 'http://www.xbrl.org/2003/instance',
        'xbrldi': 'http://xbrl.org/2006/xbrldi',
        'dei': 'http://xbrl.sec.gov/dei/2023'
    }

    # NUEVO: Criterios de validación para contextos
    MIN_ELEMENTS_FOR_VALID_BALANCE_CONTEXT = 10  # Mínimo elementos para considerar contexto válido

    def __init__(self, tree: etree._ElementTree):
        """
        Args:
            tree: Árbol XML parseado con lxml
        """
        self.tree = tree
        self.root = tree.getroot()

        # Sprint 2: Cachear año más reciente (backwards compatibility)
        self._fiscal_year = None
        self._fiscal_year_end = None
        self._balance_context = None
        self._income_context = None

        # Time-Series: Multi-year support
        self.fiscal_years: List[int] = []
        self.contexts_by_year: Dict[int, Dict] = {}
        self._multiyear_initialized = False

        # NUEVO Sprint 6: Context validation cache
        self._context_element_counts: Dict[str, int] = {}

        logger.info("context_manager_initialized")

    @property
    def fiscal_year(self) -> int:
        """
        Año fiscal más reciente en el documento.

        Returns:
            int: Año fiscal (e.g., 2025)
        """
        if self._fiscal_year is None:
            self._identify_fiscal_period()
        return self._fiscal_year

    @property
    def fiscal_year_end(self) -> date:
        """
        Fecha de cierre del año fiscal más reciente.

        Returns:
            date: Fecha de cierre (e.g., 2025-09-27)
        """
        if self._fiscal_year_end is None:
            self._identify_fiscal_period()
        return self._fiscal_year_end

    def _identify_fiscal_period(self) -> None:
        """
        Identifica el año fiscal más reciente usando estrategia multi-level.

        FIX SPRINT 6: Usa estrategia robusta en lugar de asumir filing date.

        STRATEGY:
        1. Buscar DocumentPeriodEndDate (más confiable)
        2. Buscar instant context con más elementos (balance sheet real)
        3. Fallback a instant más reciente

        Esto maneja correctamente:
        - 10-K anuales (ej: Apple 2025-09-27)
        - 10-Q trimestrales (ej: Berkshire 2025-09-30)
        - MSFT con múltiples fiscal year ends
        """
        # OPCIÓN 1: Buscar DocumentPeriodEndDate (más confiable)
        doc_period_end = self.root.find('.//dei:DocumentPeriodEndDate', self.NS)

        if doc_period_end is not None:
            self._fiscal_year_end = datetime.strptime(
                doc_period_end.text, '%Y-%m-%d'
            ).date()
            self._fiscal_year = self._fiscal_year_end.year

            logger.info(
                f"fiscal_period_identified: year={self._fiscal_year}, "
                f"year_end={self._fiscal_year_end} (from DocumentPeriodEndDate)"
            )
            return

        # OPCIÓN 2 (NUEVO Sprint 6): Buscar instant context con MÁS DATOS
        logger.warning("DocumentPeriodEndDate not found, using data-rich instant strategy")

        instant_contexts = self._find_all_instant_contexts_with_counts()

        if not instant_contexts:
            raise ValueError("No consolidated contexts with <instant> found")

        # CRÍTICO: Usar el contexto con MÁS ELEMENTOS (balance sheet real)
        # En lugar de solo el más reciente
        instant_contexts.sort(key=lambda x: x[2], reverse=True)  # Ordenar por element count

        richest_context = instant_contexts[0]
        self._fiscal_year_end = richest_context[1]
        self._fiscal_year = self._fiscal_year_end.year

        logger.info(
            f"fiscal_period_identified: year={self._fiscal_year}, "
            f"year_end={self._fiscal_year_end}, "
            f"elements={richest_context[2]} (from data-rich instant)"
        )

    def _find_all_instant_contexts_with_counts(self) -> List[Tuple[str, date, int]]:
        """
        NUEVO Sprint 6: Busca instant contexts Y cuenta elementos en cada uno.

        Esto permite identificar el "balance sheet real" vs "filing dates" o "segment dates".

        Returns:
            List de (context_id, instant_date, element_count)
        """
        instant_contexts = []
        contexts = self.root.findall('.//xbrli:context', self.NS)

        for ctx in contexts:
            # Filtrar solo consolidados (sin segmentos)
            if ctx.find('.//xbrli:segment', self.NS) is not None:
                continue

            # Extraer fecha instant
            instant = ctx.find('.//xbrli:instant', self.NS)
            if instant is not None:
                ctx_id = ctx.get('id')
                ctx_date = datetime.strptime(instant.text, '%Y-%m-%d').date()

                # Contar elementos en este contexto
                element_count = self._count_elements_in_context(ctx_id)

                instant_contexts.append((ctx_id, ctx_date, element_count))

        return instant_contexts

    def _count_elements_in_context(self, context_id: str) -> int:
        """
        NUEVO Sprint 6: Cuenta cuántos elementos XBRL usan este contexto.

        Contextos "ricos" (50+ elementos) = Balance sheets reales
        Contextos "pobres" (1-5 elementos) = Filing dates, segments, etc.

        Args:
            context_id: Context ID a analizar

        Returns:
            int: Número de elementos usando este contexto
        """
        if context_id in self._context_element_counts:
            return self._context_element_counts[context_id]

        elements = self.root.xpath(f".//*[@contextRef='{context_id}']")
        count = len(elements)

        self._context_element_counts[context_id] = count
        return count

    def _initialize_multiyear(self) -> None:
        """
        Inicializa detección multi-year (lazy loading).

        FIX SPRINT 6: Usa validación de "riqueza de datos" para seleccionar
        contextos correctos.

        Identifica TODOS los años fiscales en el XBRL (hasta 5 años).
        """
        if self._multiyear_initialized:
            return

        # Step 1: Buscar TODOS los contextos instant consolidados CON COUNTS
        instant_contexts = self._find_all_instant_contexts_with_counts()

        if not instant_contexts:
            logger.warning("No instant contexts found for multi-year")
            self._multiyear_initialized = True
            return

        # Step 2: Agrupar por año fiscal
        # NUEVO: Solo incluir contextos con suficientes elementos
        years_data = {}

        for ctx_id, instant_date, element_count in instant_contexts:
            # VALIDACIÓN: Solo considerar contextos "ricos"
            if element_count < self.MIN_ELEMENTS_FOR_VALID_BALANCE_CONTEXT:
                logger.debug(
                    f"context_skipped: id={ctx_id}, date={instant_date}, "
                    f"elements={element_count} (too few elements)"
                )
                continue

            year = instant_date.year

            # Si ya tenemos un contexto para este año, usar el más rico
            if year in years_data:
                existing_count = self._count_elements_in_context(
                    years_data[year]['balance_context']
                )

                if element_count > existing_count:
                    logger.debug(
                        f"context_replaced: year={year}, "
                        f"old_elements={existing_count}, new_elements={element_count}"
                    )
                    years_data[year] = {
                        'year': year,
                        'balance_context': ctx_id,
                        'balance_date': instant_date,
                        'income_context': None,
                        'duration_period': None
                    }
            else:
                years_data[year] = {
                    'year': year,
                    'balance_context': ctx_id,
                    'balance_date': instant_date,
                    'income_context': None,
                    'duration_period': None
                }

                logger.debug(
                    f"context_added: year={year}, date={instant_date}, "
                    f"elements={element_count}"
                )

        # Step 3: Buscar duration contexts para cada año
        for year in years_data.keys():
            duration_ctx = self._find_duration_context_for_year(
                year,
                years_data[year]['balance_date']
            )
            if duration_ctx:
                ctx_id, start_date, end_date = duration_ctx
                years_data[year]['income_context'] = ctx_id
                years_data[year]['duration_period'] = (start_date, end_date)

        # Step 4: Ordenar años descendente y almacenar
        sorted_years = sorted(years_data.keys(), reverse=True)

        self.fiscal_years = sorted_years
        self.contexts_by_year = years_data
        self._multiyear_initialized = True

        logger.info(
            f"multiyear_initialized: years={sorted_years}, "
            f"count={len(sorted_years)}"
        )

    def _find_all_instant_contexts(self) -> List[Tuple[str, date]]:
        """
        DEPRECATED: Usar _find_all_instant_contexts_with_counts() en su lugar.

        Mantenido por backwards compatibility.
        """
        contexts_with_counts = self._find_all_instant_contexts_with_counts()
        return [(ctx_id, ctx_date) for ctx_id, ctx_date, _ in contexts_with_counts]

    def _find_duration_context_for_year(
        self,
        fiscal_year: int,
        fiscal_year_end: date
    ) -> Optional[Tuple[str, date, date]]:
        """
        Busca duration context anual O trimestral para un año específico.

        FIX SPRINT 6: Ahora recibe fiscal_year_end explícito para validar
        que el duration context termina en la fecha correcta.

        Args:
            fiscal_year: Año fiscal a buscar
            fiscal_year_end: Fecha exacta de cierre del año fiscal

        Returns:
            (context_id, start_date, end_date) o None
        """
        contexts = self.root.findall('.//xbrli:context', self.NS)

        candidates = []

        for ctx in contexts:
            # Filtrar solo consolidados
            if ctx.find('.//xbrli:segment', self.NS) is not None:
                continue

            # Buscar duration period
            period = ctx.find('.//xbrli:period', self.NS)
            if period is None:
                continue

            start_elem = period.find('xbrli:startDate', self.NS)
            end_elem = period.find('xbrli:endDate', self.NS)

            if start_elem is None or end_elem is None:
                continue

            start_date = datetime.strptime(start_elem.text, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_elem.text, '%Y-%m-%d').date()

            # FIX CRÍTICO: Validar que termina en fiscal_year_end EXACTO
            # En lugar de solo validar año
            if end_date == fiscal_year_end:
                duration = (end_date - start_date).days

                # Aceptar trimestral (80-100 días) O anual (350-370 días)
                if (80 <= duration <= 100) or (350 <= duration <= 370):
                    candidates.append((ctx.get('id'), start_date, end_date, duration))

        if not candidates:
            # Fallback: Buscar por año si no hay match exacto
            logger.warning(
                f"No duration context with exact end date {fiscal_year_end}, "
                f"falling back to year match"
            )
            return self._find_duration_context_for_year_fallback(fiscal_year)

        # Prioridad: Anual > Trimestral
        annual = [c for c in candidates if c[3] >= 350]
        quarterly = [c for c in candidates if c[3] < 100]

        if annual:
            annual.sort(key=lambda x: abs(x[3] - 365))
            return annual[0][:3]
        elif quarterly:
            quarterly.sort(key=lambda x: x[2], reverse=True)
            return quarterly[0][:3]

        return None

    def _find_duration_context_for_year_fallback(
        self,
        fiscal_year: int
    ) -> Optional[Tuple[str, date, date]]:
        """
        NUEVO Sprint 6: Fallback para buscar duration context por año.

        Usado cuando no hay match exacto con fiscal_year_end.

        Args:
            fiscal_year: Año fiscal a buscar

        Returns:
            (context_id, start_date, end_date) o None
        """
        contexts = self.root.findall('.//xbrli:context', self.NS)

        candidates = []

        for ctx in contexts:
            if ctx.find('.//xbrli:segment', self.NS) is not None:
                continue

            period = ctx.find('.//xbrli:period', self.NS)
            if period is None:
                continue

            start_elem = period.find('xbrli:startDate', self.NS)
            end_elem = period.find('xbrli:endDate', self.NS)

            if start_elem is None or end_elem is None:
                continue

            start_date = datetime.strptime(start_elem.text, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_elem.text, '%Y-%m-%d').date()

            # Buscar por año
            if end_date.year == fiscal_year:
                duration = (end_date - start_date).days

                if (80 <= duration <= 100) or (350 <= duration <= 370):
                    candidates.append((ctx.get('id'), start_date, end_date, duration))

        if not candidates:
            return None

        # Prioridad: Anual > Trimestral
        annual = [c for c in candidates if c[3] >= 350]
        quarterly = [c for c in candidates if c[3] < 100]

        if annual:
            annual.sort(key=lambda x: abs(x[3] - 365))
            return annual[0][:3]
        elif quarterly:
            quarterly.sort(key=lambda x: x[2], reverse=True)
            return quarterly[0][:3]

        return None

    def get_balance_context(self, year: Optional[int] = None) -> str:
        """
        Devuelve el contextID para Balance Sheet (punto en el tiempo).

        FIX SPRINT 6: Usa validación de riqueza de datos.

        Args:
            year: Año fiscal específico, o None para más reciente

        Returns:
            str: Context ID (e.g., 'c-20')
        """
        # Sprint 2 behavior: sin year param
        if year is None:
            if self._balance_context is not None:
                return self._balance_context

            target_date = self.fiscal_year_end

            # NUEVO: Buscar contexto con validación
            candidate_contexts = self._find_all_instant_contexts_with_counts()

            # Filtrar por fecha
            matching = [c for c in candidate_contexts if c[1] == target_date]

            if not matching:
                raise ValueError(f"No balance context found for {target_date}")

            # Tomar el más rico en datos
            matching.sort(key=lambda x: x[2], reverse=True)
            self._balance_context = matching[0][0]

            logger.info(
                f"balance_context_found: context_id={self._balance_context}, "
                f"elements={matching[0][2]}"
            )
            return self._balance_context

        # Time-Series behavior: con year param
        else:
            self._initialize_multiyear()

            if year not in self.contexts_by_year:
                raise ValueError(
                    f"Year {year} not available. "
                    f"Available: {self.fiscal_years}"
                )

            ctx = self.contexts_by_year[year]['balance_context']

            if ctx is None:
                raise ValueError(f"Balance context not found for {year}")

            # VALIDACIÓN: Verificar que tiene suficientes elementos
            count = self._count_elements_in_context(ctx)
            if count < self.MIN_ELEMENTS_FOR_VALID_BALANCE_CONTEXT:
                logger.warning(
                    f"balance_context_low_quality: year={year}, "
                    f"context={ctx}, elements={count}"
                )

            return ctx

    def get_income_context(self, year: Optional[int] = None) -> str:
        """
        Devuelve el contextID para Income Statement (periodo anual o trimestral).

        Args:
            year: Año fiscal específico, o None para más reciente

        Returns:
            str: Context ID (e.g., 'c-1')
        """
        # Sprint 2 behavior: sin year param
        if year is None:
            if self._income_context is not None:
                return self._income_context

            target_end = self.fiscal_year_end
            contexts = self.root.findall('.//xbrli:context', self.NS)

            candidates_annual = []
            candidates_quarterly = []

            for ctx in contexts:
                if ctx.find('.//xbrli:segment', self.NS) is not None:
                    continue

                period = ctx.find('.//xbrli:period', self.NS)
                if period is None:
                    continue

                end_date_elem = period.find('xbrli:endDate', self.NS)
                if end_date_elem is None:
                    continue

                end_date = datetime.strptime(end_date_elem.text, '%Y-%m-%d').date()

                if end_date == target_end:
                    start_date_elem = period.find('xbrli:startDate', self.NS)
                    if start_date_elem is not None:
                        start_date = datetime.strptime(
                            start_date_elem.text, '%Y-%m-%d'
                        ).date()

                        days = (end_date - start_date).days

                        if 350 <= days <= 370:
                            candidates_annual.append((ctx.get('id'), days))
                        elif 80 <= days <= 100:
                            candidates_quarterly.append((ctx.get('id'), days))

            if candidates_annual:
                candidates_annual.sort(key=lambda x: abs(x[1] - 365))
                self._income_context = candidates_annual[0][0]

                logger.info(
                    f"income_context_found: context_id={self._income_context}, "
                    f"duration_days={candidates_annual[0][1]} (annual)"
                )
                return self._income_context

            elif candidates_quarterly:
                candidates_quarterly.sort(key=lambda x: abs(x[1] - 90))
                self._income_context = candidates_quarterly[0][0]

                logger.info(
                    f"income_context_found: context_id={self._income_context}, "
                    f"duration_days={candidates_quarterly[0][1]} (quarterly)"
                )
                return self._income_context

            else:
                raise ValueError(f"No income context found for {target_end}")

        # Time-Series behavior: con year param
        else:
            self._initialize_multiyear()

            if year not in self.contexts_by_year:
                raise ValueError(
                    f"Year {year} not available. "
                    f"Available: {self.fiscal_years}"
                )

            ctx = self.contexts_by_year[year]['income_context']

            if ctx is None:
                raise ValueError(f"Income context not found for {year}")

            return ctx

    def is_instant_context(self, context_id: str) -> bool:
        """Verifica si un contexto es de tipo <instant>."""
        ctx = self.root.find(f".//xbrli:context[@id='{context_id}']", self.NS)

        if ctx is None:
            return False

        return ctx.find('.//xbrli:instant', self.NS) is not None

    def is_duration_context(self, context_id: str) -> bool:
        """Verifica si un contexto es de tipo <duration>."""
        ctx = self.root.find(f".//xbrli:context[@id='{context_id}']", self.NS)

        if ctx is None:
            return False

        period = ctx.find('.//xbrli:period', self.NS)
        if period is None:
            return False

        has_start = period.find('xbrli:startDate', self.NS) is not None
        has_end = period.find('xbrli:endDate', self.NS) is not None

        return has_start and has_end

    def get_all_consolidated_contexts(self) -> List[str]:
        """Devuelve IDs de todos los contextos consolidados (sin segmentos)."""
        consolidated = []
        contexts = self.root.findall('.//xbrli:context', self.NS)

        for ctx in contexts:
            if ctx.find('.//xbrli:segment', self.NS) is None:
                consolidated.append(ctx.get('id'))

        return consolidated

    # ========================================================================
    # Time-Series Support
    # ========================================================================

    def get_available_years(self) -> List[int]:
        """Retorna lista de años fiscales disponibles."""
        self._initialize_multiyear()
        return self.fiscal_years.copy()

    def get_year_summary(self, year: int) -> Dict:
        """Retorna resumen de contextos para un año específico."""
        self._initialize_multiyear()

        if year not in self.contexts_by_year:
            raise ValueError(f"Year {year} not available")

        return self.contexts_by_year[year].copy()

    # ========================================================================
    # NUEVO Sprint 6: Validation & Debugging Tools
    # ========================================================================

    def validate_context_quality(self, context_id: str) -> Dict:
        """
        NUEVO Sprint 6: Valida la "calidad" de un contexto.

        Retorna métricas para debugging:
        - Número de elementos
        - Tipo de contexto (instant/duration)
        - Tiene segmentos?
        - Fecha del contexto

        Args:
            context_id: Context ID a validar

        Returns:
            Dict con métricas de calidad
        """
        element_count = self._count_elements_in_context(context_id)
        is_instant = self.is_instant_context(context_id)
        is_duration = self.is_duration_context(context_id)

        ctx = self.root.find(f".//xbrli:context[@id='{context_id}']", self.NS)
        has_segment = ctx.find('.//xbrli:segment', self.NS) is not None if ctx else None

        # Extraer fecha
        context_date = None
        if ctx is not None:
            if is_instant:
                instant_elem = ctx.find('.//xbrli:instant', self.NS)
                if instant_elem is not None:
                    context_date = instant_elem.text
            elif is_duration:
                end_elem = ctx.find('.//xbrli:endDate', self.NS)
                if end_elem is not None:
                    context_date = end_elem.text

        quality = {
            'context_id': context_id,
            'element_count': element_count,
            'is_instant': is_instant,
            'is_duration': is_duration,
            'has_segment': has_segment,
            'context_date': context_date,
            'quality_score': 'HIGH' if element_count >= 50 else 'MEDIUM' if element_count >= 10 else 'LOW'
        }

        return quality

    def debug_year_contexts(self, year: int) -> Dict:
        """
        NUEVO Sprint 6: Debug tool para analizar contextos de un año.

        Args:
            year: Año fiscal a analizar

        Returns:
            Dict con análisis completo
        """
        self._initialize_multiyear()

        if year not in self.contexts_by_year:
            return {
                'year': year,
                'available': False,
                'error': f'Year not available. Available: {self.fiscal_years}'
            }

        year_data = self.contexts_by_year[year]

        balance_ctx = year_data['balance_context']
        income_ctx = year_data['income_context']

        balance_quality = self.validate_context_quality(balance_ctx) if balance_ctx else None
        income_quality = self.validate_context_quality(income_ctx) if income_ctx else None

        return {
            'year': year,
            'available': True,
            'balance_context': balance_ctx,
            'balance_quality': balance_quality,
            'income_context': income_ctx,
            'income_quality': income_quality,
            'balance_date': str(year_data['balance_date']),
            'duration_period': str(year_data['duration_period']) if year_data['duration_period'] else None
        }
