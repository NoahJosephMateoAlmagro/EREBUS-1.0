"""
Reusable non-blocking notification popup for the EREBUS interface.

The popup slides in from the left side of the window and displays a message
without blocking interaction with the application.
"""

try:
    import winsound
except ImportError:
    winsound = None

import customtkinter as ctk

import presentation.constants as C


class NotificationPopup:
    """
    Reusable animated notification popup.

    This component replaces the old bottom-popup attributes that were stored
    directly in the main application class.
    """

    def __init__(self, parent, fonts, get_palette_callback):
        """
        Initializes the popup controller.

        Args:
            parent: Parent CustomTkinter widget where the popup is placed.
            fonts: Dictionary with the application fonts.
            get_palette_callback: Callable that returns the active theme palette.
        """
        self.parent = parent
        self.fonts = fonts
        self.get_palette_callback = get_palette_callback

        self.container = None
        self.card = None
        self.label = None
        self.close_button = None
        self.animation_id = None

        self.target_x = C.POPUP_TARGET_X
        self.y = C.POPUP_Y

    def show(self, message, closable=True, play_sound=True):
        """
        Shows the notification popup.

        Args:
            message: Message displayed inside the popup.
            closable: Whether the popup includes a close button.
            play_sound: Whether a notification sound should be played.
        """
        self.hide()

        if play_sound:
            self._play_notification_sound()

        palette = self.get_palette_callback()
        start_x = -C.POPUP_WIDTH - C.POPUP_SLIDE_EXTRA_OFFSET

        self.container = ctk.CTkFrame(
            self.parent,
            fg_color="transparent",
            bg_color=palette["bg"],
            corner_radius=0,
        )
        self.container.place(
            x=start_x,
            y=self.y,
            anchor="nw",
        )
        self.container.grid_columnconfigure(0, weight=1)

        self.card = ctk.CTkFrame(
            self.container,
            width=C.POPUP_WIDTH,
            height=C.POPUP_HEIGHT,
            fg_color=palette["warning_bg"],
            bg_color=palette["bg"],
            border_color=palette["warning_border"],
            border_width=2,
            corner_radius=18,
        )
        self.card.grid(row=0, column=0, sticky="w")
        self.card.grid_propagate(False)

        self.card.grid_rowconfigure(0, weight=1)
        self.card.grid_columnconfigure(0, weight=1)
        self.card.grid_columnconfigure(1, weight=0)

        self.label = ctk.CTkLabel(
            self.card,
            text=message,
            font=self.fonts["popup"],
            text_color=palette["warning_text"],
            wraplength=500,
            justify="center",
            fg_color="transparent",
            bg_color=palette["warning_bg"],
        )
        self.label.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(24, 18),
            pady=22,
        )

        if closable:
            self.close_button = ctk.CTkButton(
                self.card,
                text="Close",
                width=C.POPUP_CLOSE_BUTTON_WIDTH,
                height=C.POPUP_CLOSE_BUTTON_HEIGHT,
                corner_radius=10,
                font=self.fonts["small_bold"],
                command=self.hide,
                fg_color=palette["secondary"],
                hover_color=palette["secondary_hover"],
                text_color=palette["text"],
                bg_color=palette["warning_bg"],
            )
            self.close_button.grid(
                row=0,
                column=1,
                sticky="",
                padx=(0, 18),
                pady=0,
            )

        self._animate_in(start_x)

    def update_message(self, message):
        """
        Updates the popup message if the popup is currently visible.

        Args:
            message: New popup message.
        """
        if self.label:
            self.label.configure(text=message)

    def hide(self):
        """
        Hides the popup if it is currently visible.
        """
        if self.animation_id:
            self.parent.after_cancel(self.animation_id)
            self.animation_id = None

        if self.container:
            self.container.destroy()

        self.container = None
        self.card = None
        self.label = None
        self.close_button = None

    def apply_theme(self):
        """
        Applies the active theme to the currently visible popup.
        """
        if not self.container:
            return

        palette = self.get_palette_callback()

        self.container.configure(
            fg_color="transparent",
            bg_color=palette["bg"],
            corner_radius=0,
        )

        if self.card:
            self.card.configure(
                fg_color=palette["warning_bg"],
                bg_color=palette["bg"],
                border_color=palette["warning_border"],
                corner_radius=18,
            )

        if self.label:
            self.label.configure(
                text_color=palette["warning_text"],
                fg_color="transparent",
                bg_color=palette["warning_bg"],
            )

        if self.close_button:
            self.close_button.configure(
                fg_color=palette["secondary"],
                hover_color=palette["secondary_hover"],
                text_color=palette["text"],
                bg_color=palette["warning_bg"],
                corner_radius=10,
            )

    def _animate_in(self, current_x):
        """
        Animates the popup so it slides in smoothly from the left side.

        Args:
            current_x: Current horizontal position of the popup.
        """
        if not self.container:
            return

        distance = self.target_x - current_x

        if abs(distance) <= C.POPUP_ANIMATION_MIN_STEP:
            self.container.place_configure(x=self.target_x, y=self.y)
            self.animation_id = None
            return

        next_x = current_x + max(
            C.POPUP_ANIMATION_MIN_STEP,
            int(distance * C.POPUP_ANIMATION_FACTOR),
        )

        self.container.place_configure(x=next_x, y=self.y)

        self.animation_id = self.parent.after(
            C.POPUP_ANIMATION_INTERVAL_MS,
            lambda: self._animate_in(next_x),
        )

    def _play_notification_sound(self):
        """
        Plays a short notification sound.

        On Windows, it uses a distinctive system alert sound. On other systems,
        it does nothing.
        """
        if winsound is None:
            return

        try:
            winsound.PlaySound(
                C.WINDOWS_NOTIFICATION_SOUND,
                winsound.SND_ALIAS | winsound.SND_ASYNC,
            )
        except Exception:
            try:
                winsound.MessageBeep(winsound.MB_ICONHAND)
            except Exception:
                pass