# Backend Engines - Utilidades Core

## normalize_value (Sprint 2)

**Propósito:** Convertir métricas float a enteros escalados para evitar errores de floating-point.

### Uso básico

```python
from backend.engines.utils import normalize_value

@normalize_value(decimals=2)
def calculate_roe(net_income, equity):
    return (net_income / equity) * 100

# Apple 2023
roe = calculate_roe(96995000000, 62146000000)
# Resultado: 15602 (representa 156.02%)
```

### Comportamiento clave

| Input | decimals | Output | Explicación |
|-------|----------|--------|-------------|
| `147.256789` | `2` | `14725` | Trunca (no redondea) |
| `352000000000.0` | `0` | `352000000000` | Sin cambio |
| `None` | cualquiera | `None` | Passthrough |
| `"147.25"` | cualquiera | `TypeError` | Solo numéricos |

### Testing

```bash
# Ejecutar suite completa
pytest backend/tests/test_utils.py -v

# Test específico
pytest backend/tests/test_utils.py::TestNormalizeValue::test_decimals_2_basic -v
```

### Coverage actual

- ✅ 11/11 tests passing
- ✅ Edge cases: None, zero, negativos, truncamiento
- ✅ Error handling: TypeError, ValueError

## Próximos pasos (Sprint 2 - Día 1)

1. Implementar `MetricsCalculator` en `backend/engines/metrics_calculator.py`
2. Usar `@normalize_value(decimals=2)` en todos los métodos `calculate_*()`
3. Validar contra Yahoo Finance
