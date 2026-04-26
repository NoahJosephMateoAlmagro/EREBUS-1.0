"""
Presentation constants for the EREBUS graphical interface.

This module contains only constants related to the presentation layer:
colors, fonts, layout values, tab names, labels, popup configuration and
status messages.

It must not contain constants from the execution engine, collectors,
parsers, repositories or database layer.
"""

from pathlib import Path


APP_TITLE = "EREBUS"
APP_MIN_WIDTH = 1200
APP_MIN_HEIGHT = 760

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"

FONT_ZEKTON_REGULAR = FONTS_DIR / "Zekton-Regular.otf"
FONT_SHUTTLE_X = FONTS_DIR / "SHUTTLE-X.ttf"

FONT_FAMILY_TITLE = "Shuttle-X"
FONT_FAMILY_BODY = "Zekton"
FONT_FAMILY_CONSOLE = "Consolas"

THEME_DARK = "dark"
THEME_LIGHT = "light"
DEFAULT_COLOR_THEME = "blue"

HEADER_HEIGHT = 116
HEADER_PADX = 28
HEADER_PADY = (18, 8)

MAIN_AREA_PADX = 28
MAIN_AREA_PADY = (6, 28)

SIDEBAR_WIDTH = 178
SIDEBAR_BUTTON_HEIGHT = 56

TAB_EXECUTION = "execution"
TAB_DATA = "data"
TAB_RESULTS = "results"
TAB_CONSOLE = "console"

TAB_LABELS = {
    TAB_EXECUTION: "Execution",
    TAB_DATA: "Data",
    TAB_RESULTS: "Results",
    TAB_CONSOLE: "Console",
}

PLACEHOLDER_DATA_TEXT = "Data view pending"
PLACEHOLDER_RESULTS_TEXT = "Results view pending"

CARD_CORNER_RADIUS = 14
CARD_PADX = 10
CARD_PADY = (0, 20)

CONSOLE_POLL_INTERVAL_MS = 100
CONSOLE_READY_TEXT = "[Console ready]\n"

TOOLTIP_DELAY_MS = 450
TOOLTIP_WRAP_LENGTH = 390
TOOLTIP_FG_COLOR = "#0F1938"
TOOLTIP_TEXT_COLOR = "#FFFFFF"

POPUP_WIDTH = 680
POPUP_HEIGHT = 132
POPUP_TARGET_X = 34
POPUP_Y = 8
POPUP_SLIDE_EXTRA_OFFSET = 20
POPUP_ANIMATION_INTERVAL_MS = 12
POPUP_ANIMATION_FACTOR = 0.22
POPUP_ANIMATION_MIN_STEP = 2
POPUP_CLOSE_BUTTON_WIDTH = 96
POPUP_CLOSE_BUTTON_HEIGHT = 38
WINDOWS_NOTIFICATION_SOUND = "SystemHand"

APP_SUBTITLE = "Footprinting, public exposure and digital attack surface analysis"

EXECUTION_TITLE = "New execution"
EXECUTION_DESCRIPTION = (
    "Enter the target domain and start the analysis using the selected configuration."
)

GENERAL_CONFIGURATION_TITLE = "General configuration"
GENERAL_CONFIGURATION_DESCRIPTION = "These values affect the whole execution."

MODULES_TITLE = "Analysis modules"
MODULES_DESCRIPTION = (
    "Enable the modules you want to execute. If a module depends on another one, "
    "its dependency must be enabled first."
)

CONSOLE_TITLE = "Runtime console"

STATUS_READY = "Status: Ready"
STATUS_RUNNING = "Status: Running"
STATUS_CANCELLING = "Status: Cancelling"
STATUS_CANCELLED = "Status: Cancelled"
STATUS_MISSING_DOMAIN = "Status: Missing domain"
STATUS_ALREADY_RUNNING = "Status: Execution already running"
STATUS_NO_EXECUTION_RUNNING = "Status: No execution running"
STATUS_EXECUTION_FAILED = "Status: Execution failed"
STATUS_ALL_MODULES_ENABLED = "Status: All modules enabled"
STATUS_ALL_MODULES_DISABLED = "Status: All modules disabled"

STOP_REQUESTED_POPUP = (
    "Stop requested. To avoid data corruption, EREBUS will not interrupt "
    "the module that is currently running. The execution will stop safely "
    "as soon as the current module or phase finishes. Current module: {current}."
)

STOP_REQUESTED_UPDATE = (
    "Stop requested. To avoid data corruption, EREBUS will stop when "
    "the current module finishes. Current module: {current}."
)

STOP_REQUESTED_CONSOLE = (
    "[GUI] Stop requested. EREBUS will stop after the current module "
    "or current phase finishes."
)

EXECUTION_CANCELLED_POPUP = (
    "Execution cancelled safely. Results generated before cancellation "
    "have been preserved."
)

EXECUTION_STARTING_POPUP = (
    "EREBUS is starting an analysis for domain: {target}."
)

EXECUTION_FINISHED_POPUP = (
    "Execution finished for domain: {target}. Final status: {status}."
)

EXECUTION_FAILED_POPUP = (
    "Execution failed for domain: {target}. Check the runtime console for details."
)

OPTION_LOGGING_MODES = ["TRACE", "INFO", "ERROR", "SILENT"]

COLORS = {
    "dark_bg": "#0F1938",
    "dark_panel": "#1A2448",
    "dark_card": "#26345F",
    "dark_soft": "#354678",

    "light_bg": "#E9EDF8",
    "light_panel": "#D8DFF1",
    "light_card": "#C8D2EA",
    "light_soft": "#B7C4E1",

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

    "warning_bg_dark": "#F5E79D",
    "warning_border_dark": "#F5D29D",
    "warning_text_dark": "#0F1938",

    "warning_bg_light": "#354678",
    "warning_border_light": "#0F1938",
    "warning_text_light": "#FFFFFF",

    "light_hover": "#A7B6D8",
    "console_light_bg": "#F4F6FC",
}


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