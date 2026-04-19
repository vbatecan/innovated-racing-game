import random
from pathlib import Path

import config
import pygame
from core.resource_manager import ResourceManager

from models.br_hazard import BRHazard
from models.lane import Lane
from models.road import Road
from environment.obstacle_manager import ObstacleManager


class BRManager:
    """
    Manages the lifecycle of BR (Barrier/Blocker) hazards on the road including
    spawning, updating positions, and rendering. Enforces a maximum on-screen
    count and collision avoidance with other sprite groups.
    """

    def __init__(
            self,
            road: Road,
            spawn_frequency: int = config.BR_SPAWN_FREQUENCY,
            max_brs: int = config.MAX_BRS,
    ):
        """
        Initialize the BR hazard manager with spawn parameters and resource loading.

        Args:
            road: The road model providing lane geometry and spawn constraints.
            spawn_frequency: Frames between spawn attempts (minimum 1).
            max_brs: Maximum number of BR hazards allowed on screen simultaneously.
        """
        self.road = road
        self.spawn_frequency = max(1, int(spawn_frequency))
        self.max_brs = max(1, int(max_brs))
        self.brs = pygame.sprite.Group()
        self.timer = 0
        self.model_dir = Path("resources/models/obstacles")
        self.br_models = self._load_br_models()
        self.model_scale_cache: dict[tuple[int, int], pygame.Surface] = {}
        self.blocking_groups: list[pygame.sprite.Group] = []

    def set_blocking_groups(self, groups: list[pygame.sprite.Group]) -> None:
        """
        Configure sprite groups that BR hazards must avoid overlapping during spawn.

        Args:
            groups: List of pygame sprite groups to check for collisions.
        """
        self.blocking_groups = groups

    def _load_br_models(self) -> list[pygame.Surface]:
        """
        Load BR hazard sprite images from the obstacle resource directory.

        Returns:
            List of loaded and alpha-converted pygame surfaces.
        """
        if not self.model_dir.exists():
            return []

        models: list[pygame.Surface] = []
        for model_path in sorted(self.model_dir.glob("BR*.png")):
            try:
                image = ResourceManager.load_image(str(model_path), convert_alpha=True)
                if pygame.display.get_surface() is not None:
                    image = image.convert_alpha()
                models.append(image)
            except pygame.error:
                continue
        return models

    def _get_random_br_image(self, lane: Lane) -> pygame.Surface | None:
        """
        Select and scale a random BR model to fit within the specified lane.
        Uses caching to avoid redundant scaling operations.

        Args:
            lane: The target lane for determining appropriate image dimensions.

        Returns:
            A scaled pygame surface or None if no models are available.
        """
        if not self.br_models:
            return None

        model_index = random.randrange(len(self.br_models))
        source = self.br_models[model_index]

        lane_fit_width = max(1, lane.width - 20)
        target_width = min(lane_fit_width, int(lane.width * config.BR_LANE_WIDTH_RATIO))
        target_width = max(config.TRAFFIC_MIN_SIZE, target_width)

        cache_key = (model_index, target_width)
        cached = self.model_scale_cache.get(cache_key)
        if cached is not None:
            return cached

        source_width, source_height = source.get_size()
        scaled_height = max(20, int(source_height * (target_width / source_width)))
        scaled = pygame.transform.smoothscale(source, (target_width, scaled_height))
        self.model_scale_cache[cache_key] = scaled
        return scaled

    def _spawn_br(self) -> None:
        """
        Attempt to spawn a new BR hazard in a random lane with collision checking.
        Performs multiple attempts to find a non-overlapping position respecting
        both existing BR hazards and configured blocking groups.
        """
        max_attempts = 10
        for _ in range(max_attempts):
            lane = self.road.random_lane()
            br_image = self._get_random_br_image(lane)

            br_width = max(20, int(lane.width * config.BR_LANE_WIDTH_RATIO))
            br_height = max(20, int(br_width * 0.9))
            if br_image is not None:
                br_width = br_image.get_width()
                br_height = br_image.get_height()

            spawn_x = ObstacleManager._lane_spawn_x(lane, br_width, min_padding=10)
            spawn_x = self.road.clamp_spawn_x_to_borders(
                spawn_x, br_width, min_padding=10
            )
            spawn_y = -br_height - random.randint(40, 220)

            overlap = False
            for br in self.brs:
                if (
                        br.rect.left < spawn_x + br_width
                        and br.rect.right > spawn_x
                        and abs(br.rect.y - spawn_y) < br_height * 3
                ):
                    overlap = True
                    break

            if not overlap:
                spawn_rect = pygame.Rect(spawn_x, spawn_y, br_width, br_height)
                for group in self.blocking_groups:
                    for blocked_sprite in group:
                        if (
                                spawn_rect.left < blocked_sprite.rect.right
                                and spawn_rect.right > blocked_sprite.rect.left
                                and abs(blocked_sprite.rect.y - spawn_y) < br_height * 4
                        ):
                            overlap = True
                            break
                    if overlap:
                        break
            if not overlap:
                break

        br = BRHazard(spawn_x, spawn_y, br_width, br_height, image=br_image)
        self.brs.add(br)

    def update(self, map_speed: int) -> None:
        """
        Advance the spawn timer and update all BR hazard positions.
        Spawns new hazards when timer exceeds frequency and below max count.

        Args:
            map_speed: Current scroll speed affecting hazard movement.
        """
        self.timer += 1
        if self.timer >= self.spawn_frequency:
            self.timer = 0
            if len(self.brs) < self.max_brs:
                self._spawn_br()

        self.brs.update(map_speed, self.road.height)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Render all active BR hazards to the target surface.

        Args:
            surface: The pygame surface to draw hazards onto.
        """
        self.brs.draw(surface)

