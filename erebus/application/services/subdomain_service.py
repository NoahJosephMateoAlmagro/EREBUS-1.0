from datetime import datetime
import shared.constants as C
from application.objects.responses.ModuleResponse import ModuleResponse
from application.objects.responses.ModuleResponse import ModuleStatus
from exceptions.exceptions import CollectorError


class SubdomainService:

    def __init__(self, subdomain_collector, uow, domain_validator):
        self.subdomain_collector = subdomain_collector
        self.uow = uow
        self._is_valid_domain = domain_validator

    def run(self, context) -> ModuleResponse | None:

        response = ModuleResponse(
            module_name="subdomains",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "subdomains_found": 0,
            "domains_inserted": 0
        }

        try:
            subdomains = self.subdomain_collector.collect(
                context.execution.TARGET
            )

            metrics["subdomains_found"] = len(subdomains)

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

                    metrics["domains_inserted"] += 1

            response.metrics = metrics

        except CollectorError as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append("Unexpected error in subdomain module")

        finally:
            response.finished_at = datetime.utcnow()

        return response