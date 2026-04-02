from datetime import datetime, timezone
import uuid

import shared.constants as C


class Execution:
    """
    Represents a single execution of the EREBUS engine.
    Stores execution metadata including target, timestamps and status.
    """

    def __init__(self, target: str):
        """
        Initializes a new execution.
        """
        self.ID = str(uuid.uuid4())
        self.TARGET = target

        self.START = datetime.now(timezone.utc)
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