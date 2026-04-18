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

    def __init__(self, timeout: int, limit: int, max_attempts: int):
        """
        Args:
            timeout (int): Request timeout
            limit (int): Max number of subdomains returned
            max_attempts (int): Max number of HTTP attempts to crt.sh
        """
        self.timeout = timeout
        self.limit = limit
        self.max_attempts = max_attempts

    def collect(self, target: str) -> list[dict]:

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
        headers = {"User-Agent": C.USER_AGENT}

        Logger.debug(f"Requesting crt.sh URL: {url}", context=self.__class__.__name__)

        response = None
        last_error = None

        # Retry the crt.sh request because it often fails temporarily
        for attempt in range(1, self.max_attempts + 1):
            try:
                Logger.debug(
                    f"crt.sh request attempt {attempt}/{self.max_attempts}",
                    context=self.__class__.__name__
                )

                candidate_response = requests.get(
                    url,
                    headers=headers,
                    timeout=self.timeout
                )

                # Accept only successful non-empty responses
                if candidate_response.status_code == 200 and candidate_response.text:
                    response = candidate_response
                    break

                last_error = f"crt.sh returned status {candidate_response.status_code}"

                Logger.error(
                    f"Invalid response status on attempt {attempt}/{self.max_attempts}: "
                    f"{candidate_response.status_code}",
                    context=self.__class__.__name__
                )

            except RequestException as e:
                # Save the last transport error and keep retrying
                last_error = e

                Logger.error(
                    f"HTTP request failed on attempt {attempt}/{self.max_attempts}: {e}",
                    context=self.__class__.__name__
                )

        if response is None:
            raise CollectorError(f"HTTP error querying crt.sh after {self.max_attempts} attempts: {last_error}")

        # Parse JSON response
        try:
            data = response.json()

        except ValueError as e:

            Logger.error("JSON parsing failed", context=self.__class__.__name__)
            raise CollectorError(f"Error parsing crt.sh JSON: {e}") from e

        subdomains = set()

        # Extract subdomains from certificate entries
        for entry in data:
            name_value = entry.get("name_value", "")

            # crt.sh may return multiple domains separated by newlines
            for domain in name_value.split("\n"):
                domain = domain.strip().lower()

                # Filter valid subdomains (exclude wildcards)
                if domain.endswith(target.lower()) and not domain.startswith("*."):
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