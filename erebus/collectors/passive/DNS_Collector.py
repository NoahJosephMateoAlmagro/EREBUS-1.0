import dns.resolver
from collectors.base import PassiveCollector
import shared.constants as C


class DNSCollector(PassiveCollector):

    def __init__(self, timeout: int = 8):
        self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.lifetime = timeout
        self.resolver.timeout = timeout
        self.resolver.nameservers = ["8.8.8.8", "1.1.1.1"]

    def collect(self, target: str):
        resultados = []

        for record_type in ["A", "AAAA"]:
            try:
                respuestas = self.resolver.resolve(target, record_type)

                for dato in sorted(respuestas, key=lambda r: r.to_text()):
                    resultados.append({
                        "domain": target,
                        "ip": dato.to_text(),
                        "record_type": record_type,
                        "source": C.TECHNIQUE_DNS
                    })

            except dns.resolver.NXDOMAIN:
                pass
            except dns.resolver.NoAnswer:
                pass
            except dns.resolver.Timeout:
                pass
            except Exception as e:
                print("DNS ERROR:", type(e), e)

        return resultados
