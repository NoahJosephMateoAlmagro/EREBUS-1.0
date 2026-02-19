import requests
import xml.etree.ElementTree as ET
from collectors.base import PassiveCollector


class SitemapCollector(PassiveCollector):

    def __init__(self, timeout=8, max_urls=200):
        self.timeout = timeout
        self.max_urls = max_urls

    def collect(self, sitemap_url: str):

        urls = []

        try:
            r = requests.get(
                sitemap_url,
                timeout=self.timeout,
                headers={"User-Agent": "EREBUS/1.0"}
            )

            if r.status_code != 200:
                print(f"[SITEMAP] Status {r.status_code} en {sitemap_url}")
                return urls

            root = ET.fromstring(r.text)

            for loc in root.findall(".//{*}loc"):

                if len(urls) >= self.max_urls:
                    break

                text = (loc.text or "").strip()
                if text:
                    urls.append(text)

            print(f"[SITEMAP] {sitemap_url} -> {len(urls)} URLs extraídas")

        except Exception as e:
            print(f"[SITEMAP ERROR] {sitemap_url} -> {e}")

        return urls
