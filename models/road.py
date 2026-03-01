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
        self.transition_from_map_index = 0
        self.transition_to_map_index = 0
        self.transition_progress_px = 0.0
        self.is_transitioning = False
        self.active_border_left = self.default_x
        self.active_border_right = self.default_x + self.default_width

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

        self.active_border_left = left
        self.active_border_right = right

    def _get_map_borders(self, map_index: int) -> tuple[int, int]:
        if 0 <= map_index < len(self.map_border_bounds):
            return self.map_border_bounds[map_index]
        return self._default_border_bounds()

    def _apply_interpolated_borders(self, progress: float) -> None:
        from_left, from_right = self._get_map_borders(self.transition_from_map_index)
        to_left, to_right = self._get_map_borders(self.transition_to_map_index)
        blend = max(0.0, min(1.0, float(progress)))

        left = int(from_left + (to_left - from_left) * blend)
        right = int(from_right + (to_right - from_right) * blend)

        self.active_border_left = left
        self.active_border_right = right

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

    def clamp_spawn_x_to_borders(
        self, spawn_x: int, object_width: int, min_padding: int = 0
    ) -> int:
        """
        Clamp a sprite's left X so it stays inside active map borders.

        Args:
            spawn_x (int): Proposed sprite left X coordinate.
            object_width (int): Sprite width in pixels.
            min_padding (int): Extra inset from each border.

        Returns:
            int: Border-safe sprite left X coordinate.
        """
        left_border, right_border = self.get_borders()
        padding = max(0, int(min_padding))

        min_left = left_border + padding
        max_left = right_border - int(object_width) - padding

        if max_left >= min_left:
            return max(min_left, min(int(spawn_x), max_left))

        centered = left_border + ((right_border - left_border - int(object_width)) // 2)
        fallback_left = max(left_border, right_border - int(object_width))
        return max(left_border, min(centered, fallback_left))

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
            Path("resources/models/maps/highway.png")
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

        if self.is_transitioning:
            self.transition_progress_px += max(0, int(speed))
            transition_distance = max(1, int(config.MAP_TRANSITION_DISTANCE))
            progress = self.transition_progress_px / float(transition_distance)

            if progress >= 1.0:
                self.is_transitioning = False
                self.transition_progress_px = float(transition_distance)
                self._apply_map_borders(self.transition_to_map_index)
            else:
                self._apply_interpolated_borders(progress)

    def set_map_by_score(self, score: int) -> None:
        """
        Switch background map based on score threshold.

        Args:
            score (int): Current game score.
        """
        if not self.bg_images:
            return

        # Calculate which map to show based on the score (switch every n points)
        map_index = (score // config.MAP_SWITCH_SCORE) % len(self.bg_images)
        if map_index == self.current_map_index and not self.is_transitioning:
            return

        if self.is_transitioning and map_index == self.transition_to_map_index:
            return

        self.transition_from_map_index = (
            self.transition_to_map_index if self.is_transitioning else self.current_map_index
        )
        self.transition_to_map_index = map_index
        self.transition_progress_px = 0.0
        self.is_transitioning = True
        self.current_map_index = map_index
        self._apply_interpolated_borders(0.0)

    def _draw_scrolling_background(self, surface: pygame.Surface, image: pygame.Surface) -> None:
        y1 = self.bg_y_offset
        y2 = self.bg_y_offset - self.height
        surface.blit(image, (0, y1))
        surface.blit(image, (0, y2))

    def _draw_scrolling_background_range(
        self,
        surface: pygame.Surface,
        image: pygame.Surface,
        clip_top: int,
        clip_bottom: int,
    ) -> None:
        top = max(0, int(clip_top))
        bottom = min(self.height, int(clip_bottom))
        if bottom <= top:
            return

        for dest_top in (self.bg_y_offset - self.height, self.bg_y_offset):
            src_top = max(0, top - dest_top)
            src_bottom = min(self.height, bottom - dest_top)

            if src_bottom <= src_top:
                continue

            blit_height = src_bottom - src_top
            surface.blit(
                image,
                (0, dest_top + src_top),
                area=pygame.Rect(0, src_top, self.window_width, blit_height),
            )

    def _draw_seam_gradient(
        self,
        surface: pygame.Surface,
        seam_y: int,
        gradient_height: int = 64,
        max_alpha: int = 70,
    ) -> None:
        half = max(1, int(gradient_height) // 2)
        center = int(seam_y)
        top = max(0, center - half)
        bottom = min(self.height, center + half)

        if bottom <= top:
            return

        band_height = bottom - top
        overlay = pygame.Surface((self.window_width, band_height), pygame.SRCALPHA)
        for y in range(band_height):
            distance = abs((top + y) - center)
            blend = max(0.0, 1.0 - (distance / float(half)))
            alpha = int(max_alpha * blend)
            if alpha > 0:
                pygame.draw.line(
                    overlay,
                    (0, 0, 0, alpha),
                    (0, y),
                    (self.window_width, y),
                )

        surface.blit(overlay, (0, top))

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
            if self.is_transitioning and 0 <= self.transition_from_map_index < len(
                self.bg_images
            ):
                transition_distance = max(1, int(config.MAP_TRANSITION_DISTANCE))
                progress = max(
                    0.0,
                    min(1.0, self.transition_progress_px / float(transition_distance)),
                )
                seam_y = int(progress * self.height)
                from_bg = self.bg_images[self.transition_from_map_index]
                to_bg = self.bg_images[self.transition_to_map_index]

                self._draw_scrolling_background_range(surface, to_bg, 0, seam_y)
                self._draw_scrolling_background_range(
                    surface, from_bg, seam_y, self.height
                )
                self._draw_seam_gradient(surface, seam_y)
            else:
                current_bg = self.bg_images[self.current_map_index]
                self._draw_scrolling_background(surface, current_bg)
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
        return self.active_border_left, self.active_border_right
