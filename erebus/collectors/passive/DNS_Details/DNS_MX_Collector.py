from collectors.base import Collector
import dns.resolver
import shared.constants as C
from exceptions.exceptions import CollectorError


class DNS_MX_Collector(Collector):

    def __init__(self, timeout: int = 8):
        self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.lifetime = timeout
        self.resolver.timeout = timeout
        self.resolver.nameservers = ["8.8.8.8", "1.1.1.1"]

    def collect(self, domain: str):

        results = []
        domain = domain.rstrip(".").lower()

        try:
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
            # No es error grave → simplemente no hay registros MX
            return results

        except Exception as e:
            # Error inesperado → fallo real del collector
            raise CollectorError(f"MX resolution error for {domain}: {e}")

        return results