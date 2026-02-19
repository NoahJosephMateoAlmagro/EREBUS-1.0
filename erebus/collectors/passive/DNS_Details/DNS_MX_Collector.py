import dns.resolver
from collectors.base import PassiveCollector
import shared.constants as C

class DNS_MX_Collector(PassiveCollector):

    def __init__(self, timeout = 8):
        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = timeout
        self.resolver.timeout = timeout

    def collect(self, domain: str):
        results = []

        try:
            answers = self.resolver.resolve(domain, "MX")

            for rdata in answers:
                results.append({
                    "domain": domain,
                    "record": str(rdata.exchange).rstrip("."),
                    "priority": rdata.preference,
                    "source": C.TECHNIQUE_DNS_MX
                })

        except (dns.resolver.NoAnswer,
                dns.resolver.NXDOMAIN,
                dns.resolver.Timeout,
                dns.resolver.NoNameservers
                ):
            pass

        except Exception:
            pass

        return results

