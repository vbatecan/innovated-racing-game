"""Core constants for UI styling and configuration.

This module centralizes all color definitions, font sizes, and game-related
constants used across the UI system to ensure visual consistency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

# Color type alias: RGB or RGBA tuple
Color = Tuple[int, int, int] | Tuple[int, int, int, int]


@dataclass(frozen=True)
class Colors:
    """Palette of colors used throughout the UI.
    
    Attributes:
        accent: Primary accent color (cyan/blue).
        text: Default text color (off-white).
        muted: Secondary/muted text color (gray-blue).
        warn: Warning/error color (red).
        success: Success/positive color (green).
        gold: Gold/yellow highlight color.
        pink: Heart/bonus color.
        panel_bg: Semi-transparent panel background.
        track_bg: Slider track background.
        button_bg: Default button background.
        button_hover: Button hover state color.
        button_border: Button border color.
        close_btn: Close button background.
        boost_high: Boost bar high level color.
        boost_mid: Boost bar medium level color.
        boost_low: Boost bar low level color.
    """
    accent: Color = (0, 200, 255)
    text: Color = (240, 240, 250)
    muted: Color = (120, 140, 170)
    warn: Color = (255, 80, 80)
    success: Color = (80, 255, 140)
    gold: Color = (255, 200, 60)
    pink: Color = (255, 120, 160)
    panel_bg: Color = (15, 20, 35, 200)
    track_bg: Color = (40, 50, 70)
    button_bg: Color = (30, 40, 60)
    button_hover: Color = (0, 180, 255)
    button_border: Color = (60, 80, 120)
    close_btn: Color = (200, 80, 80)
    boost_high: Color = (0, 200, 255)
    boost_mid: Color = (255, 200, 60)
    boost_low: Color = (255, 80, 80)


@dataclass(frozen=True)
class FontSizes:
    """Font size definitions for consistent typography.
    
    Attributes:
        large: Large headings (e.g., speed display).
        medium: Medium text (e.g., scores, values).
        small: Small text (e.g., labels, hints).
        title: Menu titles.
        option: Menu options.
        label: Setting labels.
        hint: Keyboard hint text.
    """
    large: int = 56
    medium: int = 36
    small: int = 22
    title: int = 64
    title_small: int = 48
    option: int = 28
    option_small: int = 22
    label: int = 22
    hint: int = 20


@dataclass(frozen=True)
class Layout:
    """Layout and dimension constants.
    
    Attributes:
        margin: Default screen margin.
        panel_margin: Panel internal margin.
        speed_panel_width: Width of speed display panel.
        speed_panel_height: Height of speed display panel.
        score_panel_width: Width of score display panel.
        score_panel_height: Height of score display panel.
        stats_panel_width: Width of stats panel.
        stats_panel_height: Height of stats panel.
        boost_bar_width: Width of boost energy bar.
        boost_bar_height: Height of boost energy bar.
        pause_menu_width: Width of pause menu.
        pause_menu_height: Height of pause menu.
        settings_panel_width: Width of settings panel.
        settings_panel_height: Height of settings panel.
        sidebar_width: Settings sidebar width.
        button_height: Default button height.
        slider_thumb_radius: Slider thumb circle radius.
        camera_width: Camera preview width.
        camera_height: Camera preview height.
        camera_margin: Camera preview margin from edge.
    """
    margin: int = 25
    panel_margin: int = 20
    speed_panel_width: int = 180
    speed_panel_height: int = 80
    score_panel_width: int = 200
    score_panel_height: int = 70
    stats_panel_width: int = 200
    stats_panel_height: int = 90
    boost_bar_width: int = 280
    boost_bar_height: int = 14
    pause_menu_width: int = 340
    pause_menu_height: int = 380
    settings_panel_width: int = 800
    settings_panel_height: int = 580
    sidebar_width: int = 180
    button_height: int = 48
    slider_thumb_radius: int = 10
    camera_width: int = 180
    camera_height: int = 135
    camera_margin: int = 20


@dataclass(frozen=True)
class Animation:
    """Animation timing and speed constants.
    
    Attributes:
        speed_smoothing: Interpolation factor for speed display animation.
        pause_fade_speed: Speed of pause menu fade-in.
        menu_button_spacing: Vertical spacing between menu buttons.
        settings_option_spacing: Vertical spacing between settings options.
    """
    speed_smoothing: float = 0.15
    pause_fade_speed: float = 5.0
    menu_button_spacing: int = 60
    settings_option_spacing: int = 75


@dataclass(frozen=True)
class GameDefaults:
    """Default game state values.
    
    Attributes:
        lives: Starting lives.
        max_lives: Maximum lives for clamping.
        boost_max: Maximum boost energy.
        speed_max: Default max speed for display.
        gear: Starting gear.
    """
    lives: int = 3
    max_lives: int = 3
    boost_max: float = 100.0
    speed_max: float = 30.0
    gear: int = 1


@dataclass(frozen=True)
class FilePaths:
    """Resource file paths.
    
    Attributes:
        resources_base: Base resources directory.
        models_dir: Models subdirectory.
        life_images: Mapping of life counts to filename.
    """
    resources_base: str = "resources"
    models_dir: str = "models"
    life_image_scale: float = 0.55

    @property
    def models_path(self) -> str:
        """Returns the full path to the models directory."""
        from pathlib import Path
        return str(Path(self.resources_base) / self.models_dir)

    def life_image_path(self, lives: int) -> str:
        """Returns the path to the life image for given lives count.
        
        Args:
            lives: Number of lives (0-3).
            
        Returns:
            Path to the corresponding life image file.
        """
        from pathlib import Path
        filenames = {
            3: "full hp.png",
            2: "hp minus 1.png",
            1: "hp minus 2.png",
            0: "deds.png",
        }
        return str(Path(self.models_path) / filenames.get(lives, "deds.png"))


# Global constant instances
COLORS = Colors()
FONTS = FontSizes()
LAYOUT = Layout()
ANIMATION = Animation()
DEFAULTS = GameDefaults()
PATHS = FilePaths()
