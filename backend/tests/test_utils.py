"""
Tests para backend/engines/utils.py
Valida normalize_value antes de usarlo en Sprint 2.
"""

import pytest
from backend.engines.utils import normalize_value


class TestNormalizeValue:
    """Suite de tests para el decorador normalize_value."""

    def test_decimals_2_basic(self):
        """Caso básico: ROE con 2 decimales."""
        @normalize_value(decimals=2)
        def calculate_roe():
            return 147.256789

        result = calculate_roe()
        assert result == 14725  # int() trunca: 147.256789 × 100 = 14725.6789 → 14725
        assert isinstance(result, int)

    def test_decimals_0_large_number(self):
        """Caso assets: números grandes sin decimales."""
        @normalize_value(decimals=0)
        def get_assets():
            return 352000000000.0

        result = get_assets()
        assert result == 352000000000
        assert isinstance(result, int)

    def test_decimals_4_precision(self):
        """Alta precisión: 4 decimales."""
        @normalize_value(decimals=4)
        def precise_metric():
            return 3.141592

        result = precise_metric()
        assert result == 31415  # int() trunca: 3.141592 × 10^4 = 31415.92 → 31415

    def test_none_value_passthrough(self):
        """Métricas no calculables retornan None."""
        @normalize_value(decimals=2)
        def missing_data():
            return None

        result = missing_data()
        assert result is None

    def test_negative_decimals_raises_error(self):
        """Decimales negativos deben fallar."""
        with pytest.raises(ValueError, match="decimals debe ser >= 0"):
            @normalize_value(decimals=-1)
            def invalid():
                return 100

    def test_non_numeric_raises_typeerror(self):
        """Valores no numéricos deben fallar."""
        @normalize_value(decimals=2)
        def returns_string():
            return "147.25"

        with pytest.raises(TypeError, match="espera int/float"):
            returns_string()

    def test_zero_value(self):
        """Manejo correcto de cero."""
        @normalize_value(decimals=2)
        def zero_metric():
            return 0.0

        result = zero_metric()
        assert result == 0

    def test_negative_value(self):
        """Métricas negativas (pérdidas)."""
        @normalize_value(decimals=2)
        def net_loss():
            return -25.50

        result = net_loss()
        assert result == -2550

    def test_rounding_behavior(self):
        """Validar redondeo hacia abajo (truncamiento)."""
        @normalize_value(decimals=2)
        def edge_case():
            return 147.999

        result = edge_case()
        # int() trunca, no redondea
        assert result == 14799


class TestNormalizeValueIntegration:
    """Tests de integración simulando uso en MetricsCalculator."""

    def test_roe_comparison_safe(self):
        """Comparación estable vs valor de referencia."""
        @normalize_value(decimals=2)
        def calculate_roe(net_income, equity):
            return (net_income / equity) * 100

        # Apple 2023 aproximado
        roe = calculate_roe(net_income=96995000000, equity=62146000000)
        reference = 15602  # 156.02 × 100

        # Comparación con tolerancia
        assert abs(roe - reference) < 10  # ±0.1% tolerancia

    def test_division_by_zero_handling(self):
        """MetricsCalculator debe manejar división por cero."""
        @normalize_value(decimals=2)
        def safe_ratio(a, b):
            if b == 0:
                return None
            return a / b

        result = safe_ratio(100, 0)
        assert result is None
