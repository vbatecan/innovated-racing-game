"""Game state management system.

Handles the centralized state for the racing game including lives,
game state transitions, pause state, and run reset functionality.
"""

from typing import Optional, TYPE_CHECKING
import pygame
import config
from core.enums import GameState, QuestionConstants

if TYPE_CHECKING:
    from models.player_car import PlayerCar
    from models.score import ScoringSystem
    from environment.map import Map
    from ui.hud import PlayerHUD
    from settings import Settings
    from ui.game_ui import SettingsMenu, PauseMenu


class GameStateManager:
    """Manages the complete game state lifecycle.

    Encapsulates all state variables that were previously scattered across
    the main() function's local scope, providing a clean interface for
    state transitions and resets.
    """

    def __init__(
        self,
        player_car: "PlayerCar",
        scoring_system: "ScoringSystem",
        game_map: "Map",
        hud: "PlayerHUD",
        settings: "Settings",
        settings_menu: "SettingsMenu",
        pause_menu: "PauseMenu",
        window_size: dict,
        question_manager: object,
    ) -> None:
        """Initialize the game state manager with all required dependencies.

        Args:
            player_car: The player's car instance for position resets.
            scoring_system: The scoring system for score resets.
            game_map: The game map for hazard clearing.
            hud: The HUD for heart collection tracking.
            settings: The settings instance for visibility toggles.
            settings_menu: The settings menu UI component.
            pause_menu: The pause menu UI component.
            window_size: Dictionary with 'width' and 'height' keys.
            question_manager: The QuestionManager for fetching/validating questions.
        """
        self._player_car = player_car
        self._scoring_system = scoring_system
        self._game_map = game_map
        self._hud = hud
        self._settings = settings
        self._settings_menu = settings_menu
        self._pause_menu = pause_menu
        self._window_size = window_size
        self._question_manager = question_manager

        # Core state
        self.lives: float = float(max(1, int(config.STARTING_LIVES)))
        self.game_state: GameState = GameState.PLAYING
        self.pause_state: bool = False
        self.active_question: Optional[object] = None
        self.selected_option: int = 0
        self.heart_question_active: bool = False
        self.question_input_unlock_at: int = 0

        # Timing
        self.last_frame_time: int = 0

        # Reset all state to initial values
        self.reset_run_state()

    def reset_run_state(self) -> None:
        """Reset all game state variables to their initial values."""
        self.lives = float(max(1, int(config.STARTING_LIVES)))
        self._scoring_system.reset()

        start_x = self._window_size["width"] // 2
        start_y = self._window_size["height"] - 240
        self._player_car.rect.center = (start_x, start_y)
        self._player_car.x = float(start_x)
        self._player_car.y = float(start_y)
        self._player_car.current_speed = 0
        self._player_car.velocity_x = 0
        self._player_car.current_angle = 0.0
        self._player_car.turn(0.0, 0.0)

        self._game_map.clear_hazards()

        self.game_state = GameState.PLAYING
        self.pause_state = False
        self._pause_menu.hide()
        self.active_question = None
        self.selected_option = 0
        self.question_input_unlock_at = 0
        self.heart_question_active = False

        self._hud.reset_hearts_collected()

        self._settings.visible = False

        self.last_frame_time = pygame.time.get_ticks()

    def trigger_last_chance_question(self) -> None:
        """Trigger a last-chance question when lives reach critical level."""
        self.game_state = GameState.QUESTION
        self.heart_question_active = False
        self.active_question = self._question_manager.get_random_question()
        self.selected_option = 0
        self.question_input_unlock_at = pygame.time.get_ticks() + QuestionConstants.INPUT_LOCK_MS
        self._settings.visible = False

    def trigger_heart_question(self) -> None:
        """Trigger a heart bonus question for extra life."""
        self.game_state = GameState.QUESTION
        self.heart_question_active = True
        self.active_question = self._question_manager.get_random_question()
        self.selected_option = 0
        self.question_input_unlock_at = pygame.time.get_ticks() + QuestionConstants.INPUT_LOCK_MS
        self._settings.visible = False

    def resolve_question_answer(self, answer_index: int) -> None:
        """Resolve the answer to an active question.

        Args:
            answer_index: The zero-based index of the selected answer.
        """
        if self.active_question is None:
            return

        is_correct = self._question_manager.validate_answer(self.active_question, answer_index)

        if is_correct:
            if self.heart_question_active:
                self.lives = min(
                    QuestionConstants.MAX_LIVES,
                    self.lives + QuestionConstants.LIFE_INCREMENT
                )
                self._hud.add_heart_collected()
                self.heart_question_active = False
            else:
                self.lives = QuestionConstants.LAST_CHANCE_LIVES
            self.game_state = GameState.PLAYING
        else:
            if self.heart_question_active:
                self.heart_question_active = False
                self.game_state = GameState.PLAYING
            else:
                self.game_state = GameState.GAME_OVER

        self.active_question = None
        self.selected_option = 0
        self.question_input_unlock_at = 0

    def apply_collision_damage(self, damage: float = 1.0) -> None:
        """Apply collision damage and handle life reduction.

        If lives would drop to or below 1.0, triggers a last-chance
        question instead of immediate game over.

        Args:
            damage: The amount of damage to apply (default 1.0).
        """
        if self.game_state != GameState.PLAYING:
            return

        self._scoring_system.register_collision(pygame.time.get_ticks())

        if self.lives <= 1.0:
            self.trigger_last_chance_question()
            return

        self.lives = max(1.0, self.lives - float(damage))

    def is_question_input_ready(self) -> bool:
        """Check if question input is unlocked and ready."""
        return pygame.time.get_ticks() >= self.question_input_unlock_at

    def update_last_frame_time(self) -> int:
        """Update and return the delta time since last frame."""
        now = pygame.time.get_ticks()
        delta_time = now - self.last_frame_time
        self.last_frame_time = now
        return delta_time

    def set_last_frame_time(self, time_ms: int) -> None:
        """Manually set the last frame time."""
        self.last_frame_time = time_ms
