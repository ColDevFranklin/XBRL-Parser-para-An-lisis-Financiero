from lxml import etree
from typing import Dict, Optional, List

class XBRLParser:
    """Parser para archivos XBRL de la SEC."""
    
    # Mapping de campos a posibles tags XBRL
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
    
    def _find_balance_sheet_context(self) -> Optional[str]:
        """
        Encuentra el contexto correcto del Balance Sheet más reciente.
        Busca el contexto donde Assets = Liabilities + Equity.
        """
        assets_values = self._get_all_values('Assets')
        liabilities_values = self._get_all_values('Liabilities')
        equity_values = self._get_all_values('StockholdersEquity')
        
        if not all([assets_values, liabilities_values, equity_values]):
            return None
        
        # Buscar combinación que cuadre
        for asset in assets_values:
            for liability in liabilities_values:
                for equity in equity_values:
                    # Verificar si están en el mismo contexto
                    if asset['context'] == liability['context'] == equity['context']:
                        # Verificar ecuación contable
                        calculated = liability['value'] + equity['value']
                        diff_pct = abs(asset['value'] - calculated) / asset['value'] * 100
                        
                        if diff_pct < 1:  # Tolerancia 1%
                            return asset['context']
        
        # Fallback: usar el contexto de Assets más grande
        return max(assets_values, key=lambda x: x['value'])['context']
    
    def _extract_with_context(self, field_name: str, target_context: Optional[str]) -> Optional[float]:
        """Extrae valor de un campo usando un contexto específico."""
        candidates = self._get_all_values(field_name)
        
        if not candidates:
            return None
        
        # Si hay contexto objetivo, buscar coincidencia exacta
        if target_context:
            matched = [c for c in candidates if c['context'] == target_context]
            if matched:
                return matched[0]['value']
        
        # Fallback: el más grande
        return max(candidates, key=lambda x: x['value'])['value']
    
    def format_currency(self, value: Optional[float]) -> str:
        """Formatea un valor como moneda."""
        if value is None:
            return "No encontrado"
        return f"${value:,.0f}"
    
    def extract_balance_sheet(self) -> Dict[str, Optional[float]]:
        """Extrae líneas principales del balance con coherencia de contextos."""
        print("\n--- Balance Sheet ---")
        
        # Encontrar contexto correcto
        bs_context = self._find_balance_sheet_context()
        if bs_context:
            print(f"  → Usando contexto: {bs_context}")
        
        fields = ['Assets', 'Liabilities', 'StockholdersEquity', 
                  'CurrentAssets', 'CashAndEquivalents', 'LongTermDebt', 'CurrentLiabilities']
        
        balance = {}
        for field in fields:
            value = self._extract_with_context(field, bs_context)
            balance[field] = value
            print(f"  {field}: {self.format_currency(value)}")
        
        # Validar ecuación contable
        if all([balance.get('Assets'), balance.get('Liabilities'), balance.get('StockholdersEquity')]):
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
        """Extrae líneas principales del income statement."""
        print("\n--- Income Statement ---")
        
        fields = ['Revenues', 'CostOfRevenue', 'GrossProfit', 
                  'OperatingIncomeLoss', 'NetIncomeLoss']
        
        income = {}
        for field in fields:
            # Income statement usa valores más grandes (acumulado anual)
            values = self._get_all_values(field)
            if values:
                income[field] = max(values, key=lambda x: x['value'])['value']
            else:
                income[field] = None
            print(f"  {field}: {self.format_currency(income[field])}")
        
        return income
    
    def extract_cash_flow(self) -> Dict[str, Optional[float]]:
        """Extrae líneas principales del cash flow statement."""
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
    
    if parser.load():
        data = parser.extract_all()
        
        print("\n" + "="*60)
        print("✅ EXTRACCIÓN COMPLETADA")
        print("="*60)
        
        # Contar campos extraídos
        total_fields = sum(
            1 for section in data.values() 
            for value in section.values() 
            if value is not None
        )
        
        print(f"\n📊 Campos extraídos: {total_fields}/14")
        
        # Checkpoint Sprint 1-2
        required_fields = ['Assets', 'Liabilities', 'StockholdersEquity', 
                          'Revenues', 'NetIncomeLoss']
        
        extracted_count = 0
        for field in required_fields:
            for section in data.values():
                if section.get(field) is not None:
                    extracted_count += 1
                    break
        
        print(f"✓ Campos core extraídos: {extracted_count}/5")
        
        # Validar balance cuadra
        bs = data['balance_sheet']
        if all([bs.get('Assets'), bs.get('Liabilities'), bs.get('StockholdersEquity')]):
            diff_pct = abs(bs['Assets'] - (bs['Liabilities'] + bs['StockholdersEquity'])) / bs['Assets'] * 100
            balance_ok = diff_pct < 1
            print(f"✓ Balance cuadra: {'Sí' if balance_ok else 'No'} ({diff_pct:.2f}% diferencia)")
        else:
            balance_ok = False
        
        # Resultado final
        if extracted_count >= 5 and balance_ok:
            print("\n🎯 CHECKPOINT SPRINT 1-2: ✅ COMPLETADO")
            print("   ✓ Parser extrae 5+ campos core")
            print("   ✓ Balance sheet cuadra (<1% diferencia)")
            print("   → Siguiente paso: Test de regresión vs CFA manual")
        else:
            print("\n⚠️  CHECKPOINT SPRINT 1-2: PENDIENTE")
            if extracted_count < 5:
                print(f"   ✗ Faltan {5 - extracted_count} campos core")
            if not balance_ok:
                print("   ✗ Balance sheet no cuadra")
