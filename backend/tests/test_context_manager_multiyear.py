# backend/tests/test_context_manager_multiyear.py

"""
Tests para ContextManager con soporte multi-year.
"""
import sys
sys.path.insert(0, '/home/h4ckio/Documentos/projects')
from backend.parsers.xbrl_parser import XBRLParser
import pytest


class TestContextManagerMultiYear:
    """Tests para detección multi-year"""

    def test_apple_detects_multiple_years(self):
        """Apple 10-K debe tener al menos 2 años de datos"""
        parser = XBRLParser('data/apple_10k_xbrl.xml')
        parser.load()

        cm = parser.context_mgr
        years = cm.get_available_years()

        # Apple 10-K típicamente tiene 3 años
        assert len(years) >= 2
        assert 2025 in years

        print(f"\n✓ Apple años detectados: {years}")
        print(f"  Total: {len(years)} años")

    def test_fiscal_years_descending_order(self):
        """Años deben estar en orden descendente"""
        parser = XBRLParser('data/apple_10k_xbrl.xml')
        parser.load()

        years = parser.context_mgr.get_available_years()

        # Verificar orden descendente
        assert years == sorted(years, reverse=True)

        print(f"\n✓ Orden descendente correcto: {years}")

    def test_get_balance_context_for_specific_year(self):
        """Debe retornar contexto correcto para año específico"""
        parser = XBRLParser('data/apple_10k_xbrl.xml')
        parser.load()

        cm = parser.context_mgr
        years = cm.get_available_years()

        # Año más reciente (default behavior - backwards compat)
        ctx_default = cm.get_balance_context()
        ctx_2025 = cm.get_balance_context(year=2025)
        assert ctx_default == ctx_2025  # Deben ser iguales

        # Año anterior (si existe)
        if len(years) >= 2:
            year_prev = years[1]
            ctx_prev = cm.get_balance_context(year=year_prev)

            assert ctx_prev is not None
            assert ctx_prev != ctx_2025  # Deben ser diferentes

            print(f"\n✓ Contextos por año:")
            print(f"  2025: {ctx_2025}")
            print(f"  {year_prev}: {ctx_prev}")

    def test_get_year_summary(self):
        """get_year_summary() debe retornar metadata completa"""
        parser = XBRLParser('data/apple_10k_xbrl.xml')
        parser.load()

        summary = parser.context_mgr.get_year_summary(2025)

        assert 'year' in summary
        assert 'balance_context' in summary
        assert 'balance_date' in summary
        assert 'income_context' in summary

        assert summary['year'] == 2025
        assert summary['balance_context'] is not None
        assert summary['income_context'] is not None

        print(f"\n✓ Summary 2025:")
        print(f"  Balance: {summary['balance_context']} @ {summary['balance_date']}")
        print(f"  Income: {summary['income_context']}")

    def test_backwards_compatibility(self):
        """Sprint 2 behavior debe seguir funcionando"""
        parser = XBRLParser('data/apple_10k_xbrl.xml')
        parser.load()

        cm = parser.context_mgr

        # Estos métodos NO deben requerir inicialización multi-year
        assert cm.fiscal_year == 2025
        assert cm.fiscal_year_end is not None

        ctx_balance = cm.get_balance_context()  # Sin year param
        ctx_income = cm.get_income_context()    # Sin year param

        assert ctx_balance == 'c-20'
        assert ctx_income == 'c-1'

        print(f"\n✓ Backwards compatibility OK")
        print(f"  fiscal_year: {cm.fiscal_year}")
        print(f"  balance_context: {ctx_balance}")
        print(f"  income_context: {ctx_income}")
