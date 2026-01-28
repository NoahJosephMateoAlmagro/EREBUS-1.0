import requests
from collectors.passive.base import PassiveCollector
import core.constants as C

class RobotsCollector(PassiveCollector):

    def __init__(self, timeout=8):
        self.timeout = timeout

    def collect(self, domain: str):
        results = {
            "paths": [],
            "sitemaps": []
        }

        url = f"https://{domain}/robots.txt"

        try:
            r = requests.get(url, timeout=self.timeout)
            if r.status_code != 200:
                return results

            for line in r.text.splitlines():
                line = line.strip()

                if line.lower().startswith("disallow:"):
                    path = line.split(":", 1)[1].strip()
                    if path:
                        results["paths"].append(path)

                elif line.lower().startswith("sitemap:"):
                    sitemap = line.split(":", 1)[1].strip()
                    if sitemap:
                        results["sitemaps"].append(sitemap)

        except requests.RequestException:
            pass

        return results
