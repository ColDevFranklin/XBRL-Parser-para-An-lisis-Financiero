"""
Sector Configuration System

Defines sector-specific configurations including:
- Company tickers per sector
- Minimum peer requirements
- Key metrics for analysis
- Sector metadata
"""
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class SectorConfig:
    """
    Configuration for a specific sector

    Attributes:
        code: Sector code (e.g., 'TECH', 'MINING')
        name: Human-readable sector name
        companies: List of ticker symbols
        min_peers: Minimum companies needed for valid benchmarks
        key_metrics: Most relevant metrics for this sector
        description: Optional sector description
    """
    code: str
    name: str
    companies: List[str]
    min_peers: int
    key_metrics: List[str]
    description: Optional[str] = None

    def __post_init__(self):
        """Validate configuration on initialization"""
        if len(self.companies) < self.min_peers:
            raise ValueError(
                f"Sector {self.code} has {len(self.companies)} companies "
                f"but requires minimum {self.min_peers} for valid benchmarks"
            )

        if not self.companies:
            raise ValueError(f"Sector {self.code} must have at least one company")

        if not self.key_metrics:
            raise ValueError(f"Sector {self.code} must have at least one key metric")


# ============================================================================
# SECTOR DEFINITIONS - ULTRA-ROBUST VERSION
# ============================================================================

