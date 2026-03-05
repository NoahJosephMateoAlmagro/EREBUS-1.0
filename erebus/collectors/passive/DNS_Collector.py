import dns.resolver
from collectors.base import Collector
import shared.constants as C
from exceptions.exceptions import CollectorError


class DNSCollector(Collector):

    def __init__(self, timeout: int = 8):
        self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.lifetime = timeout
        self.resolver.timeout = timeout
        self.resolver.nameservers = ["8.8.8.8", "1.1.1.1"]

    def collect(self, target: str):

        resultados = []
        attempted = 0
        network_failures = 0

        for record_type in ["A", "AAAA"]:
            attempted += 1
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
                # Dominio no existe → no es error técnico
                continue

            except dns.resolver.NoAnswer:
                # No hay registros de ese tipo → no es error
                continue

            except dns.resolver.Timeout:
                network_failures += 1
                continue

            except Exception as e:
                raise CollectorError(f"Error inesperado resolviendo DNS: {e}")

        # Si todo fueron timeouts, lo consideramos fallo técnico
        if network_failures == attempted and attempted > 0:
            raise CollectorError(f"Timeout resolviendo DNS para {target}")

        return resultados