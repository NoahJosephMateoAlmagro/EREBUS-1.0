import dns.resolver
from collectors.base import PassiveCollector
import shared.constants as C


class DNS_TXT_Collector(PassiveCollector):

    def __init__(self, timeout: int = 8):
        self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.lifetime = timeout
        self.resolver.timeout = timeout
        self.resolver.nameservers = ["8.8.8.8", "1.1.1.1"]



    def collect(self, domain: str):

        results = []

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
            dns.resolver.Timeout
        ):
            pass

        except Exception as e:
            print(f"[DNS][TXT] Error {domain} -> {e}")

        return results
