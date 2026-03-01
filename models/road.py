import random
from pathlib import Path

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
