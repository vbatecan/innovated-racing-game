import config
import pygame

from environment.br_manager import BRManager
from environment.crack_manager import CrackManager
from environment.oil_spill_manager import OilSpillManager
from models.road import Road
from environment.obstacle_manager import ObstacleManager


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
        self._brake_freeze_until = 0

        self.road = Road(window_size, config.ROAD_SIZE["width"], lane_count=lane_count)
        self.obstacle_manager = ObstacleManager(self.road)
        self.crack_manager = CrackManager(self.road)
        self.br_manager = BRManager(self.road)
        self.oil_spill_manager = OilSpillManager(self.road)
        self.obstacle_manager.set_blocking_groups([self.br_manager.brs])
        self.br_manager.set_blocking_groups([self.obstacle_manager.obstacles])
        self.oil_spill_manager.set_blocking_groups(
            [self.obstacle_manager.obstacles, self.br_manager.brs, self.crack_manager.cracks]
        )

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
        Set the obstacle spawn frequency in frames.

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

    @property
    def oil_spills(self) -> pygame.sprite.Group:
        """Expose oil spill hazard sprites for collision checks."""
        return self.oil_spill_manager.oil_spills

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
        now = pygame.time.get_ticks()
        if is_braking:
            self._brake_freeze_until = now + max(0, int(config.BRAKE_HAZARD_FREEZE_MS))
        freeze_hazards = is_braking or now < self._brake_freeze_until

        effective_speed = 0 if freeze_hazards else self.speed

        if not freeze_hazards:
            self.scroll_y += effective_speed
            if self.scroll_y >= self.road.total_marker_segment:
                self.scroll_y -= self.road.total_marker_segment
            self.road.update_background_scroll(effective_speed)

        self.crack_manager.update(effective_speed, is_braking=freeze_hazards)
        self.br_manager.update(effective_speed, is_braking=freeze_hazards)
        self.oil_spill_manager.update(effective_speed, is_braking=freeze_hazards)
        self.obstacle_manager.update(effective_speed, is_braking=freeze_hazards)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the road, lane markers, and obstacles to the surface.

        Args:
            surface (pygame.Surface): Target drawing surface.

        Returns:
            None: Draws directly to `surface`.
        """
        self.road.draw_background(surface)
        self.crack_manager.draw(surface)
        self.br_manager.draw(surface)
        self.oil_spill_manager.draw(surface)
        self.obstacle_manager.draw(surface)
        self.road.draw_borders(surface)

    def clear_hazards(self) -> None:
        """Remove all active hazards from the map."""
        self.obstacles.empty()
        self.cracks.empty()
        self.brs.empty()
        self.oil_spills.empty()

    def get_road_borders(self) -> tuple[int, int]:
        """
        Return the left and right x-coordinates of the road.

        Returns:
            tuple[int, int]: `(left_x, right_x)` road boundaries.
        """
        return self.road.get_borders()
