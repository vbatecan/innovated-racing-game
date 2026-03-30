import config
import pygame

from environment.br_manager import BRManager
from environment.crack_manager import CrackManager
from environment.oil_spill_manager import OilSpillManager
from environment.heart_bonus_manager import HeartBonusManager
from models.road import Road
from environment.obstacle_manager import ObstacleManager


class Map:
    """
    Orchestrates the game world including the scrolling road, all hazard managers,
    and collectible items. Coordinates updates and rendering across all environmental
    systems and provides unified access to collision-relevant sprite groups.

    Attributes:
        width (int): The width of the game window.
        height (int): The height of the game window.
        speed (int): The speed of the game.
        scroll_y (int): The current scroll position of the road.
        current_score (int): The current score of the game.
        road (Road): The scrolling road.
        obstacle_manager (ObstacleManager): The obstacle manager.
        crack_manager (CrackManager): The crack manager.
        br_manager (BRManager): The BR manager.
        oil_spill_manager (OilSpillManager): The oil spill manager.
        heart_bonus_manager (HeartBonusManager): The heart bonus manager.
    """
    def __init__(
            self, window_size: dict[str, int], lane_count: int = config.LANE_COUNT
    ):
        """
        Initialize the scrolling road and all hazard managers.

        Args:
            window_size: Screen dimensions with 'width' and 'height' keys.
            lane_count: Initial number of lanes for the road.
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
        self.oil_spill_manager = OilSpillManager(self.road)
        self.heart_bonus_manager = HeartBonusManager(
            self.road, spawn_frequency=900, max_hearts=1
        )
        self.obstacle_manager.set_blocking_groups([self.br_manager.brs])
        self.br_manager.set_blocking_groups([self.obstacle_manager.obstacles])
        self.oil_spill_manager.set_blocking_groups(
            [
                self.obstacle_manager.obstacles,
                self.br_manager.brs,
                self.crack_manager.cracks,
            ]
        )

    @property
    def obstacles(self) -> pygame.sprite.Group:
        """
        Expose obstacle sprites for collision detection.

        Returns:
            The pygame sprite group containing active obstacles.
        """
        return self.obstacle_manager.obstacles

    @property
    def obstacle_frequency(self) -> int:
        """
        Get the current obstacle spawn frequency in frames.

        Returns:
            The number of frames between obstacle spawn attempts.
        """
        return self.obstacle_manager.spawn_frequency

    @obstacle_frequency.setter
    def obstacle_frequency(self, value: int) -> None:
        """
        Set the obstacle spawn frequency in frames.

        Args:
            value: Frames between spawn attempts to set on the obstacle manager.
        """
        self.obstacle_manager.set_spawn_frequency(value)

    @property
    def cracks(self) -> pygame.sprite.Group:
        """
        Expose crack hazard sprites for collision detection.

        Returns:
            The pygame sprite group containing active crack hazards.
        """
        return self.crack_manager.cracks

    @property
    def brs(self) -> pygame.sprite.Group:
        """
        Expose BR hazard sprites for collision detection.

        Returns:
            The pygame sprite group containing active BR hazards.
        """
        return self.br_manager.brs

    @property
    def oil_spills(self) -> pygame.sprite.Group:
        """
        Expose oil spill hazard sprites for collision detection.

        Returns:
            The pygame sprite group containing active oil spills.
        """
        return self.oil_spill_manager.oil_spills

    @property
    def hearts(self) -> pygame.sprite.Group:
        """
        Expose heart bonus sprites for collision detection.

        Returns:
            The pygame sprite group containing active heart bonuses.
        """
        return self.heart_bonus_manager.hearts

    def set_lane_count(self, lane_count: int) -> None:
        """
        Apply a new lane count to the road at runtime.

        Args:
            lane_count: The desired number of lanes.
        """
        self.road.set_lane_count(lane_count)

    def update_score(self, score: int) -> None:
        """
        Update the current score and trigger map transitions based on score thresholds.

        Args:
            score: The current game score.
        """
        self.current_score = score
        self.road.set_map_by_score(score)

    def update(self, is_braking: bool = False) -> None:
        """
        Advance the road scroll and update all hazard managers.

        Args:
            is_braking: Unused parameter (reserved for future braking mechanics).
        """
        _ = is_braking
        effective_speed = max(0.0, float(self.speed))

        self.scroll_y += effective_speed
        if self.scroll_y >= self.road.total_marker_segment:
            self.scroll_y -= self.road.total_marker_segment
        self.road.update_background_scroll(effective_speed)

        self.crack_manager.update(effective_speed)
        self.br_manager.update(effective_speed)
        self.oil_spill_manager.update(effective_speed)
        self.obstacle_manager.update(effective_speed)
        self.heart_bonus_manager.update(int(effective_speed))

    def draw(self, surface: pygame.Surface) -> None:
        """
        Render the road background, all hazards, and road borders to the surface.

        Args:
            surface: The target pygame surface for drawing.
        """
        self.road.draw_background(surface)
        self.crack_manager.draw(surface)
        self.br_manager.draw(surface)
        self.oil_spill_manager.draw(surface)
        self.obstacle_manager.draw(surface)
        self.heart_bonus_manager.draw(surface)
        self.road.draw_borders(surface)

    def clear_hazards(self) -> None:
        """Remove all active hazards and bonuses from the map."""
        self.obstacles.empty()
        self.cracks.empty()
        self.brs.empty()
        self.oil_spills.empty()
        self.heart_bonus_manager.clear()

    def get_road_borders(self) -> tuple[int, int]:
        """
        Retrieve the left and right x-coordinates of the road boundaries.

        Returns:
            A tuple of (left_x, right_x) defining the road edges.
        """
        return self.road.get_borders()
