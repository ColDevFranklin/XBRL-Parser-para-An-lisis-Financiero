"""
Context Manager para filtrar contextos XBRL relevantes con soporte multi-year.

Problema: Un 10-K contiene múltiples contextos:
- Años comparativos (2025, 2024, 2023)
- Segmentos (por país, producto)
- Escenarios (ajustes, reclasificaciones)
- Períodos quarterly vs anuales

Solución Sprint 2: Identificar el contexto consolidado del año fiscal más reciente.
Solución Time-Series: Identificar TODOS los años fiscales disponibles (3-5 años).

Author: @franklin
Sprint: 2 - Context Management
Sprint: Pre-Sprint 3 - Time-Series Analysis
Sprint: 3 Paso 3.2 - BRK.A Fix (DocumentPeriodEndDate)
"""

from lxml import etree
from datetime import date, datetime
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Gestiona la identificación de contextos XBRL relevantes con soporte multi-year.

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

        # Time-Series: Multi-year support (NUEVO)
        self.fiscal_years: List[int] = []
        self.contexts_by_year: Dict[int, Dict] = {}
        self._multiyear_initialized = False

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
        Identifica el año fiscal más reciente usando DocumentPeriodEndDate.

        CAMBIO SPRINT 3 PASO 3.2: Usa DocumentPeriodEndDate como source of truth
        en lugar de asumir que el segundo instant es el correcto.

        Esto maneja correctamente:
        - 10-K anuales (ej: Apple 2025-09-27)
        - 10-Q trimestrales (ej: Berkshire 2025-09-30)
        - Empresas con múltiples filing dates
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

        # OPCIÓN 2 (Fallback): Buscar instant más reciente consolidado
        logger.warning("DocumentPeriodEndDate not found, using instant fallback")

        instant_dates = []
        contexts = self.root.findall('.//xbrli:context', self.NS)

        for ctx in contexts:
            # Ignorar contextos con segmentos
            if ctx.find('.//xbrli:segment', self.NS) is not None:
                continue

            # Buscar <instant> (Balance Sheet date)
            instant = ctx.find('.//xbrli:instant', self.NS)
            if instant is not None:
                ctx_date = datetime.strptime(instant.text, '%Y-%m-%d').date()
                instant_dates.append(ctx_date)

        if not instant_dates:
            raise ValueError("No consolidated contexts with <instant> found")

        # Tomar el más reciente
        instant_dates.sort(reverse=True)
        self._fiscal_year_end = instant_dates[0]
        self._fiscal_year = self._fiscal_year_end.year

        logger.info(
            f"fiscal_period_identified: year={self._fiscal_year}, "
            f"year_end={self._fiscal_year_end} (from instant fallback)"
        )

    def _initialize_multiyear(self) -> None:
        """
        NUEVO: Inicializa detección multi-year (lazy loading).

        Identifica TODOS los años fiscales en el XBRL (hasta 5 años).
        Solo se ejecuta cuando se llama get_available_years() o
        get_balance_context(year=X).
        """
        if self._multiyear_initialized:
            return

        # Step 1: Buscar TODOS los contextos instant consolidados
        instant_contexts = self._find_all_instant_contexts()

        if not instant_contexts:
            logger.warning("No instant contexts found for multi-year")
            self._multiyear_initialized = True
            return

        # Step 2: Agrupar por año fiscal
        years_data = {}

        for ctx_id, instant_date in instant_contexts:
            year = instant_date.year

            if year not in years_data:
                years_data[year] = {
                    'year': year,
                    'balance_context': ctx_id,
                    'balance_date': instant_date,
                    'income_context': None,
                    'duration_period': None
                }

        # Step 3: Buscar duration contexts para cada año
        for year in years_data.keys():
            duration_ctx = self._find_duration_context_for_year(year)
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
        NUEVO: Busca TODOS los contextos instant consolidados (year-end dates).

        FILTRADO: Elimina filing dates (instant más reciente).
        Alineado con lógica Sprint 2 en _identify_fiscal_period().

        Returns:
            List de (context_id, instant_date) ordenados descendente
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
                ctx_date = datetime.strptime(instant.text, '%Y-%m-%d').date()
                instant_contexts.append((ctx.get('id'), ctx_date))

        # Ordenar por fecha descendente
        instant_contexts.sort(key=lambda x: x[1], reverse=True)

        # CRÍTICO: Filtrar filing date (primer instant)
        if len(instant_contexts) > 1:
            logger.debug(
                f"filing_date_filtered: excluded={instant_contexts[0][1]}, "
                f"first_valid={instant_contexts[1][1]}"
            )
            return instant_contexts[1:]  # Excluir filing date

        return instant_contexts  # Edge case: solo 1 instant

    def _find_duration_context_for_year(
        self,
        fiscal_year: int
    ) -> Optional[Tuple[str, date, date]]:
        """
        NUEVO: Busca duration context anual O trimestral para un año específico.

        CAMBIO SPRINT 3 PASO 3.2: Soporta 10-Q trimestrales además de 10-K anuales

        Args:
            fiscal_year: Año fiscal a buscar

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

            # Verificar si es periodo para este año
            if end_date.year == fiscal_year:
                duration = (end_date - start_date).days

                # NUEVO: Aceptar trimestral (80-100 días) O anual (350-370 días)
                # Quarterly: ~90 días (ejemplo: 2025-07-01 a 2025-09-30)
                # Annual: ~365 días (ejemplo: 2024-10-01 a 2025-09-27)
                if (80 <= duration <= 100) or (350 <= duration <= 370):
                    candidates.append((ctx.get('id'), start_date, end_date, duration))

        if not candidates:
            return None

        # Prioridad: Anual > Trimestral
        # Si hay contexto anual, usarlo; sino, usar trimestral
        annual = [c for c in candidates if c[3] >= 350]
        quarterly = [c for c in candidates if c[3] < 100]

        if annual:
            # Tomar el más cercano a 365 días
            annual.sort(key=lambda x: abs(x[3] - 365))
            return annual[0][:3]  # (ctx_id, start, end)
        elif quarterly:
            # Tomar el más reciente (último trimestre)
            quarterly.sort(key=lambda x: x[2], reverse=True)  # Ordenar por end_date
            return quarterly[0][:3]

        return None

    def get_balance_context(self, year: Optional[int] = None) -> str:
        """
        Devuelve el contextID para Balance Sheet (punto en el tiempo).

        Reglas:
        - Debe tener <instant> con fecha = fiscal_year_end
        - NO debe tener <segment> (datos consolidados)

        Args:
            year: Año fiscal específico, o None para más reciente (NUEVO)

        Returns:
            str: Context ID (e.g., 'c-20')
        """
        # Sprint 2 behavior: sin year param
        if year is None:
            if self._balance_context is not None:
                return self._balance_context

            target_date = self.fiscal_year_end
            contexts = self.root.findall('.//xbrli:context', self.NS)

            for ctx in contexts:
                # Filtro 1: Sin segmentos
                if ctx.find('.//xbrli:segment', self.NS) is not None:
                    continue

                # Filtro 2: Fecha exacta
                instant = ctx.find('.//xbrli:instant', self.NS)
                if instant is not None:
                    ctx_date = datetime.strptime(instant.text, '%Y-%m-%d').date()

                    if ctx_date == target_date:
                        self._balance_context = ctx.get('id')
                        logger.info(f"balance_context_found: context_id={self._balance_context}")
                        return self._balance_context

            raise ValueError(f"No balance context found for {target_date}")

        # Time-Series behavior: con year param (NUEVO)
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

            return ctx

    def get_income_context(self, year: Optional[int] = None) -> str:
        """
        Devuelve el contextID para Income Statement (periodo anual o trimestral).

        Reglas:
        - Debe tener <duration> con endDate = fiscal_year_end
        - startDate debe ser ~1 año antes (350-370 días) O ~1 trimestre (80-100 días)
        - NO debe tener <segment>
        - PRIORIDAD: Anual > Trimestral

        Args:
            year: Año fiscal específico, o None para más reciente (NUEVO)

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
                # Filtro 1: Sin segmentos
                if ctx.find('.//xbrli:segment', self.NS) is not None:
                    continue

                # Filtro 2: Duration con endDate correcto
                period = ctx.find('.//xbrli:period', self.NS)
                if period is None:
                    continue

                end_date_elem = period.find('xbrli:endDate', self.NS)
                if end_date_elem is None:
                    continue

                end_date = datetime.strptime(end_date_elem.text, '%Y-%m-%d').date()

                if end_date == target_end:
                    # Verificar que sea periodo anual O trimestral
                    start_date_elem = period.find('xbrli:startDate', self.NS)
                    if start_date_elem is not None:
                        start_date = datetime.strptime(
                            start_date_elem.text, '%Y-%m-%d'
                        ).date()

                        days = (end_date - start_date).days

                        # Periodo anual: 350-370 días
                        if 350 <= days <= 370:
                            candidates_annual.append((ctx.get('id'), days))
                        # NUEVO: Periodo trimestral: 80-100 días (10-Q)
                        elif 80 <= days <= 100:
                            candidates_quarterly.append((ctx.get('id'), days))

            # Prioridad: Anual > Trimestral
            if candidates_annual:
                # Si hay múltiples, elegir el más cercano a 365 días
                candidates_annual.sort(key=lambda x: abs(x[1] - 365))
                self._income_context = candidates_annual[0][0]

                logger.info(
                    f"income_context_found: context_id={self._income_context}, "
                    f"duration_days={candidates_annual[0][1]} (annual)"
                )
                return self._income_context

            elif candidates_quarterly:
                # Usar trimestral como fallback
                candidates_quarterly.sort(key=lambda x: abs(x[1] - 90))
                self._income_context = candidates_quarterly[0][0]

                logger.info(
                    f"income_context_found: context_id={self._income_context}, "
                    f"duration_days={candidates_quarterly[0][1]} (quarterly)"
                )
                return self._income_context

            else:
                raise ValueError(f"No income context found for {target_end}")

        # Time-Series behavior: con year param (NUEVO)
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
        """
        Verifica si un contexto es de tipo <instant>.

        Args:
            context_id: ID del contexto a verificar

        Returns:
            bool: True si tiene <instant>
        """
        ctx = self.root.find(f".//xbrli:context[@id='{context_id}']", self.NS)

        if ctx is None:
            return False

        return ctx.find('.//xbrli:instant', self.NS) is not None

    def is_duration_context(self, context_id: str) -> bool:
        """
        Verifica si un contexto es de tipo <duration>.

        Args:
            context_id: ID del contexto a verificar

        Returns:
            bool: True si tiene <startDate> y <endDate>
        """
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
        """
        Devuelve IDs de todos los contextos consolidados (sin segmentos).

        Útil para debugging.

        Returns:
            List[str]: Lista de context IDs
        """
        consolidated = []
        contexts = self.root.findall('.//xbrli:context', self.NS)

        for ctx in contexts:
            if ctx.find('.//xbrli:segment', self.NS) is None:
                consolidated.append(ctx.get('id'))

        return consolidated

    # ========================================================================
    # NUEVOS MÉTODOS: Time-Series Support
    # ========================================================================

    def get_available_years(self) -> List[int]:
        """
        NUEVO: Retorna lista de años fiscales disponibles.

        Returns:
            List[int] en orden descendente [2025, 2024, 2023]
        """
        self._initialize_multiyear()
        return self.fiscal_years.copy()

    def get_year_summary(self, year: int) -> Dict:
        """
        NUEVO: Retorna resumen de contextos para un año específico.

        Args:
            year: Año fiscal

        Returns:
            {
                'year': 2025,
                'balance_context': 'c-20',
                'balance_date': date(2025, 9, 27),
                'income_context': 'c-1',
                'duration_period': (date(...), date(...))
            }
        """
        self._initialize_multiyear()

        if year not in self.contexts_by_year:
            raise ValueError(f"Year {year} not available")

        return self.contexts_by_year[year].copy()
