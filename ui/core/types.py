"""Shared type aliases for the UI system.

This module provides type aliases used across multiple UI components
to ensure type consistency and improve code readability.
"""

from __future__ import annotations

from typing import Callable, Tuple, Union

import pygame

# Screen position as (x, y) tuple
Position = Tuple[int, int]

# Screen position as float (x, y) tuple
PositionF = Tuple[float, float]

# Rectangle as (x, y, width, height) tuple
Rect = Tuple[int, int, int, int]

# RGB or RGBA color tuple
Color = Union[Tuple[int, int, int], Tuple[int, int, int, int]]

# Mouse position tuple
MousePos = Tuple[int, int]

# Mouse button pressed state tuple (left, middle, right)
MousePressed = Tuple[bool, bool, bool]

# Optional callback with no arguments
Callback = Callable[[], None] | None

# Pygame surface type alias
Surface = pygame.Surface

# Font type alias
Font = pygame.font.Font

# Event type alias
Event = pygame.event.Event
