"""Modern polished game homepage with neon aesthetic.

Provides a clean, immersive main menu interface with:
- Centered action buttons (Start Game, Shop, Settings)
- Animated game title
- Dark theme with neon accents
- Particle effects background
- Player info and stats display
- Footer controls
"""

from __future__ import annotations

import math
from typing import Optional

import pygame

from ui.components.modern_button import ModernButton
from ui.components.particle_system import BackgroundEffect


class ModernHomePage:
    """Clean and modern game homepage with neon aesthetic and animations.
    
    Features:
    - Centered menu with three main buttons
    - Animated game title
    - Dark gradient background with particle effects
    - Player profile section
    - Score/coins display
    - Footer with options
    """

    def __init__(self, window_size: dict[str, int], player_name: str = "Player", coins: int = 0) -> None:
        """Initialize the modern homepage.
        
        Args:
            window_size: Dictionary with 'width' and 'height' keys.
            player_name: Player's display name.
            coins: Player's current coin count.
        """
        self.width: int = window_size["width"]
        self.height: int = window_size["height"]
        self.player_name: str = player_name
        self.coins: int = coins

        # Fonts
        self.title_font: pygame.font.Font | None = None
        self.subtitle_font: pygame.font.Font | None = None
        self.button_font: pygame.font.Font | None = None
        self.info_font: pygame.font.Font | None = None
        self.small_font: pygame.font.Font | None = None
        self._fonts_initialized: bool = False

        # Colors with improved contrast
        self.bg_top: tuple = (6, 10, 20)
        self.bg_bottom: tuple = (25, 35, 65)
        self.accent_cyan: tuple = (0, 220, 255)
        self.accent_purple: tuple = (160, 100, 255)
        self.accent_green: tuple = (100, 240, 150)
        self.text_color: tuple = (245, 250, 255)
        self.muted_color: tuple = (140, 160, 190)

        # Animation state
        self.elapsed_time: float = 0.0
        self.title_scale: float = 1.0
        self.title_glow: float = 0.5

        # Background effect
        self.background_effect: BackgroundEffect = BackgroundEffect(self.width, self.height)

        # Create buttons with improved spacing
        button_width: int = 340
        button_height: int = 80
        button_spacing: int = 120  # Vertical spacing between buttons
        button_x: int = (self.width - button_width) // 2
        buttons_start_y: int = self.height // 2 + 40

        self.start_button: ModernButton = ModernButton(
            button_x,
            buttons_start_y - button_spacing,
            button_width,
            button_height,
            "START GAME",
            font=self.button_font,
            accent_color=self.accent_cyan,
            secondary_color=self.accent_green,
        )
        self.start_button.is_selected = True  # Default selection

        self.shop_button: ModernButton = ModernButton(
            button_x,
            buttons_start_y,
            button_width,
            button_height,
            "SHOP",
            font=self.button_font,
            accent_color=self.accent_purple,
            secondary_color=self.accent_cyan,
        )

        self.settings_button: ModernButton = ModernButton(
            button_x,
            buttons_start_y + button_spacing,
            button_width,
            button_height,
            "SETTINGS",
            font=self.button_font,
            accent_color=self.accent_purple,
            secondary_color=self.accent_green,
        )

        # Button callbacks (to be set by game loop)
        self._callbacks: dict[str, callable] = {}

        # Mouse state
        self._mouse_pos: tuple[int, int] = (0, 0)
        self._mouse_pressed: tuple[bool, bool, bool] = (False, False, False)

        # Keyboard navigation
        self._focused_button_index: int = 0  # 0=Start, 1=Shop, 2=Settings
        self._buttons: list[ModernButton] = [self.start_button, self.shop_button, self.settings_button]
        self._update_focus()

    def _init_fonts(self) -> None:
        """Initialize fonts (called lazily on first draw/update)."""
        if self._fonts_initialized:
            return
        try:
            self.title_font = pygame.font.Font(None, 140)
            self.subtitle_font = pygame.font.Font(None, 54)
            self.button_font = pygame.font.Font(None, 44)
            self.info_font = pygame.font.Font(None, 32)
            self.small_font = pygame.font.Font(None, 26)
            self._fonts_initialized = True
            
            # Update button fonts
            self.start_button.font = self.button_font
            self.shop_button.font = self.button_font
            self.settings_button.font = self.button_font
        except Exception as e:
            # Log the error instead of silently passing
            import logging
            logging.getLogger(__name__).error(f"Failed to initialize fonts: {e}")
            # Create fallback fonts to prevent crashes
            self.title_font = pygame.font.SysFont("arial", 140)
            self.subtitle_font = pygame.font.SysFont("arial", 54)
            self.button_font = pygame.font.SysFont("arial", 44)
            self.info_font = pygame.font.SysFont("arial", 32)
            self.small_font = pygame.font.SysFont("arial", 26)

    def _update_focus(self) -> None:
        """Update button focus state based on current focus index."""
        for i, button in enumerate(self._buttons):
            button.is_selected = (i == self._focused_button_index)

    def _navigate_buttons(self, direction: int) -> None:
        """Navigate between buttons using arrow keys.
        
        Args:
            direction: -1 for up, 1 for down.
        """
        self._focused_button_index = (self._focused_button_index + direction) % len(self._buttons)
        self._update_focus()

    def set_callbacks(self, callbacks: dict[str, callable]) -> None:
        """Set button action callbacks.
        
        Args:
            callbacks: Dictionary with keys 'start', 'shop', 'settings'.
        """
        self._callbacks = callbacks

        if "start" in callbacks:
            self.start_button.callback = callbacks["start"]
        if "shop" in callbacks:
            self.shop_button.callback = callbacks["shop"]
        if "settings" in callbacks:
            self.settings_button.callback = callbacks["settings"]

    def _activate_focused_button(self) -> None:
        """Activate the currently focused button."""
        button = self._buttons[self._focused_button_index]
        if button.callback:
            button.callback()

    def update(self, delta_time: float) -> None:
        """Update homepage animations and state.
        
        Args:
            delta_time: Time elapsed since last update in seconds.
        """
        # Initialize fonts on first update
        self._init_fonts()
        
        self.elapsed_time += delta_time

        # Update title animation
        self.title_scale = 1.0 + 0.05 * math.sin(self.elapsed_time * 2)
        self.title_glow = 0.5 + 0.3 * math.sin(self.elapsed_time * 1.5)

        # Update background
        self.background_effect.update(delta_time)

        # Update buttons
        self.start_button.update(self._mouse_pos, self._mouse_pressed, delta_time)
        self.shop_button.update(self._mouse_pos, self._mouse_pressed, delta_time)
        self.settings_button.update(self._mouse_pos, self._mouse_pressed, delta_time)

    def draw(self, surface: pygame.Surface) -> None:
        """Render the homepage.
        
        Args:
            surface: The pygame surface to draw on.
        """
        # Initialize fonts on first draw
        self._init_fonts()
        
        # Draw gradient background
        self._draw_gradient_background(surface)

        # Draw particle effects
        self.background_effect.draw(surface)

        # Draw top info (player name and coins)
        self._draw_player_info(surface)

        # Draw game title
        self._draw_title(surface)

        # Draw buttons
        self.start_button.draw(surface)
        self.shop_button.draw(surface)
        self.settings_button.draw(surface)

        # Draw footer
        self._draw_footer(surface)

    def _draw_gradient_background(self, surface: pygame.Surface) -> None:
        """Draw animated gradient background.
        
        Args:
            surface: The pygame surface to draw on.
        """
        for y in range(self.height):
            progress = y / self.height
            r = int(self.bg_top[0] + (self.bg_bottom[0] - self.bg_top[0]) * progress)
            g = int(self.bg_top[1] + (self.bg_bottom[1] - self.bg_top[1]) * progress)
            b = int(self.bg_top[2] + (self.bg_bottom[2] - self.bg_top[2]) * progress)

            # Add subtle wave animation
            wave = math.sin(self.elapsed_time + y * 0.002) * 2
            r = max(0, min(255, int(r + wave)))
            g = max(0, min(255, int(g + wave)))
            b = max(0, min(255, int(b + wave * 0.5)))

            pygame.draw.line(surface, (r, g, b), (0, y), (self.width, y))

    def _draw_player_info(self, surface: pygame.Surface) -> None:
        """Draw player name and coins in top corners with improved spacing.
        
        Args:
            surface: The pygame surface to draw on.
        """
        margin: int = 40
        top_margin: int = 35

        # Top-left: Player name with background panel
        player_text = self.info_font.render(f"👤 {self.player_name}", True, self.accent_cyan)
        player_bg = pygame.Surface((player_text.get_width() + 20, player_text.get_height() + 10), pygame.SRCALPHA)
        player_bg.fill((92, 220, 255, 15))
        pygame.draw.rect(player_bg, self.accent_cyan, player_bg.get_rect(), width=1, border_radius=5)
        surface.blit(player_bg, (margin - 10, top_margin - 5))
        surface.blit(player_text, (margin, top_margin))

        # Top-right: Coins with background panel
        coins_text = self.info_font.render(f"💰 {self.coins}", True, self.accent_green)
        coins_rect = coins_text.get_rect()
        coins_bg = pygame.Surface((coins_rect.width + 20, coins_rect.height + 10), pygame.SRCALPHA)
        coins_bg.fill((80, 220, 160, 15))
        pygame.draw.rect(coins_bg, self.accent_green, coins_bg.get_rect(), width=1, border_radius=5)
        surface.blit(coins_bg, (self.width - coins_rect.width - margin + 5, top_margin - 5))
        surface.blit(coins_text, (self.width - coins_rect.width - margin + 15, top_margin))

    def _draw_title(self, surface: pygame.Surface) -> None:
        """Draw animated game title with improved spacing and effects.
        
        Args:
            surface: The pygame surface to draw on.
        """
        title_text = "8-BIT ENDLESS HIGHWAY"
        title_y = 100

        # Create title surface for scaling
        title_surf = self.title_font.render(title_text, True, self.text_color)
        original_rect = title_surf.get_rect()

        # Scale title
        scaled_width = int(original_rect.width * self.title_scale)
        scaled_height = int(original_rect.height * self.title_scale)
        scaled_title = pygame.transform.scale(title_surf, (scaled_width, scaled_height))

        # Draw glow effect
        self._draw_text_glow(
            surface,
            (self.width // 2, title_y),
            scaled_title,
            self.accent_purple,
            self.title_glow,
        )

        # Draw title
        title_rect = scaled_title.get_rect(center=(self.width // 2, title_y))
        surface.blit(scaled_title, title_rect)

        # Draw separator line
        line_y = title_y + 70
        line_width = 300
        pygame.draw.line(
            surface,
            self.accent_cyan,
            (self.width // 2 - line_width // 2, line_y),
            (self.width // 2 + line_width // 2, line_y),
            2
        )

        # Draw subtitle with better spacing
        subtitle = "Hand Gesture Racing"
        subtitle_surf = self.subtitle_font.render(subtitle, True, self.accent_cyan)
        subtitle_rect = subtitle_surf.get_rect(center=(self.width // 2, line_y + 40))

        # Add subtle animation to subtitle
        subtitle_alpha = int(200 + 55 * math.sin(self.elapsed_time * 2))
        subtitle_surf.set_alpha(subtitle_alpha)
        surface.blit(subtitle_surf, subtitle_rect)

    def _draw_text_glow(
        self,
        surface: pygame.Surface,
        pos: tuple[int, int],
        text_surf: pygame.Surface,
        glow_color: tuple,
        intensity: float,
    ) -> None:
        """Draw glow effect behind text.
        
        Args:
            surface: The pygame surface to draw on.
            pos: Center position (x, y).
            text_surf: The text surface.
            glow_color: Color of the glow.
            intensity: Glow intensity (0.0 to 1.0).
        """
        glow_radius = 20
        rect = text_surf.get_rect(center=pos)

        for i in range(glow_radius, 0, -2):
            alpha = int(30 * (1 - i / glow_radius) * intensity)
            glow_surf = pygame.Surface((rect.width + i * 2, rect.height + i * 2), pygame.SRCALPHA)

            # Draw blurred outline effect
            pygame.draw.ellipse(
                glow_surf,
                glow_color + (alpha,),
                glow_surf.get_rect().inflate(-i // 2, -i // 2),
            )

            surface.blit(glow_surf, (rect.x - i, rect.y - i))

    def _draw_footer(self, surface: pygame.Surface) -> None:
        """Draw footer with improved spacing and options.
        
        Args:
            surface: The pygame surface to draw on.
        """
        footer_y = self.height - 55
        margin = 40
        footer_height = 40
        
        # Draw footer background with slight transparency
        footer_bg = pygame.Surface((self.width, footer_height), pygame.SRCALPHA)
        footer_bg.fill((10, 12, 24, 200))
        pygame.draw.line(footer_bg, self.accent_purple, (0, 0), (self.width, 0), 1)
        surface.blit(footer_bg, (0, footer_y - footer_height + 15))

        # Left-aligned footer text with better spacing
        footer_text = self.small_font.render("🔊 Sound: ON  |  ❓ Help  |  © 2026 Racing Game", True, self.muted_color)
        surface.blit(footer_text, (margin, footer_y))

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle input events.
        
        Args:
            event: Pygame event to handle.
            
        Returns:
            Action string ('quit') or None.
        """
        if event.type == pygame.MOUSEMOTION:
            self._mouse_pos = event.pos

        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._mouse_pressed = pygame.mouse.get_pressed()

        elif event.type == pygame.MOUSEBUTTONUP:
            self._mouse_pressed = pygame.mouse.get_pressed()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "quit"
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate_focused_button()
            elif event.key == pygame.K_UP:
                self._navigate_buttons(-1)
            elif event.key == pygame.K_DOWN:
                self._navigate_buttons(1)
            elif event.key == pygame.K_TAB:
                # Tab also cycles through buttons
                direction = 1 if not (pygame.key.get_mods() & pygame.KMOD_SHIFT) else -1
                self._navigate_buttons(direction)

        return None

    def set_player_info(self, name: str, coins: int) -> None:
        """Update player display information.
        
        Args:
            name: Player name.
            coins: Coin count.
        """
        self.player_name = name
        self.coins = coins
