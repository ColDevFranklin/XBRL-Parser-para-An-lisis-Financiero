"""
Integration tests for sector configuration system

Tests real-world usage scenarios and end-to-end workflows
"""
import pytest
from backend.config import (
    SECTOR_DEFINITIONS,
    SectorConfig,
    get_sector_config,
    list_sectors,
    validate_sector,
    get_sector_companies,
    get_company_sector,
    get_sector_summary,
)


class TestSectorConfigurationIntegration:
    """Integration tests for complete sector configuration workflow"""

    def test_complete_sector_lookup_workflow(self):
        """Test complete workflow: list → validate → get config → get companies"""
        # Step 1: List all available sectors
        sectors = list_sectors()
        assert len(sectors) == 4
        assert 'TECH' in sectors

        # Step 2: Validate a sector exists
        assert validate_sector('TECH') is True

        # Step 3: Get sector configuration
        tech_config = get_sector_config('TECH')
        assert tech_config.code == 'TECH'
        assert tech_config.name == 'Technology'

        # Step 4: Get companies for that sector
        companies = get_sector_companies('TECH')
        assert len(companies) == 61
        assert 'AAPL' in companies

    def test_reverse_lookup_workflow(self):
        """Test reverse lookup: company → sector → config"""
        # Step 1: Find sector for a company
        sector_code = get_company_sector('AAPL')
        assert sector_code == 'TECH'

        # Step 2: Get full sector config
        sector_config = get_sector_config(sector_code)
        assert sector_config.name == 'Technology'

        # Step 3: Verify company is in sector
        companies = get_sector_companies(sector_code)
        assert 'AAPL' in companies

    def test_multi_sector_analysis_workflow(self):
        """Test analyzing companies across multiple sectors"""
        test_companies = {
            'AAPL': 'TECH',
            'BHP': 'MINING',
            'XOM': 'OIL_GAS',
            'WMT': 'RETAIL',
        }

        for ticker, expected_sector in test_companies.items():
            # Lookup sector
            sector = get_company_sector(ticker)
            assert sector == expected_sector

            # Get sector config
            config = get_sector_config(sector)

            # Verify company is in sector
            assert ticker in config.companies

            # Verify key metrics are defined
            assert len(config.key_metrics) > 0

    def test_sector_summary_comprehensive(self):
        """Test comprehensive sector summary generation"""
        summary = get_sector_summary()

        # Should have all 4 sectors
        assert len(summary) == 4

        total_companies = 0

        for sector_code, info in summary.items():
            # Validate summary structure
            assert 'name' in info
            assert 'company_count' in info
            assert 'min_peers' in info
            assert 'key_metrics' in info
            assert 'description' in info

            # Validate data consistency
            config = get_sector_config(sector_code)
            assert info['name'] == config.name
            assert info['company_count'] == len(config.companies)
            assert info['min_peers'] == config.min_peers
            assert info['key_metrics'] == config.key_metrics

            total_companies += info['company_count']

        # Verify total company count
        assert total_companies >= 200  # Ultra-robust requirement

    def test_case_insensitive_operations(self):
        """Test that all operations are case-insensitive"""
        # Sector lookup
        assert validate_sector('TECH') == validate_sector('tech')
        assert validate_sector('TECH') == validate_sector('TeCh')

        # Get sector config
        config_upper = get_sector_config('TECH')
        config_lower = get_sector_config('tech')
        assert config_upper.code == config_lower.code

        # Company lookup
        assert get_company_sector('AAPL') == get_company_sector('aapl')
        assert get_company_sector('BHP') == get_company_sector('bhp')

    def test_error_handling_workflow(self):
        """Test proper error handling across operations"""
        # Invalid sector validation (should return False, not error)
        assert validate_sector('INVALID') is False

        # Invalid sector config (should raise ValueError)
        with pytest.raises(ValueError, match="not found"):
            get_sector_config('INVALID')

        # Invalid sector companies (should raise ValueError)
        with pytest.raises(ValueError, match="not found"):
            get_sector_companies('INVALID')

        # Invalid company lookup (should return None, not error)
        assert get_company_sector('INVALID') is None

    def test_data_immutability(self):
        """Test that returned data cannot modify original configuration"""
        # Get companies list
        original_companies = get_sector_companies('TECH')
        original_count = len(original_companies)

        # Try to modify the returned list
        original_companies.append('FAKE_TICKER')
        original_companies.remove('AAPL')

        # Get companies again - should be unchanged
        new_companies = get_sector_companies('TECH')
        assert len(new_companies) == original_count
        assert 'AAPL' in new_companies
        assert 'FAKE_TICKER' not in new_companies

    def test_all_sectors_have_minimum_diversity(self):
        """Test that each sector has diverse company representation"""
        for sector_code in list_sectors():
            config = get_sector_config(sector_code)

            # Should have at least 40 companies for robust benchmarks
            assert len(config.companies) >= 40, \
                f"Sector {sector_code} needs more companies for robust analysis"

            # Should have at least 3 key metrics
            assert len(config.key_metrics) >= 3, \
                f"Sector {sector_code} needs more key metrics"

            # Should have description
            assert config.description is not None, \
                f"Sector {sector_code} missing description"

    def test_no_cross_sector_duplicates(self):
        """Test that no company appears in multiple sectors"""
        all_companies = {}

        for sector_code in list_sectors():
            companies = get_sector_companies(sector_code)

            for company in companies:
                if company in all_companies:
                    pytest.fail(
                        f"Company {company} appears in both "
                        f"{all_companies[company]} and {sector_code}"
                    )
                all_companies[company] = sector_code

        # Verify total count
        assert len(all_companies) >= 200


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    def test_portfolio_analysis_scenario(self):
        """Simulate analyzing a diversified portfolio"""
        portfolio = [
            'AAPL',   # Tech
            'MSFT',   # Tech
            'BHP',    # Mining
            'RIO',    # Mining
            'XOM',    # Oil & Gas
            'CVX',    # Oil & Gas
            'WMT',    # Retail
            'TGT',    # Retail
        ]

        sector_distribution = {}

        for ticker in portfolio:
            sector = get_company_sector(ticker)
            assert sector is not None, f"{ticker} not found in any sector"

            sector_distribution[sector] = sector_distribution.get(sector, 0) + 1

        # Should be diversified across at least 3 sectors
        assert len(sector_distribution) >= 3

        # Each sector should have representation
        for sector, count in sector_distribution.items():
            assert count >= 1

    def test_sector_peer_identification_scenario(self):
        """Simulate finding peer companies for benchmarking"""
        target_company = 'AAPL'

        # Step 1: Identify sector
        sector = get_company_sector(target_company)
        assert sector == 'TECH'

        # Step 2: Get all sector peers
        all_peers = get_sector_companies(sector)

        # Step 3: Remove target company to get pure peers
        peers = [c for c in all_peers if c != target_company]

        # Should have plenty of peers for comparison
        assert len(peers) >= 50

        # Key tech companies should be in peers
        assert 'MSFT' in peers
        assert 'GOOGL' in peers
        assert 'META' in peers

    def test_sector_rotation_strategy_scenario(self):
        """Simulate sector rotation investment strategy"""
        # Get summary of all sectors
        summary = get_sector_summary()

        # Should have multiple sectors to rotate between
        assert len(summary) >= 4

        # Each sector should have sufficient companies for diversification
        for sector_code, info in summary.items():
            assert info['company_count'] >= 40

            # Get key metrics for analysis
            key_metrics = info['key_metrics']
            assert len(key_metrics) >= 3

            # Verify we can access companies
            companies = get_sector_companies(sector_code)
            assert len(companies) == info['company_count']

    def test_new_company_classification_scenario(self):
        """Simulate classifying a new company into correct sector"""
        # Test companies that clearly belong to specific sectors
        test_cases = {
            'NVDA': 'TECH',      # Clearly tech (semiconductors)
            'NEM': 'MINING',     # Clearly mining (gold)
            'SLB': 'OIL_GAS',    # Clearly oil services
            'COST': 'RETAIL',    # Clearly retail
        }

        for ticker, expected_sector in test_cases.items():
            actual_sector = get_company_sector(ticker)
            assert actual_sector == expected_sector, \
                f"{ticker} classified as {actual_sector}, expected {expected_sector}"


class TestPerformanceAndScalability:
    """Test performance characteristics"""

    def test_lookup_performance(self):
        """Test that lookups are fast enough for production use"""
        import time

        # Test sector validation (should be near-instant)
        start = time.time()
        for _ in range(1000):
            validate_sector('TECH')
        duration = time.time() - start
        assert duration < 0.1, f"Sector validation too slow: {duration}s"

        # Test company lookup (should be fast)
        start = time.time()
        for _ in range(1000):
            get_company_sector('AAPL')
        duration = time.time() - start
        assert duration < 1.0, f"Company lookup too slow: {duration}s"

    def test_summary_generation_performance(self):
        """Test that summary generation is reasonable"""
        import time

        start = time.time()
        summary = get_sector_summary()
        duration = time.time() - start

        # Should generate summary quickly
        assert duration < 0.1, f"Summary generation too slow: {duration}s"
        assert len(summary) == 4
