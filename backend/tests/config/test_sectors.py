"""
Tests for sector configuration system
"""
import pytest
from backend.config.sectors import SectorConfig


class TestSectorConfig:
    """Test SectorConfig dataclass"""

    def test_sector_config_creation(self):
        """Test basic SectorConfig creation"""
        config = SectorConfig(
            code='TEST',
            name='Test Sector',
            companies=['AAPL', 'MSFT', 'GOOGL'],
            min_peers=3,
            key_metrics=['ROE', 'NetMargin', 'ROIC']
        )

        assert config.code == 'TEST'
        assert config.name == 'Test Sector'
        assert len(config.companies) == 3
        assert config.min_peers == 3
        assert len(config.key_metrics) == 3
        assert config.description is None

    def test_sector_config_with_description(self):
        """Test SectorConfig with optional description"""
        config = SectorConfig(
            code='TEST',
            name='Test Sector',
            companies=['AAPL', 'MSFT'],
            min_peers=2,
            key_metrics=['ROE'],
            description='Test sector for validation'
        )

        assert config.description == 'Test sector for validation'

    def test_sector_config_validation_min_peers(self):
        """Test that sector must meet minimum peer requirement"""
        with pytest.raises(ValueError, match="requires minimum"):
            SectorConfig(
                code='TEST',
                name='Test Sector',
                companies=['AAPL'],  # Only 1 company
                min_peers=3,  # But requires 3
                key_metrics=['ROE']
            )

    def test_sector_config_validation_no_companies(self):
        """Test that sector must have at least one company"""
        with pytest.raises(ValueError, match="at least one company"):
            SectorConfig(
                code='TEST',
                name='Test Sector',
                companies=[],  # Empty list
                min_peers=0,
                key_metrics=['ROE']
            )

    def test_sector_config_validation_no_metrics(self):
        """Test that sector must have at least one key metric"""
        with pytest.raises(ValueError, match="at least one key metric"):
            SectorConfig(
                code='TEST',
                name='Test Sector',
                companies=['AAPL'],
                min_peers=1,
                key_metrics=[]  # Empty list
            )


class TestSectorDefinitions:
    """Test SECTOR_DEFINITIONS dictionary"""

    def test_sector_definitions_exist(self):
        """Test that SECTOR_DEFINITIONS is defined"""
        from backend.config.sectors import SECTOR_DEFINITIONS

        assert SECTOR_DEFINITIONS is not None
        assert isinstance(SECTOR_DEFINITIONS, dict)
        assert len(SECTOR_DEFINITIONS) > 0

    def test_all_sectors_defined(self):
        """Test that all expected sectors are defined"""
        from backend.config.sectors import SECTOR_DEFINITIONS

        expected_sectors = {'TECH', 'MINING', 'OIL_GAS', 'RETAIL'}
        actual_sectors = set(SECTOR_DEFINITIONS.keys())

        assert actual_sectors == expected_sectors

    def test_tech_sector_config(self):
        """Test TECH sector configuration"""
        from backend.config.sectors import SECTOR_DEFINITIONS

        tech = SECTOR_DEFINITIONS['TECH']

        assert tech.code == 'TECH'
        assert tech.name == 'Technology'
        assert len(tech.companies) == 61  # UPDATED: Ultra-robust version
        assert tech.min_peers == 15
        assert 'AAPL' in tech.companies
        assert 'MSFT' in tech.companies
        assert 'NVDA' in tech.companies
        assert 'ROE' in tech.key_metrics
        assert 'ROIC' in tech.key_metrics

    def test_mining_sector_config(self):
        """Test MINING sector configuration"""
        from backend.config.sectors import SECTOR_DEFINITIONS

        mining = SECTOR_DEFINITIONS['MINING']

        assert mining.code == 'MINING'
        assert mining.name == 'Mining & Metals'
        assert len(mining.companies) == 41  # UPDATED: Ultra-robust version
        assert mining.min_peers == 15
        assert 'BHP' in mining.companies
        assert 'RIO' in mining.companies
        assert 'FCX' in mining.companies
        assert 'NEM' in mining.companies
        assert 'ROA' in mining.key_metrics
        assert 'DebtToEquity' in mining.key_metrics

    def test_oil_gas_sector_config(self):
        """Test OIL_GAS sector configuration"""
        from backend.config.sectors import SECTOR_DEFINITIONS

        oil = SECTOR_DEFINITIONS['OIL_GAS']

        assert oil.code == 'OIL_GAS'
        assert oil.name == 'Oil & Gas'
        assert len(oil.companies) == 54  # UPDATED: Ultra-robust version
        assert oil.min_peers == 15
        assert 'XOM' in oil.companies
        assert 'CVX' in oil.companies
        assert 'COP' in oil.companies
        assert 'SLB' in oil.companies
        assert 'DebtToEquity' in oil.key_metrics
        assert 'InterestCoverage' in oil.key_metrics

    def test_retail_sector_config(self):
        """Test RETAIL sector configuration"""
        from backend.config.sectors import SECTOR_DEFINITIONS

        retail = SECTOR_DEFINITIONS['RETAIL']

        assert retail.code == 'RETAIL'
        assert retail.name == 'Retail'
        assert len(retail.companies) == 49  # UPDATED: Ultra-robust version
        assert retail.min_peers == 15
        assert 'WMT' in retail.companies
        assert 'TGT' in retail.companies
        assert 'COST' in retail.companies
        assert 'HD' in retail.companies
        assert 'InventoryTurnover' in retail.key_metrics
        assert 'AssetTurnover' in retail.key_metrics

    def test_all_sectors_meet_min_peers(self):
        """Test that all sectors have enough companies to meet min_peers"""
        from backend.config.sectors import SECTOR_DEFINITIONS

        for code, config in SECTOR_DEFINITIONS.items():
            assert len(config.companies) >= config.min_peers, \
                f"Sector {code} has {len(config.companies)} companies but requires {config.min_peers}"

    def test_no_duplicate_companies_within_sector(self):
        """Test that no sector has duplicate company tickers"""
        from backend.config.sectors import SECTOR_DEFINITIONS

        for code, config in SECTOR_DEFINITIONS.items():
            unique_companies = set(config.companies)
            assert len(unique_companies) == len(config.companies), \
                f"Sector {code} has duplicate companies"

    def test_ultra_robust_coverage(self):
        """Test that we have ultra-robust coverage (200+ companies total)"""
        from backend.config.sectors import SECTOR_DEFINITIONS

        total_companies = sum(len(config.companies) for config in SECTOR_DEFINITIONS.values())

        # Should have 200+ companies for institutional-grade benchmarks
        assert total_companies >= 200, \
            f"Total companies ({total_companies}) should be >= 200 for ultra-robust benchmarks"

    def test_sector_size_balance(self):
        """Test that all sectors have substantial company count (40+ each)"""
        from backend.config.sectors import SECTOR_DEFINITIONS

        for code, config in SECTOR_DEFINITIONS.items():
            # Each sector should have at least 40 companies for robust benchmarks
            # (except we allow some flexibility)
            assert len(config.companies) >= 40, \
                f"Sector {code} has only {len(config.companies)} companies, " \
                f"should have 40+ for ultra-robust benchmarks"


