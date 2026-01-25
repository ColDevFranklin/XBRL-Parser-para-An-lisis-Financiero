"""
FinancialDataFrame: Convierte time-series XBRL → DataFrame vectorizado.

Optimizaciones:
- Extracción vectorizada de raw_values (evita loops)
- Index por año (sorted desc)
- Columnas como float64 (NumPy native)

Author: @franklin
Sprint: 4 - Metrics Optimization
"""

import pandas as pd
import numpy as np
from typing import Dict
from backend.engines.tracked_metric import SourceTrace


class FinancialDataFrame:
    """
    Wrapper para time-series con vectorización automática.

    Usage:
        timeseries = parser.extract_timeseries(years=4)
        df_wrapper = FinancialDataFrame(timeseries)

        # Acceso vectorizado
        revenue_array = df_wrapper['Revenue']  # np.ndarray

        # Cálculo vectorizado
        roe = df_wrapper['NetIncome'] / df_wrapper['Equity']
    """

    def __init__(self, timeseries: Dict[int, Dict[str, SourceTrace]]):
        """
        Args:
            timeseries: Output de XBRLParser.extract_timeseries()
        """
        self._timeseries = timeseries
        self._df = self._build_dataframe()

    def _build_dataframe(self) -> pd.DataFrame:
        """
        Convierte time-series → DataFrame vectorizado.

        O(n*m) donde n=años, m=conceptos
        Pero ejecuta una sola vez (construcción)
        """
        rows = []

        for year in sorted(self._timeseries.keys(), reverse=True):
            year_data = self._timeseries[year]

            # Extraer raw_values vectorizadamente
            row = {
                concept: trace.raw_value
                for concept, trace in year_data.items()
            }
            row['Year'] = year
            rows.append(row)

        # Crear DataFrame con Year como index
        df = pd.DataFrame(rows)
        df.set_index('Year', inplace=True)

        # Convertir todo a float64 (NumPy native)
        df = df.astype('float64', errors='ignore')

        return df

    def __getitem__(self, concept: str) -> np.ndarray:
        """
        Acceso vectorizado a conceptos.

        Returns:
            NumPy array (NO pandas Series)
            → O(1) slicing, O(n) vectorized ops
        """
        if concept not in self._df.columns:
            # Retornar array de NaN si concepto no existe
            return np.full(len(self._df), np.nan)

        return self._df[concept].values  # np.ndarray

    @property
    def years(self) -> np.ndarray:
        """Array de años (sorted desc)."""
        return self._df.index.values

    @property
    def concepts(self) -> list:
        """Lista de conceptos disponibles."""
        return self._df.columns.tolist()

    def get_dataframe(self) -> pd.DataFrame:
        """Expone DataFrame subyacente."""
        return self._df.copy()
