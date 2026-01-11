import re
import requests
from collectors.passive.base import PassiveCollector
import core.constants as C


class EmailCollector(PassiveCollector):
    EMAIL_REGEX = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    )

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

                matches = self.EMAIL_REGEX.findall(response.text)


                for email in matches:
                    results.append({
                        "value": email,
                        "source": C.TECHNIQUE_PASSIVE_HTML,
                        "context": url
                    })


            except requests.exceptions.RequestException:
                pass

        return results



