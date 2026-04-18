from collectors.base import Collector
import dns.resolver
import shared.constants as C
from exceptions.exceptions import CollectorError
from shared.logger import Logger


class DNS_TXT_Collector(Collector):
    """
     Collector that retrieves TXT DNS records for a target domain.
     """

    def __init__(self, timeout: int):
        """
        Args:
            timeout (int): DNS resolution timeout
        """
        self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.lifetime = timeout
        self.resolver.timeout = timeout
        self.resolver.nameservers = C.RESOLVER_NAMESERVERS

    def collect(self, domain: str) -> list[dict]:

        """
        Resolves TXT records for the given domain.

        Args:
            domain (str): Target domain

        Returns:
            list[dict]: List of TXT records
        """

        Logger.info(f"Starting TXT DNS resolution for {domain}", context=self.__class__.__name__)

        results = []
        domain = domain.rstrip(".").lower()

        try:
            Logger.debug("Resolving TXT records", context=self.__class__.__name__)

            answers = self.resolver.resolve(domain, "TXT", tcp=True)

            for rdata in answers:

                # TXT records may be split into multiple parts. Join them
                value = "".join(
                    part.decode() if isinstance(part, bytes) else part
                    for part in rdata.strings
                )

                results.append({
                    "domain": domain,
                    "record": value,
                    "type": "TXT",
                    "source": C.TECHNIQUE_DNS_TXT
                })

        except (
            dns.resolver.NoAnswer,
            dns.resolver.NXDOMAIN,
            dns.resolver.Timeout,
            dns.resolver.NoNameservers
        ):
            # Not a critical error, simply no TXT records available
            return results

        except Exception as e:
            Logger.error(f"TXT resolution error: {e}", context=self.__class__.__name__)
            raise CollectorError(f"TXT resolution error for {domain}: {e}") from e

        Logger.info(f"Resolved {len(results)} TXT records", context=self.__class__.__name__)
        return results