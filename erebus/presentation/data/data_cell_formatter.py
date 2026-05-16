"""
Data cell formatter for the EREBUS presentation layer.

This module contains formatting helpers used to display raw SQLite values in a
compact and readable way inside the Data page table.
"""

from __future__ import annotations

import re
import textwrap
from datetime import datetime

import presentation.constants as C
from presentation.data.data_table_metadata import DataTableMetadata


class DataCellFormatter:
    """
    Formats raw database values for table display.
    """

    DEFAULT_MAX_CELL_LENGTH = 220
    CELL_HORIZONTAL_PADDING = 10

    def __init__(self, fonts):
        """
        Initializes the formatter.

        Args:
            fonts: Application font catalog.
        """
        self.fonts = fonts

    def format_value(
        self,
        value,
        column_name: str,
        column_width: int,
        table_name: str | None = None,
    ) -> str:
        """
        Formats a raw database value for display.

        Args:
            value: Raw database value.
            column_name: Database column name.
            column_width: Available column width.
            table_name: Optional database table name.

        Returns:
            str: Display-ready value.
        """
        if value is None:
            return C.DATA_EMPTY_VALUE

        text = str(value).strip()

        if not text:
            return C.DATA_EMPTY_VALUE

        if DataTableMetadata.is_datetime(column_name):
            return self._format_datetime_cell(text)

        if DataTableMetadata.is_identifier(column_name):
            return self._format_identifier_cell(text, column_name, column_width)

        if DataTableMetadata.is_ip(column_name):
            return self._format_ip_cell(text, column_width, table_name)

        if DataTableMetadata.is_url(column_name):
            return self._format_url_cell(text, column_width, table_name)

        if DataTableMetadata.is_domain(column_name):
            return self._format_domain_cell(text, column_width)

        if DataTableMetadata.is_large_text(column_name):
            return self._format_large_text_cell(text, column_width, table_name)

        max_length = DataTableMetadata.get_max_cell_length(
            column_name=column_name,
            table_name=table_name,
            default_length=self.DEFAULT_MAX_CELL_LENGTH,
        )

        if len(text) > max_length:
            text = text[:max_length] + "..."

        return self.split_text_to_max_lines(
            text=text,
            column_width=column_width,
            max_lines=DataTableMetadata.get_max_lines(column_name, table_name),
        )

    def raw_value_to_text(self, value) -> str:
        """
        Converts a raw database value to a safe single-line text.

        Args:
            value: Raw database value.

        Returns:
            str: Text value.
        """
        if value is None:
            return C.DATA_EMPTY_VALUE

        text = str(value).strip()

        if not text:
            return C.DATA_EMPTY_VALUE

        return " ".join(text.split())

    def split_header_text(self, text: str, column_width: int) -> str:
        """
        Splits a header text into at most two lines.

        Args:
            text: Header text.
            column_width: Available column width.

        Returns:
            str: Display-ready header text.
        """
        return self.split_text_to_max_lines(
            text=text,
            column_width=column_width,
            max_lines=2,
        )

    def split_text_to_max_lines(
        self,
        text: str,
        column_width: int,
        max_lines: int,
    ) -> str:
        """
        Splits a text into a maximum number of lines according to available width.

        Args:
            text: Text to split.
            column_width: Available column width.
            max_lines: Maximum number of visual lines.

        Returns:
            str: Text split into multiple lines.
        """
        if "\n" in text:
            return self.limit_to_max_lines(text, max_lines)

        max_characters = self.estimate_characters_per_line(column_width)

        if len(text) <= max_characters:
            return text

        wrapped = textwrap.wrap(
            text,
            width=max(6, max_characters),
            break_long_words=True,
            break_on_hyphens=True,
        )

        return self.limit_to_max_lines(
            text="\n".join(wrapped),
            max_lines=max_lines,
        )

    def estimate_characters_per_line(self, column_width: int) -> int:
        """
        Estimates how many characters fit in one line.

        Args:
            column_width: Available column width.

        Returns:
            int: Estimated character count.
        """
        try:
            font_size = abs(int(self.fonts["small"].cget("size")))
        except Exception:
            font_size = 13

        usable_width = max(
            1,
            column_width - (self.CELL_HORIZONTAL_PADDING * 2),
        )

        estimated_character_width = max(1, font_size * 0.78)
        return max(4, int(usable_width / estimated_character_width))

    def estimate_text_width(self, text: str, bold: bool = False) -> int:
        """
        Estimates text width in pixels.

        Args:
            text: Text to measure.
            bold: Whether to use the bold table font.

        Returns:
            int: Estimated text width.
        """
        font = self.fonts["small_bold"] if bold else self.fonts["small"]

        try:
            return int(font.measure(str(text)))
        except Exception:
            pass

        try:
            font_size = abs(int(font.cget("size")))
        except Exception:
            font_size = 13

        return int(len(str(text)) * font_size * 0.78)

    def limit_to_max_lines(self, text: str, max_lines: int) -> str:
        """
        Limits a multiline string to the requested number of visual lines.

        Args:
            text: Multiline text.
            max_lines: Maximum number of allowed lines.

        Returns:
            str: Text with at most the requested number of lines.
        """
        lines = [line for line in text.splitlines() if line]

        if not lines:
            return C.DATA_EMPTY_VALUE

        if len(lines) <= max_lines:
            return "\n".join(lines)

        visible_lines = lines[:max_lines]

        if max_lines == 1:
            return self._truncate_text(visible_lines[0], self.DEFAULT_MAX_CELL_LENGTH)

        remaining_text = " ".join(lines[max_lines - 1:])
        visible_lines[-1] = self._truncate_text(
            remaining_text,
            self.DEFAULT_MAX_CELL_LENGTH // 2,
        )

        return "\n".join(visible_lines)

    def _truncate_text(self, text: str, max_length: int) -> str:
        """
        Truncates text if it exceeds the provided length.

        Args:
            text: Text to truncate.
            max_length: Maximum allowed length.

        Returns:
            str: Truncated text.
        """
        if len(text) <= max_length:
            return text

        return text[:max_length] + "..."

    def _format_datetime_cell(self, text: str) -> str:
        """
        Formats ISO-like datetime strings into two clean lines.

        Args:
            text: Raw datetime text.

        Returns:
            str: Formatted datetime text.
        """
        cleaned = text.strip()

        try:
            normalized = cleaned.replace("Z", "+00:00")
            value = datetime.fromisoformat(normalized)
            return value.strftime("%Y-%m-%d\n%H:%M:%S")
        except Exception:
            pass

        if "T" in cleaned:
            date_part, time_part = cleaned.split("T", 1)
            time_part = time_part.split("+", 1)[0]
            time_part = time_part.split(".", 1)[0]
            return f"{date_part}\n{time_part}"

        return self.split_text_to_max_lines(
            text=cleaned,
            column_width=160,
            max_lines=2,
        )

    def _format_identifier_cell(
        self,
        text: str,
        column_name: str,
        column_width: int,
    ) -> str:
        """
        Formats identifier-like values.

        Args:
            text: Identifier text.
            column_name: Database column name.
            column_width: Available column width.

        Returns:
            str: Display identifier.
        """
        if column_name == "id" and text.isdigit():
            return text

        if column_name in {"id", "execution_id"}:
            if self._looks_like_execution_style_id(text):
                return self._format_execution_style_id(text)

            if self._looks_like_uuid(text):
                return self._format_uuid_like_id(text)

        return self.split_text_to_max_lines(
            text=text,
            column_width=column_width,
            max_lines=2,
        )

    def _looks_like_execution_style_id(self, text: str) -> bool:
        """
        Checks whether a text looks like a domain_date_time execution id.

        Args:
            text: Identifier text.

        Returns:
            bool: True if the text looks like a readable execution id.
        """
        parts = [part for part in text.split("_") if part]

        if len(parts) < 3:
            return False

        return self._has_compact_datetime_tail(parts)

    def _has_compact_datetime_tail(self, parts: list[str]) -> bool:
        """
        Checks compact date/time execution id tails.

        Args:
            parts: Identifier parts split by underscore.

        Returns:
            bool: True if the tail is compact date/time.
        """
        if len(parts) >= 4:
            date_part = parts[-3]
            time_part = parts[-2]
            suffix_part = parts[-1]

            if (
                date_part.isdigit()
                and len(date_part) == 8
                and time_part.isdigit()
                and len(time_part) == 6
                and suffix_part.isdigit()
            ):
                return True

        if len(parts) >= 3:
            date_part = parts[-2]
            time_part = parts[-1]

            if (
                date_part.isdigit()
                and len(date_part) == 8
                and time_part.isdigit()
                and len(time_part) == 6
            ):
                return True

        return False

    def _format_execution_style_id(self, text: str) -> str:
        """
        Formats execution ids into two lines.

        The first line contains the normalized domain. The second line contains
        the date and time part.

        Args:
            text: Execution-style identifier.

        Returns:
            str: Multiline identifier.
        """
        parts = [part for part in text.split("_") if part]

        has_suffix = (
            len(parts) >= 4
            and parts[-3].isdigit()
            and len(parts[-3]) == 8
            and parts[-2].isdigit()
            and len(parts[-2]) == 6
            and parts[-1].isdigit()
        )

        if has_suffix:
            domain_part = "_".join(parts[:-3])
            date_time_part = "_".join(parts[-3:])
            return f"{domain_part}\n{date_time_part}"

        domain_part = "_".join(parts[:-2])
        date_time_part = "_".join(parts[-2:])

        return f"{domain_part}\n{date_time_part}"

    def _looks_like_uuid(self, text: str) -> bool:
        """
        Checks whether a text looks like a UUID.

        Args:
            text: Identifier text.

        Returns:
            bool: True if it matches a UUID-like pattern.
        """
        return bool(
            re.fullmatch(
                (
                    r"[0-9a-fA-F]{8}-"
                    r"[0-9a-fA-F]{4}-"
                    r"[0-9a-fA-F]{4}-"
                    r"[0-9a-fA-F]{4}-"
                    r"[0-9a-fA-F]{12}"
                ),
                text,
            )
        )

    def _format_uuid_like_id(self, text: str) -> str:
        """
        Formats UUID-like identifiers into several lines.

        Args:
            text: UUID-like identifier.

        Returns:
            str: Multiline UUID.
        """
        parts = text.split("-")

        if len(parts) != 5:
            return text

        return "\n".join(
            [
                parts[0],
                f"{parts[1]}-{parts[2]}",
                f"{parts[3]}-{parts[4]}",
            ]
        )

    def _format_ip_cell(
        self,
        text: str,
        column_width: int,
        table_name: str | None,
    ) -> str:
        """
        Formats IP values.

        Args:
            text: IP value.
            column_width: Available column width.
            table_name: Optional database table name.

        Returns:
            str: Display IP value.
        """
        return self.split_text_to_max_lines(
            text=text,
            column_width=column_width,
            max_lines=DataTableMetadata.get_max_lines("ip", table_name),
        )

    def _format_url_cell(
        self,
        text: str,
        column_width: int,
        table_name: str | None,
    ) -> str:
        """
        Formats URL-like values.

        Args:
            text: URL text.
            column_width: Available column width.
            table_name: Optional database table name.

        Returns:
            str: Display URL.
        """
        max_length = DataTableMetadata.get_max_cell_length(
            column_name="url",
            table_name=table_name,
            default_length=self.DEFAULT_MAX_CELL_LENGTH,
        )

        if len(text) > max_length:
            text = text[:max_length] + "..."

        return self.split_text_to_max_lines(
            text=text,
            column_width=column_width,
            max_lines=DataTableMetadata.get_max_lines("url", table_name),
        )

    def _format_domain_cell(self, text: str, column_width: int) -> str:
        """
        Formats domain-like values into readable lines.

        Args:
            text: Domain text.
            column_width: Available column width.

        Returns:
            str: Display domain.
        """
        return self.split_text_to_max_lines(
            text=text,
            column_width=column_width,
            max_lines=2,
        )

    def _format_large_text_cell(
        self,
        text: str,
        column_width: int,
        table_name: str | None,
    ) -> str:
        """
        Formats large text fields into a preview.

        Args:
            text: Raw text.
            column_width: Available column width.
            table_name: Optional database table name.

        Returns:
            str: Display text.
        """
        max_length = DataTableMetadata.get_max_cell_length(
            column_name="value",
            table_name=table_name,
            default_length=self.DEFAULT_MAX_CELL_LENGTH,
        )

        if len(text) > max_length:
            text = text[:max_length] + "..."

        return self.split_text_to_max_lines(
            text=text,
            column_width=column_width,
            max_lines=DataTableMetadata.get_max_lines("value", table_name),
        )