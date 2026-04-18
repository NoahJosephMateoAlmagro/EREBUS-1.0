from collectors.base import Collector
import whois
from exceptions.exceptions import CollectorError
from shared.logger import Logger
import shared.utils as Utils


class WhoisCollector(Collector):

    """
    Collector that performs a WHOIS lookup for a given target domain.

    Extracts key metadata such as registrar, dates, name servers,
    status and associated emails.
    """

    def collect(self, target: str) -> dict:

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

            # Build normalized output
            result = {
                "registrar": Utils.first_or_value(whois_data.registrar),
                "creation_date": Utils.first_or_value(whois_data.creation_date),
                "expiration_date": Utils.first_or_value(whois_data.expiration_date),
                "updated_date": Utils.first_or_value(whois_data.updated_date),
                "name_servers": Utils.ensure_list(whois_data.name_servers),
                "status": Utils.ensure_list(whois_data.status),
                "emails": Utils.ensure_list(whois_data.emails),
            }
            Logger.info(f"WHOIS lookup completed", context=self.__class__.__name__)

            return result

        except CollectorError:
            raise

        except Exception as e:
            # Wrap any exception into domain-specific error
            Logger.error(f"WHOIS error: {e}", context=self.__class__.__name__)
            raise CollectorError(f"WHOIS error for {target}: {e}") from e