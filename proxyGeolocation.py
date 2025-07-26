#!/usr/bin/env python3
"""
Proxy Geolocation and Source Tracking Tool
Identifies proxy origins and tracks which sources provide which proxies.
"""

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ProxyInfo:
    """Information about a proxy including its geolocation and source."""
    ip: str
    port: str
    country: Optional[str] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    org: Optional[str] = None
    isp: Optional[str] = None
    source: Optional[str] = None
    is_cloudflare: bool = False
    is_datacenter: bool = False

class ProxyGeolocator:
    """Main class for proxy geolocation and source tracking."""
    
    def __init__(self):
        self.session: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()
    
    def _check_special_addresses(self, ip: str, proxy_info: ProxyInfo) -> bool:
        """Check for special/reserved addresses. Returns True if special address found."""
        try:
            import ipaddress
            ip_obj = ipaddress.ip_address(ip)
            
            if str(ip_obj) == "0.0.0.0":
                proxy_info.org = "Reserved: 'This host' address"
                proxy_info.country = "Invalid"
                return True
            elif ip_obj.is_private:
                proxy_info.org = "Private network address"
                proxy_info.country = "Local"
                return True
            elif ip_obj.is_loopback:
                proxy_info.org = "Loopback address"
                proxy_info.country = "Local"
                return True
            elif ip_obj.is_reserved:
                proxy_info.org = "Reserved address"
                proxy_info.country = "Invalid"
                return True
                
            return False
        except Exception:
            return False
    
    def _process_geolocation_data(self, data: dict, proxy_info: ProxyInfo) -> None:
        """Process geolocation API response data."""
        if data.get("status") != "success":
            return
            
        proxy_info.country = data.get("country")
        proxy_info.country_code = data.get("countryCode")
        proxy_info.city = data.get("city")
        proxy_info.region = data.get("region")
        proxy_info.org = data.get("org")
        proxy_info.isp = data.get("isp")
        
        # Check if it's Cloudflare
        org_lower = (data.get("org") or "").lower()
        isp_lower = (data.get("isp") or "").lower()
        if "cloudflare" in org_lower or "cloudflare" in isp_lower:
            proxy_info.is_cloudflare = True
        
        # Check if it's a datacenter
        datacenter_keywords = ["datacenter", "hosting", "server", "cloud", "digital ocean", "aws", "amazon", "google", "microsoft"]
        if any(keyword in org_lower or keyword in isp_lower for keyword in datacenter_keywords):
            proxy_info.is_datacenter = True

    async def get_ip_info(self, ip: str) -> ProxyInfo:
        """Get geolocation information for an IP address."""
        proxy_info = ProxyInfo(ip=ip, port="")
        
        # Check for special/reserved addresses first
        if self._check_special_addresses(ip, proxy_info):
            return proxy_info
        
        try:
            # Use ip-api.com for geolocation (free, no API key needed)
            url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,city,org,isp,as"
            
            if not self.session:
                raise RuntimeError("Session not initialized")
                
            response = await self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            self._process_geolocation_data(data, proxy_info)
                    
        except Exception as e:
            logger.debug(f"Error getting IP info for {ip}: {e}")
            
        return proxy_info
    
    def _parse_proxy_line(self, line: str, line_num: int) -> Optional[Tuple[str, int]]:
        """Parse a single proxy line. Returns None if invalid."""
        line = line.strip()
        if not line or line.startswith('#'):
            return None
            
        if ':' not in line:
            return None
            
        try:
            ip, port = line.split(':', 1)
            ip = ip.strip()
            port = int(port.strip())
            return (ip, port)
        except ValueError:
            logger.warning(f"Invalid proxy format on line {line_num}: {line}")
            return None
    
    def _read_proxy_file_lines(self, file_path: str) -> List[str]:
        """Read all lines from proxy file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return list(f)
        except FileNotFoundError:
            logger.error(f"Proxy file not found: {file_path}")
            return []
        except Exception as e:
            logger.error(f"Error reading proxy file: {e}")
            return []

    def parse_proxy_list(self, file_path: str) -> List[Tuple[str, int]]:
        """Parse proxy list file and return list of (ip, port) tuples."""
        proxies = []
        lines = self._read_proxy_file_lines(file_path)
        
        for line_num, line in enumerate(lines, 1):
            proxy = self._parse_proxy_line(line, line_num)
            if proxy is not None:
                proxies.append(proxy)
                
        return proxies
    
    async def analyze_proxies(self, proxy_list: List[Tuple[str, int]], limit: Optional[int] = None) -> List[ProxyInfo]:
        """Analyze a list of proxies and get their geolocation info."""
        if limit:
            proxy_list = proxy_list[:limit]
            
        logger.info(f"🌍 Analyzing {len(proxy_list)} proxies for geolocation...")
        
        results = []
        for i, (ip, port) in enumerate(proxy_list, 1):
            logger.info(f"📍 Analyzing {i}/{len(proxy_list)}: {ip}:{port}")
            
            proxy_info = await self.get_ip_info(ip)
            proxy_info.port = str(port)
            results.append(proxy_info)
            
            # Small delay to be respectful to the API
            await asyncio.sleep(0.1)
            
        return results
    
    def _calculate_summary_stats(self, results: List[ProxyInfo]) -> Tuple[Dict[str, int], int, int, int]:
        """Calculate summary statistics from proxy results."""
        countries = {}
        cloudflare_count = 0
        datacenter_count = 0
        valid_info_count = 0
        
        for proxy in results:
            if proxy.country:
                valid_info_count += 1
                country_key = f"{proxy.country} ({proxy.country_code})" if proxy.country_code else proxy.country
                countries[country_key] = countries.get(country_key, 0) + 1
                
            if proxy.is_cloudflare:
                cloudflare_count += 1
            if proxy.is_datacenter:
                datacenter_count += 1
                
        return countries, cloudflare_count, datacenter_count, valid_info_count

    def _print_summary_stats(self, results: List[ProxyInfo], countries: Dict[str, int], 
                             cloudflare_count: int, datacenter_count: int, valid_info_count: int):
        """Print summary statistics."""
        print("\n📊 Summary:")
        print(f"Total proxies analyzed: {len(results)}")
        print(f"Proxies with geolocation data: {valid_info_count}")
        print(f"Cloudflare proxies: {cloudflare_count}")
        print(f"Datacenter proxies: {datacenter_count}")
        
        if countries:
            print("\n🌎 Countries:")
            for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
                print(f"  {country}: {count}")

    def _format_proxy_details(self, proxy: ProxyInfo) -> str:
        """Format proxy details for display."""
        flag = "🔍"
        if proxy.is_cloudflare:
            flag = "☁️"
        elif proxy.is_datacenter:
            flag = "🏢"
        elif proxy.country:
            flag = "🌍"
        
        location = "Unknown"
        if proxy.city and proxy.country:
            location = f"{proxy.city}, {proxy.country}"
        elif proxy.country:
            location = proxy.country
        
        org_info = ""
        if proxy.org:
            org_info = f" | {proxy.org}"
        if proxy.isp and proxy.isp != proxy.org:
            org_info += f" | ISP: {proxy.isp}"
        
        return f"{flag} {proxy.ip}:{proxy.port} - {location}{org_info}"

    def print_analysis_results(self, results: List[ProxyInfo], show_details: bool = True):
        """Print analysis results in a formatted way."""
        if not results:
            print("❌ No proxy data to analyze")
            return
            
        print("\n🔍 Proxy Geolocation Analysis Results")
        print("=" * 50)
        
        # Calculate summary statistics
        countries, cloudflare_count, datacenter_count, valid_info_count = self._calculate_summary_stats(results)
        
        # Print summary
        self._print_summary_stats(results, countries, cloudflare_count, datacenter_count, valid_info_count)
        
        if show_details:
            print("\n📋 Detailed Results:")
            print("-" * 80)
            
            for proxy in results:
                print(self._format_proxy_details(proxy))
    
    def save_results_json(self, results: List[ProxyInfo], output_file: str):
        """Save results to JSON file."""
        data = []
        for proxy in results:
            data.append({
                "ip": proxy.ip,
                "port": proxy.port,
                "country": proxy.country,
                "country_code": proxy.country_code,
                "city": proxy.city,
                "region": proxy.region,
                "org": proxy.org,
                "isp": proxy.isp,
                "is_cloudflare": proxy.is_cloudflare,
                "is_datacenter": proxy.is_datacenter,
                "source": proxy.source,
            })
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to: {output_file}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    async def analyze_proxy_sources(self, proxy_file: str, limit: Optional[int] = None) -> Dict[str, List[str]]:
        """Analyze which source each proxy likely came from by checking current scraper results."""
        # Dynamic import to avoid circular dependency
        try:
            import proxyScraper
            scrapers = proxyScraper.scrapers
        except ImportError:
            logger.warning("Could not import proxyScraper - source analysis unavailable")
            return {}
        
        # Load proxies from file
        proxies = self.parse_proxy_list(proxy_file)
        if limit:
            proxies = proxies[:limit]
        
        proxy_set = {f"{ip}:{port}" for ip, port in proxies}
        source_map = {}
        
        logger.info(f"🔍 Analyzing sources for {len(proxy_set)} proxies...")
        
        # Check each scraper
        client_config = {
            "follow_redirects": True,
            "timeout": 30.0,
            "limits": httpx.Limits(max_keepalive_connections=20, max_connections=100),
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            },
        }
        
        async with httpx.AsyncClient(**client_config) as client:
            for scraper in scrapers:
                try:
                    logger.info(f"� Checking {scraper.source_name}...")
                    scraped_proxies, _ = await scraper.scrape(client)
                    scraped_set = set(scraped_proxies)
                    
                    # Find matches
                    matches = proxy_set.intersection(scraped_set)
                    if matches:
                        source_map[scraper.source_name] = list(matches)
                        logger.info(f"  Found {len(matches)} matches")
                    
                    await asyncio.sleep(0.5)  # Be respectful to sources
                    
                except Exception as e:
                    logger.debug(f"Error checking {scraper.source_name}: {e}")
        
        return source_map
    
    async def check_single_ip(self, ip: str) -> ProxyInfo:
        """Check a single IP address."""
        logger.info(f"🔍 Checking IP: {ip}")
        return await self.get_ip_info(ip)

def _setup_argument_parser():
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Proxy Geolocation and Source Tracking Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python proxyGeolocation.py -i 104.16.1.31
  python proxyGeolocation.py -f output.txt -l 20
  python proxyGeolocation.py -f output.txt -s --limit 50
  python proxyGeolocation.py -f output.txt -o results.json
  python proxyGeolocation.py -f output.txt --no-details
        """,
    )
    
    parser.add_argument("-i", "--ip", type=str, help="Check single IP address")
    parser.add_argument("-f", "--file", type=str, help="Path to proxy list file (default: output.txt)")
    parser.add_argument("-s", "--sources", action="store_true", help="Analyze which sources provide which proxies")
    parser.add_argument("-l", "--limit", type=int, help="Limit number of proxies to analyze")
    parser.add_argument("-o", "--output", type=str, help="Save results to JSON file")
    parser.add_argument("--no-details", action="store_true", help="Show only summary, no detailed results")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    
    return parser

