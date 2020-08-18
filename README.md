# Proxy scraper and checker 

Scrape and check more than 600 HTTP proxies in less than 20 seconds.

Scraping fresh public proxies from 4 different sources:

* [sslproxies.org](http://sslproxies.org) (HTTP, HTTPS)
* [free-proxy-list.net](http://free-proxy-list.net) (HTTP, HTTPS)
* [us-proxy.org](http://us-proxy.org) (HTTP, HTTPS)
* [socks-proxy.net](http://socks-proxy.net) (Socks4, Socks5)
* [proxyscrape.com](https://proxyscrape.com) (HTTP, Socks4, Socks5)

## Installation

Use this command to install dependencies.


```bash
pip3 install -r requirements.txt
```

## Usage

For scraping:

```bash
python3 proxyScraper.py
```

The result will be in output.txt on your current directory.

For checking:

```bash
python3 proxyChecker.py -t 20 -l output.txt
```

## Good to know
* Dead proxies will be removed and just alive proxies will stay.
* You can change timeout in proxyChecker.py.
* This script is able to scrape Socks, but proxyChecker only check HTTP proxies.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Credit
* [Proxy Scraper](https://github.com/Abigdog4/ProxyScrapper)
* [Proxy Checker](https://github.com/byRo0t96/proxy_checker)

## License
[MIT](https://choosealicense.com/licenses/mit/)
