"""Main game loop orchestration.

Centralizes the game loop logic that was previously in main()'s massive
while loop, delegating to specialized systems for state management,
input handling, physics, and rendering.
"""

from typing import Optional, TYPE_CHECKING
from collections import deque
import time
import tracemalloc
import logging
import pygame
import cv2
import config
from core.enums import GameState, ScoringConstants
from core.game_state import GameStateManager
from core.gear_system import GearSystem
from core.oil_swerve_physics import OilSwervePhysics
from core.collision_handler import CollisionHandler
from core.music_manager import MusicManager
from core.sound_manager import init_sound_manager
from input.key_mapper import KeyMapper
from input.steering_handler import SteeringHandler

if TYPE_CHECKING:
    from ui.homepage import HomePageScreen
    from ui.modern_homepage import ModernHomePage

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
        player_car,
        game_map,
        detector,
        settings,
        hud,
        game_hud,
        pause_menu,
        settings_menu,
        window_size: dict,
        homepage: "ModernHomePage",
        shop_screen: "HomePageScreen",
        car_manager = None,
        car_selection = None,
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
            car_manager: Optional CarManager for car selection system.
            car_selection: Optional CarSelectionUI for car selection menu.
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
        self._car_manager = car_manager
        self._car_selection = car_selection
        self._settings_menu = settings_menu
        self._window_size = window_size
        self._homepage = homepage
        self._shop_screen = shop_screen

        self._current_screen = "home"
        self._menu_running = True

        self._font = pygame.font.Font(None, config.FONT_SIZE)
        self._overlay_title_font = pygame.font.Font(
            None, max(40, config.FONT_SIZE * 2)
        )
        self._overlay_body_font = pygame.font.Font(
            None, max(30, config.FONT_SIZE + 10)
        )
        self._music_overlay_font = pygame.font.Font(None, max(28, config.FONT_SIZE + 4))

        from models.score import ScoringSystem
        from environment.question_manager import QuestionManager

        self._scoring_system = ScoringSystem(config.SCORING_CONFIG)
        self._question_manager = QuestionManager()

        self._game_state_manager: Optional[GameStateManager] = None
        self._gear_system = GearSystem()
        self._oil_swerve = OilSwervePhysics()
        self._collision_handler: Optional[CollisionHandler] = None
        self._key_mapper = KeyMapper()
        self._steering_handler = SteeringHandler()
        self._sound_manager = init_sound_manager(settings=self._settings)
        self._music_manager = MusicManager(settings=self._settings)

        self._running = True
        self._return_to_menu = False
        self._selected_setting = 0
        self._is_braking = False
        self._was_braking = False
        self._last_brake_sfx_ms = 0
        self._target_steer = 0.0
        self._max_speed = player_car.max_speed
        self._music_overlay_text = ""
        self._music_overlay_until_ms = 0
        self._run_score_cashed_out = False
        self._last_frame_score_for_speed = 0
        self._score_gain_for_speed_scaling = 0


        self._player_sprite_group = pygame.sprite.GroupSingle(self._player_car)

        self._cached_lane_count: Optional[int] = None
        self._cached_obstacle_frequency: Optional[int] = None

        self._debug_perf_enabled = bool(getattr(config, 'DEBUG_PERF', False))
        self._frame_times_ms = deque(maxlen=180)
        self._perf_log_interval_ms = 1000
        self._next_perf_log_ms = 0
        if self._debug_perf_enabled and not tracemalloc.is_tracing():
            tracemalloc.start()

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

        self._initialize_car_selection()
        self._setup_menu_callbacks()

        logger.info("Starting Game Loop...")
        logger.info("Controls: Use your hands visible to the camera.")
        logger.info("Press 'Esc' to open Settings.")

    def _setup_menu_callbacks(self) -> None:
        """Configure menu navigation callbacks for homepage buttons."""
        logger.info("Setting up menu callbacks...")
        def start_game() -> None:
            """Callback for start game button."""
            logger.info("Start game callback triggered")
            self._current_screen = "game"

        def go_to_shop() -> None:
            """Callback for shop button - show car shop."""
            logger.info("Go to shop callback triggered")
            self._current_screen = "shop"

        def go_to_settings() -> None:
            """Callback for settings button - show settings menu."""
            logger.info("Go to settings callback triggered")
            self._current_screen = "settings"

        logger.info("Calling set_callbacks on homepage...")
        self._homepage.set_callbacks({
            "start": start_game,
            "shop": go_to_shop,
            "settings": go_to_settings,
        })
        logger.info("Menu callbacks setup complete")

    def _run_menu_loop(self) -> bool:
        """Run the pre-game menu loop until game starts or user quits.

        Handles navigation between home, shop, and settings screens.

        Returns:
            True if game should start, False if user quit.
        """
        self._menu_running = True
        self._current_screen = "home"
        logger.info("Starting menu loop...")

        while self._menu_running:
            delta_time = self._clock.tick(120) / 1000.0
            self._sync_music_state()
            self._sound_manager.set_sfx_enabled(False)

            if self._current_screen == "home":
                if not self._process_home_screen(delta_time):
                    logger.info("Home screen returned False, exiting menu loop")
                    return False

            elif self._current_screen == "shop":
                if not self._process_shop_screen(delta_time):
                    logger.info("Shop screen returned False, exiting menu loop")
                    return False

            elif self._current_screen == "settings":
                if not self._process_settings_screen(delta_time):
                    logger.info("Settings screen returned False, exiting menu loop")
                    return False

            elif self._current_screen == "game":
                logger.info("Switching to game mode, exiting menu loop")
                self._menu_running = False

        logger.info("Menu loop complete, returning True")
        return True

    def _process_home_screen(self, delta_time: float) -> bool:
        """Process a frame of the home screen.

        Args:
            delta_time: Time elapsed since last frame in seconds.

        Returns:
            True to continue running, False to quit.
        """
        if hasattr(self._homepage, "set_player_info") and self._car_manager:
            self._homepage.set_player_info("Player", self._car_manager.credits)

        self._refresh_display_surface()
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.info("Quit event received")
                return False

            action = self._homepage.handle_event(event)
            if action and not (event.type == pygame.MOUSEBUTTONDOWN and getattr(event, "button", None) == 1):
                self._sound_manager.play_ui_click()
            if action == "quit":
                logger.info("Homepage returned quit action")
                return False

        self._homepage._mouse_pos = mouse_pos
        self._homepage._mouse_pressed = mouse_pressed
        
        self._homepage.update(delta_time)
        self._homepage.draw(self._screen)
        self._draw_music_status_overlay()
        self._draw_perf_overlay()
        pygame.display.flip()
        return True

    def _process_shop_screen(self, delta_time: float) -> bool:
        """Process a frame of the shop (car selection) screen.

        Args:
            delta_time: Time elapsed since last frame in seconds.

        Returns:
            True to continue running, False to quit.
        """
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            action = self._shop_screen.handle_event(event)
            if action and not (event.type == pygame.MOUSEBUTTONDOWN and getattr(event, "button", None) == 1):
                self._sound_manager.play_ui_click()
            if action == "quit":
                self._current_screen = "home"
            elif action == "start":
                self._current_screen = "game"
                self._menu_running = False

        if hasattr(self._shop_screen, '_mouse_pos'):
            self._shop_screen._mouse_pos = mouse_pos
        if hasattr(self._shop_screen, '_mouse_pressed'):
            self._shop_screen._mouse_pressed = mouse_pressed
        
        self._shop_screen.update(delta_time)
        self._shop_screen.draw(self._screen)
        self._draw_music_status_overlay()
        self._draw_perf_overlay()
        pygame.display.flip()
        return True

    def _process_settings_screen(self, delta_time: float) -> bool:
        """Process a frame of the settings menu screen.

        Args:
            delta_time: Time elapsed since last frame in seconds.

        Returns:
            True to continue running, False to quit.
        """
        mouse_pos = pygame.mouse.get_pos()
        if hasattr(self._settings_menu, "bind_settings"):
            self._settings_menu.bind_settings(self._settings)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            result = self._settings_menu.handle_input(event, mouse_pos)
            if result and result.get("action") == "changed":
                self._settings_menu.apply_to_game(self._settings)
            if result and result.get("action") == "close":
                self._current_screen = "home"

        self._screen.fill((10, 12, 24))

        self._settings_menu.update(mouse_pos)
        self._settings_menu.draw(self._screen)
        self._draw_music_status_overlay()
        self._draw_perf_overlay()
        pygame.display.flip()
        return True

    def run(self) -> None:
        """Execute the main game loop until exit.

        First runs the pre-game menu loop, then proceeds to the actual gameplay loop.
        Performs cleanup after the loop terminates.

        Raises:
            RuntimeError: If initialize() was not called before run().
        """
        if self._game_state_manager is None:
            raise RuntimeError("GameLoop.initialize() must be called before run()")

        logger.info("GameLoop.run() started")

        should_quit = False
        while not should_quit:
            logger.info("Starting menu loop...")
            if not self._run_menu_loop():
                logger.info("User quit during menu, cleaning up...")
                should_quit = True
                break

            logger.info("Menu loop complete, starting gameplay...")

            # Show startup splash for 5 seconds before gameplay begins.
            try:
                self._show_startup_splash(duration_ms=5000)
            except Exception:
                logger.exception("Failed to show startup splash; continuing to gameplay")

            if hasattr(self._player_car, "refresh_configuration"):
                self._player_car.refresh_configuration()

            logger.info("Starting detector stream...")
            self._detector.start_stream()
            logger.info("Detector stream started")

            self._running = True
            self._return_to_menu = False
            self._run_score_cashed_out = False
            self._reset_speed_scaling_progress()

            logger.info("Entering main gameplay loop...")
            while self._running:
                self._process_frame()

            self._cash_out_run_score_to_credits()

            if self._return_to_menu:
                logger.info("Returning to menu...")
                self._detector.stop_stream()
                self._reset_subsystems()
                self._game_state_manager.reset_run_state()
                self._pause_menu.hide()
                self._return_to_menu = False
            else:
                logger.info("User quit game, exiting...")
                should_quit = True

        self._cleanup()

    def _process_frame(self) -> None:
        """Process a single complete game frame.

        Orchestrates the frame lifecycle: event handling, state updates,
        gameplay logic, rendering, and scoring. Applies frame rate limiting
        at the end of each frame.
        """
        self._is_braking = False
        frame_start = time.perf_counter()

        self._detector.set_require_two_hands(
            self._game_state_manager.game_state == GameState.PLAYING
        )
        self._sync_runtime_settings()
        self._handle_events()
        self._sync_sfx_state()
        self._sync_music_state()

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

        if self._game_state_manager.game_state == GameState.GAME_OVER:
            self._cash_out_run_score_to_credits()

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
        self._check_and_handle_car_unlocks()
        self._record_perf_sample(frame_start)
        self._clock.tick(self._settings.max_fps)

    def _sync_sfx_state(self) -> None:
        """Enable SFX only during active gameplay and keep menus/settings silent."""
        gameplay_active = (
            not self._menu_running
            and self._game_state_manager.game_state == GameState.PLAYING
            and not self._settings.visible
            and not self._pause_menu.visible
        )
        self._sound_manager.set_sfx_enabled(gameplay_active)

    def _sync_music_state(self) -> None:
        """Pause music in pause/settings/menu contexts and resume during gameplay."""
        not_playing_state = self._game_state_manager.game_state != GameState.PLAYING
        should_pause = (
            self._menu_running
            or self._pause_menu.visible
            or self._settings.visible
            or not_playing_state
        )
        self._music_manager.set_context_paused(should_pause)
        self._music_manager.update()

    def _show_startup_splash(self, duration_ms: int = 3000) -> None:
        """Display a startup splash image centered on screen for duration_ms.

        If resources/splash_start.jpg exists it will be displayed; otherwise
        this function is a no-op.
        """
        import os
        import pygame
        splash_path = os.path.join('resources', 'splash_start.jpg')
        if not os.path.exists(splash_path):
            return

        try:
            img = pygame.image.load(splash_path)
            # Scale to fit screen while preserving aspect
            screen_w, screen_h = self._screen.get_size()
            iw, ih = img.get_size()
            scale = min(screen_w / iw, screen_h / ih)
            new_w = int(iw * scale)
            new_h = int(ih * scale)
            img = pygame.transform.smoothscale(img, (new_w, new_h))

            x = (screen_w - new_w) // 2
            y = (screen_h - new_h) // 2

            start_ms = pygame.time.get_ticks()
            while pygame.time.get_ticks() - start_ms < int(duration_ms):
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self._running = False
                        return
                self._screen.fill((0, 0, 0))
                self._screen.blit(img, (x, y))
                pygame.display.flip()
                self._clock.tick(30)
        except Exception:
            logger.exception('Error displaying startup splash')

    def _handle_events(self) -> None:
        """Process all Pygame events for the current frame.

        Dispatches events to appropriate handlers based on current game state
        and UI visibility. Handles quit events, car selection input, pause menu,
        question answering, game over restart, settings menu, and gameplay input.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
                continue

            if (
                event.type == pygame.KEYDOWN
                and not self._menu_running
                and not self._pause_menu.visible
                and not self._settings.visible
                and self._game_state_manager.game_state == GameState.PLAYING
            ):
                music_status = self._music_manager.handle_keydown(event.key)
                if music_status is not None:
                    self._show_music_status_overlay(music_status)
                    continue

            if self._car_selection and self._car_selection.visible:
                if self._car_selection.handle_event(event):
                    continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                self._toggle_debug_perf()
                continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self._game_state_manager.game_state == GameState.GAME_OVER and self._car_selection:
                    self._car_selection.open()
                    continue
                self._handle_escape()
                continue

            if self._game_state_manager.game_state == GameState.QUESTION:
                self._handle_question_key(event)
                continue

            if self._game_state_manager.game_state == GameState.GAME_OVER:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self._cash_out_run_score_to_credits()
                        self._game_state_manager.reset_run_state()
                        self._reset_subsystems()
                        self._restart_camera_stream()
                        self._run_score_cashed_out = False
                    elif event.key in (pygame.K_l, pygame.K_b):
                        self._cash_out_run_score_to_credits()
                        self._return_to_menu = True
                        self._running = False
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
        """Handle keyboard input during question state.

        Maps numeric key presses to answer option selection.

        Args:
            event: Pygame event to process.
        """
        if event.type == pygame.KEYDOWN:
            selected = self._key_mapper.get_option_index(event.key)
            if selected is not None and self._game_state_manager.active_question is not None:
                if selected < self._game_state_manager.active_question.answer_count:
                    self._game_state_manager.resolve_question_answer(
                        selected
                    )

    def _handle_settings_event(self, event: pygame.event.Event) -> None:
        """Handle input when settings menu is visible.

        Processes settings menu interactions and applies changes to game settings.

        Args:
            event: Pygame event to process.
        """
        mouse_pos = pygame.mouse.get_pos()
        if hasattr(self._settings_menu, "bind_settings"):
            self._settings_menu.bind_settings(self._settings)
        result = self._settings_menu.handle_input(event, mouse_pos)
        if result and result.get("action") == "changed":
            self._settings_menu.apply_to_game(self._settings)
        if result and result.get("action") == "close":
            self._settings.visible = False

    def _handle_gameplay_event(self, event: pygame.event.Event) -> None:
        """Handle normal gameplay input events.

        Processes car selection toggle and settings menu events during active gameplay.

        Args:
            event: Pygame event to process.
        """

        if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
            if self._car_selection and not self._car_selection.visible:
                self._car_selection.open()
                return

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
        """Process pause menu updates and rendering.

        Handles pause menu input, updates button states, processes selection results,
        and renders the paused game scene with the pause menu overlay.
        """
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
        self._draw_music_status_overlay()
        self._draw_perf_overlay()
        pygame.display.flip()

    def _process_pause_result(self, result: Optional[str]) -> None:
        """Process pause menu selection result.

        Executes actions based on pause menu selection: resume game, restart run,
        open settings, back to homepage, or quit the application.

        Args:
            result: Selected menu option string, or None if no selection.
        """
        if result == "Resume":
            self._pause_menu.hide()
        elif result == "Restart":
            self._game_state_manager.reset_run_state()
            self._reset_subsystems()
            self._restart_camera_stream()
            self._run_score_cashed_out = False
            self._pause_menu.hide()
        elif result == "Settings":
            self._pause_menu.hide()
            self._settings.visible = True
        elif result == "Back to Homepage":
            self._return_to_menu = True
            self._running = False
        elif result == "Quit":
            self._running = False

    def _process_question_input(self) -> None:
        """Process hand gesture input during question state.

        Handles swipe gestures for option navigation and selection gesture
        for confirming answers when input cooldown has elapsed.
        """
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
        """Update gameplay state for the current frame.

        Processes detector input, handles braking and steering, manages gear shifting,
        applies oil swerve physics, updates player car physics, and updates the game map state.
        """
        self._detector.brake_threshold = self._settings.get_brake_threshold()

        frame = self._detector.get_frame()
        cv2.waitKey(1)
        camera_enabled = self._settings.show_camera and self._settings.camera_mode != "Off"
        if camera_enabled and frame is not None:
            self._game_hud.set_camera_frame(frame)
        self._game_hud.set_camera_visibility(camera_enabled)
        if hasattr(self._game_hud, "camera_size"):
            self._game_hud.camera_size = self._settings.get_camera_preview_size()

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

        if self._settings.steering_assist:
            self._target_steer *= 0.82

        self._target_steer = max(-2.0, min(2.0, self._target_steer))

        if self._settings.auto_brake_assist and abs(self._target_steer) > 1.15 and self._player_car.current_speed > (self._max_speed * 0.45):
            self._is_braking = True
        self._update_brake_audio()
        self._player_car.turn(
            max(-2, min(self._target_steer, 2)),
            self._player_car.turn_smoothing
        )

        acceleration = self._settings.ACCELERATION * self._gear_system.get_acceleration_ratio()
        acceleration *= self._settings.get_difficulty_acceleration_multiplier()
        self._max_speed = self._player_car.max_speed * self._gear_system.get_speed_ratio()

        if hasattr(self._player_car, "set_visual_cues"):
            self._player_car.set_visual_cues(self._is_braking)

        self._player_car.update(
            steering=self._target_steer,
            is_braking=self._is_braking,
            max_speed=self._max_speed,
            acceleration=acceleration,
            friction=self._settings.FRICTION,
            brake_strength=self._settings.BRAKE_STRENGTH,
            screen_width=self._window_size["width"],
        )

        self._sound_manager.update_engine(self._player_car.current_speed / self._max_speed)

        self._game_map.speed = float(self._player_car.current_speed)
        self._game_map.update_score(self._scoring_system.get_score())
        self._game_map.update(is_braking=self._is_braking)

        self._collision_handler.clamp_to_road()

        collision_result = self._collision_handler.check_and_resolve_all()

        if (
            collision_result.obstacle_hit
            or collision_result.brake_hit
            or collision_result.crack_hit
            or collision_result.oil_hit
        ):
            self._sound_manager.play_sfx("environment/collision")

    def _update_brake_audio(self) -> None:
        """Play a brake SFX when braking starts."""
        now_ms = pygame.time.get_ticks()
        started_braking = self._is_braking and not self._was_braking

        if started_braking and now_ms - self._last_brake_sfx_ms >= 300:
            self._sound_manager.play_sfx("vehicle/brake", volume=0.5)
            self._last_brake_sfx_ms = now_ms

        self._was_braking = self._is_braking


    def _refresh_display_surface(self) -> None:
        """Synchronize cached screen reference with the active display surface.

        Fullscreen toggles recreate the SDL display surface. Continuing to draw
        to the old cached surface can trigger blit errors because the stale
        surface may be locked or otherwise invalid for rendering.
        """
        current_surface = pygame.display.get_surface()
        if current_surface is not None and current_surface is not self._screen:
            self._screen = current_surface

    def _render(self) -> None:
        """Render the complete game frame.

        Synchronizes display surface, draws game world, updates HUD with current
        metrics, renders overlays for question/game over states, and draws car
        selection UI if visible.
        """
        self._refresh_display_surface()
        self._game_map.draw(self._screen)
        self._render_sprite()

        display_currency = self._get_display_currency_value()

        fps = self._clock.get_fps()
        self._hud.update_from_game(
            self._player_car,
            self._detector,
            gear=str(self._gear_system.current_gear),
            score=display_currency,
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
            score=display_currency,
            lives=int(self._game_state_manager.lives),
            distance=self._scoring_system.get_distance(),
            gear=self._gear_system.current_gear,
            is_braking=self._is_braking,
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
                display_currency,
            )

        if self._car_selection:
            car_selection_dt = 1.0 / max(1, int(self._settings.max_fps))
            self._car_selection.update(car_selection_dt)
            self._car_selection.draw(self._screen)

        self._draw_music_status_overlay()
        self._draw_perf_overlay()
        pygame.display.flip()

    def _show_music_status_overlay(self, text: str, duration_ms: int = 2200) -> None:
        self._music_overlay_text = str(text).strip()
        self._music_overlay_until_ms = pygame.time.get_ticks() + int(duration_ms)

    def _draw_music_status_overlay(self) -> None:
        if not self._music_overlay_text:
            return
        if pygame.time.get_ticks() > self._music_overlay_until_ms:
            self._music_overlay_text = ""
            self._music_overlay_until_ms = 0
            return

        text_surface = self._music_overlay_font.render(self._music_overlay_text, True, (248, 245, 225))
        width = text_surface.get_width() + 24
        height = text_surface.get_height() + 14

        x = (self._screen.get_width() - width) // 2
        y = max(16, self._screen.get_height() - height - 22)
        bg_rect = pygame.Rect(x, y, width, height)

        pygame.draw.rect(self._screen, (10, 12, 20), bg_rect, border_radius=10)
        pygame.draw.rect(self._screen, (220, 194, 124), bg_rect, 2, border_radius=10)
        self._screen.blit(text_surface, (x + 12, y + 7))

    def _render_sprite(self) -> None:
        """Render the player car sprite to the screen."""
        self._player_sprite_group.draw(self._screen)

    def _update_speed_from_score(self) -> None:
        """Adjust maximum speed using score gains accumulated per frame.

        Speed scaling is driven by positive score delta each frame so only score
        increases contribute to speed growth.
        """
        score = max(0, int(self._scoring_system.get_score()))
        frame_score_gain = score - self._last_frame_score_for_speed
        if frame_score_gain > 0:
            self._score_gain_for_speed_scaling += frame_score_gain

        self._last_frame_score_for_speed = score

        speed_increments = (
            self._score_gain_for_speed_scaling // ScoringConstants.SPEED_INCREMENT_THRESHOLD
        )
        new_max_speed = (
            ScoringConstants.BASE_SPEED
            + (speed_increments * ScoringConstants.SPEED_INCREMENT_PER_THRESHOLD)
        )
        self._player_car.set_max_speed(new_max_speed)

    def _reset_speed_scaling_progress(self) -> None:
        """Reset per-frame score tracking used by speed scaling."""
        current_score = max(0, int(self._scoring_system.get_score()))
        self._last_frame_score_for_speed = current_score
        self._score_gain_for_speed_scaling = current_score

    def _reset_subsystems(self) -> None:
        """Reset all gameplay subsystems after a game restart.

        Clears gear state, oil swerve effects, collision handler, and steering
        targets to prepare for a fresh run.
        """
        self._gear_system.reset()
        self._oil_swerve.reset()
        if self._collision_handler:
            self._collision_handler.reset()
        self._selected_setting = 0
        self._was_braking = False
        self._last_brake_sfx_ms = 0
        self._target_steer = 0.0
        self._reset_speed_scaling_progress()
        self._max_speed = self._player_car.max_speed

    def _restart_camera_stream(self) -> None:
        """Restart the detector stream so camera input resets with a run restart."""
        if hasattr(self._game_hud, "set_camera_frame"):
            self._game_hud.set_camera_frame(None)

        try:
            if hasattr(self._detector, "restart_stream"):
                self._detector.restart_stream()
            else:
                self._detector.stop_stream()
                self._detector.start_stream()
        except Exception:
            logger.exception("Failed to restart detector stream during run restart")

    def _cash_out_run_score_to_credits(self) -> None:
        """Convert final run score to credits once when leaving gameplay."""
        if self._run_score_cashed_out or not self._car_manager:
            return

        if self._game_state_manager is None or self._game_state_manager.game_state != GameState.GAME_OVER:
            return

        run_currency = self._get_display_currency_value()
        if run_currency > 0:
            gained = self._car_manager.add_credits(run_currency)
            logger.info("Run cashout applied: +%s CR (currency=%s)", gained, run_currency)

        self._run_score_cashed_out = True

    def _get_display_currency_value(self) -> int:
        """Return the currency value that should be displayed on HUD panels."""
        return max(0, int(self._scoring_system.get_distance()))

    def _initialize_car_selection(self) -> None:
        """Configure car selection UI callbacks.

        Sets up handlers for car selection and menu closure events.
        Skips initialization if car selection UI or manager is not available.
        """
        if not self._car_selection or not self._car_manager:
            return

        def on_car_selected(car):
            """Handle car selection event."""
            logger.info(f"Car selected: {car.name}")

        def on_car_selection_closed():
            """Handle car selection menu closure."""
            pass

        self._car_selection.selected_callback = on_car_selected
        self._car_selection.close_callback = on_car_selection_closed

    def _check_and_handle_car_unlocks(self) -> None:
        """Evaluate and notify newly unlocked cars based on current score.

        Updates the best score in the car manager and triggers unlock notifications
        in the car selection UI when new vehicles become available.
        """
        if not self._car_manager or not self._car_selection:
            return

        current_score = self._scoring_system.get_score()
        newly_unlocked = self._car_manager.update_best_score(current_score)

        if newly_unlocked:
            logger.info(f"New cars unlocked: {[car.name for car in newly_unlocked]}")
            self._car_selection.show_new_unlocks(newly_unlocked)

    def _sync_runtime_settings(self) -> None:
        """Apply runtime settings only when values change to reduce per-frame work."""
        self._game_map.speed = self._settings.car_speed

        lane_count = int(self._settings.lane_count)
        if lane_count != self._cached_lane_count:
            self._game_map.set_lane_count(lane_count)
            self._cached_lane_count = lane_count

        difficulty_spawn_multiplier = self._settings.get_difficulty_obstacle_multiplier()
        obstacle_setting = max(0.25, float(self._settings.obstacle_frequency) * difficulty_spawn_multiplier)
        obstacle_frequency = int((self._settings.max_fps * 2) / obstacle_setting)
        if obstacle_frequency != self._cached_obstacle_frequency:
            self._game_map.obstacle_frequency = obstacle_frequency
            self._cached_obstacle_frequency = obstacle_frequency

    def _toggle_debug_perf(self) -> None:
        self._debug_perf_enabled = not self._debug_perf_enabled
        if self._debug_perf_enabled and not tracemalloc.is_tracing():
            tracemalloc.start()
        state = "enabled" if self._debug_perf_enabled else "disabled"
        logger.info(f"Performance debug {state}")

    def _record_perf_sample(self, frame_start: float) -> None:
        if not self._debug_perf_enabled:
            return

        frame_ms = (time.perf_counter() - frame_start) * 1000.0
        self._frame_times_ms.append(frame_ms)

        now_ms = pygame.time.get_ticks()
        if now_ms < self._next_perf_log_ms:
            return
        self._next_perf_log_ms = now_ms + self._perf_log_interval_ms

        avg_ms = sum(self._frame_times_ms) / max(1, len(self._frame_times_ms))
        peak_ms = max(self._frame_times_ms) if self._frame_times_ms else frame_ms
        mem_current_mb = 0.0
        mem_peak_mb = 0.0
        if tracemalloc.is_tracing():
            mem_current, mem_peak = tracemalloc.get_traced_memory()
            mem_current_mb = mem_current / (1024 * 1024)
            mem_peak_mb = mem_peak / (1024 * 1024)

        logger.info(
            "PERF | fps=%.1f frame_avg=%.2fms frame_peak=%.2fms mem=%.1fMB peak=%.1fMB",
            self._clock.get_fps(),
            avg_ms,
            peak_ms,
            mem_current_mb,
            mem_peak_mb,
        )

    def _draw_perf_overlay(self) -> None:
        if not self._debug_perf_enabled:
            return

        avg_ms = sum(self._frame_times_ms) / max(1, len(self._frame_times_ms)) if self._frame_times_ms else 0.0
        mem_text = "mem n/a"
        if tracemalloc.is_tracing():
            mem_current, mem_peak = tracemalloc.get_traced_memory()
            mem_text = f"mem {mem_current / (1024 * 1024):.1f}/{mem_peak / (1024 * 1024):.1f}MB"

        text = f"DBG fps {self._clock.get_fps():.1f} | frame {avg_ms:.2f}ms | {mem_text}"
        surf = self._font.render(text, True, (255, 230, 150))
        pad = 10
        bg = pygame.Rect(pad - 6, pad - 4, surf.get_width() + 12, surf.get_height() + 8)
        pygame.draw.rect(self._screen, (0, 0, 0), bg, border_radius=6)
        pygame.draw.rect(self._screen, (255, 230, 150), bg, 1, border_radius=6)
        self._screen.blit(surf, (pad, pad))

    def _cleanup(self) -> None:
        """Release all resources on game exit.

        Stops the detector stream, destroys OpenCV windows, and quits Pygame.
        """
        self._music_manager.stop()
        self._detector.stop_stream()
        cv2.destroyAllWindows()
        pygame.quit()






















