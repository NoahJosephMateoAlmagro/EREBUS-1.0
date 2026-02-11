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
            r = requests.get(sitemap_url, timeout=self.timeout)
            if r.status_code != 200:
                return urls

            root = ET.fromstring(r.text)

            for loc in root.findall(".//{*}loc"):
                if len(urls) >= self.max_urls:
                    break
                urls.append(loc.text.strip())

        except Exception:
            pass

        return urls
