# backend/parsers/multi_file_xbrl_parser.py

"""
Parser multi-archivo para extracción de time-series XBRL.

Detecta automáticamente archivos XBRL históricos y los procesa
para generar un time-series completo de 2-4 años fiscales.

Author: @franklin
Sprint: 2 - Multi-Year Time-Series Extraction
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
import re

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.parsers.xbrl_parser import XBRLParser
from backend.engines.tracked_metric import SourceTrace


class MultiFileXBRLParser:
    """
    Parser que maneja múltiples archivos XBRL para time-series.

    Detecta automáticamente archivos XBRL en un directorio y extrae
    datos financieros de múltiples años fiscales.

    Usage:
        parser = MultiFileXBRLParser(ticker='AAPL')
        timeseries = parser.extract_timeseries(years=4)

        # Output:
        # {
        #   2025: {'Assets': SourceTrace(...), 'Revenue': ...},
        #   2024: {...},
        #   2023: {...},
        #   2022: {...}
        # }
    """

    # Patrones de nombres de archivo por ticker
    FILE_PATTERNS = {
        'AAPL': {
            'pattern': r'apple_10k(?:_(\d{4}))?_xbrl\.xml',
            'default_year': 2025  # Archivo sin año es 2025
        }
    }

    def __init__(self, ticker: str = 'AAPL', data_dir: str = 'data'):
        """
        Args:
            ticker: Símbolo bursátil (default: AAPL)
            data_dir: Directorio con archivos XBRL
        """
        self.ticker = ticker.upper()
        self.data_dir = Path(data_dir)

        if not self.data_dir.exists():
            raise ValueError(f"Directorio no existe: {data_dir}")

        # Descubrir archivos disponibles
        self.files = self._discover_files()

        if not self.files:
            raise ValueError(
                f"No se encontraron archivos XBRL para {ticker} en {data_dir}"
            )

        print(f"✓ MultiFileXBRLParser inicializado")
        print(f"  Ticker: {self.ticker}")
        print(f"  Archivos encontrados: {len(self.files)}")
        print(f"  Años disponibles: {sorted(self.files.keys(), reverse=True)}")

    def _discover_files(self) -> Dict[int, Path]:
        """
        Detecta archivos XBRL disponibles en el directorio.

        Returns:
            Dict mapeando año fiscal → filepath

        Example:
            {
                2025: Path('data/apple_10k_xbrl.xml'),
                2024: Path('data/apple_10k_2024_xbrl.xml'),
                2023: Path('data/apple_10k_2023_xbrl.xml'),
                2022: Path('data/apple_10k_2022_xbrl.xml')
            }
        """
        if self.ticker not in self.FILE_PATTERNS:
            raise ValueError(f"Ticker {self.ticker} no soportado")

        config = self.FILE_PATTERNS[self.ticker]
        pattern = re.compile(config['pattern'])

        files_by_year = {}

        # Buscar archivos que coincidan con el patrón
        for filepath in self.data_dir.glob('*.xml'):
            match = pattern.match(filepath.name)

            if match:
                year_str = match.group(1)  # Grupo de captura para año

                if year_str:
                    # Archivo con año explícito: apple_10k_2024_xbrl.xml
                    year = int(year_str)
                else:
                    # Archivo sin año: apple_10k_xbrl.xml
                    year = config['default_year']

                files_by_year[year] = filepath

        return files_by_year

    def get_available_years(self) -> List[int]:
        """
        Retorna lista de años fiscales disponibles (orden descendente).

        Returns:
            Lista de años [2025, 2024, 2023, 2022]
        """
        return sorted(self.files.keys(), reverse=True)

    def extract_timeseries(
        self,
        years: int = 4,
        fields: List[str] = None
    ) -> Dict[int, Dict[str, SourceTrace]]:
        """
        Extrae time-series de múltiples archivos XBRL.

        Args:
            years: Número máximo de años a extraer
            fields: Lista de campos a extraer (None = todos)

        Returns:
            Dict por año con datos financieros:
            {
                2025: {
                    'Assets': SourceTrace(...),
                    'Liabilities': SourceTrace(...),
                    'Revenues': SourceTrace(...),
                    ...
                },
                2024: {...},
                ...
            }

        Example:
            >>> parser = MultiFileXBRLParser('AAPL')
            >>> ts = parser.extract_timeseries(years=3)
            >>> len(ts)
            3
            >>> ts[2025]['Assets'].raw_value
            359241000000.0
        """
        available_years = self.get_available_years()
        years_to_extract = available_years[:min(years, len(available_years))]

        print(f"\n{'='*60}")
        print(f"EXTRACCIÓN TIME-SERIES MULTI-ARCHIVO")
        print(f"{'='*60}")
        print(f"Ticker: {self.ticker}")
        print(f"Años solicitados: {years}")
        print(f"Años disponibles: {len(available_years)}")
        print(f"Años a extraer: {years_to_extract}")

        result = {}

        for year in years_to_extract:
            filepath = self.files[year]

            print(f"\n📄 Procesando {year}:")
            print(f"   Archivo: {filepath.name}")

            try:
                # Crear parser individual para este archivo
                parser = XBRLParser(str(filepath))

                # Cargar archivo
                if not parser.load():
                    print(f"   ✗ Error cargando archivo")
                    continue

                # Extraer todos los datos
                data = parser.extract_all()

                # Combinar balance_sheet + income_statement + cash_flow
                year_data = {}
                for section_name, section_data in data.items():
                    for field_name, source_trace in section_data.items():
                        if source_trace is not None:
                            year_data[field_name] = source_trace

                # Filtrar campos si se especificaron
                if fields:
                    year_data = {
                        k: v for k, v in year_data.items()
                        if k in fields
                    }

                # Validar que hay datos mínimos
                if not year_data:
                    print(f"   ⚠️  Sin datos extraídos")
                    continue

                result[year] = year_data
                print(f"   ✓ {len(year_data)} campos extraídos")

                # Mostrar campos principales
                key_fields = ['Assets', 'Revenue', 'NetIncome']
                for field in key_fields:
                    if field in year_data:
                        value = year_data[field].raw_value
                        print(f"   - {field}: ${value:,.0f}")

            except Exception as e:
                print(f"   ✗ Error procesando: {e}")
                continue

        print(f"\n{'='*60}")
        print(f"✅ TIME-SERIES EXTRACTION COMPLETADO")
        print(f"{'='*60}")
        print(f"Años extraídos: {len(result)}/{len(years_to_extract)}")
        print(f"Años con datos: {sorted(result.keys(), reverse=True)}")

        return result

    def validate_balance_sheets(self, timeseries: Dict[int, Dict]) -> Dict[int, bool]:
        """
        Valida que la ecuación contable se cumpla para todos los años.

        Args:
            timeseries: Output de extract_timeseries()

        Returns:
            Dict: {year: balance_ok}
        """
        print(f"\n{'='*60}")
        print(f"VALIDACIÓN BALANCE SHEET")
        print(f"{'='*60}")

        results = {}

        for year in sorted(timeseries.keys(), reverse=True):
            data = timeseries[year]

            # FIX: Cambiar 'StockholdersEquity' por 'Equity' (Sprint 3 Day 3)
            required = ['Assets', 'Liabilities', 'Equity']
            if not all(field in data for field in required):
                print(f"{year}: ⚠️  Campos faltantes")
                results[year] = False
                continue

            # Extraer valores
            assets = data['Assets'].raw_value
            liabilities = data['Liabilities'].raw_value
            equity = data['Equity'].raw_value

            # Calcular diferencia
            calculated = liabilities + equity
            diff = abs(assets - calculated)
            diff_pct = (diff / assets) * 100

            # Validar (<1% es OK)
            balance_ok = diff_pct < 1.0
            results[year] = balance_ok

            status = "✓" if balance_ok else "✗"
            print(f"{year}: {status} Diferencia: {diff_pct:.4f}%")

        all_ok = all(results.values())
        print(f"\n{'='*60}")
        if all_ok:
            print("✅ TODOS LOS BALANCE SHEETS VÁLIDOS")
        else:
            failed = [y for y, ok in results.items() if not ok]
            print(f"⚠️  BALANCE SHEETS INVÁLIDOS: {failed}")
        print(f"{'='*60}")

        return results


if __name__ == "__main__":
    """
    Test del MultiFileXBRLParser con Apple 10-K históricos.
    """
    import time

    start_time = time.time()

    try:
        # Crear parser multi-archivo
        parser = MultiFileXBRLParser(ticker='AAPL', data_dir='data')

        # Extraer time-series de 4 años
        timeseries = parser.extract_timeseries(years=4)

        # Validar balance sheets
        balance_results = parser.validate_balance_sheets(timeseries)

        # Resumen final
        print(f"\n{'='*60}")
        print(f"📊 RESUMEN FINAL")
        print(f"{'='*60}")

        print(f"\nAños procesados: {len(timeseries)}")
        for year in sorted(timeseries.keys(), reverse=True):
            data = timeseries[year]
            fields_count = len(data)
            balance_ok = balance_results.get(year, False)
            status = "✓" if balance_ok else "✗"
            print(f"  {status} {year}: {fields_count} campos")

        # Métricas de performance
        elapsed = time.time() - start_time
        print(f"\n⏱️  Tiempo total: {elapsed:.2f}s")
        print(f"   Promedio por año: {elapsed/len(timeseries):.2f}s")

        # Validación Sprint 2
        all_balance_ok = all(balance_results.values())
        has_4_years = len(timeseries) == 4
        fast_enough = elapsed < 10.0

        print(f"\n{'='*60}")
        print(f"VALIDACIÓN SPRINT 2")
        print(f"{'='*60}")

        checks = {
            "Time-series 4 años": has_4_years,
            "Balance sheets válidos": all_balance_ok,
            "Performance <10s": fast_enough
        }

        for check, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {check}")

        if all(checks.values()):
            print(f"\n🎯 SPRINT 2 - MULTI-FILE PARSER COMPLETADO")
            print(f"   ✓ 4 años extraídos correctamente")
            print(f"   ✓ Balance sheets validados")
            print(f"   ✓ Performance óptima ({elapsed:.2f}s)")
            print(f"\n📋 LISTO PARA: Sprint 3 (25 Métricas)")
        else:
            print(f"\n⚠️  REVISAR:")
            for check, passed in checks.items():
                if not passed:
                    print(f"   ✗ {check}")

    except Exception as e:
        print(f"\n✗ ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
