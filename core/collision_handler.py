"""Collision detection and response system.

Handles all collision types (obstacles, cracks, oil, hearts, brake hazards)
and applies appropriate damage, effects, and state changes.
"""

from __future__ import annotations

import pygame
from core.enums import CollisionConstants
from core.oil_swerve_physics import OilSwervePhysics

from models.player_car import PlayerCar
from environment.map import Map
from core.game_state import GameStateManager


class CollisionResult:
    """Container for collision detection results."""

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


class _SpatialGrid:
    """Simple uniform-grid broadphase index to reduce collision checks."""

    def __init__(self, cell_size: int = 160) -> None:
        self._cell_size = max(32, int(cell_size))
        self._cells: dict[tuple[int, int], list[pygame.sprite.Sprite]] = {}

    def clear(self) -> None:
        self._cells.clear()

    def insert(self, sprite: pygame.sprite.Sprite) -> None:
        rect = sprite.rect
        min_cx = rect.left // self._cell_size
        max_cx = rect.right // self._cell_size
        min_cy = rect.top // self._cell_size
        max_cy = rect.bottom // self._cell_size
        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                self._cells.setdefault((cx, cy), []).append(sprite)

    def query(self, rect: pygame.Rect) -> list[pygame.sprite.Sprite]:
        min_cx = rect.left // self._cell_size
        max_cx = rect.right // self._cell_size
        min_cy = rect.top // self._cell_size
        max_cy = rect.bottom // self._cell_size

        seen: set[int] = set()
        result: list[pygame.sprite.Sprite] = []
        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                for sprite in self._cells.get((cx, cy), []):
                    sid = id(sprite)
                    if sid in seen:
                        continue
                    seen.add(sid)
                    result.append(sprite)
        return result


class CollisionHandler:
    """Manages all collision detection and response logic."""

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
        self._player_car = player_car
        self._game_map = game_map
        self._game_state = game_state_manager
        self._oil_swerve = oil_swerve
        self._crack_duration_ms = crack_duration_ms
        self._oil_duration_ms = oil_duration_ms
        self._question_manager = question_manager
        self._out_of_control_until: int = 0
        self._grid = _SpatialGrid(cell_size=160)

    @property
    def is_out_of_control(self) -> bool:
        return pygame.time.get_ticks() < self._out_of_control_until

    @property
    def out_of_control_until(self) -> int:
        return self._out_of_control_until

    def check_and_resolve_all(self) -> CollisionResult:
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

    def _build_index(self, group: pygame.sprite.Group) -> None:
        self._grid.clear()
        for sprite in group:
            self._grid.insert(sprite)

    def _collide_group(self, group: pygame.sprite.Group, dokill: bool = True) -> list[pygame.sprite.Sprite]:
        if not group:
            return []

        self._build_index(group)
        candidates = self._grid.query(self._player_car.rect)
        if not candidates:
            return []

        hits: list[pygame.sprite.Sprite] = []
        player_rect = self._player_car.rect
        for sprite in candidates:
            if not player_rect.colliderect(sprite.rect):
                continue
            if pygame.sprite.collide_mask(self._player_car, sprite):
                hits.append(sprite)

        if dokill:
            for sprite in hits:
                sprite.kill()

        return hits

    def _check_obstacle_collision(self) -> bool:
        hits = self._collide_group(self._game_map.obstacles, dokill=True)
        if hits:
            self._player_car.current_speed = 0
            self._player_car.velocity_x = 0
            self._game_state.apply_collision_damage(CollisionConstants.DEFAULT_DAMAGE)
            return True
        return False

    def _check_crack_collision(self) -> bool:
        hits = self._collide_group(self._game_map.cracks, dokill=True)
        if hits:
            now = pygame.time.get_ticks()
            self._out_of_control_until = now + self._crack_duration_ms

            self._player_car.current_speed = max(
                0.0,
                float(self._player_car.current_speed) * CollisionConstants.CRACK_SPEED_REDUCTION,
            )
            self._player_car.velocity_x *= CollisionConstants.CRACK_VELOCITY_REDUCTION
            self._player_car.velocity_x = max(
                0.0,
                float(self._player_car.velocity_x) * CollisionConstants.CRACK_SPEED_REDUCTION,
            )
            return True
        return False

    def _check_brake_collision(self) -> bool:
        hits = self._collide_group(self._game_map.brs, dokill=True)
        if hits:
            self._player_car.current_speed = 0
            self._player_car.velocity_x = 0
            self._game_state.apply_collision_damage(CollisionConstants.DEFAULT_DAMAGE)
            return True
        return False

    def _check_oil_collision(self) -> bool:
        hits = self._collide_group(self._game_map.oil_spills, dokill=True)
        if hits:
            self._oil_swerve.trigger(self._oil_duration_ms)
            return True
        return False

    def _check_heart_collision(self) -> bool:
        hits = self._collide_group(self._game_map.hearts, dokill=True)
        if hits:
            from core.enums import QuestionConstants

            if self._game_state.lives < QuestionConstants.MAX_LIVES:
                self._game_state.trigger_heart_question()
            else:
                self._game_state._scoring_system.add_score(QuestionConstants.HEART_BONUS_SCORE)
            return True
        return False

    def clamp_to_road(self) -> None:
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
        self._out_of_control_until = 0
        self._grid.clear()
