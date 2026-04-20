"""Modern UI/HUD system for the racing game.

This is the main entry point for the UI package. It re-exports all
public classes and functions for easy importing while maintaining
backward compatibility with the original monolithic structure.

Includes:
- HUD display with speed, score, lives, distance, and gear
- Pause menu with resume, restart, settings, and quit options
- Settings menu with gameplay, graphics, and controls categories
- Interactive Button and Slider components
- Drawing utilities for rounded rectangles

Example:
    >>> from ui.game_ui import HUDManager, PauseMenu, SettingsMenu
    >>> hud = HUDManager(1920, 1080)
    >>> pause = PauseMenu()
    >>> settings = SettingsMenu()
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
    Colors,
    FontSizes,
    Layout,
    Animation,
    GameDefaults,
    FilePaths,
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
