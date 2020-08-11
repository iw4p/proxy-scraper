import csv
import requests
from bs4 import BeautifulSoup
from multiprocessing.pool import ThreadPool


def makesoup(url): # pass url to beautifulsoup to parse html. Url is defined in menu for each site so code doesnt have to be repeated for each site
    page=requests.get(url)
    print(url + "  scraped successfully")
    return BeautifulSoup(page.text,"html.parser")

def proxyscrape(table): # scrape proxy data from table on site, add to list that was created earlier
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

def scrapeproxies(url): # contains the parent  table attribute where proxy data is present 
    soup=makesoup(url)
    return proxyscrape(table = soup.find('table', attrs={'id': 'proxylisttable'}))


def proxy_test(proxy):
    # Using httpbin used to test the proxies
    url = 'http://httpbin.org/ip'
    proxies = {
        'http': f'http://{proxy}',
        'https': f'http://{proxy}',
    }
    try:
        r = requests.get(url, proxies=proxies, timeout=TIMEOUT)
        load_time = round(r.elapsed.total_seconds(), 3)  # Time it took the page to load
        if r.status_code == 200:
            # Check the status code, if 200 write it to the file
            global count_working_proxies
            count_working_proxies += 1
            csv_writer.writerow([proxy, load_time])
            print(f'Working proxy --> {proxy}')


    except requests.exceptions.Timeout:
        print(f'[TIMED OUT] Proxy took too long: {proxy} ')
    except Exception as e:
        print(f'[Error occurred] Proxy not working: {proxy}')
        pass




urls = ["http://sslproxies.org", "http://free-proxy-list.net", "http://us-proxy.org", "http://socks-proxy.net"]

proxies = set()
for url in urls:
    new_proxies = scrapeproxies(url)
    proxies.update(new_proxies)


TIMEOUT = 5
file_path = 'goods.txt'
count_working_proxies = 0

with open(file_path, 'w', newline='', errors='ignore') as f:
    csv_writer = csv.writer(f)
    try:
        # Threading to speed up the proxy testing
        ThreadPool(processes=10).map(proxy_test, proxies)
    except Exception as e:
        print(f'[Thread error] {e}')

print(f'Total amount of working proxies {count_working_proxies}')