"""
Main graphical application for EREBUS.

This module contains the root CustomTkinter application. It coordinates the
main layout, navigation, appearance, execution lifecycle, console redirection
and popup widgets.

Detailed UI construction and specialized behaviors are delegated to dedicated
presentation controllers and builders.
"""

import customtkinter as ctk

import presentation.constants as C
from presentation.fonts import load_app_fonts
from presentation.layout.app_layout import AppLayout
from presentation.services.appearance_controller import AppearanceController
from presentation.services.console_controller import ConsoleController
from presentation.services.execution_controller import ExecutionController
from presentation.services.navigation_controller import NavigationController
from presentation.services.user_preference_service import UserPreferencesService
from presentation.theme import build_fonts
from presentation.widgets.loading_overlay import LoadingOverlay
from presentation.widgets.notification_popup import NotificationPopup
from persistence.database import Database


class ErebusApp(ctk.CTk):
    """
    Root CustomTkinter application for EREBUS.

    This class owns the top-level window and coordinates the presentation layer
    controllers. It intentionally keeps only high-level orchestration logic.
    """

    def __init__(self):
        """
        Initializes the EREBUS graphical application.
        """
        super().__init__()

        self.database = Database()
        self.withdraw()

        load_app_fonts()

        self.title(C.APP_TITLE)

        ctk.set_appearance_mode(C.THEME_DARK)
        ctk.set_default_color_theme(C.DEFAULT_COLOR_THEME)

        self.current_theme = C.THEME_DARK
        self.current_ui_scale_name = C.DEFAULT_UI_SCALE
        self.current_ui_scale = C.UI_SCALE_VALUES[self.current_ui_scale_name]
        self.active_tab = C.TAB_EXECUTION
        self._closing = False

        ctk.set_widget_scaling(self.current_ui_scale)
        self.fonts = build_fonts(self.current_ui_scale)

        self._set_initial_window_size()

        self.layout = AppLayout(
            parent=self,
            fonts=self.fonts,
            on_show_tab=self.show_tab,
            on_toggle_theme=self.toggle_theme,
            on_change_ui_scale=self.change_ui_scale,
            on_start_execution=self.start_execution,
            on_stop_execution=self.stop_execution,
            on_api_key_saved=self.show_api_key_saved_notification,
        )
        self.layout.build()

        self.notification_popup = NotificationPopup(
            parent=self,
            fonts=self.fonts,
            get_palette_callback=lambda: self.appearance.get_palette(),
        )
        self.loading_overlay = LoadingOverlay(
            parent=self,
            fonts=self.fonts,
            get_palette_callback=lambda: self.appearance.get_palette(),
        )

        self.user_preferences_service = UserPreferencesService()

        self.navigation = NavigationController(
            app=self,
            layout=self.layout,
        )

        self.appearance = AppearanceController(
            app=self,
            layout=self.layout,
            fonts=self.fonts,
            notification_popup=self.notification_popup,
            loading_overlay=self.loading_overlay,
        )

        self.console_controller = ConsoleController(
            app=self,
            console_page=self.layout.console_tab,
        )

        self.execution_controller = ExecutionController(
            app=self,
            execution_page=self.layout.execution_tab,
            notification_popup=self.notification_popup,
            user_preferences_service=self.user_preferences_service,
        )

        self.appearance.apply_theme()
        self.navigation.show_tab(C.TAB_EXECUTION)

        self.execution_controller.load_persistent_state()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.console_controller.start()

        self.after_idle(self._show_startup_window)

    def _set_initial_window_size(self) -> None:
        """
        Sets the initial window size using a centered 16:9 layout.

        The application starts in a large normal window instead of forcing an
        unreliable maximized state. The user can maximize it manually later.
        """
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        max_width = int(screen_width * 0.85)
        max_height = int(screen_height * 0.85)

        width_from_height = int(max_height * (16 / 9))
        height_from_width = int(max_width * (9 / 16))

        if width_from_height <= max_width:
            width = width_from_height
            height = max_height
        else:
            width = max_width
            height = height_from_width

        width = max(width, C.APP_MIN_WIDTH)
        height = max(height, C.APP_MIN_HEIGHT)

        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(C.APP_MIN_WIDTH, C.APP_MIN_HEIGHT)

    def _show_startup_window(self) -> None:
        """
        Shows the window after the interface has been fully built and laid out.
        """
        if self._closing or not self.winfo_exists():
            return

        self.update_idletasks()
        self.deiconify()
        self.lift()
        self.focus_force()

    def maximize_window(self) -> None:
        """
        Maximizes the application window if requested explicitly.
        """
        if self._closing or not self.winfo_exists():
            return

        try:
            self.state("zoomed")
        except ctk.TclError:
            self.geometry(
                f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0"
            )

        self.update_idletasks()

    def show_tab(self, tab_name: str) -> None:
        """
        Delegates tab display to the navigation controller.

        Args:
            tab_name: Internal tab name to display.
        """
        self.navigation.show_tab(tab_name)

    def toggle_theme(self) -> None:
        """
        Delegates theme toggling to the appearance controller.
        """
        self.appearance.toggle_theme()

    def change_ui_scale(self, scale_name: str) -> None:
        """
        Delegates UI scale changes to the appearance controller.

        Args:
            scale_name: Selected scale name.
        """
        self.appearance.change_ui_scale(scale_name)

    def start_execution(self) -> None:
        """
        Delegates execution start to the execution controller.
        """
        self.execution_controller.start_execution()

    def stop_execution(self) -> None:
        """
        Delegates execution stop to the execution controller.
        """
        self.execution_controller.stop_execution()

    def show_api_key_saved_notification(self, provider: str) -> None:
        """
        Shows a notification after an API key has been saved.

        Args:
            provider: API provider display name.
        """
        if self._closing or not self.winfo_exists():
            return

        if not hasattr(self, "notification_popup"):
            return

        self.notification_popup.show(
            C.API_KEY_SAVED_POPUP.format(provider=provider),
            closable=True,
            play_sound=True,
        )

    def on_close(self) -> None:
        """
        Restores resources and closes the application safely.
        """
        self._closing = True

        try:
            self.execution_controller.save_persistent_state()
        except Exception:
            pass

        try:
            self.appearance.cancel_pending_updates()
        except Exception:
            pass

        try:
            self.loading_overlay.hide()
        except Exception:
            pass

        try:
            self.notification_popup.hide()
        except Exception:
            pass

        try:
            self.console_controller.restore_streams()
        except Exception:
            pass

        try:
            self.database.close()
        except Exception:
            pass

        self.destroy()


if __name__ == "__main__":
    app = ErebusApp()
    app.mainloop()