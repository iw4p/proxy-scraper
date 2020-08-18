import csv
import requests
from bs4 import BeautifulSoup
from multiprocessing.pool import ThreadPool

urls = ["http://sslproxies.org", "http://free-proxy-list.net", "http://us-proxy.org", "http://socks-proxy.net"]

# TODO: Add New Source for HTTP, Socks4, Socks5 https://proxyscrape.com/free-proxy-list

def scrapeProxyScrape(proxytype, timeout, country):
    response = requests.get("https://api.proxyscrape.com/?request=getproxies&proxytype=" + proxytype + "&timeout=" + timeout + "&country=" + country)
    proxies = response.text
    return proxies


def makesoup(url):
    page=requests.get(url)
    print(url + "  scraped successfully")
    return BeautifulSoup(page.text,"html.parser")

def proxyscrape(table):
    proxies = set()
    for row in table.findAll('tr'):
        fields = row.findAll('td')
        count = 0
        proxy = ""
        for cell in row.findAll('td'):
            if count == 1:
                proxy += ":" + cell.text.replace('&nbsp;', '')
                proxies.add(proxy)
                break
            proxy += cell.text.replace('&nbsp;', '')
            count += 1
    return proxies

def scrapeproxies(url):
    soup=makesoup(url)
    return proxyscrape(table = soup.find('table', attrs={'id': 'proxylisttable'}))


if __name__ == "__main__":
    proxies = set()
    for url in urls:
        new_proxies = scrapeproxies(url)
        proxies.update(new_proxies)
        with open("output.txt", "w") as txt_file:
            for line in proxies:
                txt_file.write("".join(line) + "\n")
    text = scrapeProxyScrape("http", "50", "All")
    print(text)
    with open("output.txt", "a") as txt_file:
            txt_file.write(text)
