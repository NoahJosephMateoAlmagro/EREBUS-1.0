from collectors.base import PassiveCollector
import requests
from requests.exceptions import RequestException

from exceptions.exceptions import CollectorError


class EmailCollector(PassiveCollector):

    def __init__(self, timeout: int = 8):
        self.timeout = timeout

    def collect(self, target: str):

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

                if response.status_code != 200:
                    continue

                if "text/html" not in response.headers.get("Content-Type", ""):
                    continue

                results.append({
                    "url": url,
                    "html": response.text
                })

            except RequestException:
                network_failures += 1
                continue

        # Si todas las URLs fallaron por red → error real
        if network_failures == attempted:
            raise CollectorError(
                f"No se pudo acceder al dominio {target} en ninguna variante"
            )

        return results