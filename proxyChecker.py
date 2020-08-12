import urllib.request
import threading
import random
import sys
import os

try:
    txtfile = sys.argv[1]
    f = open(txtfile)
except:
    print('Usage: python3 start.py txtfile.txt')
    sys.exit()

useragents=('Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')


def checkeproxy():
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
	print("\n\nCurrent IPs in proxylist: %s\n" % (len(open(txtfile).readlines())))

def checker(i):
	proxy = 'http://' + i
	proxy_support = urllib.request.ProxyHandler({'http' : proxy})
	opener = urllib.request.build_opener(proxy_support)
	urllib.request.install_opener(opener)
	req = urllib.request.Request(("http://www.google.com"))
	req.add_header("User-Agent", useragents)
	try:
		urllib.request.urlopen(req, timeout=5)
		print ("%s works!\n" % proxy)
		out_file.write(i)
	except:
		print ("%s does not respond.\n" % proxy)

checkeproxy()
