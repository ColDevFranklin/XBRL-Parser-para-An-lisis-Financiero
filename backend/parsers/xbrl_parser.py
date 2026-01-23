# backend/parsers/xbrl_parser.py

"""
Parser XBRL con Context Management y Transparency Engine integrados.

Cambios Sprint 2:
- Integra ContextManager para filtrar contextos consolidados
- Elimina valores duplicados de segmentos
- Usa contextos específicos para Balance (instant) vs Income (duration)

Cambios Transparency Engine:
- Retorna SourceTrace en lugar de floats
- Metadata completa de origen XBRL (tag, context, timestamp)
- Trazabilidad end-to-end para analistas

Author: @franklin
Sprint: 2 - Context Management + Transparency
"""

from lxml import etree
from typing import Dict, Optional, List
from datetime import datetime  # NUEVO
import time
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.engines.context_manager import ContextManager
from backend.engines.tracked_metric import SourceTrace  # NUEVO


class XBRLParser:
    """
    Parser para archivos XBRL de la SEC con context filtering y trazabilidad.

    Uso:
        parser = XBRLParser('apple.xml')
        parser.load()
        data = parser.extract_all()

        # Acceder a valores con trazabilidad
        assets = data['balance_sheet']['Assets']
        print(assets.raw_value)  # Float value
        print(assets.xbrl_tag)   # "us-gaap:Assets"
        print(assets.context_id) # "c-20"
    """

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

    def load(self) -> bool:
        """
        Carga el archivo XBRL e inicializa ContextManager.

        Returns:
            bool: True si carga exitosa
        """
        try:
            self.tree = etree.parse(self.filepath)
            self.root = self.tree.getroot()
            self.namespaces = self.root.nsmap

            # Inicializar ContextManager
            self.context_mgr = ContextManager(self.tree)

            print(f"✓ Archivo cargado: {self.filepath}")
            print(f"  Namespaces encontrados: {len(self.namespaces)}")
            print(f"  Año fiscal: {self.context_mgr.fiscal_year}")
            print(f"  Fiscal year-end: {self.context_mgr.fiscal_year_end}")

            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def _get_value_by_context(
        self,
        field_name: str,
        target_context: str,
        section: str  # NUEVO parámetro
    ) -> Optional[SourceTrace]:  # CAMBIO: antes retornaba Optional[float]
        """
        Extrae valor de un campo filtrando por contexto específico.

        CAMBIO CLAVE: Retorna SourceTrace con metadata completa.

        Args:
            field_name: Nombre del campo en TAG_MAPPING
            target_context: ID del contexto a usar (e.g., 'c-20')
            section: 'balance_sheet', 'income_statement', 'cash_flow'

        Returns:
            SourceTrace: Objeto con valor + metadata, o None si no existe
        """
        if field_name not in self.TAG_MAPPING:
            return None

        # Buscar cada tag alternativo
        for tag_name in self.TAG_MAPPING[field_name]:
            xpath = f".//*[local-name()='{tag_name}'][@contextRef='{target_context}']"
            elements = self.root.xpath(xpath)

            for elem in elements:
                if elem.text and elem.text.strip():
                    try:
                        raw_value = float(elem.text)

                        if raw_value > 1000:  # Filtro básico
                            # NUEVO: Crear SourceTrace
                            trace = SourceTrace(
                                xbrl_tag=tag_name,  # Tag sin namespace para simplicidad
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

    def extract_balance_sheet(self) -> Dict[str, Optional[SourceTrace]]:  # CAMBIO tipo retorno
        """
        Extrae Balance Sheet usando contexto <instant> consolidado.

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

        fields = [
            'Assets', 'Liabilities', 'StockholdersEquity',
            'CurrentAssets', 'CashAndEquivalents',
            'LongTermDebt', 'CurrentLiabilities'
        ]

        balance = {}
        for field in fields:
            value = self._get_value_by_context(
                field,
                bs_context,
                section='balance_sheet'  # NUEVO
            )
            balance[field] = value
            print(f"  {field}: {self.format_currency(value)}")

        # Validar ecuación contable
        if all([
            balance.get('Assets'),
            balance.get('Liabilities'),
            balance.get('StockholdersEquity')
        ]):
            # CAMBIO: Acceder a raw_value de SourceTrace
            assets = balance['Assets'].raw_value
            liabilities = balance['Liabilities'].raw_value
            equity = balance['StockholdersEquity'].raw_value
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

    def extract_income_statement(self) -> Dict[str, Optional[SourceTrace]]:  # CAMBIO tipo retorno
        """
        Extrae Income Statement usando contexto <duration> anual.

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

        fields = [
            'Revenues', 'CostOfRevenue', 'GrossProfit',
            'OperatingIncomeLoss', 'NetIncomeLoss', 'InterestExpense'
        ]

        income = {}
        for field in fields:
            value = self._get_value_by_context(
                field,
                income_context,
                section='income_statement'  # NUEVO
            )
            income[field] = value
            print(f"  {field}: {self.format_currency(value)}")

        return income

    def extract_cash_flow(self) -> Dict[str, Optional[SourceTrace]]:  # CAMBIO tipo retorno
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
                section='cash_flow'  # NUEVO
            )
            cash_flow[field] = value
            print(f"  {field}: {self.format_currency(value)}")

        return cash_flow

    def extract_all(self) -> Dict[str, Dict[str, Optional[SourceTrace]]]:  # CAMBIO tipo retorno
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


