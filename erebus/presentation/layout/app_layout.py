"""
Application layout builder for EREBUS.

This module contains the class responsible for building the static structure of
the main window, including the header, sidebar and page container.
"""

import customtkinter as ctk

import presentation.constants as C
from presentation.pages.console_page import ConsolePage
from presentation.pages.execution_page import ExecutionPage
from presentation.pages.placeholder_page import PlaceholderPage
from presentation.theme import get_theme_palette


class AppLayout:
    """
    Builds and stores the main UI widgets for the application.

    This class is responsible only for creating and organizing widgets. It does
    not implement navigation, appearance changes or execution logic.
    """

    def __init__(
        self,
        parent,
        fonts,
        on_show_tab,
        on_toggle_theme,
        on_change_ui_scale,
        on_start_execution,
        on_stop_execution,
    ):
        """
        Initializes the layout builder.

        Args:
            parent: Root application window.
            fonts: Dictionary with the shared CTkFont objects.
            on_show_tab: Callback used to switch visible tabs.
            on_toggle_theme: Callback used to toggle the application theme.
            on_change_ui_scale: Callback used to change the UI scale.
            on_start_execution: Callback used to start execution.
            on_stop_execution: Callback used to stop execution.
        """
        self.parent = parent
        self.fonts = fonts

        self.on_show_tab = on_show_tab
        self.on_toggle_theme = on_toggle_theme
        self.on_change_ui_scale = on_change_ui_scale
        self.on_start_execution = on_start_execution
        self.on_stop_execution = on_stop_execution

        self.header = None
        self.title_container = None
        self.title_label = None
        self.subtitle_label = None
        self.theme_button = None
        self.size_menu = None

        self.main_area = None
        self.sidebar = None
        self.content_area = None

        self.execution_tab = None
        self.data_tab = None
        self.results_tab = None
        self.console_tab = None

        self.tab_buttons = {}
        self.pages = {}

    def build(self) -> None:
        """
        Builds the full layout of the application window.
        """
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_main_area()

    def _build_header(self) -> None:
        """
        Builds the top header with title, subtitle and global controls.
        """
        palette = get_theme_palette(C.THEME_DARK)

        self.header = ctk.CTkFrame(
            self.parent,
            corner_radius=0,
            height=C.HEADER_HEIGHT,
            fg_color=palette["bg"],
        )
        self.header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=C.HEADER_PADX,
            pady=C.HEADER_PADY,
        )
        self.header.grid_propagate(False)

        self.title_container = ctk.CTkFrame(
            self.header,
            fg_color="transparent",
        )
        self.title_container.place(relx=0.5, y=0, anchor="n")

        self.title_label = ctk.CTkLabel(
            self.title_container,
            text=C.APP_TITLE,
            font=self.fonts["title"],
        )
        self.title_label.grid(row=0, column=0, sticky="n")

        self.subtitle_label = ctk.CTkLabel(
            self.title_container,
            text=C.APP_SUBTITLE,
            font=self.fonts["subtitle"],
        )
        self.subtitle_label.grid(row=1, column=0, sticky="n")

        self.theme_button = ctk.CTkButton(
            self.header,
            text="Light mode",
            width=150,
            height=36,
            corner_radius=6,
            font=self.fonts["button"],
            command=self.on_toggle_theme,
        )
        self.theme_button.place(relx=1.0, y=18, anchor="ne")

        self.size_menu = ctk.CTkOptionMenu(
            self.header,
            values=C.UI_SCALE_OPTIONS,
            width=150,
            height=36,
            corner_radius=6,
            font=self.fonts["button"],
            dropdown_font=self.fonts["small"],
            command=self.on_change_ui_scale,
        )
        self.size_menu.set(C.DEFAULT_UI_SCALE)
        self.size_menu.place(relx=1.0, x=-162, y=18, anchor="ne")

    def _build_main_area(self) -> None:
        """
        Builds the main content structure with sidebar and page container.
        """
        palette = get_theme_palette(C.THEME_DARK)

        self.main_area = ctk.CTkFrame(
            self.parent,
            corner_radius=18,
            fg_color=palette["panel"],
        )
        self.main_area.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=C.MAIN_AREA_PADX,
            pady=C.MAIN_AREA_PADY,
        )

        self.main_area.grid_columnconfigure(0, weight=0)
        self.main_area.grid_columnconfigure(1, weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(
            self.main_area,
            corner_radius=10,
            fg_color=palette["card"],
        )
        self.sidebar.grid(
            row=0,
            column=0,
            sticky="nsw",
            padx=(14, 10),
            pady=14,
        )
        self.sidebar.grid_columnconfigure(0, weight=1)

        self.content_area = ctk.CTkFrame(
            self.main_area,
            corner_radius=10,
            fg_color=palette["panel"],
        )
        self.content_area.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(10, 14),
            pady=14,
        )
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_pages()

    def _build_sidebar(self) -> None:
        """
        Builds the left navigation sidebar.
        """
        self.tab_buttons[C.TAB_EXECUTION] = self._create_sidebar_button(
            text=C.TAB_LABELS[C.TAB_EXECUTION],
            row=0,
            command=lambda: self.on_show_tab(C.TAB_EXECUTION),
        )

        self.tab_buttons[C.TAB_DATA] = self._create_sidebar_button(
            text=C.TAB_LABELS[C.TAB_DATA],
            row=1,
            command=lambda: self.on_show_tab(C.TAB_DATA),
        )

        self.tab_buttons[C.TAB_RESULTS] = self._create_sidebar_button(
            text=C.TAB_LABELS[C.TAB_RESULTS],
            row=2,
            command=lambda: self.on_show_tab(C.TAB_RESULTS),
        )

        self.tab_buttons[C.TAB_CONSOLE] = self._create_sidebar_button(
            text=C.TAB_LABELS[C.TAB_CONSOLE],
            row=3,
            command=lambda: self.on_show_tab(C.TAB_CONSOLE),
        )

    def _create_sidebar_button(self, text, row, command):
        """
        Creates a sidebar navigation button.

        Args:
            text: Button label.
            row: Grid row where the button is placed.
            command: Callback executed when the button is clicked.

        Returns:
            CTkButton: Created navigation button.
        """
        button = ctk.CTkButton(
            self.sidebar,
            text=text,
            width=C.SIDEBAR_WIDTH,
            height=C.SIDEBAR_BUTTON_HEIGHT,
            corner_radius=6,
            font=self.fonts["button"],
            command=command,
        )
        button.grid(
            row=row,
            column=0,
            sticky="ew",
            padx=12,
            pady=(12 if row == 0 else 6, 6),
        )
        return button

    def _build_pages(self) -> None:
        """
        Creates all application pages and places them in the content area.
        """
        self.execution_tab = ExecutionPage(
            parent=self.content_area,
            fonts=self.fonts,
            on_start=self.on_start_execution,
            on_stop=self.on_stop_execution,
        )

        self.data_tab = PlaceholderPage(
            parent=self.content_area,
            text=C.PLACEHOLDER_DATA_TEXT,
            fonts=self.fonts,
        )

        self.results_tab = PlaceholderPage(
            parent=self.content_area,
            text=C.PLACEHOLDER_RESULTS_TEXT,
            fonts=self.fonts,
        )

        self.console_tab = ConsolePage(
            parent=self.content_area,
            fonts=self.fonts,
        )

        self.pages = {
            C.TAB_EXECUTION: self.execution_tab,
            C.TAB_DATA: self.data_tab,
            C.TAB_RESULTS: self.results_tab,
            C.TAB_CONSOLE: self.console_tab,
        }

        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")