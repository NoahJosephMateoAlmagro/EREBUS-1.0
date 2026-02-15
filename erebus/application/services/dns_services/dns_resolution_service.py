import shared.constants as C

class DNSResolutionService:
    def __init__(self, dns_collector, uow, domain_validator):
        self.dns_collector = dns_collector
        self.uow = uow
        self.domain_validator = domain_validator

    def run(self, context):
        max_dns = int(context.cfg["limits"]["dns_max_domains"])
        domains_to_resolve = list(context.all_domains)[:max_dns]

        for domain in domains_to_resolve:
            clean_domain = self.domain_validator(domain)
            if not clean_domain:
                continue

            print("DEBUG -> resolving", clean_domain)
            dns_results = self.dns_collector.collect(clean_domain)
            print("DEBUG -> result", dns_results)

            if dns_results:
                self.uow.domains.update_domain_status(
                    context.execution.ID,
                    clean_domain,
                    C.DOMAIN_STATUS_RESOLVABLE
                )

                for r in dns_results:
                    self.uow.domains.insert_resolved_domain(
                        context.execution.ID,
                        r["domain"],
                        r["ip"],
                        r["source"]
                    )
            else:
                self.uow.domains.update_domain_status(
                    context.execution.ID,
                    clean_domain,
                    C.DOMAIN_STATUS_NOT_RESOLVABLE
                )
