"""
Tests for Company Universe Module

Validates S&P 500 Tech sector company list.

Usage:
    python3 -m pytest backend/tests/benchmarks/test_company_universe.py -v
"""

import pytest
from backend.benchmarks.company_universe import (
    get_tech_universe,
    get_tickers_only,
    get_company_by_ticker,
    filter_by_market_cap,
    SP500_TECH_UNIVERSE
)


class TestCompanyUniverse:
    """Test suite for company universe definitions"""

    def test_universe_size(self):
        """Tech universe should have ~74 companies"""
        universe = get_tech_universe()
        assert len(universe) >= 70, "Expected at least 70 tech companies"
        assert len(universe) <= 80, "Expected at most 80 tech companies"

    def test_tickers_only(self):
        """get_tickers_only should return list of strings"""
        tickers = get_tickers_only()

        assert isinstance(tickers, list)
        assert all(isinstance(t, str) for t in tickers)
        assert len(tickers) == len(get_tech_universe())

    def test_required_mega_caps(self):
        """Should include AAPL, MSFT, NVDA"""
        tickers = get_tickers_only()

        assert "AAPL" in tickers, "Apple should be in tech universe"
        assert "MSFT" in tickers, "Microsoft should be in tech universe"
        assert "NVDA" in tickers, "NVIDIA should be in tech universe"

    def test_mega_cap_count(self):
        """Should have 4 mega caps (>$500B) - AAPL, MSFT, NVDA, AVGO"""
        universe = get_tech_universe()
        mega_caps = [c for c in universe if c.market_cap_b > 500]

        assert len(mega_caps) == 4, f"Expected 4 mega caps, got {len(mega_caps)}"

        # Verify specific companies
        mega_tickers = {c.ticker for c in mega_caps}
        assert mega_tickers == {"AAPL", "MSFT", "NVDA", "AVGO"}

    def test_get_company_by_ticker(self):
        """Should retrieve company info by ticker"""
        apple = get_company_by_ticker("AAPL")

        assert apple.ticker == "AAPL"
        assert apple.name == "Apple Inc."
        assert apple.market_cap_b > 1000  # >$1T

    def test_get_company_not_found(self):
        """Should raise ValueError for invalid ticker"""
        with pytest.raises(ValueError, match="not found"):
            get_company_by_ticker("INVALID")

    def test_filter_by_market_cap_large(self):
        """Filter for large caps (>$100B)"""
        large_caps = filter_by_market_cap(min_cap_b=100)

        assert len(large_caps) >= 10, "Expected at least 10 large caps"
        assert all(c.market_cap_b >= 100 for c in large_caps)

    def test_filter_by_market_cap_range(self):
        """Filter for mid caps ($10B-$100B)"""
        mid_caps = filter_by_market_cap(min_cap_b=10, max_cap_b=100)

        assert all(10 <= c.market_cap_b <= 100 for c in mid_caps)

    def test_no_duplicates(self):
        """Should not have duplicate tickers"""
        tickers = get_tickers_only()

        assert len(tickers) == len(set(tickers)), "Found duplicate tickers"

    def test_all_have_required_fields(self):
        """All companies should have complete metadata"""
        universe = get_tech_universe()

        for company in universe:
            assert company.ticker, "Ticker should not be empty"
            assert company.name, "Name should not be empty"
            assert company.gics_industry, "Industry should not be empty"
            assert company.market_cap_b > 0, "Market cap should be positive"


class TestCompanyMetadata:
    """Test specific company data quality"""

    def test_apple_metadata(self):
        """Validate Apple metadata"""
        apple = get_company_by_ticker("AAPL")

        assert apple.name == "Apple Inc."
        assert apple.gics_industry == "Technology Hardware"
        assert apple.market_cap_b > 2000  # Should be >$2T

    def test_microsoft_metadata(self):
        """Validate Microsoft metadata"""
        msft = get_company_by_ticker("MSFT")

        assert msft.name == "Microsoft Corporation"
        assert msft.gics_industry == "Systems Software"
        assert msft.market_cap_b > 2000

    def test_market_cap_distribution(self):
        """Validate market cap distribution is reasonable"""
        universe = get_tech_universe()

        mega_caps = [c for c in universe if c.market_cap_b > 500]
        large_caps = [c for c in universe if 100 <= c.market_cap_b <= 500]
        mid_caps = [c for c in universe if 10 <= c.market_cap_b < 100]
        small_caps = [c for c in universe if c.market_cap_b < 10]

        # Sanity checks
        assert len(mega_caps) >= 2, "Should have at least 2 mega caps"
        assert len(large_caps) >= 8, "Should have at least 8 large caps"
        assert len(mid_caps) >= 15, "Should have at least 15 mid caps"
        assert len(small_caps) >= 20, "Should have at least 20 small caps"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
