"""Collision detection and response system.

Handles all collision types (obstacles, cracks, oil, hearts, brake hazards)
and applies appropriate damage, effects, and state changes.
"""

import pygame
from core.enums import CollisionConstants
from core.oil_swerve_physics import OilSwervePhysics

from models.player_car import PlayerCar
from environment.map import Map
from core.game_state import GameStateManager


class CollisionResult:
    """Container for collision detection results.

    Attributes:
        obstacle_hit: True if player hit an obstacle.
        crack_hit: True if player hit a crack.
        oil_hit: True if player hit oil.
        heart_hit: True if player collected a heart.
        brake_hit: True if player hit a brake hazard.
    """

    def __init__(
        self,
        obstacle_hit: bool = False,
        crack_hit: bool = False,
        oil_hit: bool = False,
        heart_hit: bool = False,
        brake_hit: bool = False,
    ) -> None:
        self.obstacle_hit = obstacle_hit
        self.crack_hit = crack_hit
        self.oil_hit = oil_hit
        self.heart_hit = heart_hit
        self.brake_hit = brake_hit


class CollisionHandler:
    """Manages all collision detection and response logic.

    Detects collisions between the player car and various map hazards,
    then applies the appropriate damage, speed reduction, or state changes.
    """

    def __init__(
        self,
        player_car: "PlayerCar",
        game_map: "Map",
        game_state_manager: "GameStateManager",
        oil_swerve: OilSwervePhysics,
        crack_duration_ms: int,
        oil_duration_ms: int,
        question_manager: object,
    ) -> None:
        """Initialize the collision handler.

        Args:
            player_car: The player's car sprite.
            game_map: The game map containing all hazard sprite groups.
            game_state_manager: The game state manager for damage/lives.
            oil_swerve: The oil swerve physics system.
            crack_duration_ms: Duration of out-of-control from crack hits.
            oil_duration_ms: Duration of oil swerve effect.
            question_manager: The QuestionManager for triggering heart questions.
        """
        self._player_car = player_car
        self._game_map = game_map
        self._game_state = game_state_manager
        self._oil_swerve = oil_swerve
        self._crack_duration_ms = crack_duration_ms
        self._oil_duration_ms = oil_duration_ms
        self._question_manager = question_manager
        self._out_of_control_until: int = 0

    @property
    def is_out_of_control(self) -> bool:
        """Check if player is currently out of control (from crack hit).

        Returns:
            True if out-of-control period is active.
        """
        return pygame.time.get_ticks() < self._out_of_control_until

    @property
    def out_of_control_until(self) -> int:
        """Get the timestamp when out-of-control state ends."""
        return self._out_of_control_until

    def check_and_resolve_all(self) -> CollisionResult:
        """Check all collision types and apply responses.

        Performs collision detection against all hazard groups and
        applies the appropriate damage/effects for each hit.

        Returns:
            CollisionResult indicating which collision types occurred.
        """
        result = CollisionResult()

        if self._check_obstacle_collision():
            result.obstacle_hit = True

        if self._check_crack_collision():
            result.crack_hit = True

        if self._check_brake_collision():
            result.brake_hit = True

        if self._check_oil_collision():
            result.oil_hit = True

        if self._check_heart_collision():
            result.heart_hit = True

        return result

    def _check_obstacle_collision(self) -> bool:
        """Check and resolve obstacle collisions.

        Returns:
            True if collision occurred.
        """
        hits = pygame.sprite.spritecollide(
            self._player_car,
            self._game_map.obstacles,
            True,
            collided=pygame.sprite.collide_mask,
        )

        if hits:
            self._player_car.current_speed = 0
            self._player_car.velocity_x = 0
            self._game_state.apply_collision_damage(CollisionConstants.DEFAULT_DAMAGE)
            return True
        return False

    def _check_crack_collision(self) -> bool:
        """Check and resolve crack collisions.

        Applies speed reduction and out-of-control state without damage.

        Returns:
            True if collision occurred.
        """
        hits = pygame.sprite.spritecollide(
            self._player_car,
            self._game_map.cracks,
            True,
            collided=pygame.sprite.collide_mask,
        )

        if hits:
            now = pygame.time.get_ticks()
            self._out_of_control_until = now + self._crack_duration_ms

            self._player_car.current_speed = max(
                0.0,
                float(self._player_car.current_speed)
                * CollisionConstants.CRACK_SPEED_REDUCTION,
            )

            self._player_car.velocity_x *= CollisionConstants.CRACK_VELOCITY_REDUCTION
            self._player_car.velocity_x = max(
                0.0,
                float(self._player_car.velocity_x)
                * CollisionConstants.CRACK_SPEED_REDUCTION,
            )

            return True
        return False

    def _check_brake_collision(self) -> bool:
        """Check and resolve brake hazard collisions.

        Returns:
            True if collision occurred.
        """
        hits = pygame.sprite.spritecollide(
            self._player_car,
            self._game_map.brs,
            True,
            collided=pygame.sprite.collide_mask,
        )

        if hits:
            self._player_car.current_speed = 0
            self._player_car.velocity_x = 0
            self._game_state.apply_collision_damage(CollisionConstants.DEFAULT_DAMAGE)
            return True
        return False

    def _check_oil_collision(self) -> bool:
        """Check and resolve oil spill collisions.

        Triggers the oil swerve physics effect.

        Returns:
            True if collision occurred.
        """
        hits = pygame.sprite.spritecollide(
            self._player_car,
            self._game_map.oil_spills,
            True,
            collided=pygame.sprite.collide_mask,
        )

        if hits:
            self._oil_swerve.trigger(self._oil_duration_ms)
            return True
        return False

    def _check_heart_collision(self) -> bool:
        """Check and resolve heart/health pickup collisions.

        Triggers heart question if lives < 3, otherwise adds score.

        Returns:
            True if collision occurred.
        """
        hits = pygame.sprite.spritecollide(
            self._player_car,
            self._game_map.hearts,
            True,
            collided=pygame.sprite.collide_mask,
        )

        if hits:
            from core.enums import QuestionConstants

            if self._game_state.lives < QuestionConstants.MAX_LIVES:
                self._game_state.trigger_heart_question()
            else:
                self._game_state._scoring_system.add_score(
                    QuestionConstants.HEART_BONUS_SCORE
                )
            return True
        return False

    def clamp_to_road(self) -> None:
        """Clamp player position to road boundaries.

        Prevents the car from leaving the road and zeros velocity
        if attempting to drive off the edge.
        """
        road_min_x, road_max_x = self._game_map.get_road_borders()

        if self._player_car.rect.left < road_min_x:
            self._player_car.rect.left = road_min_x
            self._player_car.x = float(self._player_car.rect.x)
            if self._player_car.velocity_x < 0:
                self._player_car.velocity_x = 0
        elif self._player_car.rect.right > road_max_x:
            self._player_car.rect.right = road_max_x
            self._player_car.x = float(self._player_car.rect.x)
            if self._player_car.velocity_x > 0:
                self._player_car.velocity_x = 0

    def reset(self) -> None:
        """Reset collision handler state."""
        self._out_of_control_until = 0
