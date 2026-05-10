"""
Data page for the EREBUS graphical interface.

This page allows the user to inspect the information stored in the SQLite
database. It provides an internal table selector, a domain filter and a
read-only tabular view of the selected table.
"""

from __future__ import annotations

import customtkinter as ctk

import presentation.constants as C
from presentation.services.data_browser_service import DataBrowserService
from presentation.widgets.cards import create_card


class DataPage(ctk.CTkFrame):
    """
    Page used to browse stored EREBUS database information.
    """

    MAX_CELL_LENGTH = 120

    def __init__(self, parent, fonts):
        """
        Initializes the data page.

        Args:
            parent: Parent widget.
            fonts: Application font catalog.
        """
        super().__init__(parent, corner_radius=0)

        self.fonts = fonts
        self.database_service = DataBrowserService()

        self.current_palette = None
        self.current_table = None

        self.data_scroll = None
        self.header_card = None
        self.table_tabs_card = None
        self.table_card = None

        self.description_textbox = None
        self.domain_entry = None
        self.refresh_button = None
        self.status_label = None

        self.table_buttons = {}
        self.table_container = None
        self.rows_container = None

        self._build()

    def _build(self) -> None:
        """
        Builds the data page layout.
        """
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.data_scroll = ctk.CTkScrollableFrame(
            self,
            corner_radius=0,
        )
        self.data_scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.data_scroll.grid_columnconfigure(0, weight=1)

        self._build_header_card()
        self._build_table_tabs_card()
        self._build_table_card()

        self.refresh_tables()

    def _build_header_card(self) -> None:
        """
        Builds the header and filter card.
        """
        self.header_card = create_card(self.data_scroll, row=0)
        self.header_card.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self.header_card,
            text=C.DATA_TITLE,
            font=self.fonts["section"],
        )
        title.grid(
            row=0,
            column=0,
            sticky="w",
            padx=24,
            pady=(22, 8),
        )

        self.description_textbox = ctk.CTkTextbox(
            self.header_card,
            height=self._get_description_height(),
            font=self.fonts["body"],
            wrap="word",
            corner_radius=0,
            border_width=0,
            activate_scrollbars=False,
        )
        self.description_textbox.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=24,
            pady=(0, 18),
        )
        self._set_description_text(C.DATA_DESCRIPTION)

        filter_frame = ctk.CTkFrame(
            self.header_card,
            fg_color="transparent",
        )
        filter_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=24,
            pady=(0, 22),
        )
        filter_frame.grid_columnconfigure(0, weight=0)
        filter_frame.grid_columnconfigure(1, weight=1)
        filter_frame.grid_columnconfigure(2, weight=0)

        label = ctk.CTkLabel(
            filter_frame,
            text=C.DATA_DOMAIN_FILTER_LABEL,
            font=self.fonts["body_bold"],
        )
        label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 14),
        )

        self.domain_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text="example.com",
            height=42,
            font=self.fonts["body"],
        )
        self.domain_entry.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(0, 14),
        )
        self.domain_entry.bind(
            "<Return>",
            lambda _event: self.reload_current_table(),
        )

        self.refresh_button = ctk.CTkButton(
            filter_frame,
            text=C.DATA_REFRESH_BUTTON,
            width=150,
            height=42,
            corner_radius=6,
            font=self.fonts["button"],
            command=self.reload_current_table,
        )
        self.refresh_button.grid(
            row=0,
            column=2,
            sticky="e",
        )

        self.status_label = ctk.CTkLabel(
            self.header_card,
            text=C.DATA_STATUS_READY,
            font=self.fonts["small_bold"],
        )
        self.status_label.grid(
            row=3,
            column=0,
            sticky="w",
            padx=24,
            pady=(0, 18),
        )

    def _set_description_text(self, text: str) -> None:
        """
        Writes the description text into the read-only description textbox.

        Args:
            text: Description text.
        """
        if not self.description_textbox:
            return

        self.description_textbox.configure(state="normal")
        self.description_textbox.delete("1.0", "end")
        self.description_textbox.insert("1.0", text)
        self.description_textbox.configure(state="disabled")

    def _get_description_height(self) -> int:
        """
        Calculates a safe description textbox height for the current body font.

        Returns:
            int: Textbox height in pixels.
        """
        try:
            font_size = abs(int(self.fonts["body"].cget("size")))
        except Exception:
            font_size = 14

        return max(54, int(font_size * 4.4))

    def _configure_description_textbox(self, palette: dict) -> None:
        """
        Applies theme and size settings to the description textbox.

        Args:
            palette: Active theme palette.
        """
        if not self.description_textbox:
            return

        self.description_textbox.configure(
            height=self._get_description_height(),
            fg_color=palette["card"],
            text_color=palette["text"],
            border_width=0,
        )

        try:
            self.description_textbox._textbox.configure(
                padx=0,
                pady=0,
                borderwidth=0,
                highlightthickness=0,
            )
        except AttributeError:
            pass

    def _build_table_tabs_card(self) -> None:
        """
        Builds the internal table selector card.
        """
        self.table_tabs_card = create_card(self.data_scroll, row=1)
        self.table_tabs_card.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self.table_tabs_card,
            text=C.DATA_TABLES_TITLE,
            font=self.fonts["section"],
        )
        title.grid(
            row=0,
            column=0,
            sticky="w",
            padx=24,
            pady=(22, 10),
        )

        self.table_container = ctk.CTkFrame(
            self.table_tabs_card,
            fg_color="transparent",
        )
        self.table_container.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=24,
            pady=(0, 22),
        )

    def _build_table_card(self) -> None:
        """
        Builds the table content card.
        """
        self.table_card = create_card(self.data_scroll, row=2)
        self.table_card.grid_columnconfigure(0, weight=1)

        self.rows_container = ctk.CTkFrame(
            self.table_card,
            fg_color="transparent",
        )
        self.rows_container.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=24,
            pady=24,
        )
        self.rows_container.grid_columnconfigure(0, weight=1)

    def refresh_tables(self) -> None:
        """
        Reloads available database tables and rebuilds the internal tabs.
        """
        for child in self.table_container.winfo_children():
            child.destroy()

        self.table_buttons.clear()

        table_names = self.database_service.get_table_names()

        if not table_names:
            self.current_table = None
            self._set_status(C.DATA_STATUS_NO_DATABASE)
            self._render_message(C.DATA_NO_DATABASE_TEXT)
            return

        for index, table_name in enumerate(table_names):
            button = ctk.CTkButton(
                self.table_container,
                text=self._format_table_name(table_name),
                height=38,
                corner_radius=8,
                font=self.fonts["small_bold"],
                command=lambda name=table_name: self.select_table(name),
            )
            button.grid(
                row=index // 4,
                column=index % 4,
                sticky="ew",
                padx=6,
                pady=6,
            )

            self.table_container.grid_columnconfigure(index % 4, weight=1)
            self.table_buttons[table_name] = button

        self.select_table(table_names[0])

    def select_table(self, table_name: str) -> None:
        """
        Selects one database table and renders its rows.

        Args:
            table_name: Selected database table.
        """
        self.current_table = table_name
        self._sync_table_buttons()
        self.reload_current_table()

    def reload_current_table(self) -> None:
        """
        Reloads the currently selected table using the active domain filter.
        """
        if not self.current_table:
            self._render_message(C.DATA_NO_TABLE_SELECTED_TEXT)
            return

        domain_filter = self.domain_entry.get().strip() if self.domain_entry else ""

        columns, rows = self.database_service.fetch_table_rows(
            table_name=self.current_table,
            domain_filter=domain_filter,
        )

        if not columns:
            self._set_status(C.DATA_STATUS_NO_COLUMNS)
            self._render_message(C.DATA_NO_COLUMNS_TEXT)
            return

        self._render_table(columns, rows)

        if domain_filter:
            self._set_status(
                C.DATA_STATUS_FILTERED.format(
                    table=self.current_table,
                    count=len(rows),
                    domain=domain_filter,
                )
            )
        else:
            self._set_status(
                C.DATA_STATUS_LOADED.format(
                    table=self.current_table,
                    count=len(rows),
                )
            )

    def _render_table(self, columns: list[str], rows: list[dict]) -> None:
        """
        Renders a read-only table.

        Args:
            columns: Table column names.
            rows: Table row dictionaries.
        """
        for child in self.rows_container.winfo_children():
            child.destroy()

        if not rows:
            self._render_message(C.DATA_NO_ROWS_TEXT)
            return

        max_columns = min(len(columns), C.DATA_MAX_VISIBLE_COLUMNS)
        visible_columns = columns[:max_columns]

        header = ctk.CTkFrame(
            self.rows_container,
            corner_radius=8,
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 6),
        )

        for column_index, column_name in enumerate(visible_columns):
            header.grid_columnconfigure(column_index, weight=1)

            label = ctk.CTkLabel(
                header,
                text=column_name,
                font=self.fonts["small_bold"],
                anchor="w",
            )
            label.grid(
                row=0,
                column=column_index,
                sticky="ew",
                padx=10,
                pady=10,
            )

        for row_index, row_data in enumerate(rows, start=1):
            row_frame = ctk.CTkFrame(
                self.rows_container,
                corner_radius=8,
            )
            row_frame.grid(
                row=row_index,
                column=0,
                sticky="ew",
                pady=3,
            )

            for column_index, column_name in enumerate(visible_columns):
                row_frame.grid_columnconfigure(column_index, weight=1)

                value = self._format_cell_value(row_data.get(column_name))

                label = ctk.CTkLabel(
                    row_frame,
                    text=value,
                    font=self.fonts["small"],
                    anchor="w",
                    justify="left",
                    wraplength=220,
                )
                label.grid(
                    row=0,
                    column=column_index,
                    sticky="ew",
                    padx=10,
                    pady=8,
                )

        if len(columns) > max_columns:
            warning = ctk.CTkLabel(
                self.rows_container,
                text=C.DATA_COLUMNS_TRUNCATED_TEXT.format(
                    visible=max_columns,
                    total=len(columns),
                ),
                font=self.fonts["small_bold"],
                justify="left",
            )
            warning.grid(
                row=len(rows) + 1,
                column=0,
                sticky="w",
                pady=(12, 0),
            )

        if self.current_palette:
            self.apply_theme(self.current_palette)

    def _render_message(self, message: str) -> None:
        """
        Renders a simple message inside the table area.

        Args:
            message: Message to display.
        """
        for child in self.rows_container.winfo_children():
            child.destroy()

        label = ctk.CTkLabel(
            self.rows_container,
            text=message,
            font=self.fonts["body"],
            justify="left",
            wraplength=900,
        )
        label.grid(
            row=0,
            column=0,
            sticky="w",
        )

    def _sync_table_buttons(self) -> None:
        """
        Updates internal tab button styles according to the selected table.
        """
        if not self.current_palette:
            return

        for table_name, button in self.table_buttons.items():
            is_active = table_name == self.current_table

            button.configure(
                fg_color=(
                    self.current_palette["primary"]
                    if is_active
                    else self.current_palette["soft"]
                ),
                hover_color=self.current_palette["secondary_hover"],
                text_color=(
                    self.current_palette["inverse_text"]
                    if is_active
                    else self.current_palette["text"]
                ),
            )

    def _set_status(self, text: str) -> None:
        """
        Updates the page status label.

        Args:
            text: Status text.
        """
        if self.status_label:
            self.status_label.configure(text=text)

    def _format_table_name(self, table_name: str) -> str:
        """
        Formats a database table name for display.

        Args:
            table_name: Raw table name.

        Returns:
            str: Display table name.
        """
        return table_name.replace("_", " ").title()

    def _format_cell_value(self, value) -> str:
        """
        Formats a database cell value for display.

        Args:
            value: Raw database value.

        Returns:
            str: Display value.
        """
        if value is None:
            return C.DATA_EMPTY_VALUE

        text = str(value)

        if len(text) > self.MAX_CELL_LENGTH:
            return text[: self.MAX_CELL_LENGTH] + "..."

        return text

    def apply_theme(self, palette: dict) -> None:
        """
        Applies the active theme to the data page.

        Args:
            palette: Active theme palette.
        """
        self.current_palette = palette

        self.configure(fg_color=palette["panel"])

        if self.data_scroll:
            self.data_scroll.configure(fg_color=palette["panel"])

        for card in [
            self.header_card,
            self.table_tabs_card,
            self.table_card,
        ]:
            if card:
                card.configure(fg_color=palette["card"])

        self._configure_description_textbox(palette)

        if self.refresh_button:
            self.refresh_button.configure(
                fg_color=palette["primary"],
                hover_color=palette["primary_hover"],
                text_color=palette["inverse_text"],
            )

        if self.domain_entry:
            self.domain_entry.configure(
                fg_color=palette["soft"],
                border_color=palette["soft"],
                text_color=palette["text"],
                placeholder_text_color=palette["muted"],
            )

        if self.status_label:
            self.status_label.configure(text_color=palette["muted"])

        self._sync_table_buttons()

        if self.rows_container:
            for child in self.rows_container.winfo_children():
                if isinstance(child, ctk.CTkFrame):
                    child.configure(fg_color=palette["soft"])

                    for nested in child.winfo_children():
                        if isinstance(nested, ctk.CTkLabel):
                            nested.configure(text_color=palette["text"])

                elif isinstance(child, ctk.CTkLabel):
                    child.configure(text_color=palette["text"])