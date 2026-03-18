from collectors.base import Collector
import whois
from exceptions.exceptions import CollectorError
from shared.logger import Logger


class WhoisCollector(Collector):

    """
    Collector that performs a WHOIS lookup for a given target domain.

    Extracts key metadata such as registrar, dates, name servers,
    status and associated emails.
    """

    def collect(self, target: str):

        """
        Executes WHOIS lookup and normalizes relevant fields.
        Args:
            target (str): Target domain
        Returns:
            dict: Structured WHOIS data
        """

        Logger.info(f"Starting WHOIS lookup for {target}", context=self.__class__.__name__)

        try:
            # Perform WHOIS query

            whois_data = whois.whois(target)

            # Basic validation. Ensure domain_name exists

            if not whois_data or not getattr(whois_data, "domain_name", None):
                Logger.error(f"WHOIS lookup returned empty result", context=self.__class__.__name__)
                raise CollectorError(f"WHOIS lookup failed for {target}")

            # Normalize single/multiple values

            def _first(value):
                """
                Returns first element if value is a list, otherwise returns value.
                """

                if isinstance(value, list):
                    return value[0]
                return value

            def _as_list(value):
                """
                Ensures the value is always returned as a list.
                """

                if not value:
                    return []
                return value if isinstance(value, list) else [value]

            # Build normalized output
            result = {
                "registrar": _first(whois_data.registrar),
                "creation_date": _first(whois_data.creation_date),
                "expiration_date": _first(whois_data.expiration_date),
                "updated_date": _first(whois_data.updated_date),
                "name_servers": _as_list(whois_data.name_servers),
                "status": _as_list(whois_data.status),
                "emails": _as_list(whois_data.emails),
            }
            Logger.info(f"WHOIS lookup completed", context=self.__class__.__name__)

            return result

        except Exception as e:
            # Wrap any exception into domain-specific error
            Logger.error(f"WHOIS error: {e}", context=self.__class__.__name__)
            raise CollectorError(f"WHOIS error for {target}: {e}")