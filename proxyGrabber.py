import csv
import requests
from bs4 import BeautifulSoup
from multiprocessing.pool import ThreadPool

urls = ["http://sslproxies.org", "http://free-proxy-list.net", "http://us-proxy.org", "http://socks-proxy.net"]

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

    print ("Proxies:" + str(proxies))
