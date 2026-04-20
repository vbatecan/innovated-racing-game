"""HUD (Heads-Up Display) Manager.

Provides the in-game HUD displaying speed, score, lives, distance,
gear, and camera preview. All UI elements use glass-panel
styling with the game's color scheme.
"""

from __future__ import annotations

import os
from typing import Dict, List, Tuple

import cv2
import numpy as np
import pygame
from core.resource_manager import ResourceManager

from ui.core.constants import (
    ANIMATION,
    COLORS,
    DEFAULTS,
    FONTS,
    LAYOUT,
    PATHS,
)
from ui.core.types import Color, Position, Surface
from ui.utils.drawing import draw_rounded_rect


class HUDManager:
    """Manages the racing game's heads-up display.
    
    The HUDManager renders all on-screen game information including:
    - Speed display (top center, with animated smoothing)
    - Score (top right)
    - Lives (top left, with heart image indicators)
    - Distance, speed, gear stats (bottom left)
    - Camera preview (bottom right, when enabled)
    
    Attributes:
        screen_width: Width of the game screen.
        screen_height: Height of the game screen.
        font_large: Large font for speed display.
        font_medium: Medium font for scores and values.
        font_small: Small font for labels.
        speed: Current vehicle speed.
        max_speed: Maximum vehicle speed for display.
        score: Current player score.
        lives: Current player lives (0-3).
        distance: Distance traveled in meters.
        gear: Current gear (1-N).
        is_braking: True if vehicle is braking.
        hearts_collected: Bonus hearts collected.
        camera_frame: Current camera frame for preview.
        show_camera: True if camera preview is enabled.
        life_images: Dictionary mapping lives count to loaded images.
        _speed_display: Animated speed value for smooth transitions.
    """

    def __init__(self, screen_width: int = 1920, screen_height: int = 1080) -> None:
        """Initialize the HUD manager.
        
        Args:
            screen_width: Width of the game screen in pixels.
            screen_height: Height of the game screen in pixels.
        """
        self.screen_width: int = screen_width
        self.screen_height: int = screen_height

        self.font_large: pygame.font.Font = pygame.font.Font(None, FONTS.large)
        self.font_medium: pygame.font.Font = pygame.font.Font(None, FONTS.medium)
        self.font_small: pygame.font.Font = pygame.font.Font(None, FONTS.small)

        self.speed: float = 0.0
        self.max_speed: float = DEFAULTS.speed_max
        self.score: int = 0
        self.lives: int = DEFAULTS.lives
        self.distance: float = 0.0
        self.gear: int = DEFAULTS.gear
        self.is_braking: bool = False
        self.hearts_collected: int = 0

        self.camera_frame: np.ndarray | None = None
        self.show_camera: bool = True
        self.camera_size: Tuple[int, int] = (LAYOUT.camera_width, LAYOUT.camera_height)
        self.camera_pos: Tuple[str, str] = ("right", "bottom")

        self._speed_display: float = 0.0
        self._speed_anim_speed: float = ANIMATION.speed_smoothing

        self.life_images: Dict[int, Surface | None] = {}
        self._load_life_images()

    def _load_life_images(self) -> None:
        """Load life indicator images from the resources directory.
        
        Attempts to load heart/life images for each possible lives value (0-3).
        If an image fails to load or doesn't exist, None is stored for that key.
        
        Returns:
            None
        """
        self.life_images = {}
        image_files: Dict[int, str] = {
            3: "full hp.png",
            2: "hp minus 1.png",
            1: "hp minus 2.png",
            0: "deds.png",
        }
        for lives, filename in image_files.items():
            filepath: str = os.path.join(PATHS.models_path, filename)
            if os.path.exists(filepath):
                try:
                    img: Surface = ResourceManager.load_image(filepath, convert_alpha=True)
                    self.life_images[lives] = img
                except Exception:
                    self.life_images[lives] = None
            else:
                self.life_images[lives] = None

    def update(
        self,
        speed: float,
        max_speed: float,
        score: int,
        lives: int,
        distance: float,
        gear: int,
        is_braking: bool,
        hearts_collected: int = 0,
        dt: float = 0.016,
    ) -> None:
        """Update HUD state with current game values.
        
        Updates all tracked game state variables and animates the speed
        display value using linear interpolation for smooth transitions.
        
        Args:
            speed: Current vehicle speed.
            max_speed: Maximum vehicle speed.
            score: Current player score.
            lives: Current player lives.
            distance: Distance traveled in meters.
            gear: Current gear number.
            is_braking: True if the vehicle is braking.
            hearts_collected: Number of bonus hearts collected.
            dt: Delta time since last update (unused but kept for API compatibility).
            
        Returns:
            None
        """
        self.speed = speed
        self.max_speed = max_speed
        self.score = score
        self.lives = lives
        self.distance = distance
        self.gear = gear
        self.is_braking = is_braking
        self.hearts_collected = hearts_collected

        self._speed_display += (speed - self._speed_display) * self._speed_anim_speed

    def set_camera_frame(self, frame: np.ndarray | None) -> None:
        """Set the current camera frame for preview display.
        
        Args:
            frame: OpenCV/numpy image array, or None to clear.
            
        Returns:
            None
        """
        self.camera_frame = frame

    def set_camera_visibility(self, visible: bool) -> None:
        """Set whether the camera preview should be displayed.
        
        Args:
            visible: True to show camera preview, False to hide.
            
        Returns:
            None
        """
        self.show_camera = visible

    def draw(self, screen: Surface) -> None:
        """Render the entire HUD to the given screen.
        
        Draws all HUD components in their respective screen positions.
        Camera preview is only drawn if enabled and a frame is available.
        
        Args:
            screen: The pygame surface to draw on (typically the main screen).
            
        Returns:
            None
        """
        sw: int = screen.get_width()
        sh: int = screen.get_height()

        self._draw_speed_top_center(screen, sw)
        self._draw_score_top_right(screen, sw)
        self._draw_lives_top_left(screen)
        self._draw_stats_bottom_left(screen, sh)
        if self.show_camera and self.camera_frame is not None:
            self._draw_camera_preview(screen, sw, sh)

    def _draw_glass_panel(
        self,
        surface: Surface,
        x: int,
        y: int,
        w: int,
        h: int,
        border: bool = True,
    ) -> None:
        """Draw a semi-transparent glass panel with optional border.
        
        Args:
            surface: The pygame surface to draw on.
            x: Panel X position.
            y: Panel Y position.
            w: Panel width.
            h: Panel height.
            border: True to draw accent border.
            
        Returns:
            None
        """
        draw_rounded_rect(surface, COLORS.panel_bg, (x, y, w, h))
        if border:
            draw_rounded_rect(surface, COLORS.accent, (x, y, w, h), 1)

    def _draw_speed_top_center(self, screen: Surface, sw: int) -> None:
        """Draw the speed display panel at the top center.
        
        Displays the current speed with animated smoothing and braking
        indicator. Shows "km/h" unit below the speed value.
        
        Args:
            screen: The pygame surface to draw on.
            sw: Screen width for centering calculations.
            
        Returns:
            None
        """
        w: int = LAYOUT.speed_panel_width
        h: int = LAYOUT.speed_panel_height
        x: int = sw // 2 - w // 2
        y: int = 20

        self._draw_glass_panel(screen, x, y, w, h)
        draw_rounded_rect(screen, COLORS.accent, (x, y, w, 3))

        speed: int = int(self._speed_display)
        color: Color = COLORS.warn if self.is_braking else COLORS.text

        speed_text: Surface = self.font_large.render(f"{speed}", True, color)
        unit_text: Surface = self.font_small.render("km/h", True, COLORS.muted)

        screen.blit(speed_text, (x + w // 2 - speed_text.get_width() // 2, y + 10))
        screen.blit(unit_text, (x + w // 2 - unit_text.get_width() // 2, y + 50))

    def _draw_score_top_right(self, screen: Surface, sw: int) -> None:
        """Draw the score display panel at the top right.
        
        Displays the current score with comma separators for readability.
        
        Args:
            screen: The pygame surface to draw on.
            sw: Screen width for positioning.
            
        Returns:
            None
        """
        margin: int = LAYOUT.margin
        w: int = LAYOUT.score_panel_width
        h: int = LAYOUT.score_panel_height
        x: int = sw - w - margin
        y: int = margin

        self._draw_glass_panel(screen, x, y, w, h)

        score_text: str = f"CR {self.score:,}"
        score_surf: Surface = self.font_medium.render(score_text, True, COLORS.text)
        label_surf: Surface = self.font_small.render("CURRENCY", True, COLORS.muted)

        screen.blit(label_surf, (x + 15, y + 10))
        screen.blit(score_surf, (x + 15, y + 30))

    def _draw_lives_top_left(self, screen: Surface) -> None:
        """Draw the lives indicator at the top left.
        
        Displays the life image corresponding to current lives (0-3).
        If bonus hearts were collected, shows a pink "+N" indicator.
        
        Args:
            screen: The pygame surface to draw on.
            
        Returns:
            None
        """
        margin: int = LAYOUT.margin
        x: int = margin
        y: int = margin

        lives: int = max(0, min(DEFAULTS.max_lives, int(self.lives)))
        img: Surface | None = self.life_images.get(lives)

        if img:
            scale: float = PATHS.life_image_scale
            new_w: int = int(img.get_width() * scale)
            new_h: int = int(img.get_height() * scale)
            scaled: Surface = pygame.transform.smoothscale(img, (new_w, new_h))
            screen.blit(scaled, (x, y))

        if self.hearts_collected > 0:
            heart_text: Surface = self.font_small.render(
                f"+{self.hearts_collected}", True, COLORS.pink
            )
            screen.blit(heart_text, (x + 90, y + 25))

    def _draw_stats_bottom_left(self, screen: Surface, sh: int) -> None:
        """Draw the stats panel at the bottom left.
        
        Displays distance traveled, current speed, and gear in a vertical list.
        
        Args:
            screen: The pygame surface to draw on.
            sh: Screen height for positioning.
            
        Returns:
            None
        """
        margin: int = LAYOUT.margin
        w: int = LAYOUT.stats_panel_width
        h: int = LAYOUT.stats_panel_height
        x: int = margin
        y: int = sh - h - margin

        self._draw_glass_panel(screen, x, y, w, h)

        items: List[Tuple[str, str]] = [
            ("DISTANCE", f"{int(self.distance)}m"),
            ("SPEED", f"{self.speed:.0f}"),
            ("GEAR", f"{self.gear}"),
        ]

        for i, (label, value) in enumerate(items):
            label_surf: Surface = self.font_small.render(label, True, COLORS.muted)
            value_surf: Surface = self.font_medium.render(value, True, COLORS.text)

            screen.blit(label_surf, (x + 15, y + 12 + i * 25))
            screen.blit(value_surf, (x + 120, y + 8 + i * 25))

    def _draw_camera_preview(self, screen: Surface, sw: int, sh: int) -> None:
        """Draw the camera preview panel at the bottom right.
        
        Processes the camera frame (BGR→RGB conversion, resize, rotation, flip)
        and renders it within a bordered panel. Errors are silently caught
        and printed to console.
        
        Args:
            screen: The pygame surface to draw on.
            sw: Screen width for positioning.
            sh: Screen height for positioning.
            
        Returns:
            None
        """
        try:
            w: int = self.camera_size[0]
            h: int = self.camera_size[1]
            margin: int = LAYOUT.camera_margin

            x: int = sw - w - margin
            y: int = sh - h - margin - 80

            frame: np.ndarray = cv2.cvtColor(self.camera_frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (w, h))
            frame = np.rot90(frame)
            frame = np.flipud(frame)
            frame_surface: Surface = pygame.surfarray.make_surface(frame)

            panel: Surface = pygame.Surface((w + 8, h + 8), pygame.SRCALPHA)
            panel.fill((0, 0, 0, 180))
            screen.blit(panel, (x - 4, y - 4))

            pygame.draw.rect(screen, COLORS.accent, (x - 4, y - 4, w + 8, h + 8), 2)
            screen.blit(frame_surface, (x, y))
        except Exception as e:
            print(f"Camera draw error: {e}")

