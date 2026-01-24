================================================================================
CROSS-COMPANY VALIDATION REPORT
================================================================================

COVERAGE SUMMARY
--------------------------------------------------------------------------------
Company      Concepts     Coverage     Balance      Status
--------------------------------------------------------------------------------
AAPL         14/15          93.3%     0.0000%      ✅ PASS
MSFT         14/15          93.3%     0.0000%      ✅ PASS
BRK.A        0/15           0.0%     INVALID      ❌ FAIL

MISSING CONCEPTS BY COMPANY
--------------------------------------------------------------------------------

AAPL:
  - InterestExpense

MSFT:
  - InterestExpense

BRK.A:
  - Assets
  - Liabilities
  - Equity
  - CurrentAssets
  - CashAndEquivalents
  - LongTermDebt
  - CurrentLiabilities

SHARED CONCEPTS ACROSS ALL COMPANIES: 0/15
--------------------------------------------------------------------------------

COMPANY-SPECIFIC CONCEPTS (not shared)
--------------------------------------------------------------------------------

AAPL only:
  • Assets
  • CapitalExpenditures
  • CashAndEquivalents
  • CostOfRevenue
  • CurrentAssets
  • CurrentLiabilities
  • Equity
  • GrossProfit
  • Liabilities
  • LongTermDebt
  • NetIncome
  • OperatingCashFlow
  • OperatingIncome
  • Revenue

MSFT only:
  • Assets
  • CapitalExpenditures
  • CashAndEquivalents
  • CostOfRevenue
  • CurrentAssets
  • CurrentLiabilities
  • Equity
  • GrossProfit
  • Liabilities
  • LongTermDebt
  • NetIncome
  • OperatingCashFlow
  • OperatingIncome
  • Revenue

RECOMMENDATION
--------------------------------------------------------------------------------
⚠️  EXPAND TO 53 CONCEPTS

Razones:
  • Coverage promedio insuficiente: 62.2% (target: ≥80%)
  • Balance validation fallida en alguna empresa
  • Baja consistencia cross-company: 0.0% (target: ≥60%)

================================================================================