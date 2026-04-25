import os
import sys
import queue
import ctypes
import threading
import customtkinter as ctk
from pathlib import Path

from application.config import APP_CONFIG
from application.runner import run_erebus
from presentation.module_ui_config import (
    MODULE_UI_CONFIG,
    SETTING_LABELS,
    SETTING_TOOLTIPS,
)

try:
    import winsound
except ImportError:
    winsound = None


def load_font(font_path):
    """
    Loads a font temporarily for the current Windows session.

    The font is not permanently installed in the operating system.
    It is only made available while the application is running.

    Args:
        font_path: Path to the font file.
    """
    font_path = str(Path(font_path).resolve())

    if not os.path.exists(font_path):
        print(f"Font not found: {font_path}")
        return

    ctypes.windll.gdi32.AddFontResourceExW(font_path, 0x10, 0)


def load_app_fonts():
    """
    Loads the custom fonts used by the EREBUS interface.
    """
    base_dir = Path(__file__).resolve().parent
    fonts_dir = base_dir / "assets" / "fonts"

    load_font(fonts_dir / "Zekton-Regular.otf")
    load_font(fonts_dir / "SHUTTLE-X.ttf")


class Tooltip:
    """
    Simple tooltip displayed when the mouse hovers over a widget.

    It is used to explain configuration fields without adding too much
    permanent text to the interface.
    """

    def __init__(self, widget, text, delay=450):
        """
        Initializes the tooltip.

        Args:
            widget: Widget that triggers the tooltip.
            text: Tooltip text.
            delay: Delay in milliseconds before showing the tooltip.
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.after_id = None

        self.widget.bind("<Enter>", self._schedule)
        self.widget.bind("<Leave>", self._hide)
        self.widget.bind("<ButtonPress>", self._hide)

    def _schedule(self, _event=None):
        """
        Schedules the tooltip display.
        """
        self._cancel()
        self.after_id = self.widget.after(self.delay, self._show)

    def _cancel(self):
        """
        Cancels a pending tooltip display.
        """
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None

    def _show(self):
        """
        Displays the tooltip next to the widget.
        """
        if self.tooltip_window or not self.text:
            return

        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8

        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        self.tooltip_window.attributes("-topmost", True)

        label = ctk.CTkLabel(
            self.tooltip_window,
            text=self.text,
            justify="left",
            wraplength=390,
            padx=14,
            pady=10,
            corner_radius=8,
            fg_color="#0F1938",
            text_color="#FFFFFF",
        )
        label.pack()

    def _hide(self, _event=None):
        """
        Hides the tooltip.
        """
        self._cancel()

        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class ConsoleRedirector:
    """
    Redirects stdout or stderr messages into a thread-safe queue.

    The GUI periodically reads this queue and writes the messages into
    the console textbox. This avoids updating Tkinter widgets directly
    from background threads.
    """

    def __init__(self, output_queue, stream_name):
        """
        Initializes the redirector.

        Args:
            output_queue: Queue where console messages are stored.
            stream_name: Name of the stream, usually 'stdout' or 'stderr'.
        """
        self.output_queue = output_queue
        self.stream_name = stream_name

    def write(self, message):
        """
        Writes a message into the queue.

        Args:
            message: Text written to stdout or stderr.
        """
        if message:
            self.output_queue.put((self.stream_name, message))

    def flush(self):
        """
        Required for file-like compatibility.
        """
        pass


class ErebusApp(ctk.CTk):
    """
    Main CustomTkinter application for EREBUS.

    This class builds the graphical interface used to configure and launch
    EREBUS executions. The interface does not modify APP_CONFIG directly.
    Instead, it generates runtime configuration overrides that are passed
    to the execution runner.
    """

    def __init__(self):
        """
        Initializes the EREBUS GUI application.
        """
        super().__init__()

        load_app_fonts()

        self.title("EREBUS")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.colors = {
            "dark_bg": "#0F1938",
            "dark_panel": "#1A2448",
            "dark_card": "#26345F",
            "dark_soft": "#354678",

            "light_bg": "#E9EDF8",
            "light_panel": "#D8DFF1",
            "light_card": "#C8D2EA",
            "light_soft": "#B7C4E1",

            "accent": "#F5E79D",
            "accent_hover": "#F5D29D",
            "brown": "#735B38",
            "olive": "#7A713C",
            "blue": "#354678",
            "muted": "#B3B5B8",
            "light_muted": "#4D587A",
            "text_light": "#FFFFFF",
            "text_dark": "#0F1938",
            "danger": "#B85C5C",
            "danger_hover": "#D06A6A",

            "warning_bg_dark": "#F5E79D",
            "warning_border_dark": "#F5D29D",
            "warning_text_dark": "#0F1938",

            "warning_bg_light": "#354678",
            "warning_border_light": "#0F1938",
            "warning_text_light": "#FFFFFF",
        }
        self.fonts = {
            "title": ctk.CTkFont(family="Shuttle-X", size=54, weight="bold"),
            "subtitle": ctk.CTkFont(family="Zekton", size=17),
            "section": ctk.CTkFont(family="Zekton", size=24, weight="bold"),
            "body": ctk.CTkFont(family="Zekton", size=15),
            "body_bold": ctk.CTkFont(family="Zekton", size=16, weight="bold"),
            "button": ctk.CTkFont(family="Zekton", size=16, weight="bold"),
            "module_title": ctk.CTkFont(family="Zekton", size=19, weight="bold"),
            "small": ctk.CTkFont(family="Zekton", size=14),
            "small_bold": ctk.CTkFont(family="Zekton", size=14, weight="bold"),
            "placeholder": ctk.CTkFont(family="Zekton", size=22, weight="bold"),
            "console": ctk.CTkFont(family="Consolas", size=14),
            "popup": ctk.CTkFont(family="Zekton", size=18, weight="bold"),
        }

        self.module_switches = {}
        self.module_cards = {}
        self.module_settings_frames = {}
        self.config_entries = {}
        self.tab_buttons = {}
        self.all_modules_switch = None

        self.console_queue = queue.Queue()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.console_textbox = None
        self.console_clear_button = None

        self.execution_thread = None
        self.cancel_event = None
        self.stop_button = None

        self.running_modules = set()
        self.bottom_popup = None
        self.bottom_popup_card = None
        self.bottom_popup_label = None
        self.bottom_popup_close_button = None
        self.bottom_popup_animation_id = None
        self.bottom_popup_target_x = 34
        self.bottom_popup_y = 8

        self.current_theme = "dark"
        self.active_tab = "execution"

        self._set_fullscreen_size()
        self._build_ui()
        self._apply_theme()
        self._start_console_redirection()

    def _set_fullscreen_size(self):
        """
        Sets the initial window size to match the screen size.
        """
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        self.geometry(f"{screen_width}x{screen_height}+0+0")
        self.minsize(1200, 760)

        # For true fullscreen mode:
        # self.state("zoomed")

    def _build_ui(self):
        """
        Builds the main window layout.
        """
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_main_area()

    def _build_header(self):
        """
        Builds the top header with the centered title and theme button.
        """
        self.header = ctk.CTkFrame(self, corner_radius=0, height=116)
        self.header.grid(row=0, column=0, sticky="ew", padx=28, pady=(18, 8))
        self.header.grid_propagate(False)

        self.title_container = ctk.CTkFrame(self.header, fg_color="transparent")
        self.title_container.place(relx=0.5, y=0, anchor="n")

        self.title_label = ctk.CTkLabel(
            self.title_container,
            text="EREBUS",
            font=self.fonts["title"],
        )
        self.title_label.grid(row=0, column=0, sticky="n", pady=(0, 0))

        self.subtitle_label = ctk.CTkLabel(
            self.title_container,
            text="Footprinting, public exposure and digital attack surface analysis",
            font=self.fonts["subtitle"],
        )
        self.subtitle_label.grid(row=1, column=0, sticky="n", pady=(0, 0))

        self.theme_button = ctk.CTkButton(
            self.header,
            text="Light mode",
            width=150,
            height=36,
            corner_radius=6,
            font=self.fonts["button"],
            command=self.toggle_theme,
        )
        self.theme_button.place(relx=1.0, y=18, anchor="ne")

    def _build_main_area(self):
        """
        Builds the main layout area.

        The main area contains:
        - a left navigation sidebar
        - a right content area where each screen is displayed
        """
        self.main_area = ctk.CTkFrame(self, corner_radius=18)
        self.main_area.grid(row=1, column=0, sticky="nsew", padx=28, pady=(6, 28))

        self.main_area.grid_columnconfigure(0, weight=0)
        self.main_area.grid_columnconfigure(1, weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self.main_area, corner_radius=10)
        self.sidebar.grid(row=0, column=0, sticky="nsw", padx=(14, 10), pady=14)
        self.sidebar.grid_columnconfigure(0, weight=1)

        self.content_area = ctk.CTkFrame(self.main_area, corner_radius=10)
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=(10, 14), pady=14)
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_pages()

        self._show_tab("execution")

    def _build_sidebar(self):
        """
        Builds the left navigation buttons.
        """
        self.tab_buttons["execution"] = self._create_sidebar_button(
            text="Execution",
            row=0,
            command=lambda: self._show_tab("execution"),
        )

        self.tab_buttons["data"] = self._create_sidebar_button(
            text="Data",
            row=1,
            command=lambda: self._show_tab("data"),
        )

        self.tab_buttons["results"] = self._create_sidebar_button(
            text="Results",
            row=2,
            command=lambda: self._show_tab("results"),
        )

        self.tab_buttons["console"] = self._create_sidebar_button(
            text="Console",
            row=3,
            command=lambda: self._show_tab("console"),
        )

    def _create_sidebar_button(self, text, row, command):
        """
        Creates one navigation button for the sidebar.

        Args:
            text: Button label.
            row: Grid row where the button will be placed.
            command: Callback executed when the button is clicked.

        Returns:
            CTkButton: The created sidebar button.
        """
        button = ctk.CTkButton(
            self.sidebar,
            text=text,
            width=178,
            height=56,
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

    def _build_pages(self):
        """
        Creates all application pages and places them in the content area.
        """
        self.execution_tab = ctk.CTkFrame(self.content_area, corner_radius=0)
        self.data_tab = ctk.CTkFrame(self.content_area, corner_radius=0)
        self.results_tab = ctk.CTkFrame(self.content_area, corner_radius=0)
        self.console_tab = ctk.CTkFrame(self.content_area, corner_radius=0)

        for page in [
            self.execution_tab,
            self.data_tab,
            self.results_tab,
            self.console_tab,
        ]:
            page.grid(row=0, column=0, sticky="nsew")
            page.grid_columnconfigure(0, weight=1)
            page.grid_rowconfigure(0, weight=1)

        self._build_execution_tab()
        self._build_placeholder_tab(self.data_tab, "Data view pending")
        self._build_placeholder_tab(self.results_tab, "Results view pending")
        self._build_console_tab()

    def _show_tab(self, tab_name):
        """
        Displays the selected page and hides the others.

        Args:
            tab_name: Name of the tab to display.
        """
        self.execution_tab.grid_remove()
        self.data_tab.grid_remove()
        self.results_tab.grid_remove()
        self.console_tab.grid_remove()

        if tab_name == "execution":
            self.execution_tab.grid()
        elif tab_name == "data":
            self.data_tab.grid()
        elif tab_name == "results":
            self.results_tab.grid()
        elif tab_name == "console":
            self.console_tab.grid()

        self.active_tab = tab_name
        self._apply_theme()

    def _build_placeholder_tab(self, parent, text):
        """
        Builds a placeholder page.

        Args:
            parent: Parent frame.
            text: Placeholder text.
        """
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        label = ctk.CTkLabel(
            parent,
            text=text,
            font=self.fonts["placeholder"],
        )
        label.grid(row=0, column=0)

    def _build_execution_tab(self):
        """
        Builds the execution page.
        """
        self.execution_tab.grid_columnconfigure(0, weight=1)
        self.execution_tab.grid_rowconfigure(0, weight=1)

        self.execution_scroll = ctk.CTkScrollableFrame(
            self.execution_tab,
            corner_radius=0,
        )
        self.execution_scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.execution_scroll.grid_columnconfigure(0, weight=1)

        self._build_execution_card()
        self._build_global_settings_card()
        self._build_modules_card()

    def _build_execution_card(self):
        """
        Builds the execution control card.

        This card contains the target domain input, the execution button,
        the stop button and the current execution status.
        """
        self.execution_card = self._create_card(self.execution_scroll, row=0)

        self.execution_card.grid_columnconfigure(0, weight=1)
        self.execution_card.grid_columnconfigure(1, weight=0)

        header = ctk.CTkFrame(self.execution_card, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(22, 6))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="New execution",
            font=self.fonts["section"],
        )
        title.grid(row=0, column=0, sticky="w")

        self.status_label = ctk.CTkLabel(
            header,
            text="Status: Ready",
            font=self.fonts["small_bold"],
            corner_radius=10,
            padx=18,
            pady=8,
        )
        self.status_label.grid(row=0, column=1, sticky="e", padx=(24, 0))

        description = ctk.CTkLabel(
            self.execution_card,
            text="Enter the target domain and start the analysis using the selected configuration.",
            font=self.fonts["body"],
            wraplength=1000,
            justify="left",
        )
        description.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            padx=24,
            pady=(0, 18),
        )

        form = ctk.CTkFrame(self.execution_card, fg_color="transparent")
        form.grid(row=2, column=0, columnspan=2, sticky="ew", padx=24, pady=(0, 22))

        form.grid_columnconfigure(0, weight=0)
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(2, weight=0)
        form.grid_columnconfigure(3, weight=0)

        target_label = ctk.CTkLabel(
            form,
            text="Target domain",
            font=self.fonts["body_bold"],
        )
        target_label.grid(row=0, column=0, sticky="w", padx=(0, 14), pady=10)

        self.target_entry = ctk.CTkEntry(
            form,
            placeholder_text="example.com",
            height=44,
            font=self.fonts["body"],
        )
        self.target_entry.grid(row=0, column=1, sticky="ew", padx=(0, 14), pady=10)

        self.run_button = ctk.CTkButton(
            form,
            text="Start analysis",
            height=44,
            width=185,
            corner_radius=6,
            font=self.fonts["button"],
            command=self.start_execution,
        )
        self.run_button.grid(row=0, column=2, sticky="e", pady=10)

        self.stop_button = ctk.CTkButton(
            form,
            text="Stop",
            height=44,
            width=120,
            corner_radius=6,
            font=self.fonts["button"],
            command=self.stop_execution,
            state="disabled",
        )
        self.stop_button.grid(row=0, column=3, sticky="e", padx=(10, 0), pady=10)

    def _build_global_settings_card(self):
        """
        Builds the global configuration card.
        """
        self.global_card = self._create_card(self.execution_scroll, row=1)

        title = ctk.CTkLabel(
            self.global_card,
            text="General configuration",
            font=self.fonts["section"],
        )
        title.grid(row=0, column=0, sticky="w", padx=24, pady=(22, 6))

        description = ctk.CTkLabel(
            self.global_card,
            text="These values affect the whole execution.",
            font=self.fonts["body"],
        )
        description.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 16))

        body = ctk.CTkFrame(self.global_card, fg_color="transparent")
        body.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 22))
        body.grid_columnconfigure((0, 1, 2), weight=1)

        self._add_setting_entry(
            parent=body,
            row=0,
            column=0,
            section="logging",
            key="timezone",
        )

        self._add_option_menu(
            parent=body,
            row=0,
            column=1,
            section="logging",
            key="mode",
            values=["TRACE", "INFO", "ERROR", "SILENT"],
        )

        self._add_switch_setting(
            parent=body,
            row=0,
            column=2,
            section="debug",
            key="clear_db_on_run",
            text="Clear database on run",
        )

    def _build_modules_card(self):
        """
        Builds the analysis modules configuration card.

        This card contains the list of modules that can be enabled or disabled,
        as well as a global switch to enable or disable all modules at once.
        """
        self.modules_card = self._create_card(self.execution_scroll, row=2)
        self.modules_card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self.modules_card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 6))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        title = ctk.CTkLabel(
            header,
            text="Analysis modules",
            font=self.fonts["section"],
        )
        title.grid(row=0, column=0, sticky="w")

        self.all_modules_switch = ctk.CTkSwitch(
            header,
            text="Enable all",
            font=self.fonts["body_bold"],
            switch_width=72,
            switch_height=34,
            command=self.on_all_modules_toggle,
        )
        self.all_modules_switch.grid(row=0, column=1, sticky="e", padx=(24, 0))

        description = ctk.CTkLabel(
            self.modules_card,
            text="Enable the modules you want to execute. If a module depends on another one, its dependency must be enabled first.",
            font=self.fonts["body"],
            wraplength=1000,
            justify="left",
        )
        description.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))

        self.modules_container = ctk.CTkFrame(self.modules_card, fg_color="transparent")
        self.modules_container.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 24))
        self.modules_container.grid_columnconfigure(0, weight=1)

        row = 0

        for module_key in APP_CONFIG["modules"].keys():
            self._add_module_row(self.modules_container, row, module_key)
            row += 1

        self._sync_all_modules_switch()

    def _add_module_row(self, parent, row, module_key):
        """
        Adds one module card to the module list.

        Args:
            parent: Parent frame where the module card is placed.
            row: Grid row.
            module_key: Internal module key from APP_CONFIG.
        """
        metadata = MODULE_UI_CONFIG.get(module_key, {})
        title = metadata.get("title", module_key)
        description = metadata.get("description", "")
        depends_on = metadata.get("depends_on", [])

        card = ctk.CTkFrame(parent, corner_radius=10)
        card.grid(row=row, column=0, sticky="ew", pady=10)
        card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=16)
        header.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=self.fonts["module_title"],
        )
        title_label.grid(row=0, column=0, sticky="w")

        description_label = ctk.CTkLabel(
            header,
            text=description,
            font=self.fonts["small"],
            wraplength=950,
            justify="left",
        )
        description_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        if depends_on:
            dependency_text = "Depends on: " + ", ".join(
                MODULE_UI_CONFIG.get(dep, {}).get("title", dep)
                for dep in depends_on
            )

            dependency_label = ctk.CTkLabel(
                header,
                text=dependency_text,
                font=self.fonts["small_bold"],
            )
            dependency_label.grid(row=2, column=0, sticky="w", pady=(7, 0))

        switch = ctk.CTkSwitch(
            header,
            text="Enabled",
            font=self.fonts["small_bold"],
            command=lambda key=module_key: self.on_module_toggle(key),
        )
        switch.grid(row=0, column=1, rowspan=3, sticky="e", padx=(18, 0))

        if APP_CONFIG["modules"].get(module_key):
            switch.select()
        else:
            switch.deselect()

        settings_frame = ctk.CTkFrame(card, corner_radius=8)
        settings_frame.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 18))
        settings_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.module_switches[module_key] = switch
        self.module_cards[module_key] = card
        self.module_settings_frames[module_key] = settings_frame

        self._build_module_settings(module_key)

        if not switch.get():
            settings_frame.grid_remove()

    def _build_module_settings(self, module_key):
        """
        Builds the settings section for a module.

        Args:
            module_key: Internal module key.
        """
        settings_frame = self.module_settings_frames[module_key]
        metadata = MODULE_UI_CONFIG.get(module_key, {})
        settings = metadata.get("settings", [])

        for child in settings_frame.winfo_children():
            child.destroy()

        if not settings:
            empty_label = ctk.CTkLabel(
                settings_frame,
                text="This module has no specific settings.",
                font=self.fonts["small"],
            )
            empty_label.grid(row=0, column=0, sticky="w", padx=16, pady=14)
            return

        for index, (section, key) in enumerate(settings):
            self._add_setting_entry(
                parent=settings_frame,
                row=index // 3,
                column=index % 3,
                section=section,
                key=key,
            )

    def _add_setting_entry(self, parent, row, column, section, key):
        """
        Adds a text input field for a configuration value.

        Args:
            parent: Parent frame.
            row: Grid row.
            column: Grid column.
            section: Configuration section.
            key: Configuration key.
        """
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, sticky="ew", padx=12, pady=12)
        wrapper.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            wrapper,
            text=SETTING_LABELS.get(key, key),
            font=self.fonts["small_bold"],
            cursor="hand2",
        )
        label.grid(row=0, column=0, sticky="w", pady=(0, 7))

        Tooltip(
            label,
            SETTING_TOOLTIPS.get(key, "No description available for this setting."),
        )

        value = APP_CONFIG.get(section, {}).get(key, "")

        entry = ctk.CTkEntry(
            wrapper,
            height=40,
            font=self.fonts["small"],
        )
        entry.insert(0, self._format_setting_value(section, key, value))
        entry.grid(row=1, column=0, sticky="ew")

        self.config_entries[f"{section}.{key}"] = entry

    def _add_option_menu(self, parent, row, column, section, key, values):
        """
        Adds an option menu for a configuration value.

        Args:
            parent: Parent frame.
            row: Grid row.
            column: Grid column.
            section: Configuration section.
            key: Configuration key.
            values: Available option values.
        """
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, sticky="ew", padx=12, pady=12)
        wrapper.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            wrapper,
            text=SETTING_LABELS.get(key, key),
            font=self.fonts["small_bold"],
            cursor="hand2",
        )
        label.grid(row=0, column=0, sticky="w", pady=(0, 7))

        Tooltip(
            label,
            SETTING_TOOLTIPS.get(key, "No description available for this setting."),
        )

        option = ctk.CTkOptionMenu(
            wrapper,
            values=values,
            height=40,
            font=self.fonts["small"],
            dropdown_font=self.fonts["small"],
        )
        option.set(str(APP_CONFIG.get(section, {}).get(key, values[0])))
        option.grid(row=1, column=0, sticky="ew")

        self.config_entries[f"{section}.{key}"] = option

    def _add_switch_setting(self, parent, row, column, section, key, text):
        """
        Adds a switch for a boolean configuration value.

        Args:
            parent: Parent frame.
            row: Grid row.
            column: Grid column.
            section: Configuration section.
            key: Configuration key.
            text: Label text.
        """
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, sticky="ew", padx=12, pady=12)
        wrapper.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            wrapper,
            text=text,
            font=self.fonts["small_bold"],
            cursor="hand2",
        )
        label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        Tooltip(
            label,
            SETTING_TOOLTIPS.get(key, "No description available for this setting."),
        )

        switch = ctk.CTkSwitch(
            wrapper,
            text="",
            font=self.fonts["small"],
        )
        switch.grid(row=1, column=0, sticky="w")

        if APP_CONFIG.get(section, {}).get(key):
            switch.select()
        else:
            switch.deselect()

        self.config_entries[f"{section}.{key}"] = switch

    def _build_console_tab(self):
        """
        Builds the real-time console page.

        The console displays stdout and stderr messages generated by the
        application and the EREBUS execution engine.
        """
        self.console_tab.grid_columnconfigure(0, weight=1)
        self.console_tab.grid_rowconfigure(0, weight=0)
        self.console_tab.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.console_tab, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        title = ctk.CTkLabel(
            header,
            text="Runtime console",
            font=self.fonts["section"],
        )
        title.grid(row=0, column=0, sticky="w")

        self.console_clear_button = ctk.CTkButton(
            header,
            text="Clear console",
            width=180,
            height=42,
            corner_radius=6,
            font=self.fonts["button"],
            command=self._clear_console,
        )
        self.console_clear_button.grid(row=0, column=1, sticky="e", padx=(12, 0))

        self.console_textbox = ctk.CTkTextbox(
            self.console_tab,
            font=self.fonts["console"],
            wrap="none",
            corner_radius=10,
        )
        self.console_textbox.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=14,
            pady=(0, 14),
        )
        self.console_textbox.configure(state="disabled")

        self._style_console_textbox()
        self._append_console_text("[Console ready]\n")

    def _style_console_textbox(self):
        """
        Applies extra spacing and internal padding to the console textbox.
        """
        if not self.console_textbox:
            return

        try:
            self.console_textbox._textbox.configure(
                padx=14,
                pady=12,
                spacing1=2,
                spacing2=1,
                spacing3=5,
            )
        except AttributeError:
            pass

    def _start_console_redirection(self):
        """
        Redirects stdout and stderr to the GUI console.

        The original streams are preserved so they can be restored when the
        application closes.
        """
        sys.stdout = ConsoleRedirector(self.console_queue, "stdout")
        sys.stderr = ConsoleRedirector(self.console_queue, "stderr")

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._process_console_queue)

    def _process_console_queue(self):
        """
        Periodically processes pending console messages.

        This method runs on the Tkinter main thread, making it safe to update
        the textbox widget.
        """
        try:
            while True:
                stream_name, message = self.console_queue.get_nowait()

                if stream_name == "stderr":
                    self._append_console_text(message, is_error=True)
                else:
                    self._append_console_text(message)

        except queue.Empty:
            pass

        self.after(100, self._process_console_queue)

    def _append_console_text(self, text, is_error=False):
        """
        Appends text to the console textbox.

        Args:
            text: Text to append.
            is_error: Whether the text comes from stderr.
        """
        if not self.console_textbox:
            return

        self.console_textbox.configure(state="normal")
        self.console_textbox.insert("end", text)
        self.console_textbox.see("end")
        self.console_textbox.configure(state="disabled")

    def _clear_console(self):
        """
        Clears the console textbox.
        """
        if not self.console_textbox:
            return

        self.console_textbox.configure(state="normal")
        self.console_textbox.delete("1.0", "end")
        self.console_textbox.configure(state="disabled")

    def _show_bottom_popup(self, message, closable=True, play_sound=True):
        """
        Shows a non-blocking popup near the top-left of the application.

        The popup does not block interaction with the application. It is used
        to notify the user about important execution events, such as a safe
        cancellation request.

        Args:
            message: Message to display.
            closable: Whether the popup can be closed by the user.
            play_sound: Whether a notification sound should be played.
        """
        self._hide_bottom_popup()

        if play_sound:
            self._play_notification_sound()

        is_dark = self.current_theme == "dark"

        parent_bg = self.colors["dark_bg"] if is_dark else self.colors["light_bg"]

        popup_bg = (
            self.colors["warning_bg_dark"]
            if is_dark
            else self.colors["warning_bg_light"]
        )

        popup_border = (
            self.colors["warning_border_dark"]
            if is_dark
            else self.colors["warning_border_light"]
        )

        popup_text = (
            self.colors["warning_text_dark"]
            if is_dark
            else self.colors["warning_text_light"]
        )

        popup_width = 680
        popup_height = 132
        popup_y = 8

        self.bottom_popup_target_x = 34
        self.bottom_popup_y = popup_y
        start_x = -popup_width - 20

        self.bottom_popup_target_x = 34
        start_x = -popup_width - 20

        self.bottom_popup = ctk.CTkFrame(
            self,
            fg_color="transparent",
            bg_color=parent_bg,
            corner_radius=0,
        )

        self.bottom_popup.place(
            x=start_x,
            y=self.bottom_popup_y,
            anchor="nw",
        )

        self.bottom_popup.grid_columnconfigure(0, weight=1)

        self.bottom_popup_card = ctk.CTkFrame(
            self.bottom_popup,
            width=popup_width,
            height=popup_height,
            fg_color=popup_bg,
            bg_color=parent_bg,
            border_color=popup_border,
            border_width=2,
            corner_radius=18,
        )
        self.bottom_popup_card.grid(row=0, column=0, sticky="w")
        self.bottom_popup_card.grid_propagate(False)

        self.bottom_popup_card.grid_rowconfigure(0, weight=1)
        self.bottom_popup_card.grid_columnconfigure(0, weight=1)
        self.bottom_popup_card.grid_columnconfigure(1, weight=0)

        self.bottom_popup_label = ctk.CTkLabel(
            self.bottom_popup_card,
            text=message,
            font=self.fonts["popup"],
            text_color=popup_text,
            wraplength=500,
            justify="center",
            fg_color="transparent",
            bg_color=popup_bg,
        )
        self.bottom_popup_label.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(24, 18),
            pady=22,
        )

        if closable:
            self.bottom_popup_close_button = ctk.CTkButton(
                self.bottom_popup_card,
                text="Close",
                width=96,
                height=38,
                corner_radius=10,
                font=self.fonts["small_bold"],
                command=self._hide_bottom_popup,
                bg_color=popup_bg,
            )
            self.bottom_popup_close_button.grid(
                row=0,
                column=1,
                sticky="",
                padx=(0, 18),
                pady=0,
            )
        self._apply_theme()
        self._animate_bottom_popup_in(start_x)

    def _animate_bottom_popup_in(self, current_x):
        """
        Animates the popup so it slides in smoothly from the left side of the window.

        Args:
            current_x: Current horizontal position of the popup.
        """
        if not self.bottom_popup:
            return

        target_x = self.bottom_popup_target_x
        distance = target_x - current_x

        if abs(distance) <= 2:
            self.bottom_popup.place_configure(x=target_x, y=self.bottom_popup_y)
            self.bottom_popup_animation_id = None
            return

        next_x = current_x + max(2, int(distance * 0.22))

        self.bottom_popup.place_configure(x=next_x, y=self.bottom_popup_y)

        self.bottom_popup_animation_id = self.after(
            12,
            lambda: self._animate_bottom_popup_in(next_x),
        )

    def _play_notification_sound(self):
        """
        Plays a short notification sound.

        On Windows, it uses a more distinctive system alert sound.
        On other systems, it does nothing.
        """
        if winsound is None:
            return

        try:
            winsound.PlaySound(
                "SystemHand",
                winsound.SND_ALIAS | winsound.SND_ASYNC,
            )
        except Exception:
            try:
                winsound.MessageBeep(winsound.MB_ICONHAND)
            except Exception:
                pass

    def _update_bottom_popup(self, message):
        """
        Updates the current bottom popup message.

        Args:
            message: New popup message.
        """
        if self.bottom_popup_label:
            self.bottom_popup_label.configure(text=message)

    def _hide_bottom_popup(self):
        """
        Hides the bottom popup if it is currently visible.
        """
        if self.bottom_popup_animation_id:
            self.after_cancel(self.bottom_popup_animation_id)
            self.bottom_popup_animation_id = None

        if self.bottom_popup:
            self.bottom_popup.destroy()

        self.bottom_popup = None
        self.bottom_popup_card = None
        self.bottom_popup_label = None
        self.bottom_popup_close_button = None

    def _on_close(self):
        """
        Restores stdout and stderr before closing the application.
        """
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        self.destroy()

    def on_all_modules_toggle(self):
        """
        Handles the global module switch.

        When enabled, all modules are enabled.
        When disabled, all modules are disabled and their settings sections are hidden.
        """
        enable_all = bool(self.all_modules_switch.get())

        if enable_all:
            self._enable_all_modules()
            self.status_label.configure(text="Status: All modules enabled")
        else:
            self._disable_all_modules()
            self.status_label.configure(text="Status: All modules disabled")

    def _enable_all_modules(self):
        """
        Enables all modules and shows their settings sections.

        The activation follows APP_CONFIG order, which should place parent
        modules before dependent modules.
        """
        for module_key in APP_CONFIG["modules"].keys():
            switch = self.module_switches.get(module_key)

            if not switch:
                continue

            switch.select()
            self.module_settings_frames[module_key].grid()

        self._sync_all_modules_switch()

    def _disable_all_modules(self):
        """
        Disables all modules and hides their settings sections.
        """
        for module_key in APP_CONFIG["modules"].keys():
            switch = self.module_switches.get(module_key)

            if not switch:
                continue

            switch.deselect()
            self.module_settings_frames[module_key].grid_remove()

        self._sync_all_modules_switch()

    def _sync_all_modules_switch(self):
        """
        Synchronizes the global module switch with the individual module switches.

        If every module is enabled, the global switch is selected.
        Otherwise, it is deselected.
        """
        if not self.all_modules_switch:
            return

        all_enabled = all(
            bool(switch.get())
            for switch in self.module_switches.values()
        )

        if all_enabled:
            self.all_modules_switch.select()
        else:
            self.all_modules_switch.deselect()

    def on_module_toggle(self, module_key):
        """
        Handles module activation and dependency validation.

        Args:
            module_key: Internal module key.
        """
        switch = self.module_switches[module_key]

        if switch.get():
            if not self._dependencies_enabled(module_key):
                switch.deselect()

                missing = self._get_missing_dependencies(module_key)
                missing_names = [
                    MODULE_UI_CONFIG.get(dep, {}).get("title", dep)
                    for dep in missing
                ]

                self.status_label.configure(
                    text=f"Missing dependency: {', '.join(missing_names)}"
                )
                self._sync_all_modules_switch()
                return

            self.module_settings_frames[module_key].grid()
            self.status_label.configure(text="Status: Ready")

        else:
            self.module_settings_frames[module_key].grid_remove()
            self._disable_children_of(module_key)
            self.status_label.configure(text="Status: Ready")

        self._sync_all_modules_switch()

    def _dependencies_enabled(self, module_key):
        """
        Checks whether all dependencies for a module are enabled.

        Args:
            module_key: Internal module key.

        Returns:
            bool: True if all dependencies are enabled, False otherwise.
        """
        missing = self._get_missing_dependencies(module_key)
        return len(missing) == 0

    def _get_missing_dependencies(self, module_key):
        """
        Gets the missing dependencies for a module.

        Args:
            module_key: Internal module key.

        Returns:
            list: Missing dependency module keys.
        """
        metadata = MODULE_UI_CONFIG.get(module_key, {})
        dependencies = metadata.get("depends_on", [])

        missing = []

        for dependency in dependencies:
            dependency_switch = self.module_switches.get(dependency)

            if not dependency_switch or not dependency_switch.get():
                missing.append(dependency)

        return missing

    def _disable_children_of(self, parent_module_key):
        """
        Disables every module that depends on the provided parent module.

        Args:
            parent_module_key: Module key used as dependency by other modules.
        """
        for module_key, metadata in MODULE_UI_CONFIG.items():
            dependencies = metadata.get("depends_on", [])

            if parent_module_key in dependencies:
                switch = self.module_switches.get(module_key)

                if switch and switch.get():
                    switch.deselect()
                    self.module_settings_frames[module_key].grid_remove()
                    self._disable_children_of(module_key)

    def on_module_progress(self, event_type, module_key):
        """
        Receives module progress events from the orchestrator.

        Args:
            event_type: Event type. Expected values: 'start', 'end', 'error'.
            module_key: Internal module key.
        """
        self.after(
            0,
            lambda: self._handle_module_progress(event_type, module_key),
        )

    def _handle_module_progress(self, event_type, module_key):
        """
        Updates the UI with the current running module information.

        Args:
            event_type: Event type.
            module_key: Internal module key.
        """
        module_name = MODULE_UI_CONFIG.get(module_key, {}).get("title", module_key)

        if event_type == "start":
            self.running_modules.add(module_name)

        elif event_type in {"end", "error"}:
            self.running_modules.discard(module_name)

        if self.cancel_event and self.cancel_event.is_set():
            current = self._get_running_modules_text()

            self._update_bottom_popup(
                "Stop requested. To avoid data corruption, EREBUS will stop when "
                f"the current module finishes. Current module: {current}."
            )

    def _get_running_modules_text(self):
        """
        Gets a readable text with the currently running modules.

        Returns:
            str: Current running modules text.
        """
        if not self.running_modules:
            return "finishing current phase"

        return ", ".join(sorted(self.running_modules))

    def start_execution(self):
        """
        Starts an EREBUS execution in a background thread.
        """
        target = self.target_entry.get().strip()

        if not target:
            self.status_label.configure(text="Status: Missing domain")
            return

        if self.execution_thread and self.execution_thread.is_alive():
            self.status_label.configure(text="Status: Execution already running")
            return

        config_overrides = self.get_config_overrides_from_ui()

        self.cancel_event = threading.Event()
        self.running_modules.clear()

        self._hide_bottom_popup()

        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_label.configure(text="Status: Running")

        self.execution_thread = threading.Thread(
            target=self._run_in_background,
            args=(target, config_overrides, self.cancel_event),
            daemon=True,
        )
        self.execution_thread.start()

    def stop_execution(self):
        """
        Requests the current execution to stop safely.

        The execution thread is not killed. A cancellation event is set so the
        orchestrator can stop between modules or phases without corrupting data.
        """
        if not self.execution_thread or not self.execution_thread.is_alive():
            self.status_label.configure(text="Status: No execution running")
            return

        if self.cancel_event:
            self.cancel_event.set()

        current = self._get_running_modules_text()

        self.stop_button.configure(state="disabled")
        self.status_label.configure(text="Status: Cancelling")

        self._show_bottom_popup(
            "Stop requested. To avoid data corruption, EREBUS will not interrupt "
            "the module that is currently running. The execution will stop safely "
            f"as soon as the current module or phase finishes. Current module: {current}.",
            closable=True,
            play_sound=True,
        )

        print(
            "[GUI] Stop requested. EREBUS will stop after the current module "
            "or current phase finishes."
        )

    def _run_in_background(self, target, config_overrides, cancel_event):
        """
        Runs the EREBUS engine in a background thread.

        Args:
            target: Target domain.
            config_overrides: Runtime configuration overrides from the UI.
            cancel_event: Event used to request cancellation.
        """
        execution = run_erebus(
            target=target,
            config_overrides=config_overrides,
            cancel_event=cancel_event,
            progress_callback=self.on_module_progress,
        )

        if cancel_event and cancel_event.is_set():
            message = "Status: Cancelled"
            popup_message = (
                "Execution cancelled safely. Results generated before cancellation "
                "have been preserved."
            )
        elif execution:
            message = f"Status: {execution.STATUS}"
            popup_message = None
        else:
            message = "Status: Execution failed"
            popup_message = None

        self.after(0, lambda: self.status_label.configure(text=message))
        self.after(0, lambda: self.run_button.configure(state="normal"))
        self.after(0, lambda: self.stop_button.configure(state="disabled"))
        self.after(0, self.running_modules.clear)

        if popup_message:
            self.after(
                0,
                lambda: self._show_bottom_popup(popup_message, closable=True),
            )

    def get_config_overrides_from_ui(self):
        """
        Builds runtime configuration overrides from the UI values.

        Returns:
            dict: Configuration overrides to be merged with APP_CONFIG.
        """
        overrides = {
            "modules": {},
            "tools": {},
            "debug": {},
            "logging": {},
            "limits": {},
            "timeouts": {},
            "retries": {},
        }

        for module_key, switch in self.module_switches.items():
            overrides["modules"][module_key] = bool(switch.get())

        for full_key, widget in self.config_entries.items():
            section, key = full_key.split(".", 1)

            raw_value = self._get_widget_value(widget)
            parsed_value = self._parse_setting_value(section, key, raw_value)

            overrides[section][key] = parsed_value

        return overrides

    def _get_widget_value(self, widget):
        """
        Extracts a value from a CustomTkinter widget.

        Args:
            widget: CustomTkinter widget.

        Returns:
            Any: Widget value.
        """
        if isinstance(widget, ctk.CTkSwitch):
            return bool(widget.get())

        if isinstance(widget, ctk.CTkOptionMenu):
            return widget.get()

        return widget.get().strip()

    def _format_setting_value(self, section, key, value):
        """
        Formats a configuration value before displaying it in the UI.

        Args:
            section: Configuration section.
            key: Configuration key.
            value: Raw value.

        Returns:
            str: Display-ready value.
        """
        return str(value)

    def _parse_setting_value(self, section, key, value):
        """
        Parses a UI value before sending it to the execution runner.

        Args:
            section: Configuration section.
            key: Configuration key.
            value: Raw UI value.

        Returns:
            Any: Parsed configuration value.
        """
        if isinstance(value, bool):
            return value

        if section in {"limits", "timeouts", "retries"}:
            try:
                return int(value)
            except ValueError:
                self.status_label.configure(
                    text=f"Invalid value: {SETTING_LABELS.get(key, key)}"
                )
                return value

        return value

    def toggle_theme(self):
        """
        Toggles the application theme between dark and light mode without
        changing the current window size or position.
        """
        current_geometry = self.geometry()

        if self.current_theme == "dark":
            self.current_theme = "light"
            ctk.set_appearance_mode("light")
            self.theme_button.configure(text="Dark mode")
        else:
            self.current_theme = "dark"
            ctk.set_appearance_mode("dark")
            self.theme_button.configure(text="Light mode")

        self._apply_theme()

        self.after(10, lambda: self.geometry(current_geometry))

    def _apply_theme(self):
        """
        Applies the current visual theme to the application.
        """
        is_dark = self.current_theme == "dark"

        bg = self.colors["dark_bg"] if is_dark else self.colors["light_bg"]
        panel = self.colors["dark_panel"] if is_dark else self.colors["light_panel"]
        card = self.colors["dark_card"] if is_dark else self.colors["light_card"]
        soft = self.colors["dark_soft"] if is_dark else self.colors["light_soft"]
        muted = self.colors["muted"] if is_dark else self.colors["light_muted"]

        self.configure(fg_color=bg)
        self.header.configure(fg_color=bg)

        self.main_area.configure(fg_color=panel)
        self.sidebar.configure(fg_color=card)
        self.content_area.configure(fg_color=panel)

        self.execution_tab.configure(fg_color=panel)
        self.data_tab.configure(fg_color=panel)
        self.results_tab.configure(fg_color=panel)
        self.console_tab.configure(fg_color=panel)

        self.title_label.configure(
            text_color=self.colors["accent"] if is_dark else self.colors["text_dark"]
        )
        self.subtitle_label.configure(text_color=muted)

        for name, button in self.tab_buttons.items():
            is_active = name == self.active_tab

            button.configure(
                fg_color=self.colors["accent"] if is_active and is_dark else
                self.colors["blue"] if is_active else
                self.colors["dark_soft"] if is_dark else self.colors["light_soft"],
                hover_color=self.colors["olive"] if is_dark else "#A7B6D8",
                text_color=self.colors["text_dark"] if is_active and is_dark else
                self.colors["text_light"] if is_dark else
                self.colors["text_dark"],
                border_width=2 if is_active else 0,
                border_color=self.colors["accent"] if is_dark else self.colors["blue"],
            )

        self.execution_scroll.configure(fg_color=panel)

        for card_widget in [
            self.execution_card,
            self.global_card,
            self.modules_card,
        ]:
            card_widget.configure(fg_color=card)

        for module_card in self.module_cards.values():
            module_card.configure(fg_color=soft)

        for settings_frame in self.module_settings_frames.values():
            settings_frame.configure(fg_color=card)

        self.status_label.configure(
            fg_color=soft,
            text_color=self.colors["accent"] if is_dark else self.colors["text_dark"],
        )

        if self.all_modules_switch:
            self.all_modules_switch.configure(
                progress_color=self.colors["accent"] if is_dark else self.colors["blue"],
                button_color=self.colors["text_light"] if is_dark else self.colors["text_dark"],
                button_hover_color=self.colors["accent_hover"] if is_dark else "#A7B6D8",
                text_color=self.colors["text_light"] if is_dark else self.colors["text_dark"],
            )

        self.run_button.configure(
            fg_color=self.colors["accent"] if is_dark else self.colors["blue"],
            hover_color=self.colors["accent_hover"] if is_dark else "#A7B6D8",
            text_color=self.colors["text_dark"] if is_dark else self.colors["text_light"],
        )

        if self.stop_button:
            self.stop_button.configure(
                fg_color=self.colors["danger"],
                hover_color=self.colors["danger_hover"],
                text_color=self.colors["text_light"],
            )

        self.theme_button.configure(
            fg_color=self.colors["blue"] if is_dark else self.colors["light_soft"],
            hover_color=self.colors["olive"] if is_dark else "#A7B6D8",
            text_color=self.colors["text_light"] if is_dark else self.colors["text_dark"],
        )

        if self.console_textbox:
            self.console_textbox.configure(
                fg_color=self.colors["dark_bg"] if is_dark else "#F4F6FC",
                text_color=self.colors["text_light"] if is_dark else self.colors["text_dark"],
                border_color=soft,
                border_width=1,
            )
            self._style_console_textbox()

        if self.console_clear_button:
            self.console_clear_button.configure(
                fg_color=self.colors["blue"] if is_dark else self.colors["light_soft"],
                hover_color=self.colors["olive"] if is_dark else "#A7B6D8",
                text_color=self.colors["text_light"] if is_dark else self.colors["text_dark"],
                border_width=0,
            )

        if self.bottom_popup:
            self.bottom_popup.configure(
                fg_color="transparent",
                bg_color=bg,
                corner_radius=0,
            )

        if self.bottom_popup_card:
            self.bottom_popup_card.configure(
                fg_color=self.colors["warning_bg_dark"] if is_dark else self.colors["warning_bg_light"],
                bg_color=bg,
                border_color=self.colors["warning_border_dark"] if is_dark else self.colors["warning_border_light"],
                corner_radius=18,
            )

        if self.bottom_popup_label:
            self.bottom_popup_label.configure(
                text_color=self.colors["warning_text_dark"] if is_dark else self.colors["warning_text_light"],
                fg_color="transparent",
                bg_color=self.colors["warning_bg_dark"] if is_dark else self.colors["warning_bg_light"],
            )

        if self.bottom_popup_close_button:
            self.bottom_popup_close_button.configure(
                fg_color=self.colors["blue"] if is_dark else self.colors["light_soft"],
                hover_color=self.colors["olive"] if is_dark else "#A7B6D8",
                text_color=self.colors["text_light"] if is_dark else self.colors["text_dark"],
                bg_color=self.colors["warning_bg_dark"] if is_dark else self.colors["warning_bg_light"],
                corner_radius=10,
            )

    def _create_card(self, parent, row):
        """
        Creates a generic card frame.

        Args:
            parent: Parent frame.
            row: Grid row.

        Returns:
            CTkFrame: Created card.
        """
        card = ctk.CTkFrame(parent, corner_radius=14)
        card.grid(row=row, column=0, sticky="ew", padx=10, pady=(0, 20))
        card.grid_columnconfigure(0, weight=1)
        return card


if __name__ == "__main__":
    app = ErebusApp()
    app.mainloop()