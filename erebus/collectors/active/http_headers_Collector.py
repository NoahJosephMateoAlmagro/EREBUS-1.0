from collectors.base import Collector
import requests
import socket
from urllib.parse import urlparse

from exceptions.exceptions import CollectorError
from shared.logger import Logger
import shared.constants as C

class HTTPHeadersCollector(Collector):
    """
    Collector that retrieves HTTP response headers for a given URL.

    Performs a HEAD request and normalizes headers to lowercase.
    """
    def __init__(self, timeout: int = 6):
        """
        Args:
            timeout (int): HTTP request timeout
        """
        self.timeout = timeout

    def collect(self, url: str) -> dict:
        """
        Fetches HTTP headers for the given URL.

        Args:
            url (str): Target URL

        Returns:
            dict: Response headers (lowercased)
        """

        Logger.info(f"Starting HTTP headers collection for {url}", context=self.__class__.__name__)

        headers_result = {}

        try:
            parsed = urlparse(url)
            host = parsed.hostname

            if not host:
                Logger.debug("Invalid URL (no hostname)", context=self.__class__.__name__)
                return headers_result

            try:
                socket.getaddrinfo(host, None)
            except socket.gaierror:
                # Host not resolvable (not a critical error)
                Logger.debug("Host not resolvable", context=self.__class__.__name__)
                return headers_result

            try:
                r = requests.head(
                    url,
                    allow_redirects=True,
                    timeout=self.timeout,
                    headers={"User-Agent": C.USER_AGENT}
                )
            except requests.RequestException:
                # HTTP request failed (not a structural error)
                Logger.debug("HTTP request failed", context=self.__class__.__name__)
                return headers_result

            headers_result = {
                k.lower(): v
                for k, v in r.headers.items()
            }

        except Exception as e:
            Logger.error(f"HTTP headers collection error: {e}", context=self.__class__.__name__)
            raise CollectorError(f"HTTP headers collection error for {url}: {e}") from e

        Logger.info(f"Collected {len(headers_result)} headers", context=self.__class__.__name__)
        return headers_result