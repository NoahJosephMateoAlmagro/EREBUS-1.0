from datetime import datetime

import shared.constants as C
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError
from shared.logger import Logger


class DNSResolutionService:
    """
    Service responsible for resolving discovered domains and persisting
    DNS resolution results and domain status updates.
    """

    def __init__(self, dns_collector, uow, domain_validator):
        """
        Args:
            dns_collector: Collector responsible for resolving DNS records
            uow: Unit of Work for persistence operations
            domain_validator: Callable used to validate and normalize domain values
        """
        self.dns_collector = dns_collector
        self.uow = uow
        self.domain_validator = domain_validator

    def run(self, context) -> ModuleResponse:
        """
        Executes DNS resolution workflow for discovered domains.

        Args:
            context: Execution context containing discovered domains,
                execution metadata and configuration

        Returns:
            ModuleResponse: Execution result with status, metrics and errors
        """
        target = context.execution.TARGET
        execution_id = context.execution.ID

        Logger.info(
            f"Starting DNS resolution module execution_id={execution_id} target={target}",
            context=self.__class__.__name__
        )

        response = ModuleResponse(
            module_name="dns_resolution",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "domains_checked": 0,
            "domains_resolvable": 0,
            "domains_not_resolvable": 0,
            "domains_failed": 0,
            "records_inserted": 0
        }

        try:
            max_dns = int(context.cfg["limits"]["dns_max_domains"])
            domains_to_resolve = list(context.all_domains)[:max_dns]

            if not domains_to_resolve:
                response.status = ModuleStatus.SKIPPED
                response.metrics = metrics

                Logger.info(
                    f"Skipping DNS resolution module execution_id={execution_id} target={target} "
                    f"because there are no domains to resolve",
                    context=self.__class__.__name__
                )

                return response

            # Resolve each discovered domain independently
            for domain in domains_to_resolve:
                clean_domain = self.domain_validator(domain)
                if not clean_domain:
                    continue

                metrics["domains_checked"] += 1

                try:
                    dns_results = self.dns_collector.collect(clean_domain)

                    if dns_results:
                        metrics["domains_resolvable"] += 1

                        self.uow.domains.update_domain_status(
                            execution_id,
                            clean_domain,
                            C.DOMAIN_STATUS_RESOLVABLE
                        )

                        for record in dns_results:
                            self.uow.domains.insert_resolved_domain(
                                execution_id,
                                record["domain"],
                                record["ip"],
                                record["source"]
                            )
                            metrics["records_inserted"] += 1

                    else:
                        metrics["domains_not_resolvable"] += 1

                        self.uow.domains.update_domain_status(
                            execution_id,
                            clean_domain,
                            C.DOMAIN_STATUS_NOT_RESOLVABLE
                        )

                except CollectorError as e:
                    metrics["domains_failed"] += 1
                    response.errors.append(f"DNS resolution failed for {clean_domain}: {e}")

                    Logger.error(
                        f"DNS resolution collector error execution_id={execution_id} "
                        f"target={target} domain={clean_domain}: {e}",
                        context=self.__class__.__name__
                    )

                    continue

            if metrics["domains_checked"] == 0:
                response.status = ModuleStatus.SKIPPED
            elif metrics["domains_failed"] == 0:
                response.status = ModuleStatus.SUCCESS
            elif metrics["domains_failed"] < metrics["domains_checked"]:
                response.status = ModuleStatus.PARTIAL
            else:
                response.status = ModuleStatus.FAILED

            response.metrics = metrics

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(f"Unexpected error in DNS resolution module: {e}")

            Logger.error(
                f"Unexpected DNS resolution error execution_id={execution_id} "
                f"target={target}: {e}",
                context=self.__class__.__name__
            )

        finally:
            response.finished_at = datetime.utcnow()

            Logger.info(
                f"Finished DNS resolution module execution_id={execution_id} "
                f"status={response.status} metrics={metrics}",
                context=self.__class__.__name__
            )

        return response