# backend/parsers/xbrl_parser.py

"""
Parser XBRL con Context Management y Transparency Engine integrados.

Cambios Sprint 2:
- Integra ContextManager para filtrar contextos consolidados
- Elimina valores duplicados de segmentos
- Usa contextos específicos para Balance (instant) vs Income (duration)
- NUEVO: extract_timeseries() para análisis multi-year

Cambios Sprint 3:
- Integra TaxonomyResolver para portabilidad cross-company
- Elimina dependencia de TAG_MAPPING hardcodeado
- Resuelve tags automáticamente según empresa

Cambios Transparency Engine:
- Retorna SourceTrace en lugar de floats
- Metadata completa de origen XBRL (tag, context, timestamp)
- Trazabilidad end-to-end para analistas

Author: @franklin
Sprint: 3 - Taxonomy Mapping + 25 Métricas
"""

from lxml import etree
from typing import Dict, Optional, List, Any
from datetime import datetime
import time
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.engines.context_manager import ContextManager
from backend.engines.tracked_metric import SourceTrace
from backend.parsers.taxonomy_resolver import TaxonomyResolver


class XBRLParser:
    """
    Parser para archivos XBRL de la SEC con context filtering y trazabilidad.

    SPRINT 3 FEATURES:
    - TaxonomyResolver para cross-company compatibility
    - Auto-resolución de tags XBRL
    - Portabilidad entre Apple, Microsoft, Berkshire, etc.

    Uso:
        parser = XBRLParser('apple.xml')
        parser.load()
        data = parser.extract_all()

        # Acceder a valores con trazabilidad
        assets = data['balance_sheet']['Assets']
        print(assets.raw_value)  # Float value
        print(assets.xbrl_tag)   # "Assets" (auto-resuelto)
        print(assets.context_id) # "c-20"

        # Time-series
        timeseries = parser.extract_timeseries(years=4)
        print(timeseries[2025]['Revenue'])  # SourceTrace object
    """

    # ========================================================================
    # DEPRECADO: TAG_MAPPING será eliminado en Sprint 4
    # Mantenido SOLO para compatibilidad con tests antiguos
    # NUEVO código usa TaxonomyResolver en su lugar
    # ========================================================================
    TAG_MAPPING = {
        # Balance Sheet
        'Assets': ['Assets', 'AssetsTotal'],
        'Liabilities': ['Liabilities', 'LiabilitiesTotal'],
        'StockholdersEquity': ['StockholdersEquity', 'ShareholdersEquity'],
        'CurrentAssets': ['AssetsCurrent'],
        'CashAndEquivalents': ['CashAndCashEquivalentsAtCarryingValue', 'Cash'],
        'LongTermDebt': ['LongTermDebt', 'LongTermDebtNoncurrent'],
        'CurrentLiabilities': ['LiabilitiesCurrent'],

        # Income Statement
        'Revenues': [
            'RevenueFromContractWithCustomerExcludingAssessedTax',
            'Revenues',
            'SalesRevenueNet',
            'RevenueFromContractWithCustomer'
        ],
        'NetIncomeLoss': ['NetIncomeLoss', 'ProfitLoss'],
        'CostOfRevenue': ['CostOfRevenue', 'CostOfGoodsAndServicesSold'],
        'GrossProfit': ['GrossProfit'],
        'OperatingIncomeLoss': ['OperatingIncomeLoss', 'OperatingIncome'],
        'InterestExpense': ['InterestExpense'],

        # Cash Flow Statement
        'OperatingCashFlow': ['NetCashProvidedByUsedInOperatingActivities'],
        'CapitalExpenditures': ['PaymentsToAcquirePropertyPlantAndEquipment'],
    }

    def __init__(self, filepath: str):
        """
        Args:
            filepath: Ruta al archivo XBRL
        """
        self.filepath = filepath
        self.tree = None
        self.root = None
        self.namespaces = {}
        self.context_mgr = None
        self.resolver = None  # ← NUEVO Sprint 3: TaxonomyResolver

    def load(self) -> bool:
        """
        Carga el archivo XBRL e inicializa ContextManager y TaxonomyResolver.

        NUEVO Sprint 3: Inicializa TaxonomyResolver para portabilidad

        Returns:
            bool: True si carga exitosa
        """
        try:
            self.tree = etree.parse(self.filepath)
            self.root = self.tree.getroot()
            self.namespaces = self.root.nsmap

            # Inicializar ContextManager
            self.context_mgr = ContextManager(self.tree)

            # ← NUEVO Sprint 3: Inicializar TaxonomyResolver
            self.resolver = TaxonomyResolver()

            print(f"✓ Archivo cargado: {self.filepath}")
            print(f"  Namespaces encontrados: {len(self.namespaces)}")
            print(f"  Año fiscal: {self.context_mgr.fiscal_year}")
            print(f"  Fiscal year-end: {self.context_mgr.fiscal_year_end}")
            print(f"  TaxonomyResolver: {len(self.resolver.list_concepts())} concepts")

            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def _get_value_by_context(
        self,
        field_name: str,
        target_context: str,
        section: str
    ) -> Optional[SourceTrace]:
        """
        Extrae valor de un campo filtrando por contexto específico.

        CAMBIO SPRINT 3: Usa TaxonomyResolver en lugar de TAG_MAPPING

        Args:
            field_name: Nombre del concepto contable (e.g., "NetIncome", "Assets", "Equity")
            target_context: ID del contexto a usar (e.g., 'c-20')
            section: 'balance_sheet', 'income_statement', 'cash_flow'

        Returns:
            SourceTrace: Objeto con valor + metadata, o None si no existe

        Example:
            # ANTES (Sprint 2):
            # field_name = 'NetIncomeLoss'  (hardcoded tag)

            # AHORA (Sprint 3):
            # field_name = 'NetIncome'  (concepto abstracto)
            # resolver.resolve() → 'NetIncomeLoss' para Apple
            #                   → 'ProfitLoss' para otra empresa
        """
        try:
            # ← NUEVO Sprint 3: Usar TaxonomyResolver
            tag_name = self.resolver.resolve(field_name, self.tree)
        except ValueError:
            # Concepto no encontrado en documento XBRL
            # (puede ser normal, no todas las empresas reportan todos los campos)
            return None

        # Buscar el tag resuelto en el contexto específico
        xpath = f".//*[local-name()='{tag_name}'][@contextRef='{target_context}']"
        elements = self.root.xpath(xpath)

        for elem in elements:
            if elem.text and elem.text.strip():
                try:
                    raw_value = float(elem.text)

                    if raw_value > 1000:  # Filtro básico para valores grandes
                        # Crear SourceTrace con metadata completa
                        trace = SourceTrace(
                            xbrl_tag=tag_name,  # Tag resuelto (sin namespace)
                            raw_value=raw_value,
                            context_id=target_context,
                            extracted_at=datetime.now(),
                            section=section
                        )
                        return trace

                except ValueError:
                    continue

        return None

    def format_currency(self, value: Optional[SourceTrace]) -> str:
        """
        Formatea un SourceTrace como moneda.

        CAMBIO: Ahora recibe SourceTrace en lugar de float
        """
        if value is None:
            return "No encontrado"
        return f"${value.raw_value:,.0f}"

    def extract_balance_sheet(self) -> Dict[str, Optional[SourceTrace]]:
        """
        Extrae Balance Sheet usando contexto <instant> consolidado.

        CAMBIO Sprint 3: Field names ahora son conceptos abstractos

        Returns:
            Dict con SourceTrace por cada campo
        """
        print("\n--- Balance Sheet ---")

        try:
            bs_context = self.context_mgr.get_balance_context()
            print(f"  → Usando contexto: {bs_context}")
            print(f"    (Fecha: {self.context_mgr.fiscal_year_end})")
        except ValueError as e:
            print(f"  ✗ Error: {e}")
            return {}

        # ← NUEVO Sprint 3: Conceptos abstractos (no tags específicos)
        fields = [
            'Assets', 'Liabilities', 'Equity',  # Cambiado de 'StockholdersEquity'
            'CurrentAssets', 'CashAndEquivalents',
            'LongTermDebt', 'CurrentLiabilities'
        ]

        balance = {}
        for field in fields:
            value = self._get_value_by_context(
                field,
                bs_context,
                section='balance_sheet'
            )
            balance[field] = value
            print(f"  {field}: {self.format_currency(value)}")

        # Validar ecuación contable
        if all([
            balance.get('Assets'),
            balance.get('Liabilities'),
            balance.get('Equity')
        ]):
            assets = balance['Assets'].raw_value
            liabilities = balance['Liabilities'].raw_value
            equity = balance['Equity'].raw_value
            calculated = liabilities + equity
            diff_pct = abs(assets - calculated) / assets * 100

            print(f"\n✓ Validación:")
            print(f"  Assets: ${assets:,.0f}")
            print(f"  Liabilities + Equity: ${calculated:,.0f}")
            print(f"  Diferencia: {diff_pct:.2f}%")

            if diff_pct < 1:
                print("  ✓ Balance cuadra")
            else:
                print("  ✗ Balance NO cuadra")

        return balance

    def extract_income_statement(self) -> Dict[str, Optional[SourceTrace]]:
        """
        Extrae Income Statement usando contexto <duration> anual.

        CAMBIO Sprint 3: Field names ahora son conceptos abstractos

        Returns:
            Dict con SourceTrace por cada campo
        """
        print("\n--- Income Statement ---")

        try:
            income_context = self.context_mgr.get_income_context()
            print(f"  → Usando contexto: {income_context}")
        except ValueError as e:
            print(f"  ✗ Error: {e}")
            return {}

        # ← NUEVO Sprint 3: Conceptos abstractos
        fields = [
            'Revenue', 'CostOfRevenue', 'GrossProfit',  # Cambiado de 'Revenues'
            'OperatingIncome', 'NetIncome', 'InterestExpense'  # Cambiado nombres
        ]

        income = {}
        for field in fields:
            value = self._get_value_by_context(
                field,
                income_context,
                section='income_statement'
            )
            income[field] = value
            print(f"  {field}: {self.format_currency(value)}")

        return income

    def extract_cash_flow(self) -> Dict[str, Optional[SourceTrace]]:
        """
        Extrae Cash Flow Statement usando contexto <duration> anual.

        Returns:
            Dict con SourceTrace por cada campo
        """
        print("\n--- Cash Flow Statement ---")

        try:
            cf_context = self.context_mgr.get_income_context()
            print(f"  → Usando contexto: {cf_context}")
        except ValueError as e:
            print(f"  ✗ Error: {e}")
            return {}

        fields = ['OperatingCashFlow', 'CapitalExpenditures']

        cash_flow = {}
        for field in fields:
            value = self._get_value_by_context(
                field,
                cf_context,
                section='cash_flow'
            )
            cash_flow[field] = value
            print(f"  {field}: {self.format_currency(value)}")

        return cash_flow

    def extract_all(self) -> Dict[str, Dict[str, Optional[SourceTrace]]]:
        """
        Extrae todos los estados financieros con trazabilidad.

        Returns:
            Dict con SourceTrace objects en lugar de floats
        """
        return {
            'balance_sheet': self.extract_balance_sheet(),
            'income_statement': self.extract_income_statement(),
            'cash_flow': self.extract_cash_flow()
        }

    # ========================================================================
    # TIME-SERIES EXTRACTION (Sprint 2)
    # ========================================================================

    def extract_timeseries(self, years: int = 5) -> Dict[int, Dict[str, SourceTrace]]:
        """
        Extrae métricas financieras para múltiples años fiscales.

        Args:
            years: Número máximo de años a extraer (default: 5)

        Returns:
            {
                2025: {
                    'Assets': SourceTrace(...),
                    'Liabilities': SourceTrace(...),
                    'Equity': SourceTrace(...),
                    'Revenue': SourceTrace(...),
                    'NetIncome': SourceTrace(...),
                    ...
                },
                2024: {...},
                2023: {...}
            }

        Raises:
            ValueError: Si context_mgr no está inicializado

        Example:
            >>> parser = XBRLParser('data/apple_10k_xbrl.xml')
            >>> parser.load()
            >>> timeseries = parser.extract_timeseries(years=3)
            >>> len(timeseries)
            3
            >>> timeseries[2025]['Revenue'].raw_value
            391035000000.0
        """
        if not self.context_mgr:
            raise ValueError(
                "ContextManager not initialized. Call load() first."
            )

        # 1. Obtener años disponibles (ya ordenados desc por context_mgr)
        available_years = self.context_mgr.get_available_years()

        if not available_years:
            print("⚠️  No se detectaron años fiscales en el XBRL")
            return {}

        years_to_extract = available_years[:min(years, len(available_years))]

        print(f"\n🔍 Extrayendo time-series para {len(years_to_extract)} años:")
        print(f"   Años detectados: {available_years}")
        print(f"   Años a extraer: {years_to_extract}")

        result = {}

        # 2. Extraer datos para cada año
        for year in years_to_extract:
            try:
                print(f"\n   → Procesando año {year}...")
                year_data = self._extract_year_data(year)

                # Validar que extrajo al menos datos básicos
                if year_data.get('Assets') and year_data.get('Revenue'):
                    result[year] = year_data
                    print(f"     ✓ {len(year_data)} campos extraídos")
                else:
                    print(f"     ⚠️  Datos incompletos para {year}")

            except Exception as e:
                print(f"     ✗ Error en año {year}: {e}")
                continue

        print(f"\n✓ Time-series completo: {len(result)}/{len(years_to_extract)} años")
        return result

    def _extract_year_data(self, year: int) -> Dict[str, SourceTrace]:
        """
        Extrae datos financieros de un año fiscal específico.

        CAMBIO Sprint 3: Usa conceptos abstractos

        Args:
            year: Año fiscal (ej: 2025)

        Returns:
            Dict con SourceTrace por cada campo financiero

        Raises:
            ValueError: Si no existen contextos para el año
        """
        # Obtener contextos del año específico
        balance_ctx = self.context_mgr.get_balance_context(year=year)
        income_ctx = self.context_mgr.get_income_context(year=year)

        if not balance_ctx:
            raise ValueError(f"Balance context no encontrado para {year}")
        if not income_ctx:
            raise ValueError(f"Income context no encontrado para {year}")

        year_data = {}

        # ====================================================================
        # BALANCE SHEET (instant context) - Conceptos abstractos Sprint 3
        # ====================================================================
        balance_fields = {
            'Assets': 'balance_sheet',
            'Liabilities': 'balance_sheet',
            'Equity': 'balance_sheet',  # Cambiado de 'StockholdersEquity'
            'CurrentAssets': 'balance_sheet',
            'CurrentLiabilities': 'balance_sheet',
            'LongTermDebt': 'balance_sheet',
            'CashAndEquivalents': 'balance_sheet',
        }

        for field_name, section in balance_fields.items():
            value = self._get_value_by_context(
                field_name,
                balance_ctx,
                section
            )
            if value:  # Solo agregar si existe
                year_data[field_name] = value

        # ====================================================================
        # INCOME STATEMENT (duration context) - Conceptos abstractos Sprint 3
        # ====================================================================
        income_fields = {
            'Revenue': 'income_statement',  # Cambiado de 'Revenues'
            'NetIncome': 'income_statement',  # Cambiado de 'NetIncomeLoss'
            'OperatingIncome': 'income_statement',  # Cambiado de 'OperatingIncomeLoss'
            'GrossProfit': 'income_statement',
            'CostOfRevenue': 'income_statement',
            'InterestExpense': 'income_statement',
        }

        for field_name, section in income_fields.items():
            value = self._get_value_by_context(
                field_name,
                income_ctx,
                section
            )
            if value:
                year_data[field_name] = value

        # ====================================================================
        # CASH FLOW (duration context - usa mismo que income)
        # ====================================================================
        cashflow_fields = {
            'OperatingCashFlow': 'cash_flow',
            'CapitalExpenditures': 'cash_flow',
        }

        for field_name, section in cashflow_fields.items():
            value = self._get_value_by_context(
                field_name,
                income_ctx,  # Usa income_ctx (duration anual)
                section
            )
            if value:
                year_data[field_name] = value

        return year_data


