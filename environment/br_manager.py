import random
from pathlib import Path

import config
import pygame

from environment.models.br_hazard import BRHazard
from environment.models.lane import Lane
from environment.models.road import Road
from environment.obstacle_manager import ObstacleManager


class BRManager:
    """Spawn, update, and render BR hazards with a strict on-screen cap."""

    def __init__(
            self,
            road: Road,
            spawn_frequency: int = config.BR_SPAWN_FREQUENCY,
            max_brs: int = config.MAX_BRS,
    ):
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
        """Set sprite groups that BR spawns must avoid overlapping."""
        self.blocking_groups = groups

    def _load_br_models(self) -> list[pygame.Surface]:
        if not self.model_dir.exists():
            return []

        models: list[pygame.Surface] = []
        for model_path in sorted(self.model_dir.glob("BR*.png")):
            try:
                image = pygame.image.load(str(model_path))
                if pygame.display.get_surface() is not None:
                    image = image.convert_alpha()
                models.append(image)
            except pygame.error:
                continue
        return models

    def _get_random_br_image(self, lane: Lane) -> pygame.Surface | None:
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
                        ):
                            overlap = True
                            break
                    if overlap:
                        break
            if not overlap:
                break

        br = BRHazard(spawn_x, spawn_y, br_width, br_height, image=br_image)
        self.brs.add(br)

    def update(self, map_speed: int, is_braking: bool = False) -> None:
        if not is_braking:
            self.timer += 1
            if self.timer >= self.spawn_frequency:
                self.timer = 0
                if len(self.brs) < self.max_brs:
                    self._spawn_br()

        self.brs.update(map_speed, self.road.height, is_braking)

    def draw(self, surface: pygame.Surface) -> None:
        self.brs.draw(surface)

