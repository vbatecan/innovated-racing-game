import logging
import os
from typing import Tuple

import cv2
import pygame
from pygame.key import ScancodeWrapper

import config
from car import PlayerCar
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
    boost_active = False
    boost_end_time = 0
    boost_cooldown_end = 0  # Time when next boost is allowed
    prev_boosting = False  # Track previous boosting state for edge detection
    max_manual_gear = 5
    current_gear = 1
    gear_speed_ratio = {1: 0.45, 2: 0.62, 3: 0.78, 4: 0.9, 5: 1.0}
    gear_accel_ratio = {1: 1.3, 2: 1.15, 3: 1.0, 4: 0.9, 5: 0.8}
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE["width"], WINDOW_SIZE["height"]))
    pygame.display.set_caption("Hand Gesture Racing Game")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, config.FONT_SIZE)

    settings = Settings()
    settings.show_camera = SHOW_CAMERA
    game_map = Map(WINDOW_SIZE, lane_count=settings.lane_count)

    start_x = WINDOW_SIZE["width"] // 2
    start_y = WINDOW_SIZE["height"] - 240
    player_car = PlayerCar(start_x, start_y)

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
            (settings.max_fps * 2) / settings.obstacle_frequency
        )
        game_map.set_lane_count(settings.lane_count)

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

            # --- BOOST FEATURE ---
            now = pygame.time.get_ticks()
            # Only trigger boost on new thumbs up (rising edge)
            if detector.boosting and not prev_boosting and not boost_active and now > boost_cooldown_end:
                boost_active = True
                boost_end_time = now + 1000 
                boost_cooldown_end = now + 10000 
            if boost_active and now > boost_end_time:
                boost_active = False
            prev_boosting = detector.boosting

            # Arrow key down will break.
            is_breaking = detector.breaking
            keys = pygame.key.get_pressed()
            if keys[pygame.K_DOWN]:
                is_breaking = True

            shift_down, shift_up = detector.consume_shift_request()
            if shift_down and not shift_up:
                current_gear = max(1, current_gear - 1)
            elif shift_up and not shift_down:
                current_gear = min(max_manual_gear, current_gear + 1)

            target_steer = detector.steer * settings.steering_sensitivity
            target_steer, turn = steer(
                keys, settings.steering_sensitivity, target_steer
            )
            player_car.turn(max(-2, min(target_steer, 2)), player_car.turn_smoothing)

            # Apply boost to acceleration and max speed if active
            acceleration = settings.ACCELERATION * gear_accel_ratio[current_gear]
            max_speed = player_car.max_speed * gear_speed_ratio[current_gear]
            if boost_active:
                acceleration *= 3  # 3x acceleration
                max_speed *= 1.7   # 70% higher top speed during boost

            player_car.update(
                steering=target_steer,
                is_braking=is_breaking,
                max_speed=max_speed,
                acceleration=acceleration,
                friction=settings.FRICTION,
                brake_strength=settings.BRAKE_STRENGTH,
                screen_width=WINDOW_SIZE["width"],
            )

            game_map.speed = int(player_car.current_speed)
            game_map.update_score(score.get_score())
            game_map.update(is_braking=is_breaking)

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
                # Stop all movement, but do not reset position
                player_car.current_speed = 0
                player_car.velocity_x = 0
                if hasattr(player_car, 'velocity'):
                    player_car.velocity = 0
                score.deduct(settings.car_collision_deduction_pts)

        # Drawing
        game_map.draw(screen)
        sprite_group.draw(screen)

        fps = clock.get_fps()
        hud.update_from_game(
            player_car,
            detector,
            gear=str(current_gear),
            score=score.get_score(),
            fps=int(fps),
            max_fps=settings.max_fps,
        )
        hud.draw(screen)

        obs_text = font.render(
            f"Obs Freq: {settings.obstacle_frequency}", True, (200, 200, 200)
        )
        obs_y = hud.position[1] + hud.size[1] + 10
        screen.blit(obs_text, (10, obs_y))
        lane_text = font.render(
            f"Lanes: {settings.lane_count}", True, (200, 200, 200)
        )
        screen.blit(lane_text, (10, obs_y + font.get_linesize()))

        if settings.visible:

            settings.draw_settings_menu(
                screen, font, settings, selected_setting, config.SETTING_OPTIONS
            )

        pygame.display.flip()

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
    """Apply keyboard steering overrides and return steer value plus turn label.

    Args:
        keys (ScancodeWrapper): Current keyboard state from pygame.
        steering_sensitivity (float): Steering multiplier used for keyboard input.
        target_steer (float): Current steering value from hand input.

    Returns:
        Tuple[float, str]: Final steering value and one of LEFT/CENTER/RIGHT.
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
