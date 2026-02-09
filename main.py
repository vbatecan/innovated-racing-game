import logging
from typing import Any, Tuple

import cv2
import pygame
import os

from pygame.event import Event
from pygame.key import ScancodeWrapper

import config

from config import WINDOW_SIZE, FONT_SIZE, MAX_FPS, SHOW_CAMERA
from car import Car
from controller import Controller
from map import Map
from settings import Settings

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/main.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def draw_settings_menu(screen, font, settings, selected_index, options):
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
        hint, (overlay_rect.centerx - hint.get_width() // 2, overlay_rect.bottom - 40)
    )


def main():
    """
    Initialize the game and run the main loop.

    Sets up Pygame, the player car, map, controller, and settings menu, then
    processes input, updates game state, and renders each frame until exit.
    """
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE["width"], WINDOW_SIZE["height"]))
    pygame.display.set_caption("Hand Gesture Racing Game")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, config.FONT_SIZE)

    settings = Settings()
    settings.show_camera = SHOW_CAMERA
    game_map = Map(WINDOW_SIZE)

    start_x = WINDOW_SIZE["width"] // 2
    start_y = WINDOW_SIZE["height"] - 240
    player_car = Car(start_x, start_y)

    sprite_group = pygame.sprite.Group()
    sprite_group.add(player_car)

    detector = Controller()
    detector.start_stream()

    running = True
    print("Starting Game Loop...")
    print("Controls: Use your hands visible to the camera.")
    print("Press 'S' to open Settings.")
    selected_setting = 0

    while running:
        # 1. Provide settings to map
        game_map.speed = settings.car_speed
        game_map.obstacle_frequency = int(
            settings.max_fps / settings.obstacle_frequency
        )

        for event in pygame.event.get():
            running, selected_setting, show_settings = handle_event(event, running, selected_setting,
                                                                    config.SETTING_OPTIONS,
                                                                    settings, settings.visible)
            settings.visible = show_settings

        if not settings.visible:
            detector.brake_threshold = settings.get_brake_threshold()

            frame = detector.get_frame()
            if settings.show_camera and frame is not None:
                cv2.imshow("Hand Tracker (Press 'S' for Settings)", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    pass
            elif not settings.show_camera:
                pass

            is_breaking = detector.breaking

            keys = pygame.key.get_pressed()
            if keys[pygame.K_DOWN]:
                is_breaking = True

            target_steer = detector.steer * settings.steering_sensitivity
            target_steer, turn = steer(keys, settings.steering_sensitivity, target_steer)
            player_car.turn(target_steer)

            player_car.update(
                steering=target_steer,
                is_braking=is_breaking,
                max_speed=settings.car_speed,
                acceleration=settings.ACCELERATION,
                friction=settings.FRICTION,
                brake_strength=settings.BRAKE_STRENGTH,
                screen_width=WINDOW_SIZE["width"],
            )

            game_map.speed = int(player_car.current_speed)
            game_map.update()

            road_min_x, road_max_x = game_map.get_road_borders()
            if player_car.rect.left < road_min_x or player_car.rect.right > road_max_x:
                player_car.rect.center = (
                    WINDOW_SIZE["width"] // 2,
                    WINDOW_SIZE["height"] - 120,
                )
                player_car.velocity_x = 0

            if pygame.sprite.spritecollide(player_car, game_map.obstacles, True):
                player_car.rect.center = (
                    WINDOW_SIZE["width"] // 2,
                    WINDOW_SIZE["height"] - 120,
                )
                player_car.velocity_x = 0

        # Drawing
        game_map.draw(screen)
        sprite_group.draw(screen)

        # Display Info
        steer_text = font.render(f"Steer: {detector.steer:.2f}", True, (255, 255, 255))
        screen.blit(steer_text, (10, 10))

        fps = clock.get_fps()
        fps_text = font.render(
            f"FPS: {int(fps)} / {settings.max_fps}", True, (0, 255, 0)
        )
        screen.blit(fps_text, (10, 50))

        obs_text = font.render(
            f"Obs Freq: {settings.obstacle_frequency}", True, (200, 200, 200)
        )
        screen.blit(obs_text, (10, 90))

        if settings.visible:
            draw_settings_menu(
                screen, font, settings, selected_setting, config.SETTING_OPTIONS
            )

        pygame.display.flip()
        clock.tick(settings.max_fps)

    detector.stop_stream()
    cv2.destroyAllWindows()
    pygame.quit()


def steer(keys: ScancodeWrapper, steering_sensitivity, target_steer: float) -> Tuple[float, str]:
    turn = "CENTER"
    if keys[pygame.K_LEFT]:
        target_steer = -1.0 * steering_sensitivity
        turn = "LEFT"
    if keys[pygame.K_RIGHT]:
        target_steer = 1.0 * steering_sensitivity
        turn = "RIGHT"
    return target_steer, turn


def handle_event(event: Event, running: bool, selected_setting: int | Any, setting_options: list[str],
                 settings: Settings, show_settings: bool) -> tuple[bool, bool, int | Any]:
    if event.type == pygame.QUIT:
        running = False

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            running = False
        elif event.key == pygame.K_p:
            show_settings = not show_settings
            if not show_settings and not settings.show_camera:
                cv2.destroyAllWindows()

        if show_settings:
            if event.key == pygame.K_UP:
                selected_setting = (selected_setting - 1) % len(setting_options)
            elif event.key == pygame.K_DOWN:
                selected_setting = (selected_setting + 1) % len(setting_options)
            elif event.key == pygame.K_LEFT:
                if selected_setting == 0:
                    settings.decrease_speed()
                elif selected_setting == 1:
                    settings.decrease_fps()
                elif selected_setting == 2:
                    settings.toggle_camera()
                elif selected_setting == 3:
                    settings.decrease_obstacle_frequency()
                elif selected_setting == 4:
                    settings.decrease_sensitivity()
                elif selected_setting == 5:
                    settings.decrease_brake_sensitivity()
            elif event.key == pygame.K_RIGHT:
                if selected_setting == 0:
                    settings.increase_speed()
                elif selected_setting == 1:
                    settings.increase_fps()
                elif selected_setting == 2:
                    settings.toggle_camera()
                elif selected_setting == 3:
                    settings.increase_obstacle_frequency()
                elif selected_setting == 4:
                    settings.increase_sensitivity()
                elif selected_setting == 5:
                    settings.increase_brake_sensitivity()
    return running, selected_setting, show_settings


if __name__ == "__main__":
    main()
