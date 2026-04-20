"""Shared type aliases for the UI system.

This module provides type aliases used across multiple UI components
to ensure type consistency and improve code readability.
"""

from __future__ import annotations

from typing import Callable, Tuple, Union

import pygame

Position = Tuple[int, int]

PositionF = Tuple[float, float]

Rect = Tuple[int, int, int, int]

Color = Union[Tuple[int, int, int], Tuple[int, int, int, int]]

MousePos = Tuple[int, int]

MousePressed = Tuple[bool, bool, bool]

Callback = Callable[[], None] | None

Surface = pygame.Surface

Font = pygame.font.Font

Event = pygame.event.Event
