# backend/engines/context_manager.py

"""
Context Manager para filtrar contextos XBRL relevantes.

Problema: Un 10-K contiene múltiples contextos:
- Años comparativos (2025, 2024, 2023)
- Segmentos (por país, producto)
- Escenarios (ajustes, reclasificaciones)
- Períodos quarterly vs anuales

Solución: Identificar el contexto consolidado del año fiscal más reciente.

Author: @franklin
Sprint: 2 - Métricas
"""

from lxml import etree
from datetime import date, datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Gestiona la identificación de contextos XBRL relevantes.

    Uso:
        mgr = ContextManager(xbrl_tree)
        balance_ctx = mgr.get_balance_context()
        income_ctx = mgr.get_income_context()
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

        # Cachear contextos para performance
        self._all_contexts = None
        self._fiscal_year = None
        self._fiscal_year_end = None
        self._balance_context = None
        self._income_context = None

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
        Identifica el año fiscal más reciente buscando el <instant> más tardío
        en contextos consolidados (sin segmentos).

        CORREGIDO: Ahora busca el segundo <instant> más reciente para evitar
        fechas de filing (10-K se presenta ~2 semanas después del year-end).
        """
        instant_dates = []

        # Buscar todos los contextos consolidados
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

        # Ordenar y tomar el SEGUNDO más reciente
        # (el primero suele ser la fecha de filing, no year-end)
        instant_dates.sort(reverse=True)

        if len(instant_dates) >= 2:
            self._fiscal_year_end = instant_dates[1]
        else:
            self._fiscal_year_end = instant_dates[0]

        self._fiscal_year = self._fiscal_year_end.year

        logger.info(
            "fiscal_period_identified",
            year=self._fiscal_year,
            year_end=str(self._fiscal_year_end)
        )

    def get_balance_context(self) -> str:
        """
        Devuelve el contextID para Balance Sheet (punto en el tiempo).

        Reglas:
        - Debe tener <instant> con fecha = fiscal_year_end
        - NO debe tener <segment> (datos consolidados)

        Returns:
            str: Context ID (e.g., 'c-20')
        """
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
                    logger.info(
                        "balance_context_found",
                        context_id=self._balance_context
                    )
                    return self._balance_context

        raise ValueError(f"No balance context found for {target_date}")

    def get_income_context(self) -> str:
        """
        Devuelve el contextID para Income Statement (periodo anual).

        Reglas:
        - Debe tener <duration> con endDate = fiscal_year_end
        - startDate debe ser ~1 año antes (350-370 días)
        - NO debe tener <segment>

        CORREGIDO: Tolerancia ampliada a 350-370 días para cubrir edge cases.

        Returns:
            str: Context ID (e.g., 'c-1')
        """
        if self._income_context is not None:
            return self._income_context

        target_end = self.fiscal_year_end
        contexts = self.root.findall('.//xbrli:context', self.NS)

        candidates = []

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
                # Verificar que sea periodo anual
                start_date_elem = period.find('xbrli:startDate', self.NS)
                if start_date_elem is not None:
                    start_date = datetime.strptime(
                        start_date_elem.text, '%Y-%m-%d'
                    ).date()

                    days = (end_date - start_date).days

                    # Periodo anual: 350-370 días
                    # (tolerancia ampliada para edge cases)
                    if 350 <= days <= 370:
                        candidates.append((ctx.get('id'), days))

        if not candidates:
            raise ValueError(f"No income context found for {target_end}")

        # Si hay múltiples, elegir el más cercano a 365 días
        candidates.sort(key=lambda x: abs(x[1] - 365))
        self._income_context = candidates[0][0]

        logger.info(
            "income_context_found",
            context_id=self._income_context,
            duration_days=candidates[0][1]
        )
        return self._income_context

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
