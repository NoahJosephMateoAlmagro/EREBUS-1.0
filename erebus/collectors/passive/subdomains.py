import requests
from .base import PassiveCollector
import core.constants as C

class SubdomainCollector(PassiveCollector):

    def __init__(self, timeout : int = 8):
        self.timeout = timeout

    def collect(self, target: str):
        results = []

        try:
            url = f"https://crt.sh/?q=%25.{target}&output=json"
            headers = {"User-Agent": "EREBUS/1.0"}
            response = requests.get(url, headers=headers, timeout=self.timeout)

            if response.status_code != 200:
                return results

            data = response.json()

            subdomains = set()

            for entry in data:
                name_value = entry.get("name_value", "")
                for domain in name_value.split("\n"):
                    domain = domain.strip().lower()
                    if domain.endswith(target) and not domain.startswith("*."):
                        subdomains.add(domain)

            for sub in sorted(subdomains):
                results.append({
                    "value": sub,
                    "source": C.TECHNIQUE_SUBDOMAINS
                })



        except requests.RequestException as e:

            print("Error HTTP obteniendo subdominios:", e)

        except ValueError as e:

            print("Error parseando JSON de crt.sh:", e)

        return results
