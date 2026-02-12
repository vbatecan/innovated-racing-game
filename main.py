import logging
import os
from typing import Tuple

import cv2
import pygame
from pygame.key import ScancodeWrapper

import config
from car import Car
from config import SHOW_CAMERA, WINDOW_SIZE
from controller import Controller
from map import Map
from score import Score
from settings import Settings
from ui.hud import PlayerHUD

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/main.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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

    score = Score()
    score.set_score(0)

    hud = PlayerHUD(player_car, detector, font)

    running = True

    logger.info("Starting Game Loop...")
    logger.info("Controls: Use your hands visible to the camera.")
    logger.info("Press 'S' to open Settings.")
    selected_setting = 0

    score_timer = 0
    score_interval = 1000  # milliseconds
    min_interval = 200  # minimum interval between score increases
    interval_decrement = 10  # ms to decrease interval every 5 seconds
    last_speedup = pygame.time.get_ticks()

    while running:
        game_map.speed = settings.car_speed
        game_map.obstacle_frequency = int(
            settings.max_fps / settings.obstacle_frequency
        )

        for event in pygame.event.get():
            running, selected_setting, show_settings = settings.handle_event(
                event,
                running,
                selected_setting,
                config.SETTING_OPTIONS,
                settings.visible,
            )
            settings.visible = show_settings

        if not settings.visible:
            detector.brake_threshold = settings.get_brake_threshold()

            frame = detector.get_frame()
            if settings.show_camera and frame is not None:
                cv2.imshow("Hand Tracker (Press 'P' for Settings)", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    pass
            elif not settings.show_camera:
                pass
            
            # Arrow key down will break.
            is_breaking = detector.breaking
            keys = pygame.key.get_pressed()
            if keys[pygame.K_DOWN]:
                is_breaking = True

            target_steer = detector.steer * settings.steering_sensitivity
            target_steer, turn = steer(
                keys, settings.steering_sensitivity, target_steer
            )
            player_car.turn(target_steer)

            player_car.update(
                steering=target_steer,
                is_braking=is_breaking,
                max_speed=player_car.max_speed,
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

            if pygame.sprite.spritecollide(
                player_car,
                game_map.obstacles,
                True,
                collided=pygame.sprite.collide_mask,
            ):
                player_car.rect.center = (
                    WINDOW_SIZE["width"] // 2,
                    WINDOW_SIZE["height"] - 120,
                )
                player_car.current_speed = 0
                player_car.velocity_x = 0
                score.deduct(settings.car_collision_deduction_pts)

        # Drawing
        game_map.draw(screen)
        sprite_group.draw(screen)

        fps = clock.get_fps()
        hud.update_from_game(
            player_car,
            detector,
            score=score.get_score(),
            fps=int(fps),
            max_fps=settings.max_fps,
        )
        hud.draw(screen)

        obs_text = font.render(
            f"Obs Freq: {settings.obstacle_frequency}", True, (200, 200, 200)
        )
        screen.blit(obs_text, (10, 90))

        if settings.visible:

            settings.draw_settings_menu(
                screen, font, settings, selected_setting, config.SETTING_OPTIONS
            )

        pygame.display.flip()
        logger.info(player_car.current_speed)

        # Scoring system: add 2 points every score_interval ms, speed up over time, 
        # but pause if breaking
        now = pygame.time.get_ticks()
        if not is_breaking:
            if now - score_timer >= score_interval:
                score.add_score(1 * round(player_car.current_speed / 2))
                score_timer = now

        # Every 5 seconds, decrease interval (speed up scoring), but not below min_interval
        if now - last_speedup >= 5000 and score_interval > min_interval:
            score_interval = max(min_interval, score_interval - interval_decrement)
            last_speedup = now

        # Every 100 points, speed up scoring (decrease interval), but not below min_interval
        if score.get_score() > 0 and score.get_score() % 100 == 0:
            score_interval = max(min_interval, score_interval - interval_decrement)

        # sa every 400 points, nag-add 1 to speed
        if player_car.max_speed <= 20:
            speed_bonus = score.get_score() // settings.speed_bonus
            player_car.set_max_speed(settings.car_speed + speed_bonus)
        
        clock.tick(settings.max_fps)

    detector.stop_stream()
    cv2.destroyAllWindows()
    pygame.quit()


def steer(
    keys: ScancodeWrapper, steering_sensitivity, target_steer: float
) -> Tuple[float, str]:
    """Steer using arrow keys, if no arrow keys pressed. Return the steering sensitivity anyway.

    Args:
        keys (ScancodeWrapper): The pygame key event
        steering_sensitivity (floa): The steering sensitivity that is multiplied to the target steer
        target_steer (float): The steering.

    Returns:
        Tuple[float, str]: Returns the target_steer and the turn whether LEFT, CENTER, or RIGHT.
    """
    turn = "CENTER"
    if keys[pygame.K_LEFT]:
        target_steer = -1.0 * steering_sensitivity
        turn = "LEFT"
    if keys[pygame.K_RIGHT]:
        target_steer = 1.0 * steering_sensitivity
        turn = "RIGHT"
    return target_steer, turn




if __name__ == "__main__":
    main()
