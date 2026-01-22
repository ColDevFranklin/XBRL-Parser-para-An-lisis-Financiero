"""
Test de regresión: Berkshire Hathaway 10-K
Caso complejo: Insurance accounting (edge case)
Criterio relajado: Sistema debe manejar gracefully
"""
import sys
sys.path.insert(0, '/home/h4ckio/Documentos/projects')

from backend.parsers.xbrl_parser import XBRLParser


def test_berkshire_parsing_without_crash():
    """
    Berkshire Hathaway tiene contabilidad compleja.
    Criterio: Parser NO debe crashear, aunque falten campos.
    """
    parser = XBRLParser('data/brk_10k_xbrl.xml')
    
    # El simple hecho de no lanzar excepción es éxito
    assert parser.load() == True
    data = parser.extract_all()
    
    assert data is not None
    assert 'balance_sheet' in data


def test_berkshire_balance_equation_if_available():
    """
    Si tenemos Assets/Liabilities/Equity, validar ecuación.
    Criterio RELAJADO: ±1% (vs ±1% para empresas normales)
    """
    parser = XBRLParser('data/brk_10k_xbrl.xml')
    parser.load()
    data = parser.extract_all()
    
    balance = data['balance_sheet']
    
    assets = balance.get('Assets')
    liabilities = balance.get('Liabilities')
    equity = balance.get('StockholdersEquity')
    
    print(f"\n--- Berkshire Balance Sheet ---")
    
    if all([assets, liabilities, equity]):
        # Tenemos los 3 → validar ecuación
        diff_pct = abs(assets - (liabilities + equity)) / assets * 100
        
        print(f"Assets:      ${assets:>15,.0f}")
        print(f"Liabilities: ${liabilities:>15,.0f}")
        print(f"Equity:      ${equity:>15,.0f}")
        print(f"Diferencia:  {diff_pct:>15.4f}%")
        
        assert diff_pct < 1.0, f"Balance no cuadra: {diff_pct:.4f}%"
    else:
        print("⚠️  Análisis parcial - algunos campos no disponibles")
        assert False, "Campos A/L/E no disponibles"


def test_berkshire_minimum_fields():
    """
    Berkshire puede NO tener todos los campos estándar.
    Criterio relajado: Al menos 10/15 campos.
    """
    parser = XBRLParser('data/brk_10k_xbrl.xml')
    parser.load()
    data = parser.extract_all()
    
    all_data = {
        **data['balance_sheet'],
        **data['income_statement'],
        **data['cash_flow']
    }
    
    extracted_count = sum(1 for v in all_data.values() if v is not None)
    
    print(f"\n--- Berkshire: Extracción ---")
    print(f"Campos extraídos: {extracted_count}/15")
    
    # Mostrar qué sí extrajimos
    for key, value in all_data.items():
        if value is not None:
            print(f"  ✓ {key}")
        else:
            print(f"  ✗ {key}: NO DISPONIBLE")
    
    # Criterio RELAJADO: Al menos 10 campos
    assert extracted_count >= 10, f"Muy pocos campos: {extracted_count}/15"
    
    print(f"\n✓ Berkshire pasó con {extracted_count}/15 campos (criterio: ≥10)")
