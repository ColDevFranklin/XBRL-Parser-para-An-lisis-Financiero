"""
Financial Metrics Module - API Pública

Optimizaciones implementadas:
- Vectorización NumPy/Pandas (evita loops Python)
- Memoización con @lru_cache (NetIncome usado 1 vez)
- Paralelización automática (solo para datasets grandes)

Usage:
    from backend.metrics import calculate_metrics

    timeseries = parser.extract_timeseries(years=4)
    metrics = calculate_metrics(timeseries)  # Auto-detect: sequential

    # Para 20 años → auto usa parallel
    timeseries_large = parser.extract_timeseries(years=20)
    metrics = calculate_metrics(timeseries_large)  # Auto-detect: parallel

    print(metrics['profitability']['ROE'])  # array([0.31, 0.28, ...])

Author: @franklin
Sprint: 4 - Metrics Optimization with Auto-Detection
"""

from backend.metrics.financial_dataframe import FinancialDataFrame
from backend.metrics.metrics_calculator import MetricsCalculator
from backend.metrics.parallel_engine import ParallelMetricsEngine
from typing import Dict
import numpy as np


def calculate_metrics(
    timeseries: Dict,
    parallel: str = 'auto',
    max_workers: int = 4
) -> Dict[str, Dict[str, np.ndarray]]:
    """
    API principal: Calcula 25 métricas financieras optimizadas.

    Args:
        timeseries: Output de XBRLParser.extract_timeseries()
        parallel: Modo de ejecución
            - 'auto' (default): Sequential si <10 años, parallel si ≥10
            - 'force': Siempre parallel (para debugging/benchmarking)
            - 'never': Siempre sequential
        max_workers: Número de threads (si parallel=True), default=4

    Returns:
        {
            'profitability': {'ROE': array([...]), 'ROA': array([...]), ...},
            'liquidity': {'CurrentRatio': array([...]), ...},
            'efficiency': {'AssetTurnover': array([...]), ...},
            'leverage': {'DebtToEquity': array([...]), ...}
        }

    Notes:
        - Auto-detection usa threshold de 10 años
        - Para <10 años: sequential es más rápido (evita threading overhead)
        - Para ≥10 años: parallel compensa overhead con paralelismo

    Example:
        >>> # Single company, 4 años → auto usa sequential
        >>> parser = MultiFileXBRLParser(ticker='AAPL')
        >>> timeseries = parser.extract_timeseries(years=4)
        >>> metrics = calculate_metrics(timeseries)
        >>>
        >>> # ROE para todos los años
        >>> print(metrics['profitability']['ROE'])
        [0.312 0.283 0.267 0.256]
        >>>
        >>> # Force parallel mode (debugging)
        >>> metrics = calculate_metrics(timeseries, parallel='force')
    """
    # Paso 1: Convertir a DataFrame vectorizado
    df = FinancialDataFrame(timeseries)

    # Paso 2: Crear calculator con memoización
    calculator = MetricsCalculator(df)

    # Paso 3: Auto-detection de parallel mode
    num_years = len(timeseries)

    use_parallel = False
    if parallel == 'auto':
        # Threshold: 10 años
        # Basado en benchmarks: overhead ~0.3ms, beneficio ~0.02ms/año
        # Break-even: 0.3ms / 0.02ms = 15 años
        # Usamos 10 como margen de seguridad
        use_parallel = num_years >= 10
    elif parallel == 'force':
        use_parallel = True
    elif parallel == 'never':
        use_parallel = False
    else:
        raise ValueError(f"Invalid parallel mode: {parallel}. Use 'auto', 'force', or 'never'")

    # Paso 4: Ejecutar cálculos
    engine = ParallelMetricsEngine(calculator, max_workers=max_workers)

    if use_parallel:
        return engine.calculate_all()
    else:
        # Sequential mode (evita threading overhead)
        return {
            'profitability': engine._calculate_profitability(),
            'liquidity': engine._calculate_liquidity(),
            'efficiency': engine._calculate_efficiency(),
            'leverage': engine._calculate_leverage(),
        }


__all__ = [
    'calculate_metrics',
    'FinancialDataFrame',
    'MetricsCalculator',
    'ParallelMetricsEngine',
]
