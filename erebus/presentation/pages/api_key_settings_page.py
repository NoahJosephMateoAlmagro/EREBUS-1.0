"""
API key settings page for the EREBUS graphical interface.

This page allows the user to configure API credentials used by optional
API-based modules. At the moment it provides Shodan API key management.
"""

from __future__ import annotations

import sys

import customtkinter as ctk

import presentation.constants as C
from presentation.services.api_key_settings_service import ApiKeySettingsService
from presentation.widgets.cards import create_card


class ApiKeySettingsPage(ctk.CTkFrame):
    """
    Page used to manage API credentials.
    """

    SHODAN_PROVIDER = "shodan"
    TEXT_SIDE_MARGIN = 96

    def __init__(self, parent, fonts, on_api_key_saved=None):
        """
        Initializes the API key settings page.

        Args:
            parent: Parent widget.
            fonts: Application font catalog.
            on_api_key_saved: Optional callback executed after saving a key.
        """
        super().__init__(parent, corner_radius=0)

        self.fonts = fonts
        self.on_api_key_saved = on_api_key_saved
        self.api_key_service = ApiKeySettingsService()

        self.current_palette = None
        self.api_key_visible = False

        self.page_scroll = None
        self.header_card = None
        self.shodan_card = None
        self.future_card = None

        self.description_textbox = None
        self.future_textbox = None

        self.shodan_description_label = None
        self.shodan_policy_label = None

        self.api_key_entry = None
        self.toggle_visibility_button = None
        self.save_button = None
        self.status_label = None

        self._build()
        self.load_saved_api_key()

    def _build(self) -> None:
        """
        Builds the API key settings page.
        """
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.page_scroll = ctk.CTkScrollableFrame(
            self,
            corner_radius=0,
        )
        self.page_scroll.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=10,
            pady=10,
        )
        self.page_scroll.grid_columnconfigure(0, weight=1)

        self._build_header_card()
        self._build_shodan_card()
        self._build_future_card()

    def _build_header_card(self) -> None:
        """
        Builds the page header card.
        """
        self.header_card = create_card(self.page_scroll, row=0)
        self.header_card.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self.header_card,
            text=C.API_KEYS_TITLE,
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
            pady=(0, 20),
        )
        self._set_textbox_text(
            self.description_textbox,
            C.API_KEYS_DESCRIPTION,
        )

    def _build_shodan_card(self) -> None:
        """
        Builds the Shodan API key configuration card.
        """
        self.shodan_card = create_card(self.page_scroll, row=1)
        self.shodan_card.grid_columnconfigure(0, weight=1)
        self.shodan_card.bind("<Configure>", self._update_shodan_text_wraplength)

        title = ctk.CTkLabel(
            self.shodan_card,
            text=C.SHODAN_API_TITLE,
            font=self.fonts["section"],
        )
        title.grid(
            row=0,
            column=0,
            sticky="w",
            padx=24,
            pady=(22, 8),
        )

        self.shodan_description_label = ctk.CTkLabel(
            self.shodan_card,
            text=C.SHODAN_API_DESCRIPTION,
            font=self.fonts["body"],
            justify="left",
            anchor="w",
            wraplength=980,
        )
        self.shodan_description_label.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=24,
            pady=(0, 10),
        )

        self.shodan_policy_label = ctk.CTkLabel(
            self.shodan_card,
            text=C.SHODAN_API_TOKEN_POLICY_TEXT,
            font=self.fonts["body"],
            justify="left",
            anchor="w",
            wraplength=980,
        )
        self.shodan_policy_label.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=24,
            pady=(0, 18),
        )

        form = ctk.CTkFrame(
            self.shodan_card,
            fg_color="transparent",
        )
        form.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=24,
            pady=(0, 16),
        )
        form.grid_columnconfigure(0, weight=0)
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(2, weight=0)
        form.grid_columnconfigure(3, weight=0)

        label = ctk.CTkLabel(
            form,
            text=C.SHODAN_API_KEY_LABEL,
            font=self.fonts["body_bold"],
        )
        label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 14),
        )

        self.api_key_entry = ctk.CTkEntry(
            form,
            height=42,
            font=self.fonts["body"],
            placeholder_text=C.SHODAN_API_KEY_PLACEHOLDER,
            show="•",
        )
        self.api_key_entry.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(0, 10),
        )
        self.api_key_entry.bind(
            "<Return>",
            lambda _event: self.save_api_key(),
        )

        self.toggle_visibility_button = ctk.CTkButton(
            form,
            text=C.API_KEY_SHOW_BUTTON,
            width=70,
            height=42,
            corner_radius=6,
            font=self.fonts["button"],
            command=self.toggle_api_key_visibility,
        )
        self.toggle_visibility_button.grid(
            row=0,
            column=2,
            sticky="e",
            padx=(0, 10),
        )

        self.save_button = ctk.CTkButton(
            form,
            text=C.API_KEY_SAVE_BUTTON,
            width=150,
            height=42,
            corner_radius=6,
            font=self.fonts["button"],
            command=self.save_api_key,
        )
        self.save_button.grid(
            row=0,
            column=3,
            sticky="e",
        )

        self.status_label = ctk.CTkLabel(
            self.shodan_card,
            text=C.API_KEY_STATUS_READY,
            font=self.fonts["small_bold"],
            justify="left",
        )
        self.status_label.grid(
            row=4,
            column=0,
            sticky="w",
            padx=24,
            pady=(0, 22),
        )

    def _build_future_card(self) -> None:
        """
        Builds the bottom future API providers information card.
        """
        self.future_card = create_card(self.page_scroll, row=2)
        self.future_card.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self.future_card,
            text=C.API_KEYS_FUTURE_TITLE,
            font=self.fonts["section"],
        )
        title.grid(
            row=0,
            column=0,
            sticky="w",
            padx=24,
            pady=(22, 8),
        )

        self.future_textbox = ctk.CTkTextbox(
            self.future_card,
            height=self._get_future_text_height(),
            font=self.fonts["small"],
            wrap="word",
            corner_radius=0,
            border_width=0,
            activate_scrollbars=False,
        )
        self.future_textbox.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=24,
            pady=(0, 22),
        )
        self._set_textbox_text(
            self.future_textbox,
            C.API_KEYS_FUTURE_TEXT,
        )

    def load_saved_api_key(self) -> None:
        """
        Loads the active Shodan API key from the database.
        """
        if not self.api_key_entry:
            return

        try:
            api_key = self.api_key_service.get_api_key(
                self.SHODAN_PROVIDER
            )

            self.api_key_entry.delete(0, "end")

            if api_key:
                self.api_key_entry.insert(0, api_key)
                self._set_status(C.API_KEY_STATUS_LOADED)
            else:
                self._set_status(C.API_KEY_STATUS_EMPTY)

        except Exception as exc:
            self._set_status(C.API_KEY_STATUS_LOAD_ERROR)
            print(f"[GUI] Could not load Shodan API key: {exc}", file=sys.stderr)

    def save_api_key(self) -> None:
        """
        Saves the Shodan API key into the database.
        """
        if not self.api_key_entry:
            return

        api_key = self.api_key_entry.get().strip()

        if not api_key:
            self._set_status(C.API_KEY_STATUS_EMPTY_KEY)
            return

        try:
            self.api_key_service.save_api_key(
                provider=self.SHODAN_PROVIDER,
                api_key=api_key,
                description=C.SHODAN_API_KEY_DESCRIPTION,
            )

            self._set_status(C.API_KEY_STATUS_SAVED)

            if self.on_api_key_saved:
                self.on_api_key_saved(C.SHODAN_API_DISPLAY_NAME)

        except Exception as exc:
            self._set_status(C.API_KEY_STATUS_SAVE_ERROR)
            print(f"[GUI] Could not save Shodan API key: {exc}", file=sys.stderr)

    def toggle_api_key_visibility(self) -> None:
        """
        Toggles whether the API key entry is masked or visible.
        """
        if not self.api_key_entry:
            return

        self.api_key_visible = not self.api_key_visible

        if self.api_key_visible:
            self.api_key_entry.configure(show="")
            self.toggle_visibility_button.configure(text=C.API_KEY_HIDE_BUTTON)
        else:
            self.api_key_entry.configure(show="•")
            self.toggle_visibility_button.configure(text=C.API_KEY_SHOW_BUTTON)

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

    def _update_shodan_text_wraplength(self, event=None) -> None:
        """
        Updates Shodan card label wrap length according to the available width.

        Args:
            event: Tkinter configure event.
        """
        if event is not None:
            card_width = event.width
        elif self.shodan_card:
            card_width = self.shodan_card.winfo_width()
        else:
            return

        available_width = max(300, card_width - self.TEXT_SIDE_MARGIN)

        for label in [
            self.shodan_description_label,
            self.shodan_policy_label,
        ]:
            if label:
                label.configure(wraplength=available_width)

    def _get_description_height(self) -> int:
        """
        Calculates a safe description textbox height.

        Returns:
            int: Textbox height in pixels.
        """
        try:
            font_size = abs(int(self.fonts["body"].cget("size")))
        except Exception:
            font_size = 14

        return max(62, int(font_size * 5.0))

    def _get_future_text_height(self) -> int:
        """
        Calculates a safe future-message textbox height.

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
            text_color: Optional text color.
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

    def _set_status(self, text: str) -> None:
        """
        Updates the status label.

        Args:
            text: Status text.
        """
        if self.status_label:
            self.status_label.configure(text=text)

    def apply_theme(self, palette: dict) -> None:
        """
        Applies the active theme to the API key settings page.

        Args:
            palette: Active theme palette.
        """
        self.current_palette = palette

        self.configure(fg_color=palette["panel"])

        if self.page_scroll:
            self.page_scroll.configure(fg_color=palette["panel"])

        for card in [
            self.header_card,
            self.shodan_card,
            self.future_card,
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
            textbox=self.future_textbox,
            palette=palette,
            height=self._get_future_text_height(),
            text_color=palette["muted"],
        )

        if self.shodan_description_label:
            self.shodan_description_label.configure(text_color=palette["text"])

        if self.shodan_policy_label:
            self.shodan_policy_label.configure(text_color=palette["muted"])

        if self.api_key_entry:
            self.api_key_entry.configure(
                fg_color=palette["soft"],
                border_color=palette["soft"],
                text_color=palette["text"],
                placeholder_text_color=palette["muted"],
            )

        if self.toggle_visibility_button:
            self.toggle_visibility_button.configure(
                fg_color=palette["secondary"],
                hover_color=palette["secondary_hover"],
                text_color=palette["text"],
            )

        if self.save_button:
            self.save_button.configure(
                fg_color=palette["primary"],
                hover_color=palette["primary_hover"],
                text_color=palette["inverse_text"],
            )

        if self.status_label:
            self.status_label.configure(text_color=palette["muted"])

        self.after(0, self._update_shodan_text_wraplength)