class TestHelperFunctions:
    """Test helper functions for sector configuration"""

    def test_get_sector_config_valid(self):
        """Test getting valid sector configuration"""
        from backend.config.sectors import get_sector_config

        tech = get_sector_config('TECH')
        assert tech.code == 'TECH'
        assert tech.name == 'Technology'

        # Test case insensitive
        tech_lower = get_sector_config('tech')
        assert tech_lower.code == 'TECH'

    def test_get_sector_config_invalid(self):
        """Test getting invalid sector raises ValueError"""
        from backend.config.sectors import get_sector_config

        with pytest.raises(ValueError, match="Sector 'INVALID' not found"):
            get_sector_config('INVALID')

    def test_list_sectors(self):
        """Test listing all sectors"""
        from backend.config.sectors import list_sectors

        sectors = list_sectors()

        assert isinstance(sectors, list)
        assert len(sectors) == 4
        assert 'TECH' in sectors
        assert 'MINING' in sectors
        assert 'OIL_GAS' in sectors
        assert 'RETAIL' in sectors
        # Should be sorted
        assert sectors == sorted(sectors)

    def test_validate_sector_valid(self):
        """Test validating valid sector codes"""
        from backend.config.sectors import validate_sector

        assert validate_sector('TECH') is True
        assert validate_sector('MINING') is True
        assert validate_sector('tech') is True  # Case insensitive

    def test_validate_sector_invalid(self):
        """Test validating invalid sector codes"""
        from backend.config.sectors import validate_sector

        assert validate_sector('INVALID') is False
        assert validate_sector('') is False

    def test_get_sector_companies(self):
        """Test getting companies for a sector"""
        from backend.config.sectors import get_sector_companies

        tech_companies = get_sector_companies('TECH')

        assert isinstance(tech_companies, list)
        assert len(tech_companies) == 61
        assert 'AAPL' in tech_companies
        assert 'MSFT' in tech_companies

        # Verify it returns a copy (modification doesn't affect original)
        original_length = len(tech_companies)
        tech_companies.append('TEST')
        assert len(get_sector_companies('TECH')) == original_length

    def test_get_sector_companies_invalid(self):
        """Test getting companies for invalid sector"""
        from backend.config.sectors import get_sector_companies

        with pytest.raises(ValueError, match="not found"):
            get_sector_companies('INVALID')

    def test_get_company_sector_valid(self):
        """Test finding sector for valid companies"""
        from backend.config.sectors import get_company_sector

        assert get_company_sector('AAPL') == 'TECH'
        assert get_company_sector('aapl') == 'TECH'  # Case insensitive
        assert get_company_sector('BHP') == 'MINING'
        assert get_company_sector('XOM') == 'OIL_GAS'
        assert get_company_sector('WMT') == 'RETAIL'

    def test_get_company_sector_invalid(self):
        """Test finding sector for invalid company"""
        from backend.config.sectors import get_company_sector

        assert get_company_sector('INVALID') is None
        assert get_company_sector('') is None

    def test_get_sector_summary(self):
        """Test getting summary for all sectors"""
        from backend.config.sectors import get_sector_summary

        summary = get_sector_summary()

        assert isinstance(summary, dict)
        assert len(summary) == 4

        # Check TECH sector summary
        tech_summary = summary['TECH']
        assert tech_summary['name'] == 'Technology'
        assert tech_summary['company_count'] == 61
        assert tech_summary['min_peers'] == 15
        assert 'ROE' in tech_summary['key_metrics']
        assert tech_summary['description'] is not None

        # Check all sectors have required fields
        for sector_code, sector_summary in summary.items():
            assert 'name' in sector_summary
            assert 'company_count' in sector_summary
            assert 'min_peers' in sector_summary
            assert 'key_metrics' in sector_summary
            assert 'description' in sector_summary
