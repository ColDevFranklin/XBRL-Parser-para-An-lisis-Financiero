# backend/parsers/xbrl_parser.py

"""
Parser XBRL con Context Management integrado.

Cambios Sprint 2:
- Integra ContextManager para filtrar contextos consolidados
- Elimina valores duplicados de segmentos
- Usa contextos específicos para Balance (instant) vs Income (duration)

Author: @franklin
Sprint: 2 - Context Management
"""

from lxml import etree
from typing import Dict, Optional, List
import time
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.engines.context_manager import ContextManager


class XBRLParser:
    """
    Parser para archivos XBRL de la SEC con context filtering.

    Uso:
        parser = XBRLParser('apple.xml')
        parser.load()
        data = parser.extract_all()
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
        self.context_mgr = None  # ← NUEVO

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

            # ← NUEVO: Inicializar ContextManager
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
        target_context: str
    ) -> Optional[float]:
        """
        Extrae valor de un campo filtrando por contexto específico.

        CAMBIO CLAVE: Solo busca en el contexto consolidado indicado.

        Args:
            field_name: Nombre del campo en TAG_MAPPING
            target_context: ID del contexto a usar (e.g., 'c-20')

        Returns:
            float: Valor extraído o None
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
                        value = float(elem.text)
                        if value > 1000:  # Filtro básico
                            return value
                    except ValueError:
                        continue

        return None

    def format_currency(self, value: Optional[float]) -> str:
        """Formatea un valor como moneda."""
        if value is None:
            return "No encontrado"
        return f"${value:,.0f}"

    def extract_balance_sheet(self) -> Dict[str, Optional[float]]:
        """
        Extrae Balance Sheet usando contexto <instant> consolidado.

        CAMBIO: Usa ContextManager.get_balance_context()
        """
        print("\n--- Balance Sheet ---")

        # ← NUEVO: Obtener contexto correcto automáticamente
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
            value = self._get_value_by_context(field, bs_context)
            balance[field] = value
            print(f"  {field}: {self.format_currency(value)}")

        # Validar ecuación contable
        if all([
            balance.get('Assets'),
            balance.get('Liabilities'),
            balance.get('StockholdersEquity')
        ]):
            assets = balance['Assets']
            liabilities = balance['Liabilities']
            equity = balance['StockholdersEquity']
            calculated = liabilities + equity
            diff_pct = abs(assets - calculated) / assets * 100

            print(f"\n✓ Validación:")
            print(f"  Assets: {self.format_currency(assets)}")
            print(f"  Liabilities + Equity: {self.format_currency(calculated)}")
            print(f"  Diferencia: {diff_pct:.2f}%")

            if diff_pct < 1:
                print("  ✓ Balance cuadra")
            else:
                print("  ✗ Balance NO cuadra")

        return balance

    def extract_income_statement(self) -> Dict[str, Optional[float]]:
        """
        Extrae Income Statement usando contexto <duration> anual.

        CAMBIO: Usa ContextManager.get_income_context()
        """
        print("\n--- Income Statement ---")

        # ← NUEVO: Obtener contexto duration anual
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
            value = self._get_value_by_context(field, income_context)
            income[field] = value
            print(f"  {field}: {self.format_currency(value)}")

        return income

    def extract_cash_flow(self) -> Dict[str, Optional[float]]:
        """
        Extrae Cash Flow Statement usando contexto <duration> anual.

        CAMBIO: Usa el mismo contexto que Income Statement
        """
        print("\n--- Cash Flow Statement ---")

        # Cash Flow usa mismo contexto que Income (ambos duration)
        try:
            cf_context = self.context_mgr.get_income_context()
            print(f"  → Usando contexto: {cf_context}")
        except ValueError as e:
            print(f"  ✗ Error: {e}")
            return {}

        fields = ['OperatingCashFlow', 'CapitalExpenditures']

        cash_flow = {}
        for field in fields:
            value = self._get_value_by_context(field, cf_context)
            cash_flow[field] = value
            print(f"  {field}: {self.format_currency(value)}")

        return cash_flow

    def extract_all(self) -> Dict[str, Dict[str, Optional[float]]]:
        """Extrae todos los estados financieros."""
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

        bs = data['balance_sheet']
        balance_ok = False
        if all([bs.get('Assets'), bs.get('Liabilities'), bs.get('StockholdersEquity')]):
            diff_pct = abs(bs['Assets'] - (bs['Liabilities'] + bs['StockholdersEquity'])) / bs['Assets'] * 100
            balance_ok = diff_pct < 1
            print(f"✓ Balance cuadra: {'Si' if balance_ok else 'No'} ({diff_pct:.2f}% diferencia)")

        print(f"\n⏱️  Tiempo de procesamiento: {processing_time:.2f} segundos")

        if extracted_count >= 5 and balance_ok and processing_time < 5:
            print("\n🎯 SPRINT 1-2 COMPLETADO AL 100%")
            print("   ✓ Parser con ContextManager integrado")
            print("   ✓ Balance sheet cuadra (<1% diferencia)")
            print(f"   ✓ Tiempo <5 segundos ({processing_time:.2f}s)")
            print("\n📋 Siguiente: Sprint 3-4 (25 Métricas Financieras)")
        else:
            print("\n⚠️  REVISAR")
            if extracted_count < 5:
                print(f"   ✗ Faltan {5 - extracted_count} campos core")
            if not balance_ok:
                print("   ✗ Balance sheet no cuadra")
            if processing_time >= 5:
                print(f"   ✗ Tiempo excede 5s ({processing_time:.2f}s)")
