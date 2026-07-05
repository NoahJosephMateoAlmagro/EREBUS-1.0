"""
Results export service for the EREBUS presentation layer.

This service connects the Results page with the Word exporter. It asks the user
where to save the report and delegates document generation to the export layer.
"""

from __future__ import annotations

from datetime import datetime
from tkinter import filedialog

from export.docx.execution_summary_docx_exporter import (
    ExecutionSummaryDocxExporter,
)


class ResultsExportService:
    """
    Service used by the Results page to export execution reports.
    """

    def __init__(self):
        """
        Initializes the results export service.
        """
        self.exporter = ExecutionSummaryDocxExporter()

    def export_summary_to_word(
        self,
        summary: dict,
        parent=None,
    ) -> dict | None:
        """
        Asks the user for a destination path and exports the summary to Word.

        Args:
            summary: Structured results summary.
            parent: Optional parent window for the save dialog.

        Returns:
            dict | None: Export metadata if exported, otherwise None if the
            user cancels the dialog.
        """
        output_path = self._ask_output_path(
            summary=summary,
            parent=parent,
        )

        if not output_path:
            return None

        return self.exporter.export(
            summary=summary,
            output_path=output_path,
        )

    def _ask_output_path(
        self,
        summary: dict,
        parent=None,
    ) -> str:
        """
        Opens a save dialog for the Word report.

        Args:
            summary: Structured results summary.
            parent: Optional parent window.

        Returns:
            str: Selected output path or empty string if cancelled.
        """
        initial_file = self._build_default_filename(summary)

        return filedialog.asksaveasfilename(
            parent=parent,
            title="Export execution report",
            defaultextension=".docx",
            initialfile=initial_file,
            filetypes=[
                ("Word document", "*.docx"),
                ("All files", "*.*"),
            ],
        )

    def _build_default_filename(self, summary: dict) -> str:
        """
        Builds a readable default Word report filename.

        Args:
            summary: Structured results summary.

        Returns:
            str: Default filename.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        execution_id = self._sanitize_filename_part(
            str(summary.get("execution_id", "")).strip()
        )

        if execution_id:
            return f"erebus_report_{execution_id}.docx"

        return f"erebus_report_{timestamp}.docx"

    def _sanitize_filename_part(self, value: str) -> str:
        """
        Sanitizes a text fragment for safe filename usage.

        Args:
            value: Raw text.

        Returns:
            str: Safe filename fragment.
        """
        if not value:
            return ""

        allowed_chars = []

        for char in value:
            if char.isalnum() or char in {"_", "-"}:
                allowed_chars.append(char)
            else:
                allowed_chars.append("_")

        return "".join(allowed_chars).strip("_")[:120]
