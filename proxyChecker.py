import argparse
import concurrent.futures
import logging
import random
import re
import socket
import sys
import threading
import urllib.request
from pathlib import Path
from time import time
from typing import List, Optional, Tuple

import socks

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fallback user agents (will be extended from user_agents.txt if available)
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
]

# Load additional user agents from file if available
def load_user_agents() -> None:
    """Load user agents from external file if available."""
    try:
        user_agents_file = Path("user_agents.txt")
        if user_agents_file.exists():
            with open(user_agents_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and line not in user_agents:
                        user_agents.append(line)
            logger.debug(f"Loaded {len(user_agents)} user agents from file")
        else:
            logger.debug("user_agents.txt not found, using built-in user agents")
    except Exception as e:
        logger.warning(f"Failed to load user agents from file: {e}")

# Load user agents at module level
load_user_agents()


class Proxy:
    """Represents a proxy server with validation and checking capabilities."""
    
    SUPPORTED_METHODS = ["http", "https", "socks4", "socks5"]
    
    def __init__(self, method: str, proxy: str):
        """
        Initialize a proxy instance.
        
        Args:
            method: Proxy type (http, https, socks4, socks5)
            proxy: Proxy address in format 'ip:port'
        
        Raises:
            NotImplementedError: If proxy method is not supported
            ValueError: If proxy format is invalid
        """
        method = method.lower().strip()
        if method not in self.SUPPORTED_METHODS:
            raise NotImplementedError(f"Only {', '.join(self.SUPPORTED_METHODS)} are supported, got: {method}")
        
        self.method = method
        self.proxy = proxy.strip()
        
        # Validate proxy format during initialization
        if not self.is_valid():
            raise ValueError(f"Invalid proxy format: {proxy}")

    def is_valid(self) -> bool:
        """
        Validate proxy format (IP:port).
        
        Returns:
            True if proxy format is valid, False otherwise
        """
        if not self.proxy or ':' not in self.proxy:
            return False
            
        try:
            ip, port = self.proxy.split(':', 1)
            
            # Validate IP format
            if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                return False
            
            # Validate IP range (0-255 for each octet)
            ip_parts = [int(x) for x in ip.split('.')]
            if not all(0 <= part <= 255 for part in ip_parts):
                return False
            
            # Validate port range
            port_num = int(port)
            if not (1 <= port_num <= 65535):
                return False
                
            return True
        except (ValueError, AttributeError):
            return False

    def check(self, site: str, timeout: int, user_agent: str, verbose: bool) -> Tuple[bool, float, Optional[Exception]]:
        """
        Check if proxy is working by attempting to connect through it.
        
        Args:
            site: Target website to test connection
            timeout: Connection timeout in seconds
            user_agent: User agent string to use
            verbose: Enable verbose logging
            
        Returns:
            Tuple of (is_valid, response_time, error)
        """
        if not site.startswith(('http://', 'https://')):
            site = f"https://{site}"
            
        start_time = time()
        
        try:
            if self.method in ["socks4", "socks5"]:
                return self._check_socks_proxy(site, timeout, verbose, start_time)
            else:
                return self._check_http_proxy(site, timeout, user_agent, verbose, start_time)
        except Exception as e:
            verbose_print(verbose, f"Proxy {self.proxy} failed with unexpected error: {e}")
            return False, 0.0, e

    def _check_socks_proxy(self, site: str, timeout: int, verbose: bool, start_time: float) -> Tuple[bool, float, Optional[Exception]]:
        """Check SOCKS proxy connectivity."""
        # Store original socket to restore later
        original_socket = socket.socket
        
        try:
            ip, port = self.proxy.split(':')
            socks_type = socks.SOCKS4 if self.method == "socks4" else socks.SOCKS5
            
            socks.set_default_proxy(socks_type, ip, int(port))
            socket.socket = socks.socksocket
            
            try:
                response = urllib.request.urlopen(site, timeout=timeout)
                response.read(1024)  # Read a small amount to ensure connection works
                end_time = time()
                time_taken = end_time - start_time
                
                verbose_print(verbose, f"[+] Proxy {self.proxy} ({self.method.upper()}) is valid, time: {time_taken:.2f}s")
                return True, time_taken, None
                
            finally:
                # Always restore original socket
                socket.socket = original_socket
                
        except Exception as e:
            socket.socket = original_socket  # Ensure cleanup even on error
            verbose_print(verbose, f"[-] Proxy {self.proxy} ({self.method.upper()}) failed: {e}")
            return False, 0.0, e

    def _check_http_proxy(self, site: str, timeout: int, user_agent: str, verbose: bool, start_time: float) -> Tuple[bool, float, Optional[Exception]]:
        """Check HTTP/HTTPS proxy connectivity."""
        try:
            proxy_url = f"{self.method}://{self.proxy}"
            proxy_handler = urllib.request.ProxyHandler({
                'http': proxy_url,
                'https': proxy_url,
            })
            
            opener = urllib.request.build_opener(proxy_handler)
            
            # Create request with proper headers
            request = urllib.request.Request(site)
            request.add_header("User-Agent", user_agent)
            request.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
            request.add_header("Accept-Language", "en-US,en;q=0.5")
            request.add_header("Accept-Encoding", "gzip, deflate")
            request.add_header("Connection", "keep-alive")
            
            response = opener.open(request, timeout=timeout)
            response.read(1024)  # Read a small amount to ensure connection works
            
            end_time = time()
            time_taken = end_time - start_time
            
            verbose_print(verbose, f"[+] Proxy {self.proxy} ({self.method.upper()}) is valid, time: {time_taken:.2f}s")
            return True, time_taken, None
            
        except Exception as e:
            verbose_print(verbose, f"[-] Proxy {self.proxy} ({self.method.upper()}) failed: {e}")
            return False, 0.0, e

    def __str__(self) -> str:
        """String representation of the proxy."""
        return self.proxy

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Proxy(method='{self.method}', proxy='{self.proxy}')"


def verbose_print(verbose: bool, message: str) -> None:
    """Print message if verbose mode is enabled."""
    if verbose:
        print(message)


def _process_proxy_line(line: str, line_num: int, method: str) -> Optional[Proxy]:
    """Process a single line from proxy file."""
    line = line.strip()
    if not line or line.startswith('#'):  # Skip empty lines and comments
        return None
        
    try:
        return Proxy(method, line)
    except (ValueError, NotImplementedError) as e:
        logger.debug(f"Line {line_num}: Invalid proxy '{line}' - {e}")
        return None


def _read_proxy_file(file_path: str) -> List[str]:
    """Read and return lines from proxy file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return list(f)
    except FileNotFoundError:
        logger.error(f"Proxy file not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading proxy file {file_path}: {e}")
        sys.exit(1)


def load_proxies_from_file(file_path: str, method: str, limit: Optional[int] = None) -> List[Proxy]:
    """
    Load proxies from file and create Proxy objects.
    
    Args:
        file_path: Path to proxy list file
        method: Proxy method to use
        limit: Maximum number of proxies to load (None for all)
        
    Returns:
        List of valid Proxy objects
    """
    proxies = []
    invalid_count = 0
    
    lines = _read_proxy_file(file_path)
    
    for line_num, line in enumerate(lines, 1):
        # Check if we've reached the limit
        if limit is not None and len(proxies) >= limit:
            logger.info(f"Reached limit of {limit} proxies, stopping load")
            break
            
        proxy = _process_proxy_line(line, line_num, method)
        if proxy is not None:
            proxies.append(proxy)
        else:
            if line.strip() and not line.strip().startswith('#'):
                invalid_count += 1

    if invalid_count > 0:
        logger.warning(f"Skipped {invalid_count} invalid proxy entries")
        
    return proxies
def save_valid_proxies(file_path: str, valid_proxies: List[Proxy]) -> None:
    """
    Save valid proxies back to file.
    
    Args:
        file_path: Output file path
        valid_proxies: List of valid proxies to save
    """
    try:
        # Sort proxies for consistent output
        sorted_proxies = sorted(valid_proxies, key=lambda p: p.proxy)
        
        with open(file_path, "w", encoding="utf-8") as f:
            for proxy in sorted_proxies:
                f.write(f"{proxy}\n")
                
        logger.info(f"Saved {len(valid_proxies)} valid proxies to {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to save proxies to {file_path}: {e}")
        raise


def _prepare_checking_environment(file: str, method: str, site: str, timeout: int, random_user_agent: bool, limit: Optional[int] = None) -> Tuple[List[Proxy], str, int]:
    """Prepare the environment for proxy checking."""
    print(f"Loading proxies from {file}...")
    proxies = load_proxies_from_file(file, method, limit)
    print(f"Loaded {len(proxies)} valid proxies for checking")
    
    if not proxies:
        print("No valid proxies found to check")
        return [], "", 0
    
    # Choose base user agent
    base_user_agent = random.choice(user_agents)
    
    # Print checking parameters
    max_threads = min(len(proxies), 100)
    print(f"Starting proxy validation with {max_threads} concurrent threads...")
    print(f"Target site: {site}")
    print(f"Timeout: {timeout}s")
    print(f"Method: {method.upper()}")
    print(f"User agent strategy: {'Random per proxy' if random_user_agent else 'Fixed'}")
    print("-" * 60)
    
    return proxies, base_user_agent, max_threads


def _create_proxy_checker(valid_proxies: List[Proxy], checked_count_ref: List[int], lock: threading.Lock,
                          site: str, timeout: int, random_user_agent: bool, base_user_agent: str,
                          total_proxies: int, verbose: bool):
    """Create a proxy checking function with proper closure."""
    def check_single_proxy(proxy: Proxy) -> None:
        """Check a single proxy and update results."""
        try:
            # Select user agent
            current_user_agent = random.choice(user_agents) if random_user_agent else base_user_agent
            
            # Check proxy
            is_valid, response_time, error = proxy.check(site, timeout, current_user_agent, verbose)
            
            # Update results thread-safely
            with lock:
                checked_count_ref[0] += 1
                
                if is_valid:
                    valid_proxies.append(proxy)
                
                # Progress indicator
                if not verbose and checked_count_ref[0] % 50 == 0:
                    print(f"Progress: {checked_count_ref[0]}/{total_proxies} ({len(valid_proxies)} valid)")
                    
        except Exception as e:
            logger.debug(f"Unexpected error checking proxy {proxy}: {e}")
    
    return check_single_proxy


def check(file: str, timeout: int, method: str, site: str, verbose: bool, random_user_agent: bool, limit: Optional[int] = None) -> None:
    """
    Main proxy checking function.
    
    Args:
        file: Path to proxy list file
        timeout: Connection timeout in seconds
        method: Proxy method to check
        site: Target website for testing
        verbose: Enable verbose output
        random_user_agent: Use random user agent per proxy
        limit: Maximum number of proxies to check
    """
    start_time = time()
    
    # Prepare checking environment
    proxies, base_user_agent, max_threads = _prepare_checking_environment(
        file, method, site, timeout, random_user_agent, limit,
    )
    
    if not proxies:
        return
    
    # Initialize checking state
    valid_proxies = []
    checked_count_ref = [0]  # Use list for mutable reference
    lock = threading.Lock()
    
    # Create checker function
    check_single_proxy = _create_proxy_checker(
        valid_proxies, checked_count_ref, lock, site, timeout,
        random_user_agent, base_user_agent, len(proxies), verbose,
    )
    
    _run_proxy_check_threadpool(
        check_single_proxy, proxies, valid_proxies, checked_count_ref, file, start_time,
    )
    elapsed_time = time() - start_time
    # Final statistics
    success_rate = (len(valid_proxies) / len(proxies)) * 100 if proxies else 0
    print("-" * 60)
    print("Proxy checking completed!")
    print(f"Total checked: {len(proxies)}")
    print(f"Valid proxies: {len(valid_proxies)}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Time taken: {elapsed_time:.2f} seconds")
    print(f"Average time per proxy: {elapsed_time/len(proxies):.2f}s")
    if len(valid_proxies) == 0:
        print("WARNING: No working proxies found. Consider:")
        print("   - Increasing timeout value")
        print("   - Trying a different target site")
        print("   - Using fresh proxy list")


def _run_proxy_check_threadpool(check_single_proxy, proxies, valid_proxies, checked_count_ref, file, start_time):
    """Helper to run proxy checking in a thread pool, handles KeyboardInterrupt and saving."""
    executor = None
    try:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=min(len(proxies), 100))
        futures = [executor.submit(check_single_proxy, proxy) for proxy in proxies]
        for _ in concurrent.futures.as_completed(futures):
            pass
    except KeyboardInterrupt:
        print("\n[!] Proxy checking cancelled by user. Stopping threads and saving progress...")
        if executor is not None:
            try:
                executor.shutdown(wait=False, cancel_futures=True)
            except Exception:
                pass
        save_valid_proxies(file, valid_proxies)
        elapsed_time = time() - start_time
        print("-" * 60)
        print(f"Check cancelled. {len(valid_proxies)} valid proxies saved to {file}.")
        print(f"Checked: {checked_count_ref[0]} / {len(proxies)} | Time: {elapsed_time:.2f}s")
        sys.exit(130)
    if executor is not None:
        executor.shutdown(wait=True)
    save_valid_proxies(file, valid_proxies)


def _setup_argument_parser() -> argparse.ArgumentParser:
    """Set up and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Check proxy servers for connectivity and validity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -p http -t 10 -v                    # Check HTTP proxies with 10s timeout
  %(prog)s -p socks4 -l socks.txt -r           # Check SOCKS4 with random user agents
  %(prog)s -p https -s httpbin.org/ip --debug  # Check HTTPS proxies against custom site
  %(prog)s -p http --limit 50 -v               # Check only the first 50 HTTP proxies
  %(prog)s -p socks5 -l proxies.txt -t 30 --max-threads 20 # Check SOCKS5 proxies with 30s timeout and 20 threads
Notes:
  - Dead proxies are automatically removed from the list file
  - Use --debug for detailed error information
  - Higher timeout values may find more working proxies but take longer
  - Use --limit for quick testing or when you don't want to check all proxies
  - Random user agents can help avoid detection by target sites
  - Use --max-threads to control concurrency, default is 10
        """,
    )
    
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=20,
        help="Connection timeout in seconds (default: %(default)s)",
    )
    parser.add_argument(
        "-p", "--proxy",
        choices=Proxy.SUPPORTED_METHODS,
        default="http",
        help="Proxy type to check (default: %(default)s)",
    )
    parser.add_argument(
        "-l", "--list",
        default="output.txt",
        help="Path to proxy list file (default: %(default)s)",
    )
    parser.add_argument(
        "-s", "--site",
        default="https://httpbin.org/ip",
        help="Target website for testing (default: %(default)s)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output showing each proxy check",
    )
    parser.add_argument(
        "-r", "--random_agent",
        action="store_true",
        help="Use a different random user agent for each proxy",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging for troubleshooting",
    )
    parser.add_argument(
        "--max-threads",
        type=int,
        default=10,
        help="Maximum number of concurrent threads (default: %(default)s)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of proxies to check (default: check all)",
    )
    
    return parser


def _configure_logging_and_validate_args(args) -> str:
    """Configure logging and validate arguments."""
    # Configure logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Validate arguments
    if args.timeout <= 0:
        print("Error: Timeout must be positive")
        sys.exit(1)
    
    if args.max_threads <= 0:
        print("Error: max-threads must be positive")
        sys.exit(1)
    
    # Check if proxy file exists
    if not Path(args.list).exists():
        print(f"Error: Proxy file '{args.list}' not found")
        print("Tip: Run the proxy scraper first to generate a proxy list")
        sys.exit(1)
    
    # Normalize site URL
    site = args.site
    if not site.startswith(('http://', 'https://')):
        site = f"https://{site}"
    
    return site


def main() -> None:
    """Main entry point for the proxy checker."""
    parser = _setup_argument_parser()
    args = parser.parse_args()
    
    # Configure logging and validate arguments
    site = _configure_logging_and_validate_args(args)
    
    # Display startup information
    print("*** Proxy Checker v2.0 ***")
    print(f"Proxy file: {args.list}")
    print(f"Target site: {site}")
    print(f"Timeout: {args.timeout}s")
    print(f"Method: {args.proxy.upper()}")
    print(f"Max threads: {args.max_threads}")
    if args.limit:
        print(f"Limit: {args.limit} proxies")
    print(f"User agents: {len(user_agents)} available")
    print("=" * 60)
    
    try:
        check(
            file=args.list,
            timeout=args.timeout,
            method=args.proxy,
            site=site,
            verbose=args.verbose,
            random_user_agent=args.random_agent,
            limit=args.limit,
        )
        
    except KeyboardInterrupt:
        print("\nWARNING: Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Proxy checking failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
