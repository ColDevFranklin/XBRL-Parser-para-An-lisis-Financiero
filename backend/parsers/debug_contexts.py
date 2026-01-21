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
            # Extraer namespaces del documento
            self.namespaces = self.root.nsmap
            print(f"✓ Archivo cargado: {self.filepath}")
            print(f"  Namespaces encontrados: {len(self.namespaces)}")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    def extract_value(self, field_name: str, prefer_latest: bool = True) -> Optional[float]:
        """
        Busca un campo usando TAG_MAPPING y extrae su valor numérico.
        
        Args:
            field_name: Nombre del campo en TAG_MAPPING
            prefer_latest: Si True, retorna el valor más grande (asume más reciente)
        """
        if field_name not in self.TAG_MAPPING:
            return None
        
        tag_variants = self.TAG_MAPPING[field_name]
        candidates = []
        
        for tag_name in tag_variants:
            xpath = f".//*[local-name()='{tag_name}']"
            elements = self.root.xpath(xpath)
            
            if elements:
                for elem in elements:
                    if elem.text and elem.text.strip():
                        try:
                            value = float(elem.text)
                            if value > 1000:  # Filtro básico para valores significativos
                                context = elem.get('contextRef', '')
                                candidates.append({
                                    'value': value,
                                    'context': context,
                                    'tag': tag_name
                                })
                        except ValueError:
                            continue
        
        if not candidates:
            return None
        
        # Estrategia: retornar el valor más grande (suele ser el más reciente/consolidado)
        if prefer_latest:
            return max(candidates, key=lambda x: x['value'])['value']
        else:
            return min(candidates, key=lambda x: x['value'])['value']
    
    def format_currency(self, value: Optional[float]) -> str:
        """Formatea un valor como moneda."""
        if value is None:
            return "No encontrado"
        return f"${value:,.0f}"
    
    def extract_balance_sheet(self) -> Dict[str, Optional[float]]:
        """Extrae líneas principales del balance."""
        print("\n--- Balance Sheet ---")
        
        fields = ['Assets', 'Liabilities', 'StockholdersEquity', 
                  'CurrentAssets', 'CashAndEquivalents', 'LongTermDebt', 'CurrentLiabilities']
        
        balance = {}
        for field in fields:
            value = self.extract_value(field, prefer_latest=True)
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
            value = self.extract_value(field, prefer_latest=True)
            income[field] = value
            print(f"  {field}: {self.format_currency(value)}")
        
        return income
    
    def extract_cash_flow(self) -> Dict[str, Optional[float]]:
        """Extrae líneas principales del cash flow statement."""
        print("\n--- Cash Flow Statement ---")
        
        fields = ['OperatingCashFlow', 'CapitalExpenditures']
        
        cash_flow = {}
        for field in fields:
            value = self.extract_value(field, prefer_latest=True)
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
    
    if parser.load():
        data = parser.extract_all()
        
        print("\n" + "="*60)
        print("✅ EXTRACCIÓN COMPLETADA")
        print("="*60)
        
        # Contar campos extraídos exitosamente
        total_fields = sum(
            1 for section in data.values() 
            for value in section.values() 
            if value is not None
        )
        
        print(f"\n📊 Campos extraídos: {total_fields}/14")
        
        # Checkpoint: ¿Pasamos el criterio del Sprint 1-2?
        required_fields = ['Assets', 'Liabilities', 'StockholdersEquity', 
                          'Revenues', 'NetIncomeLoss']
        
        extracted_count = 0
        for field in required_fields:
            for section in data.values():
                if section.get(field) is not None:
                    extracted_count += 1
                    break
        
        print(f"✓ Campos core (mínimo 5): {extracted_count}/5")
        
        if extracted_count >= 5:
            print("\n🎯 CHECKPOINT SPRINT 1-2: COMPLETADO")
            print("   ✓ Parser extrae 5+ campos core")
            print("   → Siguiente paso: Test de regresión vs CFA manual")
        else:
            print("\n⚠️  CHECKPOINT SPRINT 1-2: PENDIENTE")
            print(f"   Faltan {5 - extracted_count} campos core")
