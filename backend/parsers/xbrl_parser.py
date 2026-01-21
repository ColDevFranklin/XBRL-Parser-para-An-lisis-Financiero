from lxml import etree
from typing import Dict, Optional, List
import time

class XBRLParser:
    """Parser para archivos XBRL de la SEC."""

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
        self.filepath = filepath
        self.tree = None
        self.root = None
        self.namespaces = {}

    def load(self) -> bool:
        """Carga el archivo XBRL."""
        try:
            self.tree = etree.parse(self.filepath)
            self.root = self.tree.getroot()
            self.namespaces = self.root.nsmap
            print(f"✓ Archivo cargado: {self.filepath}")
            print(f"  Namespaces encontrados: {len(self.namespaces)}")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def _get_all_values(self, field_name: str) -> List[Dict]:
        """Obtiene todos los valores de un campo con sus contextos."""
        if field_name not in self.TAG_MAPPING:
            return []

        candidates = []
        for tag_name in self.TAG_MAPPING[field_name]:
            xpath = f".//*[local-name()='{tag_name}']"
            elements = self.root.xpath(xpath)

            for elem in elements:
                if elem.text and elem.text.strip():
                    try:
                        value = float(elem.text)
                        if value > 1000:
                            context = elem.get('contextRef', '')
                            candidates.append({
                                'value': value,
                                'context': context,
                                'tag': tag_name
                            })
                    except ValueError:
                        pass

        return candidates

    def _find_balance_sheet_context(self) -> str:
        """
        Encuentra el contexto correcto del Balance Sheet mas reciente.
        Prioriza el contexto con Assets mas grande que cuadre.
        """
        assets_values = self._get_all_values('Assets')
        liabilities_values = self._get_all_values('Liabilities')
        equity_values = self._get_all_values('StockholdersEquity')

        # Buscar todas las combinaciones que cuadren
        valid_contexts = []

        for asset in assets_values:
            for liability in liabilities_values:
                for equity in equity_values:
                    # Mismo contexto
                    if asset['context'] == liability['context'] == equity['context']:
                        # Verificar ecuacion
                        calculated = liability['value'] + equity['value']
                        diff_pct = abs(asset['value'] - calculated) / asset['value'] * 100

                        if diff_pct < 1:
                            valid_contexts.append({
                                'context': asset['context'],
                                'assets': asset['value'],
                                'liabilities': liability['value'],
                                'equity': equity['value']
                            })

        # Priorizar el contexto con Assets MAS GRANDE (mas reciente)
        if valid_contexts:
            latest = max(valid_contexts, key=lambda x: x['assets'])
            return latest['context']

        # Fallback: Assets mas grande
        if assets_values:
            return max(assets_values, key=lambda x: x['value'])['context']

        return 'c-21'

    def _extract_with_context(self, field_name: str, target_context: str) -> Optional[float]:
        """Extrae valor de un campo usando un contexto especifico."""
        candidates = self._get_all_values(field_name)

        if not candidates:
            return None

        # Buscar coincidencia exacta de contexto
        matched = [c for c in candidates if c['context'] == target_context]
        if matched:
            return matched[0]['value']

        # Fallback: el mas grande
        return max(candidates, key=lambda x: x['value'])['value']

    def format_currency(self, value: Optional[float]) -> str:
        """Formatea un valor como moneda."""
        if value is None:
            return "No encontrado"
        return f"${value:,.0f}"

    def extract_balance_sheet(self) -> Dict[str, Optional[float]]:
        """Extrae lineas principales del balance."""
        print("\n--- Balance Sheet ---")

        # Encontrar contexto
        bs_context = self._find_balance_sheet_context()
        print(f"  → Usando contexto: {bs_context}")

        fields = ['Assets', 'Liabilities', 'StockholdersEquity',
                  'CurrentAssets', 'CashAndEquivalents', 'LongTermDebt', 'CurrentLiabilities']

        balance = {}
        for field in fields:
            value = self._extract_with_context(field, bs_context)
            balance[field] = value
            print(f"  {field}: {self.format_currency(value)}")

        # Validar ecuacion contable
        if all([balance.get('Assets'), balance.get('Liabilities'), balance.get('StockholdersEquity')]):
            assets = balance['Assets']
            liabilities = balance['Liabilities']
            equity = balance['StockholdersEquity']
            calculated = liabilities + equity
            diff_pct = abs(assets - calculated) / assets * 100

            print(f"\n✓ Validacion:")
            print(f"  Assets: {self.format_currency(assets)}")
            print(f"  Liabilities + Equity: {self.format_currency(calculated)}")
            print(f"  Diferencia: {diff_pct:.2f}%")

            if diff_pct < 1:
                print("  ✓ Balance cuadra")
            else:
                print("  ✗ Balance NO cuadra")

        return balance

    def extract_income_statement(self) -> Dict[str, Optional[float]]:
        """Extrae lineas principales del income statement."""
        print("\n--- Income Statement ---")

        fields = ['Revenues', 'CostOfRevenue', 'GrossProfit',
                  'OperatingIncomeLoss', 'NetIncomeLoss']

        income = {}
        for field in fields:
            values = self._get_all_values(field)
            if values:
                income[field] = max(values, key=lambda x: x['value'])['value']
            else:
                income[field] = None
            print(f"  {field}: {self.format_currency(income[field])}")

        return income

    def extract_cash_flow(self) -> Dict[str, Optional[float]]:
        """Extrae lineas principales del cash flow statement."""
        print("\n--- Cash Flow Statement ---")

        fields = ['OperatingCashFlow', 'CapitalExpenditures']

        cash_flow = {}
        for field in fields:
            values = self._get_all_values(field)
            if values:
                cash_flow[field] = max(values, key=lambda x: x['value'])['value']
            else:
                cash_flow[field] = None
            print(f"  {field}: {self.format_currency(cash_flow[field])}")

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

        print(f"\n📊 Campos extraidos: {total_fields}/14")

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
            print("\n🎯 CHECKPOINT SPRINT 1-2: ✅ COMPLETADO AL 100%")
            print("   ✓ Parser extrae 5+ campos core")
            print("   ✓ Balance sheet cuadra (<1% diferencia)")
            print(f"   ✓ Tiempo <5 segundos ({processing_time:.2f}s)")
            print("\n📋 Siguiente paso: Crear README.md + Sprint 3-4 (Metricas)")
        else:
            print("\n⚠️  CHECKPOINT SPRINT 1-2: REVISAR")
            if extracted_count < 5:
                print(f"   ✗ Faltan {5 - extracted_count} campos core")
            if not balance_ok:
                print("   ✗ Balance sheet no cuadra")
            if processing_time >= 5:
                print(f"   ✗ Tiempo excede 5s ({processing_time:.2f}s)")
