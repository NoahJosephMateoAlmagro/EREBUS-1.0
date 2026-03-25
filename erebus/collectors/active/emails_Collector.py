from collectors.base import Collector
import requests
from requests.exceptions import RequestException

from exceptions.exceptions import CollectorError
from shared.logger import Logger

class EmailCollector(Collector):
    """
    Collector that retrieves HTML content from common domain variants
    to later extract emails.
    """

    def __init__(self, timeout: int = 8):
        """
        Args:
            timeout (int): HTTP request timeout
        """
        self.timeout = timeout

    def collect(self, target: str):
        """
        Fetches HTML pages from multiple domain variants.

        Args:
            target (str): Target domain

        Returns:
            list[dict]: List of HTML contents with their source URL
        """

        Logger.info(f"Starting email collection for {target}", context=self.__class__.__name__)

        results = []
        attempted = 0
        network_failures = 0

        urls = [
            f"https://{target}",
            f"https://www.{target}",
            f"http://{target}",
            f"http://www.{target}",
        ]

        for url in urls:
            attempted += 1

            try:
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    headers={"User-Agent": "EREBUS/1.0"}
                )

                # Skip non-success responses
                if response.status_code != 200:
                    continue

                # Only process HTML content
                if "text/html" not in response.headers.get("Content-Type", ""):
                    continue

                results.append({
                    "url": url,
                    "html": response.text
                })

            except RequestException:
                # Network failure (track but do not break execution)
                network_failures += 1
                continue

        # If all URLs failed due to network issues (treat as real error)
        if network_failures == attempted:
            Logger.error(f"All requests failed for {target}", context=self.__class__.__name__)
            raise CollectorError(f"Unable to access domain {target} in any variant")

        Logger.info(f"Collected {len(results)} HTML pages", context=self.__class__.__name__)

        return results