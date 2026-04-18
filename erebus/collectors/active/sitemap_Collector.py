from collectors.base import Collector
import requests
import xml.etree.ElementTree as ET

from exceptions.exceptions import CollectorError, ParserError
from shared.logger import Logger
import shared.constants as C

class SitemapCollector(Collector):

    """
    Collector that retrieves URLs from a sitemap XML file.

    """

    def __init__(self, timeout: int, max_urls: int):
        """
        Args:
            timeout (int): HTTP request timeout
            max_urls (int): Maximum number of URLs to extract
        """
        self.timeout = timeout
        self.max_urls = max_urls

    def collect(self, sitemap_url: str)-> list[str]:
        """
        Fetches and parses a sitemap XML file.

        Args:
            sitemap_url (str): Sitemap URL

        Returns:
            list[str]: Extracted URLs from sitemap
        """

        Logger.info(f"Starting sitemap collection for {sitemap_url}", context=self.__class__.__name__)

        urls = []

        try:
            try:
                # Request sitemap content
                r = requests.get(
                    sitemap_url,
                    timeout=self.timeout,
                    headers={"User-Agent": C.USER_AGENT}
                )
            except requests.RequestException:
                # HTTP request failed (not a structural error)
                Logger.debug("Sitemap request failed", context=self.__class__.__name__)
                return urls

            # Validate response
            if r.status_code != 200 or not r.text:
                Logger.debug("Invalid sitemap response", context=self.__class__.__name__)
                return urls

            # Parse XML content
            try:
                root = ET.fromstring(r.text)

            except ET.ParseError as e:
                Logger.error("Sitemap XML parsing failed", context=self.__class__.__name__)
                raise ParserError(f"Sitemap XML parse error for {sitemap_url}: {e}") from e

            # Extract <loc> elements
            for loc in root.findall(".//{*}loc"):

                if len(urls) >= self.max_urls:
                    break

                text = (loc.text or "").strip()
                if text:
                    urls.append(text)

        except CollectorError:
            raise

        except Exception as e:
            Logger.error(f"Sitemap collector error: {e}", context=self.__class__.__name__)
            raise CollectorError(f"Sitemap collector error for {sitemap_url}: {e}") from e

        Logger.info(f"Collected {len(urls)} sitemap URLs", context=self.__class__.__name__)
        return urls