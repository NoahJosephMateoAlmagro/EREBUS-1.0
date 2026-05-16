"""
Execution entity for EREBUS.

This module defines the execution metadata object used to identify and track one
analysis run.
"""

from __future__ import annotations

from datetime import datetime, timezone

import shared.constants as C
from shared.utils import build_execution_id
from shared.utils import validate_and_normalize_domain


class Execution:
    """
    Represents a single execution of the EREBUS engine.

    Stores execution metadata including target, timestamps and status.
    """

    def __init__(self, target: str):
        """
        Initializes a new execution.

        Args:
            target: Target domain or host used for the execution.
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

    def _build_execution_id(self, target: str, start_time: datetime) -> str:
        """
        Builds a readable execution identifier.

        The identifier follows this format:

            domain_YYYYMMDD_HHMMSS

        Example:
            urjc.es_20260516_183012

        Args:
            target: Raw execution target.
            start_time: Execution start datetime.

        Returns:
            str: Readable execution identifier.
        """
        normalized_target = validate_and_normalize_domain(target) or target
        safe_target = self._sanitize_execution_id_part(normalized_target)
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")

        return f"{safe_target}_{timestamp}"

    def _sanitize_execution_id_part(self, value: str) -> str:
        """
        Sanitizes a text fragment before using it in an execution id.

        Args:
            value: Raw value.

        Returns:
            str: Sanitized value safe for identifiers.
        """
        if value is None:
            return "unknown"

        sanitized = str(value).strip().lower()
        sanitized = sanitized.replace("https://", "")
        sanitized = sanitized.replace("http://", "")
        sanitized = sanitized.replace("www.", "")
        sanitized = sanitized.replace("/", "_")
        sanitized = sanitized.replace("\\", "_")
        sanitized = sanitized.replace(":", "_")
        sanitized = sanitized.replace(" ", "_")
        sanitized = sanitized.strip("_")

        return sanitized or "unknown"
