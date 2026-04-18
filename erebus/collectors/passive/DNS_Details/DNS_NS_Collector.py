from collectors.base import Collector
import dns.resolver
import shared.constants as C
from exceptions.exceptions import CollectorError
from shared.logger import Logger


class DNS_NS_Collector(Collector):
    """
    Collector that retrieves NS (Name Server) records for a target domain.
    """


    def __init__(self, timeout: int = 8):
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
        Resolves NS records for the given domain.

        Args:
            domain (str): Target domain

        Returns:
             list[dict]: List of NS records
        """

        Logger.info(f"Starting NS DNS resolution for {domain}", context=self.__class__.__name__)

        results = []
        domain = domain.rstrip(".").lower()

        try:
            Logger.debug("Resolving NS records", context=self.__class__.__name__)

            answers = self.resolver.resolve(domain, "NS")

            for data in answers:
                ns_record = str(data.target).rstrip(".").lower()

                results.append({
                    "domain": domain,
                    "record": ns_record,
                    "type": "NS",
                    "source": C.TECHNIQUE_DNS_NS
                })

        except (
            dns.resolver.NoAnswer,
            dns.resolver.NXDOMAIN,
            dns.resolver.Timeout,
            dns.resolver.NoNameservers
        ):
            # Not a critical error, simply no NS records available
            return results

        except Exception as e:
            Logger.error(f"NS resolution error: {e}", context=self.__class__.__name__)
            raise CollectorError(f"NS resolution error for {domain}: {e}") from e

        Logger.info(f"Resolved {len(results)} NS records", context=self.__class__.__name__)
        return results