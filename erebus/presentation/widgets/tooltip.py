"""
Reusable tooltip widget for CustomTkinter controls.

The tooltip is attached to any widget and displays a small floating label when
the mouse hovers over that widget.
"""

import customtkinter as ctk

import presentation.constants as C


class Tooltip:
    """
    Simple tooltip displayed when the mouse hovers over a widget.

    It is used to explain configuration fields without adding too much
    permanent text to the interface.
    """

    def __init__(self, widget, text, delay=C.TOOLTIP_DELAY_MS):
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
            wraplength=C.TOOLTIP_WRAP_LENGTH,
            padx=14,
            pady=10,
            corner_radius=8,
            fg_color=C.TOOLTIP_FG_COLOR,
            text_color=C.TOOLTIP_TEXT_COLOR,
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