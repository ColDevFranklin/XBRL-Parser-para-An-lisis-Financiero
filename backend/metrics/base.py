# backend/metrics/base.py
"""
BaseMetric: Clase base para todas las métricas financieras.
Implementa el patrón Strategy/Factory para cálculo de métricas.
Author: @franklin
Sprint: 3 - Metrics Factory
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
import logging

from backend.engines.tracked_metric import SourceTrace
from backend.engines.calculated_metric import CalculatedMetric

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseMetric(ABC):
    """
    Clase base abstracta para todas las métricas financieras.

    Design Pattern: Template Method

    Métodos abstractos (deben implementarse):
    - get_required_fields(): Define inputs necesarios
    - get_formula(): Fórmula matemática
    - calculate_value(): Lógica de cálculo

    Métodos opcionales (pueden override):
    - get_unit(): Unidad de medida
    - get_metadata(): Metadata adicional
    - validate_range(): Validación de rango
    """

    def __init__(self, financial_data: Dict[str, SourceTrace]):
        self.financial_data = financial_data
        self._required_fields = self.get_required_fields()
        self.metric_name = self.__class__.__name__

    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """Define qué campos XBRL se necesitan"""
        pass

    @abstractmethod
    def get_formula(self) -> str:
        """Retorna fórmula matemática como string"""
        pass

    @abstractmethod
    def calculate_value(self, inputs: Dict[str, float]) -> float:
        """Calcula el valor de la métrica"""
        pass

    def get_unit(self) -> str:
        """Override para especificar unidad"""
        return ""

    def get_metadata(self) -> Dict:
        """Override para agregar metadata"""
        return {}

    def validate_range(self, value: float) -> bool:
        """Override para validar rango"""
        return True

    def validate_inputs(self) -> bool:
        """Valida que todos los campos requeridos existan"""
        for field in self._required_fields:
            if field not in self.financial_data:
                logger.warning(f"{self.metric_name}: Campo faltante: {field}")
                return False
            if self.financial_data[field] is None:
                logger.warning(f"{self.metric_name}: Campo es None: {field}")
                return False
            trace = self.financial_data[field]
            if not hasattr(trace, 'raw_value'):
                logger.warning(f"{self.metric_name}: Campo sin raw_value: {field}")
                return False
        return True

    def calculate(self) -> Optional[CalculatedMetric]:
        """
        Orquesta el cálculo completo con trazabilidad.

        Returns:
            CalculatedMetric con audit trail o None si falla
        """
        # 1. Validar inputs
        if not self.validate_inputs():
            logger.error(f"{self.metric_name}: Inputs inválidos")
            return None

        # 2. Extraer valores numéricos y traces
        inputs_numeric = {}
        inputs_traces = {}

        for field in self._required_fields:
            trace = self.financial_data[field]
            inputs_numeric[field] = trace.raw_value
            inputs_traces[field] = trace

        # 3. Calcular valor
        try:
            value = self.calculate_value(inputs_numeric)
        except ZeroDivisionError:
            logger.error(f"{self.metric_name}: División por cero")
            return None
        except ValueError as e:
            logger.error(f"{self.metric_name}: Error: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.metric_name}: Error inesperado: {e}")
            return None

        # 4. Validar rango
        if not self.validate_range(value):
            logger.warning(f"{self.metric_name}: Valor fuera de rango: {value}")

        # 5. Crear CalculatedMetric con audit trail
        metric = CalculatedMetric(
            metric_name=self.metric_name,
            value=value,
            formula=self.get_formula(),
            inputs=inputs_traces,
            unit=self.get_unit(),
            metadata=self.get_metadata()
        )

        logger.info(f"{self.metric_name}: Calculado = {value:.2f}{self.get_unit()}")

        return metric

    def __repr__(self) -> str:
        return f"{self.metric_name}(fields={self._required_fields})"


if __name__ == "__main__":
    from backend.engines.tracked_metric import SourceTrace
    from datetime import datetime

    # Definir ROE como ejemplo
    class ROE(BaseMetric):
        def get_required_fields(self):
            return ['NetIncomeLoss', 'StockholdersEquity']

        def get_formula(self):
            return "(NetIncome / Equity) * 100"

        def calculate_value(self, inputs):
            net_income = inputs['NetIncomeLoss']
            equity = inputs['StockholdersEquity']
            if equity == 0:
                raise ValueError("Equity cannot be zero")
            return (net_income / equity) * 100

        def get_unit(self):
            return "%"

        def get_metadata(self):
            return {
                "category": "Profitability",
                "benchmarks": {"excellent": 15.0, "good": 10.0}
            }

        def validate_range(self, value):
            return -100 <= value <= 500

    # Test
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

    print("="*60)
    print("BASE METRIC - EJEMPLO ROE")
    print("="*60)

    roe_metric = ROE(financial_data)
    result = roe_metric.calculate()

    if result:
        print(f"\n✓ Métrica calculada: {result}")
        print(f"\nAudit trail:")
        import json
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print("\n✗ Error calculando métrica")
