import random
from pathlib import Path

import pygame

import config
from models.lane import Lane
from models.obstacle import Obstacle
from models.road import Road


class ObstacleManager:
    """Spawn, update, and render road obstacles."""

    def __init__(
            self,
            road: Road,
            spawn_frequency: int = 60,
            max_obstacles: int = 3,
            obstacle_size: tuple[int, int] = (30, 30),
    ):
        """
        Initialize obstacle spawning limits and sprite storage.

        Args:
            road (Road): Road geometry used for lane-based spawns.
            spawn_frequency (int): Frames between spawn attempts.
            max_obstacles (int): Maximum simultaneous active obstacles.
            obstacle_size (tuple[int, int]): Obstacle `(width, height)` in pixels.
        """
        self.road = road
        self.max_obstacles = max_obstacles
        self.obstacle_width, self.obstacle_height = obstacle_size
        self.obstacles = pygame.sprite.Group()
        self.timer = 0
        self.spawn_frequency = max(1, int(spawn_frequency))
        self.model_dir = Path("resources/models")
        self.model_scale_cache: dict[tuple[int, int], pygame.Surface] = {}
        self.obstacle_models = self._load_obstacle_models()
        self.blocking_groups: list[pygame.sprite.Group] = []

    def set_blocking_groups(self, groups: list[pygame.sprite.Group]) -> None:
        """Set sprite groups that obstacle spawns must avoid overlapping."""
        self.blocking_groups = groups

    def _load_obstacle_models(self) -> list[pygame.Surface]:
        """Load top-level obstacle model PNGs from resources/models."""
        if not self.model_dir.exists():
            return []

        models: list[pygame.Surface] = []
        for model_path in sorted(self.model_dir.glob("*.png")):
            try:
                image = pygame.image.load(str(model_path))
                if pygame.display.get_surface() is not None:
                    image = image.convert_alpha()
                models.append(image)
            except pygame.error:
                continue
        return models

    def _get_random_obstacle_image(self, lane: Lane) -> pygame.Surface | None:
        """
        Return a random obstacle model scaled to fit the target lane.

        Args:
            lane (Lane): Target lane where the obstacle will spawn.

        Returns:
            pygame.Surface | None: Scaled model image, or None if unavailable.
        """
        if not self.obstacle_models:
            return None

        model_index = random.randrange(len(self.obstacle_models))
        source = self.obstacle_models[model_index]

        lane_fit_width = max(1, lane.width - 20)
        target_width = min(
            lane_fit_width, int(lane.width * config.TRAFFIC_LANE_WIDTH_RATIO)
        )
        target_width = max(config.TRAFFIC_MIN_SIZE, target_width)
        target_width = min(
            target_width,
            max(
                config.TRAFFIC_MIN_SIZE,
                int(source.get_width() * config.TRAFFIC_MAX_SOURCE_SCALE),
            ),
        )

        cache_key = (model_index, target_width)
        cached = self.model_scale_cache.get(cache_key)
        if cached is not None:
            return cached

        source_width, source_height = source.get_size()
        scaled_height = max(
            config.TRAFFIC_MIN_SIZE, int(source_height * (target_width / source_width))
        )
        scaled = pygame.transform.smoothscale(source, (target_width, scaled_height))
        self.model_scale_cache[cache_key] = scaled
        return scaled

    @staticmethod
    def _lane_spawn_x(lane: Lane, obstacle_width: int, min_padding: int = 10) -> int:
        """Return a valid spawn X for an obstacle inside the specified lane."""
        lane_padding = min(min_padding, max(0, (lane.width - obstacle_width) // 2))
        max_left = lane.right - obstacle_width - lane_padding
        min_left = lane.left + lane_padding
        if max_left <= min_left:
            return lane.left + max(0, (lane.width - obstacle_width) // 2)
        return random.randint(min_left, max_left)

    def set_spawn_frequency(self, frequency: int) -> None:
        """
        Set obstacle spawn interval in frames, clamped to at least one frame.

        Args:
            frequency (int): Frames between spawn attempts.

        Returns:
            None: Updates the internal spawn timer interval.
        """
        self.spawn_frequency = max(1, int(frequency))

    @staticmethod
    def _sample_traffic_speed(player_speed: int) -> float:
        """
        Generate a per-vehicle traffic speed in world units.

        The spawned vehicle initially approaches the player by at least one
        pixel/frame so traffic always appears active on-screen.
        """
        _ = player_speed
        return random.uniform(0.5, 2.5)

    def _spawn_obstacle(self, speed: int) -> None:
        """
        Create one obstacle at the top of a random lane.

        Args:
            speed (int): Current player/map speed used to derive traffic speed.

        Returns:
            None: Adds a new obstacle sprite to the managed group.
        """
        # Avoid spawning in a lane that already has an obstacle near the top
        max_attempts = 10
        for _ in range(max_attempts):
            lane = self.road.get_lane(self.road.lane_count // 2)
            obstacle_image = self._get_random_obstacle_image(lane)
            obstacle_width = self.obstacle_width
            obstacle_height = self.obstacle_height
            if obstacle_image is not None:
                obstacle_width = obstacle_image.get_width()
                obstacle_height = obstacle_image.get_height()

            spawn_x = self._lane_spawn_x(lane, obstacle_width)
            # Spawn just above the screen for smooth entry
            spawn_y = -obstacle_height - random.randint(0, 100)

            # Check for overlap with existing obstacles in the same lane
            overlap = False
            for obs in self.obstacles:
                # Check if obs is in the same lane (by x overlap)
                if (
                        obs.rect.left < spawn_x + obstacle_width
                        and obs.rect.right > spawn_x
                        and abs(obs.rect.y - spawn_y) < obstacle_height * 3
                ):
                    overlap = True
                    break

            if not overlap:
                spawn_rect = pygame.Rect(
                    spawn_x, spawn_y, obstacle_width, obstacle_height
                )
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
        else:
            # If all attempts failed, just pick a random lane
            lane = self.road.get_lane(self.road.lane_count // 2)
            obstacle_image = self._get_random_obstacle_image(lane)
            obstacle_width = self.obstacle_width
            obstacle_height = self.obstacle_height
            if obstacle_image is not None:
                obstacle_width = obstacle_image.get_width()
                obstacle_height = obstacle_image.get_height()
            spawn_x = self._lane_spawn_x(lane, obstacle_width)
            # Spawn just above the screen for smooth entry
            spawn_y = -obstacle_height - random.randint(0, 100)

        traffic_speed = self._sample_traffic_speed(speed)
        obstacle = Obstacle(
            spawn_x,
            spawn_y,
            obstacle_width,
            obstacle_height,
            speed,
            image=obstacle_image,
            traffic_speed=traffic_speed,
        )
        self.obstacles.add(obstacle)

    def update(self, speed: int, is_braking: bool = False) -> None:
        """
        Advance timers, spawn obstacles, and update active obstacle movement.

        Args:
            speed (int): Current map speed applied to all active obstacles.

        Returns:
            None: Mutates obstacle state and sprite group membership.
        """
        self.timer += 1
        if not is_braking and self.timer >= self.spawn_frequency:
            self.timer = 0
            if len(self.obstacles) < self.max_obstacles:
                self._spawn_obstacle(speed)

        self.obstacles.update(speed, self.road.height, is_braking)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw all active obstacle sprites.

        Args:
            surface (pygame.Surface): Target drawing surface.

        Returns:
            None: Draws directly to `surface`.
        """
        self.obstacles.draw(surface)
