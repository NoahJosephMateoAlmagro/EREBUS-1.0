from collectors.base import Collector
import requests

from exceptions.exceptions import CollectorError


class RobotsCollector(Collector):

    def __init__(self, timeout: int = 8):
        self.timeout = timeout

    def collect(self, domain: str):

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
                    continue

            if not content:
                return results

            seen_paths = set()
            seen_sitemaps = set()

            for raw_line in content.splitlines():
                line = raw_line.strip()

                if not line or line.startswith("#"):
                    continue

                if "#" in line:
                    line = line.split("#", 1)[0].strip()

                lower = line.lower()

                if lower.startswith("disallow:"):
                    path = line.split(":", 1)[1].strip()

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
            raise CollectorError(f"Robots parsing error for {domain}: {e}")

        return results