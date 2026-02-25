import random
from dataclasses import dataclass
from pathlib import Path

import pygame

import config


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
        # Always create the image at the correct size for the obstacle
        if image is None:
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
            self.image.fill((255, 50, 50))
            pygame.draw.rect(self.image, (255, 255, 0), (0, 0, width, 10))
        else:
            # Defensive: ensure the image is the correct size for the rect
            if image.get_width() != width or image.get_height() != height:
                self.image = pygame.transform.smoothscale(image, (width, height))
            else:
                self.image = image

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        # Always update the mask after scaling
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = float(speed)
        # Per-vehicle base approach speed so traffic always moves on-screen.
        self.traffic_speed = max(0.5, float(traffic_speed))
        self._y_pos = float(y)

    def update(self, player_speed: float, screen_height: int) -> None:
        """
        Move the obstacle using relative speed and delete if off-screen.

        The traffic vehicle's screen speed is computed from:
        `player_speed - traffic_speed`.

        Returns:
            None: Updates sprite position in place.
        """
        # Blend player speed with per-vehicle traffic speed so traffic remains active
        # even at low player speed and scales up as gameplay gets faster.
        blended_speed = self.traffic_speed + (0.2 * float(player_speed))
        self.speed = max(1.0, min(24.0, blended_speed))
        self._y_pos += self.speed
        self.rect.y = int(self._y_pos)

        if (
            self.rect.top > screen_height + self.rect.height
            or self.rect.bottom < -self.rect.height
        ):
            self.kill()


class Road:
    """Road geometry and rendering for lane-based driving."""

    BG_COLOR = (20, 20, 30)
    ROAD_COLOR = (30, 30, 40)
    LINE_COLOR = (0, 255, 255)
    MARKER_COLOR = (255, 255, 0)

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
        
        # Load background images for map switching
        self.bg_images = self._load_background_images()
        self.bg_y_offset = 0
        self.current_map_index = 0

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
            Path("resources/models/maps/city_road1.png"),
            Path("resources/models/maps/highway.png"),
        ]
        
        for map_path in map_paths:
            if map_path.exists():
                try:
                    image = pygame.image.load(str(map_path))
                    # Scale image to fit window size
                    scaled_image = pygame.transform.scale(image, (self.window_width, self.height))
                    if pygame.display.get_surface() is not None:
                        scaled_image = scaled_image.convert()
                    bg_images.append(scaled_image)
                except pygame.error:
                    pass
        
        return bg_images
    
    def update_background_scroll(self, speed: int) -> None:
        """
        Update the background image scroll offset.
        
        Args:
            speed (int): Current map speed.
        """
        if self.bg_images:
            self.bg_y_offset += speed
            # Loop the background when it scrolls past its height
            if self.bg_y_offset >= self.height:
                self.bg_y_offset -= self.height
    
    def set_map_by_score(self, score: int) -> None:
        """
        Switch background map based on score (every 5000 points).
        
        Args:
            score (int): Current game score.
        """
        if not self.bg_images:
            return
        
        # Calculate which map to show based on score (switch every 5000 points)
        map_index = (score // 5000) % len(self.bg_images)
        self.current_map_index = map_index

    def draw_background(self, surface: pygame.Surface) -> None:
        """
        Render the background and asphalt road body.

        Args:
            surface (pygame.Surface): Target drawing surface.

        Returns:
            None: Draws directly to `surface`.
        """
        # If background images are loaded, draw them with scrolling
        if self.bg_images and 0 <= self.current_map_index < len(self.bg_images):
            current_bg = self.bg_images[self.current_map_index]
            # Draw two copies of the background for seamless scrolling
            y1 = self.bg_y_offset
            y2 = self.bg_y_offset - self.height
            surface.blit(current_bg, (0, y1))
            surface.blit(current_bg, (0, y2))
        else:
            # Fallback to solid colors if no images loaded
            surface.fill(self.BG_COLOR)
            pygame.draw.rect(surface, self.ROAD_COLOR, (self.x, 0, self.width, self.height))

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
        pygame.draw.line(surface, self.LINE_COLOR, (self.x, 0), (self.x, self.height), 5)
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
        obstacle_size: tuple[int, int] = (40, 40),
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

        lane_fit_width = max(1, lane.width - 24)
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
            lane = self.road.random_lane()
            obstacle_image = self._get_random_obstacle_image(lane)
            obstacle_width = self.obstacle_width
            obstacle_height = self.obstacle_height
            if obstacle_image is not None:
                obstacle_width = obstacle_image.get_width()
                obstacle_height = obstacle_image.get_height()

            spawn_x = self._lane_spawn_x(lane, obstacle_width)
            # Spawn in the middle portion of the road (30-60% from top)
            spawn_y = random.randint(
                int(self.road.height * 0.3),
                int(self.road.height * 0.6)
            )

            # Check for overlap with existing obstacles in the same lane
            overlap = False
            for obs in self.obstacles:
                # Check if obs is in the same lane (by x overlap)
                if (obs.rect.left < spawn_x + obstacle_width and
                    obs.rect.right > spawn_x and
                    abs(obs.rect.y - spawn_y) < obstacle_height * 2):
                    overlap = True
                    break
            if not overlap:
                break
        else:
            # If all attempts failed, just pick a random lane
            lane = self.road.random_lane()
            obstacle_image = self._get_random_obstacle_image(lane)
            obstacle_width = self.obstacle_width
            obstacle_height = self.obstacle_height
            if obstacle_image is not None:
                obstacle_width = obstacle_image.get_width()
                obstacle_height = obstacle_image.get_height()
            spawn_x = self._lane_spawn_x(lane, obstacle_width)
            # Spawn in the middle portion of the road (30-60% from top)
            spawn_y = random.randint(
                int(self.road.height * 0.3),
                int(self.road.height * 0.6)
            )

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
        Advance timers, spawn obstacles, and update active obstacle movement.

        Args:
            speed (int): Current map speed applied to all active obstacles.

        Returns:
            None: Mutates obstacle state and sprite group membership.
        """
        self.timer += 1
        if self.timer >= self.spawn_frequency:
            self.timer = 0
            if len(self.obstacles) < self.max_obstacles:
                self._spawn_obstacle(speed)

        self.obstacles.update(speed, self.road.height)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw all active obstacle sprites.

        Args:
            surface (pygame.Surface): Target drawing surface.

        Returns:
            None: Draws directly to `surface`.
        """
        self.obstacles.draw(surface)


class Map:
    def __init__(self, window_size: dict[str, int], lane_count: int = config.LANE_COUNT):
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

    def update(self) -> None:
        """
        Advance the road scroll and update obstacles.

        Returns:
            None: Mutates map scroll and obstacle state.
        """
        self.scroll_y += self.speed
        if self.scroll_y >= self.road.total_marker_segment:
            self.scroll_y -= self.road.total_marker_segment
        self.road.update_background_scroll(self.speed)
        self.obstacle_manager.update(self.speed)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the road, lane markers, and obstacles to the surface.

        Args:
            surface (pygame.Surface): Target drawing surface.

        Returns:
            None: Draws directly to `surface`.
        """
        self.road.draw_background(surface)
        self.road.draw_lane_markers(surface, self.scroll_y)
        self.obstacle_manager.draw(surface)
        self.road.draw_borders(surface)

    def get_road_borders(self) -> tuple[int, int]:
        """
        Return the left and right x-coordinates of the road.

        Returns:
            tuple[int, int]: `(left_x, right_x)` road boundaries.
        """
        return self.road.get_borders()
