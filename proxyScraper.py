import requests
from bs4 import BeautifulSoup
import threading
import os
import asyncio


pathTextFile = 'output.txt'

def scrapeAPI(proxytype, timeout, country):
    response = requests.get("https://api.proxyscrape.com/?request=getproxies&proxytype=" + proxytype + "&timeout=" + timeout + "&country=" + country)
    proxies = response.text
    with open(pathTextFile, "a") as txt_file:
        txt_file.write(proxies)


def makesoup(url):
    page=requests.get(url)
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
    result = proxyscrape(table = soup.find('table', attrs={'id': 'proxylisttable'}))
    proxies = set()
    proxies.update(result)
    with open(pathTextFile, "a") as txt_file:
        for line in proxies:
            print(line)
            txt_file.write("".join(line) + "\n")
    


if __name__ == "__main__":

    if os.path.exists(pathTextFile):
        os.remove(pathTextFile)
    elif not os.path.exists(pathTextFile):
        with open(pathTextFile, 'w'): pass

    threading.Thread(target=scrapeproxies, args=('http://sslproxies.org',)).start()
    threading.Thread(target=scrapeproxies, args=('http://free-proxy-list.net',)).start()
    threading.Thread(target=scrapeproxies, args=('http://us-proxy.org',)).start()

    threading.Thread(target=scrapeAPI, args=('http','1000','All',)).start()

    # TODO: Socks does not support for checker script at this time
    
    # threading.Thread(target=scrapeproxies, args=('http://socks-proxy.net',)).start()
    # threading.Thread(target=scrapeAPI, args=('socks4','1000','All',)).start()
    # threading.Thread(target=scrapeAPI, args=('socks5','1000','All',)).start()

