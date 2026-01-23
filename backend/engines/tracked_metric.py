# backend/engines/tracked_metric.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class SourceTrace:
    """Metadata de origen de un valor financiero"""
    xbrl_tag: str                    # "us-gaap:NetIncomeLoss"
    raw_value: float                 # 112000000000
    context_id: str                  # "FY2025_Consolidated"
    extracted_at: datetime           # ISO timestamp
    section: str                     # "income_statement"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'xbrl_tag': self.xbrl_tag,
            'raw_value': self.raw_value,
            'context_id': self.context_id,
            'extracted_at': self.extracted_at.isoformat(),
            'section': self.section
        }

@dataclass
class TrackedMetric:
    """Métrica financiera con trazabilidad completa"""
    name: str                        # "ROE"
    value: Optional[float]           # 152.0
    unit: str                        # "percentage"
    formula: str                     # "(Net Income / Equity) * 100"
    inputs: Dict[str, SourceTrace]   # {"net_income": SourceTrace(...), "equity": SourceTrace(...)}
    calculated_at: datetime

    def __repr__(self) -> str:
        if self.value is None:
            return f"{self.name}: N/A"
        return f"{self.name}: {self.value}{self.unit}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'unit': self.unit,
            'formula': self.formula,
            'inputs': {k: v.to_dict() for k, v in self.inputs.items()},
            'calculated_at': self.calculated_at.isoformat()
        }

    def explain(self) -> str:
        """
        Genera explicación legible de la métrica.

        Example:
            ROE: 152.0%
            Formula: (Net Income / Equity) * 100
            Based on:
              - Net Income: $112,000,000,000 (us-gaap:NetIncomeLoss)
              - Equity: $73,700,000,000 (us-gaap:StockholdersEquity)
        """
        if self.value is None:
            return f"{self.name}: N/A (calculation failed)"

        lines = [
            f"{self.name}: {self.value}{self.unit}",
            f"Formula: {self.formula}",
            "Based on:"
        ]

        for input_name, trace in self.inputs.items():
            lines.append(
                f"  - {input_name.replace('_', ' ').title()}: "
                f"${trace.raw_value:,.0f} ({trace.xbrl_tag})"
            )

        return "\n".join(lines)
