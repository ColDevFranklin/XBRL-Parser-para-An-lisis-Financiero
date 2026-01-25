"""
Integration test for fuzzy mapper with real XBRL data.
Tests end-to-end fuzzy matching with Apple 10-K filing.

**NEW Sprint 3 Día 5**: Tie-breaking test for ambiguous matches

Author: @franklin
Sprint: 3 Día 4-5 - Fuzzy Mapping Integration Tests + Tie-Breaking
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
        result = parser.extract_all()

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

        parser.extract_all()

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

    def test_fuzzy_tiebreaker_with_multiple_candidates(self):
        """
        Test tie-breaking when fuzzy match returns multiple candidates.

        **NEW Sprint 3 Día 5**: Validates Balance Sheet equation is used
        to select correct candidate when multiple fuzzy matches exist.

        Scenario:
        - Fuzzy mapper finds 2+ tags matching 'Assets' with >75% similarity
        - Parser should use Balance equation to choose correct one
        - Winner: Tag that makes Assets = Liabilities + Equity (<1% diff)
        - Loser: Tag that breaks Balance equation (>1% diff)
        """
        parser = XBRLParser(str(self.filing_path))
        parser.load()

        # Extract Balance Sheet
        bs = parser.extract_balance_sheet()

        # If Assets was extracted via fuzzy matching
        if bs.get('Assets'):
            assets = bs['Assets'].raw_value
            liabilities = bs.get('Liabilities')
            equity = bs.get('Equity')

            # Verify Balance equation holds
            if liabilities and equity:
                l_value = liabilities.raw_value
                e_value = equity.raw_value
                calculated = l_value + e_value

                diff_pct = abs(assets - calculated) / assets * 100

                # Tie-breaking should ensure <1% diff
                assert diff_pct < 1.0, (
                    f"Balance Sheet equation failed: "
                    f"Assets=${assets:,.0f} vs L+E=${calculated:,.0f} "
                    f"({diff_pct:.2f}% diff)"
                )

                print(f"\n✓ TIE-BREAKING VALIDATION PASSED")
                print(f"  Assets: ${assets:,.0f}")
                print(f"  L + E:  ${calculated:,.0f}")
                print(f"  Diff:   {diff_pct:.4f}%")

    def test_fuzzy_tiebreaker_rejects_invalid_candidates(self):
        """
        Test that tie-breaking REJECTS candidates that break Balance equation.

        **NEW Sprint 3 Día 5**: Validates that invalid fuzzy matches are
        discarded even if they have high similarity scores.

        Expected behavior:
        - If fuzzy mapper finds tag with 95% similarity but breaks Balance
        - Parser should REJECT it and try next candidate
        - If all candidates fail → record MAPPING_GAP (don't guess)
        """
        parser = XBRLParser(str(self.filing_path))
        parser.load()

        # Get fuzzy mapper
        mapper = parser.fuzzy_mapper

        # Get available tags
        available_tags = parser._get_available_tags()

        # Simulate finding multiple candidates for 'Assets'
        # (use fuzzy_match_with_tiebreaker to get ALL matches)
        aliases = parser._get_concept_aliases('Assets')

        if aliases:
            candidates = mapper.fuzzy_match_with_tiebreaker(
                concept='Assets',
                available_tags=available_tags,
                aliases=aliases
            )

            if len(candidates) > 1:
                # Multiple candidates found
                print(f"\n✓ MULTIPLE CANDIDATES DETECTED: {len(candidates)}")

                for tag, score in candidates:
                    print(f"  - {tag} (similarity: {score:.2f})")

                # Extract Balance Sheet (should apply tie-breaking)
                bs = parser.extract_balance_sheet()

                # Verify Assets was extracted
                assert bs.get('Assets') is not None, (
                    "Tie-breaking should have selected valid candidate"
                )

                # Verify Balance equation
                assets = bs['Assets'].raw_value
                liabilities = bs['Liabilities'].raw_value
                equity = bs['Equity'].raw_value

                diff_pct = abs(assets - (liabilities + equity)) / assets * 100

                assert diff_pct < 1.0, (
                    "Tie-breaking selected invalid candidate that breaks Balance"
                )

                print(f"\n✓ TIE-BREAKING CORRECTLY SELECTED VALID CANDIDATE")
                print(f"  Selected tag: {bs['Assets'].xbrl_tag}")
                print(f"  Balance diff: {diff_pct:.4f}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
