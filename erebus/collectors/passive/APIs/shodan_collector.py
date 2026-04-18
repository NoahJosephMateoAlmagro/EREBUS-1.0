import requests

from collectors.base import Collector
from exceptions.exceptions import CollectorError
from shared.logger import Logger


class ShodanCollector(Collector):
    """
    Collector that retrieves information from Shodan API.

    It gathers subdomains, IPs and host service data related to a target domain.
    """

    BASE_URL = "https://api.shodan.io"

    def __init__(self, timeout: int = 10):
        """
        Args:
            timeout (int): HTTP request timeout
        """
        self.timeout = timeout
        self.api_key = None

    def set_api_key(self, api_key: str):
        """
        Sets the Shodan API key.

        Args:
            api_key (str): Shodan API key
        """
        self.api_key = api_key

    def collect(self, domain: str):
        """
        Queries Shodan API to retrieve subdomains, IPs and host data.

        Args:
            domain (str): Target domain

        Returns:
            dict: Collected Shodan data
        """
        Logger.info(f"Starting Shodan collection for {domain}", context=self.__class__.__name__)

        if not self.api_key:
            Logger.error("Shodan API key not configured", context=self.__class__.__name__)
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
            Logger.debug("Querying Shodan DNS endpoint", context=self.__class__.__name__)

            dns_url = f"{self.BASE_URL}/dns/domain/{domain}"

            r = requests.get(
                dns_url,
                params={"key": self.api_key},
                timeout=self.timeout,
                headers={"User-Agent": C.USER_AGENT}
            )

            if r.status_code == 200:
                data = r.json()

                for sub in data.get("subdomains", []):
                    results["subdomains"].add(f"{sub}.{domain}")
            else:
                Logger.error(f"Shodan DNS request failed: {r.status_code}", context=self.__class__.__name__)

            # --------------------------
            # HOST SEARCH
            # --------------------------
            Logger.debug("Querying Shodan host search endpoint", context=self.__class__.__name__)

            search_url = f"{self.BASE_URL}/shodan/host/search"

            r = requests.get(
                search_url,
                params={
                    "key": self.api_key,
                    "query": f"hostname:{domain}",
                },
                headers={"User-Agent": C.USER_AGENT},
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
            else:
                Logger.error(f"Shodan host search failed: {r.status_code}", context=self.__class__.__name__)

            # Convert sets to lists for consistency and serialization
            results["subdomains"] = list(results["subdomains"])
            results["ips"] = list(results["ips"])

            Logger.info(
                f"Shodan results: {len(results['subdomains'])} subdomains, "
                f"{len(results['ips'])} IPs, {len(results['hosts'])} hosts",
                context=self.__class__.__name__
            )

            return results

        except requests.RequestException as e:
            Logger.error(f"Shodan request error: {e}", context=self.__class__.__name__)
            raise CollectorError(f"Shodan collector error: {e}")

    def get_host(self, ip: str):
        """
        Retrieves detailed host information for a specific IP.

        Args:
            ip (str): Target IP

        Returns:
            dict | None: Host data or None if not available
        """
        Logger.debug(f"Querying Shodan host for {ip}", context=self.__class__.__name__)

        url = f"{self.BASE_URL}/shodan/host/{ip}"

        try:
            r = requests.get(
                url,
                params={"key": self.api_key},
                timeout=self.timeout,
                headers={"User-Agent": C.USER_AGENT}
            )

            if r.status_code != 200:
                Logger.error(f"Shodan host request failed: {r.status_code}", context=self.__class__.__name__)
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

        except requests.RequestException as e:

            Logger.error(f"Shodan request error: {e}", context=self.__class__.__name__)
            raise CollectorError(f"Shodan collector error: {e}") from e