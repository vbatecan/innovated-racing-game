import random
from pathlib import Path

import config
import pygame

from models.crack import Crack
from models.lane import Lane
from models.road import Road
from environment.obstacle_manager import ObstacleManager


class CrackManager:
    """Spawn, update, and render low-volume road crack hazards."""

    def __init__(
            self,
            road: Road,
            spawn_frequency: int = config.CRACK_SPAWN_FREQUENCY,
            max_cracks: int = config.MAX_CRACKS,
    ):
        self.road = road
        self.spawn_frequency = max(1, int(spawn_frequency))
        self.max_cracks = max(1, int(max_cracks))
        self.cracks = pygame.sprite.Group()
        self.timer = 0
        self.model_dir = Path("resources/models/obstacles")
        self.crack_models = self._load_crack_models()
        self.model_scale_cache: dict[tuple[int, int], pygame.Surface] = {}

    def _load_crack_models(self) -> list[pygame.Surface]:
        """Load crack sprites from the obstacle resource directory."""
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

    def _spawn_crack(self) -> None:
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
        crack = Crack(spawn_x, spawn_y, crack_width, crack_height, image=crack_image)
        self.cracks.add(crack)

    def update(self, map_speed: int, is_braking: bool = False) -> None:
        if not is_braking:
            self.timer += 1
            if self.timer >= self.spawn_frequency:
                self.timer = 0
                if len(self.cracks) < self.max_cracks:
                    self._spawn_crack()

        self.cracks.update(map_speed, self.road.height, is_braking)

    def draw(self, surface: pygame.Surface) -> None:
        self.cracks.draw(surface)
