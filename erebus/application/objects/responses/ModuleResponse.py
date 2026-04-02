from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime


class ModuleStatus(str, Enum):
    """
    Enumeration representing the execution status of a module.
    """
    SKIPPED = "SKIPPED"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


@dataclass
class ModuleResponse:
    """
    Standard response object returned by all modules.
    """

    module_name: str
    status: ModuleStatus
    metrics: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        """
        Computes execution duration in seconds.

        Returns:
            Optional[float]: Duration in seconds if both timestamps are present,
            otherwise None.
        """
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None