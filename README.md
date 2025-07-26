# Proxy Scraper & Checker

[![Tests](https://github.com/iw4p/proxy-scraper/actions/workflows/tests.yml/badge.svg)](https://github.com/iw4p/proxy-scraper/actions/workflows/tests.yml)
[![Downloads](https://static.pepy.tech/badge/proxyz)](https://pepy.tech/project/proxyz)

**Fast, reliable proxy scraper that collects 30K+ HTTP/HTTPS/SOCKS proxies from 5+ sources in seconds.**

✨ **Features:**
- ⚡ **Fast scraping** - All sources scraped concurrently  
- 🛡️ **Smart filtering** - Automatically removes CDN/bad IPs (Cloudflare, etc.)
- 🌍 **Global coverage** - Proxies from Asia, Europe, Americas
- 🔧 **Easy to use** - Simple CLI interface
- ✅ **Quality checked** - Built-in proxy validation

## Installation & Setup

### 📦 Option 1: Install from PyPI (Recommended)

You can install the package directly from PyPI using `pip`:

```bash
pip install proxyz
```

**Verify installation:**
```bash
proxy_scraper --help
proxy_checker --help
```

### 🔧 Option 2: Install from Source Code

Alternatively, you can install dependencies manually if you're working from the source code:

```bash
# Clone the repository
git clone https://github.com/iw4p/proxy-scraper.git
cd proxy-scraper

# Install dependencies
pip3 install -r requirements.txt

# Test the installation
python proxyScraper.py --help
python proxyChecker.py --help
```

### 🐍 Python Requirements
- **Python 3.9+** (3.9, 3.10, 3.11, 3.12 supported)
- **Dependencies:** httpx, beautifulsoup4, pysocks

## Quick Start Tutorial

### Step 1: Scrape Proxies
```bash
# Get HTTP proxies (basic)
proxy_scraper -p http

# Get HTTPS proxies
proxy_scraper -p https

# Get SOCKS4 proxies
proxy_scraper -p socks4

# Get SOCKS5 proxies
proxy_scraper -p socks5

# Get all SOCKS proxies (SOCKS4 + SOCKS5)
proxy_scraper -p socks

# Save to custom file (example: HTTP)
proxy_scraper -p http -o output.txt -v

# Save HTTPS proxies with verbose output
proxy_scraper -p https -v -o output.txt

# Save SOCKS4 proxies
proxy_scraper -p socks4 -o output.txt

# Save SOCKS5 proxies
proxy_scraper -p socks5 -o output.txt
```


### Step 2: Check Proxy Quality
```bash
# Test scraped HTTP proxies (basic)
proxy_checker -l output.txt -t 10

# Test HTTP proxies
proxy_checker -p http -l output.txt -t 10

# Test HTTPS proxies
proxy_checker -p https -l output.txt -t 10

# Test SOCKS4 proxies
proxy_checker -p socks4 -l output.txt -t 10

# Test SOCKS5 proxies
proxy_checker -p socks5 -l output.txt -t 10

# Test against specific site with verbose output
proxy_checker -l output.txt -s https://google.com -v

# Use random user agents for testing
proxy_checker -l output.txt -r -v
```

### Step 3: Complete Workflow Example
```bash
# 1. Scrape HTTP proxies
proxy_scraper -p http -v -o output.txt

# 2. Scrape HTTPS proxies
proxy_scraper -p https -v -o output.txt

# 3. Scrape SOCKS4 proxies
proxy_scraper -p socks4 -v -o output.txt

# 4. Scrape SOCKS5 proxies
proxy_scraper -p socks5 -v -o output.txt

# 5. Check HTTP proxies
proxy_checker -l output.txt -t 15 -v

# 6. Check HTTPS proxies
proxy_checker -l output.txt -t 15 -v

# 7. Check SOCKS4 proxies
proxy_checker -l output.txt -t 15 -v

# 8. Check SOCKS5 proxies
proxy_checker -l output.txt -t 15 -v

# 9. Result: output.txt contains only working proxies (for each type)
```

## Supported Proxy Types
- **HTTP** - Web traffic
- **HTTPS** - Secure web traffic  
- **SOCKS4** - TCP connections
- **SOCKS5** - TCP + UDP connections

## Proxy Sources

We collect proxies from **24 sources**:

**🌐 Direct Websites (11 sources)**
- spys.me, free-proxy-list.net, proxyscrape.com, geonode.com
- sslproxies.org, us-proxy.org, socks-proxy.net  
- proxy-list.download, proxyscan.io, proxyspace.pro
- freeproxy.lunaproxy.com, more

**📦 GitHub Repositories (13 sources)**  
- proxifly/free-proxy-list, monosans/proxy-list, TheSpeedX/PROXY-List
- jetkai/proxy-list, roosterkid/openproxylist, mmpx12/proxy-list
- ShiftyTR/Proxy-List, clarketm/proxy-list, sunny9577/proxy-scraper
- zloi-user/hideip.me, almroot/proxylist, aslisk/proxyhttps
- proxy4parsing/proxy-list, more

## Advanced Usage

### CLI Options

**Scraping:**
```bash
proxy_scraper -p <type> [-o output.txt] [-v]

Options:
  -p, --proxy     Proxy type: http, https, socks, socks4, socks5
  -o, --output    Output file (default: output.txt)  
  -v, --verbose   Show detailed statistics
  -l, --list      Input proxy file (default: output.txt)
  -h, --help      Show this help message
```

**Checking:**
```bash
proxy_checker [-l input.txt] [-t timeout] [-s site] [-v]

Options:
  -l, --list      Input proxy file (default: output.txt)
  -p, --proxy     Proxy type: http, https, socks, socks4, socks5
  -o, --output    Output file (default: output.txt)
  -t, --timeout   Timeout in seconds (default: 20)
  -s, --site      Test site (default: https://google.com)
  -r, --random_agent  Use random user agents
  -v, --verbose   Show detailed progress
  --max-threads  Maximum concurrent threads (default: 10)
```

### From Source Code
```bash
# Clone repository
git clone https://github.com/iw4p/proxy-scraper
cd proxy-scraper

# Install dependencies  
pip install -r requirements.txt

# Run scraper
python proxyScraper.py -p http -v

# Check proxies
python proxyChecker.py -l output.txt -v
```

## Quality & Performance

- ✅ **Automatic filtering** - Removes bad IPs (Cloudflare, CDNs, private ranges)
- 📊 **Source statistics** - See which sources provide the best proxies
- ⚡ **Fast concurrent** - All sources scraped simultaneously


## Example Output
```bash
*** Source Statistics ***
--------------------------------------------------
PlainTextScraper: 0 valid, 0 bad IPs, 0 invalid
GeneralTableScraper: 0 valid, 0 bad IPs, 0 invalid
ProxyScrapeScraper: 1666 valid, 334 bad IPs, 0 invalid
GitHubScraper: 0 valid, 0 bad IPs, 0 invalid
ProxyListApiScraper: 261 valid, 0 bad IPs, 0 invalid
GeneralDivScraper: 0 valid, 0 bad IPs, 0 invalid
SpysMeScraper: 400 valid, 0 bad IPs, 0 invalid

Total filtered: 334 bad IPs (CDN/etc), 0 invalid format
Writing 37030 unique proxies to output.txt...
Scraping completed in 13.13 seconds
Found 37030 unique valid proxies
```

## 🌍 Proxy Geolocation & Analysis

The project includes a powerful geolocation tool to analyze proxy origins and track sources:

### Features
- **🔍 IP Geolocation** - Get country, city, ISP, and organization info
- **☁️ CDN Detection** - Automatically identifies Cloudflare and other CDNs  
- **🏢 Datacenter Detection** - Flags hosting providers and datacenters
- **📊 Source Tracking** - Maps proxies back to their original sources
- **💾 JSON Export** - Save analysis results for further processing

### Usage Examples

**Analyze single IP:**
```bash
python proxyGeolocation.py -i 104.16.1.31
```

**Analyze proxy file:**
```bash
python proxyGeolocation.py -f output.txt -l 50
```

**Track proxy sources:**
```bash
python proxyGeolocation.py -f output.txt -s --limit 100
```

**Export to JSON:**
```bash
python proxyGeolocation.py -f output.txt -o analysis.json
```

### Sample Output
```bash
🔍 Proxy Geolocation Analysis Results
==================================================

📊 Summary:
Total proxies analyzed: 50
Proxies with geolocation data: 45
Cloudflare proxies: 8
Datacenter proxies: 12

🌎 Countries:
  United States (US): 15
  Germany (DE): 8
  Singapore (SG): 6
  ...

📋 Detailed Results:
────────────────────────────────────────────────────────────────
☁️ 104.16.1.31:80 - San Francisco, United States | Cloudflare Inc.
🌍  45.79.143.52:3128 - Tokyo, Japan | Linode LLC
🏢  159.203.61.169:3128 - New York, United States | DigitalOcean
```

## Good to Know

- Dead proxies will be removed, and only alive proxies will remain in the output file.
- The proxy checker supports all proxy types: **HTTP, HTTPS, SOCKS4, and SOCKS5**.
- Use random user agents (`-r` flag) for better success rates when checking proxies.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=iw4p/proxy-scraper&type=Date)](https://star-history.com/#iw4p/proxy-scraper&Date)

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

### Issues

Feel free to submit issues and enhancement requests or contact me via [vida.page/nima](https://vida.page/nima).

## License

[MIT](https://choosealicense.com/licenses/mit/)
