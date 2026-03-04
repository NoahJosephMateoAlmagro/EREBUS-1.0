from datetime import datetime
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError


class WhoisService:

    def __init__(self, whois_collector, uow):
        self.whois_collector = whois_collector
        self.uow = uow

    def run(self, context) -> ModuleResponse | None:

        response = ModuleResponse(
            module_name="whois",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "whois_found": 0
        }

        try:
            whois_data = self.whois_collector.collect(
                context.execution.TARGET
            )

            if whois_data:
                self.uow.whois.insert_whois_result(
                    context.execution.ID,
                    context.execution.TARGET,
                    whois_data
                )
                metrics["whois_found"] = 1

            response.metrics = metrics

        except CollectorError as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

        except Exception:
            response.status = ModuleStatus.FAILED
            response.errors.append("Unexpected error in WHOIS module")

        finally:
            response.finished_at = datetime.utcnow()

        return response