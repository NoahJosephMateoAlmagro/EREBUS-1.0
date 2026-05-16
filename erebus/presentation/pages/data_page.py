"""
Data page for the EREBUS graphical interface.

This page allows the user to inspect the information stored in the SQLite
database. It provides an internal table selector, an execution identifier filter,
pagination controls and a read-only tabular view of the selected table.

The table rendering itself is delegated to DataTableView. This page acts as a
coordinator between the database browser service and the visual table widget.

A danger zone is displayed at the bottom of the page to clear stored execution
data while preserving saved API credentials.
"""

from __future__ import annotations

import sys
from tkinter import messagebox

import customtkinter as ctk

import presentation.constants as C
from presentation.services.data_browser_service import DataBrowserService
from presentation.widgets.cards import create_card
from presentation.widgets.data_table_view import DataTableView


class DataPage(ctk.CTkFrame):
    """
    Page used to browse stored EREBUS database information.
    """

    LOADING_DELAY_MS = 80

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
        self.current_page = 1
        self.current_page_size = C.DATA_DEFAULT_PAGE_SIZE
        self.current_page_data = None

        self.pending_load_id = None

        self.data_scroll = None
        self.header_card = None
        self.table_tabs_card = None
        self.table_card = None
        self.danger_zone_card = None

        self.description_textbox = None
        self.execution_filter_entry = None
        self.refresh_button = None
        self.filter_help_textbox = None
        self.status_label = None

        self.table_container = None
        self.table_buttons = {}

        self.table_view = None
        self.pagination_frame = None
        self.previous_button = None
        self.next_button = None
        self.page_size_menu = None
        self.pagination_label = None

        self.danger_description_label = None
        self.clear_database_button = None

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
        self.data_scroll.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=10,
            pady=10,
        )
        self.data_scroll.grid_columnconfigure(0, weight=1)

        self._build_header_card()
        self._build_table_tabs_card()
        self._build_table_card()
        self._build_danger_zone_card()

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
            pady=(0, 14),
        )
        self._set_textbox_text(self.description_textbox, C.DATA_DESCRIPTION)

        filter_frame = ctk.CTkFrame(
            self.header_card,
            fg_color="transparent",
        )
        filter_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=24,
            pady=(0, 8),
        )
        filter_frame.grid_columnconfigure(0, weight=0)
        filter_frame.grid_columnconfigure(1, weight=1)
        filter_frame.grid_columnconfigure(2, weight=0)

        label = ctk.CTkLabel(
            filter_frame,
            text=C.DATA_EXECUTION_FILTER_LABEL,
            font=self.fonts["body_bold"],
        )
        label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 14),
        )

        self.execution_filter_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text=C.DATA_EXECUTION_FILTER_PLACEHOLDER,
            height=42,
            font=self.fonts["body"],
        )
        self.execution_filter_entry.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(0, 14),
        )
        self.execution_filter_entry.bind(
            "<Return>",
            lambda _event: self.reload_current_table(reset_page=True),
        )

        self.refresh_button = ctk.CTkButton(
            filter_frame,
            text=C.DATA_REFRESH_BUTTON,
            width=150,
            height=42,
            corner_radius=6,
            font=self.fonts["button"],
            command=lambda: self.reload_current_table(reset_page=True),
        )
        self.refresh_button.grid(
            row=0,
            column=2,
            sticky="e",
        )

        self.filter_help_textbox = ctk.CTkTextbox(
            self.header_card,
            height=self._get_help_text_height(),
            font=self.fonts["small"],
            wrap="word",
            corner_radius=0,
            border_width=0,
            activate_scrollbars=False,
        )
        self.filter_help_textbox.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=24,
            pady=(0, 16),
        )
        self._set_textbox_text(
            self.filter_help_textbox,
            self._get_filter_help_text(),
        )

        self.status_label = ctk.CTkLabel(
            self.header_card,
            text=C.DATA_STATUS_READY,
            font=self.fonts["small_bold"],
        )
        self.status_label.grid(
            row=4,
            column=0,
            sticky="w",
            padx=24,
            pady=(0, 18),
        )

    def _build_table_tabs_card(self) -> None:
        """
        Builds the internal database table selector card.
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
        Builds the table card with pagination controls and table widget.
        """
        self.table_card = create_card(self.data_scroll, row=2)
        self.table_card.grid_columnconfigure(0, weight=1)

        self.pagination_frame = ctk.CTkFrame(
            self.table_card,
            fg_color="transparent",
        )
        self.pagination_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=24,
            pady=(22, 12),
        )
        self.pagination_frame.grid_columnconfigure(0, weight=0)
        self.pagination_frame.grid_columnconfigure(1, weight=0)
        self.pagination_frame.grid_columnconfigure(2, weight=1)
        self.pagination_frame.grid_columnconfigure(3, weight=0)
        self.pagination_frame.grid_columnconfigure(4, weight=0)

        self.previous_button = ctk.CTkButton(
            self.pagination_frame,
            text="Previous",
            width=120,
            height=38,
            corner_radius=6,
            font=self.fonts["button"],
            command=self.go_to_previous_page,
        )
        self.previous_button.grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 10),
        )

        self.next_button = ctk.CTkButton(
            self.pagination_frame,
            text="Next",
            width=120,
            height=38,
            corner_radius=6,
            font=self.fonts["button"],
            command=self.go_to_next_page,
        )
        self.next_button.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(0, 16),
        )

        self.pagination_label = ctk.CTkLabel(
            self.pagination_frame,
            text="Page - / - · 0 rows",
            font=self.fonts["small_bold"],
            justify="left",
        )
        self.pagination_label.grid(
            row=0,
            column=2,
            sticky="w",
        )

        page_size_label = ctk.CTkLabel(
            self.pagination_frame,
            text="Rows",
            font=self.fonts["small_bold"],
        )
        page_size_label.grid(
            row=0,
            column=3,
            sticky="e",
            padx=(16, 8),
        )

        self.page_size_menu = ctk.CTkOptionMenu(
            self.pagination_frame,
            values=C.DATA_PAGE_SIZE_OPTIONS,
            width=92,
            height=38,
            corner_radius=6,
            font=self.fonts["small_bold"],
            dropdown_font=self.fonts["small"],
            command=self.change_page_size,
        )
        self.page_size_menu.set(str(self.current_page_size))
        self.page_size_menu.grid(
            row=0,
            column=4,
            sticky="e",
        )

        self.table_view = DataTableView(
            parent=self.table_card,
            fonts=self.fonts,
        )
        self.table_view.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=24,
            pady=(0, 24),
        )

    def _build_danger_zone_card(self) -> None:
        """
        Builds the danger zone card used to clear stored execution data.
        """
        self.danger_zone_card = create_card(self.data_scroll, row=3)
        self.danger_zone_card.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self.danger_zone_card,
            text=C.DATA_DANGER_ZONE_TITLE,
            font=self.fonts["section"],
        )
        title.grid(
            row=0,
            column=0,
            sticky="w",
            padx=24,
            pady=(22, 8),
        )

        self.danger_description_label = ctk.CTkLabel(
            self.danger_zone_card,
            text=C.DATA_DANGER_ZONE_DESCRIPTION,
            font=self.fonts["body"],
            justify="left",
            anchor="w",
            wraplength=980,
        )
        self.danger_description_label.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=24,
            pady=(0, 16),
        )

        self.clear_database_button = ctk.CTkButton(
            self.danger_zone_card,
            text=C.DATA_CLEAR_DATABASE_BUTTON,
            width=190,
            height=42,
            corner_radius=6,
            font=self.fonts["button"],
            command=self.clear_database_with_confirmation,
        )
        self.clear_database_button.grid(
            row=2,
            column=0,
            sticky="w",
            padx=24,
            pady=(0, 22),
        )

    def refresh_tables(self) -> None:
        """
        Reloads available database tables and rebuilds the internal table tabs.
        """
        for child in self.table_container.winfo_children():
            child.destroy()

        self.table_buttons.clear()

        table_names = self.database_service.get_table_names()

        if not table_names:
            self.current_table = None
            self.current_page_data = None
            self._set_status(C.DATA_STATUS_NO_DATABASE)
            self._update_pagination_controls(None)

            if self.table_view:
                self.table_view.render_message(C.DATA_NO_DATABASE_TEXT)

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
        Selects a database table and loads its first page.

        Args:
            table_name: Selected database table.
        """
        self.current_table = table_name
        self.current_page = 1
        self.current_page_data = None
        self._sync_table_buttons()
        self.reload_current_table(reset_page=True)

    def reload_current_table(self, reset_page: bool = False) -> None:
        """
        Reloads the currently selected table.

        Args:
            reset_page: Whether to reset pagination to the first page.
        """
        if not self.current_table:
            self._set_status(C.DATA_NO_TABLE_SELECTED_TEXT)

            if self.table_view:
                self.table_view.render_message(C.DATA_NO_TABLE_SELECTED_TEXT)

            return

        if reset_page:
            self.current_page = 1

        if self.pending_load_id:
            try:
                self.after_cancel(self.pending_load_id)
            except Exception:
                pass
            self.pending_load_id = None

        table_name = self.current_table
        execution_filter = self._get_execution_filter()

        self._set_status(C.DATA_STATUS_LOADING.format(table=table_name))
        self._update_pagination_controls(None)

        if self.table_view:
            self.table_view.show_loading(table_name)

        self.pending_load_id = self.after(
            self.LOADING_DELAY_MS,
            lambda: self._load_table_page(
                table_name=table_name,
                execution_filter=execution_filter,
                page=self.current_page,
                page_size=self.current_page_size,
            ),
        )

    def _load_table_page(
        self,
        table_name: str,
        execution_filter: str,
        page: int,
        page_size: int,
    ) -> None:
        """
        Loads a paginated table page and renders it.

        Args:
            table_name: Database table name.
            execution_filter: Active execution identifier filter.
            page: Requested page number.
            page_size: Requested page size.
        """
        self.pending_load_id = None

        try:
            page_data = self.database_service.fetch_table_page(
                table_name=table_name,
                execution_filter=execution_filter,
                page=page,
                page_size=page_size,
            )

            if table_name != self.current_table:
                return

            self.current_page_data = page_data
            self.current_page = page_data.get("page", 1)
            self.current_page_size = page_data.get("page_size", self.current_page_size)

            if self.table_view:
                self.table_view.render_page(page_data)

            self._update_pagination_controls(page_data)
            self._update_status_from_page(page_data)

        except Exception as exc:
            self.current_page_data = None
            self._update_pagination_controls(None)
            self._set_status(C.DATA_STATUS_ERROR.format(table=table_name))
            print(f"[GUI] Data page load error: {exc}", file=sys.stderr)

            if self.table_view:
                self.table_view.render_message(f"Could not load {table_name}.")

        finally:
            if self.table_view:
                self.table_view.hide_loading_when_ready()

    def go_to_previous_page(self) -> None:
        """
        Loads the previous table page.
        """
        if not self.current_page_data:
            return

        if not self.current_page_data.get("has_previous"):
            return

        self.current_page = max(1, self.current_page - 1)
        self.reload_current_table(reset_page=False)

    def go_to_next_page(self) -> None:
        """
        Loads the next table page.
        """
        if not self.current_page_data:
            return

        if not self.current_page_data.get("has_next"):
            return

        self.current_page += 1
        self.reload_current_table(reset_page=False)

    def change_page_size(self, value: str) -> None:
        """
        Changes the active page size and reloads the current table.

        Args:
            value: Selected page size text.
        """
        try:
            self.current_page_size = int(value)
        except Exception:
            self.current_page_size = C.DATA_DEFAULT_PAGE_SIZE

        self.current_page = 1
        self.reload_current_table(reset_page=True)

    def clear_database_with_confirmation(self) -> None:
        """
        Asks for confirmation and clears stored execution data if confirmed.
        """
        confirmed = messagebox.askyesno(
            C.DATA_CLEAR_DATABASE_CONFIRM_TITLE,
            C.DATA_CLEAR_DATABASE_CONFIRM_MESSAGE,
            parent=self.winfo_toplevel(),
        )

        if not confirmed:
            return

        self.clear_database()

    def clear_database(self) -> None:
        """
        Clears stored execution data and refreshes the Data page.
        """
        self._set_status(C.DATA_STATUS_CLEARING_DATABASE)

        try:
            self.database_service.clear_execution_data()

            self.current_page = 1
            self.current_page_data = None

            self.refresh_tables()
            self._set_status(C.DATA_STATUS_DATABASE_CLEARED)

        except Exception as exc:
            self._set_status(C.DATA_STATUS_DATABASE_CLEAR_ERROR)
            print(f"[GUI] Data page clear database error: {exc}", file=sys.stderr)

    def _update_status_from_page(self, page_data: dict) -> None:
        """
        Updates the status text after loading a page.

        Args:
            page_data: Page data returned by DataBrowserService.
        """
        table_name = page_data.get("table_name", self.current_table)
        execution_filter = page_data.get("execution_filter", "")
        total_rows = page_data.get("total_rows", 0)
        shown_rows = len(page_data.get("rows", []))

        if not page_data.get("columns"):
            self._set_status(C.DATA_STATUS_NO_COLUMNS)
            return

        if execution_filter:
            self._set_status(
                C.DATA_STATUS_FILTERED.format(
                    shown=shown_rows,
                    table=table_name,
                    filter_value=execution_filter,
                    total=total_rows,
                )
            )
            return

        self._set_status(
            C.DATA_STATUS_LOADED.format(
                shown=shown_rows,
                table=table_name,
                total=total_rows,
            )
        )

    def _update_pagination_controls(self, page_data: dict | None) -> None:
        """
        Updates pagination controls from the loaded page data.

        Args:
            page_data: Current page data or None.
        """
        if not page_data:
            if self.pagination_label:
                self.pagination_label.configure(text="Page - / - · 0 rows")

            if self.previous_button:
                self.previous_button.configure(state="disabled")

            if self.next_button:
                self.next_button.configure(state="disabled")

            return

        page = page_data.get("page", 1)
        total_pages = page_data.get("total_pages", 1)
        total_rows = page_data.get("total_rows", 0)
        shown_rows = len(page_data.get("rows", []))
        page_size = page_data.get("page_size", self.current_page_size)

        if self.pagination_label:
            self.pagination_label.configure(
                text=(
                    f"Page {page} / {total_pages} · "
                    f"{shown_rows} shown · {total_rows} total"
                )
            )

        if self.previous_button:
            self.previous_button.configure(
                state="normal" if page_data.get("has_previous") else "disabled"
            )

        if self.next_button:
            self.next_button.configure(
                state="normal" if page_data.get("has_next") else "disabled"
            )

        if self.page_size_menu:
            self.page_size_menu.set(str(page_size))

    def _set_textbox_text(self, textbox, text: str) -> None:
        """
        Writes text into a read-only textbox.

        Args:
            textbox: Target CTkTextbox.
            text: Text to write.
        """
        if not textbox:
            return

        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", text)
        textbox.configure(state="disabled")

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

    def _get_help_text_height(self) -> int:
        """
        Calculates a safe height for the execution filter help textbox.

        Returns:
            int: Textbox height in pixels.
        """
        try:
            font_size = abs(int(self.fonts["small"].cget("size")))
        except Exception:
            font_size = 12

        return max(46, int(font_size * 4.2))

    def _configure_readonly_textbox(
        self,
        textbox,
        palette: dict,
        height: int,
        text_color: str | None = None,
    ) -> None:
        """
        Applies theme and layout settings to a read-only textbox.

        Args:
            textbox: Target CTkTextbox.
            palette: Active theme palette.
            height: Textbox height.
            text_color: Optional text color. If omitted, the main text color is used.
        """
        if not textbox:
            return

        textbox.configure(
            height=height,
            fg_color=palette["card"],
            text_color=text_color or palette["text"],
            border_width=0,
        )

        try:
            textbox._textbox.configure(
                padx=0,
                pady=0,
                borderwidth=0,
                highlightthickness=0,
            )
        except AttributeError:
            pass

    def _get_filter_help_text(self) -> str:
        """
        Gets the execution filter help text.

        Returns:
            str: Filter help text.
        """
        if hasattr(C, "DATA_EXECUTION_FILTER_HELP"):
            return C.DATA_EXECUTION_FILTER_HELP

        return C.DATA_EXECUTION_FILTER_HELP_TEXT

    def _get_execution_filter(self) -> str:
        """
        Gets the current execution identifier filter.

        Returns:
            str: Execution identifier filter text.
        """
        if not self.execution_filter_entry:
            return ""

        return self.execution_filter_entry.get().strip()

    def _sync_table_buttons(self) -> None:
        """
        Updates table selector button styles according to the selected table.
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
            self.danger_zone_card,
        ]:
            if card:
                card.configure(fg_color=palette["card"])

        self._configure_readonly_textbox(
            textbox=self.description_textbox,
            palette=palette,
            height=self._get_description_height(),
            text_color=palette["text"],
        )

        self._configure_readonly_textbox(
            textbox=self.filter_help_textbox,
            palette=palette,
            height=self._get_help_text_height(),
            text_color=palette["muted"],
        )

        if self.execution_filter_entry:
            self.execution_filter_entry.configure(
                fg_color=palette["soft"],
                border_color=palette["soft"],
                text_color=palette["text"],
                placeholder_text_color=palette["muted"],
            )

        if self.refresh_button:
            self.refresh_button.configure(
                fg_color=palette["primary"],
                hover_color=palette["primary_hover"],
                text_color=palette["inverse_text"],
            )

        if self.status_label:
            self.status_label.configure(text_color=palette["muted"])

        for button in [
            self.previous_button,
            self.next_button,
        ]:
            if button:
                button.configure(
                    fg_color=palette["secondary"],
                    hover_color=palette["secondary_hover"],
                    text_color=palette["text"],
                )

        if self.page_size_menu:
            self.page_size_menu.configure(
                fg_color=palette["secondary"],
                button_color=palette["secondary"],
                button_hover_color=palette["secondary_hover"],
                text_color=palette["text"],
                dropdown_fg_color=palette["card"],
                dropdown_hover_color=palette["soft"],
                dropdown_text_color=palette["text"],
            )

        if self.pagination_label:
            self.pagination_label.configure(text_color=palette["muted"])

        if self.table_view:
            self.table_view.apply_theme(palette)

        if self.danger_description_label:
            self.danger_description_label.configure(text_color=palette["muted"])

        if self.clear_database_button:
            self.clear_database_button.configure(
                fg_color=palette["danger"],
                hover_color=palette["danger_hover"],
                text_color=C.COLORS["text_light"],
            )

        self._sync_table_buttons()