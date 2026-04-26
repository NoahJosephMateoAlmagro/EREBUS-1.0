"""
Appearance controller for EREBUS.

This module contains the controller responsible for theme changes, UI scale
changes, font resizing and temporary loading overlay handling.
"""

import customtkinter as ctk

import presentation.constants as C
from presentation.theme import get_theme_palette


class AppearanceController:
    """
    Controls application appearance, including theme and UI scale.
    """

    def __init__(self, app, layout, fonts, notification_popup, loading_overlay):
        """
        Initializes the appearance controller.

        Args:
            app: Root application instance.
            layout: Built application layout.
            fonts: Shared CTkFont dictionary.
            notification_popup: Notification popup widget.
            loading_overlay: Loading overlay widget.
        """
        self.app = app
        self.layout = layout
        self.fonts = fonts
        self.notification_popup = notification_popup
        self.loading_overlay = loading_overlay

        self._pending_overlay_callback_id = None
        self._pending_overlay_hide_id = None

    def get_palette(self) -> dict:
        """
        Gets the active palette according to the current theme.

        Returns:
            dict: Active theme palette.
        """
        return get_theme_palette(self.app.current_theme)

    def apply_theme(self) -> None:
        """
        Applies the current visual theme to the application and all pages.
        """
        palette = self.get_palette()

        self.app.configure(fg_color=palette["bg"])

        if self.layout.header:
            self.layout.header.configure(fg_color=palette["bg"])

        if self.layout.main_area:
            self.layout.main_area.configure(fg_color=palette["panel"])

        if self.layout.sidebar:
            self.layout.sidebar.configure(fg_color=palette["card"])

        if self.layout.content_area:
            self.layout.content_area.configure(fg_color=palette["panel"])

        if self.layout.title_label:
            self.layout.title_label.configure(text_color=palette["primary"])

        if self.layout.subtitle_label:
            self.layout.subtitle_label.configure(text_color=palette["muted"])

        if self.layout.theme_button:
            self.layout.theme_button.configure(
                fg_color=palette["secondary"],
                hover_color=palette["secondary_hover"],
                text_color=palette["text"],
            )

        if self.layout.size_menu:
            self.layout.size_menu.configure(
                fg_color=palette["secondary"],
                button_color=palette["secondary"],
                button_hover_color=palette["secondary_hover"],
                text_color=palette["text"],
                dropdown_fg_color=palette["card"],
                dropdown_hover_color=palette["soft"],
                dropdown_text_color=palette["text"],
            )

        for name, button in self.layout.tab_buttons.items():
            is_active = name == self.app.active_tab

            button.configure(
                fg_color=palette["primary"] if is_active else palette["soft"],
                hover_color=palette["secondary_hover"],
                text_color=palette["inverse_text"] if is_active else palette["text"],
                border_width=2 if is_active else 0,
                border_color=palette["primary"],
            )

        for page in self.layout.pages.values():
            page.apply_theme(palette)

        self.notification_popup.apply_theme()
        self.loading_overlay.apply_theme()

    def toggle_theme(self) -> None:
        """
        Toggles the application theme between dark and light mode.
        """
        self._run_with_loading_overlay(
            message="Applying theme...",
            callback=self._apply_theme_change,
        )

    def change_ui_scale(self, scale_name: str) -> None:
        """
        Changes the global UI scale.

        Args:
            scale_name: Selected scale name.
        """
        if scale_name not in C.UI_SCALE_VALUES:
            return

        self._run_with_loading_overlay(
            message="Resizing interface...",
            callback=lambda: self._apply_ui_scale_change(scale_name),
        )

    def _apply_theme_change(self) -> None:
        """
        Applies the current theme change while the loading overlay is visible.
        """
        was_zoomed = self.app.state() == "zoomed"
        current_tab = self.app.active_tab

        if self.app.current_theme == C.THEME_DARK:
            self.app.current_theme = C.THEME_LIGHT
            ctk.set_appearance_mode(C.THEME_LIGHT)
            self.layout.theme_button.configure(text="Dark mode")
        else:
            self.app.current_theme = C.THEME_DARK
            ctk.set_appearance_mode(C.THEME_DARK)
            self.layout.theme_button.configure(text="Light mode")

        self.apply_theme()
        self.app.navigation.raise_active_tab(current_tab)

        if was_zoomed:
            self.app.after(10, self.app.maximize_window)

    def _apply_ui_scale_change(self, scale_name: str) -> None:
        """
        Applies the selected UI scale while the loading overlay is visible.

        Args:
            scale_name: Selected scale name.
        """
        current_tab = self.app.active_tab
        was_zoomed = self.app.state() == "zoomed"

        self.app.current_ui_scale_name = scale_name
        self.app.current_ui_scale = C.UI_SCALE_VALUES[scale_name]

        ctk.set_widget_scaling(self.app.current_ui_scale)
        self._configure_font_sizes()

        if self.layout.size_menu:
            self.layout.size_menu.set(scale_name)

        self.apply_theme()
        self.app.navigation.raise_active_tab(current_tab)

        if was_zoomed:
            self.app.after(10, self.app.maximize_window)

    def _configure_font_sizes(self) -> None:
        """
        Updates the existing CTkFont objects according to the current UI scale.
        """
        for font_key, font in self.fonts.items():
            if font_key not in C.FONT_BASE_SIZES:
                continue

            scaled_size = max(
                1,
                int(round(C.FONT_BASE_SIZES[font_key] * self.app.current_ui_scale)),
            )
            font.configure(size=scaled_size)

    def _run_with_loading_overlay(self, message: str, callback) -> None:
        """
        Runs a visual update while showing a temporary loading overlay.

        Args:
            message: Message displayed in the overlay.
            callback: Function executed while the overlay is visible.
        """
        if self.app._closing or not self.app.winfo_exists():
            return

        self.loading_overlay.show(message)

        self._pending_overlay_callback_id = self.app.after(
            C.LOADING_OVERLAY_START_DELAY_MS,
            lambda: self._execute_overlay_callback(callback),
        )

    def _execute_overlay_callback(self, callback) -> None:
        """
        Executes a delayed callback and hides the loading overlay afterwards.

        Args:
            callback: Function to execute.
        """
        self._pending_overlay_callback_id = None

        if self.app._closing or not self.app.winfo_exists():
            return

        try:
            callback()
            self.app.update_idletasks()
        finally:
            if self.app._closing or not self.app.winfo_exists():
                return

            self._pending_overlay_hide_id = self.app.after(
                C.LOADING_OVERLAY_HIDE_DELAY_MS,
                self._hide_loading_overlay_safe,
            )

    def _hide_loading_overlay_safe(self) -> None:
        """
        Hides the loading overlay safely if the application is still alive.
        """
        self._pending_overlay_hide_id = None

        if self.app._closing or not self.app.winfo_exists():
            return

        self.loading_overlay.hide()

    def cancel_pending_updates(self) -> None:
        """
        Cancels pending overlay callbacks scheduled with Tkinter's event loop.
        """
        if self._pending_overlay_callback_id:
            try:
                self.app.after_cancel(self._pending_overlay_callback_id)
            except Exception:
                pass
            self._pending_overlay_callback_id = None

        if self._pending_overlay_hide_id:
            try:
                self.app.after_cancel(self._pending_overlay_hide_id)
            except Exception:
                pass
            self._pending_overlay_hide_id = None