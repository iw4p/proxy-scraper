import urllib.request
import threading
import random
import sys
import os
import argparse
from time import time

useragents=('Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')

proxyType = ''

def checkproxy(txtfile):
	global out_file
	candidate_proxies = open(txtfile).readlines()
	filedl = open(txtfile, "w")
	filedl.close()
	out_file = open(txtfile, "a")
	threads = []
	for i in candidate_proxies:
		t = threading.Thread(target=checker, args=[i])
		t.start()
		threads.append(t)

	for t in threads:
		t.join()

	out_file.close()
	if args.verbose:
		print("\n\nCurrent IPs in proxylist: %s\n" % (len(open(txtfile).readlines())))

def checker(i):
	proxy = proxyType + '://' + i
	proxy_support = urllib.request.ProxyHandler({proxyType: proxy})
	opener = urllib.request.build_opener(proxy_support)
	urllib.request.install_opener(opener)
	global site
	req = urllib.request.Request(proxyType + '://' + site)
	req.add_header("User-Agent", useragents)
	try:
		global chosenTimeout
		start_time = time()
		urllib.request.urlopen(req, timeout=chosenTimeout)
		end_time = time()
		time_taken = end_time - start_time
		out_file.write(i)
		if args.verbose:
			print ("%s works!" % proxy)
			print('time: ' + str(time_taken) + '\n')
	except:
		pass
		if args.verbose:
			print ("%s does not respond.\n" % proxy)




if __name__ == "__main__":

	global chosenTimeout
	global txtfile
	global site

	parser = argparse.ArgumentParser()
	parser.add_argument("-t", "--timeout", type=int, help="dismiss the proxy after -t seconds", default=20)
	parser.add_argument("-p", "--proxy", help="check HTTPS or HTTP proxies", default='http')
	parser.add_argument("-l", "--list", help="path to your list.txt", default='output.txt')
	parser.add_argument("-s", "--site", help="check with specific website like google.com", default='google.com')
	parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
	args = parser.parse_args()

	chosenTimeout = args.timeout
	txtfile = args.list
	site = args.site
	proxyType = args.proxy

	threading.Thread(target=checkproxy, args=(txtfile,)).start()
