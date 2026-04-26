"""
Reusable loading overlay for the EREBUS graphical interface.

The overlay covers the full application window temporarily and displays a
centered message in a separate top-level window.

This overlay is intentionally implemented with standard tkinter widgets instead
of CustomTkinter widgets. This makes it immune to global CustomTkinter theme
and scaling changes while it is visible. Once shown, its colors, font and
geometry remain frozen until it is hidden.
"""

import tkinter as tk
from tkinter import font as tkfont


class LoadingOverlay:
    """
    Reusable loading overlay component.

    The overlay is displayed as an independent top-level window placed above the
    main application. It uses plain tkinter widgets so it does not react to
    CustomTkinter appearance or scaling changes while visible.
    """

    def __init__(self, parent, fonts, get_palette_callback):
        """
        Initializes the loading overlay.

        Args:
            parent: Main application window that will be covered.
            fonts: Dictionary with the application fonts.
            get_palette_callback: Callable that returns the active theme palette.
        """
        self.parent = parent
        self.fonts = fonts
        self.get_palette_callback = get_palette_callback

        self.window = None
        self.container = None
        self.card = None
        self.label = None

        self.frozen_palette = None
        self.frozen_font = None

    def show(self, message="Loading..."):
        """
        Shows the loading overlay.

        The overlay freezes the current palette and font at the moment it is
        shown. Later theme or UI scale changes do not affect the visible overlay.

        Args:
            message: Message displayed in the center of the overlay.
        """
        self.hide()

        self.frozen_palette = dict(self.get_palette_callback())
        self.frozen_font = self._clone_font(self.fonts["section"])

        self.parent.update_idletasks()

        self.window = tk.Toplevel(self.parent)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.configure(bg=self.frozen_palette["bg"])

        self._sync_geometry()

        self.container = tk.Frame(
            self.window,
            bg=self.frozen_palette["bg"],
            highlightthickness=0,
            bd=0,
        )
        self.container.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.card = tk.Frame(
            self.container,
            bg=self.frozen_palette["card"],
            highlightthickness=2,
            highlightbackground=self.frozen_palette["primary"],
            bd=0,
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")

        self.label = tk.Label(
            self.card,
            text=message,
            bg=self.frozen_palette["card"],
            fg=self.frozen_palette["primary"],
            font=self.frozen_font,
            padx=42,
            pady=28,
            bd=0,
        )
        self.label.pack()

        self.window.deiconify()
        self.window.lift()

    def hide(self):
        """
        Hides the loading overlay if it is currently visible.
        """
        if self.window:
            try:
                self.window.destroy()
            except Exception:
                pass

        self.window = None
        self.container = None
        self.card = None
        self.label = None
        self.frozen_palette = None
        self.frozen_font = None

    def set_message(self, message):
        """
        Updates the loading message if the overlay is visible.

        Args:
            message: New loading message.
        """
        if self.label:
            self.label.configure(text=message)

    def apply_theme(self):
        """
        Keeps the overlay above the rest of the interface.

        The overlay intentionally does not update its palette or font while it
        is visible. This prevents visual flickering during theme and scale
        changes.
        """
        if self.window:
            self._sync_geometry()
            self.window.lift()

    def is_visible(self):
        """
        Checks whether the overlay is currently visible.

        Returns:
            bool: True if the overlay is visible, False otherwise.
        """
        return self.window is not None

    def _sync_geometry(self):
        """
        Synchronizes the overlay geometry with the parent window.
        """
        if not self.parent.winfo_exists():
            return

        self.parent.update_idletasks()

        width = self.parent.winfo_width()
        height = self.parent.winfo_height()
        x = self.parent.winfo_rootx()
        y = self.parent.winfo_rooty()

        if self.window and width > 1 and height > 1:
            self.window.geometry(f"{width}x{height}+{x}+{y}")

    def _clone_font(self, ctk_font):
        """
        Creates an independent tkinter font based on a CTkFont.

        Args:
            ctk_font: Source CTkFont.

        Returns:
            tkinter.font.Font: Independent font copy frozen at current size.
        """
        try:
            family = ctk_font.cget("family")
            size = ctk_font.cget("size")
            weight = ctk_font.cget("weight")
            slant = ctk_font.cget("slant")
            underline = ctk_font.cget("underline")
            overstrike = ctk_font.cget("overstrike")

            return tkfont.Font(
                family=family,
                size=size,
                weight=weight,
                slant=slant,
                underline=underline,
                overstrike=overstrike,
            )
        except Exception:
            return ("Segoe UI", 18, "normal")