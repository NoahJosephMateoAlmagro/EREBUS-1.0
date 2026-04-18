from collectors.base import Collector
import dns.resolver
import shared.constants as C
from exceptions.exceptions import CollectorError
from shared.logger import Logger


class DNS_CNAME_Collector(Collector):
    """
    Collector that retrieves CNAME records for a target domain.
    """

    def __init__(self, timeout: int):
        """
        Args:
            timeout (int): DNS resolution timeout
        """
        self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.nameservers = C.RESOLVER_NAMESERVERS
        self.resolver.timeout = timeout
        self.resolver.lifetime = timeout

    def collect(self, domain: str) -> list[dict]:
        """
        Resolves CNAME records for the given domain.

        Args:
            domain (str): Target domain

        Returns:
            list[dict]: List of CNAME records
        """

        Logger.info(f"Starting CNAME DNS resolution for {domain}", context=self.__class__.__name__)

        results = []
        domain = domain.rstrip(".").lower()

        try:

            Logger.debug("Resolving CNAME records", context=self.__class__.__name__)

            answers = self.resolver.resolve(domain, "CNAME", tcp=True)

            for data in answers:
                cname = str(data.target).rstrip(".").lower()

                results.append({
                    "domain": domain,
                    "record": cname,
                    "type": "CNAME",
                    "source": C.TECHNIQUE_DNS_CNAME
                })

        except (
            dns.resolver.NoAnswer,
            dns.resolver.NXDOMAIN,
            dns.resolver.Timeout,
            dns.resolver.NoNameservers
        ):
            # Not a critical error, simply no CNAME records available
            Logger.debug("No CNAME records found or DNS issue", context=self.__class__.__name__)
            return results

        except Exception as e:
            Logger.error(f"CNAME resolution error: {e}", context=self.__class__.__name__)
            raise CollectorError(f"CNAME resolution error for {domain}: {e}") from e

        Logger.info(f"Resolved {len(results)} CNAME records", context=self.__class__.__name__)
        return results