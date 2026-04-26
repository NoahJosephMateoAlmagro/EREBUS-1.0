"""
Reusable card helpers for the EREBUS presentation layer.
"""

import customtkinter as ctk

import presentation.constants as C


def create_card(parent, row):
    """
    Creates a generic card frame.

    Args:
        parent: Parent frame.
        row: Grid row.

    Returns:
        CTkFrame: Created card.
    """
    card = ctk.CTkFrame(parent, corner_radius=C.CARD_CORNER_RADIUS)
    card.grid(row=row, column=0, sticky="ew", padx=C.CARD_PADX, pady=C.CARD_PADY)
    card.grid_columnconfigure(0, weight=1)
    return card