"""
Execution summary Word exporter for EREBUS.

This module creates a readable Word report from the structured summary shown in
the Results page. It intentionally exports interpreted execution information,
not raw database dumps. Raw table data is handled by the Excel export available
from the Data page.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt


class ExecutionSummaryDocxExporter:
    """
    Exports an EREBUS execution summary to a Word document.
    """

    EMPTY_VALUE = "-"

    def export(
        self,
        summary: dict[str, Any],
        output_path: str | Path,
    ) -> dict[str, Any]:
        """
        Exports an execution summary to a Word document.

        Args:
            summary: Structured summary dictionary rendered by ResultsPage.
            output_path: Destination .docx path.

        Returns:
            dict[str, Any]: Export metadata.

        Raises:
            ValueError: If summary or output path are not valid.
        """
        if not isinstance(summary, dict) or not summary:
            raise ValueError("A valid execution summary is required.")

        if not output_path:
            raise ValueError("Output path is required.")

        output_path = Path(output_path)

        if output_path.suffix.lower() != ".docx":
            output_path = output_path.with_suffix(".docx")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        document = Document()
        self._configure_document(document)

        self._add_title(document, summary)
        self._add_execution_section(document, summary)
        self._add_global_highlights_section(document, summary)
        self._add_active_modules_section(document, summary)
        self._add_module_details_section(document, summary)
        self._add_footer_note(document)

        document.save(output_path)

        return {
            "output_path": str(output_path),
            "execution_id": summary.get("execution_id", self.EMPTY_VALUE),
            "target": summary.get("target", self.EMPTY_VALUE),
        }

    def _configure_document(self, document: Document) -> None:
        """
        Applies base document layout and style settings.

        Args:
            document: Target Word document.
        """
        section = document.sections[0]
        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

        style = document.styles["Normal"]
        style.font.name = "Calibri"
        style.font.size = Pt(10.5)

    def _add_title(self, document: Document, summary: dict[str, Any]) -> None:
        """
        Adds the report title.

        Args:
            document: Target Word document.
            summary: Execution summary.
        """
        title = document.add_heading("EREBUS Execution Report", level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        subtitle = document.add_paragraph()
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle.add_run(
            self._safe_text(summary.get("execution_id"))
        ).bold = True

        generated = document.add_paragraph()
        generated.alignment = WD_ALIGN_PARAGRAPH.CENTER
        generated.add_run(
            f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        document.add_paragraph()

    def _add_execution_section(
        self,
        document: Document,
        summary: dict[str, Any],
    ) -> None:
        """
        Adds the main execution metadata section.

        Args:
            document: Target Word document.
            summary: Execution summary.
        """
        document.add_heading("1. Execution overview", level=1)

        rows = [
            ("Execution ID", self._safe_text(summary.get("execution_id"))),
            ("Target", self._safe_text(summary.get("target"))),
            ("Status", self._safe_text(summary.get("status"))),
            ("Started at", self._format_datetime(summary.get("started_at"))),
            (
                "Duration",
                self._format_duration(summary.get("total_duration_seconds", 0)),
            ),
        ]

        self._add_key_value_table(document, rows)

    def _add_global_highlights_section(
        self,
        document: Document,
        summary: dict[str, Any],
    ) -> None:
        """
        Adds the global findings section.

        Args:
            document: Target Word document.
            summary: Execution summary.
        """
        document.add_heading("2. Main findings", level=1)

        highlights = summary.get("global_highlights", [])

        if not highlights:
            document.add_paragraph(
                "No relevant findings were reported by the enabled modules."
            )
            return

        table = document.add_table(rows=1, cols=2)
        table.style = "Table Grid"

        header_cells = table.rows[0].cells
        header_cells[0].text = "Metric"
        header_cells[1].text = "Value"

        for item in highlights:
            row_cells = table.add_row().cells
            row_cells[0].text = self._safe_text(item.get("label"))
            row_cells[1].text = self._safe_text(item.get("value"))

        self._bold_first_row(table)

    def _add_active_modules_section(
        self,
        document: Document,
        summary: dict[str, Any],
    ) -> None:
        """
        Adds the active modules section.

        Args:
            document: Target Word document.
            summary: Execution summary.
        """
        document.add_heading("3. Active modules", level=1)

        active_modules = summary.get("active_modules", [])

        if not active_modules:
            document.add_paragraph("No active module information is available.")
            return

        for module in active_modules:
            paragraph = document.add_paragraph(style="List Bullet")
            paragraph.add_run(self._safe_text(module.get("title"))).bold = True
            key = module.get("key")

            if key:
                paragraph.add_run(f" ({key})")

    def _add_module_details_section(
        self,
        document: Document,
        summary: dict[str, Any],
    ) -> None:
        """
        Adds a per-module summary section.

        Args:
            document: Target Word document.
            summary: Execution summary.
        """
        document.add_heading("4. Module results", level=1)

        module_cards = summary.get("module_cards", [])

        if not module_cards:
            document.add_paragraph("No module results are available.")
            return

        for module in module_cards:
            title = self._safe_text(
                module.get("title") or module.get("module_key")
            )
            document.add_heading(title, level=2)

            rows = [
                ("Module key", self._safe_text(module.get("module_key"))),
                ("Status", self._safe_text(module.get("status"))),
                (
                    "Duration",
                    self._format_duration(module.get("duration_seconds", 0)),
                ),
            ]

            self._add_key_value_table(document, rows)

            highlights = module.get("highlights", [])

            if not highlights:
                document.add_paragraph("No relevant findings for this module.")
                continue

            table = document.add_table(rows=1, cols=2)
            table.style = "Table Grid"

            header_cells = table.rows[0].cells
            header_cells[0].text = "Finding"
            header_cells[1].text = "Value"

            for item in highlights:
                row_cells = table.add_row().cells
                row_cells[0].text = self._safe_text(item.get("label"))
                row_cells[1].text = self._safe_text(item.get("value"))

            self._bold_first_row(table)
            document.add_paragraph()

    def _add_footer_note(self, document: Document) -> None:
        """
        Adds a short explanatory note at the end of the report.

        Args:
            document: Target Word document.
        """
        document.add_heading("5. Notes", level=1)

        document.add_paragraph(
            "This report summarizes the interpreted results shown in the EREBUS "
            "Results page. It is intended for quick review and documentation. "
            "For full raw data inspection, use the Excel export available from "
            "the Data page."
        )

    def _add_key_value_table(
        self,
        document: Document,
        rows: list[tuple[str, str]],
    ) -> None:
        """
        Adds a two-column key/value table.

        Args:
            document: Target Word document.
            rows: Key/value rows.
        """
        table = document.add_table(rows=0, cols=2)
        table.style = "Table Grid"

        for label, value in rows:
            row_cells = table.add_row().cells
            row_cells[0].text = label
            row_cells[1].text = value

            for paragraph in row_cells[0].paragraphs:
                for run in paragraph.runs:
                    run.bold = True

        document.add_paragraph()

    def _bold_first_row(self, table) -> None:
        """
        Applies bold text to the first table row.

        Args:
            table: Word table.
        """
        if not table.rows:
            return

        for cell in table.rows[0].cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.bold = True

    def _format_datetime(self, value) -> str:
        """
        Formats a datetime value.

        Args:
            value: Datetime-like value.

        Returns:
            str: Human-readable datetime.
        """
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")

        if value:
            return str(value)

        return self.EMPTY_VALUE

    def _format_duration(self, seconds: float | int | None) -> str:
        """
        Formats duration seconds as minutes and seconds.

        Args:
            seconds: Duration in seconds.

        Returns:
            str: Human-readable duration.
        """
        try:
            total_seconds = max(0, int(round(float(seconds or 0))))
            minutes = total_seconds // 60
            remaining_seconds = total_seconds % 60
            return f"{minutes} min {remaining_seconds} s"
        except Exception:
            return self.EMPTY_VALUE

    def _safe_text(self, value) -> str:
        """
        Converts a value to safe display text.

        Args:
            value: Raw value.

        Returns:
            str: Safe text.
        """
        if value is None:
            return self.EMPTY_VALUE

        text = str(value).strip()
        return text or self.EMPTY_VALUE