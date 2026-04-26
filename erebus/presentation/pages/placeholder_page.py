"""
Reusable placeholder page for unfinished EREBUS interface sections.
"""

import customtkinter as ctk


class PlaceholderPage(ctk.CTkFrame):
    """
    Simple placeholder page used for sections that are not implemented yet.
    """

    def __init__(self, parent, text, fonts):
        """
        Initializes the placeholder page.

        Args:
            parent: Parent widget.
            text: Placeholder text.
            fonts: Application font catalog.
        """
        super().__init__(parent, corner_radius=0)

        self.text = text
        self.fonts = fonts
        self.label = None

        self._build()

    def _build(self):
        """
        Builds the placeholder layout.
        """
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.label = ctk.CTkLabel(
            self,
            text=self.text,
            font=self.fonts["placeholder"],
        )
        self.label.grid(row=0, column=0)

    def apply_theme(self, palette):
        """
        Applies the active theme to the placeholder page.

        Args:
            palette: Active theme palette.
        """
        self.configure(fg_color=palette["panel"])

        if self.label:
            self.label.configure(text_color=palette["text"])