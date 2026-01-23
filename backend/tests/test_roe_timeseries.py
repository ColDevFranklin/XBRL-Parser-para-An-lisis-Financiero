"""
Test: ROE con Time-Series (4 años)
Valida que Transparency Engine funciona con datos históricos.

Sprint 3 - Tarea B
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.parsers.multi_file_xbrl_parser import MultiFileXBRLParser
from backend.metrics.profitability.roe import ROE
import json
from datetime import datetime


def test_roe_timeseries_4_years():
    """
    Valida que ROE funciona con datos de 4 años.
    Verifica audit trail completo para cada año.

    Acceptance Criteria:
    - ROE calculado para 4 años (2022-2025)
    - Audit trail completo con XBRL tags
    - JSON exportado con trazabilidad
    - Cálculo reproducible validado
    """
    print("\n" + "="*60)
    print("TEST: ROE Time-Series (4 años)")
    print("="*60)

    # ============================================================
    # PASO 3.1: Cargar 4 años de datos
    # ============================================================
    print("\n[PASO 3.1] Cargando datos históricos...")

    parser = MultiFileXBRLParser(ticker='AAPL')
    timeseries = parser.extract_timeseries(years=4)

    # Validar que tenemos 4 años
    assert len(timeseries) == 4, f"❌ Esperado 4 años, obtenido {len(timeseries)}"
    print(f"✓ Años cargados: {sorted(timeseries.keys())}")

    # ============================================================
    # PASO 3.2: Validar datos mínimos por año
    # ============================================================
    print("\n[PASO 3.2] Validando datos por año...")

    for year in sorted(timeseries.keys()):
        data = timeseries[year]

        # Verificar campos requeridos para ROE
        required_fields = ['NetIncomeLoss', 'StockholdersEquity']

        for field in required_fields:
            assert field in data, f"❌ {year}: Falta campo {field}"
            assert data[field] is not None, f"❌ {year}: Campo {field} es None"

        print(f"✓ {year}: NetIncome=${data['NetIncomeLoss'].raw_value:,.0f}, "
              f"Equity=${data['StockholdersEquity'].raw_value:,.0f}")

    print("\n✅ PASO 3 COMPLETADO: Datos cargados y validados")
    print("="*60)

    # ============================================================
    # PASO 4.1: Calcular ROE para cada año
    # ============================================================
    print("\n[PASO 4.1] Calculando ROE para cada año...")

    roe_results = {}

    for year in sorted(timeseries.keys()):
        data = timeseries[year]

        # Crear ROE metric
        roe_metric = ROE(data)
        result = roe_metric.calculate()

        assert result is not None, f"❌ ROE falló para {year}"
        roe_results[year] = result

        # Mostrar resultado
        print(f"\n{year}: ROE = {result.value:.2f}%")
        print(f"  NetIncome: ${result.get_input_value('NetIncomeLoss'):,.0f}")
        print(f"  Equity: ${result.get_input_value('StockholdersEquity'):,.0f}")
        print(f"  XBRL Tag: {result.get_input_source('NetIncomeLoss').xbrl_tag}")
        print(f"  Context: {result.get_input_source('NetIncomeLoss').context_id}")

    # ============================================================
    # PASO 4.2: Validar Audit Trail Completo
    # ============================================================
    print(f"\n{'='*60}")
    print("[PASO 4.2] Validando audit trail...")

    for year in sorted(timeseries.keys()):
        result = roe_results[year]

        # Obtener audit trail
        audit = result.to_dict()

        # Verificar estructura
        assert 'metric' in audit, f"❌ {year}: Falta 'metric' en audit"
        assert 'value' in audit, f"❌ {year}: Falta 'value' en audit"
        assert 'formula' in audit, f"❌ {year}: Falta 'formula' en audit"
        assert 'inputs' in audit, f"❌ {year}: Falta 'inputs' en audit"
        assert 'metadata' in audit, f"❌ {year}: Falta 'metadata' en audit"

        # Verificar inputs tienen XBRL tags
        for input_name, input_data in audit['inputs'].items():
            assert 'xbrl_tag' in input_data, f"❌ {year}: Falta 'xbrl_tag' en {input_name}"
            assert 'context_id' in input_data, f"❌ {year}: Falta 'context_id' en {input_name}"
            assert 'value' in input_data, f"❌ {year}: Falta 'value' en {input_name}"

        # Verificar reproducibilidad
        def recalc(inputs):
            return (inputs['NetIncomeLoss'] / inputs['StockholdersEquity']) * 100

        assert result.validate_reconstruction(recalc), f"❌ {year}: Cálculo no reproducible"

        print(f"✓ {year}: Audit trail completo y cálculo reproducible")

    # ============================================================
    # PASO 4.3: Análisis de Tendencia
    # ============================================================
    print(f"\n{'='*60}")
    print("[PASO 4.3] Análisis de tendencia...")

    years_sorted = sorted(roe_results.keys())
    roe_values = [roe_results[y].value for y in years_sorted]

    print(f"\n📊 ROE Trend Analysis:")
    print(f"  Years: {years_sorted}")
    print(f"  ROE:   {[f'{v:.2f}%' for v in roe_values]}")

    # Calcular cambio promedio
    if len(roe_values) > 1:
        changes = [roe_values[i] - roe_values[i-1] for i in range(1, len(roe_values))]
        avg_change = sum(changes) / len(changes)
        print(f"  Cambio promedio anual: {avg_change:+.2f}%")

    # ============================================================
    # PASO 4.4: Exportar Audit Trail a JSON
    # ============================================================
    print(f"\n{'='*60}")
    print("[PASO 4.4] Exportando audit trail a JSON...")

    audit_trail_4_years = {
        str(year): result.to_dict()
        for year, result in roe_results.items()
    }

    output_file = 'audit_trail_roe_4_years.json'
    with open(output_file, 'w') as f:
        json.dump(audit_trail_4_years, f, indent=2)

    print(f"✓ Audit trail guardado: {output_file}")

    # ============================================================
    # RESUMEN FINAL
    # ============================================================
    print(f"\n{'='*60}")
    print("✅ PASO 4 COMPLETADO: ROE Time-Series")
    print("="*60)
    print(f"  ✓ 4 años procesados: {years_sorted}")
    print(f"  ✓ ROE calculado con audit trail completo")
    print(f"  ✓ Cálculos reproducibles validados")
    print(f"  ✓ JSON exportado con trazabilidad end-to-end")
    print("="*60)


if __name__ == "__main__":
    test_roe_timeseries_4_years()
