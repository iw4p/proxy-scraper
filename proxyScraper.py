import argparse
import os
import re
import threading

import requests
from bs4 import BeautifulSoup

pathTextFile = ""
proxyType = ""

# From spys.me
def spys_me_scraper(proxytype):
    response = requests.get("https://spys.me/" + proxytype + ".txt")
    proxies = response.text

    pattern = re.compile("\\d{1,3}(?:\\.\\d{1,3}){3}(?::\\d{1,5})?")
    matcher = re.findall(pattern, proxies)

    with open(pathTextFile, "a") as txt_file:
        for proxy in matcher:
            txt_file.write(proxy + "\n")


# From proxyscrape.com
def proxy_scrape_scraper(proxytype, timeout, country):
    response = requests.get(
        "https://api.proxyscrape.com/?request=getproxies&proxytype="
        + proxytype
        + "&timeout="
        + timeout
        + "&country="
        + country,
    )

    proxies = response.text
    with open(pathTextFile, "a") as txt_file:
        txt_file.write(proxies)


# From proxy-list.download
def proxy_list_download_scraper(url, proxy_type, anon):
    session = requests.session()
    url = url + "?type=" + proxy_type + "&anon=" + anon
    html = session.get(url).text
    if args.verbose:
        print(url)
    with open(pathTextFile, "a") as txt_file:
        for line in html.split("\n"):
            if len(line) > 0:
                txt_file.write(line)


def scrape_proxies(url):
    page = requests.get(url)
    if args.verbose:
        print(url + " scraped successfully")
    soup = BeautifulSoup(page.text, "html.parser")

    proxies = set()
    table = soup.find("table", attrs={"class": "table table-striped table-bordered"})
    for row in table.findAll("tr"):
        count = 0
        proxy = ""
        for cell in row.findAll("td"):
            if count == 1:
                proxy += ":" + cell.text.replace("&nbsp;", "")
                proxies.add(proxy)
                break
            proxy += cell.text.replace("&nbsp;", "")
            count += 1

    with open(pathTextFile, "a") as txt_file:
        for line in proxies:
            txt_file.write("".join(line) + "\n")


# output watcher
def output():
    if os.path.exists(pathTextFile):
        os.remove(pathTextFile)
    elif not os.path.exists(pathTextFile):
        with open(pathTextFile, "w"):
            pass


def start_https():
    threading.Thread(target=scrape_proxies, args=("http://sslproxies.org",)).start()
    threading.Thread(
        target=proxy_list_download_scraper,
        args=(
            "https://www.proxy-list.download/api/v1/get",
            "https",
            "elite",
        ),
    ).start()
    output()


def start_http():
    threading.Thread(
        target=scrape_proxies,
        args=("http://free-proxy-list.net",),
    ).start()
    threading.Thread(target=scrape_proxies, args=("http://us-proxy.org",)).start()
    threading.Thread(
        target=proxy_scrape_scraper,
        args=(
            "http",
            "1000",
            "All",
        ),
    ).start()

    for status in ["elite", "transparent", "anonymous"]:
        threading.Thread(
            target=proxy_list_download_scraper,
            args=(
                "https://www.proxy-list.download/api/v1/get",
                "http",
                status,
            ),
        ).start()

    threading.Thread(target=spys_me_scraper, args=("proxy",)).start()
    output()


def start_socks():
    threading.Thread(target=scrape_proxies, args=("http://socks-proxy.net",)).start()
    threading.Thread(
        target=proxy_scrape_scraper,
        args=(
            "socks4",
            "1000",
            "All",
        ),
    ).start()
    threading.Thread(
        target=proxy_scrape_scraper,
        args=(
            "socks5",
            "1000",
            "All",
        ),
    ).start()

    for socks in ["socks5", "socks4"]:
        threading.Thread(
            target=proxy_list_download_scraper,
            args=(
                "https://www.proxy-list.download/api/v1/get",
                socks,
                "elite",
            ),
        ).start()

    threading.Thread(target=spys_me_scraper, args=("socks",)).start()
    output()


def start_socks4():
    threading.Thread(
        target=proxy_scrape_scraper,
        args=(
            "socks4",
            "1000",
            "All",
        ),
    ).start()
    threading.Thread(
        target=proxy_list_download_scraper,
        args=(
            "https://www.proxy-list.download/api/v1/get",
            "socks4",
            "elite",
        ),
    ).start()
    output()


def start_socks5():
    threading.Thread(
        target=proxy_scrape_scraper,
        args=(
            "socks5",
            "1000",
            "All",
        ),
    ).start()
    threading.Thread(
        target=proxy_list_download_scraper,
        args=(
            "https://www.proxy-list.download/api/v1/get",
            "socks5",
            "elite",
        ),
    ).start()
    output()


if __name__ == "__main__":
    global proxy

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--proxy",
        help="Supported proxy type: http ,https, socks, socks4, socks5",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="output file name to save .txt file",
        default="output.txt",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="increase output verbosity",
        action="store_true",
    )
    args = parser.parse_args()

    proxy = args.proxy
    pathTextFile = args.output

    if proxy == "https":
        start_https()

    if proxy == "http":
        start_http()

    if proxy == "socks":
        start_socks()

    if proxy == "socks4":
        start_socks4()

    if proxy == "socks5":
        start_socks5()
