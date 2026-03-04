from datetime import datetime
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus


class DNSService:

    def __init__(self, context_service, resolution_service, observation_service, headers_service):
        self.context_service = context_service
        self.resolution_service = resolution_service
        self.observation_service = observation_service
        self.headers_service = headers_service

    def run(self, context) -> ModuleResponse | None:

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

            # Agregamos métricas
            for r in [context_result, resolution_result, observation_result]:
                metrics.update(r.metrics)
                if r.status == ModuleStatus.FAILED:
                    response.status = ModuleStatus.FAILED
                errors.extend(r.errors)

            # Headers opcional
            if context.cfg["modules"].get("http_headers"):
                headers_result = self.headers_service.run(context)
                metrics.update(headers_result.metrics)
                if headers_result.status == ModuleStatus.FAILED:
                    response.status = ModuleStatus.FAILED
                errors.extend(headers_result.errors)

            response.metrics = metrics
            response.errors = errors

        except Exception:
            response.status = ModuleStatus.FAILED
            response.errors.append("Unexpected error in DNSService wrapper")

        finally:
            response.finished_at = datetime.utcnow()

        return response