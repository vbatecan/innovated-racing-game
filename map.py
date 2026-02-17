import random
from dataclasses import dataclass

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
    def __init__(self, x: int, y: int, width: int, height: int, speed: int):
        """
        Create a rectangular obstacle sprite.

        Args:
            x (int): Initial X position (left) of the obstacle sprite.
            y (int): Initial Y position (top) of the obstacle sprite.
            width (int): Obstacle width in pixels.
            height (int): Obstacle height in pixels.
            speed (int): Vertical movement speed per frame.
        """
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill((255, 50, 50))
        pygame.draw.rect(self.image, (255, 255, 0), (0, 0, width, 10))

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = speed

    def update(self) -> None:
        """
        Move the obstacle downward and delete if off-screen.

        Returns:
            None: Updates sprite position in place.
        """
        self.rect.y += self.speed
        if self.rect.y > 2000:
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

    def draw_background(self, surface: pygame.Surface) -> None:
        """
        Render the background and asphalt road body.

        Args:
            surface (pygame.Surface): Target drawing surface.

        Returns:
            None: Draws directly to `surface`.
        """
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
        spawn_frequency: int = 30,
        max_obstacles: int = 5,
        obstacle_size: tuple[int, int] = (50, 50),
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

    def set_spawn_frequency(self, frequency: int) -> None:
        """
        Set obstacle spawn interval in frames, clamped to at least one frame.

        Args:
            frequency (int): Frames between spawn attempts.

        Returns:
            None: Updates the internal spawn timer interval.
        """
        self.spawn_frequency = max(1, int(frequency))

    def _spawn_obstacle(self, speed: int) -> None:
        """
        Create one obstacle at the top of a random lane.

        Args:
            speed (int): Initial vertical speed for the spawned obstacle.

        Returns:
            None: Adds a new obstacle sprite to the managed group.
        """
        spawn_x = self.road.random_lane_spawn_x(self.obstacle_width)
        spawn_y = -self.obstacle_height
        obstacle = Obstacle(
            spawn_x, spawn_y, self.obstacle_width, self.obstacle_height, speed
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

        for obstacle in self.obstacles:
            obstacle.speed = speed
        self.obstacles.update()

        for obstacle in tuple(self.obstacles):
            if obstacle.rect.y > self.road.height:
                obstacle.kill()

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

    def update(self) -> None:
        """
        Advance the road scroll and update obstacles.

        Returns:
            None: Mutates map scroll and obstacle state.
        """
        self.scroll_y += self.speed
        if self.scroll_y >= self.road.total_marker_segment:
            self.scroll_y -= self.road.total_marker_segment
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
