import dns.resolver
from .base import PassiveCollector
import core.constants as C

class DNSCollector(PassiveCollector):

    def __init__(self, timeout: int = 8):
        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = timeout
        self.resolver.timeout = timeout

    def collect(self, target: str):
        resultados = []

        try:
            respuestas = dns.resolver.resolve(target, "A")
            for dato in sorted(respuestas, key=lambda r: r.to_text()):

                resultados.append({
                    "domain": target,
                    "ip": dato.to_text(),
                    "source": C.TECHNIQUE_DNS

                })

        #SILENCIADO DE ERRORES
        except dns.resolver.NXDOMAIN:
            pass  # dominio no existe (esperable)
        except dns.resolver.NoAnswer:
            pass  # no hay A record
        except dns.resolver.Timeout:
            pass  # timeout DNS
        except Exception:
            pass  # cualquier otro error no crítico

        return resultados
