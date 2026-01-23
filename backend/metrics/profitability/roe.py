# backend/metrics/profitability/roe.py
"""
ROE (Return on Equity) - Métrica de rentabilidad con trazabilidad completa.

Mide la capacidad de generar utilidad a partir del capital de accionistas.

Author: @franklin
Sprint: 3 - Metrics Implementation
Category: Profitability
"""

import sys
import os
from typing import Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from backend.metrics.base import BaseMetric


class ROE(BaseMetric):
    """
    Return on Equity (ROE) con trazabilidad completa.

    Formula: (Net Income / Stockholders Equity) * 100

    Interpretation:
        - >20%: Excepcional (elite companies)
        - 15-20%: Excelente (tech/growth)
        - 10-15%: Bueno (most industries)
        - 5-10%: Aceptable
        - <5%: Pobre
        - Negativo: Pérdidas

    Benchmarks by Industry:
        - Technology: 15-25%
        - Financial Services: 10-15%
        - Consumer Goods: 12-18%
        - Utilities: 8-12%
        - Retail: 15-20%

    Red Flags:
        - ROE >50%: Posible apalancamiento excesivo
        - ROE <0%: Pérdidas o equity negativo
        - ROE muy volátil año a año

    Apple Example (FY 2024):
        Input:
            NetIncome: $93,736,000,000
            Equity: $62,146,000,000
        Calculation:
            ROE = (93,736,000,000 / 62,146,000,000) * 100 = 150.79%
        Interpretation:
            Apple's exceptional ROE reflects high profitability,
            efficient capital structure, and aggressive buybacks.
    """

    def get_required_fields(self) -> list:
        return ['NetIncomeLoss', 'StockholdersEquity']

    def get_formula(self) -> str:
        return "(NetIncome / Equity) * 100"

    def calculate_value(self, inputs: Dict[str, float]) -> float:
        net_income = inputs['NetIncomeLoss']
        equity = inputs['StockholdersEquity']

        if equity == 0:
            raise ValueError("Stockholders Equity cannot be zero")

        return (net_income / equity) * 100

    def get_unit(self) -> str:
        return "%"

    def get_metadata(self) -> Dict:
        return {
            "category": "Profitability",
            "subcategory": "Return Metrics",
            "benchmarks": {
                "exceptional": 20.0,
                "excellent": 15.0,
                "good": 10.0,
                "acceptable": 5.0,
                "poor": 0.0
            },
            "industry_benchmarks": {
                "Technology": {"excellent": 20.0, "good": 15.0},
                "Financial Services": {"excellent": 15.0, "good": 10.0},
                "Consumer Goods": {"excellent": 18.0, "good": 12.0},
                "Utilities": {"excellent": 12.0, "good": 8.0},
                "Retail": {"excellent": 20.0, "good": 15.0}
            },
            "interpretation": {
                "high": "Strong profitability and efficient use of equity",
                "low": "Weak profitability or inefficient capital structure",
                "negative": "Company operating at a loss"
            },
            "red_flags": {
                "excessive": 50.0,
                "minimum": -10.0
            },
            "related_metrics": ["ROA", "ROIC", "NetMargin"],
            "formula_components": {
                "numerator": "Net Income (after taxes)",
                "denominator": "Average Stockholders Equity"
            },
            "notes": [
                "High ROE can result from low equity (high leverage)",
                "Compare with ROA to assess leverage impact",
                "Best analyzed as 5-year trend, not single year"
            ]
        }

    def validate_range(self, value: float) -> bool:
        return -200.0 <= value <= 500.0


if __name__ == "__main__":
    from backend.engines.tracked_metric import SourceTrace
    from datetime import datetime
    import json

    print("="*60)
    print("ROE METRIC - TEST CON APPLE FY2024")
    print("="*60)

    # Datos reales Apple FY2024
    financial_data = {
        'NetIncomeLoss': SourceTrace(
            xbrl_tag="us-gaap:NetIncomeLoss",
            raw_value=93_736_000_000.0,
            context_id="c-1",
            extracted_at=datetime.now(),
            section="income_statement"
        ),
        'StockholdersEquity': SourceTrace(
            xbrl_tag="us-gaap:StockholdersEquity",
            raw_value=62_146_000_000.0,
            context_id="c-20",
            extracted_at=datetime.now(),
            section="balance_sheet"
        )
    }

    # Calcular ROE
    roe_metric = ROE(financial_data)
    result = roe_metric.calculate()

    if result:
        print(f"\n✓ ROE Calculado: {result.value:.2f}%")
        print(f"  Formula: {result.formula}")
        print(f"  Unit: {result.unit}")

        print("\n--- Inputs ---")
        print(f"  Net Income: ${result.get_input_value('NetIncomeLoss'):,.0f}")
        print(f"  Equity: ${result.get_input_value('StockholdersEquity'):,.0f}")

        print("\n--- XBRL Tags ---")
        for name, tag in result.list_input_tags().items():
            print(f"  {name}: {tag}")

        print("\n--- Interpretation ---")
        if result.value > 20:
            print("  ✓ EXCEPCIONAL: Elite company performance")
        elif result.value > 15:
            print("  ✓ EXCELENTE: Strong profitability")
        elif result.value > 10:
            print("  ✓ BUENO: Healthy returns")
        else:
            print("  ⚠️  REVISAR: Below industry average")

        print("\n--- Audit Trail Completo (JSON) ---")
        print(json.dumps(result.to_dict(), indent=2))

        print("\n--- Validation ---")
        def recalc(inputs):
            return (inputs['NetIncomeLoss'] / inputs['StockholdersEquity']) * 100

        valid = result.validate_reconstruction(recalc)
        print(f"  Cálculo reproducible: {'✓' if valid else '✗'}")

        print("\n" + "="*60)
        print("✅ ROE METRIC TEST COMPLETADO")
        print("="*60)
    else:
        print("\n✗ Error calculando ROE")
