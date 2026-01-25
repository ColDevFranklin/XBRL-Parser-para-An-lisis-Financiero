"""
ParallelMetricsEngine: Ejecuta categorías de métricas en paralelo.

Optimizaciones:
- ThreadPoolExecutor (4 workers)
- I/O-bound eliminated (todo en memoria)
- Expected speedup: ~3x

Author: @franklin
Sprint: 4 - Metrics Optimization
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict
import numpy as np
from backend.metrics.metrics_calculator import MetricsCalculator


class ParallelMetricsEngine:
    """
    Ejecuta cálculo de métricas en paralelo por categoría.

    Categories:
    1. Profitability → Thread 1
    2. Liquidity     → Thread 2
    3. Efficiency    → Thread 3
    4. Leverage      → Thread 4

    Usage:
        engine = ParallelMetricsEngine(calculator)
        results = engine.calculate_all()

        # Output:
        # {
        #   'profitability': {'ROE': array([...]), ...},
        #   'liquidity': {'CurrentRatio': array([...]), ...},
        #   ...
        # }
    """

    def __init__(self, calculator: MetricsCalculator, max_workers: int = 4):
        """
        Args:
            calculator: MetricsCalculator instance
            max_workers: Número de threads (default: 4)
        """
        self.calc = calculator
        self.max_workers = max_workers

    def _calculate_profitability(self) -> Dict[str, np.ndarray]:
        """
        Calcula 8 ratios de rentabilidad.

        Thread-safe (cada thread tiene su propio scope)
        """
        return {
            'ROE': self.calc.return_on_equity(),
            'ROA': self.calc.return_on_assets(),
            'NetMargin': self.calc.net_margin(),
            'GrossMargin': self.calc.gross_margin(),
            'OperatingMargin': self.calc.operating_margin(),
            'ROIC': self.calc.return_on_invested_capital(),
            'EPS': self.calc.earnings_per_share_proxy(),
            'OCFMargin': self.calc.operating_cash_flow_margin(),
        }

    def _calculate_liquidity(self) -> Dict[str, np.ndarray]:
        """
        Calcula 5 ratios de liquidez.
        """
        return {
            'CurrentRatio': self.calc.current_ratio(),
            'QuickRatio': self.calc.quick_ratio(),
            'CashRatio': self.calc.cash_ratio(),
            'WorkingCapital': self.calc.working_capital(),
            'OCFRatio': self.calc.operating_cash_flow_ratio(),
        }

    def _calculate_efficiency(self) -> Dict[str, np.ndarray]:
        """
        Calcula 6 ratios de eficiencia.
        """
        return {
            'AssetTurnover': self.calc.asset_turnover(),
            'InventoryTurnover': self.calc.inventory_turnover(),
            'DIO': self.calc.days_inventory_outstanding(),
            'ReceivablesTurnover': self.calc.receivables_turnover(),
            'DSO': self.calc.days_sales_outstanding(),
            'CCC': self.calc.cash_conversion_cycle(),
        }

    def _calculate_leverage(self) -> Dict[str, np.ndarray]:
        """
        Calcula 6 ratios de apalancamiento.
        """
        return {
            'DebtToEquity': self.calc.debt_to_equity(),
            'DebtToAssets': self.calc.debt_to_assets(),
            'EquityMultiplier': self.calc.equity_multiplier(),
            'InterestCoverage': self.calc.interest_coverage(),
            'DSCR': self.calc.debt_service_coverage(),
            'TotalDebtRatio': self.calc.total_debt_ratio(),
        }

    def calculate_all(self) -> Dict[str, Dict[str, np.ndarray]]:
        """
        Calcula TODAS las métricas en paralelo.

        Returns:
            {
                'profitability': {'ROE': array([...]), ...},
                'liquidity': {...},
                'efficiency': {...},
                'leverage': {...}
            }

        Performance:
            Sequential: ~100ms (25 ratios × 4ms)
            Parallel:   ~30ms (4 categories × 7.5ms)
            Speedup:    ~3.3x
        """
        # Mapeo de categorías → funciones
        tasks = {
            'profitability': self._calculate_profitability,
            'liquidity': self._calculate_liquidity,
            'efficiency': self._calculate_efficiency,
            'leverage': self._calculate_leverage,
        }

        results = {}

        # Ejecutar en paralelo
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_category = {
                executor.submit(func): category
                for category, func in tasks.items()
            }

            # Collect results as they complete
            for future in as_completed(future_to_category):
                category = future_to_category[future]

                try:
                    results[category] = future.result()
                except Exception as e:
                    print(f"✗ Error en categoría {category}: {e}")
                    results[category] = {}

        return results

    def calculate_category(self, category: str) -> Dict[str, np.ndarray]:
        """
        Calcula UNA categoría específica (sin paralelización).

        Args:
            category: 'profitability', 'liquidity', 'efficiency', 'leverage'

        Returns:
            Dict con ratios de la categoría
        """
        if category == 'profitability':
            return self._calculate_profitability()
        elif category == 'liquidity':
            return self._calculate_liquidity()
        elif category == 'efficiency':
            return self._calculate_efficiency()
        elif category == 'leverage':
            return self._calculate_leverage()
        else:
            raise ValueError(f"Categoría inválida: {category}")
