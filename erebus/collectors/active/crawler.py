from typing import Union, List
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from exceptions.exceptions import CollectorError
from shared.logger import Logger


class Crawler:
    """
    Crawler that navigates internal links starting from one or multiple URLs.
    """
    def __init__(
        self,
        start_url: Union[str, List[str]],
        max_pages: int = 30,
        timeout: int = 8,
        allowed_domain: str | None = None
    ):
        """
        Args:
            start_url (str | list): Initial URL(s)
            max_pages (int): Maximum number of pages to crawl
            timeout (int): HTTP request timeout
            allowed_domain (str | None): Optional domain restriction
        """
        self.max_pages = max_pages
        self.timeout = timeout
        self.allowed_domain = allowed_domain

        self.visited = set()
        self.queue = []

        if isinstance(start_url, list):
            self.queue.extend(start_url)
            first = start_url[0] if start_url else ""
        else:
            self.queue.append(start_url)
            first = start_url

        self.domain = urlparse(first).netloc if first else ""

    def _normalize(self, url: str) -> str:
        """
        Normalizes URLs by removing fragments and trailing slashes.
        """
        return url.split("#")[0].rstrip("/")

    def _is_internal(self, url: str) -> bool:
        """
        Checks whether a URL belongs to the allowed domain scope.
        """
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()

        if not netloc:
            return False

        if ":" in netloc:
            netloc = netloc.split(":")[0]

        if self.allowed_domain:
            return (
                netloc == self.allowed_domain
                or netloc.endswith("." + self.allowed_domain)
            )

        return netloc == self.domain

    def collect(self):
        """
        Executes crawling process.

        Returns:
            list[dict]: Crawled pages with HTML, links and scripts
        """

        Logger.info("Starting crawler", context=self.__class__.__name__)

        results = []

        try:
            while self.queue and len(self.visited) < self.max_pages:

                url = self._normalize(self.queue.pop(0))

                if url in self.visited:
                    continue

                Logger.debug(f"Crawling {url}", context=self.__class__.__name__)

                try:
                    response = requests.get(
                        url,
                        timeout=self.timeout,
                        headers={"User-Agent": "EREBUS/1.0"}
                    )
                except requests.RequestException:
                    # HTTP failure (skip URL)
                    Logger.debug(f"Request failed for {url}", context=self.__class__.__name__)
                    continue

                content_type = response.headers.get("Content-Type", "")

                if "text/html" not in content_type:
                    continue

                self.visited.add(url)

                soup = BeautifulSoup(response.text, "html.parser")

                links = set()
                for a in soup.find_all("a", href=True):
                    href = a["href"]

                    # Skip mailto links
                    if "@" in href:
                        continue

                    full_url = self._normalize(urljoin(url, href))

                    if self._is_internal(full_url):
                        links.add(full_url)

                        if full_url not in self.visited:
                            self.queue.append(full_url)

                scripts = set()
                for s in soup.find_all("script", src=True):
                    full = self._normalize(urljoin(url, s["src"]))
                    if self._is_internal(full):
                        scripts.add(full)

                results.append({
                    "url": url,
                    "html": response.text,
                    "links": list(links),
                    "scripts": list(scripts)
                })

        except Exception as e:
            Logger.error(f"Crawler internal error: {e}", context=self.__class__.__name__)
            raise CollectorError(f"Crawler internal error: {e}")

        Logger.info(f"Crawled {len(results)} pages", context=self.__class__.__name__)

        return results