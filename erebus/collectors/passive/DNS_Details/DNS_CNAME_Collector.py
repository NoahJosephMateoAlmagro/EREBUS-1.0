import dns.resolver
from collectors.passive.base import PassiveCollector
import core.constants as C

class DNS_CNAME_Collector(PassiveCollector):

    def __init__(self, timeout):
        self.timeout = timeout

    def collect(self, domain: str):

        results = []

        try:

            resolver = dns.resolver.Resolver()
            resolver.lifetime = self.timeout

            answers = resolver.resolve(domain, "CNAME")

            for data in answers:
                cname = str(data.target).rstrip(".").lower()

                results.append({
                    "domain": domain,
                    "record": cname,
                    "type": "CNAME",
                    "source": C.TECHNIQUE_DNS_CNAME
                })
        except (dns.resolver.NoAnswer,
                dns.resolver.NXDOMAIN,
                dns.resolver.Timeout):
            pass

        except Exception as e:
            print(f"[DNS][CNAME] Error {domain} -> {e}")

        return results

