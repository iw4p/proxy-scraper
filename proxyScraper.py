import argparse
import asyncio
import ipaddress
import logging
import platform
import re
import sys
import time
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Module-level helpers for source statistics ---
def _extract_domain(url):
    """Extract domain from URL for statistics."""
    try:
        domain = urlparse(url).netloc or urlparse('//' + url).netloc
        if not domain:
            domain = url
    except Exception:
        domain = url
    return domain

def _aggregate_domain_stats(source_stats):
    """Aggregate statistics by domain."""
    total_bad_filtered = 0
    total_invalid_filtered = 0
    domain_valid = {}
    skipped = 0
    for source, stats in source_stats.items():
        url = source.split(": ", 1)[-1]
        domain = _extract_domain(url)
        if stats['valid'] > 0:
            domain_valid[domain] = domain_valid.get(domain, 0) + stats['valid']
        else:
            skipped += 1
        total_bad_filtered += stats['filtered_bad']
        total_invalid_filtered += stats['filtered_invalid']
    return domain_valid, skipped, total_bad_filtered, total_invalid_filtered

def _print_summary(domain_valid, skipped, total_bad_filtered, total_invalid_filtered):
    """Print formatted statistics summary."""
    print("\n*** Source Statistics ***")
    print("-" * 50)
    for domain, valid_count in sorted(domain_valid.items(), key=lambda x: -x[1]):
        print(f"{valid_count} valid from {domain}")
    if skipped:
        print(f"...{skipped} sources returned 0 valid proxies and are hidden...")
    print(f"\nTotal filtered: {total_bad_filtered} bad IPs (CDN/etc), {total_invalid_filtered} invalid format")

# Known bad IP ranges to filter out (Cloudflare, major CDNs, etc.)
BAD_IP_RANGES = [
    # Cloudflare
    "173.245.48.0/20",
    "103.21.244.0/22", 
    "103.22.200.0/22",
    "103.31.4.0/22",
    "141.101.64.0/18",
    "108.162.192.0/18",
    "190.93.240.0/20",
    "188.114.96.0/20",
    "197.234.240.0/22",
    "198.41.128.0/17",
    "162.158.0.0/15",
    "104.16.0.0/13",  # This includes our problematic IP 104.16.1.31
    "104.24.0.0/14",
    "172.64.0.0/13",
    "131.0.72.0/22",
    # Amazon CloudFront
    "13.32.0.0/15",
    "13.35.0.0/17",
    "18.160.0.0/15",
    "52.222.128.0/17",
    "54.182.0.0/16",
    "54.192.0.0/16",
    "54.230.0.0/16",
    "54.239.128.0/18",
    "99.86.0.0/16",
    "205.251.200.0/21",
    "216.137.32.0/19",
]

def is_bad_ip(ip: str) -> bool:
    """Check if an IP is in a known bad range (CDN, etc.) or is a reserved address."""
    try:
        ip_obj = ipaddress.ip_address(ip)
        
        # Check for reserved/special addresses
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_multicast:
            return True
            
        # Check for specific bad addresses
        if str(ip_obj) in ["0.0.0.0", "255.255.255.255", "127.0.0.1"]:
            return True
        
        # Check against known bad ranges (CDNs)
        for cidr in BAD_IP_RANGES:
            if ip_obj in ipaddress.ip_network(cidr):
                return True
                
    except (ValueError, ipaddress.AddressValueError):
        return True  # Invalid IP format
    return False


