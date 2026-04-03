"""Car selection UI system."""

import math
from typing import Callable, Optional

import pygame

from models.car_data import Car, get_car_by_id
from models.car_manager import CarManager


class CarSelectionUI:
    """Interactive car selection menu interface."""
    
    def __init__(self, window_size: dict, car_manager: CarManager, font_large: pygame.font.Font | None = None, font_small: pygame.font.Font | None = None):
        """
        Initialize car selection UI.
        
        Args:
            window_size: {'width': int, 'height': int}
            car_manager: CarManager instance
            font_large: Large font for titles
            font_small: Small font for details
        """
        self.width = window_size["width"]
        self.height = window_size["height"]
        self.car_manager = car_manager
        
        self.font_large = font_large or pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = font_small or pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)
        
        self.visible = False
        self.current_index = 0  # Index in all cars list
        self.selected_car: Optional[Car] = None
        self.animation_progress = 0.0
        self.show_unlock_animation = False
        self.unlock_animation_time = 0.0
        self.newly_unlocked_cars = []
        
        # Colors
        self.COLOR_BG = (20, 20, 30)
        self.COLOR_ACCENT = (0, 200, 255)
        self.COLOR_LOCKED = (100, 100, 100)
        self.COLOR_UNLOCKED = (0, 255, 100)
        self.COLOR_TEXT = (255, 255, 255)
        self.COLOR_RARITY = {
            "Common": (200, 200, 200),
            "Rare": (100, 200, 255),
            "Epic": (200, 100, 255),
            "Legendary": (255, 215, 0)
        }
        
        self.selected_callback: Optional[Callable[[Car], None]] = None
        self.close_callback: Optional[Callable[[], None]] = None
        
        # Initialize car index to selected car
        self._sync_index_to_selected()
    
    def _sync_index_to_selected(self) -> None:
        """Sync current index to selected car."""
        from models.car_data import CARS
        selected = self.car_manager.get_selected_car()
        if selected:
            for i, car in enumerate(CARS):
                if car.id == selected.id:
                    self.current_index = i
                    break
    
    def open(self) -> None:
        """Open the car selection menu."""
        self.visible = True
        self.animation_progress = 0.0
        self._sync_index_to_selected()
    
    def close(self) -> None:
        """Close the car selection menu."""
        self.visible = False
        if self.close_callback:
            self.close_callback()
    
    def update(self, delta_time: float) -> None:
        """Update UI state."""
        if not self.visible:
            return
        
        # Smooth animation
        self.animation_progress = min(1.0, self.animation_progress + delta_time * 3.0)
        
        # Update unlock animation
        if self.show_unlock_animation:
            self.unlock_animation_time += delta_time
            if self.unlock_animation_time > 3.0:
                self.show_unlock_animation = False
                self.unlock_animation_time = 0.0
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame events.
        
        Returns:
            True if event was handled
        """
        if not self.visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self.previous_car()
                return True
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self.next_car()
                return True
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self.select_current_car()
                return True
            elif event.key == pygame.K_ESCAPE:
                self.close()
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check if clicking on car
                car_rect = self._get_car_preview_rect()
                if car_rect.collidepoint(event.pos):
                    self.select_current_car()
                    return True
                
                # Check arrow buttons
                left_arrow_rect = pygame.Rect(100, self.height // 2 - 30, 60, 60)
                right_arrow_rect = pygame.Rect(self.width - 160, self.height // 2 - 30, 60, 60)
                
                if left_arrow_rect.collidepoint(event.pos):
                    self.previous_car()
                    return True
                elif right_arrow_rect.collidepoint(event.pos):
                    self.next_car()
                    return True
        
        return False
    
    def next_car(self) -> None:
        """Navigate to next car."""
        from models.car_data import CARS
        self.current_index = (self.current_index + 1) % len(CARS)
        self.animation_progress = 0.0
    
    def previous_car(self) -> None:
        """Navigate to previous car."""
        from models.car_data import CARS
        self.current_index = (self.current_index - 1) % len(CARS)
        self.animation_progress = 0.0
    
    def select_current_car(self) -> None:
        """Select the currently displayed car."""
        from models.car_data import CARS
        current_car = CARS[self.current_index]
        
        if self.car_manager.select_car(current_car.id):
            if self.selected_callback:
                self.selected_callback(current_car)
            self.close()
    
    def _get_car_preview_rect(self) -> pygame.Rect:
        """Get the rectangle for car preview area."""
        preview_width = 200
        preview_height = 300
        x = self.width // 2 - preview_width // 2
        y = self.height // 2 - preview_height // 2 - 50
        return pygame.Rect(x, y, preview_width, preview_height)
    
    def _draw_car_preview(self, surface: pygame.Surface, car: Car) -> None:
        """Draw the car preview visually."""
        rect = self._get_car_preview_rect()
        
        # Draw car body (simple rectangle with color)
        color = self._hex_to_rgb(car.color_hex)
        pygame.draw.rect(surface, color, rect, border_radius=10)
        pygame.draw.rect(surface, self.COLOR_ACCENT, rect, width=3, border_radius=10)
        
        # If unlocked, make it bright; if locked, make it dark
        if not self.car_manager.is_car_unlocked(car.id):
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surface.blit(overlay, rect)
            
            # Draw lock icon
            lock_text = self.font_large.render("🔒", True, self.COLOR_TEXT)
            lock_rect = lock_text.get_rect(center=rect.center)
            surface.blit(lock_text, lock_rect)
    
    def _draw_car_stats(self, surface: pygame.Surface, car: Car, x: int, y: int) -> None:
        """Draw car stats bars."""
        stats = [
            ("Speed", car.stats.speed),
            ("Handling", car.stats.handling),
            ("Accel", car.stats.acceleration),
            ("Weight", car.stats.weight),
        ]
        
        bar_width = 250
        bar_height = 20
        stat_spacing = 35
        
        for i, (label, value) in enumerate(stats):
            label_text = self.font_small.render(label, True, self.COLOR_TEXT)
            surface.blit(label_text, (x, y + i * stat_spacing))
            
            # Draw stat bar background
            bar_rect = pygame.Rect(x + 100, y + i * stat_spacing, bar_width, bar_height)
            pygame.draw.rect(surface, (50, 50, 50), bar_rect)
            
            # Draw stat bar fill
            fill_width = int(bar_width * (value / 100.0))
            fill_rect = pygame.Rect(x + 100, y + i * stat_spacing, fill_width, bar_height)
            pygame.draw.rect(surface, self.COLOR_ACCENT, fill_rect)
            
            # Draw value text
            value_text = self.font_tiny.render(f"{int(value)}", True, self.COLOR_TEXT)
            surface.blit(value_text, (x + 100 + bar_width + 10, y + i * stat_spacing + 2))
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the car selection UI."""
        if not self.visible:
            return
        
        from models.car_data import CARS
        
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        # Current car
        current_car = CARS[self.current_index]
        
        # Title
        title_text = self.font_large.render("SELECT YOUR CAR", True, self.COLOR_ACCENT)
        title_rect = title_text.get_rect(center=(self.width // 2, 50))
        surface.blit(title_text, title_rect)
        
        # Draw car preview
        self._draw_car_preview(surface, current_car)
        
        # Draw car info
        car_name_text = self.font_medium.render(current_car.name, True, self.COLOR_TEXT)
        car_name_rect = car_name_text.get_rect(center=(self.width // 2, self.height // 2 + 180))
        surface.blit(car_name_text, car_name_rect)
        
        # Draw rarity
        rarity_color = self.COLOR_RARITY.get(current_car.rarity, self.COLOR_TEXT)
        rarity_text = self.font_small.render(current_car.rarity, True, rarity_color)
        rarity_rect = rarity_text.get_rect(center=(self.width // 2, self.height // 2 + 215))
        surface.blit(rarity_text, rarity_rect)
        
        # Draw description
        desc_text = self.font_tiny.render(current_car.description, True, (200, 200, 200))
        desc_rect = desc_text.get_rect(center=(self.width // 2, self.height // 2 + 245))
        surface.blit(desc_text, desc_rect)
        
        # Draw stats
        self._draw_car_stats(surface, current_car, 100, self.height - 280)
        
        # Draw unlock info if locked
        if not self.car_manager.is_car_unlocked(current_car.id):
            progress = self.car_manager.get_unlock_progress(current_car.id)
            unlock_score = progress.get("unlock_score", 0)
            current_score = progress.get("current_score", 0)
            
            unlock_text = self.font_small.render(
                f"REACH {unlock_score} POINTS TO UNLOCK", 
                True, 
                self.COLOR_LOCKED
            )
            unlock_rect = unlock_text.get_rect(center=(self.width // 2, self.height - 100))
            surface.blit(unlock_text, unlock_rect)
            
            # Progress bar
            progress_bar_width = 300
            progress_bar_height = 20
            progress_bar_x = self.width // 2 - progress_bar_width // 2
            progress_bar_y = self.height - 70
            
            pygame.draw.rect(surface, (50, 50, 50), (progress_bar_x, progress_bar_y, progress_bar_width, progress_bar_height))
            
            progress_percent = min(100, (current_score / unlock_score * 100)) if unlock_score > 0 else 0
            fill_width = int(progress_bar_width * (progress_percent / 100.0))
            pygame.draw.rect(surface, (255, 100, 100), (progress_bar_x, progress_bar_y, fill_width, progress_bar_height))
            
            progress_text = self.font_tiny.render(f"{int(progress_percent)}%", True, self.COLOR_TEXT)
            surface.blit(progress_text, (progress_bar_x + 10, progress_bar_y + 2))
        else:
            selected_text = self.font_small.render("✓ UNLOCKED", True, self.COLOR_UNLOCKED)
            selected_rect = selected_text.get_rect(center=(self.width // 2, self.height - 100))
            surface.blit(selected_text, selected_rect)
        
        # Draw navigation arrows
        self._draw_navigation_arrows(surface)
        
        # Draw selected indicator
        is_selected = self.car_manager.selected_car_id == current_car.id
        if is_selected:
            indicator = self.font_small.render("★ SELECTED ★", True, self.COLOR_ACCENT)
            indicator_rect = indicator.get_rect(center=(self.width // 2, self.height - 130))
            surface.blit(indicator, indicator_rect)
        
        # Draw controls
        controls_text = self.font_tiny.render(
            "← → or A/D: Navigate | ENTER/SPACE: Select | ESC: Cancel",
            True,
            (150, 150, 150)
        )
        controls_rect = controls_text.get_rect(center=(self.width // 2, self.height - 30))
        surface.blit(controls_text, controls_rect)
        
        # Draw unlock animation
        if self.show_unlock_animation:
            self._draw_unlock_animation(surface)
    
    def _draw_navigation_arrows(self, surface: pygame.Surface) -> None:
        """Draw left/right navigation arrows."""
        arrow_color = self.COLOR_ACCENT
        arrow_size = 30
        
        # Left arrow
        left_x = 100
        left_y = self.height // 2
        pygame.draw.polygon(surface, arrow_color, [
            (left_x, left_y),
            (left_x + arrow_size, left_y - arrow_size),
            (left_x + arrow_size, left_y + arrow_size)
        ])
        
        # Right arrow
        right_x = self.width - 100
        right_y = self.height // 2
        pygame.draw.polygon(surface, arrow_color, [
            (right_x, right_y),
            (right_x - arrow_size, right_y - arrow_size),
            (right_x - arrow_size, right_y + arrow_size)
        ])
    
    def _draw_unlock_animation(self, surface: pygame.Surface) -> None:
        """Draw new car unlocked animation."""
        time = self.unlock_animation_time
        
        # Pulse effect
        pulse = math.sin(time * 5) * 0.5 + 0.5
        scale = 1.0 + pulse * 0.2
        
        animation_text = self.font_large.render("🎉 NEW CAR UNLOCKED! 🎉", True, (255, 215, 0))
        scaled_text = pygame.transform.scale(
            animation_text,
            (int(animation_text.get_width() * scale), int(animation_text.get_height() * scale))
        )
        
        rect = scaled_text.get_rect(center=(self.width // 2, self.height // 4))
        surface.blit(scaled_text, rect)
    
    def show_new_unlocks(self, newly_unlocked: list) -> None:
        """Show animation for newly unlocked cars."""
        if newly_unlocked:
            self.show_unlock_animation = True
            self.unlock_animation_time = 0.0
            self.newly_unlocked_cars = newly_unlocked
