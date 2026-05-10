"""
Aggregated presentation constants for the EREBUS graphical interface.

This package contains only constants related to the presentation layer:
application identity, asset paths, theme values, layout dimensions, texts,
statuses, scaling values and timing configuration.

It must not contain constants from the execution engine, collectors, parsers,
repositories or database layer.
"""

from .app import *
from .layout import *
from .text import *
from .theme import *
from .scaling import *
from .timing import *
from .results import *
from .data import *