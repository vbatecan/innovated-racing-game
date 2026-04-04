"""Drawing utilities for UI components.

Provides low-level drawing primitives used by UI components,
including anti-aliased rounded rectangles.
"""

from __future__ import annotations

import pygame
import pygame.gfxdraw

from ui.core.types import Color, Rect, Surface


def draw_rounded_rect(
    surface: Surface,
    color: Color,
    rect: Rect,
    width: int = 0,
) -> None:
    """Draw a rounded rectangle on the given surface.
    
    Uses pygame.gfxdraw for anti-aliased rendering. When width is 0,
    fills the rectangle; otherwise draws an outline with the specified
    border width.
    
    Args:
        surface: The pygame surface to draw on.
        color: RGB or RGBA color tuple.
        rect: Rectangle definition as (x, y, width, height).
        width: Border width in pixels. 0 for filled rectangle.
        
    Returns:
        None
    """
    if width == 0:
        pygame.gfxdraw.box(surface, rect, color)
    else:
        pygame.gfxdraw.rectangle(
            surface,
            (
                rect[0] + width // 2,
                rect[1] + width // 2,
                rect[2] - width,
                rect[3] - width,
            ),
            color,
        )
