import shared.constants as C

class SubdomainService:

    def __init__(self, subdomain_collector, uow, domain_validator):
        self.subdomain_collector = subdomain_collector
        self.uow = uow
        self._is_valid_domain = domain_validator

    def run(self, context):

        print("Encontrando subdominios...")

        subdomains = self.subdomain_collector.collect(
            context.execution.TARGET
        )

        for s in subdomains:
            domain = self._is_valid_domain(s.get("value"))
            if domain:
                context.all_domains.add(domain)

        for domain in context.all_domains:
            if domain not in context.seen_domains:
                context.seen_domains.add(domain)

                self.uow.domains.insert_domain(
                    context.execution.ID,
                    domain,
                    source=C.TECHNIQUE_SUBDOMAINS,
                    status=C.DOMAIN_STATUS_NOT_EVALUATED
                )
