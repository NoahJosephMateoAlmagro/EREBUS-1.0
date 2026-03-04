from datetime import datetime
from typing import List

from application.objects.responses.ModuleResponse import ModuleResponse


class ExecutionResponse:

    def __init__(
        self,
        execution_id: str,
        target: str,
        started_at: datetime,
        modules: List[ModuleResponse]
    ):
        self.execution_id = execution_id
        self.target = target
        self.started_at = started_at.utcnow()
        self.finished_at = datetime.utcnow()

        self.modules = modules

        self.duration_seconds = (
            self.finished_at - self.started_at
        ).total_seconds()

        self.metrics_global = self._compute_global_metrics()

    def _compute_global_metrics(self):

        totals = {
            "emails_inserted": 0,
            "credentials_inserted": 0,
            "domains_inserted": 0
        }

        for module in self.modules:

            metrics = module.metrics or {}

            totals["emails_inserted"] += metrics.get("emails_inserted", 0)
            totals["credentials_inserted"] += metrics.get("credentials_inserted", 0)
            totals["domains_inserted"] += metrics.get("domains_inserted", 0)

        return totals