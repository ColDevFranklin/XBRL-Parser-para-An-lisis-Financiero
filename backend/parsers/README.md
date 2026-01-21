# XBRL Parser para Análisis Financiero

Parser para archivos XBRL de reportes 10-K de la SEC.

## Características

- ✅ Extrae 14 campos financieros de Balance Sheet, Income Statement y Cash Flow
- ✅ Validación automática de ecuación contable (Assets = Liabilities + Equity)
- ✅ Procesamiento en <0.1 segundos
- ✅ Precisión validada contra Yahoo Finance (<2% diferencia)

## Uso

```python
from backend.parsers.xbrl_parser import XBRLParser

# Cargar archivo XBRL
parser = XBRLParser('data/apple_10k_xbrl.xml')
parser.load()

# Extraer datos
data = parser.extract_all()

# Acceder a datos
print(f"Assets: ${data['balance_sheet']['Assets']:,.0f}")
print(f"Revenue: ${data['income_statement']['Revenues']:,.0f}")
print(f"Operating CF: ${data['cash_flow']['OperatingCashFlow']:,.0f}")
```

## Campos Extraídos

### Balance Sheet

- Assets (Total)
- Liabilities (Total)
- Stockholders Equity
- Current Assets
- Cash and Equivalents
- Long Term Debt
- Current Liabilities

### Income Statement

- Revenues
- Cost of Revenue
- Gross Profit
- Operating Income
- Net Income

### Cash Flow Statement

- Operating Cash Flow
- Capital Expenditures

## Ejemplo de Output

```
--- Balance Sheet ---
  → Usando contexto: c-21
  Assets: $364,980,000,000
  Liabilities: $308,030,000,000
  StockholdersEquity: $56,950,000,000

✓ Validación:
  Balance cuadra (0.00% diferencia)

⏱️ Tiempo: 0.06 segundos
```

## Validación

Parser validado contra:

- **Yahoo Finance**: <2% diferencia en Balance Sheet
- **SEC 10-K oficial**: Ecuación contable cuadra perfectamente
- **Performance**: 83x más rápido que requisito (<5s)

## Siguiente Paso

Sprint 3-4: Motor de Métricas (ROE, P/E, Graham Score, Buffett Score)