class Scraper:
    """Base scraper class for proxy sources."""

    def __init__(self, method: str, _url: str, timeout: int = 10):
        self.method = method
        self._url = _url
        self.timeout = timeout
        self.source_name = self.__class__.__name__

    def get_url(self, **kwargs) -> str:
        """Get the formatted URL for the scraper."""
        return self._url.format(**kwargs, method=self.method)

    async def get_response(self, client: httpx.AsyncClient) -> httpx.Response:
        """Get HTTP response from the proxy source."""
        return await client.get(self.get_url(), timeout=self.timeout)

    async def handle(self, response: httpx.Response) -> str:
        """Handle the response and extract proxy data."""
        return response.text

    def filter_proxies(self, proxy_text: str) -> Tuple[Set[str], Dict[str, int]]:
        """Filter proxies and return valid ones with statistics."""
        proxies = set()
        stats = {"total": 0, "filtered_bad": 0, "filtered_invalid": 0, "valid": 0}
        
        for line in proxy_text.split('\n'):
            line = line.strip()
            if not line:
                continue

            stats["total"] += 1

            # Basic format validation
            if ':' not in line:
                stats["filtered_invalid"] += 1
                continue

            try:
                ip, port = line.split(':', 1)
                ip = ip.strip()
                port = port.strip()

                # Validate IP format
                ipaddress.ip_address(ip)

                # Validate port
                port_num = int(port)
                if not (1 <= port_num <= 65535):
                    stats["filtered_invalid"] += 1
                    continue

                # Check if it's a bad IP (CDN, etc.)
                if is_bad_ip(ip):
                    stats["filtered_bad"] += 1
                    logger.debug(f"Filtered bad IP from {self.source_name}: {ip}:{port}")
                    continue

                proxies.add(f"{ip}:{port}")
                stats["valid"] += 1

            except (ValueError, ipaddress.AddressValueError):
                stats["filtered_invalid"] += 1
                continue

        return proxies, stats

    async def scrape(self, client: httpx.AsyncClient) -> Tuple[List[str], Dict[str, int]]:
        """Scrape proxies from the source."""
        try:
            response = await self.get_response(client)
            response.raise_for_status()  # Raise an exception for bad status codes
            proxy_text = await self.handle(response)
            
            # Use regex to find all potential proxies
            pattern = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}(?::\d{1,5})?")
            raw_proxies = re.findall(pattern, proxy_text)
            
            # Filter and validate proxies
            valid_proxies, stats = self.filter_proxies('\n'.join(raw_proxies))
            
            return list(valid_proxies), stats
        except Exception as e:
            logger.debug(f"Failed to scrape from {self.source_name} ({self.get_url()}): {e}")
            return [], {"total": 0, "filtered_bad": 0, "filtered_invalid": 0, "valid": 0}


# From spys.me
class SpysMeScraper(Scraper):
    """Scraper for spys.me proxy source."""

    def __init__(self, method: str):
        super().__init__(method, "https://spys.me/{mode}.txt", timeout=15)

    def get_url(self, **kwargs) -> str:
        """Get URL with appropriate mode for the proxy method."""
        mode = "proxy" if self.method == "http" else "socks" if self.method == "socks" else "unknown"
        if mode == "unknown":
            raise NotImplementedError(f"Method {self.method} not supported by SpysMeScraper")
        return super().get_url(mode=mode, **kwargs)

    async def handle(self, response: httpx.Response) -> str:
        """Parse spys.me format to extract only IP:port."""
        try:
            lines = response.text.strip().split('\n')
            proxies: Set[str] = set()
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Skip header lines and comments
                if (line.startswith('Proxy list') or
                        line.startswith('Socks proxy=') or
                        line.startswith('Support by') or
                        line.startswith('BTC ') or
                        line.startswith('IP address:Port') or
                        line.startswith('#')):
                    continue
                
                # Extract IP:port from lines like "89.58.55.193:80 DE-A + "
                # The format is: IP:PORT COUNTRY-ANONYMITY-SSL GOOGLE_PASSED
                parts = line.split()
                if parts and ':' in parts[0]:
                    proxy = parts[0].strip()
                    # Validate IP:port format
                    if re.match(r"\d{1,3}(?:\.\d{1,3}){3}:\d{1,5}", proxy):
                        proxies.add(proxy)
            
            return "\n".join(proxies)
        except Exception as e:
            logger.debug(f"Error parsing spys.me format: {e}")
            return ""


# From proxyscrape.com
class ProxyScrapeScraper(Scraper):
    """Scraper for proxyscrape.com v4 API."""

    def __init__(self, method: str, country: str = "all"):
        self.country = country
        super().__init__(method,
                         "https://api.proxyscrape.com/v4/free-proxy-list/get?"
                         "request=display_proxies&proxy_format=ipport&format=text"
                         "&protocol={method}&country={country}", 
                         timeout=20)

    def get_url(self, **kwargs) -> str:
        """Get URL with API parameters."""
        return super().get_url(country=self.country, **kwargs)

# From proxy-list.download
class ProxyListDownloadScraper(Scraper):
    """Scraper for proxy-list.download API."""

    def __init__(self, method: str, anon: str):
        self.anon = anon
        super().__init__(method, "https://www.proxy-list.download/api/v1/get?type={method}&anon={anon}", timeout=15)

    def get_url(self, **kwargs) -> str:
        """Get URL with anonymity level parameter."""
        return super().get_url(anon=self.anon, **kwargs)


