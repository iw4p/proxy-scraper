# Proxy grabber and checker 

Grabbing fresh public proxies from 4 different sources

[sslproxies.org](http://sslproxies.org)
[free-proxy-list.net](http://free-proxy-list.net)
[us-proxy.org](http://us-proxy.org)
[socks-proxy.net](http://socks-proxy.net)


## Installation

Use this command to install dependencies.


```bash
pip3 install -r requirements.txt
```

## Usage

For grabbing:

```bash
python3 proxyGrabber.py
```

The result will be on output.txt on your current directory.

For checking:

```bash
python3 proxyChecker.py output.txt
```

Dead proxies will be removed and just alive proxies will stay.


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)