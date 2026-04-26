"""
UI scaling and font size constants for the EREBUS presentation layer.
"""


UI_SCALE_SMALL = "Small"
UI_SCALE_MEDIUM = "Medium"
UI_SCALE_LARGE = "Large"
UI_SCALE_VERY_LARGE = "Very large"

UI_SCALE_OPTIONS = [
    UI_SCALE_SMALL,
    UI_SCALE_MEDIUM,
    UI_SCALE_LARGE,
    UI_SCALE_VERY_LARGE,
]

UI_SCALE_VALUES = {
    UI_SCALE_SMALL: 0.85,
    UI_SCALE_MEDIUM: 1.00,
    UI_SCALE_LARGE: 1.15,
    UI_SCALE_VERY_LARGE: 1.30,
}

DEFAULT_UI_SCALE = UI_SCALE_MEDIUM

FONT_BASE_SIZES = {
    "title": 54,
    "subtitle": 17,
    "section": 24,
    "body": 15,
    "body_bold": 16,
    "button": 16,
    "module_title": 19,
    "small": 14,
    "small_bold": 14,
    "placeholder": 22,
    "console": 14,
    "popup": 18,
}