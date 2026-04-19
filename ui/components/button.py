"""Interactive button component.

Provides a clickable button with hover effects, customizable colors,
and callback support for pygame-based UI systems.
"""

from __future__ import annotations

import pygame
import core.sound_manager as sound_manager_module

from ui.core.constants import COLORS
from ui.core.types import Callback, Color, MousePos, MousePressed, Surface
from ui.utils.drawing import draw_rounded_rect


def _play_ui_click_sfx() -> None:
    manager = sound_manager_module.sound_manager
    if manager is not None:
        manager.play_ui_click()


class Button:
    """Interactive button component with hover and click handling.
    
    A rectangular button that detects mouse hover and triggers a callback
    when clicked. Supports customizable colors, fonts, and text.
    
    Attributes:
        rect: The button's rectangular bounds.
        text: The button label text.
        callback: Function called when button is clicked.
        font: Font used for rendering the button text.
        bg_color: Default background color.
        hover_color: Background color when hovered.
        text_color: Text color.
        border_color: Border outline color.
        is_hovered: True if mouse is currently over the button.
        is_active: True if button is in active/pressed state.
        
    Example:
        >>> button = Button(100, 100, 200, 50, "Click Me", on_click)
        >>> button.update(mouse_pos, mouse_pressed)
        >>> button.draw(screen)
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        callback: Callback = None,
        font: pygame.font.Font | None = None,
    ) -> None:
        """Initialize a new Button instance.
        
        Args:
            x: X-coordinate of the button's top-left corner.
            y: Y-coordinate of the button's top-left corner.
            width: Button width in pixels.
            height: Button height in pixels.
            text: The label text displayed on the button.
            callback: Optional function to call when clicked.
            font: Optional custom font. Uses default pygame font if None.
        """
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.text: str = text
        self.callback: Callback = callback
        self.font: pygame.font.Font = font or pygame.font.Font(None, 28)

        self.bg_color: Color = COLORS.button_bg
        self.hover_color: Color = COLORS.button_hover
        self.text_color: Color = COLORS.text
        self.border_color: Color = COLORS.button_border
        self.is_hovered: bool = False
        self.is_active: bool = False
        self._was_pressed: bool = False

    def update(self, mouse_pos: MousePos, mouse_pressed: MousePressed) -> None:
        """Update button state based on mouse input.
        
        Checks for hover state and triggers the callback if the button
        is clicked (hovered + left mouse button pressed).
        
        Args:
            mouse_pos: Current (x, y) position of the mouse cursor.
            mouse_pressed: Tuple of mouse button states (left, middle, right).
            
        Returns:
            None
        """
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        is_pressed: bool = bool(mouse_pressed[0])
        if self.is_hovered and is_pressed and not self._was_pressed:
            _play_ui_click_sfx()
            if self.callback:
                self.callback()
        self._was_pressed = is_pressed

    def draw(self, surface: Surface) -> None:
        """Render the button on the given surface.
        
        Draws the button background, border, and centered text label.
        Background color changes based on hover state.
        
        Args:
            surface: The pygame surface to draw on.
            
        Returns:
            None
        """
        color: Color = self.hover_color if self.is_hovered else self.bg_color

        draw_rounded_rect(surface, color, self.rect)
        draw_rounded_rect(surface, self.border_color, self.rect, 2)

        text_surf: Surface = self.font.render(self.text, True, self.text_color)
        text_rect: pygame.Rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
