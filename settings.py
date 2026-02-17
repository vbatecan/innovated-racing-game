from pygame.event import Event
from typing import Any
import cv2
import pygame

from config import (
    ACCELERATION,
    AVAILABLE_FPS,
    BRAKE_SENSITIVITY,
    BRAKE_STRENGTH,
    CAR_SPEED,
    FRICTION,
    LANE_COUNT,
    MAX_LANE_COUNT,
    MAX_FPS,
    MIN_LANE_COUNT,
    OBSTACLE_FREQUENCY,
    STEERING_SENSITIVITY,
)


class Settings:
    def __init__(self):
        """
        Initialize runtime-tunable game settings.

        Returns:
            None: Initializes mutable runtime settings from configuration defaults.
        """
        self.car_speed = CAR_SPEED
        self.max_fps = MAX_FPS
        self.show_camera = True
        self.obstacle_frequency = OBSTACLE_FREQUENCY
        self.lane_count = LANE_COUNT
        self.steering_sensitivity = STEERING_SENSITIVITY
        self._vals = AVAILABLE_FPS

        # Physics
        self.ACCELERATION = ACCELERATION
        self.FRICTION = FRICTION
        self.BRAKE_STRENGTH = BRAKE_STRENGTH
        self.brake_sensitivity = BRAKE_SENSITIVITY  # 1 (Hard) to 10 (Easy)

        # This
        self.visible = False

        # Scoring system
        self.speed_bonus = 50  # Every n points, increase speed by 1
        self.car_collision_deduction_pts = 100

    def get_brake_threshold(self):
        """
        Convert brake sensitivity into a thumb-raise threshold for gesture braking.

        Returns:
            float: Gesture threshold value used by the controller.
        """
        return 0.07 - (self.brake_sensitivity * 0.01)

    def increase_brake_sensitivity(self):
        """
        Make braking easier to trigger by raising sensitivity.

        Returns:
            None: Increases `brake_sensitivity` within allowed bounds.
        """
        self.brake_sensitivity = min(self.brake_sensitivity + 1, 10)

    def decrease_brake_sensitivity(self):
        """
        Make braking harder to trigger by lowering sensitivity.

        Returns:
            None: Decreases `brake_sensitivity` within allowed bounds.
        """
        self.brake_sensitivity = max(self.brake_sensitivity - 1, 1)

    def increase_speed(self):
        """
        Increase the car speed setting within limits.

        Returns:
            None: Increases `car_speed` within allowed bounds.
        """
        self.car_speed = min(self.car_speed + 1, 50)

    def decrease_speed(self):
        """
        Decrease the car speed setting within limits.

        Returns:
            None: Decreases `car_speed` within allowed bounds.
        """
        self.car_speed = max(self.car_speed - 1, 1)

    def toggle_camera(self):
        """
        Toggle whether the camera preview is shown.

        Returns:
            None: Flips `show_camera`.
        """
        self.show_camera = not self.show_camera

    def increase_fps(self):
        """
        Increase the max FPS setting using supported values.

        Returns:
            None: Moves to the next supported FPS value.
        """
        vals = [30, 60, 120]
        try:
            idx = vals.index(self.max_fps)
            self.max_fps = vals[min(idx + 1, len(vals) - 1)]
        except ValueError:
            self.max_fps = 30

    def decrease_fps(self):
        """
        Decrease the max FPS setting using supported values.

        Returns:
            None: Moves to the previous supported FPS value.
        """
        try:
            idx = self._vals.index(self.max_fps)
            self.max_fps = self._vals[max(idx - 1, 0)]
        except ValueError:
            self.max_fps = 30

    def increase_obstacle_frequency(self):
        """
        Increase how often obstacles spawn (smaller gap).

        Returns:
            None: Increments obstacle frequency control value.
        """
        self.obstacle_frequency += 1

    def decrease_obstacle_frequency(self):
        """
        Decrease how often obstacles spawn (larger gap).

        Returns:
            None: Decrements obstacle frequency control value when possible.
        """
        if self.obstacle_frequency <= 1:
            return
        self.obstacle_frequency -= 1

    def increase_lane_count(self):
        """
        Increase the number of road lanes within limits.

        Returns:
            None: Increases `lane_count` within configured bounds.
        """
        self.lane_count = min(self.lane_count + 1, MAX_LANE_COUNT)

    def decrease_lane_count(self):
        """
        Decrease the number of road lanes within limits.

        Returns:
            None: Decreases `lane_count` within configured bounds.
        """
        self.lane_count = max(self.lane_count - 1, MIN_LANE_COUNT)

    def increase_sensitivity(self):
        """
        Increase steering sensitivity within limits.

        Returns:
            None: Increases steering sensitivity within allowed bounds.
        """
        self.steering_sensitivity = min(self.steering_sensitivity + 0.1, 5.0)

    def decrease_sensitivity(self):
        """
        Decrease steering sensitivity within limits.

        Returns:
            None: Decreases steering sensitivity within allowed bounds.
        """
        self.steering_sensitivity = max(self.steering_sensitivity - 0.1, 0.1)

    def increase_points_speed_increment(self, points):
        """
        Increase the score interval used to grant speed bonuses.

        Args:
            points (int): Amount added to `speed_bonus`.

        Returns:
            None: Updates score threshold for speed bonus changes.
        """
        self.speed_bonus += points

    def decrease_points_speed_increment(self, deduct):
        """
        Decrease the score interval used to grant speed bonuses.

        Args:
            deduct (int): Amount subtracted from `speed_bonus`.

        Returns:
            None: Updates score threshold for speed bonus changes.
        """
        self.speed_bonus -= deduct

    def draw_settings_menu(self, screen, font, settings, selected_index, options):
        """
        Render the in-game settings overlay.

        Args:
            screen (pygame.Surface): Main display surface.
            font (pygame.font.Font): Font used to render menu text.
            settings (Settings): Current mutable settings instance.
            selected_index (int): Selected menu row index.
            options (list[str]): Ordered settings labels to display.

        Returns:
            None: Draws directly to the screen surface.
        """
        overlay_width = 400
        overlay_height = max(300, 140 + len(options) * 40)
        overlay = pygame.Surface((overlay_width, overlay_height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)

        screen_rect = screen.get_rect()
        overlay_rect = overlay.get_rect(center=screen_rect.center)

        screen.blit(overlay, overlay_rect)

        title = font.render("SETTINGS", True, (255, 255, 255))
        screen.blit(
            title, (overlay_rect.centerx - title.get_width() // 2, overlay_rect.y + 20)
        )

        for i, option in enumerate(options):
            color = (255, 255, 0) if i == selected_index else (255, 255, 255)

            value_text = ""
            if option == "Car Speed":
                value_text = str(settings.car_speed)
            elif option == "Max FPS":
                value_text = str(settings.max_fps)
            elif option == "Show Camera":
                value_text = "ON" if settings.show_camera else "OFF"
            elif option == "Obstacle Freq":
                value_text = str(settings.obstacle_frequency)
            elif option == "Lane Count":
                value_text = str(settings.lane_count)
            elif option == "Sensitivity":
                value_text = f"{settings.steering_sensitivity:.1f}"
            elif option == "Brake Sens":
                value_text = str(settings.brake_sensitivity)

            text = font.render(f"{option}: {value_text}", True, color)

            # Center the text in the overlay
            text_rect = text.get_rect(
                center=(overlay_rect.centerx, overlay_rect.y + 80 + i * 40)
            )
            screen.blit(text, text_rect)

        hint = font.render("Press P to Close", True, (150, 150, 150))
        screen.blit(
            hint,
            (overlay_rect.centerx - hint.get_width() // 2, overlay_rect.bottom - 40),
        )

    def handle_event(
        self,
        event: Event,
        running: bool,
        selected_setting: int | Any,
        setting_options: list[str],
        show_settings: bool,
    ) -> tuple[bool, int | Any, bool]:
        """
        Process input for game and settings navigation.

        Args:
            event (Event): Current pygame event to process.
            running (bool): Existing game running state.
            selected_setting (int | Any): Current selected settings menu index.
            setting_options (list[str]): Menu options used for index wrapping.
            show_settings (bool): Current visibility of settings menu.

        Returns:
            tuple[bool, int | Any, bool]: Updated `(running, selected_setting, show_settings)`.
        """
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_p:
                show_settings = not show_settings
                if not show_settings and not self.show_camera:
                    cv2.destroyAllWindows()

            if show_settings:
                if event.key == pygame.K_UP:
                    selected_setting = (selected_setting - 1) % len(setting_options)
                elif event.key == pygame.K_DOWN:
                    selected_setting = (selected_setting + 1) % len(setting_options)
                elif event.key == pygame.K_LEFT:
                    if selected_setting == 0:
                        self.decrease_speed()
                    elif selected_setting == 1:
                        self.decrease_fps()
                    elif selected_setting == 2:
                        self.toggle_camera()
                    elif selected_setting == 3:
                        self.decrease_obstacle_frequency()
                    elif selected_setting == 4:
                        self.decrease_lane_count()
                    elif selected_setting == 5:
                        self.decrease_sensitivity()
                    elif selected_setting == 6:
                        self.decrease_brake_sensitivity()
                elif event.key == pygame.K_RIGHT:
                    if selected_setting == 0:
                        self.increase_speed()
                    elif selected_setting == 1:
                        self.increase_fps()
                    elif selected_setting == 2:
                        self.toggle_camera()
                    elif selected_setting == 3:
                        self.increase_obstacle_frequency()
                    elif selected_setting == 4:
                        self.increase_lane_count()
                    elif selected_setting == 5:
                        self.increase_sensitivity()
                    elif selected_setting == 6:
                        self.increase_brake_sensitivity()
        return running, selected_setting, show_settings
