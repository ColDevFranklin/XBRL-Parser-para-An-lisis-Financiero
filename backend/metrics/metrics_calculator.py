"""
MetricsCalculator: Calcula 25 ratios financieros con memoización y vectorización.

Optimizaciones:
- @lru_cache para base metrics (NetIncome usado en ROE, ROA, Margin)
- Vectorized operations (evita loops Python)
- Lazy evaluation (calcula solo lo solicitado)

Author: @franklin
Sprint: 4 - Metrics Optimization
"""

import numpy as np
from functools import lru_cache
from typing import Dict, Optional
from backend.metrics.financial_dataframe import FinancialDataFrame


class MetricsCalculator:
    """
    Calcula ratios financieros con vectorización y memoización.

    Features:
    - Base metrics memoizados (NetIncome, Revenue, Assets, etc.)
    - Vectorized calculations (O(1) broadcast)
    - Division-by-zero safe (retorna NaN)

    Usage:
        calc = MetricsCalculator(df_wrapper)

        # Memoizado - 1a llamada extrae, 2a-N usa cache
        roe = calc.return_on_equity()
        roa = calc.return_on_assets()  # Reusa NetIncome (memoizado)
        net_margin = calc.net_margin()  # Reusa NetIncome (memoizado)
    """

    def __init__(self, df: FinancialDataFrame):
        """
        Args:
            df: FinancialDataFrame wrapper
        """
        self.df = df

        # Cache explícito (además de @lru_cache)
        self._cache = {}

    # ========================================================================
    # BASE METRICS (Memoizados)
    # ========================================================================

    @lru_cache(maxsize=128)
    def _get_concept(self, name: str) -> np.ndarray:
        """
        Extrae concepto con memoización.

        Cache hit: O(1)
        Cache miss: O(n) - acceso a DataFrame

        Returns:
            NumPy array de valores
        """
        return self.df[name]

    # ========================================================================
    # CATEGORY 1: PROFITABILITY (8 ratios)
    # ========================================================================

    def return_on_equity(self) -> np.ndarray:
        """
        ROE = NetIncome / Equity

        Vectorizado: O(1) broadcast division
        Memoizado: NetIncome extraído 1 sola vez
        """
        net_income = self._get_concept('NetIncome')
        equity = self._get_concept('Equity')

        # Division-by-zero safe (retorna NaN)
        with np.errstate(divide='ignore', invalid='ignore'):
            roe = net_income / equity

        return roe

    def return_on_assets(self) -> np.ndarray:
        """
        ROA = NetIncome / Assets

        Reusa NetIncome (memoizado)
        """
        net_income = self._get_concept('NetIncome')
        assets = self._get_concept('Assets')

        with np.errstate(divide='ignore', invalid='ignore'):
            roa = net_income / assets

        return roa

    def net_margin(self) -> np.ndarray:
        """
        Net Margin = NetIncome / Revenue

        Reusa NetIncome (memoizado)
        """
        net_income = self._get_concept('NetIncome')
        revenue = self._get_concept('Revenue')

        with np.errstate(divide='ignore', invalid='ignore'):
            margin = net_income / revenue

        return margin

    def gross_margin(self) -> np.ndarray:
        """
        Gross Margin = GrossProfit / Revenue
        """
        gross_profit = self._get_concept('GrossProfit')
        revenue = self._get_concept('Revenue')

        with np.errstate(divide='ignore', invalid='ignore'):
            margin = gross_profit / revenue

        return margin

    def operating_margin(self) -> np.ndarray:
        """
        Operating Margin = OperatingIncome / Revenue
        """
        operating_income = self._get_concept('OperatingIncome')
        revenue = self._get_concept('Revenue')

        with np.errstate(divide='ignore', invalid='ignore'):
            margin = operating_income / revenue

        return margin

    def return_on_invested_capital(self) -> np.ndarray:
        """
        ROIC = OperatingIncome / (Equity + LongTermDebt)
        """
        operating_income = self._get_concept('OperatingIncome')
        equity = self._get_concept('Equity')
        long_term_debt = self._get_concept('LongTermDebt')

        invested_capital = equity + long_term_debt

        with np.errstate(divide='ignore', invalid='ignore'):
            roic = operating_income / invested_capital

        return roic

    def earnings_per_share_proxy(self) -> np.ndarray:
        """
        EPS Proxy = NetIncome / 1 (placeholder)

        NOTA: EPS real requiere SharesOutstanding
        Este es un proxy simplificado
        """
        return self._get_concept('NetIncome')

    def operating_cash_flow_margin(self) -> np.ndarray:
        """
        OCF Margin = OperatingCashFlow / Revenue
        """
        ocf = self._get_concept('OperatingCashFlow')
        revenue = self._get_concept('Revenue')

        with np.errstate(divide='ignore', invalid='ignore'):
            margin = ocf / revenue

        return margin

    # ========================================================================
    # CATEGORY 2: LIQUIDITY (5 ratios)
    # ========================================================================

    def current_ratio(self) -> np.ndarray:
        """
        Current Ratio = CurrentAssets / CurrentLiabilities
        """
        current_assets = self._get_concept('CurrentAssets')
        current_liabilities = self._get_concept('CurrentLiabilities')

        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = current_assets / current_liabilities

        return ratio

    def quick_ratio(self) -> np.ndarray:
        """
        Quick Ratio = (CurrentAssets - Inventory) / CurrentLiabilities
        """
        current_assets = self._get_concept('CurrentAssets')
        inventory = self._get_concept('Inventory')
        current_liabilities = self._get_concept('CurrentLiabilities')

        quick_assets = current_assets - inventory

        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = quick_assets / current_liabilities

        return ratio

    def cash_ratio(self) -> np.ndarray:
        """
        Cash Ratio = CashAndEquivalents / CurrentLiabilities
        """
        cash = self._get_concept('CashAndEquivalents')
        current_liabilities = self._get_concept('CurrentLiabilities')

        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = cash / current_liabilities

        return ratio

    def working_capital(self) -> np.ndarray:
        """
        Working Capital = CurrentAssets - CurrentLiabilities
        """
        current_assets = self._get_concept('CurrentAssets')
        current_liabilities = self._get_concept('CurrentLiabilities')

        return current_assets - current_liabilities

    def operating_cash_flow_ratio(self) -> np.ndarray:
        """
        OCF Ratio = OperatingCashFlow / CurrentLiabilities
        """
        ocf = self._get_concept('OperatingCashFlow')
        current_liabilities = self._get_concept('CurrentLiabilities')

        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = ocf / current_liabilities

        return ratio

    # ========================================================================
    # CATEGORY 3: EFFICIENCY (6 ratios)
    # ========================================================================

    def asset_turnover(self) -> np.ndarray:
        """
        Asset Turnover = Revenue / Assets
        """
        revenue = self._get_concept('Revenue')
        assets = self._get_concept('Assets')

        with np.errstate(divide='ignore', invalid='ignore'):
            turnover = revenue / assets

        return turnover

    def inventory_turnover(self) -> np.ndarray:
        """
        Inventory Turnover = CostOfRevenue / Inventory
        """
        cogs = self._get_concept('CostOfRevenue')
        inventory = self._get_concept('Inventory')

        with np.errstate(divide='ignore', invalid='ignore'):
            turnover = cogs / inventory

        return turnover

    def days_inventory_outstanding(self) -> np.ndarray:
        """
        DIO = 365 / Inventory Turnover
        """
        inventory_turnover = self.inventory_turnover()

        with np.errstate(divide='ignore', invalid='ignore'):
            dio = 365 / inventory_turnover

        return dio

    def receivables_turnover(self) -> np.ndarray:
        """
        Receivables Turnover = Revenue / AccountsReceivable
        """
        revenue = self._get_concept('Revenue')
        ar = self._get_concept('AccountsReceivable')

        with np.errstate(divide='ignore', invalid='ignore'):
            turnover = revenue / ar

        return turnover

    def days_sales_outstanding(self) -> np.ndarray:
        """
        DSO = 365 / Receivables Turnover
        """
        receivables_turnover = self.receivables_turnover()

        with np.errstate(divide='ignore', invalid='ignore'):
            dso = 365 / receivables_turnover

        return dso

    def cash_conversion_cycle(self) -> np.ndarray:
        """
        CCC = DIO + DSO - DPO

        NOTA: DPO requiere AccountsPayable (no disponible)
        Simplificado: DIO + DSO
        """
        dio = self.days_inventory_outstanding()
        dso = self.days_sales_outstanding()

        return dio + dso

    # ========================================================================
    # CATEGORY 4: LEVERAGE (6 ratios)
    # ========================================================================

    def debt_to_equity(self) -> np.ndarray:
        """
        Debt/Equity = LongTermDebt / Equity
        """
        debt = self._get_concept('LongTermDebt')
        equity = self._get_concept('Equity')

        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = debt / equity

        return ratio

    def debt_to_assets(self) -> np.ndarray:
        """
        Debt/Assets = LongTermDebt / Assets
        """
        debt = self._get_concept('LongTermDebt')
        assets = self._get_concept('Assets')

        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = debt / assets

        return ratio

    def equity_multiplier(self) -> np.ndarray:
        """
        Equity Multiplier = Assets / Equity
        """
        assets = self._get_concept('Assets')
        equity = self._get_concept('Equity')

        with np.errstate(divide='ignore', invalid='ignore'):
            multiplier = assets / equity

        return multiplier

    def interest_coverage(self) -> np.ndarray:
        """
        Interest Coverage = OperatingIncome / InterestExpense
        """
        operating_income = self._get_concept('OperatingIncome')
        interest_expense = self._get_concept('InterestExpense')

        with np.errstate(divide='ignore', invalid='ignore'):
            coverage = operating_income / interest_expense

        return coverage

    def debt_service_coverage(self) -> np.ndarray:
        """
        DSCR = OperatingCashFlow / (InterestExpense + Principal)

        NOTA: Principal payments no disponibles en XBRL
        Simplificado: OCF / InterestExpense
        """
        ocf = self._get_concept('OperatingCashFlow')
        interest_expense = self._get_concept('InterestExpense')

        with np.errstate(divide='ignore', invalid='ignore'):
            coverage = ocf / interest_expense

        return coverage

    def total_debt_ratio(self) -> np.ndarray:
        """
        Total Debt Ratio = Liabilities / Assets
        """
        liabilities = self._get_concept('Liabilities')
        assets = self._get_concept('Assets')

        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = liabilities / assets

        return ratio
