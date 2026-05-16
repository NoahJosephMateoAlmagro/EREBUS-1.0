"""
Data export service for the EREBUS presentation layer.

This service connects the Data page with the Excel exporter. It is responsible
for asking the user where to save the file and delegating the workbook generation
to the export layer.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tkinter import filedialog

from export.excel.filtered_database_excel_exporter import (
    FilteredDatabaseExcelExporter,
)
from presentation.services.data_browser_service import DataBrowserService


class DataExportService:
    """
    Service used by the Data page to export filtered stored data.
    """

    def __init__(self, database_service: DataBrowserService | None = None):
        """
        Initializes the data export service.

        Args:
            database_service: Optional data browser service shared with the Data
                page.
        """
        self.database_service = database_service or DataBrowserService()
        self.exporter = FilteredDatabaseExcelExporter(self.database_service)

    def export_filtered_database_to_excel(
        self,
        execution_filter: str = "",
        parent=None,
    ) -> dict | None:
        """
        Asks the user for a destination path and exports filtered data to Excel.

        Args:
            execution_filter: Active execution identifier filter.
            parent: Optional parent window for the save dialog.

        Returns:
            dict | None: Export metadata if the file was generated, otherwise
            None when the user cancels the dialog.
        """
        output_path = self._ask_output_path(
            execution_filter=execution_filter,
            parent=parent,
        )

        if not output_path:
            return None

        return self.exporter.export(
            output_path=output_path,
            execution_filter=execution_filter,
        )

    def _ask_output_path(
        self,
        execution_filter: str = "",
        parent=None,
    ) -> str:
        """
        Opens a save dialog for the Excel export.

        Args:
            execution_filter: Active execution identifier filter.
            parent: Optional parent window.

        Returns:
            str: Selected output path or an empty string if cancelled.
        """
        initial_file = self._build_default_filename(execution_filter)

        return filedialog.asksaveasfilename(
            parent=parent,
            title="Export filtered data",
            defaultextension=".xlsx",
            initialfile=initial_file,
            filetypes=[
                ("Excel workbook", "*.xlsx"),
                ("All files", "*.*"),
            ],
        )

    def _build_default_filename(self, execution_filter: str = "") -> str:
        """
        Builds a readable default Excel filename.

        Args:
            execution_filter: Active execution identifier filter.

        Returns:
            str: Default export filename.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_filter = self._sanitize_filename_part(execution_filter.strip())

        if clean_filter:
            return f"erebus_data_{clean_filter}_{timestamp}.xlsx"

        return f"erebus_data_all_{timestamp}.xlsx"

    def _sanitize_filename_part(self, value: str) -> str:
        """
        Sanitizes a text fragment so it can be used inside a filename.

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

        return "".join(allowed_chars).strip("_")[:80]