"""Modern neon-styled button component with glow effects.

Provides an enhanced button with soft glow, hover animations, and
smooth transitions for a polished, modern UI aesthetic.
"""

from __future__ import annotations

import pygame
import core.sound_manager as sound_manager_module

from ui.core.types import Callback, Color, MousePos, MousePressed, Surface
from ui.utils.drawing import draw_rounded_rect


def _play_ui_click_sfx() -> None:
    manager = sound_manager_module.sound_manager
    if manager is not None:
        manager.play_ui_click()


class ModernButton:
    """Modern button with neon glow and smooth animations.
    
    Features:
    - Soft neon glow outline
    - Smooth hover scaling animation
    - Click press effect
    - Animated glow intensity
    - Multiple accent colors
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
        accent_color: Color = (0, 220, 255),
        secondary_color: Color = (160, 100, 255),
    ) -> None:
        """Initialize a modern button.
        
        Args:
            x: X-coordinate of the button's top-left corner.
            y: Y-coordinate of the button's top-left corner.
            width: Button width in pixels.
            height: Button height in pixels.
            text: The button label text.
            callback: Optional function to call when clicked.
            font: Optional custom font.
            accent_color: Primary neon color (cyan by default).
            secondary_color: Secondary neon color (purple by default).
        """
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.text: str = text
        self.callback: Callback = callback
        self.font: pygame.font.Font = font or self._get_default_font()
        self.accent_color: Color = accent_color
        self.secondary_color: Color = secondary_color
        
        # Animation state
        self.is_hovered: bool = False
        self.is_pressed: bool = False
        self.hover_scale: float = 1.0
        self.glow_intensity: float = 0.5
        self.target_hover_scale: float = 1.0
        self.is_selected: bool = False
        self.click_pulse: float = 0.0
        
        # Base colors
        self.bg_color: Color = (12, 18, 32)
        self.text_color: Color = (245, 250, 255)
        
        # Animation timing
        self._hover_animation_speed: float = 0.18
        self._glow_pulse_speed: float = 0.06
        self._was_pressed: bool = False

    @staticmethod
    def _get_default_font() -> pygame.font.Font:
        """Get default font, using system font if pygame fonts unavailable."""
        try:
            return pygame.font.Font(None, 28)
        except Exception:
            # Fallback to system font
            return pygame.font.SysFont(None, 28)

    def update(self, mouse_pos: MousePos, mouse_pressed: MousePressed, delta_time: float = 0.016) -> None:
        """Update button state and animations.
        
        Args:
            mouse_pos: Current (x, y) position of the mouse cursor.
            mouse_pressed: Tuple of mouse button states.
            delta_time: Time elapsed since last update in seconds.
        """
        # Check hover state
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        self.target_hover_scale = 1.12 if self.is_hovered else 1.0
        
        # Smooth hover scale animation
        self.hover_scale += (self.target_hover_scale - self.hover_scale) * self._hover_animation_speed
        
        # Animate glow intensity for selected or hovered button
        if self.is_selected or self.is_hovered:
            self.glow_intensity = min(1.0, self.glow_intensity + self._glow_pulse_speed * 1.2)
        else:
            self.glow_intensity = max(0.5, self.glow_intensity - self._glow_pulse_speed)
        
        # Update click pulse animation
        if self.click_pulse > 0:
            self.click_pulse = max(0, self.click_pulse - delta_time * 8)
        
        # Handle click
        is_pressed = bool(mouse_pressed[0])
        if self.is_hovered and is_pressed and not self._was_pressed:
            self.is_pressed = True
            _play_ui_click_sfx()
            if self.callback:
                self.callback()
            self.click_pulse = 1.0
        else:
            self.is_pressed = False
        self._was_pressed = is_pressed

    def draw(self, surface: Surface) -> None:
        """Render the button with glow effects.
        
        Args:
            surface: The pygame surface to draw on.
        """
        # Get scaled button rect with click pulse
        pulse_scale = 1.0 + (self.click_pulse * 0.08)
        total_scale = self.hover_scale * pulse_scale
        
        scaled_width = int(self.rect.width * total_scale)
        scaled_height = int(self.rect.height * total_scale)
        offset_x = int((self.rect.width - scaled_width) / 2)
        offset_y = int((self.rect.height - scaled_height) / 2)
        
        scaled_rect = pygame.Rect(
            self.rect.x + offset_x,
            self.rect.y + offset_y,
            scaled_width,
            scaled_height
        )
        
        # Draw glow layers
        glow_color = self.accent_color if not self.is_selected else self.secondary_color
        enhanced_glow_intensity = self.glow_intensity + (self.click_pulse * 0.3)
        self._draw_glow(surface, scaled_rect, glow_color, enhanced_glow_intensity)
        
        # Draw button background with gradient
        self._draw_button_background(surface, scaled_rect)
        
        # Draw border/outline glow
        border_color = self._blend_colors(glow_color, (255, 255, 255), enhanced_glow_intensity)
        draw_rounded_rect(surface, border_color, scaled_rect, width=3)
        
        # Draw text with shadow
        self._draw_text_with_shadow(surface, scaled_rect, glow_color)

    def _draw_glow(self, surface: Surface, rect: pygame.Rect, color: Color, intensity: float = None) -> None:
        """Draw soft glow effect around button.
        
        Args:
            surface: The pygame surface to draw on.
            rect: The button rect.
            color: The glow color.
            intensity: Override glow intensity.
        """
        if intensity is None:
            intensity = self.glow_intensity
            
        glow_radius = 20
        glow_surface = pygame.Surface(
            (rect.width + glow_radius * 2, rect.height + glow_radius * 2),
            pygame.SRCALPHA
        )
        
        # Create soft gradient glow with multiple layers
        center_rect = pygame.Rect(glow_radius, glow_radius, rect.width, rect.height)
        for i in range(glow_radius, 0, -1):
            alpha = int(25 * (1 - i / glow_radius) * intensity)
            glow_rect = center_rect.inflate(i * 2, i * 2)
            color_with_alpha = color + (alpha,)
            draw_rounded_rect(glow_surface, color_with_alpha, glow_rect, width=0)
        
        surface.blit(
            glow_surface,
            (rect.x - glow_radius, rect.y - glow_radius)
        )

    def _draw_button_background(self, surface: Surface, rect: pygame.Rect) -> None:
        """Draw button background with subtle gradient.
        
        Args:
            surface: The pygame surface to draw on.
            rect: The button rect.
        """
        # Draw main background
        draw_rounded_rect(surface, self.bg_color, rect, width=0)
        
        # Draw subtle highlight at top
        highlight_rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height // 3)
        highlight_color = (20, 35, 60) if not self.is_hovered else (30, 50, 80)
        draw_rounded_rect(surface, highlight_color, highlight_rect, width=0)

    def _draw_text_with_shadow(self, surface: Surface, rect: pygame.Rect, accent: Color) -> None:
        """Draw button text with subtle shadow and shimmer.
        
        Args:
            surface: The pygame surface to draw on.
            rect: The button rect.
            accent: The accent color for text tint.
        """
        # Draw shadow text for depth
        shadow_surface = self.font.render(self.text, True, (0, 0, 0, 80))
        shadow_rect = shadow_surface.get_rect(center=(rect.centerx + 2, rect.centery + 2))
        surface.blit(shadow_surface, shadow_rect)
        
        # Draw main text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)



    @staticmethod
    def _blend_colors(color1: Color, color2: Color, t: float) -> Color:
        """Blend two colors together.
        
        Args:
            color1: First color.
            color2: Second color.
            t: Blend factor (0.0 to 1.0).
            
        Returns:
            Blended color.
        """
        t = max(0.0, min(1.0, t))
        return (
            int(color1[0] + (color2[0] - color1[0]) * t),
            int(color1[1] + (color2[1] - color1[1]) * t),
            int(color1[2] + (color2[2] - color1[2]) * t),
        )
