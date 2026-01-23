# backend/parsers/download_historical_xbrl.py

"""
Descarga 10-K XBRL históricos de Apple para completar time-series.

Objetivo: Obtener 4 años completos (2025, 2024, 2023, 2022)
Ya tenemos: 2025 (data/apple_10k_xbrl.xml)
Necesitamos: 2024, 2023, 2022

Author: @franklin
Sprint: 2 - Time-Series Completion
Email: negusnet101@gmail.com
"""

import os
import requests
from pathlib import Path
from typing import Dict, Optional


class HistoricalXBRLDownloader:
    """Descarga 10-K XBRL históricos desde SEC EDGAR"""

    BASE_URL = "https://www.sec.gov/Archives/edgar/data"

    # SEC requiere identificación en User-Agent
    HEADERS = {
        'User-Agent': 'FinancialAnalyzer/1.0 (negusnet101@gmail.com)',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }

    # Mapeo de años fiscales a accession numbers de Apple
    # Fuente: SEC EDGAR (validado 2026-01-23)
    # IMPORTANTE: El archivo XBRL instance tiene formato aapl-YYYYMMDD_htm.xml
    APPLE_FILINGS = {
        2024: {
            'accession': '0000320193-24-000123',
            'fiscal_year_end': '2024-09-28',
            'filename': 'apple_10k_2024_xbrl.xml',
            'xbrl_instance': 'aapl-20240928_htm.xml'  # FIX: agregado _htm
        },
        2023: {
            'accession': '0000320193-23-000106',
            'fiscal_year_end': '2023-09-30',
            'filename': 'apple_10k_2023_xbrl.xml',
            'xbrl_instance': 'aapl-20230930_htm.xml'  # FIX: agregado _htm
        },
        2022: {
            'accession': '0000320193-22-000108',
            'fiscal_year_end': '2022-09-24',
            'filename': 'apple_10k_2022_xbrl.xml',
            'xbrl_instance': 'aapl-20220924_htm.xml'  # FIX: agregado _htm
        }
    }

    APPLE_CIK = '320193'

    def __init__(self, output_dir: str = 'data'):
        """
        Args:
            output_dir: Directorio donde guardar los archivos
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def _build_xbrl_url(self, year: int) -> Optional[str]:
        """
        Construye URL del XBRL instance document.

        Args:
            year: Año fiscal (2022, 2023, 2024)

        Returns:
            URL completa del XBRL o None si año inválido

        Example:
            https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928_htm.xml
        """
        if year not in self.APPLE_FILINGS:
            return None

        filing = self.APPLE_FILINGS[year]

        # Limpiar accession number (remover guiones)
        accession_clean = filing['accession'].replace('-', '')

        # Construir URL
        url = (
            f"{self.BASE_URL}/"
            f"{self.APPLE_CIK}/"
            f"{accession_clean}/"
            f"{filing['xbrl_instance']}"
        )

        return url

    def download_year(self, year: int, force: bool = False) -> bool:
        """
        Descarga el 10-K XBRL de un año específico.

        Args:
            year: Año fiscal (2022, 2023, 2024)
            force: Si True, re-descarga aunque ya exista

        Returns:
            bool: True si descarga exitosa o archivo ya existe
        """
        if year not in self.APPLE_FILINGS:
            print(f"✗ Año {year} no disponible en mapeo")
            return False

        filing = self.APPLE_FILINGS[year]
        output_path = self.output_dir / filing['filename']

        # Verificar si ya existe (cache)
        if output_path.exists() and not force:
            file_size_mb = output_path.stat().st_size / 1_000_000
            print(f"✓ Ya existe: {filing['filename']} ({file_size_mb:.2f} MB)")
            print(f"   (usa force=True para re-descargar)")
            return True

        # Construir URL
        url = self._build_xbrl_url(year)
        if not url:
            print(f"✗ No se pudo construir URL para {year}")
            return False

        print(f"\n📥 Descargando {year} 10-K XBRL...")
        print(f"   URL: {url}")
        print(f"   Destino: {output_path}")

        try:
            # Hacer request con timeout
            response = requests.get(
                url,
                headers=self.HEADERS,
                timeout=30
            )
            response.raise_for_status()

            # Validar que es XML
            content = response.text
            if not content.strip().startswith('<?xml'):
                print(f"   ✗ Respuesta no es XML válido")
                print(f"   Primeros 200 chars: {content[:200]}")
                return False

            # Validar que contiene datos XBRL
            if 'xbrli:xbrl' not in content and '<xbrl' not in content:
                print(f"   ✗ No parece ser XBRL válido")
                return False

            # Guardar archivo
            output_path.write_text(content, encoding='utf-8')

            file_size_mb = output_path.stat().st_size / 1_000_000
            print(f"   ✓ Descargado: {file_size_mb:.2f} MB")

            return True

        except requests.exceptions.HTTPError as e:
            print(f"   ✗ HTTP Error: {e}")
            if e.response.status_code == 403:
                print(f"   Hint: SEC rechazó request (User-Agent issue?)")
            elif e.response.status_code == 404:
                print(f"   Hint: Archivo no encontrado (URL incorrecta?)")
                print(f"   Verificar: {url}")
            return False

        except requests.exceptions.Timeout:
            print(f"   ✗ Timeout: Servidor no respondió en 30s")
            return False

        except requests.exceptions.RequestException as e:
            print(f"   ✗ Error de red: {e}")
            return False

        except Exception as e:
            print(f"   ✗ Error inesperado: {e}")
            return False

    def download_all(
        self,
        years: list = None,
        force: bool = False
    ) -> Dict[int, bool]:
        """
        Descarga múltiples años.

        Args:
            years: Lista de años a descargar (default: [2024, 2023, 2022])
            force: Si True, re-descarga archivos existentes

        Returns:
            dict: {year: success_bool}
        """
        if years is None:
            years = [2024, 2023, 2022]

        results = {}

        print("="*60)
        print("📥 DESCARGA DE 10-K XBRL HISTÓRICOS - APPLE")
        print("="*60)
        print(f"Email: negusnet101@gmail.com")
        print(f"Target: {len(years)} archivos")
        print(f"Cache: {'Disabled (force)' if force else 'Enabled'}")

        for year in years:
            success = self.download_year(year, force=force)
            results[year] = success

        # Resumen
        print("\n" + "="*60)
        print("📊 RESUMEN DE DESCARGAS")
        print("="*60)

        successful = sum(1 for s in results.values() if s)
        total = len(results)

        for year, success in results.items():
            status = "✓" if success else "✗"
            filename = self.APPLE_FILINGS[year]['filename']
            print(f"   {status} {year}: {filename}")

        print(f"\n   Total: {successful}/{total} exitosas")

        if successful == total:
            print("\n🎯 TODAS LAS DESCARGAS COMPLETADAS")
            print("   Ahora tienes 4 años de datos XBRL:")
            print("   - data/apple_10k_xbrl.xml (2025)")
            print("   - data/apple_10k_2024_xbrl.xml")
            print("   - data/apple_10k_2023_xbrl.xml")
            print("   - data/apple_10k_2022_xbrl.xml")
            print("\n📋 SIGUIENTE PASO:")
            print("   python backend/parsers/xbrl_parser.py")
        elif successful > 0:
            print(f"\n⚠️  DESCARGAS PARCIALES: {successful}/{total}")
            print("   Revisa errores arriba")
        else:
            print("\n✗ TODAS LAS DESCARGAS FALLARON")
            print("   Posibles causas:")
            print("   - Sin conexión a internet")
            print("   - SEC bloqueó User-Agent")
            print("   - URLs cambiaron")

        return results

    def verify_downloads(self) -> None:
        """Verifica archivos XBRL descargados"""
        print("\n" + "="*60)
        print("📁 VERIFICACIÓN DE ARCHIVOS")
        print("="*60)

        xbrl_files = sorted(self.output_dir.glob('apple_10k*xbrl.xml'))

        if not xbrl_files:
            print("   ✗ No se encontraron archivos XBRL")
            return

        for filepath in xbrl_files:
            size_mb = filepath.stat().st_size / 1_000_000

            # Extraer año del filename
            if '2024' in filepath.name:
                year = "2024"
            elif '2023' in filepath.name:
                year = "2023"
            elif '2022' in filepath.name:
                year = "2022"
            else:
                year = "2025"

            print(f"   ✓ [{year}] {filepath.name} ({size_mb:.2f} MB)")

        total_files = len(xbrl_files)
        total_size = sum(f.stat().st_size for f in xbrl_files) / 1_000_000

        print(f"\n   Total: {total_files} archivos ({total_size:.2f} MB)")

        if total_files >= 4:
            print(f"\n✅ Time-series completo: {total_files} años disponibles")
        else:
            print(f"\n⚠️  Time-series incompleto: {total_files}/4 años")


if __name__ == "__main__":
    import sys

    # Crear downloader
    downloader = HistoricalXBRLDownloader()

    # Parsear argumentos opcionales
    force = '--force' in sys.argv

    # Descargar años faltantes
    print("Iniciando descargas...")
    print(f"Force mode: {force}\n")

    results = downloader.download_all(
        years=[2024, 2023, 2022],
        force=force
    )

    # Verificar archivos
    downloader.verify_downloads()

    # Exit code
    successful = sum(1 for s in results.values() if s)
    if successful == len(results):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Partial/total failure
