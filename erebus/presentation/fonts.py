"""
Font loading utilities for the EREBUS presentation layer.

The functions in this module load custom fonts used by the graphical
interface. Fonts are loaded temporarily for the current application session.
"""

import os
import ctypes
from pathlib import Path

import presentation.constants as C


def load_font(font_path):
    """
    Loads a font temporarily for the current Windows session.

    The font is not permanently installed in the operating system. It is only
    made available while the application is running.

    Args:
        font_path: Path to the font file.
    """
    font_path = str(Path(font_path).resolve())

    if not os.path.exists(font_path):
        print(f"Font not found: {font_path}")
        return

    try:
        ctypes.windll.gdi32.AddFontResourceExW(font_path, 0x10, 0)
    except AttributeError:
        pass


def load_app_fonts():
    """
    Loads the custom fonts used by the EREBUS interface.
    """
    load_font(C.FONT_ZEKTON_REGULAR)
    load_font(C.FONT_SHUTTLE_X)