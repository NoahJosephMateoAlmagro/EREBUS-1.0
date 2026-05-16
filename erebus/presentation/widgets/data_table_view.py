"""
Reusable data table widget for the EREBUS presentation layer.

This widget renders read-only database rows inside a canvas-based table view.
It supports horizontal and vertical scrollbars, loading overlay, fixed viewport
height and display formatting for long database values.

Mouse wheel scrolling is intentionally not handled here. The table should be
moved using its scrollbars so it does not conflict with the outer page scroll.
"""

from __future__ import annotations

import time
import tkinter as tk

import customtkinter as ctk

import presentation.constants as C
from presentation.data.data_cell_formatter import DataCellFormatter
from presentation.data.data_table_metadata import DataTableMetadata


class DataTableView(ctk.CTkFrame):
    """
    Read-only table widget used by the Data page.
    """

    CELL_HORIZONTAL_PADDING = 10
    CELL_VERTICAL_PADDING = 9

    TABLE_MAX_VIEWPORT_HEIGHT = 560
    TABLE_MIN_VIEWPORT_HEIGHT = 140
    WIDTH_CHANGE_THRESHOLD = 12

    MIN_LOADING_VISIBLE_MS = 350

    def __init__(self, parent, fonts):
        """
        Initializes the table widget.

        Args:
            parent: Parent widget.
            fonts: Application font catalog.
        """
        super().__init__(parent, corner_radius=0, fg_color="transparent")

        self.fonts = fonts
        self.formatter = DataCellFormatter(fonts)

        self.current_palette = None
        self.last_page_data = None

        self.table_canvas = None
        self.table_canvas_window = None
        self.horizontal_scrollbar = None
        self.vertical_scrollbar = None
        self.rows_container = None

        self.loading_overlay = None
        self.loading_label = None
        self.loading_started_at = 0.0
        self.pending_hide_loading_id = None

        self.rendered_frames = []
        self.rendered_labels = []

        self._build()

    def _build(self) -> None:
        """
        Builds the base table layout.
        """
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self._build_canvas()

    def _build_canvas(self) -> None:
        """
        Builds the canvas and scrollbars used by the table.
        """
        self._clear_children()

        self.rendered_frames = []
        self.rendered_labels = []

        palette = self._get_palette()

        self.table_canvas = tk.Canvas(
            self,
            borderwidth=0,
            highlightthickness=0,
            bg=palette["card"],
        )
        self.table_canvas.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        self.vertical_scrollbar = ctk.CTkScrollbar(
            self,
            orientation="vertical",
            command=self.table_canvas.yview,
        )

        self.horizontal_scrollbar = ctk.CTkScrollbar(
            self,
            orientation="horizontal",
            command=self.table_canvas.xview,
        )

        self.table_canvas.configure(
            xscrollcommand=self.horizontal_scrollbar.set,
            yscrollcommand=self.vertical_scrollbar.set,
        )

        self.rows_container = ctk.CTkFrame(
            self.table_canvas,
            fg_color=palette["card"],
            corner_radius=0,
        )

        self.table_canvas_window = self.table_canvas.create_window(
            (0, 0),
            window=self.rows_container,
            anchor="nw",
        )

        self.rows_container.bind(
            "<Configure>",
            self._update_canvas_scrollregion,
        )

        self.table_canvas.bind(
            "<Configure>",
            self._on_canvas_configure,
        )

    def _get_palette(self) -> dict:
        """
        Gets the current palette or a safe dark fallback.

        Returns:
            dict: Palette dictionary.
        """
        if self.current_palette:
            return self.current_palette

        return {
            "card": C.COLORS["dark_card"],
            "soft": C.COLORS["dark_soft"],
            "text": C.COLORS["text_light"],
            "muted": C.COLORS["muted"],
            "primary": C.COLORS["accent"],
            "primary_hover": C.COLORS["accent_hover"],
            "secondary_hover": C.COLORS["olive"],
        }

    def _widget_exists(self, widget) -> bool:
        """
        Checks whether a Tkinter widget still exists.

        Args:
            widget: Tkinter or CustomTkinter widget.

        Returns:
            bool: True if the widget exists, False otherwise.
        """
        if widget is None:
            return False

        try:
            return bool(widget.winfo_exists())
        except Exception:
            return False

    def _safe_configure(self, widget, **kwargs) -> None:
        """
        Configures a widget only if it still exists.

        Args:
            widget: Tkinter or CustomTkinter widget.
            **kwargs: Configuration values.
        """
        if not self._widget_exists(widget):
            return

        try:
            widget.configure(**kwargs)
        except tk.TclError:
            pass
        except Exception:
            pass

    def _clear_children(self) -> None:
        """
        Removes all direct child widgets from the table.
        """
        for child in self.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass

    def show_loading(self, table_name: str) -> None:
        """
        Shows a loading overlay above the table.

        Args:
            table_name: Name of the table being loaded.
        """
        self.loading_started_at = time.perf_counter()

        if self.pending_hide_loading_id:
            try:
                self.after_cancel(self.pending_hide_loading_id)
            except Exception:
                pass
            self.pending_hide_loading_id = None

        self._destroy_loading_overlay()

        palette = self._get_palette()

        self.loading_overlay = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=palette["card"],
            border_width=2,
            border_color=palette["primary"],
        )
        self.loading_overlay.place(
            relx=0,
            rely=0,
            relwidth=1,
            relheight=1,
        )
        self.loading_overlay.grid_columnconfigure(0, weight=1)
        self.loading_overlay.grid_rowconfigure(0, weight=1)

        self.loading_label = ctk.CTkLabel(
            self.loading_overlay,
            text=f"Loading {self._format_table_name(table_name)}...",
            font=self.fonts["section"],
            text_color=palette["text"],
        )
        self.loading_label.grid(
            row=0,
            column=0,
            sticky="n",
            pady=72,
        )

        try:
            self.loading_overlay.lift()
            self.update_idletasks()
        except Exception:
            pass

    def hide_loading_when_ready(self) -> None:
        """
        Hides the loading overlay after a minimum visible time.
        """
        if not self._widget_exists(self.loading_overlay):
            self.loading_overlay = None
            self.loading_label = None
            return

        elapsed_ms = int((time.perf_counter() - self.loading_started_at) * 1000)
        remaining_ms = max(0, self.MIN_LOADING_VISIBLE_MS - elapsed_ms)

        self.pending_hide_loading_id = self.after(
            remaining_ms,
            self._hide_loading_now,
        )

    def _hide_loading_now(self) -> None:
        """
        Hides the loading overlay immediately.
        """
        self.pending_hide_loading_id = None
        self._destroy_loading_overlay()

    def _destroy_loading_overlay(self) -> None:
        """
        Destroys the loading overlay if it exists.
        """
        overlay = self.loading_overlay

        self.loading_overlay = None
        self.loading_label = None

        if not self._widget_exists(overlay):
            return

        try:
            overlay.destroy()
        except Exception:
            pass

    def render_page(self, page_data: dict) -> None:
        """
        Renders a paginated table response.

        Args:
            page_data: Page dictionary returned by DataBrowserService.
        """
        self.last_page_data = page_data
        self._build_canvas()

        columns = page_data.get("columns", [])
        rows = page_data.get("rows", [])

        if not columns:
            self.render_message(C.DATA_NO_COLUMNS_TEXT)
            return

        if not rows:
            self.render_message(C.DATA_NO_ROWS_TEXT)
            return

        table_name = page_data.get("table_name")

        column_widths = self._calculate_column_widths(
            columns=columns,
            rows=rows,
            table_name=table_name,
        )

        formatted_rows = self._build_formatted_rows(
            columns=columns,
            rows=rows,
            column_widths=column_widths,
            table_name=table_name,
        )

        self._render_header(columns, column_widths)
        self._render_rows(columns, column_widths, formatted_rows)
        self._update_viewport_after_render()

        self.apply_theme(self._get_palette())

        try:
            self.update_idletasks()
        except Exception:
            pass

    def render_message(self, message: str) -> None:
        """
        Renders a simple message inside the table area.

        Args:
            message: Message to display.
        """
        self._build_canvas()

        palette = self._get_palette()

        label = ctk.CTkLabel(
            self.rows_container,
            text=message,
            font=self.fonts["body"],
            justify="left",
            wraplength=900,
            text_color=palette["text"],
        )
        label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=18,
            pady=18,
        )

        self.rendered_labels.append(label)

        self._update_viewport_after_render()
        self.apply_theme(palette)

    def _render_header(
        self,
        columns: list[str],
        column_widths: list[int],
    ) -> None:
        """
        Renders the table header.

        Args:
            columns: Visible column names.
            column_widths: Calculated column widths.
        """
        palette = self._get_palette()

        header = ctk.CTkFrame(
            self.rows_container,
            corner_radius=8,
            fg_color=palette["soft"],
        )
        header.grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 8),
        )

        self.rendered_frames.append(header)
        self._configure_row_columns(header, column_widths)

        for column_index, column_name in enumerate(columns):
            width = column_widths[column_index]

            label = ctk.CTkLabel(
                header,
                text=self.formatter.split_header_text(column_name, width),
                width=width,
                font=self.fonts["small_bold"],
                anchor=self._get_cell_anchor(column_name),
                justify=self._get_cell_justify(column_name),
                text_color=palette["text"],
            )
            label.grid(
                row=0,
                column=column_index,
                sticky="nsew",
                padx=self.CELL_HORIZONTAL_PADDING,
                pady=10,
            )

            self.rendered_labels.append(label)

    def _render_rows(
        self,
        columns: list[str],
        column_widths: list[int],
        formatted_rows: list[dict],
    ) -> None:
        """
        Renders table rows.

        Args:
            columns: Visible column names.
            column_widths: Calculated column widths.
            formatted_rows: Display-ready row dictionaries.
        """
        palette = self._get_palette()

        for row_index, formatted_row in enumerate(formatted_rows, start=1):
            row_frame = ctk.CTkFrame(
                self.rows_container,
                corner_radius=8,
                fg_color=palette["soft"],
            )
            row_frame.grid(
                row=row_index,
                column=0,
                sticky="w",
                pady=4,
            )

            self.rendered_frames.append(row_frame)
            self._configure_row_columns(row_frame, column_widths)

            for column_index, column_name in enumerate(columns):
                width = column_widths[column_index]

                label = ctk.CTkLabel(
                    row_frame,
                    text=formatted_row[column_name],
                    width=width,
                    font=self.fonts["small"],
                    anchor=self._get_cell_anchor(column_name),
                    justify=self._get_cell_justify(column_name),
                    text_color=palette["text"],
                )
                label.grid(
                    row=0,
                    column=column_index,
                    sticky="nsew",
                    padx=self.CELL_HORIZONTAL_PADDING,
                    pady=self.CELL_VERTICAL_PADDING,
                )

                self.rendered_labels.append(label)

    def _update_canvas_scrollregion(self, event=None) -> None:
        """
        Updates the canvas scroll region according to rendered content.

        Args:
            event: Tkinter configure event.
        """
        if not self._widget_exists(self.table_canvas):
            return

        try:
            self.table_canvas.configure(
                scrollregion=self.table_canvas.bbox("all"),
            )
        except Exception:
            pass

    def _on_canvas_configure(self, event=None) -> None:
        """
        Keeps the table content aligned when it fits horizontally.

        Args:
            event: Tkinter configure event.
        """
        if not self._widget_exists(self.table_canvas):
            return

        if not self.table_canvas_window:
            return

        if not self._widget_exists(self.rows_container):
            return

        try:
            content_width = self.rows_container.winfo_reqwidth()
            canvas_width = self.table_canvas.winfo_width()

            if content_width <= canvas_width:
                self.table_canvas.itemconfigure(
                    self.table_canvas_window,
                    width=max(1, canvas_width),
                )
        except Exception:
            pass

    def _update_viewport_after_render(self) -> None:
        """
        Updates canvas size, scrollbars and scroll region after rendering.
        """
        if not self._widget_exists(self.table_canvas):
            return

        if not self._widget_exists(self.rows_container):
            return

        try:
            self.update_idletasks()
        except Exception:
            pass

        content_width = max(1, self.rows_container.winfo_reqwidth())
        content_height = max(1, self.rows_container.winfo_reqheight())

        viewport_width = self.winfo_width()

        if viewport_width <= 1 and self.master:
            viewport_width = self.master.winfo_width()

        viewport_width = max(420, viewport_width)
        viewport_height = min(
            max(content_height, self.TABLE_MIN_VIEWPORT_HEIGHT),
            self.TABLE_MAX_VIEWPORT_HEIGHT,
        )

        self.table_canvas.configure(
            width=viewport_width,
            height=viewport_height,
            scrollregion=(0, 0, content_width, content_height),
        )

        if self.table_canvas_window:
            self.table_canvas.itemconfigure(
                self.table_canvas_window,
                width=max(content_width, viewport_width),
            )

        if content_width > viewport_width + self.WIDTH_CHANGE_THRESHOLD:
            self.horizontal_scrollbar.grid(
                row=1,
                column=0,
                sticky="ew",
                pady=(8, 0),
            )
        else:
            self.horizontal_scrollbar.grid_remove()

        if content_height > viewport_height + self.WIDTH_CHANGE_THRESHOLD:
            self.vertical_scrollbar.grid(
                row=0,
                column=1,
                sticky="ns",
                padx=(8, 0),
            )
        else:
            self.vertical_scrollbar.grid_remove()

        self.table_canvas.xview_moveto(0)
        self.table_canvas.yview_moveto(0)

    def _calculate_column_widths(
        self,
        columns: list[str],
        rows: list[dict],
        table_name: str | None,
    ) -> list[int]:
        """
        Calculates readable column widths for the current page.

        Args:
            columns: Table columns.
            rows: Current page rows.
            table_name: Current database table name.

        Returns:
            list[int]: Column widths.
        """
        widths = []

        for column_name in columns:
            min_width = DataTableMetadata.get_min_width(column_name, table_name)
            max_width = DataTableMetadata.get_max_width(column_name, table_name)
            max_length = DataTableMetadata.get_max_cell_length(
                column_name=column_name,
                table_name=table_name,
                default_length=self.formatter.DEFAULT_MAX_CELL_LENGTH,
            )

            measured_width = self.formatter.estimate_text_width(
                column_name,
                bold=True,
            )

            for row in rows:
                text = self.formatter.raw_value_to_text(row.get(column_name))

                if len(text) > max_length:
                    text = text[:max_length] + "..."

                measured_width = max(
                    measured_width,
                    self.formatter.estimate_text_width(text),
                )

            width = measured_width + (self.CELL_HORIZONTAL_PADDING * 2)
            width = max(min_width, width)
            width = min(max_width, width)

            widths.append(width)

        return widths

    def _build_formatted_rows(
        self,
        columns: list[str],
        rows: list[dict],
        column_widths: list[int],
        table_name: str | None,
    ) -> list[dict]:
        """
        Builds display-ready row dictionaries.

        Args:
            columns: Table columns.
            rows: Raw rows.
            column_widths: Calculated column widths.
            table_name: Current database table name.

        Returns:
            list[dict]: Formatted rows.
        """
        formatted_rows = []

        for row in rows:
            formatted_row = {}

            for index, column_name in enumerate(columns):
                formatted_row[column_name] = self.formatter.format_value(
                    value=row.get(column_name),
                    column_name=column_name,
                    column_width=column_widths[index],
                    table_name=table_name,
                )

            formatted_rows.append(formatted_row)

        return formatted_rows

    def _configure_row_columns(
        self,
        frame: ctk.CTkFrame,
        column_widths: list[int],
    ) -> None:
        """
        Configures fixed grid widths for one row frame.

        Args:
            frame: Row frame.
            column_widths: Calculated column widths.
        """
        for column_index, width in enumerate(column_widths):
            frame.grid_columnconfigure(
                column_index,
                weight=0,
                minsize=width + (self.CELL_HORIZONTAL_PADDING * 2),
            )

    def _get_cell_anchor(self, column_name: str) -> str:
        """
        Gets text anchor for a cell.

        Args:
            column_name: Column name.

        Returns:
            str: Tkinter anchor.
        """
        if DataTableMetadata.is_centered(column_name):
            return "center"

        return "w"

    def _get_cell_justify(self, column_name: str) -> str:
        """
        Gets text justification for a cell.

        Args:
            column_name: Column name.

        Returns:
            str: Tkinter justification.
        """
        if DataTableMetadata.is_centered(column_name):
            return "center"

        return "left"

    def _format_table_name(self, table_name: str) -> str:
        """
        Formats a table name for display.

        Args:
            table_name: Raw table name.

        Returns:
            str: Display table name.
        """
        return table_name.replace("_", " ").title()

    def apply_theme(self, palette: dict) -> None:
        """
        Applies the active theme to the table widget.

        Args:
            palette: Active theme palette.
        """
        self.current_palette = palette

        self._safe_configure(self, fg_color="transparent")

        if self._widget_exists(self.table_canvas):
            try:
                self.table_canvas.configure(
                    bg=palette["card"],
                    highlightthickness=0,
                )
            except Exception:
                pass

        self._safe_configure(
            self.rows_container,
            fg_color=palette["card"],
        )

        self._safe_configure(
            self.horizontal_scrollbar,
            fg_color=palette["soft"],
            button_color=palette["primary"],
            button_hover_color=palette["primary_hover"],
        )

        self._safe_configure(
            self.vertical_scrollbar,
            fg_color=palette["soft"],
            button_color=palette["primary"],
            button_hover_color=palette["primary_hover"],
        )

        for frame in list(self.rendered_frames):
            self._safe_configure(frame, fg_color=palette["soft"])

        for label in list(self.rendered_labels):
            self._safe_configure(label, text_color=palette["text"])

        if self._widget_exists(self.loading_overlay):
            self._safe_configure(
                self.loading_overlay,
                fg_color=palette["card"],
                border_color=palette["primary"],
            )
        else:
            self.loading_overlay = None
            self.loading_label = None

        self._safe_configure(
            self.loading_label,
            text_color=palette["text"],
        )