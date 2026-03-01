import random
from pathlib import Path
from typing import Any

import pygame

import config
from models.lane import Lane


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
        self.default_width = road_width
        self.default_x = (self.window_width - self.default_width) // 2
        self.width = self.default_width
        self.x = self.default_x

        self.marker_height = marker_height
        self.marker_gap = marker_gap
        self.marker_width = marker_width
        self.total_marker_segment = self.marker_height + self.marker_gap

        self.lane_count = 1
        self.set_lane_count(lane_count)

        # Load background images for map switching
        self.map_border_bounds: list[tuple[int, int]] = []
        self.bg_images = self._load_background_images()
        self.bg_y_offset = 0
        self.current_map_index = 0

        self._apply_map_borders(self.current_map_index)

    def _default_border_bounds(self) -> tuple[int, int]:
        return self.default_x, self.default_x + self.default_width

    def _resolve_map_border_bounds(self, map_name: str) -> tuple[int, int]:
        default_left, default_right = self._default_border_bounds()
        overrides: dict[str, dict[str, Any]] = getattr(
            config, "MAP_BORDER_OVERRIDES", {}
        )
        map_override = overrides.get(map_name, {})

        left = map_override.get("left")
        right = map_override.get("right")
        left_ratio = map_override.get("left_ratio")
        right_ratio = map_override.get("right_ratio")

        if left is None and left_ratio is not None:
            left = int(float(left_ratio) * self.window_width)
        if right is None and right_ratio is not None:
            right = int(float(right_ratio) * self.window_width)

        if left is None:
            left = default_left
        if right is None:
            right = default_right

        left = max(0, min(int(left), self.window_width - 1))
        right = max(1, min(int(right), self.window_width))
        if right <= left:
            return default_left, default_right

        return left, right

    def _apply_map_borders(self, map_index: int) -> None:
        if 0 <= map_index < len(self.map_border_bounds):
            left, right = self.map_border_bounds[map_index]
        else:
            left, right = self._default_border_bounds()

        self.x = left
        self.width = max(1, right - left)

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
        Compute valid obstacle spawn X within a random lane.

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
        self.map_border_bounds = []
        map_paths = [
            Path("resources/models/maps/city_roadfinal.png"),
            Path("resources/models/maps/desert.png"),
            Path("resources/models/maps/highway.png"),
        ]

        for map_path in map_paths:
            if map_path.exists():
                try:
                    image = pygame.image.load(str(map_path))
                    # Scale image to fit window size
                    scaled_image = pygame.transform.scale(
                        image, (self.window_width, self.height)
                    )
                    if pygame.display.get_surface() is not None:
                        scaled_image = scaled_image.convert()
                    bg_images.append(scaled_image)
                    self.map_border_bounds.append(
                        self._resolve_map_border_bounds(map_path.name)
                    )
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

        # Calculate which map to show based on the score (switch every n points)
        map_index = (score // config.MAP_SWITCH_SCORE) % len(self.bg_images)
        self.current_map_index = map_index
        self._apply_map_borders(map_index)

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
            pygame.draw.rect(
                surface, self.ROAD_COLOR, (self.x, 0, self.width, self.height)
            )

    def draw_borders(self, surface: pygame.Surface) -> None:
        """
        Draw left and right road boundary lines.

        Args:
            surface (pygame.Surface): Target drawing surface.

        Returns:
            None: Draws directly to `surface`.
        """

        # Kanan
        left_x, right_x = self.get_borders()
        pygame.draw.line(
            surface,
            self.LINE_COLOR,
            (left_x, 0),
            (left_x, self.height),
            config.ROAD_LINE_BORDER_WIDTH,
        )

        # Kaliwa
        pygame.draw.line(
            surface,
            self.LINE_COLOR,
            (right_x, 0),
            (right_x, self.height),
            config.ROAD_LINE_BORDER_WIDTH,
        )

    def get_borders(self) -> tuple[int, int]:
        """
        Return the absolute X positions of the road borders.

        Returns:
            tuple[int, int]: `(left_x, right_x)` border positions.
        """
        if 0 <= self.current_map_index < len(self.map_border_bounds):
            return self.map_border_bounds[self.current_map_index]
        return self._default_border_bounds()
