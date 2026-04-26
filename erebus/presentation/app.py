"""
Main graphical application for EREBUS.

This module contains the root CustomTkinter application. It coordinates the
presentation pages, execution thread, console redirection, notification popup
and global theme.

The detailed layout of each page is delegated to classes inside the pages
package. Reusable widgets are delegated to the widgets package.
"""

import queue
import sys
import threading

import customtkinter as ctk

from application.runner import run_erebus

import presentation.constants as C
from presentation.fonts import load_app_fonts
from presentation.module_ui_metadata import MODULE_UI_CONFIG
from presentation.pages.console_page import ConsolePage
from presentation.pages.execution_page import ExecutionPage
from presentation.pages.placeholder_page import PlaceholderPage
from presentation.services.console_redirector import ConsoleRedirector
from presentation.theme import build_fonts, get_theme_palette
from presentation.widgets.loading_overlay import LoadingOverlay
from presentation.widgets.notification_popup import NotificationPopup


class ErebusApp(ctk.CTk):
    """
    Main CustomTkinter application for EREBUS.

    This class owns the root window, the global layout, the sidebar, the page
    container, the execution thread state, the console redirection and the
    notification popup.

    It intentionally does not contain the detailed layout of the execution,
    console or placeholder pages.
    """

    def __init__(self):
        """
        Initializes the EREBUS graphical application.
        """
        super().__init__()

        load_app_fonts()

        self.title(C.APP_TITLE)

        ctk.set_appearance_mode(C.THEME_DARK)
        ctk.set_default_color_theme(C.DEFAULT_COLOR_THEME)

        self.current_ui_scale_name = C.DEFAULT_UI_SCALE
        self.current_ui_scale = C.UI_SCALE_VALUES[self.current_ui_scale_name]

        ctk.set_widget_scaling(self.current_ui_scale)

        self.fonts = build_fonts(self.current_ui_scale)

        self.current_theme = C.THEME_DARK
        self.active_tab = C.TAB_EXECUTION

        self.tab_buttons = {}

        self.console_queue = queue.Queue()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        self.execution_thread = None
        self.cancel_event = None
        self.running_modules = set()

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

        self._closing = False
        self._pending_overlay_callback_id = None
        self._pending_overlay_hide_id = None

        self.notification_popup = NotificationPopup(
            parent=self,
            fonts=self.fonts,
            get_palette_callback=self._get_palette,
        )
        self.loading_overlay = LoadingOverlay(
            parent=self,
            fonts=self.fonts,
            get_palette_callback=self._get_palette,
        )

        self._set_initial_window_size()
        self._build_ui()
        self._apply_theme()
        self._start_console_redirection()
        self.after(100, self._maximize_window)

    def _get_palette(self):
        """
        Gets the active theme palette.

        Returns:
            dict: Theme-dependent color palette.
        """
        return get_theme_palette(self.current_theme)

    def _set_initial_window_size(self):
        """
        Sets a safe initial window size before the interface is built.

        The real maximized state is applied later, after CustomTkinter has
        finished creating and rendering the main widgets.
        """
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        self.geometry(f"{screen_width}x{screen_height}+0+0")
        self.minsize(C.APP_MIN_WIDTH, C.APP_MIN_HEIGHT)

    def _maximize_window(self):
        """
        Maximizes the application window.

        This is executed after the UI has been built to avoid Windows or Tkinter
        restoring the window back to a normal state during startup.
        """
        if self._closing or not self.winfo_exists():
            return

        try:
            self.state("zoomed")
        except ctk.TclError:
            self.geometry(
                f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0"
            )

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
        Builds the top header with the centered title and the theme button.
        """
        palette = self._get_palette()

        self.header = ctk.CTkFrame(
            self,
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
        self.title_label.grid(row=0, column=0, sticky="n", pady=(0, 0))

        self.subtitle_label = ctk.CTkLabel(
            self.title_container,
            text=C.APP_SUBTITLE,
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

        self.size_menu = ctk.CTkOptionMenu(
            self.header,
            values=C.UI_SCALE_OPTIONS,
            width=150,
            height=36,
            corner_radius=6,
            font=self.fonts["button"],
            dropdown_font=self.fonts["small"],
            command=self.change_ui_scale,
        )
        self.size_menu.set(self.current_ui_scale_name)
        self.size_menu.place(relx=1.0, x=-162, y=18, anchor="ne")

    def _build_main_area(self):
        """
        Builds the main application area.

        The main area contains:
        - a left sidebar with navigation buttons
        - a right content area where pages are displayed
        """
        palette = self._get_palette()

        self.main_area = ctk.CTkFrame(
            self,
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
        self._show_tab(C.TAB_EXECUTION)

    def _build_sidebar(self):
        """
        Builds the left navigation sidebar.
        """
        self.tab_buttons[C.TAB_EXECUTION] = self._create_sidebar_button(
            text=C.TAB_LABELS[C.TAB_EXECUTION],
            row=0,
            command=lambda: self._show_tab(C.TAB_EXECUTION),
        )

        self.tab_buttons[C.TAB_DATA] = self._create_sidebar_button(
            text=C.TAB_LABELS[C.TAB_DATA],
            row=1,
            command=lambda: self._show_tab(C.TAB_DATA),
        )

        self.tab_buttons[C.TAB_RESULTS] = self._create_sidebar_button(
            text=C.TAB_LABELS[C.TAB_RESULTS],
            row=2,
            command=lambda: self._show_tab(C.TAB_RESULTS),
        )

        self.tab_buttons[C.TAB_CONSOLE] = self._create_sidebar_button(
            text=C.TAB_LABELS[C.TAB_CONSOLE],
            row=3,
            command=lambda: self._show_tab(C.TAB_CONSOLE),
        )

    def _create_sidebar_button(self, text, row, command):
        """
        Creates one sidebar navigation button.

        Args:
            text: Button label.
            row: Grid row where the button is placed.
            command: Callback executed when the button is clicked.

        Returns:
            CTkButton: Created sidebar button.
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

    def _build_pages(self):
        """
        Creates all application pages and places them in the content area.
        """
        self.execution_tab = ExecutionPage(
            parent=self.content_area,
            fonts=self.fonts,
            on_start=self.start_execution,
            on_stop=self.stop_execution,
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

        for page in (
            self.execution_tab,
            self.data_tab,
            self.results_tab,
            self.console_tab,
        ):
            page.grid(row=0, column=0, sticky="nsew")

    def _show_tab(self, tab_name):
        """
        Displays the selected page and hides the rest.

        Args:
            tab_name: Name of the tab to display.
        """
        self.execution_tab.grid_remove()
        self.data_tab.grid_remove()
        self.results_tab.grid_remove()
        self.console_tab.grid_remove()

        selected_page = None

        if tab_name == C.TAB_EXECUTION:
            selected_page = self.execution_tab
        elif tab_name == C.TAB_DATA:
            selected_page = self.data_tab
        elif tab_name == C.TAB_RESULTS:
            selected_page = self.results_tab
        elif tab_name == C.TAB_CONSOLE:
            selected_page = self.console_tab

        if selected_page:
            selected_page.grid()
            selected_page.tkraise()

        self.active_tab = tab_name
        self._apply_theme()

    def toggle_theme(self):
        """
        Toggles the application theme between dark and light mode.
        """
        self._run_with_loading_overlay(
            message="Applying theme...",
            callback=self._apply_theme_change,
        )

    def _apply_theme_change(self):
        """
        Applies the actual theme change while the loading overlay is visible.
        """
        was_zoomed = self.state() == "zoomed"
        current_tab = self.active_tab

        if self.current_theme == C.THEME_DARK:
            self.current_theme = C.THEME_LIGHT
            ctk.set_appearance_mode(C.THEME_LIGHT)
            self.theme_button.configure(text="Dark mode")
        else:
            self.current_theme = C.THEME_DARK
            ctk.set_appearance_mode(C.THEME_DARK)
            self.theme_button.configure(text="Light mode")

        self._apply_theme()
        self._raise_active_tab(current_tab)

        if was_zoomed:
            self.after(10, self._maximize_window)

    def _apply_theme(self):
        """
        Applies the current visual theme to the main application and pages.
        """
        palette = self._get_palette()

        self.configure(fg_color=palette["bg"])

        if self.header:
            self.header.configure(fg_color=palette["bg"])

        if self.main_area:
            self.main_area.configure(fg_color=palette["panel"])

        if self.sidebar:
            self.sidebar.configure(fg_color=palette["card"])

        if self.content_area:
            self.content_area.configure(fg_color=palette["panel"])

        if self.title_label:
            self.title_label.configure(text_color=palette["primary"])

        if self.subtitle_label:
            self.subtitle_label.configure(text_color=palette["muted"])

        if self.theme_button:
            self.theme_button.configure(
                fg_color=palette["secondary"],
                hover_color=palette["secondary_hover"],
                text_color=palette["text"],
            )

        if self.size_menu:
            self.size_menu.configure(
                fg_color=palette["secondary"],
                button_color=palette["secondary"],
                button_hover_color=palette["secondary_hover"],
                text_color=palette["text"],
                dropdown_fg_color=palette["card"],
                dropdown_hover_color=palette["soft"],
                dropdown_text_color=palette["text"],
            )

        for name, button in self.tab_buttons.items():
            is_active = name == self.active_tab

            button.configure(
                fg_color=palette["primary"] if is_active else palette["soft"],
                hover_color=palette["secondary_hover"],
                text_color=palette["inverse_text"] if is_active else palette["text"],
                border_width=2 if is_active else 0,
                border_color=palette["primary"],
            )

        if self.execution_tab:
            self.execution_tab.apply_theme(palette)

        if self.data_tab:
            self.data_tab.apply_theme(palette)

        if self.results_tab:
            self.results_tab.apply_theme(palette)

        if self.console_tab:
            self.console_tab.apply_theme(palette)

        self.notification_popup.apply_theme()
        self.loading_overlay.apply_theme()

    def _start_console_redirection(self):
        """
        Redirects stdout and stderr to the GUI console.

        The original streams are preserved so they can be restored when the
        application closes.
        """
        sys.stdout = ConsoleRedirector(self.console_queue, "stdout")
        sys.stderr = ConsoleRedirector(self.console_queue, "stderr")

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(C.CONSOLE_POLL_INTERVAL_MS, self._process_console_queue)

    def _process_console_queue(self):
        """
        Processes pending console messages from the queue.

        This method runs on the Tkinter main thread, which makes it safe to
        update CustomTkinter widgets.
        """
        if self._closing or not self.winfo_exists():
            return

        try:
            while True:
                stream_name, message = self.console_queue.get_nowait()

                if stream_name == "stderr":
                    self.console_tab.append(message, is_error=True)
                else:
                    self.console_tab.append(message)

        except queue.Empty:
            pass

        self.after(C.CONSOLE_POLL_INTERVAL_MS, self._process_console_queue)

    def _on_close(self):
        """
        Restores stdout and stderr before closing the application.
        """
        self._closing = True

        if self._pending_overlay_callback_id:
            try:
                self.after_cancel(self._pending_overlay_callback_id)
            except Exception:
                pass
            self._pending_overlay_callback_id = None

        if self._pending_overlay_hide_id:
            try:
                self.after_cancel(self._pending_overlay_hide_id)
            except Exception:
                pass
            self._pending_overlay_hide_id = None

        try:
            self.loading_overlay.hide()
        except Exception:
            pass

        try:
            self.notification_popup.hide()
        except Exception:
            pass

        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        self.destroy()

    def start_execution(self):
        """
        Starts an EREBUS execution in a background thread.
        """
        target = self.execution_tab.get_target()

        if not target:
            self.execution_tab.set_status(C.STATUS_MISSING_DOMAIN)
            return

        if self.execution_thread and self.execution_thread.is_alive():
            self.execution_tab.set_status(C.STATUS_ALREADY_RUNNING)
            return

        config_overrides = self.execution_tab.get_config_overrides()

        self.cancel_event = threading.Event()
        self.running_modules.clear()

        self.notification_popup.show(
            C.EXECUTION_STARTING_POPUP.format(target=target),
            closable=True,
            play_sound=True,
        )
        self.execution_tab.set_running_state(True)
        self.execution_tab.set_status(C.STATUS_RUNNING)

        self.execution_thread = threading.Thread(
            target=self._run_in_background,
            args=(target, config_overrides, self.cancel_event),
            daemon=True,
        )
        self.execution_thread.start()

    def stop_execution(self):
        """
        Requests the current execution to stop safely.

        The execution thread is not killed directly. Instead, a cancellation
        event is set so the engine can stop between modules or phases without
        corrupting data.
        """
        if not self.execution_thread or not self.execution_thread.is_alive():
            self.execution_tab.set_status(C.STATUS_NO_EXECUTION_RUNNING)
            return

        if self.cancel_event:
            self.cancel_event.set()

        current = self._get_running_modules_text()

        self.execution_tab.set_cancelling_state()

        self.notification_popup.show(
            C.STOP_REQUESTED_POPUP.format(current=current),
            closable=True,
            play_sound=True,
        )

        print(C.STOP_REQUESTED_CONSOLE)

    def _run_in_background(self, target, config_overrides, cancel_event):
        """
        Runs the EREBUS engine in a background thread.

        Args:
            target: Target domain.
            config_overrides: Runtime configuration overrides from the UI.
            cancel_event: Event used to request safe cancellation.
        """
        try:
            execution = run_erebus(
                target=target,
                config_overrides=config_overrides,
                cancel_event=cancel_event,
                progress_callback=self.on_module_progress,
            )

            if cancel_event and cancel_event.is_set():
                message = C.STATUS_CANCELLED
                popup_message = C.EXECUTION_CANCELLED_POPUP

            elif execution:
                message = f"Status: {execution.STATUS}"
                popup_message = C.EXECUTION_FINISHED_POPUP.format(
                    target=target,
                    status=execution.STATUS,
                )

            else:
                message = C.STATUS_EXECUTION_FAILED
                popup_message = C.EXECUTION_FAILED_POPUP.format(target=target)

        except Exception as exc:
            message = C.STATUS_EXECUTION_FAILED
            popup_message = C.EXECUTION_FAILED_POPUP.format(target=target)
            print(f"[GUI] Execution failed: {exc}", file=sys.stderr)

        if self._closing or not self.winfo_exists():
            return

        self.after(0, lambda: self.execution_tab.set_status(message))
        self.after(0, lambda: self.execution_tab.set_running_state(False))
        self.after(0, self.running_modules.clear)

        if popup_message:
            self.after(
                0,
                lambda: self.notification_popup.show(
                    popup_message,
                    closable=True,
                    play_sound=True,
                ),
            )

    def on_module_progress(self, event_type, module_key):
        """
        Receives module progress events from the orchestrator.

        Args:
            event_type: Event type. Expected values are 'start', 'end' or 'error'.
            module_key: Internal module key.
        """
        if self._closing or not self.winfo_exists():
            return

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

            self.notification_popup.update_message(
                C.STOP_REQUESTED_UPDATE.format(current=current)
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

    def change_ui_scale(self, scale_name):
        """
        Changes the global interface scale.

        The scale affects widget dimensions and semantic font sizes. This allows
        the user to choose between small, medium, large and very large interface
        sizes without restarting the application.

        Args:
            scale_name: Selected scale name.
        """
        if scale_name not in C.UI_SCALE_VALUES:
            return

        self._run_with_loading_overlay(
            message="Resizing interface...",
            callback=lambda: self._apply_ui_scale_change(scale_name),
        )

    def _apply_ui_scale_change(self, scale_name):
        """
        Applies the actual UI scale change while the loading overlay is visible.

        Args:
            scale_name: Selected scale name.
        """
        current_tab = self.active_tab
        was_zoomed = self.state() == "zoomed"

        self.current_ui_scale_name = scale_name
        self.current_ui_scale = C.UI_SCALE_VALUES[scale_name]

        ctk.set_widget_scaling(self.current_ui_scale)
        self._configure_font_sizes()

        if self.size_menu:
            self.size_menu.set(scale_name)

        self._apply_theme()
        self._raise_active_tab(current_tab)

        if was_zoomed:
            self.after(10, self._maximize_window)

    def _configure_font_sizes(self):
        """
        Updates the existing CTkFont objects according to the current UI scale.

        CTkFont instances are shared by widgets, so changing their size updates the
        visible text without recreating the whole interface.
        """
        for font_key, font in self.fonts.items():
            if font_key not in C.FONT_BASE_SIZES:
                continue

            scaled_size = max(
                1,
                int(round(C.FONT_BASE_SIZES[font_key] * self.current_ui_scale)),
            )
            font.configure(size=scaled_size)

    def _run_with_loading_overlay(self, message, callback):
        """
        Runs a visual update while showing a temporary loading overlay.

        The overlay is displayed first and the visual update is delayed slightly so
        Tkinter has time to paint the overlay before the expensive redraw starts.

        Args:
            message: Message displayed in the overlay.
            callback: Function executed while the overlay is visible.
        """
        if self._closing or not self.winfo_exists():
            return

        self.loading_overlay.show(message)

        self._pending_overlay_callback_id = self.after(
            C.LOADING_OVERLAY_START_DELAY_MS,
            lambda: self._execute_overlay_callback(callback),
        )

    def _execute_overlay_callback(self, callback):
        """
        Executes a delayed callback and hides the loading overlay afterwards.

        The overlay remains visible for a short delay after the callback finishes so
        the user does not see the final redraw and geometry recalculation.

        Args:
            callback: Function to execute.
        """
        self._pending_overlay_callback_id = None

        if self._closing or not self.winfo_exists():
            return

        try:
            callback()
            self.update_idletasks()
        finally:
            if self._closing or not self.winfo_exists():
                return

            self._pending_overlay_hide_id = self.after(
                C.LOADING_OVERLAY_HIDE_DELAY_MS,
                self._hide_loading_overlay_safe,
            )

    def _hide_loading_overlay_safe(self):
        """
        Hides the loading overlay safely if the application is still alive.
        """
        self._pending_overlay_hide_id = None

        if self._closing or not self.winfo_exists():
            return

        self.loading_overlay.hide()

    def _raise_active_tab(self, tab_name):
        """
        Raises the selected tab without reapplying the visual theme.

        This is useful during theme and scale changes because applying the theme
        twice causes extra redraw flickering.

        Args:
            tab_name: Name of the tab to raise.
        """
        page = None

        if tab_name == C.TAB_EXECUTION:
            page = self.execution_tab
        elif tab_name == C.TAB_DATA:
            page = self.data_tab
        elif tab_name == C.TAB_RESULTS:
            page = self.results_tab
        elif tab_name == C.TAB_CONSOLE:
            page = self.console_tab

        if page:
            page.grid()
            page.tkraise()

        self.active_tab = tab_name


if __name__ == "__main__":
    app = ErebusApp()
    app.mainloop()