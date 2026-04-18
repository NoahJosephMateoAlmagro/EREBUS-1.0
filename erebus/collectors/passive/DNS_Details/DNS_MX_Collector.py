from collectors.base import Collector
import dns.resolver
import shared.constants as C
from exceptions.exceptions import CollectorError
from shared.logger import Logger


class DNS_MX_Collector(Collector):
    """
    Collector that retrieves MX (Mail Exchange) records for a target domain.
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
        Resolves MX records for the given domain.

        Args:
            domain (str): Target domain

        Returns:
            list[dict]: List of MX records
        """

        Logger.info(f"Starting MX DNS resolution for {domain}", context=self.__class__.__name__)

        results = []
        domain = domain.rstrip(".").lower()

        try:

            Logger.debug("Resolving MX records", context=self.__class__.__name__)

            answers = self.resolver.resolve(domain, "MX", tcp=True)

            for rdata in answers:
                results.append({
                    "domain": domain,
                    "record": str(rdata.exchange).rstrip(".").lower(),
                    "priority": rdata.preference,
                    "source": C.TECHNIQUE_DNS_MX
                })

        except (
            dns.resolver.NoAnswer,
            dns.resolver.NXDOMAIN,
            dns.resolver.Timeout,
            dns.resolver.NoNameservers
        ):
            # Not a critical error, simply no MX records available
            Logger.debug("No MX records found or DNS issue", context=self.__class__.__name__)
            return results

        except Exception as e:
            Logger.error(f"MX resolution error: {e}", context=self.__class__.__name__)
            raise CollectorError(f"MX resolution error for {domain}: {e}") from e

        return results