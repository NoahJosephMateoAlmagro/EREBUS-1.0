from datetime import datetime
import shared.constants as C
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError


class DNSResolutionService:

    def __init__(self, dns_collector, uow, domain_validator):
        self.dns_collector = dns_collector
        self.uow = uow
        self.domain_validator = domain_validator

    def run(self, context) -> ModuleResponse | None:

        response = ModuleResponse(
            module_name="dns_resolution",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "domains_checked": 0,
            "domains_resolvable": 0,
            "domains_not_resolvable": 0,
            "records_inserted": 0
        }

        try:
            max_dns = int(context.cfg["limits"]["dns_max_domains"])
            domains_to_resolve = list(context.all_domains)[:max_dns]

            for domain in domains_to_resolve:

                clean_domain = self.domain_validator(domain)
                if not clean_domain:
                    continue

                metrics["domains_checked"] += 1

                dns_results = self.dns_collector.collect(clean_domain)

                if dns_results:

                    metrics["domains_resolvable"] += 1

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
                        metrics["records_inserted"] += 1

                else:

                    metrics["domains_not_resolvable"] += 1

                    self.uow.domains.update_domain_status(
                        context.execution.ID,
                        clean_domain,
                        C.DOMAIN_STATUS_NOT_RESOLVABLE
                    )

            response.metrics = metrics

        except CollectorError as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append("Unexpected error in DNS module")

        finally:
            response.finished_at = datetime.utcnow()

        return response