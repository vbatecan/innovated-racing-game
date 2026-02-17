import random
from dataclasses import dataclass

import pygame

import config


@dataclass(frozen=True)
class Lane:
    index: int
    left: int
    right: int

    @property
    def width(self) -> int:
        return max(1, self.right - self.left)


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, width: int, height: int, speed: int):
        """
        Create a rectangular obstacle sprite.

        Positions the obstacle at the given coordinates and assigns its vertical
        scroll speed.
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
        """
        self.rect.y += self.speed
        if self.rect.y > 2000:
            self.kill()


class Road:
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
        self.lane_count = max(
            config.MIN_LANE_COUNT, min(int(lane_count), config.MAX_LANE_COUNT)
        )

    def lane_width(self) -> float:
        return self.width / float(self.lane_count)

    def get_lane(self, lane_index: int) -> Lane:
        clamped_index = max(0, min(lane_index, self.lane_count - 1))
        lane_w = self.lane_width()
        left = int(self.x + clamped_index * lane_w)
        right = int(self.x + (clamped_index + 1) * lane_w)
        if clamped_index == self.lane_count - 1:
            right = self.x + self.width
        return Lane(index=clamped_index, left=left, right=right)

    def random_lane(self) -> Lane:
        return self.get_lane(random.randrange(self.lane_count))

    def random_lane_spawn_x(self, obstacle_width: int, min_padding: int = 10) -> int:
        lane = self.random_lane()
        lane_padding = min(min_padding, max(0, (lane.width - obstacle_width) // 2))
        max_left = lane.right - obstacle_width - lane_padding
        min_left = lane.left + lane_padding
        if max_left <= min_left:
            return lane.left + max(0, (lane.width - obstacle_width) // 2)
        return random.randint(min_left, max_left)

    def draw_background(self, surface: pygame.Surface) -> None:
        surface.fill(self.BG_COLOR)
        pygame.draw.rect(surface, self.ROAD_COLOR, (self.x, 0, self.width, self.height))

    def draw_lane_markers(self, surface: pygame.Surface, scroll_y: int) -> None:
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
        pygame.draw.line(surface, self.LINE_COLOR, (self.x, 0), (self.x, self.height), 5)
        pygame.draw.line(
            surface,
            self.LINE_COLOR,
            (self.x + self.width, 0),
            (self.x + self.width, self.height),
            5,
        )

    def get_borders(self) -> tuple[int, int]:
        return self.x, self.x + self.width


class ObstacleManager:
    def __init__(
        self,
        road: Road,
        spawn_frequency: int = 30,
        max_obstacles: int = 5,
        obstacle_size: tuple[int, int] = (50, 50),
    ):
        self.road = road
        self.max_obstacles = max_obstacles
        self.obstacle_width, self.obstacle_height = obstacle_size
        self.obstacles = pygame.sprite.Group()
        self.timer = 0
        self.spawn_frequency = max(1, int(spawn_frequency))

    def set_spawn_frequency(self, frequency: int) -> None:
        self.spawn_frequency = max(1, int(frequency))

    def _spawn_obstacle(self, speed: int) -> None:
        spawn_x = self.road.random_lane_spawn_x(self.obstacle_width)
        spawn_y = -self.obstacle_height
        obstacle = Obstacle(
            spawn_x, spawn_y, self.obstacle_width, self.obstacle_height, speed
        )
        self.obstacles.add(obstacle)

    def update(self, speed: int) -> None:
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
        self.obstacles.draw(surface)


class Map:
    def __init__(self, window_size: dict[str, int], lane_count: int = config.LANE_COUNT):
        """
        Initialize the scrolling road and obstacle system.

        Manages the road rendering, lane configuration, and obstacle lifecycle.
        """
        self.width = window_size["width"]
        self.height = window_size["height"]
        self.speed = 1
        self.scroll_y = 0

        self.road = Road(window_size, config.ROAD_SIZE["width"], lane_count=lane_count)
        self.obstacle_manager = ObstacleManager(self.road)

    @property
    def obstacles(self) -> pygame.sprite.Group:
        return self.obstacle_manager.obstacles

    @property
    def obstacle_frequency(self) -> int:
        return self.obstacle_manager.spawn_frequency

    @obstacle_frequency.setter
    def obstacle_frequency(self, value: int) -> None:
        self.obstacle_manager.set_spawn_frequency(value)

    def set_lane_count(self, lane_count: int) -> None:
        self.road.set_lane_count(lane_count)

    def update(self) -> None:
        """
        Advance the road scroll and update obstacles.
        """
        self.scroll_y += self.speed
        if self.scroll_y >= self.road.total_marker_segment:
            self.scroll_y -= self.road.total_marker_segment
        self.obstacle_manager.update(self.speed)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the road, lane markers, and obstacles to the surface.
        """
        self.road.draw_background(surface)
        self.road.draw_lane_markers(surface, self.scroll_y)
        self.obstacle_manager.draw(surface)
        self.road.draw_borders(surface)

    def get_road_borders(self) -> tuple[int, int]:
        """
        Return the left and right x-coordinates of the road.
        """
        return self.road.get_borders()