SECTOR_DEFINITIONS: Dict[str, SectorConfig] = {
    'TECH': SectorConfig(
        code='TECH',
        name='Technology',
        companies=[
            # FAANG + Mega Cap
            'AAPL',   # Apple Inc.
            'MSFT',   # Microsoft Corporation
            'GOOGL',  # Alphabet Inc. (Class A)
            'GOOG',   # Alphabet Inc. (Class C)
            'META',   # Meta Platforms Inc.
            'AMZN',   # Amazon.com Inc.
            'NVDA',   # NVIDIA Corporation
            'TSLA',   # Tesla Inc.

            # Software & Cloud
            'ORCL',   # Oracle Corporation
            'CRM',    # Salesforce Inc.
            'ADBE',   # Adobe Inc.
            'NOW',    # ServiceNow Inc.
            'INTU',   # Intuit Inc.
            'PANW',   # Palo Alto Networks
            'SNOW',   # Snowflake Inc.
            'WDAY',   # Workday Inc.
            'TEAM',   # Atlassian Corporation
            'ZS',     # Zscaler Inc.
            'DDOG',   # Datadog Inc.
            'CRWD',   # CrowdStrike Holdings
            'FTNT',   # Fortinet Inc.
            'PLTR',   # Palantir Technologies
            'NET',    # Cloudflare Inc.
            'MDB',    # MongoDB Inc.
            'DOCN',   # DigitalOcean Holdings

            # Hardware & Devices
            'DELL',   # Dell Technologies
            'HPQ',    # HP Inc.
            'HPE',    # Hewlett Packard Enterprise
            'NTAP',   # NetApp Inc.
            'PSTG',   # Pure Storage Inc.
            'WDC',    # Western Digital
            'STX',    # Seagate Technology

            # Semiconductors
            'INTC',   # Intel Corporation
            'AMD',    # Advanced Micro Devices
            'QCOM',   # Qualcomm Inc.
            'AVGO',   # Broadcom Inc.
            'TXN',    # Texas Instruments
            'MU',     # Micron Technology
            'AMAT',   # Applied Materials
            'LRCX',   # Lam Research
            'KLAC',   # KLA Corporation
            'ASML',   # ASML Holding (ADR)
            'MRVL',   # Marvell Technology
            'NXPI',   # NXP Semiconductors
            'ADI',    # Analog Devices
            'MCHP',   # Microchip Technology
            'ON',     # ON Semiconductor
            'SWKS',   # Skyworks Solutions
            'QRVO',   # Qorvo Inc.

            # Media & Entertainment
            'NFLX',   # Netflix Inc.
            'DIS',    # Walt Disney Company
            'SPOT',   # Spotify Technology
            'ROKU',   # Roku Inc.

            # E-commerce & Platforms
            'EBAY',   # eBay Inc.
            'SHOP',   # Shopify Inc.
            'SQ',     # Block Inc. (Square)
            'PYPL',   # PayPal Holdings

            # Communication Equipment
            'CSCO',   # Cisco Systems
            'JNPR',   # Juniper Networks
            'ANET',   # Arista Networks
            'FFIV',   # F5 Inc.
        ],
        min_peers=15,
        key_metrics=['ROE', 'ROIC', 'NetMargin', 'AssetTurnover', 'RevenueGrowth'],
        description='Technology companies including software, hardware, semiconductors, and digital platforms'
    ),

    'MINING': SectorConfig(
        code='MINING',
        name='Mining & Metals',
        companies=[
            # Diversified Miners (Global Major)
            'BHP',    # BHP Group (ADR)
            'RIO',    # Rio Tinto (ADR)
            'VALE',   # Vale S.A. (ADR)
            'GLNCY',  # Glencore (ADR)

            # Copper (Primary Focus)
            'FCX',    # Freeport-McMoRan Inc.
            'SCCO',   # Southern Copper Corporation
            'IVN',    # Ivanhoe Mines Ltd.
            'HBM',    # Hudbay Minerals Inc.
            'TECK',   # Teck Resources Ltd.
            'FM',     # First Quantum Minerals
            'CPER',   # United States Copper Index Fund

            # Gold (Major Producers)
            'NEM',    # Newmont Corporation
            'GOLD',   # Barrick Gold Corporation
            'AEM',    # Agnico Eagle Mines
            'FNV',    # Franco-Nevada Corporation
            'WPM',    # Wheaton Precious Metals
            'KGC',    # Kinross Gold Corporation
            'AU',     # AngloGold Ashanti (ADR)
            'IAG',    # IAMGOLD Corporation
            'BTG',    # B2Gold Corp.
            'PAAS',   # Pan American Silver
            'HL',     # Hecla Mining Company
            'EGO',    # Eldorado Gold Corporation
            'AGI',    # Alamos Gold Inc.
            'GFI',    # Gold Fields Ltd. (ADR)

            # Silver (Specialized)
            'CDE',    # Coeur Mining Inc.
            'FSM',    # Fortuna Silver Mines
            'MAG',    # MAG Silver Corp.

            # Steel & Iron Ore
            'NUE',    # Nucor Corporation
            'STLD',   # Steel Dynamics Inc.
            'CLF',    # Cleveland-Cliffs Inc.
            'X',      # United States Steel
            'MT',     # ArcelorMittal (ADR)
            'RS',     # Reliance Steel & Aluminum
            'CMC',    # Commercial Metals Company

            # Aluminum
            'AA',     # Alcoa Corporation
            'CENX',   # Century Aluminum Company

            # Rare Earth & Specialty Metals
            'MP',     # MP Materials Corp.
            'LAC',    # Lithium Americas Corp.
            'ALB',    # Albemarle Corporation (Lithium)
            'SQM',    # Sociedad Química y Minera (Lithium)
        ],
        min_peers=15,
        key_metrics=['ROA', 'DebtToEquity', 'CurrentRatio', 'AssetTurnover', 'InterestCoverage'],
        description='Mining and metals companies: diversified miners, copper, gold, silver, steel, aluminum, and specialty metals'
    ),

    'OIL_GAS': SectorConfig(
        code='OIL_GAS',
        name='Oil & Gas',
        companies=[
            # Integrated Oil & Gas (Super Majors)
            'XOM',    # Exxon Mobil Corporation
            'CVX',    # Chevron Corporation
            'COP',    # ConocoPhillips
            'BP',     # BP plc (ADR)
            'SHEL',   # Shell plc (ADR)
            'TTE',    # TotalEnergies SE (ADR)
            'E',      # Eni S.p.A. (ADR)

            # Exploration & Production (Large Cap)
            'EOG',    # EOG Resources Inc.
            'OXY',    # Occidental Petroleum
            'HES',    # Hess Corporation
            'DVN',    # Devon Energy Corporation
            'FANG',   # Diamondback Energy Inc.
            'PXD',    # Pioneer Natural Resources
            'MRO',    # Marathon Oil Corporation
            'APA',    # APA Corporation
            'CTRA',   # Coterra Energy Inc.
            'OVV',    # Ovintiv Inc.
            'CNQ',    # Canadian Natural Resources (ADR)
            'SU',     # Suncor Energy Inc.
            'IMO',    # Imperial Oil Ltd.
            'CVE',    # Cenovus Energy Inc.

            # Exploration & Production (Mid Cap)
            'MTDR',   # Matador Resources Company
            'SM',     # SM Energy Company
            'RRC',    # Range Resources Corporation
            'AR',     # Antero Resources Corporation
            'CHRD',   # Chord Energy Corporation
            'PR',     # Permian Resources Corporation
            'MGY',    # Magnolia Oil & Gas Corporation
            'VTLE',   # Vital Energy Inc.

            # Natural Gas Focused
            'EQT',    # EQT Corporation
            'CHK',    # Chesapeake Energy Corporation
            'SWN',    # Southwestern Energy Company
            'CNX',    # CNX Resources Corporation

            # Refining & Marketing
            'MPC',    # Marathon Petroleum Corporation
            'PSX',    # Phillips 66
            'VLO',    # Valero Energy Corporation
            'DK',     # Delek US Holdings Inc.
            'PBF',    # PBF Energy Inc.
            'DINO',   # HF Sinclair Corporation

            # Oilfield Services (Large Cap)
            'SLB',    # Schlumberger NV
            'HAL',    # Halliburton Company
            'BKR',    # Baker Hughes Company
            'NOV',    # NOV Inc.
            'FTI',    # TechnipFMC plc
            'CHX',    # ChampionX Corporation
            'WTTR',   # Select Water Solutions Inc.
            'HP',     # Helmerich & Payne Inc.
            'PTEN',   # Patterson-UTI Energy Inc.

            # Midstream & Infrastructure
            'EPD',    # Enterprise Products Partners
            'MMP',    # Magellan Midstream Partners
            'PAA',    # Plains All American Pipeline
            'WMB',    # Williams Companies Inc.
            'KMI',    # Kinder Morgan Inc.
            'OKE',    # ONEOK Inc.
        ],
        min_peers=15,
        key_metrics=['ROE', 'DebtToEquity', 'InterestCoverage', 'FCFGrowth', 'CurrentRatio'],
        description='Oil & Gas: integrated majors, E&P, refining, natural gas, oilfield services, and midstream infrastructure'
    ),

    'RETAIL': SectorConfig(
        code='RETAIL',
        name='Retail',
        companies=[
            # General Merchandise (Big Box)
            'WMT',    # Walmart Inc.
            'TGT',    # Target Corporation
            'COST',   # Costco Wholesale Corporation
            'DG',     # Dollar General Corporation
            'DLTR',   # Dollar Tree Inc.
            'BIG',    # Big Lots Inc.

            # Home Improvement & Garden
            'HD',     # Home Depot Inc.
            'LOW',    # Lowe's Companies Inc.

            # Specialty Retail (Off-Price)
            'TJX',    # TJX Companies Inc.
            'ROST',   # Ross Stores Inc.
            'BURL',   # Burlington Stores Inc.

            # Electronics & Appliances
            'BBY',    # Best Buy Co. Inc.
            'CONN',   # Conn's Inc.

            # Apparel & Fashion (Mass Market)
            'GPS',    # Gap Inc.
            'AEO',    # American Eagle Outfitters
            'ANF',    # Abercrombie & Fitch Co.
            'URBN',   # Urban Outfitters Inc.
            'EXPR',   # Express Inc.
            'CHS',    # Chico's FAS Inc.

            # Apparel & Fashion (Premium)
            'NKE',    # Nike Inc.
            'LULU',   # Lululemon Athletica Inc.
            'DECK',   # Deckers Outdoor Corporation
            'VFC',    # VF Corporation (Vans, North Face)
            'GOOS',   # Canada Goose Holdings Inc.

            # Department Stores
            'M',      # Macy's Inc.
            'KSS',    # Kohl's Corporation
            'JWN',    # Nordstrom Inc.
            'DDS',    # Dillard's Inc.

            # Automotive Retail
            'AAP',    # Advance Auto Parts Inc.
            'AZO',    # AutoZone Inc.
            'ORLY',   # O'Reilly Automotive Inc.
            'GPC',    # Genuine Parts Company
            'LAD',    # Lithia Motors Inc.
            'AN',     # AutoNation Inc.
            'ABG',    # Asbury Automotive Group
            'SAH',    # Sonic Automotive Inc.
            'PAG',    # Penske Automotive Group

            # Specialty Retail (Other)
            'ULTA',   # Ulta Beauty Inc.
            'FL',     # Foot Locker Inc.
            'DKS',    # Dick's Sporting Goods Inc.
            'ASO',    # Academy Sports and Outdoors
            'HIBB',   # Hibbett Sports Inc.
            'PETS',   # PetMed Express Inc.
            'CHWY',   # Chewy Inc.

            # Furniture & Home Furnishings
            'WSM',    # Williams-Sonoma Inc.
            'RH',     # RH (Restoration Hardware)
            'BBBY',   # Bed Bath & Beyond Inc.

            # Warehouse Clubs
            'BJ',     # BJ's Wholesale Club Holdings

            # Convenience Stores
            'CASY',   # Casey's General Stores Inc.
        ],
        min_peers=15,
        key_metrics=['InventoryTurnover', 'AssetTurnover', 'NetMargin', 'ROE', 'CurrentRatio'],
        description='Retail: general merchandise, home improvement, apparel, automotive, specialty, department stores, and e-commerce'
    ),
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_sector_config(sector_code: str) -> SectorConfig:
    """
    Get configuration for a specific sector

    Args:
        sector_code: Sector code (e.g., 'TECH', 'MINING')

    Returns:
        SectorConfig object

    Raises:
        ValueError: If sector code is not found

    Examples:
        >>> config = get_sector_config('TECH')
        >>> print(config.name)
        'Technology'
    """
    sector_code = sector_code.upper()

    if sector_code not in SECTOR_DEFINITIONS:
        available = ', '.join(sorted(SECTOR_DEFINITIONS.keys()))
        raise ValueError(
            f"Sector '{sector_code}' not found. "
            f"Available sectors: {available}"
        )

    return SECTOR_DEFINITIONS[sector_code]


def list_sectors() -> List[str]:
    """
    List all available sector codes

    Returns:
        List of sector codes (e.g., ['TECH', 'MINING', 'OIL_GAS', 'RETAIL'])

    Examples:
        >>> sectors = list_sectors()
        >>> print(sectors)
        ['MINING', 'OIL_GAS', 'RETAIL', 'TECH']
    """
    return sorted(SECTOR_DEFINITIONS.keys())


def validate_sector(sector_code: str) -> bool:
    """
    Check if a sector code is valid

    Args:
        sector_code: Sector code to validate

    Returns:
        True if sector exists, False otherwise

    Examples:
        >>> validate_sector('TECH')
        True
        >>> validate_sector('INVALID')
        False
    """
    return sector_code.upper() in SECTOR_DEFINITIONS


def get_sector_companies(sector_code: str) -> List[str]:
    """
    Get list of companies for a specific sector

    Args:
        sector_code: Sector code (e.g., 'TECH', 'MINING')

    Returns:
        List of company ticker symbols

    Raises:
        ValueError: If sector code is not found

    Examples:
        >>> companies = get_sector_companies('TECH')
        >>> len(companies)
        61
        >>> 'AAPL' in companies
        True
    """
    config = get_sector_config(sector_code)
    return config.companies.copy()  # Return copy to prevent modification


def get_company_sector(ticker: str) -> Optional[str]:
    """
    Find which sector a company belongs to

    Args:
        ticker: Company ticker symbol (e.g., 'AAPL', 'BHP')

    Returns:
        Sector code if found, None otherwise

    Examples:
        >>> get_company_sector('AAPL')
        'TECH'
        >>> get_company_sector('BHP')
        'MINING'
        >>> get_company_sector('INVALID')
        None
    """
    ticker = ticker.upper()

    for sector_code, config in SECTOR_DEFINITIONS.items():
        if ticker in config.companies:
            return sector_code

    return None


def get_sector_summary() -> Dict[str, Dict[str, any]]:
    """
    Get summary statistics for all sectors

    Returns:
        Dictionary with sector code as key and summary dict as value

    Examples:
        >>> summary = get_sector_summary()
        >>> summary['TECH']['company_count']
        61
        >>> summary['TECH']['name']
        'Technology'
    """
    summary = {}

    for code, config in SECTOR_DEFINITIONS.items():
        summary[code] = {
            'name': config.name,
            'company_count': len(config.companies),
            'min_peers': config.min_peers,
            'key_metrics': config.key_metrics,
            'description': config.description
        }

    return summary
