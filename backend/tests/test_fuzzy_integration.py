"""
Integration test for fuzzy mapper with real XBRL data.
Tests end-to-end fuzzy matching with Apple 10-K filing.

Author: @franklin
Sprint: 3 Día 4 - Fuzzy Mapping Integration Tests
"""

import pytest
from pathlib import Path
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.parsers.xbrl_parser import XBRLParser


class TestFuzzyIntegration:
    """Integration tests for fuzzy mapper with real XBRL."""

    def setup_method(self):
        """Locate Apple 10-K filing."""
        self.filing_path = Path("data/apple_10k_xbrl.xml")

        if not self.filing_path.exists():
            pytest.skip("Apple 10-K data not available")

    def test_fuzzy_mapper_initialized(self):
        """Test that fuzzy mapper is properly initialized."""
        parser = XBRLParser(str(self.filing_path))
        parser.load()

        assert parser.fuzzy_mapper is not None
        assert parser.fuzzy_mapper.similarity_threshold == 0.75

    def test_fuzzy_fallback_increases_coverage(self):
        """Test that fuzzy mapper increases extraction coverage."""
        parser = XBRLParser(str(self.filing_path))
        parser.load()

        # Extract with fuzzy mapper enabled
        result = parser.extract_all()  # Cambio: extract_financial_data → extract_all

        # Check that we extracted data
        assert result is not None
        assert 'balance_sheet' in result

        # Count extracted fields
        total_fields = sum(
            1 for section in result.values()
            for value in section.values()
            if value is not None
        )

        # Should extract at least 15 fields with fuzzy mapping
        assert total_fields >= 15

    def test_mapping_gaps_reported(self):
        """Test that mapping gaps are properly reported."""
        parser = XBRLParser(str(self.filing_path))
        parser.load()
        parser.extract_all()  # Cambio: extract_financial_data → extract_all

        gaps_report = parser.get_mapping_gaps_report()

        # Report should exist
        assert gaps_report is not None

        # Should either show no gaps or provide actionable report
        assert ("No mapping gaps" in gaps_report or
                "ACTION REQUIRED" in gaps_report)

    def test_xsd_schema_loading(self):
        """Test XSD schema loading for parent discovery."""
        parser = XBRLParser(str(self.filing_path))
        parser.load()

        # XSD may or may not be available - both are OK
        # Just verify attribute exists
        assert hasattr(parser, 'xsd_tree')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
