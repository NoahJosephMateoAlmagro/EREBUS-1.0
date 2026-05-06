"""
Results page for the EREBUS graphical interface.

This page presents a clean summary of the latest execution, including the final
status, active modules and the most important findings. It intentionally avoids
showing raw errors or console-level debug information.
"""

from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

import presentation.constants as C
from presentation.widgets.cards import create_card


class ResultsPage(ctk.CTkFrame):
    """
    Page used to present the latest execution summary.
    """

    STATUS_BADGE_WIDTH = 170
    STATUS_BADGE_HEIGHT = 32

    def __init__(self, parent, fonts):
        """
        Initializes the results page.

        Args:
            parent: Parent widget.
            fonts: Application font catalog.
        """
        super().__init__(parent, corner_radius=0)

        self.fonts = fonts

        self.results_scroll = None
        self.header_card = None
        self.modules_card = None
        self.highlights_card = None
        self.modules_container = None
        self.highlights_container = None
        self.empty_label = None

        self.status_badge_info = None
        self.info_blocks = []
        self.highlight_tiles = []
        self.module_rows = []
        self.module_status_badges = []

        self.current_palette = None

        self._build()

    def _build(self) -> None:
        """
        Builds the results page layout.
        """
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.results_scroll = ctk.CTkScrollableFrame(
            self,
            corner_radius=0,
        )
        self.results_scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.results_scroll.grid_columnconfigure(0, weight=1)

        self._build_empty_state()

    def _reset_theme_targets(self) -> None:
        """
        Clears all cached widgets that receive explicit theme updates.
        """
        self.status_badge_info = None
        self.info_blocks = []
        self.highlight_tiles = []
        self.module_rows = []
        self.module_status_badges = []

    def _build_empty_state(self) -> None:
        """
        Builds the initial empty state shown before any execution summary exists.
        """
        self._reset_theme_targets()

        card = create_card(self.results_scroll, row=0)
        self.header_card = card
        card.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            card,
            text=C.RESULTS_TITLE,
            font=self.fonts["section"],
        )
        title.grid(row=0, column=0, sticky="w", padx=24, pady=(22, 8))

        self.empty_label = ctk.CTkLabel(
            card,
            text=C.RESULTS_EMPTY_TEXT,
            font=self.fonts["body"],
            justify="left",
        )
        self.empty_label.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 22))

    def render_summary(self, summary: dict) -> None:
        """
        Renders a new execution summary.

        Args:
            summary: Structured summary dictionary built for the UI.
        """
        for child in self.results_scroll.winfo_children():
            child.destroy()

        self._reset_theme_targets()

        self._build_header_card(summary)
        self._build_highlights_card(summary)
        self._build_modules_card(summary)

        # Reapply theme after recreating all widgets.
        if self.current_palette:
            self.apply_theme(self.current_palette)

    def _build_header_card(self, summary: dict) -> None:
        """
        Builds the main execution summary card.

        Args:
            summary: Structured summary dictionary.
        """
        self.header_card = create_card(self.results_scroll, row=0)
        self.header_card.grid_columnconfigure(0, weight=1)
        self.header_card.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            self.header_card,
            text=C.RESULTS_LATEST_EXECUTION_TITLE,
            font=self.fonts["section"],
        )
        title.grid(row=0, column=0, sticky="w", padx=24, pady=(22, 8))

        execution_status = summary.get("status", C.RESULTS_STATUS_UNKNOWN)

        status_badge = ctk.CTkLabel(
            self.header_card,
            text=f"{C.RESULTS_STATUS_PREFIX} {execution_status}",
            font=self.fonts["small_bold"],
            corner_radius=10,
            width=self.STATUS_BADGE_WIDTH,
            height=self.STATUS_BADGE_HEIGHT,
            anchor="center",
        )
        status_badge.grid(row=0, column=1, sticky="e", padx=24, pady=(22, 8))

        self.status_badge_info = {
            "widget": status_badge,
            "status": execution_status,
        }

        info_frame = ctk.CTkFrame(self.header_card, fg_color="transparent")
        info_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=24, pady=(0, 14))
        info_frame.grid_columnconfigure((0, 1), weight=1)

        self._add_info_block(
            info_frame,
            row=0,
            column=0,
            title=C.RESULTS_LABEL_TARGET,
            value=str(summary.get("target", C.RESULTS_VALUE_EMPTY)),
        )

        self._add_info_block(
            info_frame,
            row=0,
            column=1,
            title=C.RESULTS_LABEL_STARTED_AT,
            value=self._format_datetime(summary.get("started_at")),
        )

        self._add_info_block(
            info_frame,
            row=1,
            column=0,
            title=C.RESULTS_LABEL_DURATION,
            value=self._format_duration(summary.get("total_duration_seconds", 0)),
        )

        active_modules = summary.get("active_modules", [])
        active_names = ", ".join(item["title"] for item in active_modules) or C.RESULTS_VALUE_EMPTY

        self._add_info_block(
            info_frame,
            row=1,
            column=1,
            title=C.RESULTS_LABEL_ACTIVE_MODULES,
            value=active_names,
        )

    def _build_highlights_card(self, summary: dict) -> None:
        """
        Builds the global highlights card.

        Args:
            summary: Structured summary dictionary.
        """
        self.highlights_card = create_card(self.results_scroll, row=1)
        self.highlights_card.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self.highlights_card,
            text=C.RESULTS_FINDINGS_TITLE,
            font=self.fonts["section"],
        )
        title.grid(row=0, column=0, sticky="w", padx=24, pady=(22, 10))

        self.highlights_container = ctk.CTkFrame(
            self.highlights_card,
            fg_color="transparent",
        )
        self.highlights_container.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 22))
        self.highlights_container.grid_columnconfigure((0, 1, 2), weight=1)

        highlights = summary.get("global_highlights", [])

        if not highlights:
            empty = ctk.CTkLabel(
                self.highlights_container,
                text=C.RESULTS_NO_FINDINGS_TEXT,
                font=self.fonts["body"],
            )
            empty.grid(row=0, column=0, sticky="w")
            return

        for index, item in enumerate(highlights):
            row = index // 3
            column = index % 3

            tile = ctk.CTkFrame(self.highlights_container, corner_radius=10)
            tile.grid(row=row, column=column, sticky="ew", padx=8, pady=8)
            tile.grid_columnconfigure(0, weight=1)

            self.highlight_tiles.append(tile)

            label = ctk.CTkLabel(
                tile,
                text=item["label"],
                font=self.fonts["small_bold"],
                justify="left",
            )
            label.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))

            value = ctk.CTkLabel(
                tile,
                text=str(item["value"]),
                font=self.fonts["section"],
                justify="left",
            )
            value.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))

    def _build_modules_card(self, summary: dict) -> None:
        """
        Builds the per-module summary card.

        Args:
            summary: Structured summary dictionary.
        """
        self.modules_card = create_card(self.results_scroll, row=2)
        self.modules_card.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self.modules_card,
            text=C.RESULTS_MODULE_SUMMARY_TITLE,
            font=self.fonts["section"],
        )
        title.grid(row=0, column=0, sticky="w", padx=24, pady=(22, 10))

        self.modules_container = ctk.CTkFrame(
            self.modules_card,
            fg_color="transparent",
        )
        self.modules_container.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 22))
        self.modules_container.grid_columnconfigure(0, weight=1)

        module_cards = summary.get("module_cards", [])

        if not module_cards:
            empty = ctk.CTkLabel(
                self.modules_container,
                text=C.RESULTS_NO_MODULE_RESULTS_TEXT,
                font=self.fonts["body"],
            )
            empty.grid(row=0, column=0, sticky="w")
            return

        for row, item in enumerate(module_cards):
            self._build_module_row(self.modules_container, row, item)

    def _build_module_row(self, parent, row: int, item: dict) -> None:
        """
        Builds one module summary row.

        Args:
            parent: Parent frame.
            row: Grid row.
            item: Module summary dictionary.
        """
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.grid(row=row, column=0, sticky="ew", pady=8)
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=0)

        self.module_rows.append(card)

        title = ctk.CTkLabel(
            card,
            text=item.get("title", item.get("module_key", "module")),
            font=self.fonts["module_title"],
        )
        title.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 4))

        module_status = item.get("status", C.RESULTS_STATUS_UNKNOWN)

        status_badge = ctk.CTkLabel(
            card,
            text=f"{C.RESULTS_STATUS_PREFIX} {module_status}",
            font=self.fonts["small_bold"],
            corner_radius=10,
            width=self.STATUS_BADGE_WIDTH,
            height=self.STATUS_BADGE_HEIGHT,
            anchor="center",
        )
        status_badge.grid(row=0, column=1, sticky="e", padx=18, pady=(14, 4))

        self.module_status_badges.append(
            {
                "widget": status_badge,
                "status": module_status,
            }
        )

        duration = ctk.CTkLabel(
            card,
            text=f"{C.RESULTS_DURATION_PREFIX} {self._format_duration(item.get('duration_seconds', 0))}",
            font=self.fonts["small"],
        )
        duration.grid(row=1, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 8))

        highlights = item.get("highlights", [])

        if not highlights:
            empty = ctk.CTkLabel(
                card,
                text=C.RESULTS_NO_MODULE_FINDINGS_TEXT,
                font=self.fonts["small"],
            )
            empty.grid(row=2, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 14))
            return

        highlights_text = " · ".join(
            f"{entry['label']}: {entry['value']}"
            for entry in highlights
        )

        body = ctk.CTkLabel(
            card,
            text=highlights_text,
            font=self.fonts["small"],
            wraplength=950,
            justify="left",
        )
        body.grid(row=2, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 14))

    def _add_info_block(self, parent, row: int, column: int, title: str, value: str) -> None:
        """
        Adds a small information block to the header card.

        Args:
            parent: Parent frame.
            row: Grid row.
            column: Grid column.
            title: Block title.
            value: Block value.
        """
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, sticky="ew", padx=8, pady=8)

        self.info_blocks.append(wrapper)

        title_label = ctk.CTkLabel(
            wrapper,
            text=title,
            font=self.fonts["small_bold"],
        )
        title_label.grid(row=0, column=0, sticky="w")

        value_label = ctk.CTkLabel(
            wrapper,
            text=value,
            font=self.fonts["body"],
            justify="left",
            wraplength=450,
        )
        value_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

    def _normalize_status(self, status_value: str) -> str:
        """
        Normalizes a module or execution status string.

        Args:
            status_value: Raw status value.

        Returns:
            str: Normalized status.
        """
        text = str(status_value or "").strip().upper()

        if text.startswith("MODULESTATUS."):
            text = text.split(".", 1)[1]

        return text

    def _get_status_badge_colors(self, palette: dict, status_value: str) -> tuple[str, str]:
        """
        Resolves badge background and text color according to status.

        Args:
            palette: Active theme palette.
            status_value: Raw or normalized status.

        Returns:
            tuple[str, str]: Background color and text color.
        """
        normalized = self._normalize_status(status_value)

        if normalized == "FAILED":
            return palette["status_failed_bg"], palette["status_failed_text"]

        if normalized == "PARTIAL":
            return palette["status_partial_bg"], palette["status_partial_text"]

        if normalized == "SUCCESS":
            return palette["status_success_bg"], palette["status_success_text"]

        # SKIPPED vuelve al azul anterior:
        # fondo azul "soft" y texto con el color principal como antes.
        if normalized == "SKIPPED":
            return palette["soft"], palette["primary"]

        return palette["status_unknown_bg"], palette["status_unknown_text"]

    def _format_datetime(self, value) -> str:
        """
        Formats a datetime value for display.

        Args:
            value: Datetime value or None.

        Returns:
            str: Formatted datetime string.
        """
        if isinstance(value, datetime):
            return value.strftime(f"%Y-%m-%d %H:%M:%S {C.RESULTS_UTC_SUFFIX}")

        return C.RESULTS_VALUE_EMPTY

    def _format_duration(self, seconds: float | int) -> str:
        """
        Formats a duration in seconds.

        Args:
            seconds: Duration in seconds.

        Returns:
            str: Human-readable duration string.
        """
        try:
            return C.RESULTS_DURATION_FORMAT.format(seconds=float(seconds))
        except Exception:
            return C.RESULTS_VALUE_EMPTY

    def apply_theme(self, palette: dict) -> None:
        """
        Applies the active theme to the results page.

        Args:
            palette: Active theme palette.
        """
        self.current_palette = palette

        self.configure(fg_color=palette["panel"])

        if self.results_scroll:
            self.results_scroll.configure(fg_color=palette["panel"])

        for card_widget in [
            self.header_card,
            self.highlights_card,
            self.modules_card,
        ]:
            if card_widget:
                card_widget.configure(fg_color=palette["card"])

        for block in self.info_blocks:
            block.configure(fg_color="transparent")

        for tile in self.highlight_tiles:
            tile.configure(fg_color=palette["soft"])

        for row_card in self.module_rows:
            row_card.configure(fg_color=palette["soft"])

        if self.status_badge_info:
            widget = self.status_badge_info["widget"]
            status_value = self.status_badge_info["status"]
            bg_color, text_color = self._get_status_badge_colors(palette, status_value)

            widget.configure(
                fg_color=bg_color,
                text_color=text_color,
            )

        for badge_info in self.module_status_badges:
            widget = badge_info["widget"]
            status_value = badge_info["status"]
            bg_color, text_color = self._get_status_badge_colors(palette, status_value)

            widget.configure(
                fg_color=bg_color,
                text_color=text_color,
            )