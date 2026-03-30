import random
from pathlib import Path

import config
import pygame

from environment.obstacle_manager import ObstacleManager
from models.lane import Lane
from models.oil_spill import OilSpill
from models.road import Road


class OilSpillManager:
    """Manages spawning, movement, and rendering of oil spill hazards on the road."""

    def __init__(
        self,
        road: Road,
        spawn_frequency: int = config.OIL_SPILL_SPAWN_FREQUENCY,
        max_oil_spills: int = config.MAX_OIL_SPILLS,
    ):
        """
        Initialize the oil spill manager with spawn parameters and resource loading.

        Args:
            road: Road geometry defining lane boundaries for spill placement.
            spawn_frequency: Frames between spawn attempts. Clamped to minimum of 1.
            max_oil_spills: Maximum number of simultaneous active oil spills allowed.
        """
        self.road = road
        self.spawn_frequency = max(1, int(spawn_frequency))
        self.max_oil_spills = max(1, int(max_oil_spills))
        self.oil_spills = pygame.sprite.Group()
        self.timer = 0
        self.model_dir = Path("resources/models/obstacles")
        self.oil_spill_models = self._load_oil_spill_models()
        self.model_scale_cache: dict[tuple[int, int], pygame.Surface] = {}
        self.blocking_groups: list[pygame.sprite.Group] = []

    def set_blocking_groups(self, groups: list[pygame.sprite.Group]) -> None:
        """
        Configure sprite groups that must not overlap with spawned oil spills.

        Args:
            groups: List of pygame sprite groups to check for collisions during spawn.
        """
        self.blocking_groups = groups

    def _load_oil_spill_models(self) -> list[pygame.Surface]:
        """
        Load oil spill model images from resources/models/obstacles directory.

        Only loads files matching the pattern "OilSpill*.png".
        Images are converted to alpha format if a display surface is available.

        Returns:
            List of loaded pygame Surface objects, empty if directory missing or no valid images.
        """
        if not self.model_dir.exists():
            return []

        models: list[pygame.Surface] = []
        for model_path in sorted(self.model_dir.glob("OilSpill*.png")):
            try:
                image = pygame.image.load(str(model_path))
                if pygame.display.get_surface() is not None:
                    image = image.convert_alpha()
                models.append(image)
            except pygame.error:
                continue
        return models

    def _get_random_oil_spill_image(self, lane: Lane) -> pygame.Surface | None:
        """
        Select and scale a random oil spill model to fit within lane constraints.

        Applies width ratio limits and caching to avoid repeated scaling operations.
        Target width respects lane fit and minimum size constraints.

        Args:
            lane: Target lane determining width constraints for scaling.

        Returns:
            Scaled pygame Surface ready for use, or None if no models are loaded.
        """
        if not self.oil_spill_models:
            return None

        model_index = random.randrange(len(self.oil_spill_models))
        source = self.oil_spill_models[model_index]

        lane_fit_width = max(1, lane.width - 20)
        target_width = min(lane_fit_width, int(lane.width * config.OIL_SPILL_LANE_WIDTH_RATIO))
        target_width = max(config.TRAFFIC_MIN_SIZE, target_width)

        cache_key = (model_index, target_width)
        cached = self.model_scale_cache.get(cache_key)
        if cached is not None:
            return cached

        source_width, source_height = source.get_size()
        scaled_height = max(18, int(source_height * (target_width / source_width)))
        scaled = pygame.transform.smoothscale(source, (target_width, scaled_height))
        self.model_scale_cache[cache_key] = scaled
        return scaled

    def _spawn_oil_spill(self) -> None:
        """
        Spawn a single oil spill at the top of a random valid lane.

        Attempts multiple times to find a non-overlapping position considering
        existing oil spills and blocking groups. Falls back to random lane after
        maximum attempts exceeded.
        """
        max_attempts = 10
        for _ in range(max_attempts):
            lane = self.road.random_lane()
            oil_image = self._get_random_oil_spill_image(lane)

            oil_width = max(28, int(lane.width * config.OIL_SPILL_LANE_WIDTH_RATIO))
            oil_height = max(18, int(oil_width * 0.6))
            if oil_image is not None:
                oil_width = oil_image.get_width()
                oil_height = oil_image.get_height()

            spawn_x = ObstacleManager._lane_spawn_x(lane, oil_width, min_padding=8)
            spawn_x = self.road.clamp_spawn_x_to_borders(
                spawn_x, oil_width, min_padding=8
            )
            spawn_y = -oil_height - random.randint(50, 240)

            overlap = False
            for oil in self.oil_spills:
                if (
                    oil.rect.left < spawn_x + oil_width
                    and oil.rect.right > spawn_x
                    and abs(oil.rect.y - spawn_y) < oil_height * 3
                ):
                    overlap = True
                    break

            if not overlap:
                spawn_rect = pygame.Rect(spawn_x, spawn_y, oil_width, oil_height)
                for group in self.blocking_groups:
                    for blocked_sprite in group:
                        if (
                            spawn_rect.left < blocked_sprite.rect.right
                            and spawn_rect.right > blocked_sprite.rect.left
                            and abs(blocked_sprite.rect.y - spawn_y) < oil_height * 3
                        ):
                            overlap = True
                            break
                    if overlap:
                        break
            if not overlap:
                break

        oil_spill = OilSpill(spawn_x, spawn_y, oil_width, oil_height, image=oil_image)
        self.oil_spills.add(oil_spill)

    def update(self, map_speed: int) -> None:
        """
        Advance the spawn timer, trigger oil spill spawning, and update all spills.

        Args:
            map_speed: Current map speed applied to oil spill movement.
        """
        self.timer += 1
        if self.timer >= self.spawn_frequency:
            self.timer = 0
            if len(self.oil_spills) < self.max_oil_spills:
                self._spawn_oil_spill()

        self.oil_spills.update(map_speed, self.road.height)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Render all active oil spills to the target surface.

        Args:
            surface: pygame Surface to draw oil spills onto.
        """
        self.oil_spills.draw(surface)