# For websites using table in html
class GeneralTableScraper(Scraper):
    """Scraper for websites that use HTML tables to display proxies."""

    async def handle(self, response: httpx.Response) -> str:
        """Parse HTML table to extract proxies."""
        try:
            soup = BeautifulSoup(response.text, "html.parser")
            proxies: Set[str] = set()
            table = soup.find("table", attrs={"class": "table table-striped table-bordered"})
            
            if table is None:
                logger.debug("No table found with expected class")
                return ""
                
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    ip = cells[0].get_text(strip=True).replace("&nbsp;", "")
                    port = cells[1].get_text(strip=True).replace("&nbsp;", "")
                    if ip and port:
                        proxies.add(f"{ip}:{port}")
            
            return "\n".join(proxies)
        except Exception as e:
            logger.debug(f"Error parsing HTML table: {e}")
            return ""


# For websites using div in html
class GeneralDivScraper(Scraper):
    """Scraper for websites that use HTML divs to display proxies."""

    async def handle(self, response: httpx.Response) -> str:
        """Parse HTML divs to extract proxies."""
        try:
            soup = BeautifulSoup(response.text, "html.parser")
            proxies: Set[str] = set()
            container = soup.find("div", attrs={"class": "list"})
            
            if container is None:
                logger.debug("No div found with class 'list'")
                return ""
                
            for row in container.find_all("div"):
                cells = row.find_all("div", attrs={"class": "td"})
                if len(cells) >= 2:
                    ip = cells[0].get_text(strip=True)
                    port = cells[1].get_text(strip=True)
                    if ip and port:
                        proxies.add(f"{ip}:{port}")
            
            return "\n".join(proxies)
        except Exception as e:
            logger.debug(f"Error parsing HTML divs: {e}")
            return ""
    
# For scraping live proxylist from github
class GitHubScraper(Scraper):
    """Scraper for GitHub raw proxy lists."""
        
    async def handle(self, response: httpx.Response) -> str:
        """Parse GitHub raw proxy list format."""
        try:
            temp_proxies = response.text.strip().split("\n")
            proxies: Set[str] = set()
            
            for proxy_line in temp_proxies:
                proxy_line = proxy_line.strip()
                if not proxy_line:
                    continue
                    
                # Handle different formats: "type://ip:port" or just "ip:port"
                if self.method in proxy_line:
                    # Extract IP:port from lines like "http://1.2.3.4:8080"
                    if "//" in proxy_line:
                        proxy = proxy_line.split("//")[-1]
                    else:
                        proxy = proxy_line
                    
                    # Validate IP:port format
                    if re.match(r"\d{1,3}(?:\.\d{1,3}){3}:\d{1,5}", proxy):
                        proxies.add(proxy)

            return "\n".join(proxies)
        except Exception as e:
            logger.debug(f"Error parsing GitHub proxy list: {e}")
            return ""

# For scraping from proxy list APIs with JSON response
class ProxyListApiScraper(Scraper):
    """Scraper for APIs that return JSON proxy lists."""
    
    def _extract_proxy_from_item(self, item: dict) -> Optional[str]:
        """Extract proxy string from a single item for new www.proxy-list.download format."""
        if not isinstance(item, dict):
            return None
        # Support both old and new keys
        ip = item.get('ip') or item.get('IP')
        port = item.get('port') or item.get('PORT')
        if ip and port:
            return f"{ip}:{port}"
        return None

    def _process_dict_data(self, data: dict) -> Set[str]:
        """Process dict-type JSON data for new www.proxy-list.download format."""
        proxies = set()
        # New format: proxies are in 'LISTA' key
        if 'LISTA' in data and isinstance(data['LISTA'], list):
            for item in data['LISTA']:
                proxy = self._extract_proxy_from_item(item)
                if proxy:
                    proxies.add(proxy)
        # Fallback for old format
        elif 'data' in data and isinstance(data['data'], list):
            for item in data['data']:
                proxy = self._extract_proxy_from_item(item)
                if proxy:
                    proxies.add(proxy)
        return proxies

    async def handle(self, response: httpx.Response) -> str:
        """Parse JSON API response for proxies (new and old format)."""
        try:
            data = response.json()
            proxies: Set[str] = set()
            if isinstance(data, dict):
                proxies = self._process_dict_data(data)
            return "\n".join(proxies)
        except Exception as e:
            logger.debug(f"Error parsing JSON API response: {e}")
            return ""

