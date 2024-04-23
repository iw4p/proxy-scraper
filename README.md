# Proxy scraper and checker

[![Tests](https://github.com/iw4p/proxy-scraper/actions/workflows/tests.yml/badge.svg)](https://github.com/iw4p/proxy-scraper/actions/workflows/tests.yml)

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

Use this command to install dependencies.

```bash
pip3 install -r requirements.txt
```

## Usage

For scraping:

```bash
python3 proxyScraper.py -p http
```

- With `-p` or `--proxy`, You can choose your proxy type. Supported proxy types are: **HTTP - HTTPS - Socks (Both 4 and 5) - Socks4 - Socks5**
- With `-o` or `--output`, create and write to a .txt file. (Default is **output.txt**)
- With `-v` or `--verbose`, more details.
- With `-h` or `--help`, Show help to who did't read this README.

For checking:

```bash
python3 proxyChecker.py -p http -t 20 -s https://google.com -l output.txt

python3 proxyChecker.py -p https -t 20 -s https://google.com -l output.txt

python3 proxyChecker.py -p socks4 -t 20 -s https://google.com -l output.txt

python3 proxyChecker.py -p socks5 -t 20 -s https://google.com -l output.txt
```

- With `-t` or `--timeout`, dismiss the proxy after -t seconds (Default is **20**)
- With `-p` or `--proxy`, check HTTPS,HTTP,SOCKS4 or SOCKS5 proxies (Default is **HTTP**)
- With `-l` or `--list`, path to your list.txt. (Default is **output.txt**)
- With `-s` or `--site`, check with specific website like google.com. (Default is **google.com**)
- With `-r` or `--random_agent`, it will use a random user agent per proxy.
- With `-v` or `--verbose`, more details.
- With `-h` or `--help`, Show help to who did't read this README.

## Good to know

- Dead proxies will be removed and just alive proxies will stay.
- This script is also able to scrape Socks, but proxyChecker only checks HTTP(S) proxies.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=iw4p/proxy-scraper&type=Date)](https://star-history.com/#iw4p/proxy-scraper&Date)

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

### Issues

Feel free to submit issues and enhancement requests or contact me via [vida.page/nima](https://vida.page/nima).

## License

[MIT](https://choosealicense.com/licenses/mit/)
