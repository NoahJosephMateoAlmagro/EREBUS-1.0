from collectors.base import PassiveCollector
import dns.resolver
import shared.constants as C
from exceptions.exceptions import CollectorError


class DNS_CNAME_Collector(PassiveCollector):

    def __init__(self, timeout: int):
        self.timeout = timeout

    def collect(self, domain: str):

        results = []
        domain = domain.rstrip(".").lower()

        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = self.timeout
            resolver.lifetime = self.timeout

            answers = resolver.resolve(domain, "CNAME", tcp=True)

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
            # No es error técnico grave → simplemente no hay CNAME
            return results

        except Exception as e:
            # Error inesperado → fallo real del collector
            raise CollectorError(f"CNAME resolution error for {domain}: {e}")

        return results