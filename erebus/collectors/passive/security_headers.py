import requests
import socket
from urllib.parse import urlparse
class SecurityHeadersCollector:

    def __init__(self, timeout=6):
        self.timeout = timeout

    def collect(self, url: str) -> dict:
        host = urlparse(url).hostname
        if not host:
            return {}

        try:
            socket.getaddrinfo(host, None)
        except socket.gaierror:
            return {}

        try:
            r = requests.head(
                url,
                allow_redirects=True,
                timeout=self.timeout,
                headers={"User-Agent": "EREBUS/1.0"}
            )
        except requests.RequestException:
            return {}

        return {
            k.lower(): v
            for k, v in r.headers.items()
        }
