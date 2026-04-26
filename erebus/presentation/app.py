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

        self.after(100, self.maximize_window)

    def _set_initial_window_size(self) -> None:
        """
        Sets a safe initial window size before the full UI is rendered.
        """
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        self.geometry(f"{screen_width}x{screen_height}+0+0")
        self.minsize(C.APP_MIN_WIDTH, C.APP_MIN_HEIGHT)

    def maximize_window(self) -> None:
        """
        Maximizes the application window.

        This is executed after the interface has been built to avoid the window
        being restored to a normal state during startup.
        """
        if self._closing or not self.winfo_exists():
            return

        try:
            self.state("zoomed")
        except ctk.TclError:
            self.geometry(
                f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0"
            )

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
            scale_name: Selected UI scale name.
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

        self.destroy()


if __name__ == "__main__":
    app = ErebusApp()
    app.mainloop()