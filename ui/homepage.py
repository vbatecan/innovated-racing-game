"""Homepage and car shop screen for the racing game.

Provides the main menu interface with a browsable car grid, hero display for
selected vehicles, and game launch controls. Handles car selection, unlock
notifications, and visual feedback for locked/unlocked vehicles.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Optional

import pygame

from models.car_data import CARS, Car
from models.car_manager import CarManager


class HomePageScreen:
    """Polished homepage interface featuring a browsable car selection grid.

    Displays available cars in a card grid layout with a hero section showing
    detailed stats for the selected car. Supports keyboard and mouse navigation,
    handles car unlock states, and provides visual feedback for locked vehicles.
    """

    def __init__(self, window_size: dict[str, int], car_manager: CarManager) -> None:
        self.width = window_size["width"]
        self.height = window_size["height"]
        self.car_manager = car_manager

        self.title_font = pygame.font.Font(None, 84)
        self.section_font = pygame.font.Font(None, 46)
        self.body_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)
        self.tiny_font = pygame.font.Font(None, 20)

        self.background_top = (10, 12, 24)
        self.background_bottom = (28, 34, 58)
        self.panel_color = (18, 22, 38)
        self.card_color = (32, 38, 60)
        self.accent_color = (92, 220, 255)
        self.highlight_color = (255, 205, 88)
        self.text_color = (246, 248, 255)
        self.muted_color = (163, 176, 204)
        self.lock_color = (125, 130, 142)
        self.good_color = (84, 255, 160)

        self.cards_per_row = 4
        self.card_rects: list[pygame.Rect] = []
        self._selected_index = 0
        self._elapsed = 0.0
        self._car_images: dict[int, pygame.Surface] = {}
        self._unlock_notice_timer = 0.0
        self._unlock_notice_text: str | None = None
        self._load_car_images()
        self._sync_selected_to_manager()

    def _load_car_images(self) -> None:
        for car in CARS:
            self._car_images[car.id] = self._load_scaled_image(car.image_path, (210, 130))

    def _load_scaled_image(self, image_path: str, size: tuple[int, int]) -> Optional[pygame.Surface]:
        """Load and scale an image to the specified dimensions.

        Args:
            image_path: Path to the image file.
            size: Target dimensions as (width, height).

        Returns:
            Scaled pygame Surface if successful, None if the file doesn't exist or fails to load.
        """
        path = Path(image_path)
        if not path.exists():
            return None

        try:
            image = pygame.image.load(str(path)).convert_alpha()
            scaled = pygame.transform.smoothscale(image, size)
            canvas = pygame.Surface(size, pygame.SRCALPHA)
            canvas.blit(scaled, scaled.get_rect(center=canvas.get_rect().center))
            return canvas
        except pygame.error:
            return None

    def _sync_selected_to_manager(self) -> None:
        """Synchronize the selected index with the car manager's current selection."""
        selected = self.car_manager.get_selected_car()
        if selected is None:
            return

        for index, car in enumerate(CARS):
            if car.id == selected.id:
                self._selected_index = index
                break

    @property
    def selected_car(self) -> Car:
        """Get the currently selected car from the CARS list.

        Returns:
            The Car object at the current selection index.
        """
        return CARS[self._selected_index]

    def update(self, delta_time: float) -> None:
        """Update animation timers and unlock notice countdown.

        Args:
            delta_time: Time elapsed since last frame in seconds.
        """
        self._elapsed += delta_time
        if self._unlock_notice_timer > 0.0:
            self._unlock_notice_timer = max(0.0, self._unlock_notice_timer - delta_time)
            if self._unlock_notice_timer == 0.0:
                self._unlock_notice_text = None

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Process input events for navigation, selection, and game control.

        Supports keyboard (arrows/WASD, Enter, Space, Escape) and mouse clicks
        for interacting with the car grid and action buttons.

        Args:
            event: Pygame event to process.

        Returns:
            Action string ("start", "quit", "locked") if a game action was triggered,
            None for navigation events that don't trigger game actions.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.previous_car()
                return None
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                self.next_car()
                return None
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.start_game()
            if event.key == pygame.K_ESCAPE:
                return "quit"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.card_rects):
                if rect.collidepoint(event.pos):
                    self._selected_index = index
                    if self.car_manager.is_car_unlocked(self.selected_car.id):
                        self.car_manager.select_car(self.selected_car.id)
                    return None

            if self._button_rect("start").collidepoint(event.pos):
                return self.start_game()
            if self._button_rect("quit").collidepoint(event.pos):
                return "quit"

            if self._left_arrow_rect().collidepoint(event.pos):
                self.previous_car()
            elif self._right_arrow_rect().collidepoint(event.pos):
                self.next_car()

        return None

    def previous_car(self) -> None:
        """Navigate to the previous car in the carousel. Wraps around to the end if at the start."""
        self._selected_index = (self._selected_index - 1) % len(CARS)

    def next_car(self) -> None:
        """Navigate to the next car in the carousel. Wraps around to the start if at the end."""
        self._selected_index = (self._selected_index + 1) % len(CARS)

    def start_game(self) -> str:
        """Attempt to start the game with the currently selected car.

        Validates that the selected car is unlocked before allowing the game to start.
        If locked, displays a notice with the unlock requirement.

        Returns:
            "start" if the game can begin, "locked" if the car is not yet unlocked.
        """
        car = self.selected_car
        if not self.car_manager.is_car_unlocked(car.id):
            self._unlock_notice_text = f"Reach {car.unlock_score} points to unlock {car.name}."
            self._unlock_notice_timer = 2.5
            return "locked"

        self.car_manager.select_car(car.id)
        return "start"

    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        """Convert a hexadecimal color string to RGB values.

        Args:
            hex_color: Hex color string (e.g., "#FF5733").

        Returns:
            Tuple of three integers (R, G, B) with values 0-255.
        """
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def _blend(self, a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
        """Linearly interpolate between two colors.

        Args:
            a: Starting RGB color tuple.
            b: Ending RGB color tuple.
            t: Interpolation factor between 0.0 and 1.0.

        Returns:
            Blended RGB color tuple.
        """
        t = max(0.0, min(1.0, t))
        return tuple(int(x + (y - x) * t) for x, y in zip(a, b))

    def _draw_background(self, surface: pygame.Surface) -> None:
        """Render the animated background with gradient and decorative elements.

        Args:
            surface: Pygame surface to draw on.
        """
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            color = self._blend(self.background_top, self.background_bottom, t)
            pygame.draw.line(surface, color, (0, y), (self.width, y))

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for i in range(12):
            pulse = 20 + int(14 * math.sin(self._elapsed * 1.1 + i * 0.45))
            alpha = 14 + (i % 5) * 3
            color = (*self.accent_color, alpha)
            pygame.draw.circle(overlay, color, (120 + i * 130, 92 + (i % 4) * 42), pulse)

        for x in range(0, self.width, 72):
            pygame.draw.line(overlay, (255, 255, 255, 10), (x, 0), (x - 80, self.height))
        surface.blit(overlay, (0, 0))

    def _draw_panel(self, surface: pygame.Surface, rect: pygame.Rect, fill: tuple[int, int, int], border: tuple[int, int, int]) -> None:
        """Draw a rounded rectangle panel with border.

        Args:
            surface: Pygame surface to draw on.
            rect: Panel rectangle dimensions.
            fill: RGB fill color tuple.
            border: RGB border color tuple.
        """
        pygame.draw.rect(surface, fill, rect, border_radius=18)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=18)

    def _draw_soft_shadow(self, surface: pygame.Surface, rect: pygame.Rect, alpha: int = 70) -> None:
        """Draw a soft drop shadow beneath a rectangle for depth effect.

        Args:
            surface: Pygame surface to draw on.
            rect: Source rectangle to cast shadow from.
            alpha: Shadow opacity (0-255).
        """
        shadow = pygame.Surface((rect.width + 26, rect.height + 26), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, alpha), shadow.get_rect(), border_radius=24)
        surface.blit(shadow, shadow.get_rect(center=(rect.centerx + 6, rect.centery + 8)))

    def _button_rect(self, name: str) -> pygame.Rect:
        """Calculate the rectangle for a named action button.

        Args:
            name: Button identifier ("start" or "quit").

        Returns:
            Rectangle defining the button's position and size.
        """
        if name == "start":
            return pygame.Rect(self.width // 2 - 190, self.height - 92, 170, 52)
        return pygame.Rect(self.width // 2 + 18, self.height - 92, 130, 52)

    def _left_arrow_rect(self) -> pygame.Rect:
        """Calculate the rectangle for the left navigation arrow button.

        Returns:
            Rectangle defining the left arrow's position and size.
        """
        return pygame.Rect(24, self.height // 2 - 32, 54, 64)

    def _right_arrow_rect(self) -> pygame.Rect:
        """Calculate the rectangle for the right navigation arrow button.

        Returns:
            Rectangle defining the right arrow's position and size.
        """
        return pygame.Rect(self.width - 78, self.height // 2 - 32, 54, 64)

    def _draw_car_card(self, surface: pygame.Surface, car: Car, rect: pygame.Rect, selected: bool) -> None:
        """Render a single car card in the grid display.

        Displays car image, rarity badge, name, and lock status. Applies visual
        effects for selection state and locked status.

        Args:
            surface: Pygame surface to draw on.
            car: Car data object to display.
            rect: Card rectangle position and dimensions.
            selected: Whether this card is currently selected.
        """
        unlocked = self.car_manager.is_car_unlocked(car.id)
        border_color = self.highlight_color if selected else (58, 68, 104)
        fill = self.card_color if unlocked else (24, 28, 36)
        self._draw_soft_shadow(surface, rect, 55 if selected else 38)
        self._draw_panel(surface, rect, fill, border_color)

        image = self._car_images.get(car.id)
        image_rect = pygame.Rect(rect.x + 16, rect.y + 12, rect.width - 32, 92)
        if image is not None:
            image_surface = pygame.transform.smoothscale(image, image_rect.size)
            if not unlocked:
                dim = pygame.Surface(image_surface.get_size(), pygame.SRCALPHA)
                dim.fill((0, 0, 0, 120))
                image_surface.blit(dim, (0, 0))
            surface.blit(image_surface, image_rect)
        else:
            car_color = self._hex_to_rgb(car.color_hex)
            preview_rect = pygame.Rect(rect.x + 42, rect.y + 20, rect.width - 84, 72)
            pygame.draw.rect(surface, car_color if unlocked else (90, 90, 90), preview_rect, border_radius=12)

        top_badge = pygame.Rect(rect.x + 12, rect.y + 10, 64, 26)
        badge_fill = self.highlight_color if unlocked else self.lock_color
        self._draw_panel(surface, top_badge, badge_fill, (255, 255, 255) if unlocked else self.lock_color)
        badge_text = self.tiny_font.render(car.rarity[:3].upper(), True, (20, 24, 38) if unlocked else self.text_color)
        surface.blit(badge_text, badge_text.get_rect(center=top_badge.center))

        name_text = self.small_font.render(car.name, True, self.text_color if unlocked else self.lock_color)
        surface.blit(name_text, name_text.get_rect(center=(rect.centerx, rect.bottom - 50)))

        rarity_color = {
            "Common": (210, 210, 220),
            "Rare": (94, 182, 255),
            "Epic": (190, 120, 255),
            "Legendary": (255, 206, 82),
        }.get(car.rarity, self.text_color)
        rarity_text = self.tiny_font.render(car.rarity, True, rarity_color if unlocked else self.lock_color)
        surface.blit(rarity_text, rarity_text.get_rect(center=(rect.centerx, rect.bottom - 24)))

        if not unlocked:
            lock_text = self.section_font.render("🔒", True, self.lock_color)
            surface.blit(lock_text, lock_text.get_rect(center=(rect.centerx, rect.centery + 10)))
            unlock_hint = self.tiny_font.render(f"Reach {car.unlock_score:,} to unlock", True, self.lock_color)
            surface.blit(unlock_hint, unlock_hint.get_rect(center=(rect.centerx, rect.bottom - 72)))

        if selected:
            pulse = 1.0 + math.sin(self._elapsed * 4.0) * 0.03
            outline = pygame.Surface((rect.width + 10, rect.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(outline, (*self.accent_color, 90), outline.get_rect(), width=4, border_radius=20)
            outline = pygame.transform.smoothscale(outline, (int(outline.get_width() * pulse), int(outline.get_height() * pulse)))
            surface.blit(outline, outline.get_rect(center=rect.center))

    def _draw_selected_hero(self, surface: pygame.Surface) -> None:
        """Render the hero section displaying detailed info for the selected car.

        Shows large car image with floating animation, stat bars, description,
        unlock status, and unlock notification if applicable.

        Args:
            surface: Pygame surface to draw on.
        """
        car = self.selected_car
        unlocked = self.car_manager.is_car_unlocked(car.id)

        hero_rect = pygame.Rect(70, 120, self.width - 140, 280)
        self._draw_soft_shadow(surface, hero_rect, 72)
        self._draw_panel(surface, hero_rect, self.panel_color, (74, 88, 130))

        title = self.title_font.render("TRIKY GARAGE", True, self.text_color)
        surface.blit(title, (hero_rect.x + 28, hero_rect.y + 22))

        subtitle = self.body_font.render("Choose a car, unlock better rides, and start your run.", True, self.muted_color)
        surface.blit(subtitle, (hero_rect.x + 28, hero_rect.y + 88))

        accent_line = pygame.Rect(hero_rect.x + 28, hero_rect.y + 136, 200, 4)
        pygame.draw.rect(surface, self.accent_color, accent_line, border_radius=4)

        hero_image = self._car_images.get(car.id)
        if hero_image is not None:
            angle = math.sin(self._elapsed * 1.8) * 2.5
            floating = math.sin(self._elapsed * 2.1) * 6.0
            image = pygame.transform.rotozoom(hero_image, angle, 1.85)
            image_rect = image.get_rect(midright=(hero_rect.right - 90, hero_rect.centery + floating))
            if not unlocked:
                dim = pygame.Surface(image.get_size(), pygame.SRCALPHA)
                dim.fill((0, 0, 0, 100))
                image.blit(dim, (0, 0))
            surface.blit(image, image_rect)

        name_text = self.section_font.render(car.name, True, self.highlight_color)
        surface.blit(name_text, (hero_rect.x + 28, hero_rect.y + 154))

        description = self.small_font.render(car.description, True, self.text_color)
        surface.blit(description, (hero_rect.x + 28, hero_rect.y + 202))

        stat_base_y = hero_rect.y + 152
        stat_rows = [
            ("SPD", car.stats.speed, self.accent_color),
            ("HND", car.stats.handling, self.good_color),
            ("ACC", car.stats.acceleration, self.highlight_color),
            ("WGT", car.stats.weight, (255, 134, 104)),
        ]
        for row_index, (label, value, color) in enumerate(stat_rows):
            y = stat_base_y + row_index * 24
            surface.blit(self.tiny_font.render(label, True, self.muted_color), (hero_rect.x + 28, y))
            pygame.draw.rect(surface, (52, 60, 84), (hero_rect.x + 74, y + 4, 170, 10), border_radius=5)
            pygame.draw.rect(surface, color, (hero_rect.x + 74, y + 4, int(170 * (value / 100.0)), 10), border_radius=5)

        best_score = int(self.car_manager.best_score)
        score_text = self.small_font.render(f"Best score: {best_score:,}", True, self.muted_color)
        surface.blit(score_text, (hero_rect.x + 28, hero_rect.bottom - 62))

        if unlocked:
            status = self.small_font.render("Unlocked and ready", True, self.good_color)
        else:
            status = self.small_font.render(f"Reach {car.unlock_score:,} to unlock", True, (255, 142, 142))
        surface.blit(status, (hero_rect.x + 28, hero_rect.bottom - 34))

        if self._unlock_notice_text:
            notice_w, notice_h = 640, 58
            notice_rect = pygame.Rect(self.width // 2 - notice_w // 2, hero_rect.bottom + 14, notice_w, notice_h)
            notice_alpha = int(255 * min(1.0, self._unlock_notice_timer / 2.5))
            notice_surface = pygame.Surface((notice_w, notice_h), pygame.SRCALPHA)
            pygame.draw.rect(notice_surface, (18, 24, 38, 230), notice_surface.get_rect(), border_radius=18)
            pygame.draw.rect(notice_surface, (*self.highlight_color, 255), notice_surface.get_rect(), width=2, border_radius=18)
            notice_text = self.body_font.render(self._unlock_notice_text, True, self.highlight_color)
            notice_surface.blit(notice_text, notice_text.get_rect(center=notice_surface.get_rect().center))
            notice_surface.set_alpha(notice_alpha)
            surface.blit(notice_surface, notice_rect)

    def _draw_car_grid(self, surface: pygame.Surface) -> None:
        """Render the grid of all available car cards.

        Calculates positions and renders each car card, storing click rectangles
        for hit detection.

        Args:
            surface: Pygame surface to draw on.
        """
        self.card_rects.clear()

        grid_top = 440
        card_w = 246
        card_h = 172
        gap_x = 18
        gap_y = 18
        start_x = 70

        for index, car in enumerate(CARS):
            row = index // self.cards_per_row
            col = index % self.cards_per_row
            x = start_x + col * (card_w + gap_x)
            y = grid_top + row * (card_h + gap_y)
            rect = pygame.Rect(x, y, card_w, card_h)
            self.card_rects.append(rect)
            self._draw_car_card(surface, car, rect, index == self._selected_index)

    def _draw_buttons(self, surface: pygame.Surface) -> None:
        """Render the START GAME and QUIT action buttons.

        Start button appearance changes based on whether the selected car is unlocked.

        Args:
            surface: Pygame surface to draw on.
        """
        start_rect = self._button_rect("start")
        quit_rect = self._button_rect("quit")

        can_start = self.car_manager.is_car_unlocked(self.selected_car.id)
        start_fill = self.accent_color if can_start else (60, 72, 92)

        self._draw_panel(surface, start_rect, start_fill, self.highlight_color if can_start else (92, 98, 118))
        self._draw_panel(surface, quit_rect, (40, 48, 68), (88, 98, 124))

        start_label = self.body_font.render("START GAME", True, (8, 16, 26) if can_start else self.muted_color)
        quit_label = self.body_font.render("QUIT", True, self.text_color)
        surface.blit(start_label, start_label.get_rect(center=start_rect.center))
        surface.blit(quit_label, quit_label.get_rect(center=quit_rect.center))

        if not can_start:
            hint = self.tiny_font.render(f"Locked until {self.selected_car.unlock_score:,} points", True, self.lock_color)
            surface.blit(hint, hint.get_rect(midtop=(start_rect.centerx, start_rect.bottom + 10)))

    def _draw_navigation(self, surface: pygame.Surface) -> None:
        """Render the left and right navigation arrow buttons.

        Args:
            surface: Pygame surface to draw on.
        """
        left = self._left_arrow_rect()
        right = self._right_arrow_rect()
        for rect, direction in ((left, -1), (right, 1)):
            self._draw_panel(surface, rect, (28, 34, 56), self.accent_color)
            if direction < 0:
                points = [(rect.centerx + 10, rect.top + 14), (rect.centerx - 10, rect.centery), (rect.centerx + 10, rect.bottom - 14)]
            else:
                points = [(rect.centerx - 10, rect.top + 14), (rect.centerx + 10, rect.centery), (rect.centerx - 10, rect.bottom - 14)]
            pygame.draw.polygon(surface, self.text_color, points)

    def _draw_footer(self, surface: pygame.Surface) -> None:
        """Render the footer with improved spacing.

        Args:
            surface: Pygame surface to draw on.
        """
        footer_height = 50
        footer_y = self.height - footer_height
        
        # Draw footer background
        footer_bg = pygame.Surface((self.width, footer_height), pygame.SRCALPHA)
        footer_bg.fill((10, 12, 24, 200))
        pygame.draw.line(footer_bg, self.accent_color, (0, 0), (self.width, 0), 1)
        surface.blit(footer_bg, (0, footer_y))

    def draw(self, surface: pygame.Surface) -> None:
        """Render the complete homepage interface with improved spacing.

        Draws all components: background, header, hero section, car grid,
        navigation buttons, action buttons, and footer.

        Args:
            surface: Pygame surface to draw the homepage onto.
        """
        self._draw_background(surface)

        # Main header with better spacing
        header = self.title_font.render("RACING GAME HOME", True, self.text_color)
        header_y = 40
        surface.blit(header, (70, header_y))
        
        # Separator line below header
        pygame.draw.line(surface, self.accent_color, (70, header_y + 65), (self.width - 70, header_y + 65), 2)

        # Best score panel with better positioning
        best_score = self.car_manager.best_score
        best_rect = pygame.Rect(self.width - 320, header_y + 15, 240, 88)
        self._draw_panel(surface, best_rect, self.panel_color, self.accent_color)
        best_title = self.small_font.render("BEST SCORE", True, self.muted_color)
        best_value = self.section_font.render(f"{int(best_score)}", True, self.highlight_color)
        surface.blit(best_title, (best_rect.x + 18, best_rect.y + 12))
        surface.blit(best_value, (best_rect.x + 18, best_rect.y + 34))

        self._draw_selected_hero(surface)
        self._draw_navigation(surface)
        self._draw_car_grid(surface)
        self._draw_buttons(surface)
        self._draw_footer(surface)