# Helper functions for PlainTextScraper
def _is_protocol_match(protocol: str, method: str) -> bool:
    """Check if protocol matches the scraper method."""
    return (protocol.lower() == method.lower() or 
            (method == "socks" and protocol.lower() in ["socks4", "socks5"]))

def _is_valid_proxy_format(address: str) -> bool:
    """Validate IP:port format."""
    return bool(re.match(r"\d{1,3}(?:\.\d{1,3}){3}:\d{1,5}", address))

def _process_protocol_line(line: str, method: str) -> Optional[str]:
    """Process a line with protocol://ip:port format."""
    protocol, address = line.split("://", 1)
    if _is_protocol_match(protocol, method):
        if _is_valid_proxy_format(address):
            return address
    return None

def _process_plain_line(line: str) -> Optional[str]:
    """Process a plain IP:port line."""
    if _is_valid_proxy_format(line):
        return line
    return None

# For scraping from plain text sources
class PlainTextScraper(Scraper):
    """Scraper for plain text proxy lists."""
    
    async def handle(self, response: httpx.Response) -> str:
        """Parse plain text proxy list."""
        try:
            proxies: Set[str] = set()
            lines = response.text.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Handle protocol://ip:port format (ProxyScrape v4 API)
                if "://" in line:
                    proxy = _process_protocol_line(line, self.method)
                    if proxy:
                        proxies.add(proxy)
                else:
                    # Look for plain IP:port pattern (legacy format)
                    proxy = _process_plain_line(line)
                    if proxy:
                        proxies.add(proxy)
                        
            return "\n".join(proxies)
        except Exception as e:
            logger.debug(f"Error parsing plain text proxy list: {e}")
            return ""