if __name__ == "__main__":
    parser = XBRLParser('data/apple_10k_xbrl.xml')

    start_time = time.time()

    if parser.load():
        data = parser.extract_all()

        end_time = time.time()
        processing_time = end_time - start_time

        print("\n" + "="*60)
        print("✅ EXTRACCION COMPLETADA")
        print("="*60)

        total_fields = sum(
            1 for section in data.values()
            for value in section.values()
            if value is not None
        )

        print(f"\n📊 Campos extraidos: {total_fields}/15")

        required_fields = ['Assets', 'Liabilities', 'StockholdersEquity',
                          'Revenues', 'NetIncomeLoss']

        extracted_count = 0
        for field in required_fields:
            for section in data.values():
                if section.get(field) is not None:
                    extracted_count += 1
                    break

        print(f"✓ Campos core extraidos: {extracted_count}/5")

        # CAMBIO: Acceder a raw_value de SourceTrace
        bs = data['balance_sheet']
        balance_ok = False
        if all([bs.get('Assets'), bs.get('Liabilities'), bs.get('StockholdersEquity')]):
            assets = bs['Assets'].raw_value
            liabilities = bs['Liabilities'].raw_value
            equity = bs['StockholdersEquity'].raw_value

            diff_pct = abs(assets - (liabilities + equity)) / assets * 100
            balance_ok = diff_pct < 1
            print(f"✓ Balance cuadra: {'Si' if balance_ok else 'No'} ({diff_pct:.2f}% diferencia)")

        print(f"\n⏱️  Tiempo de procesamiento: {processing_time:.2f} segundos")

        # NUEVO: Demostrar trazabilidad
        if bs.get('Assets'):
            print("\n🔍 Trazabilidad ejemplo (Assets):")
            assets_trace = bs['Assets']
            print(f"   Tag XBRL: {assets_trace.xbrl_tag}")
            print(f"   Valor: ${assets_trace.raw_value:,.0f}")
            print(f"   Contexto: {assets_trace.context_id}")
            print(f"   Sección: {assets_trace.section}")
            print(f"   Timestamp: {assets_trace.extracted_at.isoformat()}")

        if extracted_count >= 5 and balance_ok and processing_time < 5:
            print("\n🎯 SPRINT 2 + TRANSPARENCY ENGINE COMPLETADO")
            print("   ✓ Parser con ContextManager integrado")
            print("   ✓ SourceTrace con metadata completa")
            print("   ✓ Balance sheet cuadra (<1% diferencia)")
            print(f"   ✓ Tiempo <5 segundos ({processing_time:.2f}s)")
            print("\n📋 Siguiente: Sprint 3 (25 Métricas con Trazabilidad)")
        else:
            print("\n⚠️  REVISAR")
            if extracted_count < 5:
                print(f"   ✗ Faltan {5 - extracted_count} campos core")
            if not balance_ok:
                print("   ✗ Balance sheet no cuadra")
            if processing_time >= 5:
                print(f"   ✗ Tiempo excede 5s ({processing_time:.2f}s)")
