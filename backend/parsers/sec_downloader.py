"""
backend/parsers/sec-downloader.py
SEC EDGAR XBRL Downloader - Hybrid Strategy (Local-First + SEC Fallback)

Features:
- Local-first: Check data/ directory before downloading
- Auto-download: Fetch from SEC EDGAR if file missing
- Batch processing: Download entire sectors efficiently
- Manifest tracking: JSON log of downloads
- Error handling: Skip failed downloads, continue batch
- Real SEC EDGAR integration: Parses filing pages, extracts XBRL URLs

Architecture:
1. Check local cache (data/ directory)
2. If missing, query SEC EDGAR API
3. Parse HTML response to find XBRL instance file
4. Download and save to data/
5. Update manifest for tracking

Author: @franklin
Sprint 6 - Multi-Sector Expansion
Micro-Tarea 2.2: SEC Downloader (Hybrid Strategy)
"""

import os
import json
import time
import requests
from typing import Dict, Optional, List, Tuple
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup


class SECDownloader:
    """
    Hybrid XBRL downloader (local-first, then SEC EDGAR)

    SEC EDGAR API Documentation:
    - Base URL: https://www.sec.gov/cgi-bin/browse-edgar
    - Requires User-Agent header with contact info
    - Rate limit: 10 requests/second (we use 0.15s delays = ~6 req/s)
    - Response: HTML page with filing links

    Attributes:
        data_dir: Local cache directory (default: 'data/')
        manifest_path: Download log (default: 'data/download_manifest.json')
        sec_base_url: SEC EDGAR endpoint
        user_agent: Required by SEC (your email)

    Example:
        >>> downloader = SECDownloader(user_agent='franklin@example.com')
        >>>
        >>> # Single download (hybrid)
        >>> filepath = downloader.get_or_download('AAPL', 2025)
        >>>
        >>> # Batch download (sector)
        >>> files = downloader.download_sector_batch('MINING')
        >>> print(f"Downloaded {len(files)}/41 companies")
    """

    # SEC EDGAR endpoints
    SEC_BASE_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
    SEC_ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data"

    # Rate limiting (SEC allows 10 req/s, we use 6-7 req/s to be safe)
    REQUEST_DELAY = 0.15  # 150ms between requests

    def __init__(
        self,
        data_dir: str = 'data',
        user_agent: str = 'financial-analyzer/1.0 (contact@xbrl-analyzer.com)',
        verbose: bool = True
    ):
        """
        Initialize SEC downloader

        Args:
            data_dir: Directory for cached XBRL files
            user_agent: SEC requires User-Agent with contact info
            verbose: Print progress messages

        Note:
            SEC EDGAR requires User-Agent header with email/contact.
            Default is generic but you should override with real email:

            >>> downloader = SECDownloader(user_agent='yourname@yourdomain.com')
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.manifest_path = self.data_dir / 'download_manifest.json'
        self.user_agent = user_agent
        self.verbose = verbose

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        })

        # Load existing manifest
        self.manifest = self._load_manifest()

        if self.verbose:
            print(f"✓ SECDownloader initialized")
            print(f"  Data dir: {self.data_dir}")
            print(f"  User-Agent: {self.user_agent}")
            print(f"  Manifest: {len(self.manifest.get('downloads', {}))} entries")

    def _load_manifest(self) -> Dict:
        """
        Load download manifest from JSON

        Manifest tracks:
        - Download history (timestamp, source)
        - Failed downloads (for debugging)
        - Performance metrics (download times)

        Returns:
            Dict with 'downloads' and 'failed' keys
        """
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                if self.verbose:
                    print(f"⚠️  Corrupt manifest, creating new one")

        # Default empty manifest
        return {
            'downloads': {},
            'failed': {},
            'metadata': {
                'created': datetime.now().isoformat(),
                'version': '1.0'
            }
        }

    def _save_manifest(self) -> None:
        """Save manifest to JSON"""
        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest, f, indent=2)

    def get_local_file(self, ticker: str, year: int = 2025) -> Optional[str]:
        """
        Check if XBRL file exists locally

        Naming convention (observed from your data/):
        - Pattern: {ticker.lower()}_10k_{year}_xbrl.xml
        - Examples: aapl_10k_2025_xbrl.xml, msft_10k_2024_xbrl.xml

        Args:
            ticker: Stock ticker (e.g., 'AAPL', 'BHP')
            year: Fiscal year (default: 2025)

        Returns:
            Absolute filepath if exists, None otherwise

        Example:
            >>> downloader = SECDownloader()
            >>> path = downloader.get_local_file('AAPL', 2025)
            >>> # Returns: 'data/aapl_10k_2025_xbrl.xml' (if exists)
        """
        filename = f"{ticker.lower()}_10k_{year}_xbrl.xml"
        filepath = self.data_dir / filename

        if filepath.exists():
            if self.verbose:
                print(f"  ✓ Local cache hit: {filename}")
            return str(filepath)

        return None

    def _get_cik_number(self, ticker: str) -> Optional[str]:
        """
        Get CIK number for a ticker from SEC EDGAR

        CIK (Central Index Key) is SEC's unique company identifier.
        Required for querying filings.

        Args:
            ticker: Stock ticker (e.g., 'AAPL')

        Returns:
            CIK number (zero-padded to 10 digits) or None if not found

        Example:
            >>> cik = downloader._get_cik_number('AAPL')
            >>> # Returns: '0000320193'
        """
        try:
            # SEC company search endpoint
            url = f"https://www.sec.gov/cgi-bin/browse-edgar"
            params = {
                'action': 'getcompany',
                'company': ticker,
                'type': '10-K',
                'dateb': '',
                'owner': 'exclude',
                'count': '1'
            }

            time.sleep(self.REQUEST_DELAY)  # Rate limiting
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            # Parse HTML to extract CIK
            soup = BeautifulSoup(response.text, 'html.parser')

            # CIK is in the page title or company info section
            # Pattern: "CIK#: 0000320193" or similar
            cik_elem = soup.find('span', class_='companyName')
            if cik_elem:
                cik_text = cik_elem.get_text()
                # Extract digits from "CIK#: 0000320193"
                if 'CIK' in cik_text:
                    cik = ''.join(filter(str.isdigit, cik_text.split('CIK')[1]))
                    return cik.zfill(10)  # Pad to 10 digits

            # Alternative: Look for CIK in href attributes
            cik_link = soup.find('a', href=lambda x: x and '/cgi-bin/browse-edgar?action=getcompany&CIK=' in x)
            if cik_link:
                href = cik_link['href']
                cik = href.split('CIK=')[1].split('&')[0]
                return cik.zfill(10)

            return None

        except Exception as e:
            if self.verbose:
                print(f"  ✗ Error getting CIK for {ticker}: {e}")
            return None

    def _find_latest_10k_filing(self, cik: str, year: int) -> Optional[Tuple[str, str]]:
        """
        Find latest 10-K filing URL for a given year

        Args:
            cik: CIK number (10 digits, zero-padded)
            year: Fiscal year

        Returns:
            Tuple of (accession_number, filing_url) or None if not found

        Example:
            >>> acc, url = downloader._find_latest_10k_filing('0000320193', 2025)
            >>> # Returns: ('0000320193-25-000001', 'https://sec.gov/...')
        """
        try:
            # Get filings for company
            url = self.SEC_BASE_URL
            params = {
                'action': 'getcompany',
                'CIK': cik,
                'type': '10-K',
                'dateb': f'{year}1231',  # Before Dec 31 of year
                'owner': 'exclude',
                'count': '10'  # Last 10 filings
            }

            time.sleep(self.REQUEST_DELAY)
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find filing table
            filing_table = soup.find('table', class_='tableFile2')
            if not filing_table:
                return None

            # Iterate through rows to find 10-K from target year
            rows = filing_table.find_all('tr')[1:]  # Skip header

            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 4:
                    continue

                # Check if this is a 10-K
                filing_type = cols[0].get_text(strip=True)
                if filing_type != '10-K':
                    continue

                # Check filing date year
                filing_date = cols[3].get_text(strip=True)
                if not filing_date.startswith(str(year)):
                    continue

                # Get documents link
                doc_link = cols[1].find('a', id='documentsbutton')
                if not doc_link:
                    continue

                href = doc_link['href']
                accession = href.split('/')[-1]

                filing_url = f"https://www.sec.gov{href}"

                return (accession, filing_url)

            return None

        except Exception as e:
            if self.verbose:
                print(f"  ✗ Error finding 10-K filing: {e}")
            return None

    def _extract_xbrl_url(self, filing_url: str) -> Optional[str]:
        """
        Extract XBRL instance document URL from filing page

        The filing page lists all documents. We need to find the one
        that ends with '_htm.xml' (XBRL instance) or similar pattern.

        Args:
            filing_url: URL to filing documents page

        Returns:
            Full URL to XBRL instance file or None

        Example:
            >>> xbrl_url = downloader._extract_xbrl_url(filing_url)
            >>> # Returns: 'https://sec.gov/.../aapl-20250928_htm.xml'
        """
        try:
            time.sleep(self.REQUEST_DELAY)
            response = self.session.get(filing_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find document table
            doc_table = soup.find('table', class_='tableFile')
            if not doc_table:
                return None

            # Look for XBRL instance file
            # Patterns: *_htm.xml, *.xml (but not .xsd)
            # Type column should show "EX-101.INS" or "INSTANCE DOCUMENT"

            rows = doc_table.find_all('tr')[1:]  # Skip header

            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 4:
                    continue

                # Check document type
                doc_type = cols[3].get_text(strip=True).upper()

                # XBRL instance indicators
                if 'INSTANCE' in doc_type or 'EX-101.INS' in doc_type:
                    # Get document link
                    doc_link = cols[2].find('a')
                    if doc_link:
                        href = doc_link['href']
                        xbrl_url = f"https://www.sec.gov{href}"
                        return xbrl_url

                # Alternative: Check filename pattern
                filename = cols[2].get_text(strip=True)
                if filename.endswith('_htm.xml') or (filename.endswith('.xml') and not filename.endswith('.xsd')):
                    doc_link = cols[2].find('a')
                    if doc_link:
                        href = doc_link['href']
                        xbrl_url = f"https://www.sec.gov{href}"
                        return xbrl_url

            return None

        except Exception as e:
            if self.verbose:
                print(f"  ✗ Error extracting XBRL URL: {e}")
            return None

    def download_from_sec(self, ticker: str, year: int = 2025) -> Optional[str]:
        """
        Download XBRL from SEC EDGAR

        Full workflow:
        1. Get CIK number for ticker
        2. Find latest 10-K filing for year
        3. Parse filing page to find XBRL instance URL
        4. Download XBRL file
        5. Save to data/ directory
        6. Update manifest

        Args:
            ticker: Stock ticker (e.g., 'BHP')
            year: Fiscal year (default: 2025)

        Returns:
            Filepath if successful, None if failed

        Example:
            >>> filepath = downloader.download_from_sec('BHP', 2025)
            >>> # Returns: 'data/bhp_10k_2025_xbrl.xml'
        """
        start_time = time.time()

        if self.verbose:
            print(f"  → Downloading {ticker} from SEC EDGAR...")

        try:
            # Step 1: Get CIK
            cik = self._get_cik_number(ticker)
            if not cik:
                if self.verbose:
                    print(f"  ✗ CIK not found for {ticker}")
                if 'failed' not in self.manifest:
                    self.manifest['failed'] = {}
                self.manifest['failed'][ticker] = f"CIK not found"
                self._save_manifest()
                return None

            if self.verbose:
                print(f"    CIK: {cik}")

            # Step 2: Find 10-K filing
            filing_info = self._find_latest_10k_filing(cik, year)
            if not filing_info:
                if self.verbose:
                    print(f"  ✗ No 10-K filing found for {year}")
                if 'failed' not in self.manifest:
                    self.manifest['failed'] = {}
                self.manifest['failed'][ticker] = f"No 10-K for {year}"
                self._save_manifest()
                return None

            accession, filing_url = filing_info
            if self.verbose:
                print(f"    Accession: {accession}")

            # Step 3: Extract XBRL URL
            xbrl_url = self._extract_xbrl_url(filing_url)
            if not xbrl_url:
                if self.verbose:
                    print(f"  ✗ XBRL instance not found in filing")
                if 'failed' not in self.manifest:
                    self.manifest['failed'] = {}
                self.manifest['failed'][ticker] = f"XBRL not found in filing"
                self._save_manifest()
                return None

            if self.verbose:
                print(f"    XBRL URL: {xbrl_url.split('/')[-1]}")

            # Step 4: Download XBRL
            time.sleep(self.REQUEST_DELAY)
            response = self.session.get(xbrl_url, timeout=30)
            response.raise_for_status()

            # Step 5: Save to data/
            filename = f"{ticker.lower()}_10k_{year}_xbrl.xml"
            filepath = self.data_dir / filename

            with open(filepath, 'wb') as f:
                f.write(response.content)

            download_time = time.time() - start_time

            # Step 6: Update manifest
            self.manifest['downloads'][ticker] = {
                'last_download': datetime.now().isoformat(),
                'year': year,
                'filepath': str(filepath),
                'source': 'sec_edgar',
                'download_time_seconds': round(download_time, 2),
                'cik': cik,
                'accession': accession
            }
            self._save_manifest()

            if self.verbose:
                print(f"  ✓ Downloaded: {filename} ({download_time:.2f}s)")

            return str(filepath)

        except Exception as e:
            if self.verbose:
                print(f"  ✗ Download failed: {e}")

            if 'failed' not in self.manifest:
                self.manifest['failed'] = {}
            self.manifest['failed'][ticker] = str(e)
            self._save_manifest()
            return None

    def get_or_download(self, ticker: str, year: int = 2025) -> Optional[str]:
        """
        HYBRID: Try local first, download if missing

        This is the main API method you should use.

        Workflow:
        1. Check local cache (instant)
        2. If missing, download from SEC (~2-3s)
        3. Return filepath

        Args:
            ticker: Stock ticker
            year: Fiscal year

        Returns:
            Filepath to XBRL file or None if failed

        Example:
            >>> downloader = SECDownloader()
            >>> filepath = downloader.get_or_download('AAPL', 2025)
            >>> # Returns: 'data/aapl_10k_2025_xbrl.xml'
            >>> # (from cache if exists, otherwise downloads)
        """
        # Try local first
        local_path = self.get_local_file(ticker, year)
        if local_path:
            return local_path

        # Fallback to SEC download
        if self.verbose:
            print(f"  Cache miss: {ticker} {year}")

        return self.download_from_sec(ticker, year)

    def download_sector_batch(
        self,
        sector_code: str,
        year: int = 2025,
        max_companies: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Download all companies in a sector (batch processing)

        Features:
        - Progress tracking
        - Error resilience (continues on failures)
        - Performance metrics
        - Respects SEC rate limits

        Args:
            sector_code: 'TECH', 'MINING', 'OIL_GAS', 'RETAIL'
            year: Fiscal year (default: 2025)
            max_companies: Limit number of downloads (for testing)

        Returns:
            {ticker: filepath} for successful downloads

        Example:
            >>> downloader = SECDownloader()
            >>> files = downloader.download_sector_batch('MINING')
            >>> print(f"Downloaded {len(files)}/41 MINING companies")
        """
        from backend.config import get_sector_companies

        # Get companies for sector
        companies = get_sector_companies(sector_code)

        if max_companies:
            companies = companies[:max_companies]

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"📊 BATCH DOWNLOAD - {sector_code} SECTOR")
            print(f"{'='*60}")
            print(f"Companies: {len(companies)}")
            print(f"Year: {year}")
            print(f"Rate limit: {1/self.REQUEST_DELAY:.1f} req/s")
            print()

        results = {}
        failed = []
        start_time = time.time()

        for i, ticker in enumerate(companies, 1):
            if self.verbose:
                print(f"[{i}/{len(companies)}] {ticker}")

            filepath = self.get_or_download(ticker, year)

            if filepath:
                results[ticker] = filepath
            else:
                failed.append(ticker)

            # Progress indicator
            if self.verbose and i % 5 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(companies) - i) / rate if rate > 0 else 0
                print(f"  Progress: {i}/{len(companies)} ({i/len(companies)*100:.1f}%) | "
                      f"Rate: {rate:.1f} co/s | ETA: {eta/60:.1f}m")

        total_time = time.time() - start_time

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"✅ BATCH DOWNLOAD COMPLETE")
            print(f"{'='*60}")
            print(f"Successful: {len(results)}/{len(companies)} ({len(results)/len(companies)*100:.1f}%)")
            print(f"Failed: {len(failed)}/{len(companies)}")
            if failed:
                print(f"  Failed tickers: {', '.join(failed[:10])}")
                if len(failed) > 10:
                    print(f"  ... and {len(failed)-10} more")
            print(f"Total time: {total_time/60:.1f}m ({total_time:.1f}s)")
            print(f"Avg time per company: {total_time/len(companies):.2f}s")

        return results