# Latest and most frequently updated proxy sources (2025)
scrapers = [
    # Primary API scrapers (most reliable)
    SpysMeScraper("http"),
    SpysMeScraper("socks"),
    ProxyScrapeScraper("http"),
    ProxyScrapeScraper("socks4"),
    ProxyScrapeScraper("socks5"),
    
    # TheSpeedX/PROXY-List (updated daily)
    GitHubScraper("http", "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"),
    GitHubScraper("socks4", "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt"),
    GitHubScraper("socks5", "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt"),

    # jetkai/proxy-list (hourly updates, geolocation)
    GitHubScraper("http", "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt"),
    GitHubScraper("https", "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt"),
    GitHubScraper("socks4", "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt"),
    GitHubScraper("socks5", "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt"),

    # prxchk/proxy-list (10 min updates, deduplicated)
    GitHubScraper("http", "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt"),
    GitHubScraper("socks4", "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks4.txt"),
    GitHubScraper("socks5", "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks5.txt"),

    # roosterkid/openproxylist (hourly updates)
    GitHubScraper("http", "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt"),
    GitHubScraper("socks4", "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt"),
    GitHubScraper("socks5", "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt"),

    # mmpx12/proxy-list (hourly updates)
    GitHubScraper("http", "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt"),
    GitHubScraper("https", "https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt"),
    GitHubScraper("socks4", "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt"),
    GitHubScraper("socks5", "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt"),



    # ProxyScrape API v4 (live, no key needed)
    PlainTextScraper("http", "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&protocol=http&proxy_format=protocolipport&format=text&timeout=20000"),
    PlainTextScraper("socks4", "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&protocol=socks4&proxy_format=protocolipport&format=text&timeout=20000"),
    PlainTextScraper("socks5", "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&protocol=socks5&proxy_format=protocolipport&format=text&timeout=20000"),

    # OpenProxyList API (10 min updates)
    PlainTextScraper("http", "https://api.openproxylist.xyz/http.txt"),
    PlainTextScraper("https", "https://api.openproxylist.xyz/https.txt"),
    PlainTextScraper("socks4", "https://api.openproxylist.xyz/socks4.txt"),
    PlainTextScraper("socks5", "https://api.openproxylist.xyz/socks5.txt"),
    PlainTextScraper("http", "https://www.proxyscan.io/download?type=http"),
    PlainTextScraper("socks4", "https://www.proxyscan.io/download?type=socks4"),
    PlainTextScraper("socks5", "https://raw.githubusercontent.com/Surfboardv2ray/Proxy-sorter/main/socks5.txt"),
    
    # JSON APIs
    ProxyListApiScraper("http", "https://www.proxy-list.download/api/v2/get?l=en&t=http"),
    ProxyListApiScraper("https", "https://www.proxy-list.download/api/v2/get?l=en&t=https"),
    ProxyListApiScraper("socks4", "https://www.proxy-list.download/api/v2/get?l=en&t=socks4"),
    ProxyListApiScraper("socks5", "https://www.proxy-list.download/api/v2/get?l=en&t=socks5"),
    
    # Fresh community sources (updated daily)
    GitHubScraper("http", "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt"),
    GitHubScraper("socks4", "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks4.txt"),
    GitHubScraper("socks5", "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks5.txt"),
    
    # Ultra-fresh sources (updated every few hours)
    PlainTextScraper("http", "https://api.openproxylist.xyz/http.txt"),
    PlainTextScraper("socks4", "https://api.openproxylist.xyz/socks4.txt"),
    PlainTextScraper("socks5", "https://api.openproxylist.xyz/socks5.txt"),
    
    # Elite proxy APIs

    
    # New 2025 sources
    GitHubScraper("http", "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt"),
    GitHubScraper("https", "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/https.txt"),
    GitHubScraper("socks4", "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks4.txt"),
    GitHubScraper("socks5", "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks5.txt"),
    
    # Quality HTML scrapers (still active)
    GeneralTableScraper("https", "http://sslproxies.org"),
    GeneralTableScraper("http", "http://free-proxy-list.net"),
    GeneralTableScraper("http", "http://us-proxy.org"),
    GeneralTableScraper("socks", "http://socks-proxy.net"),
    

    GeneralTableScraper("http", "https://premproxy.com/proxy-by-country/"),
    GeneralTableScraper("https", "https://premproxy.com/socks-list/"),
    GeneralTableScraper("http", "https://proxyservers.pro/proxy/list/protocol/http"),
    GeneralTableScraper("https", "https://proxyservers.pro/proxy/list/protocol/https"),
    
    # Updated HTML div scrapers
    GeneralDivScraper("http", "https://freeproxy.lunaproxy.com/"),
    GeneralDivScraper("http", "https://www.freeproxylists.net/"),
    GeneralDivScraper("socks4", "https://www.freeproxylists.net/socks4.html"),
    GeneralDivScraper("socks5", "https://www.freeproxylists.net/socks5.html"),
    
    # Modern proxy sites with table format
    GeneralTableScraper("http", "https://hidemy.name/en/proxy-list/?type=h"),
    GeneralTableScraper("https", "https://hidemy.name/en/proxy-list/?type=s"),
    GeneralTableScraper("socks4", "https://hidemy.name/en/proxy-list/?type=4"),
    GeneralTableScraper("socks5", "https://hidemy.name/en/proxy-list/?type=5"),

    # Additional HTML sources
    GeneralTableScraper("http", "https://www.proxynova.com/proxy-server-list/"),
    GeneralTableScraper("http", "https://www.proxydocker.com/en/proxylist/"),
    GeneralTableScraper("https", "https://www.proxydocker.com/en/proxylist/type/https"),
]


def verbose_print(verbose: bool, message: str) -> None:
    """Print message if verbose mode is enabled."""
    if verbose:
        print(message)


def _determine_scraping_methods(method: str) -> List[str]:
    """Determine which methods to scrape based on input."""
    methods = [method]
    if method == "socks":
        methods.extend(["socks4", "socks5"])
    return methods

def _get_scrapers_for_methods(methods: List[str]) -> List:
    """Get scrapers that match the specified methods."""
    proxy_scrapers = [s for s in scrapers if s.method in methods]
    if not proxy_scrapers:
        raise ValueError(f"Methods '{methods}' not supported")
    return proxy_scrapers

def _create_http_client_config() -> Dict:
    """Create HTTP client configuration."""
    return {
        "follow_redirects": True,
        "timeout": 30.0,
        "limits": httpx.Limits(max_keepalive_connections=20, max_connections=100),
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        },
    }

def _print_source_statistics(verbose: bool, source_stats: Dict) -> None:
    """Print source statistics if verbose mode is enabled."""
    if not verbose:
        return
    domain_valid, skipped, total_bad_filtered, total_invalid_filtered = _aggregate_domain_stats(source_stats)
    _print_summary(domain_valid, skipped, total_bad_filtered, total_invalid_filtered)

