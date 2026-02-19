import dns.resolver
from collectors.base import PassiveCollector
import shared.constants as C


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

            answers = resolver.resolve(domain, "CNAME")

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
            pass

        except Exception as e:
            print(f"[DNS][CNAME] Error {domain} -> {e}")

        return results
