from collectors.base import Collector
import requests

from exceptions.exceptions import CollectorError
from shared.logger import Logger


class RobotsCollector(Collector):
    """
    Collector that retrieves and parses robots.txt for a target domain.
    """

    def __init__(self, timeout: int = 8):
        """
        Args:
            timeout (int): HTTP request timeout
        """
        self.timeout = timeout

    def collect(self, domain: str):
        """
        Fetches and parses robots.txt.

        Args:
            domain (str): Target domain

        Returns:
            dict: Parsed robots data (paths and sitemaps)
        """

        Logger.info(f"Starting robots.txt collection for {domain}", context=self.__class__.__name__)

        results = {
            "paths": [],
            "sitemaps": []
        }

        urls_to_try = [
            f"https://{domain}/robots.txt",
            f"http://{domain}/robots.txt"
        ]

        content = None

        try:
            # Try HTTPS first, then HTTP fallback
            for url in urls_to_try:
                try:
                    r = requests.get(
                        url,
                        timeout=self.timeout,
                        headers={"User-Agent": "EREBUS/1.0"}
                    )

                    if r.status_code == 200 and r.text:
                        content = r.text
                        break

                except requests.RequestException:
                    Logger.debug(f"Request failed for {url}", context=self.__class__.__name__)
                    continue

            # No robots.txt found
            if not content:
                Logger.debug("No robots.txt found", context=self.__class__.__name__)
                return results

            seen_paths = set()
            seen_sitemaps = set()

            # Parse robots.txt line by line
            for raw_line in content.splitlines():
                line = raw_line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Remove inline comments
                if "#" in line:
                    line = line.split("#", 1)[0].strip()

                lower = line.lower()

                if lower.startswith("disallow:"):
                    path = line.split(":", 1)[1].strip()

                    # Only keep valid paths
                    if not path or not path.startswith("/"):
                        continue

                    if path not in seen_paths:
                        seen_paths.add(path)
                        results["paths"].append(path)

                elif lower.startswith("sitemap:"):
                    sitemap = line.split(":", 1)[1].strip()

                    if not sitemap:
                        continue

                    if sitemap not in seen_sitemaps:
                        seen_sitemaps.add(sitemap)
                        results["sitemaps"].append(sitemap)

        except Exception as e:
            Logger.error(f"Robots parsing error: {e}", context=self.__class__.__name__)
            raise CollectorError(f"Robots parsing error for {domain}: {e}")

        Logger.info(
            f"Robots parsed (paths: {len(results['paths'])}, sitemaps: {len(results['sitemaps'])})",
            context=self.__class__.__name__
        )
        return results