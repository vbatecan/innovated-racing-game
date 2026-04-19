import os
import random

import pygame
from core.resource_manager import ResourceManager

from models.road import Road


class HeartBonus(pygame.sprite.Sprite):
    """
    A collectible heart bonus sprite that moves down the screen with the road scroll.
    Automatically removes itself when passing below the visible area.
    """
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        image: pygame.Surface | None = None,
    ):
        """
        Initialize a heart bonus sprite at the specified position.

        Args:
            x: Horizontal spawn coordinate in pixels.
            y: Vertical spawn coordinate in pixels (typically negative for off-screen spawn).
            width: Bounding width for the sprite rect.
            height: Bounding height for the sprite rect.
            image: Optional pre-loaded sprite image; if None, creates a blank surface.
        """
        super().__init__()
        self.width = width
        self.height = height
        if image:
            self.image = image
            self.rect = self.image.get_rect()
        else:
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
            self.rect = pygame.Rect(x, y, width, height)
        self.rect.x = x
        self.rect.y = y
        # CRITICAL FIX: Initialize the collision mask (was missing entirely)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, speed: int, road_height: int) -> None:
        """
        Move the heart downward and remove if it passes below the road.

        Args:
            speed: Pixels to move downward this frame.
            road_height: The bottom boundary for culling off-screen sprites.
        """
        self.rect.y += speed
        if self.rect.top > road_height:
            self.kill()


class HeartBonusManager:
    """
    Manages the spawning, updating, and rendering of collectible heart bonuses.
    Controls spawn frequency and enforces a maximum on-screen count.
    """
    def __init__(
        self,
        road: Road,
        spawn_frequency: int = 600,
        max_hearts: int = 1,
    ):
        """
        Initialize the heart bonus manager with spawn configuration.

        Args:
            road: The road model providing lane geometry for spawn positioning.
            spawn_frequency: Frames between spawn attempts (minimum 60).
            max_hearts: Maximum number of hearts allowed on screen simultaneously.
        """
        self.road = road
        self.spawn_frequency = max(60, spawn_frequency)
        self.max_hearts = max_hearts
        self.hearts = pygame.sprite.Group()
        self.timer = 0
        self._heart_image = self._load_heart_image()
        self.heart_width = 40
        self.heart_height = 40
        if self._heart_image:
            img_w, img_h = self._heart_image.get_size()
            scale = min(self.heart_width / img_w, self.heart_height / img_h)
            new_w = max(1, int(img_w * scale))
            new_h = max(1, int(img_h * scale))
            self._heart_image = pygame.transform.smoothscale(
                self._heart_image, (new_w, new_h)
            )
            self.heart_width = new_w
            self.heart_height = new_h

    def _load_heart_image(self) -> pygame.Surface | None:
        """
        Load the heart bonus sprite from the resources directory.

        Returns:
            The loaded and alpha-converted image, or None if loading fails.
        """
        filepath = os.path.join("resources", "models", "full hp.png")
        if os.path.exists(filepath):
            try:
                img = ResourceManager.load_image(filepath, convert_alpha=True)
                return img
            except pygame.error:
                pass
        return None

    def _spawn_heart(self) -> None:
        """
        Spawn a new heart bonus in a random lane above the visible screen area,
        centered within the selected lane.
        """
        lane = self.road.get_lane(random.randint(0, self.road.lane_count - 1))
        lane_center = lane.left + lane.width // 2
        spawn_x = lane_center - self.heart_width // 2
        spawn_x = self.road.clamp_spawn_x_to_borders(spawn_x, self.heart_width)
        spawn_y = -self.heart_height - random.randint(50, 150)

        heart = HeartBonus(
            spawn_x,
            spawn_y,
            self.heart_width,
            self.heart_height,
            image=self._heart_image,
        )
        self.hearts.add(heart)

    def update(self, speed: int) -> None:
        """
        Advance the spawn timer and update all heart bonus positions.
        Spawns new hearts when timer exceeds frequency and below max count.

        Args:
            speed: Current scroll speed affecting heart movement.
        """
        self.timer += 1
        if self.timer >= self.spawn_frequency:
            self.timer = 0
            if len(self.hearts) < self.max_hearts:
                self._spawn_heart()

        self.hearts.update(speed, self.road.height)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Render all active heart bonuses to the target surface.

        Args:
            surface: The pygame surface to draw hearts onto.
        """
        self.hearts.draw(surface)

    def get_hearts(self) -> pygame.sprite.Group:
        """
        Access the sprite group containing all active heart bonuses.

        Returns:
            The pygame sprite group of heart bonuses.
        """
        return self.hearts

    def clear(self) -> None:
        """Remove all active heart bonuses from the game."""
        self.hearts.empty()
