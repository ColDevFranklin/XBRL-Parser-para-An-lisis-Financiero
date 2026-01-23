# backend/tests/test_xbrl_parser_timeseries.py

"""
Tests para validar extract_timeseries() - Sprint 2 Final

Author: @franklin
Sprint: 2 - Time-Series Extraction
"""

import pytest
from backend.parsers.xbrl_parser import XBRLParser
from backend.engines.tracked_metric import SourceTrace


class TestTimeSeriesExtraction:
    """Suite de tests para extracción multi-year"""

    @pytest.fixture
    def parser(self):
        """Parser inicializado con Apple 10-K"""
        parser = XBRLParser('data/apple_10k_xbrl.xml')
        success = parser.load()
        assert success, "Failed to load XBRL file"
        return parser

    def test_extract_timeseries_returns_multiple_years(self, parser):
        """Debe retornar datos de múltiples años"""
        timeseries = parser.extract_timeseries(years=4)

        assert len(timeseries) >= 3, "Expected at least 3 years of data"
        assert 2025 in timeseries, "Missing fiscal year 2025"
        assert isinstance(timeseries, dict), "Should return dict"

    def test_timeseries_years_are_integers(self, parser):
        """Claves deben ser años (integers)"""
        timeseries = parser.extract_timeseries(years=3)

        for year in timeseries.keys():
            assert isinstance(year, int), f"Year {year} should be int"
            assert 2020 <= year <= 2030, f"Year {year} out of reasonable range"

    def test_timeseries_data_structure(self, parser):
        """Cada año debe tener campos completos"""
        timeseries = parser.extract_timeseries(years=3)

        for year, data in timeseries.items():
            # Balance Sheet
            assert 'Assets' in data, f"{year} missing Assets"
            assert 'Liabilities' in data, f"{year} missing Liabilities"
            assert 'StockholdersEquity' in data, f"{year} missing Equity"

            # Income Statement
            assert 'Revenues' in data, f"{year} missing Revenues"
            assert 'NetIncomeLoss' in data, f"{year} missing NetIncome"

    def test_timeseries_returns_source_traces(self, parser):
        """Valores deben ser SourceTrace objects"""
        timeseries = parser.extract_timeseries(years=2)

        for year, data in timeseries.items():
            for field, value in data.items():
                assert isinstance(value, SourceTrace), \
                    f"{year}.{field} should be SourceTrace, got {type(value)}"

                # Validar estructura SourceTrace
                assert hasattr(value, 'raw_value')
                assert hasattr(value, 'xbrl_tag')
                assert hasattr(value, 'context_id')
                assert isinstance(value.raw_value, (int, float))

    def test_balance_equation_holds_all_years(self, parser):
        """Balance sheet debe cuadrar para todos los años"""
        timeseries = parser.extract_timeseries(years=4)

        for year, data in timeseries.items():
            if all(k in data for k in ['Assets', 'Liabilities', 'StockholdersEquity']):
                assets = data['Assets'].raw_value
                liabilities = data['Liabilities'].raw_value
                equity = data['StockholdersEquity'].raw_value

                diff = abs(assets - (liabilities + equity))
                diff_pct = (diff / assets) * 100

                assert diff_pct < 1.0, (
                    f"Balance equation failed for {year}: "
                    f"{diff_pct:.2f}% difference (max 1%)"
                )

    def test_raises_error_if_not_loaded(self):
        """Debe fallar si no se llamó load() primero"""
        parser = XBRLParser('data/apple_10k_xbrl.xml')
        # NO llamar parser.load()

        with pytest.raises(ValueError, match="ContextManager not initialized"):
            parser.extract_timeseries()

    def test_respects_years_parameter(self, parser):
        """Debe respetar el parámetro years"""
        timeseries_2 = parser.extract_timeseries(years=2)
        timeseries_4 = parser.extract_timeseries(years=4)

        assert len(timeseries_2) <= 2, "Should limit to 2 years"
        assert len(timeseries_4) <= 4, "Should limit to 4 years"

    def test_years_in_descending_order(self, parser):
        """Años deben estar en orden descendente (2025, 2024, 2023...)"""
        timeseries = parser.extract_timeseries(years=4)
        years = list(timeseries.keys())

        assert years == sorted(years, reverse=True), \
            "Years should be in descending order"

    def test_revenue_values_reasonable(self, parser):
        """Valores de Revenue deben estar en rango razonable"""
        timeseries = parser.extract_timeseries(years=3)

        for year, data in timeseries.items():
            if 'Revenues' in data:
                revenue = data['Revenues'].raw_value

                # Apple revenue debería ser >$200B
                assert revenue > 200_000_000_000, \
                    f"{year} revenue {revenue:,.0f} seems too low"

                # Pero <$1T (sanity check)
                assert revenue < 1_000_000_000_000, \
                    f"{year} revenue {revenue:,.0f} seems too high"

    def test_performance_under_5_seconds(self, parser):
        """Extracción debe completar en <5 segundos"""
        import time

        start = time.time()
        timeseries = parser.extract_timeseries(years=4)
        elapsed = time.time() - start

        assert elapsed < 5.0, \
            f"Extraction took {elapsed:.2f}s (max 5s)"

    def test_context_ids_differ_between_years(self, parser):
        """Cada año debe usar contextos diferentes"""
        timeseries = parser.extract_timeseries(years=3)

        # Recopilar context_ids por año
        contexts_by_year = {}
        for year, data in timeseries.items():
            if 'Assets' in data:
                contexts_by_year[year] = data['Assets'].context_id

        # Al menos 2 años deben tener contextos diferentes
        unique_contexts = set(contexts_by_year.values())
        assert len(unique_contexts) >= 2, \
            "Expected different context IDs for different years"
