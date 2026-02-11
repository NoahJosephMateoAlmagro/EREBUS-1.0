import dns.resolver
from collectors.base import PassiveCollector
import shared.constants as C


class DNS_NS_Collector(PassiveCollector):

    def __init__(self, timeout):
        self.timeout = timeout

    def collect(self, domain: str):

        results = []

        try:

            resolver = dns.resolver.Resolver()
            resolver.lifetime = self.timeout

            answers = resolver.resolve(domain, "NS")

            for data in answers:
                NS = str(data.target).rstrip(".").lower()

                results.append({
                    "domain": domain,
                    "record": NS,
                    "type": "NS",
                    "source": C.TECHNIQUE_DNS_NS
                })
        except (dns.resolver.NoAnswer,
                dns.resolver.NXDOMAIN,
                dns.resolver.Timeout):
            pass

        except Exception as e:
            print(f"[DNS][NS] Error {domain} -> {e}")

        return results

