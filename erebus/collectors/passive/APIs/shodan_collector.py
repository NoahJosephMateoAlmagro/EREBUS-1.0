import requests
from collectors.base import Collector
from exceptions.exceptions import CollectorError


class ShodanCollector(Collector):

    BASE_URL = "https://api.shodan.io"

    def __init__(self, timeout=10):
        self.timeout = timeout
        self.api_key = None

    def set_api_key(self, api_key):
        self.api_key = api_key

    def collect(self, domain):

        if not self.api_key:
            raise CollectorError("Shodan API key not configured")

        results = {
            "subdomains": set(),
            "ips": set(),
            "hosts": []
        }

        try:

            # --------------------------
            # DNS DOMAIN
            # --------------------------

            dns_url = f"{self.BASE_URL}/dns/domain/{domain}"

            r = requests.get(
                dns_url,
                params={"key": self.api_key},
                timeout=self.timeout
            )

            if r.status_code == 200:

                data = r.json()

                for sub in data.get("subdomains", []):
                    results["subdomains"].add(f"{sub}.{domain}")

            # --------------------------
            # HOST SEARCH
            # --------------------------

            search_url = f"{self.BASE_URL}/shodan/host/search"

            r = requests.get(
                search_url,
                params={
                    "key": self.api_key,
                    "query": f"hostname:{domain}"
                },
                timeout=self.timeout
            )

            if r.status_code == 200:

                data = r.json()

                for match in data.get("matches", []):

                    ip = match.get("ip_str")

                    if ip:
                        results["ips"].add(ip)

                    results["hosts"].append({
                        "ip": ip,
                        "port": match.get("port"),
                        "transport": match.get("transport"),
                        "product": match.get("product"),
                        "version": match.get("version"),
                        "org": match.get("org"),
                        "isp": match.get("isp"),
                        "hostnames": match.get("hostnames", []),
                        "domains": match.get("domains", [])
                    })

            return results

        except requests.RequestException as e:
            raise CollectorError(f"Shodan collector error: {e}")


    def get_host(self, ip):

        url = f"{self.BASE_URL}/shodan/host/{ip}"

        try:

            r = requests.get(
                url,
                params={"key": self.api_key},
                timeout=self.timeout
            )

            if r.status_code != 200:
                return None

            data = r.json()

            services = []

            for item in data.get("data", []):

                services.append({
                    "port": item.get("port"),
                    "transport": item.get("transport"),
                    "product": item.get("product"),
                    "version": item.get("version"),
                    "org": item.get("org"),
                    "isp": item.get("isp"),
                    "asn": data.get("asn"),
                    "hostnames": data.get("hostnames", [])
                })

            return {
                "ip": ip,
                "services": services
            }

        except requests.RequestException:
            return None