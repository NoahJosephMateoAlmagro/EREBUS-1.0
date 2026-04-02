from datetime import datetime, timezone
from typing import List

from application.objects.responses.ModuleResponse import ModuleResponse


class ExecutionResponse:
    """
    Aggregated response representing the result of a full execution.

    """

    def __init__(
        self,
        execution_id: str,
        target: str,
        started_at: datetime,
        modules: List[ModuleResponse]
    ):
        """
        Initializes the execution response.

        Args:
            execution_id (str): Unique execution identifier
            target (str): Target domain or scope
            started_at (datetime): Execution start timestamp
            modules (List[ModuleResponse]): List of module responses
        """
        self.execution_id = execution_id
        self.target = target
        self.started_at = started_at
        self.finished_at = datetime.now(timezone.utc)

        self.modules = modules

        self.duration_seconds = (
            self.finished_at - self.started_at
        ).total_seconds()

        self.metrics_global = self._compute_global_metrics()

    def _compute_global_metrics(self):
        """
        Aggregates key metrics across all module responses.

        Returns:
            dict: Aggregated metrics (emails, credentials, domains)
        """
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