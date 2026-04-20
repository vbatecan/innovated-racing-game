"""UI package for the racing game.

This package provides modern UI components, HUD elements, and menus
for the racing game. All public classes and functions are exported
through this top-level module for convenient importing.

Example:
    >>> from ui import HUDManager, PauseMenu, SettingsMenu, Button
    >>> hud = HUDManager(1920, 1080)
    >>> pause = PauseMenu()
"""

from __future__ import annotations

from ui.components.button import Button
from ui.components.slider import Slider
from ui.core.constants import (
    ANIMATION,
    COLORS,
    DEFAULTS,
    FONTS,
    LAYOUT,
    PATHS,
    Animation,
    Colors,
    FilePaths,
    FontSizes,
    GameDefaults,
    Layout,
)
from ui.core.types import (
    Callback,
    Color,
    Event,
    Font,
    MousePos,
    MousePressed,
    Position,
    PositionF,
    Rect,
    Surface,
)
from ui.hud.manager import HUDManager
from ui.menus.pause import PauseMenu
from ui.menus.settings import SettingsMenu
from ui.utils.drawing import draw_rounded_rect

__all__ = [
    "Button",
    "Slider",
    "HUDManager",
    "PauseMenu",
    "SettingsMenu",
    "draw_rounded_rect",
    "COLORS",
    "FONTS",
    "LAYOUT",
    "ANIMATION",
    "DEFAULTS",
    "PATHS",
    "Colors",
    "FontSizes",
    "Layout",
    "Animation",
    "GameDefaults",
    "FilePaths",
    "Callback",
    "Color",
    "Event",
    "Font",
    "MousePos",
    "MousePressed",
    "Position",
    "PositionF",
    "Rect",
    "Surface",
]
