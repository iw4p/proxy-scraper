import argparse
import random
import re
import threading
import urllib.request
from time import time

user_agents = []
with open("user_agents.txt", "r") as f:
    for line in f:
        user_agents.append(line.replace("\n", ""))


class Proxy:
    def __init__(self, method, proxy):
        if method.lower() not in ["http", "https"]:
            raise NotImplementedError("Only HTTP and HTTPS are supported")
        self.method = method.lower()
        self.proxy = proxy

    def is_valid(self):
        return re.match(r"\d{1,3}(?:\.\d{1,3}){3}(?::\d{1,5})?$", self.proxy)

    def check(self, site, timeout, user_agent):
        url = self.method + "://" + self.proxy
        proxy_support = urllib.request.ProxyHandler({self.method: url})
        opener = urllib.request.build_opener(proxy_support)
        urllib.request.install_opener(opener)
        req = urllib.request.Request(self.method + "://" + site)
        req.add_header("User-Agent", user_agent)
        try:
            start_time = time()
            urllib.request.urlopen(req, timeout=timeout)
            end_time = time()
            time_taken = end_time - start_time
            return True, time_taken, None
        except Exception as e:
            return False, 0, e

    def __str__(self):
        return self.proxy


def verbose_print(verbose, message):
    if verbose:
        print(message)


def check(file, timeout, method, site, verbose, random_user_agent):
    proxies = []
    with open(file, "r") as f:
        for line in f:
            proxies.append(Proxy(method, line.replace("\n", "")))

    print(f"Checking {len(proxies)} proxies")
    proxies = filter(lambda x: x.is_valid(), proxies)
    valid_proxies = []
    user_agent = random.choice(user_agents)

    def check_proxy(proxy, user_agent):
        new_user_agent = user_agent
        if random_user_agent:
            new_user_agent = random.choice(user_agents)
        valid, time_taken, error = proxy.check(site, timeout, new_user_agent)
        message = {
            True: f"{proxy} is valid, took {time_taken} seconds",
            False: f"{proxy} is invalid: {repr(error)}",
        }[valid]
        verbose_print(verbose, message)
        valid_proxies.extend([proxy] if valid else [])

    threads = []
    for proxy in proxies:
        t = threading.Thread(target=check_proxy, args=(proxy, user_agent))
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    with open(file, "w") as f:
        for proxy in valid_proxies:
            f.write(str(proxy) + "\n")

    print(f"Found {len(valid_proxies)} valid proxies")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        help="Dismiss the proxy after -t seconds",
        default=20,
    )
    parser.add_argument("-p", "--proxy", help="Check HTTPS or HTTP proxies", default="http")
    parser.add_argument("-l", "--list", help="Path to your proxy list file", default="output.txt")
    parser.add_argument(
        "-s",
        "--site",
        help="Check with specific website like google.com",
        default="https://google.com/",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Increase output verbosity",
        action="store_true",
    )
    parser.add_argument(
        "-r",
        "--random_agent",
        help="Use a random user agent per proxy",
        action="store_true",
    )
    args = parser.parse_args()
    check(file=args.list, timeout=args.timeout, method=args.proxy, site=args.site, verbose=args.verbose,
          random_user_agent=args.random_agent)
