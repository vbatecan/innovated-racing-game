"""Main game loop orchestration.

Centralizes the game loop logic that was previously in main()'s massive
while loop, delegating to specialized systems for state management,
input handling, physics, and rendering.
"""

from typing import Optional
import logging
import pygame
import cv2
import config
from core.enums import GameState, ScoringConstants
from core.game_state import GameStateManager
from core.boost_system import BoostSystem
from core.gear_system import GearSystem
from core.oil_swerve_physics import OilSwervePhysics
from core.collision_handler import CollisionHandler
from input.key_mapper import KeyMapper
from input.steering_handler import SteeringHandler

logger = logging.getLogger(__name__)


class GameLoop:
    """Orchestrates the main game loop and coordinates all subsystems.

    This class replaces the monolithic main() function, delegating specific
    responsibilities to dedicated handler classes while maintaining the exact
    logic flow and timing of the original implementation.
    """

    def __init__(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
        player_car: object,
        game_map: object,
        detector: object,
        settings: object,
        hud: object,
        game_hud: object,
        pause_menu: object,
        settings_menu: object,
        window_size: dict,
    ) -> None:
        """Initialize the game loop with all required components.

        Args:
            screen: The main Pygame display surface.
            clock: The Pygame clock for frame timing.
            player_car: The player car sprite/model.
            game_map: The game map/environment.
            detector: The hand gesture controller.
            settings: The game settings instance.
            hud: The legacy HUD component.
            game_hud: The new game HUD manager.
            pause_menu: The pause menu UI.
            settings_menu: The settings menu UI.
            window_size: Dictionary with 'width' and 'height' keys.
        """
        self._screen = screen
        self._clock = clock
        self._player_car = player_car
        self._game_map = game_map
        self._detector = detector
        self._settings = settings
        self._hud = hud
        self._game_hud = game_hud
        self._pause_menu = pause_menu
        self._settings_menu = settings_menu
        self._window_size = window_size

        self._font = pygame.font.Font(None, config.FONT_SIZE)
        self._overlay_title_font = pygame.font.Font(
            None, max(40, config.FONT_SIZE * 2)
        )
        self._overlay_body_font = pygame.font.Font(
            None, max(30, config.FONT_SIZE + 10)
        )

        from models.score import ScoringSystem
        from environment.question_manager import QuestionManager

        self._scoring_system = ScoringSystem(config.SCORING_CONFIG)
        self._question_manager = QuestionManager()

        self._game_state_manager: Optional[GameStateManager] = None
        self._boost_system = BoostSystem()
        self._gear_system = GearSystem()
        self._oil_swerve = OilSwervePhysics()
        self._collision_handler: Optional[CollisionHandler] = None
        self._key_mapper = KeyMapper()
        self._steering_handler = SteeringHandler()

        self._running = True
        self._selected_setting = 0
        self._is_braking = False
        self._target_steer = 0.0
        self._max_speed = player_car.max_speed

    def initialize(self) -> None:
        """Initialize game state manager and collision handler.

        Must be called after all dependencies are set up but before run().
        """
        self._game_state_manager = GameStateManager(
            player_car=self._player_car,
            scoring_system=self._scoring_system,
            game_map=self._game_map,
            hud=self._hud,
            settings=self._settings,
            settings_menu=self._settings_menu,
            pause_menu=self._pause_menu,
            window_size=self._window_size,
            question_manager=self._question_manager,
        )

        self._collision_handler = CollisionHandler(
            player_car=self._player_car,
            game_map=self._game_map,
            game_state_manager=self._game_state_manager,
            oil_swerve=self._oil_swerve,
            crack_duration_ms=1000,
            oil_duration_ms=config.OIL_SWERVE_DURATION_MS,
            question_manager=self._question_manager,
        )

        logger.info("Starting Game Loop...")
        logger.info("Controls: Use your hands visible to the camera.")
        logger.info("Press 'S' to open Settings.")

    def run(self) -> None:
        """Execute the main game loop until exit."""
        if self._game_state_manager is None:
            raise RuntimeError("GameLoop.initialize() must be called before run()")

        while self._running:
            self._process_frame()

        self._cleanup()

    def _process_frame(self) -> None:
        """Process a single game frame."""
        self._is_braking = False

        self._detector.set_require_two_hands(
            self._game_state_manager.game_state == GameState.PLAYING
        )
        self._game_map.speed = self._settings.car_speed
        self._game_map.obstacle_frequency = int(
            (self._settings.max_fps * 2) / self._settings.obstacle_frequency
        )
        self._game_map.set_lane_count(self._settings.lane_count)

        self._handle_events()

        if self._pause_menu.visible:
            self._process_pause_menu()
            return

        if self._game_state_manager.game_state == GameState.QUESTION:
            self._process_question_input()

        if (
            self._game_state_manager.game_state == GameState.PLAYING
            and not self._settings.visible
        ):
            self._update_gameplay()

        self._render()

        delta_time = self._game_state_manager.update_last_frame_time()

        if (
            self._game_state_manager.game_state == GameState.PLAYING
            and not self._is_braking
            and not self._settings.visible
        ):
            self._scoring_system.update(
                current_speed=self._player_car.current_speed,
                max_speed=self._max_speed,
                delta_time=delta_time,
                steering=self._target_steer,
                is_braking=self._is_braking,
                current_time=pygame.time.get_ticks(),
                obstacles=list(self._game_map.obstacles)
                if self._game_map.obstacles
                else None,
            )

        self._update_speed_from_score()

        self._clock.tick(self._settings.max_fps)

    def _handle_events(self) -> None:
        """Process all Pygame events for the current frame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
                continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._handle_escape()
                continue

            if self._game_state_manager.game_state == GameState.QUESTION:
                self._handle_question_key(event)
                continue

            if self._game_state_manager.game_state == GameState.GAME_OVER:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self._game_state_manager.reset_run_state()
                    self._reset_subsystems()
                continue

            if self._settings.visible:
                self._handle_settings_event(event)
                continue

            self._handle_gameplay_event(event)

    def _handle_escape(self) -> None:
        """Handle ESC key press for pause menu toggle."""
        if (
            self._game_state_manager.game_state == GameState.PLAYING
            and not self._settings.visible
        ):
            if not self._pause_menu.visible:
                self._pause_menu.show()
            else:
                self._pause_menu.hide()

    def _handle_question_key(self, event: pygame.event.Event) -> None:
        """Handle keyboard input during question state."""
        if event.type == pygame.KEYDOWN:
            selected = self._key_mapper.get_option_index(event.key)
            if selected is not None and self._game_state_manager.active_question is not None:
                if selected < self._game_state_manager.active_question.answer_count:
                    self._game_state_manager.resolve_question_answer(
                        selected
                    )

    def _handle_settings_event(self, event: pygame.event.Event) -> None:
        """Handle input when settings menu is visible."""
        mouse_pos = pygame.mouse.get_pos()
        result = self._settings_menu.handle_input(event, mouse_pos)
        if result and result.get("action") in ("changed", "close"):
            self._settings_menu.apply_to_game(self._settings)
        if result and result.get("action") == "close":
            self._settings.visible = False

    def _handle_gameplay_event(self, event: pygame.event.Event) -> None:
        """Handle normal gameplay input events."""
        running, selected_setting, show_settings = self._settings.handle_event(
            event,
            self._running,
            self._selected_setting,
            config.SETTING_OPTIONS,
            self._settings.visible,
        )
        self._running = running
        self._selected_setting = selected_setting
        self._settings.visible = show_settings

    def _process_pause_menu(self) -> None:
        """Process pause menu updates and rendering."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        for event in pygame.event.get([pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]):
            result = self._pause_menu.handle_input(event)
            self._process_pause_result(result)

        self._pause_menu.update(mouse_pos, mouse_pressed)

        clicked = self._pause_menu._clicked_option
        self._pause_menu._clicked_option = None
        self._process_pause_result(clicked)

        delta_time = 16
        self._game_map.draw(self._screen)
        self._render_sprite()
        self._game_hud.draw(self._screen)
        self._pause_menu.draw(self._screen, delta_time / 1000.0)
        pygame.display.flip()

    def _process_pause_result(self, result: Optional[str]) -> None:
        """Process pause menu selection result."""
        if result == "Resume":
            self._pause_menu.hide()
        elif result == "Restart":
            self._game_state_manager.reset_run_state()
            self._reset_subsystems()
            self._pause_menu.hide()
        elif result == "Settings":
            self._pause_menu.hide()
            self._settings.visible = True
        elif result == "Quit":
            self._running = False

    def _process_question_input(self) -> None:
        """Process hand gesture input during question state."""
        if self._game_state_manager.active_question is None:
            return

        swipe_up, swipe_down = self._detector.consume_swipe_request()

        if self._game_state_manager.is_question_input_ready():
            if swipe_up:
                self._game_state_manager.selected_option = max(
                    0, self._game_state_manager.selected_option - 1
                )
            if swipe_down:
                self._game_state_manager.selected_option = min(
                    self._game_state_manager.active_question.answer_count - 1,
                    self._game_state_manager.selected_option + 1
                )

            if self._detector.consume_question_select_request():
                self._game_state_manager.resolve_question_answer(
                    self._game_state_manager.selected_option
                )

    def _update_gameplay(self) -> None:
        """Update gameplay state for the current frame."""
        self._detector.brake_threshold = self._settings.get_brake_threshold()

        frame = self._detector.get_frame()
        cv2.waitKey(1)
        if self._settings.show_camera and frame is not None:
            self._game_hud.set_camera_frame(frame)
        self._game_hud.set_camera_visibility(self._settings.show_camera)

        self._boost_system.update(self._detector.boosting)

        self._is_braking = self._detector.breaking
        keys = pygame.key.get_pressed()
        if keys[pygame.K_DOWN]:
            self._is_braking = True

        now = pygame.time.get_ticks()
        if self._oil_swerve.is_active:
            self._is_braking = False

        shift_down, shift_up = self._detector.consume_shift_request()
        self._gear_system.handle_shift_request(shift_down, shift_up)

        if self._oil_swerve.is_active:
            self._target_steer = self._oil_swerve.calculate_steering(
                base_frequency=config.OIL_SWERVE_FREQUENCY,
                base_strength=config.OIL_SWERVE_STRENGTH,
                is_out_of_control=self._collision_handler.is_out_of_control
            )
        else:
            self._target_steer = (
                self._detector.steer * self._settings.steering_sensitivity
            )
            self._target_steer, _ = self._steering_handler.calculate_steering(
                keys, self._settings.steering_sensitivity, self._target_steer
            )

            if self._collision_handler.is_out_of_control:
                self._target_steer = max(
                    -2.0, min(2.0, -self._target_steer)
                )

        self._target_steer = max(-2.0, min(2.0, self._target_steer))
        self._player_car.turn(
            max(-2, min(self._target_steer, 2)),
            self._player_car.turn_smoothing
        )

        acceleration = self._settings.ACCELERATION * self._gear_system.get_acceleration_ratio()
        self._max_speed = self._player_car.max_speed * self._gear_system.get_speed_ratio()

        if self._boost_system.is_active:
            acceleration *= self._boost_system.get_acceleration_multiplier()
            self._max_speed *= self._boost_system.get_speed_multiplier()

        self._player_car.update(
            steering=self._target_steer,
            is_braking=self._is_braking,
            max_speed=self._max_speed,
            acceleration=acceleration,
            friction=self._settings.FRICTION,
            brake_strength=self._settings.BRAKE_STRENGTH,
            screen_width=self._window_size["width"],
        )

        self._game_map.speed = float(self._player_car.current_speed)
        self._game_map.update_score(self._scoring_system.get_score())
        self._game_map.update(is_braking=self._is_braking)

        self._collision_handler.clamp_to_road()

        self._collision_handler.check_and_resolve_all()

    def _render(self) -> None:
        """Render the game frame."""
        self._game_map.draw(self._screen)
        self._render_sprite()

        fps = self._clock.get_fps()
        self._hud.update_from_game(
            self._player_car,
            self._detector,
            gear=str(self._gear_system.current_gear),
            score=self._scoring_system.get_score(),
            lives=self._game_state_manager.lives,
            fps=int(fps),
            max_fps=self._settings.max_fps,
        )
        self._hud.set_scoring_info(
            combo=self._scoring_system.get_combo(),
            difficulty=self._scoring_system.get_difficulty(),
            distance=self._scoring_system.get_distance(),
        )

        hearts_collected = (
            self._hud._hearts_collected
            if hasattr(self._hud, "_hearts_collected")
            else 0
        )
        self._game_hud.update(
            speed=self._player_car.current_speed,
            max_speed=self._max_speed,
            score=self._scoring_system.get_score(),
            lives=int(self._game_state_manager.lives),
            distance=self._scoring_system.get_distance(),
            gear=self._gear_system.current_gear,
            is_braking=self._is_braking,
            boost_energy=100.0,
            hearts_collected=hearts_collected,
        )
        self._game_hud.draw(self._screen)

        if self._settings.visible:
            self._settings_menu.update(pygame.mouse.get_pos())
            self._settings_menu.draw(self._screen)

        if self._game_state_manager.game_state == GameState.QUESTION:
            from ui.overlays import draw_question_overlay
            draw_question_overlay(
                self._screen,
                self._overlay_title_font,
                self._overlay_body_font,
                self._game_state_manager.active_question,
                self._game_state_manager.selected_option,
                self._game_state_manager.heart_question_active,
            )
        elif self._game_state_manager.game_state == GameState.GAME_OVER:
            from ui.overlays import draw_game_over_overlay
            draw_game_over_overlay(
                self._screen,
                self._overlay_title_font,
                self._overlay_body_font,
                self._scoring_system.get_score(),
            )

        pygame.display.flip()

    def _render_sprite(self) -> None:
        """Render the player sprite group."""
        sprite_group = pygame.sprite.Group()
        sprite_group.add(self._player_car)
        sprite_group.draw(self._screen)

    def _update_speed_from_score(self) -> None:
        """Update max speed based on current score."""
        score = self._scoring_system.get_score()
        speed_increments = score // ScoringConstants.SPEED_INCREMENT_THRESHOLD
        new_max_speed = (
            ScoringConstants.BASE_SPEED
            + (speed_increments * ScoringConstants.SPEED_INCREMENT_PER_THRESHOLD)
        )
        self._player_car.set_max_speed(new_max_speed)

    def _reset_subsystems(self) -> None:
        """Reset all subsystems after a game restart."""
        self._boost_system.reset()
        self._gear_system.reset()
        self._oil_swerve.reset()
        if self._collision_handler:
            self._collision_handler.reset()
        self._selected_setting = 0
        self._target_steer = 0.0
        self._max_speed = self._player_car.max_speed

    def _cleanup(self) -> None:
        """Clean up resources on exit."""
        self._detector.stop_stream()
        cv2.destroyAllWindows()
        pygame.quit()
