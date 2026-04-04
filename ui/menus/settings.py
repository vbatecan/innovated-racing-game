"""Settings menu component.

Provides a tabbed settings interface with categories for Gameplay,
Graphics, and Controls. Supports keyboard and mouse navigation with
visual feedback for value adjustments.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

import pygame

from ui.components.slider import Slider
from ui.core.constants import ANIMATION, COLORS, FONTS, LAYOUT
from ui.core.types import Event, MousePos, Surface
from ui.utils.drawing import draw_rounded_rect


class SettingsMenu:
    """Settings menu with categorized options and value adjustment.
    
    Displays a tabbed interface with three categories: Gameplay, Graphics,
    and Controls. Each category contains various settings that can be
    adjusted via keyboard or mouse interaction. Settings are stored as
    tuples with heterogeneous structures depending on value type.
    
    Attributes:
        categories: List of setting category names.
        selected_category: Index of currently selected category.
        selected_option: Index of currently selected option within category.
        settings: Dictionary mapping category names to option tuples.
        sliders: Dictionary of Slider components (currently unused).
        fonts: Dictionary of fonts for different text elements.
    """

    def __init__(self) -> None:
        """Initialize the settings menu.
        
        Sets up fonts, colors, categories, and default setting values.
        The settings data structure uses tuples where:
        - Length 4: Numeric range (name, value, min, max)
        - Length 3 with list: Discrete options (name, index, [options])
        - Length 2: Boolean toggle (name, value)
        """
        self.font_title: pygame.font.Font = pygame.font.Font(None, FONTS.title_small)
        self.font_option: pygame.font.Font = pygame.font.Font(None, FONTS.option)
        self.font_label: pygame.font.Font = pygame.font.Font(None, FONTS.label)
        self.font_hint: pygame.font.Font = pygame.font.Font(None, FONTS.hint)

        self.accent_color: pygame.Color = pygame.Color(COLORS.accent)
        self.text_color: pygame.Color = pygame.Color(COLORS.text)
        self.muted_color: pygame.Color = pygame.Color(COLORS.muted)

        self.categories: List[str] = ["Gameplay", "Graphics", "Controls"]
        self.selected_category: int = 0
        self.selected_option: int = 0

        self.settings: Dict[str, List[Tuple[Any, ...]]] = {
            "Gameplay": [
                ("Difficulty", 1, ["Easy", "Normal", "Hard"]),
                ("Traffic Density", 50, 0, 100),
                ("Show FPS", True),
            ],
            "Graphics": [
                ("Fullscreen", True),
                ("Show Camera", True),
                ("VSync", True),
            ],
            "Controls": [
                ("Steering Sens", 1.0, 0.1, 5.0),
                ("Brake Sens", 5, 1, 10),
            ],
        }

        self.sliders: Dict[str, Slider] = {}
        self._hovered_category: Optional[int] = None
        self._hovered_option: Optional[int] = None
        self._close_button: Optional[pygame.Rect] = None

    def handle_input(
        self, event: Event, mouse_pos: Optional[MousePos] = None
    ) -> Optional[Dict[str, str]]:
        """Process input events for settings navigation and adjustment.
        
        Handles keyboard navigation (arrow keys, TAB, ESCAPE) for adjusting
        values and switching categories. Mouse clicks on categories, options,
        toggle buttons, and adjust buttons are also handled.
        
        Args:
            event: A pygame event object.
            mouse_pos: Optional mouse position for click detection.
            
        Returns:
            A dictionary with {"action": "changed"} or {"action": "close"}
            if an action occurred, or None if no action was triggered.
        """
        if event.type == pygame.KEYDOWN:
            cat: str = self.categories[self.selected_category]
            options: List[Tuple[Any, ...]] = self.settings[cat]

            if event.key == pygame.K_LEFT:
                self._adjust_value(cat, options[self.selected_option][0], -1)
                return {"action": "changed"}
            elif event.key == pygame.K_RIGHT:
                self._adjust_value(cat, options[self.selected_option][0], 1)
                return {"action": "changed"}
            elif event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(options)
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(options)
            elif event.key == pygame.K_TAB:
                self.selected_category = (self.selected_category + 1) % len(
                    self.categories
                )
                self.selected_option = 0
            elif event.key == pygame.K_ESCAPE:
                return {"action": "close"}

        if event.type == pygame.MOUSEBUTTONDOWN and mouse_pos:
            sw: int = pygame.display.get_surface().get_width()
            sh: int = pygame.display.get_surface().get_height()
            panel_w: int = LAYOUT.settings_panel_width
            panel_h: int = LAYOUT.settings_panel_height
            panel_x: int = sw // 2 - panel_w // 2
            panel_y: int = sh // 2 - panel_h // 2

            close_btn: pygame.Rect = pygame.Rect(
                panel_x + panel_w - 50, panel_y + 15, 35, 35
            )
            if close_btn.collidepoint(mouse_pos):
                return {"action": "close"}

            sidebar_w: int = LAYOUT.sidebar_width
            sidebar_x: int = panel_x + 20
            sidebar_y: int = panel_y + 80

            for i in range(len(self.categories)):
                cat_rect: pygame.Rect = pygame.Rect(
                    sidebar_x + 5, sidebar_y + 25 + i * 60, sidebar_w - 10, 45
                )
                if cat_rect.collidepoint(mouse_pos):
                    self.selected_category = i
                    self.selected_option = 0
                    return {"action": "changed"}

            cat = self.categories[self.selected_category]
            opts: List[Tuple[Any, ...]] = self.settings[cat]
            content_x: int = panel_x + sidebar_w + 35
            content_y: int = panel_y + 80

            for i in range(len(opts)):
                opt_y: int = content_y + 25 + i * ANIMATION.settings_option_spacing
                bar_rect: pygame.Rect = pygame.Rect(content_x, opt_y + 28, 350, 20)
                if bar_rect.collidepoint(mouse_pos):
                    self.selected_option = i
                    return {"action": "changed"}

                if i == self.selected_option:
                    val: Any = self.get_value(cat, opts[i][0])
                    if isinstance(val, bool):
                        toggle_rect: pygame.Rect = pygame.Rect(
                            content_x + 280, opt_y, 50, 25
                        )
                        if toggle_rect.collidepoint(mouse_pos):
                            self._adjust_value(cat, opts[i][0], 1)
                            return {"action": "changed"}
                    elif isinstance(val, str):
                        left_rect: pygame.Rect = pygame.Rect(
                            content_x + 200, opt_y, 30, 25
                        )
                        right_rect: pygame.Rect = pygame.Rect(
                            content_x + 320, opt_y, 30, 25
                        )
                        if left_rect.collidepoint(mouse_pos):
                            self._adjust_value(cat, opts[i][0], -1)
                            return {"action": "changed"}
                        elif right_rect.collidepoint(mouse_pos):
                            self._adjust_value(cat, opts[i][0], 1)
                            return {"action": "changed"}

        return None

    def update(self, mouse_pos: MousePos) -> None:
        """Update hover states based on mouse position.
        
        Tracks which category or option is currently hovered for
        visual feedback during rendering.
        
        Args:
            mouse_pos: Current (x, y) position of the mouse cursor.
            
        Returns:
            None
        """
        sw: int = pygame.display.get_surface().get_width()
        sh: int = pygame.display.get_surface().get_height()
        panel_w: int = LAYOUT.settings_panel_width
        panel_h: int = LAYOUT.settings_panel_height
        panel_x: int = sw // 2 - panel_w // 2
        panel_y: int = sh // 2 - panel_h // 2

        sidebar_w: int = LAYOUT.sidebar_width
        sidebar_x: int = panel_x + 20
        sidebar_y: int = panel_y + 80

        self._hovered_category = None
        self._hovered_option = None

        for i in range(len(self.categories)):
            cat_rect: pygame.Rect = pygame.Rect(
                sidebar_x + 5, sidebar_y + 25 + i * 60, sidebar_w - 10, 45
            )
            if cat_rect.collidepoint(mouse_pos):
                self._hovered_category = i
                return

        cat: str = self.categories[self.selected_category]
        opts: List[Tuple[Any, ...]] = self.settings[cat]
        content_x: int = panel_x + sidebar_w + 35
        content_y: int = panel_y + 80

        for i in range(len(opts)):
            opt_y: int = content_y + 25 + i * ANIMATION.settings_option_spacing
            bar_rect: pygame.Rect = pygame.Rect(content_x, opt_y + 28, 350, 20)
            if bar_rect.collidepoint(mouse_pos):
                self._hovered_option = i
                return

            val: Any = self.get_value(cat, opts[i][0])
            if isinstance(val, bool):
                toggle_rect: pygame.Rect = pygame.Rect(content_x + 280, opt_y, 50, 25)
                if toggle_rect.collidepoint(mouse_pos):
                    self._hovered_option = i
                    return
            elif isinstance(val, str):
                left_rect: pygame.Rect = pygame.Rect(content_x + 200, opt_y, 30, 25)
                right_rect: pygame.Rect = pygame.Rect(content_x + 320, opt_y, 30, 25)
                if left_rect.collidepoint(mouse_pos) or right_rect.collidepoint(
                    mouse_pos
                ):
                    self._hovered_option = i
                    return

    def _adjust_value(self, category: str, option: str, delta: int) -> None:
        """Adjust a setting value by the given delta.
        
        Modifies the setting value based on its type:
        - Discrete lists: Cycle through options using modulo
        - Numeric ranges: Adjust by step (0.5 or 5 depending on option name)
        - Booleans: Toggle between True/False
        
        Args:
            category: The category name containing the option.
            option: The option name to adjust.
            delta: Amount to adjust (+1 or -1).
            
        Returns:
            None
        """
        opts: List[Tuple[Any, ...]] = self.settings[category]
        for i, opt in enumerate(opts):
            if opt[0] == option:
                if len(opt) == 3 and isinstance(opt[2], list):
                    new_idx: int = (opt[1] + delta) % len(opt[2])
                    self.settings[category][i] = (opt[0], new_idx, opt[2])
                elif len(opt) == 4:
                    step: float = 5.0 if "Density" in option else 0.5
                    new_val: float = opt[1] + delta * step
                    new_val = max(opt[2], min(opt[3], new_val))
                    self.settings[category][i] = (opt[0], new_val, opt[2], opt[3])
                elif len(opt) == 2:
                    self.settings[category][i] = (opt[0], not opt[1])
                break

    def get_value(self, category: str, option: str) -> Any:
        """Get the current value of a setting.
        
        For discrete list options, returns the string at the current index.
        For other options, returns the direct value.
        
        Args:
            category: The category name containing the option.
            option: The option name to retrieve.
            
        Returns:
            The current value (type depends on option), or None if not found.
        """
        for opt in self.settings[category]:
            if opt[0] == option:
                if len(opt) == 3 and isinstance(opt[2], list):
                    return opt[2][opt[1]]
                return opt[1]
        return None

    def apply_to_game(self, game_settings: Any) -> None:
        """Apply current settings to a game settings object.
        
        Maps internal setting names to game_settings attributes:
        - Difficulty -> difficulty
        - Traffic Density -> obstacle_frequency
        - Show FPS -> show_fps
        - Fullscreen -> set_fullscreen() method
        - Show Camera -> show_camera
        - VSync -> vsync
        - Steering Sens -> steering_sensitivity
        - Brake Sens -> brake_threshold
        
        Args:
            game_settings: An object with attributes matching the mapped names.
            
        Returns:
            None
        """
        cat: str = self.categories[0]
        opts: List[Tuple[Any, ...]] = self.settings[cat]
        for opt in opts:
            if opt[0] == "Difficulty":
                game_settings.difficulty = self.get_value(cat, "Difficulty")
            elif opt[0] == "Traffic Density":
                game_settings.obstacle_frequency = self.get_value(
                    cat, "Traffic Density"
                )
            elif opt[0] == "Show FPS":
                game_settings.show_fps = self.get_value(cat, "Show FPS")

        cat = self.categories[1]
        opts = self.settings[cat]
        for opt in opts:
            if opt[0] == "Fullscreen":
                game_settings.set_fullscreen(self.get_value(cat, "Fullscreen"))
            elif opt[0] == "Show Camera":
                game_settings.show_camera = self.get_value(cat, "Show Camera")
            elif opt[0] == "VSync":
                game_settings.vsync = self.get_value(cat, "VSync")

        cat = self.categories[2]
        opts = self.settings[cat]
        for opt in opts:
            if opt[0] == "Steering Sens":
                game_settings.steering_sensitivity = self.get_value(
                    cat, "Steering Sens"
                )
            elif opt[0] == "Brake Sens":
                game_settings.brake_threshold = self.get_value(cat, "Brake Sens")

    def draw(self, screen: Surface) -> None:
        """Render the settings menu to the given screen.
        
        Draws the dark overlay, settings panel with title and close button,
        category sidebar with selection highlighting, and the content area
        with option labels, values, and progress bars where applicable.
        
        Args:
            screen: The pygame surface to draw on.
            
        Returns:
            None
        """
        sw: int = screen.get_width()
        sh: int = screen.get_height()

        overlay: Surface = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        panel_w: int = LAYOUT.settings_panel_width
        panel_h: int = LAYOUT.settings_panel_height
        panel_x: int = sw // 2 - panel_w // 2
        panel_y: int = sh // 2 - panel_h // 2

        draw_rounded_rect(
            screen, (20, 30, 50, 245), (panel_x, panel_y, panel_w, panel_h)
        )
        draw_rounded_rect(screen, self.accent_color, (panel_x, panel_y, panel_w, 4))
        draw_rounded_rect(
            screen, self.accent_color, (panel_x, panel_y, panel_w, panel_h), 1
        )

        title: Surface = self.font_title.render("SETTINGS", True, self.accent_color)
        screen.blit(title, (panel_x + 30, panel_y + 20))

        close_btn: pygame.Rect = pygame.Rect(
            panel_x + panel_w - 50, panel_y + 15, 35, 35
        )
        draw_rounded_rect(screen, COLORS.close_btn, close_btn)
        close_x: Surface = self.font_title.render("X", True, (255, 255, 255))
        screen.blit(close_x, (close_btn.x + 10, close_btn.y + 2))
        self._close_button = close_btn

        sidebar_w: int = LAYOUT.sidebar_width
        sidebar_x: int = panel_x + 20
        sidebar_y: int = panel_y + 80
        sidebar_h: int = panel_h - 110

        sb: Surface = pygame.Surface((sidebar_w, sidebar_h), pygame.SRCALPHA)
        sb.fill((25, 35, 55, 120))
        screen.blit(sb, (sidebar_x, sidebar_y))

        for i, cat in enumerate(self.categories):
            cat_y: int = sidebar_y + 25 + i * 60
            is_sel: bool = i == self.selected_category
            is_hover: bool = i == self._hovered_category

            bg_col: Tuple[int, int, int, int] = (
                (0, 180, 255, 60)
                if is_sel
                else ((0, 180, 255, 30) if is_hover else (0, 0, 0, 0))
            )
            sb2: Surface = pygame.Surface((sidebar_w - 10, 45), pygame.SRCALPHA)
            sb2.fill(bg_col)
            screen.blit(sb2, (sidebar_x + 5, cat_y))

            color: pygame.Color = self.accent_color if is_sel else self.text_color
            cat_text: Surface = self.font_option.render(cat, True, color)
            screen.blit(cat_text, (sidebar_x + 25, cat_y + 10))

        content_x: int = panel_x + sidebar_w + 35
        content_w: int = panel_w - sidebar_w - 55
        content_y: int = panel_y + 80

        cat = self.categories[self.selected_category]
        opts: List[Tuple[Any, ...]] = self.settings[cat]

        for i, opt in enumerate(opts):
            opt_y: int = content_y + 25 + i * ANIMATION.settings_option_spacing
            is_sel: bool = i == self.selected_option
            is_hover: bool = i == self._hovered_option

            if is_hover or is_sel:
                hover_bg: Surface = pygame.Surface((content_w - 20, 60), pygame.SRCALPHA)
                hover_bg.fill((0, 180, 255, 20))
                screen.blit(hover_bg, (content_x - 5, opt_y - 5))

            color = self.accent_color if is_sel else self.text_color
            label: Surface = self.font_label.render(opt[0], True, color)
            screen.blit(label, (content_x, opt_y))

            value: Any = self.get_value(cat, opt[0])

            if isinstance(value, bool):
                val_str: str = "ON" if value else "OFF"
                val_color: pygame.Color = self.accent_color if value else self.muted_color
            elif isinstance(value, str):
                val_str = value
                val_color = self.text_color
            else:
                val_str = f"{value:.0f}" if isinstance(value, float) else str(value)
                val_color = self.text_color

            val_text: Surface = self.font_option.render(val_str, True, val_color)
            screen.blit(val_text, (content_x + content_w - 100, opt_y))

            bar_y: int = opt_y + 30
            bar_h: int = 10
            pygame.draw.rect(
                screen,
                (40, 50, 70),
                (content_x, bar_y, content_w - 20, bar_h),
                border_radius=5,
            )

            if isinstance(opt[1], int) and len(opt) == 4:
                pct: float = (opt[1] - opt[2]) / (opt[3] - opt[2])
                fill_w: int = int((content_w - 20) * pct)
                if fill_w > 0:
                    pygame.draw.rect(
                        screen,
                        self.accent_color,
                        (content_x, bar_y, fill_w, bar_h),
                        border_radius=5,
                    )

        hint: Surface = self.font_hint.render(
            "← → Adjust  |  ↑ ↓ Navigate  |  TAB Category  |  ESC Close",
            True,
            self.muted_color,
        )
        screen.blit(
            hint,
            (panel_x + panel_w // 2 - hint.get_width() // 2, panel_y + panel_h - 30),
        )