async def _handle_single_ip(geolocator, args):
    """Handle single IP analysis."""
    result = await geolocator.check_single_ip(args.ip)
    geolocator.print_analysis_results([result], show_details=True)
    
    if args.output:
        geolocator.save_results_json([result], args.output)

def _validate_proxy_file(proxy_file: str) -> bool:
    """Validate that proxy file exists."""
    if not Path(proxy_file).exists():
        print(f"❌ Proxy file not found: {proxy_file}")
        print("💡 Run proxy scraper first: python proxyScraper.py -p http")
        return False
    return True

def _print_source_summary(source_map: dict, total_mapped: int) -> None:
    """Print source analysis summary."""
    print("\n🔍 Proxy Source Analysis Results")
    print("=" * 50)
    print(f"Total proxies mapped to sources: {total_mapped}")

def _print_source_details(source_map: dict, show_details: bool) -> None:
    """Print detailed source information."""
    if not source_map:
        return
        
    print("\n📊 Sources:")
    for source, proxy_list in sorted(source_map.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {source}: {len(proxy_list)} proxies")
        if not show_details:
            continue
            
        # Show first few proxies as examples
        for proxy in proxy_list[:5]:
            print(f"    - {proxy}")
        if len(proxy_list) > 5:
            print(f"    ... and {len(proxy_list) - 5} more")
        print()

async def _handle_source_analysis(geolocator, args):
    """Handle proxy source analysis."""
    proxy_file = args.file or "output.txt"
    
    if not _validate_proxy_file(proxy_file):
        return
    
    source_map = await geolocator.analyze_proxy_sources(proxy_file, args.limit)
    total_mapped = sum(len(proxies) for proxies in source_map.values())
    
    _print_source_summary(source_map, total_mapped)
    _print_source_details(source_map, not args.no_details)
    
    if args.output:
        output_data = {
            "analysis_type": "source_mapping",
            "total_mapped": total_mapped,
            "sources": source_map,
        }
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2)
            print(f"💾 Source analysis saved to: {args.output}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

async def _handle_file_analysis(geolocator, args):
    """Handle proxy file analysis."""
    proxy_file = args.file or "output.txt"
    
    if not Path(proxy_file).exists():
        print(f"❌ Proxy file not found: {proxy_file}")
        print("💡 Run proxy scraper first: python proxyScraper.py -p http")
        return
    
    proxies = geolocator.parse_proxy_list(proxy_file)
    
    if not proxies:
        print(f"❌ No valid proxies found in {proxy_file}")
        return
    
    results = await geolocator.analyze_proxies(proxies, args.limit)
    geolocator.print_analysis_results(results, show_details=not args.no_details)
    
    if args.output:
        geolocator.save_results_json(results, args.output)

def _configure_environment(args) -> None:
    """Configure logging and environment settings."""
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle Windows event loop
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

async def _run_analysis_based_on_args(geolocator, args):
    """Run analysis based on command line arguments."""
    if args.ip:
        await _handle_single_ip(geolocator, args)
    elif args.sources:
        await _handle_source_analysis(geolocator, args)
    else:
        await _handle_file_analysis(geolocator, args)

def main():
    """Main function for CLI usage."""
    parser = _setup_argument_parser()
    args = parser.parse_args()
    
    _configure_environment(args)
    
    async def run_analysis():
        async with ProxyGeolocator() as geolocator:
            await _run_analysis_based_on_args(geolocator, args)
    
    # Run the analysis
    try:
        asyncio.run(run_analysis())
    except KeyboardInterrupt:
        print("\n⏹️  Analysis interrupted by user")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")

if __name__ == "__main__":
    main()
