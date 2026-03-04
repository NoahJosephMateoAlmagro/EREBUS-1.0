from collectors.base import PassiveCollector
import requests
import xml.etree.ElementTree as ET

from exceptions.exceptions import CollectorError


class SitemapCollector(PassiveCollector):

    def __init__(self, timeout: int = 8, max_urls: int = 200):
        self.timeout = timeout
        self.max_urls = max_urls

    def collect(self, sitemap_url: str):

        urls = []

        try:
            try:
                r = requests.get(
                    sitemap_url,
                    timeout=self.timeout,
                    headers={"User-Agent": "EREBUS/1.0"}
                )
            except requests.RequestException:
                # Fallo HTTP → no es error estructural
                return urls

            if r.status_code != 200 or not r.text:
                return urls

            try:
                root = ET.fromstring(r.text)
            except ET.ParseError as e:
                raise CollectorError(f"Sitemap XML parse error for {sitemap_url}: {e}")

            for loc in root.findall(".//{*}loc"):

                if len(urls) >= self.max_urls:
                    break

                text = (loc.text or "").strip()
                if text:
                    urls.append(text)

        except CollectorError:
            raise

        except Exception as e:
            raise CollectorError(f"Sitemap collector error for {sitemap_url}: {e}")

        return urls