# ============================================================================
# STANDALONE FUNCTIONS (for convenience)
# ============================================================================

def download_company(ticker: str, year: int = 2025, **kwargs) -> Optional[str]:
    """
    Convenience function to download a single company

    Args:
        ticker: Stock ticker
        year: Fiscal year
        **kwargs: Additional args for SECDownloader

    Returns:
        Filepath to XBRL file

    Example:
        >>> filepath = download_company('AAPL', 2025)
    """
    downloader = SECDownloader(**kwargs)
    return downloader.get_or_download(ticker, year)


def download_sector(sector_code: str, year: int = 2025, **kwargs) -> Dict[str, str]:
    """
    Convenience function to download entire sector

    Args:
        sector_code: Sector code from sectors.py
        year: Fiscal year
        **kwargs: Additional args for SECDownloader

    Returns:
        {ticker: filepath} dict

    Example:
        >>> files = download_sector('MINING', 2025)
    """
    downloader = SECDownloader(**kwargs)
    return downloader.download_sector_batch(sector_code, year)


# ============================================================================
# DEMO / TESTING
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("SEC DOWNLOADER - DEMO")
    print("="*60)

    # Initialize downloader
    downloader = SECDownloader(
        user_agent='xbrl-analyzer-demo/1.0 (demo@example.com)',
        verbose=True
    )

    # Test 1: Single download (hybrid)
    print("\n--- TEST 1: Single Download (Hybrid Strategy) ---")
    filepath = downloader.get_or_download('AAPL', 2024)

    if filepath:
        print(f"✓ Success: {filepath}")
    else:
        print(f"✗ Failed")

    # Test 2: Batch download (limited to 3 companies for demo)
    print("\n--- TEST 2: Batch Download (3 companies) ---")
    files = downloader.download_sector_batch('TECH', year=2024, max_companies=3)

    print(f"\n✓ Downloaded {len(files)}/3 companies")
    for ticker, path in files.items():
        print(f"  {ticker}: {Path(path).name}")
