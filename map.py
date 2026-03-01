import random
from dataclasses import dataclass
from pathlib import Path

import config
import pygame

try:
    import numpy as np
except ImportError:
    np = None


@dataclass(frozen=True)
class Lane:
    """Immutable lane segment defined by horizontal boundaries."""

    index: int
    left: int
    right: int

    @property
    def width(self) -> int:
        """Return the pixel width of the lane."""
        return max(1, self.right - self.left)


class Obstacle(pygame.sprite.Sprite):
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        speed: int,
        image: pygame.Surface | None = None,
        traffic_speed: float = 0.0,
    ):
        """
        Create an obstacle sprite.

        Args:
            x (int): Initial X position (left) of the obstacle sprite.
            y (int): Initial Y position (top) of the obstacle sprite.
            width (int): Obstacle width in pixels.
            height (int): Obstacle height in pixels.
            speed (int): Initial vertical movement speed per frame.
            image (pygame.Surface | None): Optional pre-built obstacle image.
            traffic_speed (float): World traffic speed used for relative movement.
        """
        super().__init__()
        if image is None:
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
            self.image.fill((255, 50, 50))
            pygame.draw.rect(self.image, (255, 255, 0), (0, 0, width, 10))
        else:
            if image.get_width() != width or image.get_height() != height:
                self.image = pygame.transform.smoothscale(image, (width, height))
            else:
                self.image = image

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = float(speed)
        self.traffic_speed = max(0.5, float(traffic_speed))
        self._y_pos = float(y)
        self.direction_factor = 1.0

    def update(
        self,
        player_speed: float,
        screen_height: int,
        is_braking: bool = False,
    ) -> None:
        """
        Move the obstacle using relative speed and delete if off-screen.

        The traffic vehicle's screen speed is computed from:
        `player_speed - traffic_speed`.

        Returns:
            None: Updates sprite position in place.
        """
        blended_speed = self.traffic_speed + (0.2 * float(player_speed))
        self.speed = max(1.0, min(24.0, blended_speed))
        target_direction = -1.0 if is_braking else 1.0
        self.direction_factor += (target_direction - self.direction_factor) * 0.18
        self._y_pos += self.speed * self.direction_factor
        self.rect.y = int(self._y_pos)

        if (
            self.rect.top > screen_height + self.rect.height
            or self.rect.bottom < -self.rect.height
        ):
            self.kill()


