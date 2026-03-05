import requests
from requests.exceptions import RequestException
from collectors.base import Collector
import shared.constants as C
from exceptions.exceptions import CollectorError


class SubdomainCollector(Collector):

    def __init__(self, timeout: int = 8, limit: int = 20):
        self.timeout = timeout
        self.limit = limit

    def collect(self, target: str):

        results = []

        url = f"https://crt.sh/?q=%25.{target}&output=json"
        headers = {"User-Agent": "EREBUS/1.0"}

        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)

        except RequestException as e:
            raise CollectorError(f"Error HTTP consultando crt.sh: {e}")

        if response.status_code != 200:
            raise CollectorError(
                f"crt.sh respondió con status {response.status_code}"
            )

        try:
            data = response.json()

        except ValueError as e:
            raise CollectorError(f"Error parseando JSON de crt.sh: {e}")

        subdomains = set()

        for entry in data:
            name_value = entry.get("name_value", "")
            for domain in name_value.split("\n"):
                domain = domain.strip().lower()

                if domain.endswith(target) and not domain.startswith("*."):
                    subdomains.add(domain)

        for sub in sorted(subdomains):
            if len(results) >= self.limit:
                break

            results.append({
                "value": sub,
                "source": C.TECHNIQUE_SUBDOMAINS
            })

        return results