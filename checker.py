#!/usr/bin/python3

'''
    PROX - utility for checking proxy in terminal under the GNU GPL V3.0 Licensy
    AUTHORS: Hasanov Abdurahmon & Ilyosiddin Kalandar
    Version: 0.2
'''

from sys import argv
import urllib3
from os import system as terminal
import requests
from colorama import Fore,Style

URL = "http://google.com"
CMD_CLEAR_TERM = "clear"
TIMEOUT = (3.05,27)

def check_proxy(proxy):
    '''
        Function for check proxy return ERROR
        if proxy is Bad else
        Function return None
    '''
    try:
        session = requests.Session()
        session.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'
        session.max_redirects = 300
        proxy = proxy.split('\n',1)[0]
        print(Fore.LIGHTYELLOW_EX + 'Checking ' + proxy)
        session.get(URL, proxies={'http':'http://' + proxy}, timeout=TIMEOUT,allow_redirects=True)
    except requests.exceptions.ConnectionError as e:
        print(Fore.LIGHTRED_EX + 'Error!')
        return e
    except requests.exceptions.ConnectTimeout as e:
        print(Fore.LIGHTRED_EX + 'Error,Timeout!')
        return e
    except requests.exceptions.HTTPError as e:
        print(Fore.LIGHTRED_EX + 'HTTP ERROR!')
        return e
    except requests.exceptions.Timeout as e:
        print(Fore.LIGHTRED_EX + 'Error! Connection Timeout!')
        return e
    except urllib3.exceptions.ProxySchemeUnknown as e:
        print(Fore.LIGHTRED_EX + 'ERROR unkown Proxy Scheme!')
        return e
    except requests.exceptions.TooManyRedirects as e:
        print(Fore.LIGHTRED_EX + 'ERROR! Too many redirects!')
        return e
def print_help():
    terminal(CMD_CLEAR_TERM)
    print(Fore.LIGHTGREEN_EX + 'PROX v0.2 - Utility for checking proxy in terminal')
    print(Fore.LIGHTGREEN_EX + 'Authors: Hasanov Abdurahmon & Ilyosiddin Kalandar')
    print(Fore.LIGHTCYAN_EX)
    print('Usage -> prox -f <filename> - Check file with proxies')
    print('prox -p <proxy> - check only one proxy')
    print('prox --help - show this menu')

if len(argv) > 1:
    commands = ['--help','-h','-f','-p','/?','--file','-file','--proxy','-proxy']
    if argv[1] in commands:
        if argv[1] in ('--help','-help','/?','--?'):
            print_help()
        elif argv[1] in ('-f','--file','-file'):
            try:
                file = open(argv[2])
                proxies = list(file)
                goods = 0
                terminal(CMD_CLEAR_TERM)
                print(Fore.LIGHTCYAN_EX + '===========================================')
                for proxy in proxies:
                    try:
                        if check_proxy(proxy):
                            print(Fore.LIGHTRED_EX + 'Bad proxy ' + proxy)
                        else:
                            print(Fore.LIGHTGREEN_EX + 'Good proxy ' + proxy)
                            file_with_goods = open('good.txt','a')
                            file_with_goods.write(proxy)
                            goods += 1
                        print(Fore.LIGHTCYAN_EX + '=================================================')
                    except KeyboardInterrupt:
                        print(Fore.LIGHTGREEN_EX + '\nExit.')
                        exit()
                print(Fore.LIGHTGREEN_EX + 'Total ' + str(goods) + ' good proxies found')
                print(Fore.LIGHTRED_EX + 'And ' + str(len(proxies) - goods) + ' is bad')
                print(Fore.LIGHTYELLOW_EX + 'Have nice day! :)')
                print()
            except FileNotFoundError:
                print(Fore.LIGHTRED_EX + 'Error!\nFile Not found!')
            except IndexError:
                print(Fore.LIGHTRED_EX + 'Error!\nMissing filename!')
        elif argv[1] in ('-p','--proxy','-proxy'):
            try:
                argv[2] = argv[2].split(' ')[0]
                if check_proxy(argv[2]):
                    print(Fore.LIGHTRED_EX + 'BAD PROXY ' + argv[2])
                else:
                    print(Fore.LIGHTGREEN_EX + 'GOOD PROXY ' + argv[2])
            except IndexError:
                print(Fore.LIGHTRED_EX + 'Error! Missing proxy!')
    else:
        print(Fore.LIGHTRED_EX + 'Unknown option \"' + argv[1] + '\"')
else:
    print_help()