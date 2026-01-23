# backend/engines/calculated_metric.py
"""
CalculatedMetric: Métrica calculada con trazabilidad completa (audit trail).
Author: @franklin
Sprint: 3 - Metrics Factory + Transparency
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
from backend.engines.tracked_metric import SourceTrace


@dataclass
class CalculatedMetric:
    """
    Métrica calculada con trazabilidad completa (audit trail).

    Encapsula resultado de cálculo financiero con:
    - Fórmula utilizada
    - Inputs originales (SourceTrace)
    - Timestamp del cálculo
    - Metadata adicional
    """

    metric_name: str
    value: float
    formula: str
    inputs: Dict[str, SourceTrace]
    unit: str = ""
    calculated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a dict para JSON/API/Dashboard"""
        return {
            "metric": self.metric_name,
            "value": round(self.value, 2),
            "formula": self.formula,
            "unit": self.unit,
            "calculated_at": self.calculated_at.isoformat(),
            "inputs": {
                name: {
                    "value": trace.raw_value,
                    "xbrl_tag": trace.xbrl_tag,
                    "context_id": trace.context_id,
                    "section": trace.section,
                    "extracted_at": trace.extracted_at.isoformat()
                }
                for name, trace in self.inputs.items()
            },
            "metadata": self.metadata
        }

    def to_json_compact(self) -> Dict[str, Any]:
        """Versión compacta sin audit trail"""
        return {
            "metric": self.metric_name,
            "value": round(self.value, 2),
            "unit": self.unit
        }

    def get_input_source(self, input_name: str) -> Optional[SourceTrace]:
        """Retorna SourceTrace de un input específico"""
        return self.inputs.get(input_name)

    def get_input_value(self, input_name: str) -> Optional[float]:
        """Retorna valor numérico de un input"""
        trace = self.get_input_source(input_name)
        return trace.raw_value if trace else None

    def list_input_tags(self) -> Dict[str, str]:
        """Lista todos los tags XBRL usados"""
        return {
            name: trace.xbrl_tag
            for name, trace in self.inputs.items()
        }

    def validate_reconstruction(self, recalculate_fn) -> bool:
        """Valida que el cálculo sea reproducible"""
        input_values = {
            name: trace.raw_value
            for name, trace in self.inputs.items()
        }
        try:
            recalculated = recalculate_fn(input_values)
            diff = abs(self.value - recalculated)
            return diff < 0.01
        except Exception:
            return False

    def __repr__(self) -> str:
        return (
            f"CalculatedMetric(metric='{self.metric_name}', "
            f"value={self.value:.2f}{self.unit}, "
            f"inputs={list(self.inputs.keys())})"
        )

    def __str__(self) -> str:
        return f"{self.metric_name}: {self.value:.2f}{self.unit}"


if __name__ == "__main__":
    from backend.engines.tracked_metric import SourceTrace

    # Test con datos simulados
    net_income_trace = SourceTrace(
        xbrl_tag="us-gaap:NetIncomeLoss",
        raw_value=93_736_000_000.0,
        context_id="c-1",
        extracted_at=datetime.now(),
        section="income_statement"
    )

    equity_trace = SourceTrace(
        xbrl_tag="us-gaap:StockholdersEquity",
        raw_value=62_146_000_000.0,
        context_id="c-20",
        extracted_at=datetime.now(),
        section="balance_sheet"
    )

    roe_value = (net_income_trace.raw_value / equity_trace.raw_value) * 100

    roe = CalculatedMetric(
        metric_name="ROE",
        value=roe_value,
        formula="(NetIncome / Equity) * 100",
        inputs={
            "NetIncome": net_income_trace,
            "Equity": equity_trace
        },
        unit="%",
        metadata={
            "category": "Profitability",
            "benchmarks": {"excellent": 15.0, "good": 10.0}
        }
    )

    print("="*60)
    print("CALCULATED METRIC - EJEMPLO")
    print("="*60)
    print(f"\n{roe}")

    print("\n--- Audit Trail ---")
    import json
    print(json.dumps(roe.to_dict(), indent=2))

    print("\n--- Input Sources ---")
    for name in roe.inputs.keys():
        source = roe.get_input_source(name)
        print(f"{name}: {source.xbrl_tag} @ {source.context_id}")

    print("\n--- Validación ---")
    def recalc(inputs):
        return (inputs['NetIncome'] / inputs['Equity']) * 100

    valid = roe.validate_reconstruction(recalc)
    print(f"Cálculo reproducible: {valid}")
