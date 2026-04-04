import random
from pathlib import Path

import config
import pygame

from models.crack import Crack
from models.lane import Lane
from models.road import Road
from environment.obstacle_manager import ObstacleManager


class CrackManager:
    """
    Manages the lifecycle of road crack hazards including spawning, updating
    positions based on scroll speed, and rendering. Maintains a configurable
    maximum number of simultaneous cracks on screen.
    """

    def __init__(
            self,
            road: Road,
            spawn_frequency: int = config.CRACK_SPAWN_FREQUENCY,
            max_cracks: int = config.MAX_CRACKS,
    ):
        """
        Initialize the crack hazard manager with spawn parameters.

        Args:
            road: The road model providing lane geometry and spawn constraints.
            spawn_frequency: Frames between spawn attempts (minimum 1).
            max_cracks: Maximum number of crack hazards allowed on screen.
        """
        self.road = road
        self.spawn_frequency = max(1, int(spawn_frequency))
        self.max_cracks = max(1, int(max_cracks))
        self.cracks = pygame.sprite.Group()
        self.timer = 0
        self.model_dir = Path("resources/models/obstacles")
        self.crack_models = self._load_crack_models()
        self.model_scale_cache: dict[tuple[int, int], pygame.Surface] = {}
        self.blocking_groups: list[pygame.sprite.Group] = []

    def _load_crack_models(self) -> list[pygame.Surface]:
        """
        Load crack sprite images from the obstacle resource directory.

        Returns:
            List of loaded and alpha-converted pygame surfaces.
        """
        if not self.model_dir.exists():
            return []

        models: list[pygame.Surface] = []
        for model_path in sorted(self.model_dir.glob("Crack*.png")):
            try:
                image = pygame.image.load(str(model_path))
                if pygame.display.get_surface() is not None:
                    image = image.convert_alpha()
                models.append(image)
            except pygame.error:
                continue
        return models

    def _get_random_crack_image(self, lane: Lane) -> pygame.Surface | None:
        """
        Select and scale a random crack model to fit within the specified lane.
        Uses caching to avoid redundant scaling operations.

        Args:
            lane: The target lane for determining appropriate image dimensions.

        Returns:
            A scaled pygame surface or None if no models are available.
        """
        if not self.crack_models:
            return None

        model_index = random.randrange(len(self.crack_models))
        source = self.crack_models[model_index]
        lane_fit_width = max(1, lane.width - 20)
        target_width = min(
            lane_fit_width, int(lane.width * config.CRACK_LANE_WIDTH_RATIO)
        )
        target_width = max(config.TRAFFIC_MIN_SIZE, target_width)

        cache_key = (model_index, target_width)
        cached = self.model_scale_cache.get(cache_key)
        if cached is not None:
            return cached

        source_width, source_height = source.get_size()
        scaled_height = max(12, int(source_height * (target_width / source_width)))
        scaled = pygame.transform.smoothscale(source, (target_width, scaled_height))
        self.model_scale_cache[cache_key] = scaled
        return scaled

    def set_blocking_groups(self, groups: list[pygame.sprite.Group]) -> None:
        """
        Configure sprite groups that crack hazards must avoid overlapping during spawn.

        Args:
            groups: List of pygame sprite groups to check for collisions.
        """
        self.blocking_groups = groups

    def _spawn_crack(self) -> None:
        """
        Spawn a new crack hazard in a random lane above the visible screen area.
        Attempts multiple times to find a non-overlapping position considering
        existing cracks and blocking groups.
        """
        max_attempts = 10
        for _ in range(max_attempts):
            lane = self.road.random_lane()
            crack_image = self._get_random_crack_image(lane)

            crack_width = max(20, int(lane.width * config.CRACK_LANE_WIDTH_RATIO))
            crack_height = max(12, crack_width // 2)
            if crack_image is not None:
                crack_width = crack_image.get_width()
                crack_height = crack_image.get_height()

            spawn_x = ObstacleManager._lane_spawn_x(lane, crack_width, min_padding=14)
            spawn_x = self.road.clamp_spawn_x_to_borders(
                spawn_x, crack_width, min_padding=14
            )
            spawn_y = -crack_height - random.randint(40, 260)

            # Check for overlap with existing cracks
            overlap = False
            for crack in self.cracks:
                if (
                    crack.rect.left < spawn_x + crack_width
                    and crack.rect.right > spawn_x
                    and abs(crack.rect.y - spawn_y) < crack_height * 3
                ):
                    overlap = True
                    break

            # Check for overlap with blocking groups
            if not overlap:
                spawn_rect = pygame.Rect(spawn_x, spawn_y, crack_width, crack_height)
                for group in self.blocking_groups:
                    for blocked_sprite in group:
                        if (
                            spawn_rect.left < blocked_sprite.rect.right
                            and spawn_rect.right > blocked_sprite.rect.left
                            and abs(blocked_sprite.rect.y - spawn_y) < crack_height * 4
                        ):
                            overlap = True
                            break
                    if overlap:
                        break
            
            if not overlap:
                break

        crack = Crack(spawn_x, spawn_y, crack_width, crack_height, image=crack_image)
        self.cracks.add(crack)

    def update(self, map_speed: int) -> None:
        """
        Advance the spawn timer and update all crack hazard positions.
        Spawns new cracks when timer exceeds frequency and below max count.

        Args:
            map_speed: Current scroll speed affecting hazard movement.
        """
        self.timer += 1
        if self.timer >= self.spawn_frequency:
            self.timer = 0
            if len(self.cracks) < self.max_cracks:
                self._spawn_crack()

        self.cracks.update(map_speed, self.road.height)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Render all active crack hazards to the target surface.

        Args:
            surface: The pygame surface to draw hazards onto.
        """
        self.cracks.draw(surface)
