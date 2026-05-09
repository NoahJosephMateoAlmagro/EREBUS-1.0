"""
Theme and color constants for the EREBUS presentation layer.
"""

THEME_DARK = "dark"
THEME_LIGHT = "light"
DEFAULT_COLOR_THEME = "blue"

TOOLTIP_FG_COLOR = "#0F1938"
TOOLTIP_TEXT_COLOR = "#FFFFFF"

COLORS = {
    # -------------------------------------------------
    # Base dark palette
    # -------------------------------------------------
    "dark_bg": "#0F1938",
    "dark_panel": "#1A2448",
    "dark_card": "#26345F",
    "dark_soft": "#354678",

    # -------------------------------------------------
    # Base light palette
    # -------------------------------------------------
    "light_bg": "#E9EDF8",
    "light_panel": "#D8DFF1",
    "light_card": "#C8D2EA",
    "light_soft": "#B7C4E1",

    # -------------------------------------------------
    # Shared neutrals and accents
    # -------------------------------------------------
    "accent": "#F5E79D",
    "accent_hover": "#F5D29D",
    "brown": "#735B38",
    "olive": "#7A713C",
    "blue": "#354678",
    "muted": "#B3B5B8",
    "light_muted": "#4D587A",
    "text_light": "#FFFFFF",
    "text_dark": "#0F1938",

    "danger": "#B85C5C",
    "danger_hover": "#D06A6A",

    "light_hover": "#A7B6D8",
    "console_light_bg": "#F4F6FC",

    # -------------------------------------------------
    # Reusable semantic colors
    # -------------------------------------------------
    "success_bg": "#55B978",
    "success_border": "#55B978",
    "success_text": "#FFFFFF",

    "error_bg": "#C76666",
    "error_border": "#C76666",
    "error_text": "#FFFFFF",

    "warning_bg_dark": "#F5E79D",
    "warning_border_dark": "#F5D29D",
    "warning_text_dark": "#0F1938",

    "warning_bg_light": "#354678",
    "warning_border_light": "#0F1938",
    "warning_text_light": "#FFFFFF",

    # -------------------------------------------------
    # Status badge colors
    # Kept for compatibility with the current results page.
    # They intentionally reuse the semantic colors above.
    # -------------------------------------------------
    "status_success_bg": "#55B978",
    "status_success_border": "#55B978",
    "status_success_text": "#FFFFFF",

    "status_failed_bg": "#C76666",
    "status_failed_border": "#C76666",
    "status_failed_text": "#FFFFFF",

    "status_partial_bg": "#F5E79D",
    "status_partial_border": "#F5D29D",
    "status_partial_text": "#0F1938",

    "status_skipped_bg_dark": "#1A2448",
    "status_skipped_border_dark": "#0F1938",
    "status_skipped_text_dark": "#FFFFFF",

    "status_skipped_bg_light": "#D8DFF1",
    "status_skipped_border_light": "#4D587A",
    "status_skipped_text_light": "#0F1938",

    "status_unknown_bg_dark": "#354678",
    "status_unknown_border_dark": "#0F1938",
    "status_unknown_text_dark": "#FFFFFF",

    "status_unknown_bg_light": "#B7C4E1",
    "status_unknown_border_light": "#4D587A",
    "status_unknown_text_light": "#0F1938",
}