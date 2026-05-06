"""
Theme helpers for the EREBUS presentation layer.

This module centralizes font creation and theme-dependent color selection.
"""

import customtkinter as ctk

import presentation.constants as C


def build_fonts(scale=1.0):
    """
    Builds the font catalog used by the interface.

    Args:
        scale: UI scale factor applied to base font sizes.

    Returns:
        dict: Mapping between semantic font names and CTkFont instances.
    """
    def scaled_size(font_key):
        """
        Calculates the scaled size for a semantic font key.

        Args:
            font_key: Font key from FONT_BASE_SIZES.

        Returns:
            int: Scaled font size.
        """
        return max(1, int(round(C.FONT_BASE_SIZES[font_key] * scale)))

    return {
        "title": ctk.CTkFont(
            family=C.FONT_FAMILY_TITLE,
            size=scaled_size("title"),
            weight="bold",
        ),
        "subtitle": ctk.CTkFont(
            family=C.FONT_FAMILY_BODY,
            size=scaled_size("subtitle"),
        ),
        "section": ctk.CTkFont(
            family=C.FONT_FAMILY_BODY,
            size=scaled_size("section"),
            weight="bold",
        ),
        "body": ctk.CTkFont(
            family=C.FONT_FAMILY_BODY,
            size=scaled_size("body"),
        ),
        "body_bold": ctk.CTkFont(
            family=C.FONT_FAMILY_BODY,
            size=scaled_size("body_bold"),
            weight="bold",
        ),
        "button": ctk.CTkFont(
            family=C.FONT_FAMILY_BODY,
            size=scaled_size("button"),
            weight="bold",
        ),
        "module_title": ctk.CTkFont(
            family=C.FONT_FAMILY_BODY,
            size=scaled_size("module_title"),
            weight="bold",
        ),
        "small": ctk.CTkFont(
            family=C.FONT_FAMILY_BODY,
            size=scaled_size("small"),
        ),
        "small_bold": ctk.CTkFont(
            family=C.FONT_FAMILY_BODY,
            size=scaled_size("small_bold"),
            weight="bold",
        ),
        "placeholder": ctk.CTkFont(
            family=C.FONT_FAMILY_BODY,
            size=scaled_size("placeholder"),
            weight="bold",
        ),
        "console": ctk.CTkFont(
            family=C.FONT_FAMILY_CONSOLE,
            size=scaled_size("console"),
        ),
        "popup": ctk.CTkFont(
            family=C.FONT_FAMILY_BODY,
            size=scaled_size("popup"),
            weight="bold",
        ),
    }


def is_dark_theme(theme_name):
    """
    Checks whether the current theme is dark.

    Args:
        theme_name: Current theme name.

    Returns:
        bool: True if the current theme is dark, False otherwise.
    """
    return theme_name == C.THEME_DARK


def get_theme_palette(theme_name):
    """
    Gets the effective color palette for the current theme.

    Args:
        theme_name: Current theme name.

    Returns:
        dict: Theme-dependent colors ready to be used by widgets.
    """
    is_dark = is_dark_theme(theme_name)

    return {
        "bg": C.COLORS["dark_bg"] if is_dark else C.COLORS["light_bg"],
        "panel": C.COLORS["dark_panel"] if is_dark else C.COLORS["light_panel"],
        "card": C.COLORS["dark_card"] if is_dark else C.COLORS["light_card"],
        "soft": C.COLORS["dark_soft"] if is_dark else C.COLORS["light_soft"],
        "muted": C.COLORS["muted"] if is_dark else C.COLORS["light_muted"],
        "text": C.COLORS["text_light"] if is_dark else C.COLORS["text_dark"],
        "inverse_text": C.COLORS["text_dark"] if is_dark else C.COLORS["text_light"],
        "primary": C.COLORS["accent"] if is_dark else C.COLORS["blue"],
        "primary_hover": (
            C.COLORS["accent_hover"] if is_dark else C.COLORS["light_hover"]
        ),
        "secondary": C.COLORS["blue"] if is_dark else C.COLORS["light_soft"],
        "secondary_hover": C.COLORS["olive"] if is_dark else C.COLORS["light_hover"],
        "danger": C.COLORS["danger"],
        "danger_hover": C.COLORS["danger_hover"],
        "warning_bg": (
            C.COLORS["warning_bg_dark"]
            if is_dark
            else C.COLORS["warning_bg_light"]
        ),
        "warning_border": (
            C.COLORS["warning_border_dark"]
            if is_dark
            else C.COLORS["warning_border_light"]
        ),
        "warning_text": (
            C.COLORS["warning_text_dark"]
            if is_dark
            else C.COLORS["warning_text_light"]
        ),
        "console_bg": (
            C.COLORS["dark_bg"]
            if is_dark
            else C.COLORS["console_light_bg"]
        ),

        "status_success_bg": C.COLORS["status_success_bg"],
        "status_success_text": C.COLORS["status_success_text"],

        "status_failed_bg": C.COLORS["status_failed_bg"],
        "status_failed_text": C.COLORS["status_failed_text"],

        "status_partial_bg": C.COLORS["status_partial_bg"],
        "status_partial_text": C.COLORS["status_partial_text"],

        "status_skipped_bg": (
            C.COLORS["status_skipped_bg_dark"]
            if is_dark
            else C.COLORS["status_skipped_bg_light"]
        ),
        "status_skipped_text": (
            C.COLORS["status_skipped_text_dark"]
            if is_dark
            else C.COLORS["status_skipped_text_light"]
        ),

        "status_unknown_bg": (
            C.COLORS["status_unknown_bg_dark"]
            if is_dark
            else C.COLORS["status_unknown_bg_light"]
        ),
        "status_unknown_text": (
            C.COLORS["status_unknown_text_dark"]
            if is_dark
            else C.COLORS["status_unknown_text_light"]
        ),
    }