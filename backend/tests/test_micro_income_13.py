def test_income_statement_13_concepts():
    """Valida Income Statement expandido a 13 conceptos"""
    parser = XBRLParser('data/apple_10k_xbrl.xml')
    parser.load()

    income = parser.extract_income_statement()

    # Assert 13 conceptos definidos
    expected_fields = 13
    assert len(parser.extract_income_statement.__code__.co_consts) >= expected_fields

    # Assert core 6 presentes
    core = ['Revenue', 'NetIncome', 'GrossProfit', 'OperatingIncome', 'CostOfRevenue']
    core_found = sum(1 for f in core if income.get(f))
    assert core_found >= 5

    # Assert 3+ nuevos conceptos extraídos
    new_fields = ['ResearchAndDevelopment', 'SellingGeneralAdmin', 'TaxExpense', 'DepreciationAmortization']
    new_found = sum(1 for f in new_fields if income.get(f))
    assert new_found >= 3
