from datetime import datetime, timezone

import shared.constants as C
from shared.utils import build_execution_id


class Execution:
    """
    Represents a single execution of the EREBUS engine.
    Stores execution metadata including target, timestamps and status.
    """

    def __init__(self, target: str):
        """
        Initializes a new execution.

        Args:
            target: Target domain analyzed by EREBUS.
        """
        self.TARGET = target

        self.START = datetime.now(timezone.utc)
        self.ID = build_execution_id(target, self.START)

        self.END = None
        self.STATUS = C.EXECUTION_STATUS_RUNNING

    def finish(self):
        """
        Marks the execution as successfully finished.
        """
        self.END = datetime.now(timezone.utc)
        self.STATUS = C.EXECUTION_STATUS_FINISHED

    def fail(self):
        """
        Marks the execution as failed.
        """
        self.END = datetime.now(timezone.utc)
        self.STATUS = C.EXECUTION_STATUS_ERROR

    @property
    def duration_seconds(self):
        """
        Returns execution duration in seconds.
        """
        if not self.END:
            return None

        return (self.END - self.START).total_seconds()