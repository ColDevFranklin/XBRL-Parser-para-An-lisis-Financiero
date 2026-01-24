"""
Sprint 3 - Cross-Company Validation Test Suite
Valida taxonomy_map.json (15 conceptos) contra Apple, Microsoft, Berkshire

Ejecución:
    cd /home/h4ckio/Documentos/projects
    python3 backend/tests/test_cross_company_validation.py
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.parsers.xbrl_parser import XBRLParser


@dataclass
class ConceptStatus:
    """Estado de un concepto XBRL en una empresa"""
    found: bool
    value: Optional[float]
    xbrl_tag: Optional[str]


@dataclass
class CompanyReport:
    """Reporte de validación por empresa"""
    ticker: str
    total_concepts: int
    found_concepts: int
    missing_concepts: List[str]
    balance_valid: bool
    balance_error_pct: float
    concept_details: Dict[str, ConceptStatus]

    @property
    def coverage_pct(self) -> float:
        return (self.found_concepts / self.total_concepts) * 100 if self.total_concepts > 0 else 0


class CrossCompanyValidator:
    """Validador cross-company para taxonomy_map.json"""

    EXPECTED_CONCEPTS = 15

    def __init__(self):
        self.reports: Dict[str, CompanyReport] = {}
        self.project_root = PROJECT_ROOT

        # Definir rutas relativas al proyecto
        self.companies = {
            'AAPL': self.project_root / 'data' / 'apple_10k_xbrl.xml',
            'MSFT': self.project_root / 'data' / 'msft_10k_xbrl.xml',
            'BRK.A': self.project_root / 'data' / 'brk_10k_xbrl.xml'
        }

    def validate_company(self, xml_path: Path, ticker: str) -> CompanyReport:
        """Valida extracción de conceptos para una empresa"""

        if not xml_path.exists():
            raise FileNotFoundError(f"XBRL file not found: {xml_path}")

        parser = XBRLParser(str(xml_path))

        if not parser.load():
            raise ValueError(f"Failed to load XBRL: {xml_path}")

        data = parser.extract_all()

        # Consolidar todos los conceptos extraídos
        all_concepts = {}
        for section_name, section_data in data.items():
            all_concepts.update(section_data)

        # Analizar conceptos encontrados/faltantes
        concept_details = {}
        found_count = 0
        missing = []

        for concept_name, concept_data in all_concepts.items():
            if concept_data and hasattr(concept_data, 'raw_value'):
                concept_details[concept_name] = ConceptStatus(
                    found=True,
                    value=concept_data.raw_value,
                    xbrl_tag=concept_data.xbrl_tag
                )
                found_count += 1
            else:
                concept_details[concept_name] = ConceptStatus(
                    found=False,
                    value=None,
                    xbrl_tag=None
                )
                missing.append(concept_name)

        # Balance sheet validation
        balance_valid, balance_error = self._validate_balance(all_concepts)

        return CompanyReport(
            ticker=ticker,
            total_concepts=self.EXPECTED_CONCEPTS,
            found_concepts=found_count,
            missing_concepts=missing,
            balance_valid=balance_valid,
            balance_error_pct=balance_error,
            concept_details=concept_details
        )

    def _validate_balance(self, concepts: dict) -> tuple:
        """Valida: Assets = Liabilities + Equity"""

        required = ['Assets', 'Liabilities', 'Equity']

        # Verificar campos requeridos
        if not all(concepts.get(field) for field in required):
            return False, 100.0

        assets = concepts['Assets'].raw_value
        liabilities = concepts['Liabilities'].raw_value
        equity = concepts['Equity'].raw_value

        expected_assets = liabilities + equity
        error_pct = abs(assets - expected_assets) / assets * 100 if assets != 0 else 100.0

        return error_pct < 1.0, error_pct

    def validate_all(self) -> Dict[str, CompanyReport]:
        """Valida todas las empresas"""

        print("\nValidando empresas:")
        print("-" * 60)

        for ticker, xml_path in self.companies.items():
            try:
                print(f"Procesando {ticker}...", end=" ")
                report = self.validate_company(xml_path, ticker)
                self.reports[ticker] = report
                print(f"✓ {report.found_concepts}/{report.total_concepts} conceptos")
            except FileNotFoundError as e:
                print(f"✗ Archivo no encontrado")
                print(f"   Expected: {xml_path}")
            except Exception as e:
                print(f"✗ Error: {e}")

        return self.reports

    def generate_comparative_report(self) -> str:
        """Genera reporte comparativo detallado"""

        lines = []
        lines.append("=" * 80)
        lines.append("CROSS-COMPANY VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Summary Table
        lines.append("COVERAGE SUMMARY")
        lines.append("-" * 80)
        lines.append(f"{'Company':<12} {'Concepts':<12} {'Coverage':<12} {'Balance':<12} {'Status'}")
        lines.append("-" * 80)

        for ticker, report in self.reports.items():
            status = "✅ PASS" if report.coverage_pct >= 80 and report.balance_valid else "❌ FAIL"
            balance_status = f"{report.balance_error_pct:.4f}%" if report.balance_valid else "INVALID"

            lines.append(
                f"{ticker:<12} "
                f"{report.found_concepts}/{report.total_concepts:<9} "
                f"{report.coverage_pct:>6.1f}%     "
                f"{balance_status:<12} "
                f"{status}"
            )

        lines.append("")

        # Missing Concepts Analysis
        lines.append("MISSING CONCEPTS BY COMPANY")
        lines.append("-" * 80)

        any_missing = False
        for ticker, report in self.reports.items():
            if report.missing_concepts:
                any_missing = True
                lines.append(f"\n{ticker}:")
                for concept in report.missing_concepts:
                    lines.append(f"  - {concept}")

        if not any_missing:
            lines.append("\n✓ Ningún concepto faltante - 100% coverage en todas las empresas")

        lines.append("")

        # Shared Concepts
        shared_concepts = self._find_shared_concepts()
        lines.append(f"SHARED CONCEPTS ACROSS ALL COMPANIES: {len(shared_concepts)}/{self.EXPECTED_CONCEPTS}")
        lines.append("-" * 80)
        for concept in sorted(shared_concepts):
            lines.append(f"  ✓ {concept}")

        lines.append("")

        # Company-Specific Concepts
        unique_concepts = self._find_unique_concepts()
        if unique_concepts:
            lines.append("COMPANY-SPECIFIC CONCEPTS (not shared)")
            lines.append("-" * 80)
            for ticker, concepts in unique_concepts.items():
                if concepts:
                    lines.append(f"\n{ticker} only:")
                    for concept in sorted(concepts):
                        lines.append(f"  • {concept}")

        lines.append("")

        # Recommendation
        lines.append("RECOMMENDATION")
        lines.append("-" * 80)
        recommendation = self.recommend_expansion()

        # Calcular métricas para justificación
        avg_coverage = sum(r.coverage_pct for r in self.reports.values()) / len(self.reports) if self.reports else 0
        all_balance_valid = all(r.balance_valid for r in self.reports.values()) if self.reports else False
        shared_pct = (len(shared_concepts) / self.EXPECTED_CONCEPTS) * 100 if self.EXPECTED_CONCEPTS > 0 else 0

        if recommendation:
            lines.append("⚠️  EXPAND TO 53 CONCEPTS")
            lines.append("\nRazones:")
            if avg_coverage < 80:
                lines.append(f"  • Coverage promedio insuficiente: {avg_coverage:.1f}% (target: ≥80%)")
            if not all_balance_valid:
                lines.append(f"  • Balance validation fallida en alguna empresa")
            if shared_pct < 60:
                lines.append(f"  • Baja consistencia cross-company: {shared_pct:.1f}% (target: ≥60%)")
        else:
            lines.append("✅ MANTENER 15 CONCEPTOS")
            lines.append("\nJustificación:")
            lines.append(f"  • Coverage promedio: {avg_coverage:.1f}% (≥80% ✓)")
            lines.append(f"  • Balance validation: {'PASS en todas ✓' if all_balance_valid else 'FAIL'}")
            lines.append(f"  • Consistencia cross-company: {shared_pct:.1f}% (≥60% ✓)")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _find_shared_concepts(self) -> set:
        """Encuentra conceptos presentes en todas las empresas"""

        if not self.reports:
            return set()

        # Inicializar con conceptos de la primera empresa
        first_report = next(iter(self.reports.values()))
        shared = {
            concept
            for concept, status in first_report.concept_details.items()
            if status.found
        }

        # Intersectar con las demás empresas
        for report in self.reports.values():
            company_concepts = {
                concept
                for concept, status in report.concept_details.items()
                if status.found
            }
            shared &= company_concepts

        return shared

    def _find_unique_concepts(self) -> Dict[str, set]:
        """Encuentra conceptos únicos por empresa (no compartidos)"""

        shared = self._find_shared_concepts()
        unique = {}

        for ticker, report in self.reports.items():
            company_concepts = {
                concept
                for concept, status in report.concept_details.items()
                if status.found
            }
            unique[ticker] = company_concepts - shared

        return unique

    def recommend_expansion(self) -> bool:
        """
        Recomienda si expandir a 53 conceptos.

        Criterios para MANTENER 15:
        - Coverage promedio ≥ 80%
        - Balance validation exitoso en todas
        - ≥ 60% conceptos compartidos
        """

        if not self.reports:
            return True  # Sin datos, expandir por default

        # Criterio 1: Coverage promedio
        avg_coverage = sum(r.coverage_pct for r in self.reports.values()) / len(self.reports)

        # Criterio 2: Balance validation
        all_balance_valid = all(r.balance_valid for r in self.reports.values())

        # Criterio 3: Conceptos compartidos
        shared_concepts = self._find_shared_concepts()
        shared_pct = (len(shared_concepts) / self.EXPECTED_CONCEPTS) * 100

        # Decisión
        should_maintain = (
            avg_coverage >= 80.0 and
            all_balance_valid and
            shared_pct >= 60.0
        )

        return not should_maintain  # Retorna True si debe expandir


def main():
    """Ejecuta validación cross-company"""

    print("\n" + "=" * 80)
    print("SPRINT 3 - CROSS-COMPANY VALIDATION TEST")
    print("=" * 80)
    print("\nObjetivo: Validar taxonomy_map.json (15 conceptos) contra:")
    print("  • Apple (AAPL) - Tech operational excellence")
    print("  • Microsoft (MSFT) - Tech SaaS business model")
    print("  • Berkshire Hathaway (BRK.A) - Holding/Insurance")
    print("\nCriterios de éxito:")
    print("  • Coverage: ≥80% conceptos por empresa")
    print("  • Balance: <1% error en todas")
    print("  • Consistencia: ≥60% conceptos compartidos")
    print("")

    validator = CrossCompanyValidator()

    # Validar archivos existen
    print("\nVerificando archivos XBRL:")
    print("-" * 60)
    all_exist = True
    for ticker, xml_path in validator.companies.items():
        exists = xml_path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {ticker}: {xml_path.relative_to(PROJECT_ROOT)}")
        all_exist = all_exist and exists

    if not all_exist:
        print("\n❌ ERROR: Faltan archivos XBRL requeridos")
        print("\nPara descargar archivos faltantes:")
        print("  cd backend/parsers")
        print("  python3 download_sample.py")
        sys.exit(1)

    print()

    # Ejecutar validación
    validator.validate_all()

    if not validator.reports:
        print("\n❌ ERROR: No se pudo validar ninguna empresa")
        sys.exit(1)

    # Generar reporte
    report = validator.generate_comparative_report()
    print("\n" + report)

    # Guardar reporte
    report_path = PROJECT_ROOT / 'backend' / 'tests' / 'reports' / 'cross_company_report.md'
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(report)
    print(f"📄 Reporte guardado: {report_path.relative_to(PROJECT_ROOT)}")

    # Exit code basado en éxito
    all_passed = all(
        r.coverage_pct >= 80 and r.balance_valid
        for r in validator.reports.values()
    )

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ TEST PASSED - Todos los criterios cumplidos")
    else:
        print("⚠️  TEST PARTIAL - Revisar reporte para detalles")
    print("=" * 80 + "\n")

    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
