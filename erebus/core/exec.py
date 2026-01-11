from datetime import datetime, timezone
import uuid

import core.constants as C


class Execution:
    def __init__(self, target: str):
        self.ID = str(uuid.uuid4())
        self.TARGET = target

        self.START = datetime.now(timezone.utc)
        self.END = None

        self.STATUS = C.EXECUTION_STATUS_RUNNING

    def finish(self):
        self.END = datetime.now(timezone.utc)
        self.STATUS = C.EXECUTION_STATUS_FINISHED

    def fail(self):
        self.END = datetime.now(timezone.utc)
        self.STATUS = C.EXECUTION_STATUS_ERROR

    @property
    def duration_seconds(self):
        if not self.END:
            return None
        return (self.END - self.START).total_seconds()
