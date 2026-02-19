from collectors.base import PassiveCollector
import requests


class EmailCollector(PassiveCollector):

    def __init__(self, timeout: int = 8):
        self.timeout = timeout

    def collect(self, target: str):

        results = []

        urls = [
            f"https://{target}",
            f"https://www.{target}",
            f"http://{target}",
            f"http://www.{target}",
        ]

        for url in urls:
            try:
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    headers={"User-Agent": "EREBUS/1.0"}
                )

                if response.status_code != 200:
                    continue

                if "text/html" not in response.headers.get("Content-Type", ""):
                    continue

                results.append({
                    "url": url,
                    "html": response.text
                })

            except requests.exceptions.RequestException:
                continue

        return results
