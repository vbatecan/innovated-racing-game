"""Car selection UI system."""

import math
from typing import Callable, Optional

import pygame
import core.sound_manager as sound_manager_module

from models.car_data import Car, get_car_by_id
from models.car_manager import CarManager


def _play_ui_click_sfx() -> None:
    manager = sound_manager_module.sound_manager
    if manager is not None:
        manager.play_ui_click()


class CarSelectionUI:
    """Interactive car selection menu interface for browsing and selecting vehicles.

    Provides a visual carousel for navigating available cars, displaying stats,
    unlock requirements, and rarity information. Supports both keyboard and mouse input.
    """

    def __init__(
        self,
        window_size: dict,
        car_manager: CarManager,
        font_large: pygame.font.Font | None = None,
        font_small: pygame.font.Font | None = None,
    ):
        """Initialize the car selection UI with rendering configuration.

        Args:
            window_size: Dictionary with 'width' and 'height' keys defining the screen dimensions.
            car_manager: Manager instance handling car unlock states and selection persistence.
            font_large: Optional large font for titles. Uses default pygame font if not provided.
            font_small: Optional small font for details. Uses default pygame font if not provided.
        """
        self.width = window_size["width"]
        self.height = window_size["height"]
        self.car_manager = car_manager
        
        self.font_large = font_large or pygame.font.Font(None, 64)
        self.font_medium = pygame.font.Font(None, 44)
        self.font_small = font_small or pygame.font.Font(None, 28)
        self.font_tiny = pygame.font.Font(None, 20)

        self.visible = False
        self.current_index = 0
        self.selected_car: Optional[Car] = None
        self.animation_progress = 0.0
        self.show_unlock_animation = False
        self.unlock_animation_time = 0.0
        self.newly_unlocked_cars = []

        self.COLOR_BG = (20, 20, 30)
        self.COLOR_ACCENT = (0, 200, 255)
        self.COLOR_LOCKED = (100, 100, 100)
        self.COLOR_UNLOCKED = (0, 255, 100)
        self.COLOR_TEXT = (255, 255, 255)
        self.COLOR_RARITY = {
            "Common": (200, 200, 200),
            "Rare": (100, 200, 255),
            "Epic": (200, 100, 255),
            "Legendary": (255, 215, 0),
        }

        self.selected_callback: Optional[Callable[[Car], None]] = None
        self.close_callback: Optional[Callable[[], None]] = None

        self._sync_index_to_selected()
    
    def _sync_index_to_selected(self) -> None:
        """Synchronize the current carousel index to match the car manager's selected car."""
        from models.car_data import CARS

        selected = self.car_manager.get_selected_car()
        if selected:
            for i, car in enumerate(CARS):
                if car.id == selected.id:
                    self.current_index = i
                    break
    
    def open(self) -> None:
        """Open the car selection menu and reset animation state."""
        self.visible = True
        self.animation_progress = 0.0
        self._sync_index_to_selected()

    def close(self) -> None:
        """Close the car selection menu and invoke the close callback if set."""
        self.visible = False
        if self.close_callback:
            self.close_callback()
    
    def update(self, delta_time: float) -> None:
        """Update UI animation states and unlock animation timing.

        Args:
            delta_time: Time elapsed since the last frame in seconds.
        """
        if not self.visible:
            return

        self.animation_progress = min(1.0, self.animation_progress + delta_time * 3.0)

        if self.show_unlock_animation:
            self.unlock_animation_time += delta_time
            if self.unlock_animation_time > 3.0:
                self.show_unlock_animation = False
                self.unlock_animation_time = 0.0
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Process pygame input events for navigation and selection.

        Supports keyboard (arrow keys, WASD, Enter, Space, Escape) and mouse input
        for navigating the car carousel and making selections.

        Args:
            event: Pygame event object to process.

        Returns:
            True if the event was consumed by this UI, False otherwise.
        """
        if not self.visible:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.previous_car()
                return True
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.next_car()
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.select_current_car()
                return True
            elif event.key == pygame.K_ESCAPE:
                self.close()
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                car_rect = self._get_car_preview_rect()
                if car_rect.collidepoint(event.pos):
                    _play_ui_click_sfx()
                    self.select_current_car()
                    return True

                preview_rect = self._get_car_preview_rect()
                arrow_y = preview_rect.centery
                left_arrow_rect = pygame.Rect(20, arrow_y - 50, 80, 100)
                right_arrow_rect = pygame.Rect(self.width - 100, arrow_y - 50, 80, 100)

                if left_arrow_rect.collidepoint(event.pos):
                    _play_ui_click_sfx()
                    self.previous_car()
                    return True
                elif right_arrow_rect.collidepoint(event.pos):
                    _play_ui_click_sfx()
                    self.next_car()
                    return True

        return False
    
    def next_car(self) -> None:
        """Navigate to the next car in the carousel. Wraps around to the start if at the end."""
        from models.car_data import CARS

        self.current_index = (self.current_index + 1) % len(CARS)
        self.animation_progress = 0.0

    def previous_car(self) -> None:
        """Navigate to the previous car in the carousel. Wraps around to the end if at the start."""
        from models.car_data import CARS

        self.current_index = (self.current_index - 1) % len(CARS)
        self.animation_progress = 0.0
    
    def select_current_car(self) -> None:
        """Attempt to select the currently displayed car.

        If the car is unlocked, invokes the selected callback and closes the menu.
        Locked cars cannot be selected.
        """
        from models.car_data import CARS

        current_car = CARS[self.current_index]

        if self.car_manager.select_car(current_car.id):
            if self.selected_callback:
                self.selected_callback(current_car)
            self.close()
    
    def _get_car_preview_rect(self) -> pygame.Rect:
        """Calculate the rectangle defining the car preview display area.

        Returns:
            Rectangle centered horizontally, positioned above the stats area.
        """
        preview_width = 280
        preview_height = 280
        x = self.width // 2 - preview_width // 2
        y = 100
        return pygame.Rect(x, y, preview_width, preview_height)

    def _draw_car_preview(self, surface: pygame.Surface, car: Car) -> None:
        """Render the visual preview of a car with locked/unlocked state overlay.

        Args:
            surface: Pygame surface to draw on.
            car: Car data object containing color and unlock information.
        """
        rect = self._get_car_preview_rect()

        color = self._hex_to_rgb(car.color_hex)
        pygame.draw.rect(surface, color, rect, border_radius=10)
        pygame.draw.rect(surface, self.COLOR_ACCENT, rect, width=3, border_radius=10)

        if not self.car_manager.is_car_unlocked(car.id):
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surface.blit(overlay, rect)

            lock_text = self.font_large.render("\U0001F512", True, self.COLOR_TEXT)
            lock_rect = lock_text.get_rect(center=rect.center)
            surface.blit(lock_text, lock_rect)
    
    def _draw_car_stats(self, surface: pygame.Surface, car: Car, x: int, y: int) -> None:
        """Render stat bars showing car performance attributes.

        Args:
            surface: Pygame surface to draw on.
            car: Car data object containing stats.
            x: Horizontal position for the stats block.
            y: Vertical position for the stats block.
        """
        stats = [
            ("Speed", car.stats.speed),
            ("Handling", car.stats.handling),
            ("Accel", car.stats.acceleration),
            ("Weight", car.stats.weight),
        ]

        bar_width = 320
        bar_height = 26
        stat_spacing = 60

        for i, (label, value) in enumerate(stats):
            label_text = self.font_small.render(label, True, self.COLOR_TEXT)
            surface.blit(label_text, (x, y + i * stat_spacing))

            bar_rect = pygame.Rect(x + 140, y + i * stat_spacing, bar_width, bar_height)
            pygame.draw.rect(surface, (50, 50, 50), bar_rect, border_radius=5)

            fill_width = int(bar_width * (value / 100.0))
            fill_rect = pygame.Rect(x + 140, y + i * stat_spacing, fill_width, bar_height)
            pygame.draw.rect(surface, self.COLOR_ACCENT, fill_rect, border_radius=5)

            value_text = self.font_tiny.render(f"{int(value)}", True, self.COLOR_TEXT)
            surface.blit(value_text, (x + 140 + bar_width + 20, y + i * stat_spacing + 4))
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert a hexadecimal color string to an RGB tuple.

        Args:
            hex_color: Hex color string (e.g., "#FF5733" or "FF5733").

        Returns:
            Tuple of three integers representing RGB values (0-255).
        """
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    
    def draw(self, surface: pygame.Surface) -> None:
        """Render the complete car selection UI including car preview, stats, and navigation.

        Args:
            surface: Pygame surface to draw the UI onto.
        """
        if not self.visible:
            return

        from models.car_data import CARS

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        current_car = CARS[self.current_index]

        title_text = self.font_large.render("SELECT YOUR CAR", True, self.COLOR_ACCENT)
        title_rect = title_text.get_rect(center=(self.width // 2, 50))
        surface.blit(title_text, title_rect)

        self._draw_car_preview(surface, current_car)

        preview_rect = self._get_car_preview_rect()
        info_y_start = preview_rect.bottom + 75

        car_name_text = self.font_medium.render(current_car.name, True, self.COLOR_TEXT)
        car_name_rect = car_name_text.get_rect(center=(self.width // 2, info_y_start))
        surface.blit(car_name_text, car_name_rect)

        rarity_color = self.COLOR_RARITY.get(current_car.rarity, self.COLOR_TEXT)
        rarity_text = self.font_small.render(current_car.rarity, True, rarity_color)
        rarity_rect = rarity_text.get_rect(center=(self.width // 2, info_y_start + 55))
        surface.blit(rarity_text, rarity_rect)

        desc_text = self.font_tiny.render(current_car.description, True, (200, 200, 200))
        desc_rect = desc_text.get_rect(center=(self.width // 2, info_y_start + 95))
        surface.blit(desc_text, desc_rect)

        self._draw_car_stats(surface, current_car, 60, info_y_start + 145)

        if not self.car_manager.is_car_unlocked(current_car.id):
            progress = self.car_manager.get_unlock_progress(current_car.id)
            unlock_score = progress.get("unlock_score", 0)
            current_score = progress.get("current_score", 0)

            unlock_text = self.font_small.render(
                f"REACH {unlock_score} POINTS TO UNLOCK", True, self.COLOR_LOCKED
            )
            unlock_rect = unlock_text.get_rect(center=(self.width // 2, self.height - 130))
            surface.blit(unlock_text, unlock_rect)

            progress_bar_width = 350
            progress_bar_height = 28
            progress_bar_x = self.width // 2 - progress_bar_width // 2
            progress_bar_y = self.height - 80

            pygame.draw.rect(
                surface,
                (50, 50, 50),
                (progress_bar_x, progress_bar_y, progress_bar_width, progress_bar_height),
                border_radius=5
            )

            progress_percent = min(100, (current_score / unlock_score * 100)) if unlock_score > 0 else 0
            fill_width = int(progress_bar_width * (progress_percent / 100.0))
            pygame.draw.rect(
                surface,
                (255, 100, 100),
                (progress_bar_x, progress_bar_y, fill_width, progress_bar_height),
                border_radius=5
            )

            progress_text = self.font_tiny.render(f"{int(progress_percent)}%", True, self.COLOR_TEXT)
            surface.blit(progress_text, (progress_bar_x + 15, progress_bar_y + 6))
        else:
            selected_text = self.font_small.render("\u2713 UNLOCKED", True, self.COLOR_UNLOCKED)
            selected_rect = selected_text.get_rect(center=(self.width // 2, self.height - 130))
            surface.blit(selected_text, selected_rect)

        self._draw_navigation_arrows(surface)

        is_selected = self.car_manager.selected_car_id == current_car.id
        if is_selected:
            indicator = self.font_small.render("\u2605 SELECTED \u2605", True, self.COLOR_ACCENT)
            indicator_rect = indicator.get_rect(center=(self.width // 2, self.height - 75))
            surface.blit(indicator, indicator_rect)

        if self.show_unlock_animation:
            self._draw_unlock_animation(surface)
    
    def _draw_navigation_arrows(self, surface: pygame.Surface) -> None:
        """Render left and right navigation arrow indicators.

        Args:
            surface: Pygame surface to draw on.
        """
        arrow_color = self.COLOR_ACCENT
        arrow_size = 45

        preview_rect = self._get_car_preview_rect()
        arrow_y = preview_rect.centery

        left_x = 50
        pygame.draw.polygon(
            surface,
            arrow_color,
            [
                (left_x, arrow_y),
                (left_x + arrow_size, arrow_y - arrow_size),
                (left_x + arrow_size, arrow_y + arrow_size),
            ],
        )

        right_x = self.width - 50
        pygame.draw.polygon(
            surface,
            arrow_color,
            [
                (right_x, arrow_y),
                (right_x - arrow_size, arrow_y - arrow_size),
                (right_x - arrow_size, arrow_y + arrow_size),
            ],
        )
    
    def _draw_unlock_animation(self, surface: pygame.Surface) -> None:
        """Render the "new car unlocked" celebration animation with pulsing text.

        Args:
            surface: Pygame surface to draw on.
        """
        time = self.unlock_animation_time

        pulse = math.sin(time * 5) * 0.5 + 0.5
        scale = 1.0 + pulse * 0.2

        animation_text = self.font_large.render("\U0001F389 NEW CAR UNLOCKED! \U0001F389", True, (255, 215, 0))
        scaled_text = pygame.transform.scale(
            animation_text,
            (int(animation_text.get_width() * scale), int(animation_text.get_height() * scale)),
        )

        rect = scaled_text.get_rect(center=(self.width // 2, self.height // 4))
        surface.blit(scaled_text, rect)

    def show_new_unlocks(self, newly_unlocked: list) -> None:
        """Trigger the unlock animation for newly unlocked cars.

        Args:
            newly_unlocked: List of car IDs that were just unlocked.
        """
        if newly_unlocked:
            self.show_unlock_animation = True
            self.unlock_animation_time = 0.0
            self.newly_unlocked_cars = newly_unlocked