class Crack(pygame.sprite.Sprite):
    """Road crack hazard that scrolls toward the player."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        image: pygame.Surface | None = None,
    ):
        super().__init__()
        if image is None:
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.ellipse(self.image, (35, 35, 35), (0, 0, width, height))
        else:
            if image.get_width() != width or image.get_height() != height:
                self.image = pygame.transform.smoothscale(image, (width, height))
            else:
                self.image = image

        self.rect = self.image.get_rect(topleft=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self._y_pos = float(y)

    def update(
        self, map_speed: int, screen_height: int, is_braking: bool = False
    ) -> None:
        """Move crack downward with map scroll and remove when off-screen."""
        if is_braking:
            return

        self._y_pos += max(1.0, float(map_speed))
        self.rect.y = int(self._y_pos)
        if self.rect.top > screen_height + self.rect.height:
            self.kill()


class BRHazard(pygame.sprite.Sprite):
    """BR hazard that scrolls toward the player."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        image: pygame.Surface | None = None,
    ):
        super().__init__()
        if image is None:
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(
                self.image, (200, 30, 30), (0, 0, width, height), border_radius=5
            )
        else:
            if image.get_width() != width or image.get_height() != height:
                self.image = pygame.transform.smoothscale(image, (width, height))
            else:
                self.image = image

        self.rect = self.image.get_rect(topleft=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self._y_pos = float(y)

    def update(
        self, map_speed: int, screen_height: int, is_braking: bool = False
    ) -> None:
        if is_braking:
            return

        self._y_pos += max(1.0, float(map_speed))
        self.rect.y = int(self._y_pos)
        if self.rect.top > screen_height + self.rect.height:
            self.kill()


class Road:
    """Road geometry and rendering for lane-based driving."""

    BG_COLOR = (20, 20, 30)
    ROAD_COLOR = (30, 30, 40)
    LINE_COLOR = (0, 255, 255)
    MARKER_COLOR = (255, 255, 0)
    MAP_BLEND_WINDOW = 0.35

    def __init__(
        self,
        window_size: dict[str, int],
        road_width: int,
        lane_count: int,
        marker_height: int = 50,
        marker_gap: int = 50,
        marker_width: int = 10,
    ):
        """
        Build a centered road model with configurable lane and marker sizes.

        Args:
            window_size (dict[str, int]): Screen dimensions with `width` and `height`.
            road_width (int): Total road width in pixels.
            lane_count (int): Initial number of lanes.
            marker_height (int): Height of each dashed lane marker.
            marker_gap (int): Vertical gap between lane markers.
            marker_width (int): Width of each lane marker.
        """
        self.window_width = window_size["width"]
        self.height = window_size["height"]
        self.width = road_width
        self.x = (self.window_width - self.width) // 2

        self.marker_height = marker_height
        self.marker_gap = marker_gap
        self.marker_width = marker_width
        self.total_marker_segment = self.marker_height + self.marker_gap

        self.lane_count = 1
        self.set_lane_count(lane_count)

        self.bg_images = self._load_background_images()
        self.bg_y_offset = 0
        self.current_map_index = 0
        self.next_map_index = 0
        self.transition_alpha = 0

    def set_lane_count(self, lane_count: int) -> None:
        """
        Clamp and apply the active number of lanes.

        Args:
            lane_count (int): Requested lane count.

        Returns:
            None: Mutates the current road lane configuration.
        """
        self.lane_count = max(
            config.MIN_LANE_COUNT, min(int(lane_count), config.MAX_LANE_COUNT)
        )

    def lane_width(self) -> float:
        """
        Return the width of one lane in pixels.

        Returns:
            float: Width of a single lane.
        """
        return self.width / float(self.lane_count)

    def get_lane(self, lane_index: int) -> Lane:
        """
        Return lane boundaries for a specific lane index.

        Args:
            lane_index (int): Zero-based lane index.

        Returns:
            Lane: Lane object with clamped index and boundaries.
        """
        clamped_index = max(0, min(lane_index, self.lane_count - 1))
        lane_w = self.lane_width()
        left = int(self.x + clamped_index * lane_w)
        right = int(self.x + (clamped_index + 1) * lane_w)
        if clamped_index == self.lane_count - 1:
            right = self.x + self.width
        return Lane(index=clamped_index, left=left, right=right)

    def random_lane(self) -> Lane:
        """
        Pick and return a random lane.

        Returns:
            Lane: Randomly selected lane.
        """
        return self.get_lane(random.randrange(self.lane_count))

    def random_lane_spawn_x(self, obstacle_width: int, min_padding: int = 10) -> int:
        """
        Compute a valid obstacle spawn X within a random lane.

        Args:
            obstacle_width (int): Width of the obstacle being spawned.
            min_padding (int): Minimum horizontal inset from lane boundaries.

        Returns:
            int: Valid obstacle X position inside the chosen lane.
        """
        lane = self.random_lane()
        lane_padding = min(min_padding, max(0, (lane.width - obstacle_width) // 2))
        max_left = lane.right - obstacle_width - lane_padding
        min_left = lane.left + lane_padding
        if max_left <= min_left:
            return lane.left + max(0, (lane.width - obstacle_width) // 2)
        return random.randint(min_left, max_left)

    def _load_background_images(self) -> list[pygame.Surface]:
        """
        Load background map images from resources/models/maps/.

        Returns:
            list[pygame.Surface]: List of loaded and scaled background images.
        """
        bg_images = []
        map_paths = [
            Path("resources/models/maps/city_roadfinal.png"),
            Path("resources/models/maps/desert.png"),
            Path("resources/models/maps/highway.png"),
        ]

        for map_path in map_paths:
            if map_path.exists():
                try:
                    image = pygame.image.load(str(map_path))
                    scaled_image = pygame.transform.scale(
                        image, (self.window_width, self.height)
                    )
                    scaled_image = self._suppress_road_markings(scaled_image)
                    if pygame.display.get_surface() is not None:
                        scaled_image = scaled_image.convert()
                    bg_images.append(scaled_image)
                except pygame.error:
                    pass

        return bg_images

    @staticmethod
    def _suppress_road_markings(image: pygame.Surface) -> pygame.Surface:
        """Reduce bright painted lane markings baked into map textures."""
        if np is None:
            return image

        rgb = pygame.surfarray.array3d(image)

        white_lines = (rgb[:, :, 0] > 180) & (rgb[:, :, 1] > 180) & (rgb[:, :, 2] > 180)
        yellow_lines = (rgb[:, :, 0] > 165) & (rgb[:, :, 1] > 145) & (rgb[:, :, 2] < 150)
        cyan_lines = (rgb[:, :, 0] < 140) & (rgb[:, :, 1] > 155) & (rgb[:, :, 2] > 165)
        lane_mask = white_lines | yellow_lines | cyan_lines

        if lane_mask.any():
            rgb[lane_mask] = (62, 64, 70)

        return pygame.surfarray.make_surface(rgb)

    def update_background_scroll(self, speed: int) -> None:
        """
        Update the background image scroll offset.

        Args:
            speed (int): Current map speed.
        """
        if self.bg_images:
            self.bg_y_offset += speed
            if self.bg_y_offset >= self.height:
                self.bg_y_offset -= self.height

    def set_map_by_score(self, score: int) -> None:
        """
        Set active/background blend maps based on score progression.

        Args:
            score (int): Current game score.
        """
        if not self.bg_images:
            return

        switch_score = max(1, int(config.MAP_SWITCH_SCORE))
        map_count = len(self.bg_images)
        map_index = (score // switch_score) % map_count
        cycle_progress = (score % switch_score) / float(switch_score)
        blend_window = max(0.05, min(self.MAP_BLEND_WINDOW, 0.95))
        blend_start = 1.0 - blend_window

        self.current_map_index = map_index
        if cycle_progress >= blend_start:
            blend_progress = (cycle_progress - blend_start) / blend_window
            self.next_map_index = (map_index + 1) % map_count
            self.transition_alpha = int(max(0.0, min(1.0, blend_progress)) * 255)
        else:
            self.next_map_index = map_index
            self.transition_alpha = 0

    def draw_background(self, surface: pygame.Surface) -> None:
        """
        Render the background and asphalt road body.

        Args:
            surface (pygame.Surface): Target drawing surface.

        Returns:
            None: Draws directly to `surface`.
        """
        if self.bg_images and 0 <= self.current_map_index < len(self.bg_images):
            current_bg = self.bg_images[self.current_map_index]
            y1 = self.bg_y_offset
            y2 = self.bg_y_offset - self.height
            surface.blit(current_bg, (0, y1))
            surface.blit(current_bg, (0, y2))

            if (
                self.transition_alpha > 0
                and 0 <= self.next_map_index < len(self.bg_images)
                and self.next_map_index != self.current_map_index
            ):
                next_bg = self.bg_images[self.next_map_index]
                next_bg_blended = next_bg.copy()
                next_bg_blended.set_alpha(self.transition_alpha)
                surface.blit(next_bg_blended, (0, y1))
                surface.blit(next_bg_blended, (0, y2))
        else:
            surface.fill(self.BG_COLOR)
            pygame.draw.rect(
                surface, self.ROAD_COLOR, (self.x, 0, self.width, self.height)
            )

    def draw_lane_markers(self, surface: pygame.Surface, scroll_y: int) -> None:
        """
        Draw animated dashed lane separators based on scroll offset.

        Args:
            surface (pygame.Surface): Target drawing surface.
            scroll_y (int): Current vertical scroll offset for animation.

        Returns:
            None: Draws directly to `surface`.
        """
        start_y = -self.total_marker_segment + scroll_y
        for lane_boundary in range(1, self.lane_count):
            lane_x = int(self.x + lane_boundary * self.lane_width())
            marker_x = lane_x - self.marker_width // 2
            marker_y = start_y
            while marker_y < self.height:
                pygame.draw.rect(
                    surface,
                    self.MARKER_COLOR,
                    (marker_x, marker_y, self.marker_width, self.marker_height),
                )
                marker_y += self.total_marker_segment

    def draw_borders(self, surface: pygame.Surface) -> None:
        """
        Draw left and right road boundary lines.

        Args:
            surface (pygame.Surface): Target drawing surface.

        Returns:
            None: Draws directly to `surface`.
        """
        pygame.draw.line(
            surface, self.LINE_COLOR, (self.x, 0), (self.x, self.height), 5
        )
        pygame.draw.line(
            surface,
            self.LINE_COLOR,
            (self.x + self.width, 0),
            (self.x + self.width, self.height),
            5,
        )

    def get_borders(self) -> tuple[int, int]:
        """
        Return the absolute X positions of the road borders.

        Returns:
            tuple[int, int]: `(left_x, right_x)` border positions.
        """
        return self.x, self.x + self.width


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


class Map:
    def __init__(
        self, window_size: dict[str, int], lane_count: int = config.LANE_COUNT
    ):
        """
        Initialize the scrolling road and obstacle system.

        Args:
            window_size (dict[str, int]): Screen dimensions with `width` and `height`.
            lane_count (int): Initial lane count used by the road.
        """
        self.width = window_size["width"]
        self.height = window_size["height"]
        self.speed = 1
        self.scroll_y = 0
        self.current_score = 0

        self.road = Road(window_size, config.ROAD_SIZE["width"], lane_count=lane_count)
        self.obstacle_manager = ObstacleManager(self.road)
        self.crack_manager = CrackManager(self.road)
        self.br_manager = BRManager(self.road)
        self.obstacle_manager.set_blocking_groups([self.br_manager.brs])
        self.br_manager.set_blocking_groups([self.obstacle_manager.obstacles])

    @property
    def obstacles(self) -> pygame.sprite.Group:
        """
        Expose obstacle sprites for collision checks.

        Returns:
            pygame.sprite.Group: Active obstacle sprites.
        """
        return self.obstacle_manager.obstacles

    @property
    def obstacle_frequency(self) -> int:
        """
        Get the current obstacle spawn frequency in frames.

        Returns:
            int: Spawn interval in frames.
        """
        return self.obstacle_manager.spawn_frequency

    @obstacle_frequency.setter
    def obstacle_frequency(self, value: int) -> None:
        """
        Set obstacle spawn frequency in frames.

        Args:
            value (int): Frames between spawn attempts.

        Returns:
            None: Updates obstacle manager frequency.
        """
        self.obstacle_manager.set_spawn_frequency(value)

    @property
    def cracks(self) -> pygame.sprite.Group:
        """Expose crack hazard sprites for collision checks."""
        return self.crack_manager.cracks

    @property
    def brs(self) -> pygame.sprite.Group:
        """Expose BR hazard sprites for collision checks."""
        return self.br_manager.brs

    def set_lane_count(self, lane_count: int) -> None:
        """
        Apply a new runtime lane count to the road model.

        Args:
            lane_count (int): Requested lane count.

        Returns:
            None: Mutates road lane configuration.
        """
        self.road.set_lane_count(lane_count)

    def update_score(self, score: int) -> None:
        """
        Update the current score and switch maps if needed.

        Args:
            score (int): Current game score.
        """
        self.current_score = score
        self.road.set_map_by_score(score)

    def update(self, is_braking: bool = False) -> None:
        """
        Advance the road scroll and update obstacles.

        Returns:
            None: Mutates map scroll and obstacle state.
        """
        self.scroll_y += self.speed
        if self.scroll_y >= self.road.total_marker_segment:
            self.scroll_y -= self.road.total_marker_segment
        self.road.update_background_scroll(self.speed)
        self.crack_manager.update(self.speed, is_braking=is_braking)
        self.br_manager.update(self.speed, is_braking=is_braking)
        self.obstacle_manager.update(self.speed, is_braking=is_braking)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the map background and hazards to the surface.

        Args:
            surface (pygame.Surface): Target drawing surface.

        Returns:
            None: Draws directly to `surface`.
        """
        self.road.draw_background(surface)
        self.crack_manager.draw(surface)
        self.br_manager.draw(surface)
        self.obstacle_manager.draw(surface)

    def clear_hazards(self) -> None:
        """Remove all active hazards from the map."""
        self.obstacles.empty()
        self.cracks.empty()
        self.brs.empty()

    def get_road_borders(self) -> tuple[int, int]:
        """
        Return the left and right x-coordinates of the road.

        Returns:
            tuple[int, int]: `(left_x, right_x)` road boundaries.
        """
        return self.road.get_borders()
