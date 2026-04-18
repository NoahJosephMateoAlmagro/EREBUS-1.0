from datetime import datetime
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError
from shared.logger import Logger


class WhoisService:
    """
    Service responsible for orchestrating WHOIS data collection and persistence.
    """

    def __init__(self, whois_collector, uow):
        """
        Args:
            whois_collector: Collector responsible for retrieving WHOIS data
            uow: Unit of Work for persistence operations
        """
        self.whois_collector = whois_collector
        self.uow = uow

    def run(self, context) -> ModuleResponse:
        """
        Executes WHOIS collection workflow.

        Args:
            context: Execution context containing target and execution metadata

        Returns:
            ModuleResponse: Execution result with status, metrics and errors
        """
        target = context.execution.TARGET
        execution_id = context.execution.ID

        Logger.info(
            f"Starting WHOIS module execution_id={execution_id} target={target}",
            context=self.__class__.__name__
        )

        response = ModuleResponse(
            module_name="whois",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "whois_record_found": 0
        }

        try:
            if target.endswith(".es"):
                response.status = ModuleStatus.SKIPPED

                Logger.info(
                    f"Skipping WHOIS module for target={target} because .es domains are not supported",
                    context=self.__class__.__name__
                )

                response.metrics = metrics
                return response

            whois_data = self.whois_collector.collect(target)

            if whois_data:
                self.uow.whois.insert_whois_result(
                    execution_id,
                    target,
                    whois_data
                )
                metrics["whois_record_found"] = 1

            response.metrics = metrics

        except CollectorError as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

            Logger.error(
                f"WHOIS collector error execution_id={execution_id} target={target}: {e}",
                context=self.__class__.__name__
            )

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(f"Unexpected error in WHOIS module: {e}")

            Logger.error(
                f"Unexpected WHOIS error execution_id={execution_id} target={target}: {e}",
                context=self.__class__.__name__
            )

        finally:
            response.finished_at = datetime.utcnow()

            Logger.info(
                f"Finished WHOIS module execution_id={execution_id} "
                f"status={response.status} metrics={metrics}",
                context=self.__class__.__name__
            )

        return response