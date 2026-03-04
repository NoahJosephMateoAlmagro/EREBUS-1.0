from collectors.base import PassiveCollector
import requests
import socket
from urllib.parse import urlparse

from exceptions.exceptions import CollectorError


class HttpHeadersCollector(PassiveCollector):

    def __init__(self, timeout: int = 6):
        self.timeout = timeout

    def collect(self, url: str) -> dict:

        headers_result = {}

        try:
            parsed = urlparse(url)
            host = parsed.hostname

            if not host:
                return headers_result

            try:
                socket.getaddrinfo(host, None)
            except socket.gaierror:
                # Host no resolvible → no es error grave
                return headers_result

            try:
                r = requests.head(
                    url,
                    allow_redirects=True,
                    timeout=self.timeout,
                    headers={"User-Agent": "EREBUS/1.0"}
                )
            except requests.RequestException:
                # Fallo HTTP → no consideramos fallo estructural
                return headers_result

            headers_result = {
                k.lower(): v
                for k, v in r.headers.items()
            }

        except Exception as e:
            raise CollectorError(f"HTTP headers collection error for {url}: {e}")

        return headers_result