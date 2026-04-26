"""
Application identity and asset path constants for the EREBUS presentation layer.
"""

from pathlib import Path


APP_TITLE = "EREBUS"
APP_MIN_WIDTH = 1200
APP_MIN_HEIGHT = 760

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"

FONT_ZEKTON_REGULAR = FONTS_DIR / "Zekton-Regular.otf"
FONT_SHUTTLE_X = FONTS_DIR / "SHUTTLE-X.ttf"

FONT_FAMILY_TITLE = "Shuttle-X"
FONT_FAMILY_BODY = "Zekton"
FONT_FAMILY_CONSOLE = "Consolas"