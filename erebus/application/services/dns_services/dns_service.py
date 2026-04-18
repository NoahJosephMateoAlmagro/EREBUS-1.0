from datetime import datetime

from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from shared.logger import Logger


class DNSService:
    """
    Service responsible for orchestrating DNS-related subservices
    and aggregating their results into a single module response.
    """

    def __init__(self, context_service, resolution_service, observation_service, headers_service):
        """
        Args:
            context_service: Service responsible for DNS context analysis
            resolution_service: Service responsible for DNS resolution workflow
            observation_service: Service responsible for DNS observation workflow
            headers_service: Optional service responsible for HTTP headers workflow
        """
        self.context_service = context_service
        self.resolution_service = resolution_service
        self.observation_service = observation_service
        self.headers_service = headers_service

    def run(self, context) -> ModuleResponse:
        """
        Executes the DNS module wrapper workflow.

        Args:
            context: Execution context containing configuration,
                execution metadata and shared state

        Returns:
            ModuleResponse: Aggregated execution result for the DNS module
        """
        target = context.execution.TARGET
        execution_id = context.execution.ID

        Logger.info(
            f"Starting DNS module execution_id={execution_id} target={target}",
            context=self.__class__.__name__
        )

        response = ModuleResponse(
            module_name="dns",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {}
        errors = []

        try:
            context_result = self.context_service.run(context)
            resolution_result = self.resolution_service.run(context)
            observation_result = self.observation_service.run(context)

            # Aggregate metrics and errors from mandatory DNS subservices
            for result in [context_result, resolution_result, observation_result]:
                metrics.update(result.metrics)

                if result.status == ModuleStatus.FAILED:
                    response.status = ModuleStatus.FAILED

                errors.extend(result.errors)

            # Run optional HTTP headers subservice if enabled
            if context.cfg["modules"].get("http_headers"):
                headers_result = self.headers_service.run(context)
                metrics.update(headers_result.metrics)

                if headers_result.status == ModuleStatus.FAILED:
                    response.status = ModuleStatus.FAILED

                errors.extend(headers_result.errors)

            response.metrics = metrics
            response.errors = errors

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(f"Unexpected error in DNS module wrapper: {e}")

            Logger.error(
                f"Unexpected DNS module wrapper error execution_id={execution_id} "
                f"target={target}: {e}",
                context=self.__class__.__name__
            )

        finally:
            response.finished_at = datetime.utcnow()

            Logger.info(
                f"Finished DNS module execution_id={execution_id} "
                f"status={response.status} metrics={metrics}",
                context=self.__class__.__name__
            )

        return response