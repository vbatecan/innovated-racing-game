"""Interactive slider component.

Provides a draggable slider for numeric value selection with visual
feedback including a filled track and circular thumb.
"""

from __future__ import annotations

import pygame

from ui.core.constants import COLORS, LAYOUT
from ui.core.types import Color, MousePos, MousePressed, Position, Surface
from ui.utils.drawing import draw_rounded_rect


class Slider:
    """Interactive slider for numeric value selection.
    
    A horizontal slider component that allows users to select a value
    within a defined range by dragging the thumb or clicking on the track.
    
    Attributes:
        x: X-coordinate of the slider's left edge.
        y: Y-coordinate of the slider's top edge.
        width: Width of the slider track.
        height: Height of the slider component.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.
        value: Current slider value.
        label: Optional label text displayed above the slider.
        font: Font used for rendering the label and value.
        track_rect: Rectangle defining the clickable track area.
        thumb_radius: Radius of the circular thumb indicator.
        is_dragging: True if the user is currently dragging the thumb.
        accent_color: Color of the filled portion and thumb.
        track_color: Color of the unfilled track background.
        text_color: Color of the label and value text.
        
    Example:
        >>> slider = Slider(100, 200, 300, 40, 0.0, 100.0, 50.0, "Volume")
        >>> slider.update(mouse_pos, mouse_pressed)
        >>> slider.draw(screen)
        >>> current_value = slider.get_value()
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        min_val: float,
        max_val: float,
        value: float,
        label: str = "",
        font: pygame.font.Font | None = None,
    ) -> None:
        """Initialize a new Slider instance.
        
        Args:
            x: X-coordinate of the slider's left edge.
            y: Y-coordinate of the slider's top edge.
            width: Width of the slider track in pixels.
            height: Height of the slider component.
            min_val: Minimum value of the slider range.
            max_val: Maximum value of the slider range.
            value: Initial slider value.
            label: Optional text label displayed above the slider.
            font: Optional custom font. Uses default pygame font if None.
        """
        self.x: int = x
        self.y: int = y
        self.width: int = width
        self.height: int = height
        self.min_val: float = min_val
        self.max_val: float = max_val
        self.value: float = value
        self.label: str = label
        self.font: pygame.font.Font = font or pygame.font.Font(None, 24)

        self.track_rect: pygame.Rect = pygame.Rect(x, y + height // 2 - 3, width, 6)
        self.thumb_radius: int = LAYOUT.slider_thumb_radius
        self.is_dragging: bool = False

        self.accent_color: Color = COLORS.accent
        self.track_color: Color = COLORS.track_bg
        self.text_color: Color = (200, 200, 220)

    def update(self, mouse_pos: MousePos, mouse_pressed: MousePressed) -> None:
        """Update slider state based on mouse input.
        
        Handles drag initiation when clicking on the track, drag release,
        and updates the slider value based on thumb position during dragging.
        Value is clamped to [min_val, max_val] range.
        
        Args:
            mouse_pos: Current (x, y) position of the mouse cursor.
            mouse_pressed: Tuple of mouse button states (left, middle, right).
            
        Returns:
            None
        """
        if self.track_rect.collidepoint(mouse_pos) and mouse_pressed[0]:
            self.is_dragging = True

        if not mouse_pressed[0]:
            self.is_dragging = False

        if self.is_dragging:
            rel_x: int = max(0, min(mouse_pos[0] - self.x, self.width))
            pct: float = rel_x / self.width
            self.value = self.min_val + pct * (self.max_val - self.min_val)

    def draw(self, surface: Surface) -> None:
        """Render the slider on the given surface.
        
        Draws the track background, filled portion indicating current value,
        circular thumb at the current position, and label/value text.
        
        Args:
            surface: The pygame surface to draw on.
            
        Returns:
            None
        """
        draw_rounded_rect(surface, self.track_color, self.track_rect)

        pct: float = (self.value - self.min_val) / (self.max_val - self.min_val)
        fill_width: int = int(self.width * pct)
        fill_rect: pygame.Rect = pygame.Rect(
            self.x, self.y + self.height // 2 - 3, fill_width, 6
        )
        draw_rounded_rect(surface, self.accent_color, fill_rect)

        thumb_x: int = self.x + fill_width
        thumb_y: int = self.y + self.height // 2
        pygame.draw.circle(
            surface, self.accent_color, (thumb_x, thumb_y), self.thumb_radius
        )

        if self.label:
            label_surf: Surface = self.font.render(self.label, True, self.text_color)
            surface.blit(label_surf, (self.x, self.y - 20))

        value_surf: Surface = self.font.render(
            f"{self.value:.0f}", True, self.text_color
        )
        surface.blit(value_surf, (self.x + self.width + 10, self.y))

    def get_value(self) -> float:
        """Get the current slider value.
        
        Returns:
            The current numeric value of the slider.
        """
        return self.value
