#!/usr/bin/env python3
"""
Batch XBRL Downloader - S&P 500 Tech Sector (FIXED VERSION)

Downloads XBRL instance documents directly from SEC EDGAR Archives.
Uses correct URL pattern: /Archives/edgar/data/{CIK}/{ACCESSION}/{FILE}.xml

Author: @franklin
Sprint 5: Micro-Tarea 3 - Data Collection (FIXED)
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import argparse
import time
import requests
from typing import List, Dict, Optional
import json
from datetime import datetime
import re

from backend.benchmarks.company_universe import get_tech_universe, CompanyInfo


class SECDownloader:
    """
    Downloads XBRL files directly from SEC EDGAR Archives

    Correct URL pattern:
    https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION-NO-DASHES}/{TICKER}-{DATE}.xml
    """

    # CIK mapping for S&P 500 Tech companies
    CIK_MAP = {
        'AAPL': '0000320193',
        'MSFT': '0000789019',
        'NVDA': '0001045810',
        'AVGO': '0001730168',
        'ORCL': '0001341439',
        'CRM': '0001108524',
        'ADBE': '0000796343',
        'CSCO': '0000858877',
        'ACN': '0001467373',
        'AMD': '0000002488',
        'NOW': '0001373715',
        'TXN': '0000097476',
        'IBM': '0000051143',
        'QCOM': '0000804328',
        'INTU': '0000896878',
        'AMAT': '0000006951',
        'PANW': '0001327567',
        'MU': '0000723125',
        'ADI': '0000006281',
        'LRCX': '0000707549',
    }

    def __init__(self, output_dir: str = 'data', rate_limit: float = 0.15):
        """
        Initialize downloader

        Args:
            output_dir: Output directory for XBRL files
            rate_limit: Seconds between requests (SEC allows ~10/sec, we use 6/sec)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.rate_limit = rate_limit
        self.user_agent = "XBRL-Analyzer/1.0 (franklin@company.com)"  # Required by SEC

        self.headers = {
            'User-Agent': self.user_agent,
            'Accept-Encoding': 'gzip, deflate',
        }

        self.stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0
        }

    def download_company_filings(
        self,
        ticker: str,
        years: int = 4
    ) -> Dict[str, str]:
        """
        Download 10-K filings for a company

        Args:
            ticker: Company ticker
            years: Number of years to download

        Returns:
            Dict mapping year to local filepath
        """
        cik = self.CIK_MAP.get(ticker)
        if not cik:
            print(f"   ⚠️  {ticker}: CIK not found (skipping)")
            return {}

        # Create company subdirectory (flat structure for compatibility)
        downloaded_files = {}
        current_year = datetime.now().year

        for year_offset in range(years):
            target_year = current_year - year_offset

            # Check if file already exists (legacy format)
            legacy_files = [
                self.output_dir / f"{ticker.lower()}_10k_{target_year}_xbrl.xml",
                self.output_dir / f"{ticker.lower()}_10k_xbrl.xml"  # Most recent
            ]

            for legacy_file in legacy_files:
                if legacy_file.exists():
                    print(f"   ⏭️  {ticker} {target_year}: Already exists (legacy)")
                    downloaded_files[str(target_year)] = str(legacy_file)
                    self.stats['skipped'] += 1
                    continue

            # Find filing for target year
            try:
                filing_info = self._find_10k_filing(cik, target_year)

                if not filing_info:
                    print(f"   ❌ {ticker} {target_year}: 10-K not found")
                    self.stats['failed'] += 1
                    continue

                # Download XBRL file
                print(f"   📥 {ticker} {target_year}: Downloading...")

                xbrl_url = filing_info['xbrl_url']
                output_file = self.output_dir / f"{ticker.lower()}_10k_{target_year}_xbrl.xml"

                success = self._download_file(xbrl_url, output_file)

                if success:
                    downloaded_files[str(target_year)] = str(output_file)
                    print(f"   ✅ {ticker} {target_year}: Downloaded")
                    self.stats['success'] += 1
                else:
                    print(f"   ❌ {ticker} {target_year}: Download failed")
                    self.stats['failed'] += 1

                # Rate limiting
                time.sleep(self.rate_limit)

            except Exception as e:
                print(f"   ❌ {ticker} {target_year}: Error - {e}")
                self.stats['failed'] += 1

        return downloaded_files

    def _find_10k_filing(self, cik: str, year: int) -> Optional[Dict]:
        """
        Find 10-K filing for a specific year using SEC submissions API

        Args:
            cik: Company CIK (with leading zeros)
            year: Filing year

        Returns:
            Dict with filing info or None
        """
        # Remove leading zeros for API
        cik_no_zeros = cik.lstrip('0')

        # SEC submissions endpoint
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            filings = data.get('filings', {}).get('recent', {})

            forms = filings.get('form', [])
            filing_dates = filings.get('filingDate', [])
            accession_numbers = filings.get('accessionNumber', [])
            primary_documents = filings.get('primaryDocument', [])

            # Find 10-K for target year (or filed in year+1)
            for idx, form in enumerate(forms):
                if form != '10-K':
                    continue

                filing_date = filing_dates[idx]
                filing_year = int(filing_date.split('-')[0])

                # 10-K for fiscal year X is typically filed in year X+1
                if filing_year in [year, year + 1]:
                    accession = accession_numbers[idx]
                    primary_doc = primary_documents[idx]

                    # Construct XBRL URL
                    accession_no_dashes = accession.replace('-', '')

                    # Try instance document (ends in .xml or _htm.xml)
                    # Pattern: {ticker}-{date}.xml or {ticker}-{date}_htm.xml
                    base_url = f"https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/{accession_no_dashes}"

                    # Try common naming patterns
                    possible_files = [
                        primary_doc.replace('.htm', '.xml'),  # Primary doc as XML
                        primary_doc.replace('.htm', '_htm.xml'),  # Alternative pattern
                        f"{primary_doc.split('.')[0]}.xml",  # Base name + .xml
                    ]

                    for xml_file in possible_files:
                        xbrl_url = f"{base_url}/{xml_file}"

                        # Quick HEAD request to check if file exists
                        try:
                            head_response = requests.head(xbrl_url, headers=self.headers, timeout=5)
                            if head_response.status_code == 200:
                                return {
                                    'xbrl_url': xbrl_url,
                                    'accession': accession,
                                    'filing_date': filing_date
                                }
                        except:
                            continue

            return None

        except Exception as e:
            print(f"      Error finding filing: {e}")
            return None

    def _download_file(self, url: str, output_path: Path) -> bool:
        """
        Download file from URL to output path

        Args:
            url: Source URL
            output_path: Destination path

        Returns:
            True if successful
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            # Verify it's XML (not HTML)
            content = response.text
            if not content.strip().startswith('<?xml') and '<html' in content.lower():
                print(f"      ERROR: Downloaded HTML instead of XML")
                return False

            # Save to disk
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"      Download error: {e}")
            return False

    def download_universe(
        self,
        universe: List[CompanyInfo],
        years: int = 4,
        max_companies: int = None
    ) -> Dict[str, Dict[str, str]]:
        """
        Download filings for entire universe

        Args:
            universe: List of CompanyInfo objects
            years: Number of years to download
            max_companies: Optional limit

        Returns:
            Dict mapping ticker to downloaded files
        """
        # Filter to companies we have CIKs for
        available_companies = [c for c in universe if c.ticker in self.CIK_MAP]

        if max_companies:
            available_companies = available_companies[:max_companies]

        total = len(available_companies)

        print(f"\n{'='*70}")
        print(f"📥 BATCH XBRL DOWNLOAD (FIXED VERSION)")
        print(f"{'='*70}")
        print(f"   Universe: {total} companies (with CIKs)")
        print(f"   Years: {years}")
        print(f"   Output: {self.output_dir}")
        print(f"   Rate limit: {self.rate_limit}s/request")
        print(f"\n")

        results = {}

        for idx, company in enumerate(available_companies, 1):
            print(f"[{idx:3d}/{total:3d}] {company.ticker:6s} - {company.name}")

            files = self.download_company_filings(company.ticker, years=years)
            results[company.ticker] = files

        # Summary
        print(f"\n{'='*70}")
        print(f"📊 DOWNLOAD SUMMARY")
        print(f"{'='*70}")
        print(f"   ✅ Success: {self.stats['success']}")
        print(f"   ❌ Failed: {self.stats['failed']}")
        print(f"   ⏭️  Skipped (cached): {self.stats['skipped']}")
        print(f"   📁 Total files: {self.stats['success'] + self.stats['skipped']}")
        print(f"\n")

        return results


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Download XBRL filings for S&P 500 Tech sector'
    )
    parser.add_argument(
        '--years',
        type=int,
        default=4,
        help='Number of years to download (default: 4)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data',
        help='Output directory (default: data)'
    )
    parser.add_argument(
        '--max-companies',
        type=int,
        default=None,
        help='Maximum companies to download'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: download only first 3 companies'
    )

    args = parser.parse_args()

    if args.test:
        print("🧪 TEST MODE: Downloading first 3 companies only")
        args.max_companies = 3

    # Get universe
    universe = get_tech_universe()

    # Initialize downloader
    downloader = SECDownloader(output_dir=args.output)

    # Download
    results = downloader.download_universe(
        universe=universe,
        years=args.years,
        max_companies=args.max_companies
    )

    # Save manifest
    manifest_file = Path(args.output) / 'download_manifest_fixed.json'
    with open(manifest_file, 'w') as f:
        json.dump({
            'downloaded_at': datetime.now().isoformat(),
            'years': args.years,
            'companies': len(results),
            'files': results,
            'stats': downloader.stats
        }, f, indent=2)

    print(f"📄 Manifest saved to: {manifest_file}\n")

    return 0


if __name__ == "__main__":
    exit(main())
