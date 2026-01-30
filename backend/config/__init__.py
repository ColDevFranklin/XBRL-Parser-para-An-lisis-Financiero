"""
Configuration module for XBRL Financial Analyzer
"""
from backend.config.sectors import (
    SectorConfig,
    SECTOR_DEFINITIONS,
    get_sector_config,
    list_sectors,
    validate_sector,
    get_sector_companies,
    get_company_sector,
    get_sector_summary,
)

__all__ = [
    'SectorConfig',
    'SECTOR_DEFINITIONS',
    'get_sector_config',
    'list_sectors',
    'validate_sector',
    'get_sector_companies',
    'get_company_sector',
    'get_sector_summary',
]
