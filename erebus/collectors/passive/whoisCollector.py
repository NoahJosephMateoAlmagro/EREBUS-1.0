import whois
from .base import PassiveCollector


class WhoisCollector(PassiveCollector):


    def collect(self, target: str):
        try:
            w = whois.whois(target)

            def first(value):
                if isinstance(value, list):
                    return value[0]
                return value

            def as_list(value):
                if not value:
                    return []
                return value if isinstance(value, list) else [value]

            return {
                "registrar": first(w.registrar),
                "creation_date": first(w.creation_date),
                "expiration_date": first(w.expiration_date),
                "updated_date": first(w.updated_date),

                # Campos potencialmente múltiples
                "name_servers": as_list(w.name_servers),
                "status": as_list(w.status),
                "emails": as_list(w.emails),
            }

        except Exception as e:
            print("Error WHOIS:", e)
            return None
