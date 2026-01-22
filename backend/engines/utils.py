"""
Utilidades para normalización de valores financieros.
Contexto: Sprint 2 - Cálculo de métricas con precisión garantizada.
"""

from functools import wraps
from typing import Optional, Union, Callable


def normalize_value(decimals: int) -> Callable:
    """
    Decorador que convierte valores float a enteros escalados.

    Propósito: Evitar errores de floating-point en comparaciones de métricas.

    Args:
        decimals: Número de decimales a preservar en la conversión.
                  Ejemplo: decimals=2 convierte 147.25 → 14725

    Returns:
        Función decorada que retorna int escalado o None.

    Raises:
        TypeError: Si el valor retornado no es numérico.
        ValueError: Si decimals es negativo.

    Example:
        >>> @normalize_value(decimals=2)
        ... def calculate_roe():
        ...     return 147.256789
        >>> calculate_roe()
        14726

        >>> @normalize_value(decimals=0)
        ... def get_assets():
        ...     return 352000000000
        >>> get_assets()
        352000000000
    """
    if decimals < 0:
        raise ValueError(f"decimals debe ser >= 0, recibido: {decimals}")

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[int]:
            result = func(*args, **kwargs)

            # Caso 1: Valor None (métrica no calculable)
            if result is None:
                return None

            # Caso 2: Validar tipo numérico
            if not isinstance(result, (int, float)):
                raise TypeError(
                    f"normalize_value espera int/float, "
                    f"recibió {type(result).__name__}: {result}"
                )

            # Caso 3: Conversión a entero escalado
            multiplier = 10 ** decimals
            scaled_value = int(result * multiplier)

            return scaled_value

        return wrapper
    return decorator
