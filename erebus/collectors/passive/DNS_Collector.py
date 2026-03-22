import dns.resolver
from collectors.base import Collector
import shared.constants as C
from exceptions.exceptions import CollectorError
from shared.logger import Logger


class DNSCollector(Collector):

    """
       Collector that resolves DNS records (A and AAAA) for a target domain.

       Uses a custom resolver with predefined nameservers.
       """

    def __init__(self, timeout: int = 8):

        """
         Args:
         timeout (int): DNS resolution timeout
         """

        self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.lifetime = timeout
        self.resolver.timeout = timeout
        self.resolver.nameservers = ["8.8.8.8", "1.1.1.1"]

    def collect(self, target: str):

        """
       Resolves A and AAAA records for the target domain.

       Args:
           target (str): Target domain

       Returns:
           list[dict]: List of resolved IP addresses

       """

        Logger.info(f"Starting DNS resolution for {target}", context=self.__class__.__name__)

        results = []
        attempted = 0
        network_failures = 0

        for record_type in ["A", "AAAA"]:
            attempted += 1

            Logger.debug(f"Resolving {record_type} records", context=self.__class__.__name__)

            try:
                answers = self.resolver.resolve(target, record_type)

                for dato in sorted(answers, key=lambda r: r.to_text()):
                    results.append({
                        "domain": target,
                        "ip": dato.to_text(),
                        "record_type": record_type,
                        "source": C.TECHNIQUE_DNS
                    })

            except dns.resolver.NXDOMAIN:
                # Domain does not exist (not a technical error)
                Logger.debug(f"{record_type}: NXDOMAIN", context=self.__class__.__name__)
                continue

            except dns.resolver.NoAnswer:
                # No records of this type (expected behavior)
                Logger.debug(f"{record_type}: NoAnswer", context=self.__class__.__name__)
                continue

            except dns.resolver.Timeout:
                #Network issue (just track failures)
                Logger.debug(f"{record_type}: Timeout", context=self.__class__.__name__)
                network_failures += 1
                continue

            except Exception as e:
                Logger.error(f"Unexpected DNS error: {e}", context=self.__class__.__name__)
                raise CollectorError(f"Unexpected DNS resolution error: {e}")

        # If all attempts failed due to timeouts, we treat it as technical failure
        if network_failures == attempted and attempted > 0:
            raise CollectorError(f"DNS resolution timeout for{target}")

        Logger.info(f"Resolved {len(results)} DNS records", context=self.__class__.__name__)

        return results