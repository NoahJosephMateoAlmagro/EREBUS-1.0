from collectors.base import PassiveCollector
import dns.resolver
import shared.constants as C
from exceptions.exceptions import CollectorError


class DNS_TXT_Collector(PassiveCollector):

    def __init__(self, timeout: int = 8):
        self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.lifetime = timeout
        self.resolver.timeout = timeout
        self.resolver.nameservers = ["8.8.8.8", "1.1.1.1"]

    def collect(self, domain: str):

        results = []
        domain = domain.rstrip(".").lower()

        try:
            answers = self.resolver.resolve(domain, "TXT", tcp=True)

            for rdata in answers:

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
            # No es error grave → simplemente no hay registros TXT
            return results

        except Exception as e:
            raise CollectorError(f"TXT resolution error for {domain}: {e}")

        return results