from datetime import datetime
import shared.constants as C
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError
from shared.logger import Logger


class SubdomainService:
    """
    Service responsible for collecting subdomains, validating discovered domains
    and persisting new domain entries.
    """

    def __init__(self, subdomain_collector, uow, domain_validator):
        """
        Args:
            subdomain_collector: Collector responsible for retrieving subdomains
            uow: Unit of Work for persistence operations
            domain_validator: Callable used to validate and normalize domain values
        """
        self.subdomain_collector = subdomain_collector
        self.uow = uow
        self._valid_domain = domain_validator

    def run(self, context) -> ModuleResponse:
        """
        Executes subdomain collection workflow.

        Args:
            context: Execution context containing target, execution metadata
                and shared domain state

        Returns:
            ModuleResponse: Execution result with status, metrics and errors
        """

        target = context.execution.TARGET
        execution_id = context.execution.ID

        Logger.info(
            f"Starting subdomain module execution_id={execution_id} target={target}",
            context=self.__class__.__name__
        )

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
                target
            )

            metrics["subdomains_found"] = len(subdomains)

            for s in subdomains:
                domain = self._valid_domain(s.get("value"))

                if domain:
                    context.all_domains.add(domain)

            for domain in context.all_domains:
                if domain not in context.seen_domains:

                    context.seen_domains.add(domain)

                    self.uow.domains.insert_domain(
                        execution_id,
                        domain,
                        source=C.TECHNIQUE_SUBDOMAINS,
                        status=C.DOMAIN_STATUS_NOT_EVALUATED
                    )

                    metrics["domains_inserted"] += 1

            response.metrics = metrics

        except CollectorError as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

            Logger.error(
                f"Subdomain collector error execution_id={execution_id} target={target}: {e}",
                context=self.__class__.__name__
            )

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(f"Unexpected error in subdomain module: {e}")


            Logger.error(
                f"Unexpected subdomain error execution_id={execution_id} target={target}: {e}",
                context=self.__class__.__name__
            )


        finally:
            response.finished_at = datetime.utcnow()

            Logger.info(
                f"Finished subdomain module execution_id={execution_id} "
                f"status={response.status} metrics={metrics}",
                context=self.__class__.__name__
            )


        return response