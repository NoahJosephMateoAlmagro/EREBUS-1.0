import re
import requests
from collectors.base import PassiveCollector
from processing.normalizers.email_normalizer import normalize_obfuscated

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

                if "text/html" not in response.headers.get("Content-Type", ""):
                    continue

                matches = normalize_obfuscated(response.text)

                for email in matches:
                    results.append({
                        "value": email,
                        "context": url
                    })


            except requests.exceptions.RequestException:
                pass

        return results



