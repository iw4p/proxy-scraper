import asyncio
import sys
sys.argv
import aiohttp

proxy_type = "http"
test_url = "http://www.google.com" # URL
timeout = 5
tasks = []
loop = asyncio.get_event_loop()

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

file = 'proxy_list.txt'
proxylistfile = open(file)
proxyList = proxylistfile.read().splitlines()

async def main(ipport):
    try:
        session = aiohttp.ClientSession()
        r = await session.get(test_url, proxy=ipport, timeout=timeout)
        if not r.headers["Via"]:
            raise "Error"
        print(bcolors.OKBLUE + "Working:", ipport + bcolors.ENDC)
        session.close()
    except:
        session.close()
        print(bcolors.FAIL + "Not Working:", ipport + bcolors.ENDC)

for item in proxyList:
    tasks.append(asyncio.ensure_future(main("http://" + item + "/")))

print(bcolors.HEADER + "Now checking... \n" + bcolors.ENDC)
loop.run_until_complete(asyncio.wait(tasks))
print(bcolors.HEADER + "Finished." + bcolors.ENDC)
loop.close()