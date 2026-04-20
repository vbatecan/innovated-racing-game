"""Enumerations and constants for the racing game.

Centralizes all game state values, turn directions, and gear-related constants
to ensure consistency across the codebase.
"""

from enum import Enum, auto
from typing import Dict


class GameState(Enum):
    """Enumeration of possible game states.

    Attributes:
        PLAYING: Normal gameplay state.
        QUESTION: Question/answer overlay active.
        GAME_OVER: Game over screen displayed.
    """
    PLAYING = auto()
    QUESTION = auto()
    GAME_OVER = auto()


class TurnDirection(Enum):
    """Enumeration of turn direction states.

    Attributes:
        LEFT: Vehicle turning left.
        CENTER: Vehicle centered/no turn.
        RIGHT: Vehicle turning right.
    """
    LEFT = "LEFT"
    CENTER = "CENTER"
    RIGHT = "RIGHT"


class GearConstants:
    """Constants for the gear system.

    Preserves the exact gear ratios and limits from the original monolithic code.
    """

    MAX_MANUAL_GEAR: int = 5
    DEFAULT_GEAR: int = 1

    SPEED_RATIOS: Dict[int, float] = {
        1: 0.45,
        2: 0.62,
        3: 0.78,
        4: 0.9,
        5: 1.0,
    }

    ACCEL_RATIOS: Dict[int, float] = {
        1: 1.3,
        2: 1.15,
        3: 1.0,
        4: 0.9,
        5: 0.8,
    }


class OilSwerveConstants:
    """Constants for oil spill swerve physics.

    These values control the sine-wave based swerve behavior when
    the player drives over an oil spill.
    """

    SECONDARY_WAVE_AMPLITUDE: float = 0.4
    SECONDARY_WAVE_FREQUENCY_MULT: float = 1.9
    SECONDARY_WAVE_PHASE_MULT: float = 0.6
    ENVELOPE_BASE: float = 0.35
    ENVELOPE_PROGRESS_MULTIPLIER: float = 0.65
    FREQUENCY_PROGRESS_MULTIPLIER: float = 0.25
    FREQUENCY_BASE_MULTIPLIER: float = 1.15


class QuestionConstants:
    """Constants for the question/answer system."""

    INPUT_LOCK_MS: int = 700
    MAX_LIVES: float = 3.0
    LIFE_INCREMENT: float = 1.0
    LAST_CHANCE_LIVES: float = 1.0
    HEART_BONUS_SCORE: int = 50


class CollisionConstants:
    """Constants for collision damage and effects."""

    DEFAULT_DAMAGE: float = 1.0
    CRACK_SPEED_REDUCTION: float = 0.5
    CRACK_VELOCITY_REDUCTION: float = 0.6
    CRACK_OUT_OF_CONTROL_MS: int = 1000
    OUT_OF_CONTROL_STEER_CLAMP: float = 2.0


class ScoringConstants:
    """Constants for the scoring system."""

    BASE_SPEED: float = 4.0
    SPEED_INCREMENT_THRESHOLD: int = 500
    SPEED_INCREMENT_PER_THRESHOLD: float = 1.0
