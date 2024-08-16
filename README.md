# Proxy Scraper and Checker

[![Tests](https://github.com/iw4p/proxy-scraper/actions/workflows/tests.yml/badge.svg)](https://github.com/iw4p/proxy-scraper/actions/workflows/tests.yml)
[![Downloads](https://static.pepy.tech/badge/proxyz)](https://pepy.tech/project/proxyz)

Scrape more than 1K HTTP - HTTPS - SOCKS4 - SOCKS5 proxies in less than 2 seconds.

Scraping fresh public proxies from different sources:

- [sslproxies.org](http://sslproxies.org) (HTTP, HTTPS)
- [free-proxy-list.net](http://free-proxy-list.net) (HTTP, HTTPS)
- [us-proxy.org](http://us-proxy.org) (HTTP, HTTPS)
- [socks-proxy.net](http://socks-proxy.net) (Socks4, Socks5)
- [proxyscrape.com](https://proxyscrape.com) (HTTP, Socks4, Socks5)
- [proxy-list.download](https://www.proxy-list.download) (HTTP, HTTPS, Socks4, Socks5)
- [geonode.com](https://geonode.com) (HTTP, HTTPS, Socks4, Socks5)

## Installation

You can install the package directly from PyPI using `pip`:

```bash
pip install proxyz
```

Alternatively, you can install dependencies manually if you're working from the source code:

```bash
pip3 install -r requirements.txt
```

## Usage

### Using the Command-Line Interface

Once installed via `pip`, you can use the command-line tools `proxy_scraper` and `proxy_checker` directly.

#### For Scraping Proxies:

```bash
proxy_scraper -p http
```

- With `-p` or `--proxy`, you can choose your proxy type. Supported proxy types are: **HTTP - HTTPS - Socks (Both 4 and 5) - Socks4 - Socks5**.
- With `-o` or `--output`, specify the output file name where the proxies will be saved. (Default is **output.txt**).
- With `-v` or `--verbose`, increase output verbosity.
- With `-h` or `--help`, show the help message.

#### For Checking Proxies:

```bash
proxy_checker -p http -t 20 -s https://google.com -l output.txt
```

- With `-t` or `--timeout`, set the timeout in seconds after which the proxy is considered dead. (Default is **20**).
- With `-p` or `--proxy`, check HTTPS, HTTP, SOCKS4, or SOCKS5 proxies. (Default is **HTTP**).
- With `-l` or `--list`, specify the path to your proxy list file. (Default is **output.txt**).
- With `-s` or `--site`, check proxies against a specific website like google.com. (Default is **https://google.com**).
- With `-r` or `--random_agent`, use a random user agent per proxy.
- With `-v` or `--verbose`, increase output verbosity.
- With `-h` or `--help`, show the help message.

### Running Directly from Source

If you prefer running the scripts directly from the source code, you can use the following commands:

#### For Scraping:

```bash
python3 proxyScraper.py -p http
```

#### For Checking:

```bash
python3 proxyChecker.py -p http -t 20 -s https://google.com -l output.txt
```

## Good to Know

- Dead proxies will be removed, and only alive proxies will remain in the output file.
- This script is capable of scraping SOCKS proxies, but `proxyChecker` currently only checks HTTP(S) proxies.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=iw4p/proxy-scraper&type=Date)](https://star-history.com/#iw4p/proxy-scraper&Date)

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

### Issues

Feel free to submit issues and enhancement requests or contact me via [vida.page/nima](https://vida.page/nima).

## License

[MIT](https://choosealicense.com/licenses/mit/)
