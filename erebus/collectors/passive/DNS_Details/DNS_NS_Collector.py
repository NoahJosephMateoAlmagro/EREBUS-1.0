import dns.resolver
from collectors.base import PassiveCollector
import shared.constants as C

class DNS_NS_Collector(PassiveCollector):

    def __init__(self, timeout=8):
        self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.lifetime = timeout
        self.resolver.timeout = timeout
        self.resolver.nameservers = ["8.8.8.8", "1.1.1.1"]

    def collect(self, domain: str):

        results = []

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
            dns.resolver.Timeout
        ):
            pass

        except Exception as e:
            print(f"[DNS][NS] Error {domain} -> {e}")

        return results
