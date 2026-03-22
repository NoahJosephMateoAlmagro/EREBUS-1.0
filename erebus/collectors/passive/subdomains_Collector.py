import requests
from requests.exceptions import RequestException
from collectors.base import Collector
import shared.constants as C
from exceptions.exceptions import CollectorError
from shared.logger import Logger


class SubdomainCollector(Collector):
    """
      Collector that retrieves subdomains from crt.sh (Certificate Transparency logs).

      It extracts subdomains from certificate entries and normalizes them
      into a consistent format for further processing.
      """

    def __init__(self, timeout: int = 8, limit: int = 20):
        """
        Args:
            timeout (int): Request timeout
            limit (int): Max number of subdomains returned
        """
        self.timeout = timeout
        self.limit = limit

    def collect(self, target: str):

        """
        Queries crt.sh and extracts subdomains related to the target domain.

        Args:
            target (str): Target domain

        Returns:
            list[dict]: List of subdomains with value and source
        """
        Logger.info(f"Starting subdomain collection for {target}", context=self.__class__.__name__)

        results = []

        url = f"https://crt.sh/?q=%25.{target}&output=json"
        headers = {"User-Agent": "EREBUS/1.0"}

        Logger.debug(f"Requesting crt.sh URL: {url}", context=self.__class__.__name__)


        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)

        except RequestException as e:
            Logger.error(f"HTTP request failed: {e}", context=self.__class__.__name__)
            raise CollectorError(f"HTTP error querying crt.sh: {e}")

        # Validate response status
        if response.status_code != 200:
            Logger.error(f"Invalid response status: {response.status_code}", context=self.__class__.__name__)
            raise CollectorError( f"crt.sh returned status {response.status_code}")

        # Parse JSON response
        try:
            data = response.json()

        except ValueError as e:
            Logger.error("JSON parsing failed", context=self.__class__.__name__)
            raise CollectorError(f"Error parsing crt.sh JSON: {e}")

        subdomains = set()

        # Extract subdomains from certificate entries
        for entry in data:
            name_value = entry.get("name_value", "")

            # crt.sh may return multiple domains separated by newlines
            for domain in name_value.split("\n"):
                domain = domain.strip().lower()

                # Filter valid subdomains (exclude wildcards)
                if domain.endswith(target) and not domain.startswith("*."):
                    subdomains.add(domain)

        Logger.debug(f"Unique subdomains found: {len(subdomains)}", context=self.__class__.__name__)

        # Apply limit and build result structure
        for sub in sorted(subdomains):
            if len(results) >= self.limit:
                break

            results.append({
                "value": sub,
                "source": C.TECHNIQUE_SUBDOMAINS
            })

        Logger.info(f"Returning {len(results)} subdomains", context=self.__class__.__name__)

        return results