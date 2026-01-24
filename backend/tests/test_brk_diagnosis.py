"""
Sprint 3 Paso 3.2 - Test Diagnóstico BRK.A
Valida que el diagnóstico identifica el problema root cause

Ejecutar:
    cd /home/h4ckio/Documentos/projects
    python3 -m pytest backend/tests/test_brk_diagnosis.py -v
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.parsers.xbrl_parser import XBRLParser
from lxml import etree
import pytest


class TestBRKDiagnosis:
    """Test suite para diagnosticar fallo de BRK.A"""

    @pytest.fixture
    def brk_xml_path(self):
        return project_root / 'data' / 'brk_10k_xbrl.xml'

    @pytest.fixture
    def brk_tree(self, brk_xml_path):
        return etree.parse(str(brk_xml_path))

    def test_file_exists(self, brk_xml_path):
        """Archivo BRK XBRL existe"""
        assert brk_xml_path.exists(), f"Archivo no encontrado: {brk_xml_path}"

    def test_file_is_valid_xml(self, brk_tree):
        """Archivo es XML válido"""
        assert brk_tree is not None
        assert brk_tree.getroot() is not None

    def test_has_xbrl_namespaces(self, brk_tree):
        """Tiene namespaces XBRL esperados"""
        root = brk_tree.getroot()
        namespaces = root.nsmap

        # Namespaces críticos
        assert 'us-gaap' in namespaces or None in namespaces
        assert 'dei' in namespaces

        print(f"\n✓ Namespaces encontrados: {len(namespaces)}")

    def test_has_contexts(self, brk_tree):
        """Tiene contexts XBRL"""
        root = brk_tree.getroot()
        ns = {'xbrli': 'http://www.xbrl.org/2003/instance'}

        contexts = root.findall('.//xbrli:context', ns)
        assert len(contexts) > 0, "No se encontraron contexts"

        print(f"\n✓ Total contexts: {len(contexts)}")

    def test_has_fiscal_year_end(self, brk_tree):
        """Detecta fiscal year end"""
        root = brk_tree.getroot()
        namespaces = root.nsmap

        doc_period_end = root.find('.//dei:DocumentPeriodEndDate', namespaces)

        if doc_period_end is not None:
            print(f"\n✓ DocumentPeriodEndDate: {doc_period_end.text}")
        else:
            pytest.fail("⚠️  DocumentPeriodEndDate NO ENCONTRADO - ROOT CAUSE")

    def test_has_financial_concepts(self, brk_tree):
        """Tiene conceptos financieros clave"""
        root = brk_tree.getroot()
        namespaces = root.nsmap

        key_concepts = ['Assets', 'Liabilities', 'StockholdersEquity', 'Revenues', 'NetIncome']
        found_concepts = []

        for concept in key_concepts:
            elements = root.findall(f'.//us-gaap:{concept}', namespaces)
            if elements:
                found_concepts.append(concept)

        print(f"\n✓ Conceptos encontrados: {found_concepts}")
        assert len(found_concepts) > 0, "No se encontraron conceptos financieros"

    def test_parser_loads(self, brk_xml_path):
        """XBRLParser carga el archivo"""
        parser = XBRLParser(str(brk_xml_path))
        assert parser.load() == True

        print(f"\n✓ Parser loaded")
        print(f"  Fiscal year-end: {parser.fiscal_year_end}")
        print(f"  Year: {parser.year}")

    def test_context_manager_detects_contexts(self, brk_xml_path):
        """ContextManager detecta contexts"""
        parser = XBRLParser(str(brk_xml_path))
        parser.load()

        balance_ctx = parser.context_manager.balance_context
        income_ctx = parser.context_manager.income_context

        print(f"\n  Balance context: {balance_ctx}")
        print(f"  Income context: {income_ctx}")

        if balance_ctx is None or income_ctx is None:
            pytest.fail("⚠️  ContextManager NO DETECTÓ contexts - ROOT CAUSE")

    def test_extract_all_returns_data(self, brk_xml_path):
        """extract_all() retorna datos"""
        parser = XBRLParser(str(brk_xml_path))
        parser.load()

        data = parser.extract_all()

        all_fields = {
            **data['balance_sheet'],
            **data['income_statement'],
            **data['cash_flow']
        }

        extracted = sum(1 for v in all_fields.values() if v)

        print(f"\n  Conceptos extraídos: {extracted}/15")

        if extracted == 0:
            pytest.fail(f"⚠️  CERO conceptos extraídos - ROOT CAUSE confirmado")

        assert extracted > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