if __name__ == "__main__":
    parser = XBRLParser('data/apple_10k_xbrl.xml')

    start_time = time.time()

    if parser.load():
        # ====================================================================
        # TEST 1: Extracción estándar (Sprint 3 - TaxonomyResolver)
        # ====================================================================
        print("\n" + "="*60)
        print("TEST 1: EXTRACCIÓN CON TAXONOMY RESOLVER")
        print("="*60)

        data = parser.extract_all()

        total_fields = sum(
            1 for section in data.values()
            for value in section.values()
            if value is not None
        )

        print(f"\n📊 Campos extraidos: {total_fields}")

        required_fields = ['Assets', 'Liabilities', 'Equity',
                          'Revenue', 'NetIncome']

        extracted_count = 0
        for field in required_fields:
            for section in data.values():
                if section.get(field) is not None:
                    extracted_count += 1
                    break

        print(f"✓ Campos core extraidos: {extracted_count}/5")

        # Validar balance
        bs = data['balance_sheet']
        balance_ok = False
        if all([bs.get('Assets'), bs.get('Liabilities'), bs.get('Equity')]):
            assets = bs['Assets'].raw_value
            liabilities = bs['Liabilities'].raw_value
            equity = bs['Equity'].raw_value

            diff_pct = abs(assets - (liabilities + equity)) / assets * 100
            balance_ok = diff_pct < 1
            print(f"✓ Balance cuadra: {'Si' if balance_ok else 'No'} ({diff_pct:.2f}% diferencia)")

        # ====================================================================
        # TEST 2: Time-Series (Sprint 2 + Sprint 3)
        # ====================================================================
        print("\n" + "="*60)
        print("TEST 2: TIME-SERIES CON TAXONOMY RESOLVER")
        print("="*60)

        timeseries = parser.extract_timeseries(years=4)

        print(f"\n📊 Años extraídos: {len(timeseries)}")
        print(f"   Años: {list(timeseries.keys())}")

        # Validar estructura
        for year, year_data in timeseries.items():
            print(f"\n   {year}:")
            print(f"      Campos: {len(year_data)}")

            # Mostrar campos principales
            if year_data.get('Revenue'):
                print(f"      Revenue: ${year_data['Revenue'].raw_value:,.0f}")
            if year_data.get('NetIncome'):
                print(f"      Net Income: ${year_data['NetIncome'].raw_value:,.0f}")
            if year_data.get('Assets'):
                print(f"      Assets: ${year_data['Assets'].raw_value:,.0f}")

            # Validar balance para este año
            if all(k in year_data for k in ['Assets', 'Liabilities', 'Equity']):
                a = year_data['Assets'].raw_value
                l = year_data['Liabilities'].raw_value
                e = year_data['Equity'].raw_value
                diff = abs(a - (l + e)) / a * 100
                print(f"      Balance check: {diff:.2f}% diff {'✓' if diff < 1 else '✗'}")

        end_time = time.time()
        processing_time = end_time - start_time

        print(f"\n⏱️  Tiempo de procesamiento: {processing_time:.2f} segundos")

        # ====================================================================
        # DEMOSTRACIÓN DE TRAZABILIDAD + TAXONOMY RESOLVER
        # ====================================================================
        if bs.get('Assets'):
            print("\n" + "="*60)
            print("🔍 TRAZABILIDAD CON TAXONOMY RESOLVER")
            print("="*60)
            assets_trace = bs['Assets']
            print(f"   Concepto abstracto: Assets")
            print(f"   Tag XBRL resuelto: {assets_trace.xbrl_tag}")
            print(f"   Valor: ${assets_trace.raw_value:,.0f}")
            print(f"   Contexto: {assets_trace.context_id}")
            print(f"   Sección: {assets_trace.section}")
            print(f"   Timestamp: {assets_trace.extracted_at.isoformat()}")

        # ====================================================================
        # VALIDACIÓN FINAL SPRINT 3
        # ====================================================================
        print("\n" + "="*60)
        print("✅ VALIDACIÓN SPRINT 3 - TAXONOMY RESOLVER")
        print("="*60)

        checks = {
            "TaxonomyResolver cargado": parser.resolver is not None,
            "Extracción estándar (5+ campos)": extracted_count >= 5,
            "Balance cuadra (<1%)": balance_ok,
            "Time-series (3+ años)": len(timeseries) >= 3,
            "Performance (<5 segundos)": processing_time < 5.0,
        }

        all_passed = all(checks.values())

        for check, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"   {status} {check}")

        if all_passed:
            print("\n🎯 SPRINT 3 - TAXONOMY RESOLVER INTEGRADO")
            print("   ✓ TaxonomyResolver funcional")
            print("   ✓ Cross-company compatibility ready")
            print("   ✓ Conceptos abstractos (no tags hardcoded)")
            print("   ✓ Time-series multi-year funcional")
            print(f"   ✓ Performance óptima ({processing_time:.2f}s)")
            print("\n📋 LISTO PARA: Implementar 24 métricas restantes")
        else:
            print("\n⚠️  REVISAR ISSUES:")
            for check, passed in checks.items():
                if not passed:
                    print(f"   ✗ {check}")
