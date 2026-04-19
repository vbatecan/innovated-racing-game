import random
from pathlib import Path

import pygame
from core.resource_manager import ResourceManager

import config
from models.lane import Lane
from models.obstacle import Obstacle
from models.road import Road


class ObstacleManager:
    """Manages the lifecycle of road obstacles including spawning, movement, and rendering."""

    def __init__(
        self,
        road: Road,
        spawn_frequency: int = 60,
        max_obstacles: int = 3,
        obstacle_size: tuple[int, int] = (30, 30),
    ):
        """
        Initialize the obstacle manager with spawning parameters and resource loading.

        Args:
            road: Road geometry defining lane boundaries for obstacle placement.
            spawn_frequency: Frames between spawn attempts. Clamped to minimum of 1.
            max_obstacles: Maximum number of simultaneous active obstacles allowed.
            obstacle_size: Default (width, height) in pixels when no model image is available.
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
        """
        Configure sprite groups that must not overlap with spawned obstacles.

        Args:
            groups: List of pygame sprite groups to check for collisions during spawn.
        """
        self.blocking_groups = groups

    def _load_obstacle_models(self) -> list[pygame.Surface]:
        """
        Load obstacle model images from resources/models directory.

        Excludes HP indicator images (full hp.png, hp minus 1.png, etc.) from loading.
        Images are converted to alpha format if a display surface is available.

        Returns:
            List of loaded pygame Surface objects, empty if directory missing or no valid images.
        """
        if not self.model_dir.exists():
            return []

        models: list[pygame.Surface] = []
        exclude_names = {"full hp.png", "hp minus 1.png", "hp minus 2.png", "deds.png"}
        for model_path in sorted(self.model_dir.glob("*.png")):
            if model_path.name in exclude_names:
                continue
            try:
                image = ResourceManager.load_image(str(model_path), convert_alpha=True)
                if pygame.display.get_surface() is not None:
                    image = image.convert_alpha()
                models.append(image)
            except pygame.error:
                continue
        return models

    def _get_random_obstacle_image(self, lane: Lane) -> pygame.Surface | None:
        """
        Select and scale a random obstacle model to fit within lane constraints.

        Applies width ratio limits and caching to avoid repeated scaling operations.
        Target width respects lane fit, minimum size constraints, and maximum source scale limits.

        Args:
            lane: Target lane determining width constraints for scaling.

        Returns:
            Scaled pygame Surface ready for use, or None if no models are loaded.
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
        """
        Calculate a random valid X coordinate for obstacle spawning within a lane.

        Ensures the obstacle fits within lane boundaries with minimum padding on both sides.
        Falls back to centered position if constraints cannot be satisfied.

        Args:
            lane: Lane defining the horizontal spawn boundaries.
            obstacle_width: Width of the obstacle being spawned.
            min_padding: Minimum pixels to maintain from lane edges.

        Returns:
            Integer X coordinate for the left edge of the obstacle.
        """
        lane_padding = min(min_padding, max(0, (lane.width - obstacle_width) // 2))
        max_left = lane.right - obstacle_width - lane_padding
        min_left = lane.left + lane_padding
        if max_left <= min_left:
            return lane.left + max(0, (lane.width - obstacle_width) // 2)
        return random.randint(min_left, max_left)

    def set_spawn_frequency(self, frequency: int) -> None:
        """
        Update the frame interval between obstacle spawn attempts.

        Args:
            frequency: Desired frames between spawns. Values below 1 are clamped to 1.
        """
        self.spawn_frequency = max(1, int(frequency))

    @staticmethod
    def _sample_traffic_speed(player_speed: int) -> float:
        """
        Generate a random traffic speed for approaching vehicles.

        Produces a speed value ensuring vehicles appear to approach the player,
        creating the visual effect of active on-screen traffic.

        Args:
            player_speed: Current player speed (unused in calculation but provided for API consistency).

        Returns:
            Random float between 0.5 and 2.5 representing traffic speed in world units.
        """
        _ = player_speed
        return random.uniform(0.5, 2.5)

    def _spawn_obstacle(self, speed: int) -> None:
        """
        Spawn a single obstacle at the top of a random valid lane.

        Attempts multiple times to find a non-overlapping position considering
        existing obstacles and blocking groups. Falls back to random lane after
        maximum attempts exceeded.

        Args:
            speed: Current player/map speed used to calculate traffic speed.
        """
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
            spawn_x = self.road.clamp_spawn_x_to_borders(spawn_x, obstacle_width)
            spawn_y = -obstacle_height - random.randint(0, 100)

            overlap = False
            for obs in self.obstacles:
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
                            and abs(blocked_sprite.rect.y - spawn_y) < obstacle_height * 4
                        ):
                            overlap = True
                            break
                    if overlap:
                        break
            if not overlap:
                break
        else:
            lane = self.road.get_lane(self.road.lane_count // 2)
            obstacle_image = self._get_random_obstacle_image(lane)
            obstacle_width = self.obstacle_width
            obstacle_height = self.obstacle_height
            if obstacle_image is not None:
                obstacle_width = obstacle_image.get_width()
                obstacle_height = obstacle_image.get_height()
            spawn_x = self._lane_spawn_x(lane, obstacle_width)
            spawn_x = self.road.clamp_spawn_x_to_borders(spawn_x, obstacle_width)
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

    def update(self, speed: int) -> None:
        """
        Advance the spawn timer, trigger obstacle spawning, and update all obstacles.

        Args:
            speed: Current map speed applied to obstacle movement and used for new spawns.
        """
        self.timer += 1
        if self.timer >= self.spawn_frequency:
            self.timer = 0
            if len(self.obstacles) < self.max_obstacles:
                self._spawn_obstacle(speed)

        self.obstacles.update(speed, self.road.height)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Render all active obstacles to the target surface.

        Args:
            surface: pygame Surface to draw obstacles onto.
        """
        self.obstacles.draw(surface)
