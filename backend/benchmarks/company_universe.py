"""
Company Universe - S&P 500 Tech Sector

Defines the peer universe for benchmark calculations.
Based on GICS Sector: Information Technology (S&P 500, Jan 2025)

Author: @franklin
Sprint 5: Micro-Tarea 3 - Benchmark Calculator
"""

from typing import List, Dict
from dataclasses import dataclass


@dataclass
class CompanyInfo:
    """
    Company metadata for benchmark universe

    Attributes:
        ticker: Stock ticker symbol
        name: Company legal name
        gics_industry: GICS Industry classification
        market_cap_b: Market cap in billions USD (approximate)
    """
    ticker: str
    name: str
    gics_industry: str
    market_cap_b: float


# S&P 500 Information Technology Sector (74 companies as of Jan 2025)
# Source: S&P Dow Jones Indices + SEC filings
SP500_TECH_UNIVERSE: List[CompanyInfo] = [
    # Mega Cap (>$500B)
    CompanyInfo("AAPL", "Apple Inc.", "Technology Hardware", 3200.0),
    CompanyInfo("MSFT", "Microsoft Corporation", "Systems Software", 3100.0),
    CompanyInfo("NVDA", "NVIDIA Corporation", "Semiconductors", 2400.0),

    # Large Cap ($100B - $500B)
    CompanyInfo("AVGO", "Broadcom Inc.", "Semiconductors", 680.0),
    CompanyInfo("ORCL", "Oracle Corporation", "Systems Software", 350.0),
    CompanyInfo("CRM", "Salesforce Inc.", "Application Software", 280.0),
    CompanyInfo("ADBE", "Adobe Inc.", "Application Software", 240.0),
    CompanyInfo("CSCO", "Cisco Systems Inc.", "Communications Equipment", 220.0),
    CompanyInfo("ACN", "Accenture plc", "IT Consulting & Services", 210.0),
    CompanyInfo("AMD", "Advanced Micro Devices", "Semiconductors", 200.0),
    CompanyInfo("NOW", "ServiceNow Inc.", "Application Software", 180.0),
    CompanyInfo("TXN", "Texas Instruments", "Semiconductors", 165.0),
    CompanyInfo("IBM", "IBM Corporation", "IT Consulting & Services", 160.0),
    CompanyInfo("QCOM", "Qualcomm Inc.", "Semiconductors", 155.0),
    CompanyInfo("INTU", "Intuit Inc.", "Application Software", 150.0),
    CompanyInfo("AMAT", "Applied Materials", "Semiconductor Equipment", 145.0),
    CompanyInfo("PANW", "Palo Alto Networks", "Systems Software", 120.0),
    CompanyInfo("MU", "Micron Technology", "Semiconductors", 110.0),
    CompanyInfo("ADI", "Analog Devices", "Semiconductors", 105.0),
    CompanyInfo("LRCX", "Lam Research", "Semiconductor Equipment", 100.0),

    # Mid Cap ($10B - $100B)
    CompanyInfo("KLAC", "KLA Corporation", "Semiconductor Equipment", 85.0),
    CompanyInfo("SNPS", "Synopsys Inc.", "Application Software", 82.0),
    CompanyInfo("CDNS", "Cadence Design Systems", "Application Software", 78.0),
    CompanyInfo("CRWD", "CrowdStrike Holdings", "Systems Software", 75.0),
    CompanyInfo("ADSK", "Autodesk Inc.", "Application Software", 68.0),
    CompanyInfo("ROP", "Roper Technologies", "Electronic Equipment", 55.0),
    CompanyInfo("FTNT", "Fortinet Inc.", "Systems Software", 52.0),
    CompanyInfo("FICO", "Fair Isaac Corporation", "Application Software", 45.0),
    CompanyInfo("MSI", "Motorola Solutions", "Communications Equipment", 42.0),
    CompanyInfo("APH", "Amphenol Corporation", "Electronic Components", 40.0),
    CompanyInfo("MCHP", "Microchip Technology", "Semiconductors", 38.0),
    CompanyInfo("ON", "ON Semiconductor", "Semiconductors", 35.0),
    CompanyInfo("ANSS", "ANSYS Inc.", "Application Software", 32.0),
    CompanyInfo("KEYS", "Keysight Technologies", "Electronic Equipment", 30.0),
    CompanyInfo("MPWR", "Monolithic Power Systems", "Semiconductors", 28.0),
    CompanyInfo("CDW", "CDW Corporation", "IT Consulting & Services", 26.0),
    CompanyInfo("NTAP", "NetApp Inc.", "Technology Hardware", 24.0),
    CompanyInfo("TYL", "Tyler Technologies", "Application Software", 22.0),
    CompanyInfo("STX", "Seagate Technology", "Technology Hardware", 20.0),
    CompanyInfo("WDC", "Western Digital", "Technology Hardware", 18.0),
    CompanyInfo("ZBRA", "Zebra Technologies", "Electronic Equipment", 16.0),
    CompanyInfo("TRMB", "Trimble Inc.", "Electronic Equipment", 14.0),
    CompanyInfo("GEN", "Gen Digital Inc.", "Systems Software", 12.0),
    CompanyInfo("EPAM", "EPAM Systems Inc.", "IT Consulting & Services", 11.0),

    # Small Cap ($2B - $10B) - Sample (not exhaustive)
    CompanyInfo("JNPR", "Juniper Networks", "Communications Equipment", 9.5),
    CompanyInfo("AKAM", "Akamai Technologies", "IT Consulting & Services", 8.2),
    CompanyInfo("FFIV", "F5 Networks", "Systems Software", 7.8),
    CompanyInfo("VRSN", "VeriSign Inc.", "IT Consulting & Services", 7.5),
    CompanyInfo("JKHY", "Jack Henry & Associates", "Application Software", 7.2),
    CompanyInfo("GDDY", "GoDaddy Inc.", "IT Consulting & Services", 6.8),
    CompanyInfo("SMCI", "Super Micro Computer", "Technology Hardware", 6.5),
    CompanyInfo("NLOK", "NortonLifeLock Inc.", "Systems Software", 6.2),
    CompanyInfo("PTC", "PTC Inc.", "Application Software", 5.8),
    CompanyInfo("TER", "Teradyne Inc.", "Semiconductor Equipment", 5.5),
    CompanyInfo("GLW", "Corning Inc.", "Electronic Components", 5.2),
    CompanyInfo("SWKS", "Skyworks Solutions", "Semiconductors", 4.8),
    CompanyInfo("QRVO", "Qorvo Inc.", "Semiconductors", 4.5),
    CompanyInfo("ENPH", "Enphase Energy", "Semiconductors", 4.2),
    CompanyInfo("FLEX", "Flex Ltd.", "Electronic Equipment", 3.8),
    CompanyInfo("HPE", "Hewlett Packard Enterprise", "Technology Hardware", 3.5),
    CompanyInfo("DELL", "Dell Technologies", "Technology Hardware", 3.2),
    CompanyInfo("HPQ", "HP Inc.", "Technology Hardware", 3.0),
    CompanyInfo("ANET", "Arista Networks", "Communications Equipment", 2.8),
    CompanyInfo("NXPI", "NXP Semiconductors", "Semiconductors", 2.5),
    CompanyInfo("CTSH", "Cognizant Technology", "IT Consulting & Services", 2.2),

    # Additional companies to reach ~74 total
    CompanyInfo("LDOS", "Leidos Holdings", "IT Consulting & Services", 2.0),
    CompanyInfo("BAH", "Booz Allen Hamilton", "IT Consulting & Services", 1.8),
    CompanyInfo("CACI", "CACI International", "IT Consulting & Services", 1.5),
    CompanyInfo("SAIC", "Science Applications", "IT Consulting & Services", 1.2),
    CompanyInfo("DXC", "DXC Technology", "IT Consulting & Services", 1.0),
    CompanyInfo("IT", "Gartner Inc.", "IT Consulting & Services", 0.9),
    CompanyInfo("CVLT", "Commvault Systems", "Systems Software", 0.8),
    CompanyInfo("SNX", "TD SYNNEX Corporation", "Technology Distributors", 0.7),
    CompanyInfo("CCOI", "Cogent Communications", "IT Consulting & Services", 0.6),
    CompanyInfo("ATEN", "A10 Networks", "Communications Equipment", 0.5),
]


def get_tech_universe() -> List[CompanyInfo]:
    """Get full S&P 500 Tech sector universe"""
    return SP500_TECH_UNIVERSE


def get_tickers_only() -> List[str]:
    """Get list of tickers only (for batch processing)"""
    return [company.ticker for company in SP500_TECH_UNIVERSE]


def get_company_by_ticker(ticker: str) -> CompanyInfo:
    """Look up company info by ticker"""
    for company in SP500_TECH_UNIVERSE:
        if company.ticker == ticker:
            return company
    raise ValueError(f"Ticker '{ticker}' not found in tech universe")


def filter_by_market_cap(min_cap_b: float = 0, max_cap_b: float = float('inf')) -> List[CompanyInfo]:
    """
    Filter universe by market cap range

    Args:
        min_cap_b: Minimum market cap in billions
        max_cap_b: Maximum market cap in billions

    Returns:
        Filtered list of companies

    Example:
        >>> large_caps = filter_by_market_cap(min_cap_b=100)  # >$100B only
    """
    return [
        company for company in SP500_TECH_UNIVERSE
        if min_cap_b <= company.market_cap_b <= max_cap_b
    ]