async def scrape(method: str, output: str, verbose: bool) -> None:
    """
    Main scraping function that coordinates all scrapers.
    
    Args:
        method: Proxy type to scrape (http, https, socks, socks4, socks5)
        output: Output file path
        verbose: Enable verbose logging
    """
    start_time = time.time()
    
    # Setup scraping parameters
    methods = _determine_scraping_methods(method)
    proxy_scrapers = _get_scrapers_for_methods(methods)
    client_config = _create_http_client_config()
    
    verbose_print(verbose, f"Scraping proxies using {len(proxy_scrapers)} sources...")
    all_proxies: List[str] = []
    source_stats: Dict[str, Dict[str, int]] = {}

    async def scrape_source(scraper, client) -> None:
        """Scrape from a single source."""
        try:
            source_id = f"{scraper.source_name}: {scraper.get_url()}"
            verbose_print(verbose, f"Scraping from {scraper.get_url()}...")
            proxies, stats = await scraper.scrape(client)
            all_proxies.extend(proxies)
            source_stats[source_id] = stats
            verbose_print(verbose, f"Found {len(proxies)} valid proxies from {source_id} ({stats['filtered_bad']} bad IPs filtered, {stats['filtered_invalid']} invalid filtered)")
        except Exception as e:
            source_id = f"{scraper.source_name}: {scraper.get_url()}"
            logger.debug(f"Failed to scrape from {source_id}: {e}")
            source_stats[source_id] = {"total": 0, "filtered_bad": 0, "filtered_invalid": 0, "valid": 0}

    # Execute all scrapers concurrently
    async with httpx.AsyncClient(**client_config) as client:
        tasks = [scrape_source(scraper, client) for scraper in proxy_scrapers]
        await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    unique_proxies: Set[str] = set(all_proxies)
    _print_source_statistics(verbose, source_stats)

    # Write results to file
    verbose_print(verbose, f"Writing {len(unique_proxies)} unique proxies to {output}...")
    try:
        with open(output, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(unique_proxies)) + "\n")
    except IOError as e:
        logger.error(f"Failed to write to output file {output}: {e}")
        raise

    elapsed_time = time.time() - start_time
    verbose_print(verbose, f"Scraping completed in {elapsed_time:.2f} seconds")
    verbose_print(verbose, f"Found {len(unique_proxies)} unique valid proxies")

def _setup_argument_parser():
    """Set up and return the argument parser."""
    parser = argparse.ArgumentParser(
        description="Scrape proxies from multiple sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -p http -v                    # Scrape HTTP proxies with verbose output
  %(prog)s -p socks -o socks.txt         # Scrape SOCKS proxies to custom file
  %(prog)s -p https --verbose           # Scrape HTTPS proxies with verbose output
  %(prog)s -p socks4 --debug             # Scrape SOCKS4 proxies with debug logging
  %(prog)s -p socks5 -o output.txt -v     # Scrape SOCKS5 proxies to output.txt with verbose logging
  %(prog)s -p http -o proxies.txt --debug  # Scrape HTTP proxies to proxies.txt with debug logging
        """,
    )
    
    supported_methods = sorted(set(s.method for s in scrapers))
    
    parser.add_argument(
        "-p", "--proxy",
        required=True,
        choices=supported_methods,
        help=f"Proxy type to scrape. Supported types: {', '.join(supported_methods)}",
    )
    parser.add_argument(
        "-o", "--output",
        default="output.txt",
        help="Output file name to save proxies (default: %(default)s)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    
    return parser

def _configure_logging(args):
    """Configure logging based on command line arguments."""
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

def _run_scraping(args):
    """Run the scraping process with appropriate event loop handling."""
    if sys.version_info >= (3, 7):
        if platform.system() == 'Windows':
            # Windows-specific asyncio policy for better compatibility
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        asyncio.run(scrape(args.proxy, args.output, args.verbose))
    else:
        # Fallback for Python < 3.7
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(scrape(args.proxy, args.output, args.verbose))
        finally:
            loop.close()

def main() -> None:
    """Main entry point for the proxy scraper."""
    parser = _setup_argument_parser()
    args = parser.parse_args()
    
    _configure_logging(args)

    try:
        _run_scraping(args)
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
