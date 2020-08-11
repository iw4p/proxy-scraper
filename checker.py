import asyncio
from sys import argv

import aiohttp

proxy_type = "http"
test_url = "http://www.google.com"
timeout_sec = 4


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# read the list of proxy IPs in proxyList from the first Argument given
filename = argv[1]
proxylistfile = open(filename)
proxyList = proxylistfile.read().splitlines()


async def is_bad_proxy(ipport):
    try:
        session = aiohttp.ClientSession()
        resp = await session.get(test_url, proxy=ipport, timeout=timeout_sec)
        if not resp.headers["Via"]:
            raise "Error"
        # print(bcolors.OKBLUE + "Working:", ipport + bcolors.ENDC)
        session.close()
    except:
        session.close()
        # print(bcolors.FAIL + "Not Working:", ipport + bcolors.ENDC)

tasks = []

loop = asyncio.get_event_loop()

for item in proxyList:
    tasks.append(asyncio.ensure_future(is_bad_proxy("http://" + item)))

print(bcolors.HEADER + "Starting... \n" + bcolors.ENDC)
loop.run_until_complete(asyncio.wait(tasks))
print(bcolors.HEADER + "\n...Finished" + bcolors.ENDC)
loop.close()