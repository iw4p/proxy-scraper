from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import random
import threading 


ua = UserAgent(verify_ssl=False)
proxies = [] # Will contain proxies [ip, port]

# Main function
def main():

  # Retrieve latest proxies
  proxies_req = Request('https://www.sslproxies.org/')
  proxies_req.add_header('User-Agent', ua.random)
  proxies_doc = urlopen(proxies_req).read().decode('utf8')

  soup = BeautifulSoup(proxies_doc, 'html.parser')
  proxies_table = soup.find(id='proxylisttable')

  # Save proxies in the array
  for row in proxies_table.tbody.find_all('tr'):
    proxies.append({
      'ip':   row.find_all('td')[0].string,
      'port': row.find_all('td')[1].string
    })

  for row in proxies_table.tbody.find_all('tr'):
    print(row.find_all('td')[0].string + ":" + row.find_all('td')[1].string)
 



if __name__ == '__main__':
  main()

  