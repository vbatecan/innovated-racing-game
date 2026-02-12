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
    MAX_FPS,
    OBSTACLE_FREQUENCY,
    STEERING_SENSITIVITY,
)


class Settings:
    def __init__(self):
        """
        Initialize runtime-tunable game settings.

        Loads defaults from config and sets up physics and control parameters
        used throughout the game loop.
        """
        self.car_speed = CAR_SPEED
        self.max_fps = MAX_FPS
        self.show_camera = True
        self.obstacle_frequency = OBSTACLE_FREQUENCY
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
        Compute the thumb raise the threshold for braking detection.
        """
        return 0.07 - (self.brake_sensitivity * 0.01)

    def increase_brake_sensitivity(self):
        """
        Make braking easier to trigger by raising sensitivity.
        """
        self.brake_sensitivity = min(self.brake_sensitivity + 1, 10)

    def decrease_brake_sensitivity(self):
        """
        Make braking harder to trigger by lowering sensitivity.
        """
        self.brake_sensitivity = max(self.brake_sensitivity - 1, 1)

    def increase_speed(self):
        """
        Increase the car speed setting within limits.
        """
        self.car_speed = min(self.car_speed + 1, 50)

    def decrease_speed(self):
        """
        Decrease the car speed setting within limits.
        """
        self.car_speed = max(self.car_speed - 1, 1)

    def toggle_camera(self):
        """
        Toggle whether the camera preview is shown.
        """
        self.show_camera = not self.show_camera

    def increase_fps(self):
        """
        Increase the max FPS setting using supported values.
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
        """
        try:
            idx = self._vals.index(self.max_fps)
            self.max_fps = self._vals[max(idx - 1, 0)]
        except ValueError:
            self.max_fps = 30

    def increase_obstacle_frequency(self):
        """
        Increase how often obstacles spawn (smaller gap).
        """
        self.obstacle_frequency += 1

    def decrease_obstacle_frequency(self):
        """
        Decrease how often obstacles spawn (larger gap).
        """
        if self.obstacle_frequency <= 1:
            return
        self.obstacle_frequency -= 1

    def increase_sensitivity(self):
        """
        Increase steering sensitivity within limits.
        """
        self.steering_sensitivity = min(self.steering_sensitivity + 0.1, 5.0)

    def decrease_sensitivity(self):
        """
        Decrease steering sensitivity within limits.
        """
        self.steering_sensitivity = max(self.steering_sensitivity - 0.1, 0.1)

    def increase_points_speed_increment(self, points):
        self.speed_bonus += points

    def decrease_points_speed_increment(self, deduct):
        self.speed_bonus -= deduct

    def draw_settings_menu(self, screen, font, settings, selected_index, options):
        """
        Render the in-game settings overlay.

        Draws a centered semi-transparent panel with the available options, highlights
        the currently selected item, and shows the current value for each setting.
        """
        overlay = pygame.Surface((400, 300))
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
    ) -> tuple[bool, bool, int | Any]:
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
                        self.decrease_sensitivity()
                    elif selected_setting == 5:
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
                        self.increase_sensitivity()
                    elif selected_setting == 5:
                        self.increase_brake_sensitivity()
        return running, selected_setting, show_settings
