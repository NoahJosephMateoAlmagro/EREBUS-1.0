import dns.resolver
from collectors.base import PassiveCollector
import shared.constants as C


class DNS_TXT_Collector(PassiveCollector):

    def __init__(self, timeout: int = 8):
        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = timeout
        self.resolver.timeout = timeout

    def collect(self, domain: str):
        results = []

        try:
            answers = dns.resolver.resolve(domain, "TXT")

            for rdata in answers:
                value = "".join(
                    part.decode() if isinstance(part, bytes) else part
                    for part in rdata.strings
                )

                results.append({
                    "domain": domain,
                    "value": value,
                    "source": C.TECHNIQUE_DNS_TXT
                })

        except (dns.resolver.NoAnswer,
                dns.resolver.NXDOMAIN,
                dns.resolver.Timeout):
            pass

        except Exception:
            pass

        return results
