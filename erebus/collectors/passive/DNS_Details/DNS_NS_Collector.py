from collectors.base import PassiveCollector
import dns.resolver
import shared.constants as C
from exceptions.exceptions import CollectorError


class DNS_NS_Collector(PassiveCollector):

    def __init__(self, timeout: int = 8):
        self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.lifetime = timeout
        self.resolver.timeout = timeout
        self.resolver.nameservers = ["8.8.8.8", "1.1.1.1"]

    def collect(self, domain: str):

        results = []
        domain = domain.rstrip(".").lower()

        try:
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
            # No es error técnico grave → simplemente no hay registros NS
            return results

        except Exception as e:
            # Error inesperado → fallo real del collector
            raise CollectorError(f"NS resolution error for {domain}: {e}")

        return results