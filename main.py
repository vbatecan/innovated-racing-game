import time
import cv2
import pygame
import logging
from controller import Controller
from car import Car
from map import Map
from settings import Settings

logging.basicConfig(level=logging.INFO)


def draw_settings_menu(screen, font, settings, selected_index, options):
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

        text = font.render(f"{option}: {value_text}", True, color)

        # Center the text in the overlay
        text_rect = text.get_rect(
            center=(overlay_rect.centerx, overlay_rect.y + 80 + i * 40)
        )
        screen.blit(text, text_rect)

    hint = font.render("Press S to Close", True, (150, 150, 150))
    screen.blit(
        hint, (overlay_rect.centerx - hint.get_width() // 2, overlay_rect.bottom - 40)
    )


def main():
    pygame.init()
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Hand Gesture Racing Game")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)

    settings = Settings()
    game_map = Map(SCREEN_WIDTH, SCREEN_HEIGHT)

    start_x = SCREEN_WIDTH // 2
    start_y = SCREEN_HEIGHT - 120
    player_car = Car(start_x, start_y)

    sprite_group = pygame.sprite.Group()
    sprite_group.add(player_car)

    detector = Controller()
    detector.start_stream()

    running = True
    print("Starting Game Loop...")
    print("Controls: Use your hands visible to the camera.")
    print("Press 'S' to open Settings.")

    show_settings = False
    setting_options = [
        "Car Speed",
        "Max FPS",
        "Show Camera",
        "Obstacle Freq",
        "Sensitivity",
    ]
    selected_setting = 0

    while running:
        # 1. Provide settings to map
        game_map.speed = settings.car_speed
        game_map.obstacle_frequency = settings.obstacle_frequency

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_s:
                    show_settings = not show_settings
                    # If turning off camera via settings, ensure window is closed
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

        # Update Logic
        if not show_settings:
            # Get detector frame
            frame = detector.get_frame()
            if settings.show_camera and frame is not None:
                cv2.imshow("Hand Tracker (Press 'S' for Settings)", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    # Just close camera or quit game? Let's just do nothing here, let main loop handle quit
                    pass
            elif not settings.show_camera:
                # If we just toggled it off, we need to make sure window is gone.
                # cv2.destroyWindow throws error if window doesn't exist, so use try/except or just destroyAllWindows occassionally
                # But calling destroyAllWindows every frame is bad.
                # We handled it in the toggle logic above.
                pass

            steer_input = detector.steer * settings.steering_sensitivity
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                steer_input = -1.0 * settings.steering_sensitivity
            if keys[pygame.K_RIGHT]:
                steer_input = 1.0 * settings.steering_sensitivity

            game_map.update()
            player_car.update(steer_input, SCREEN_WIDTH)

            road_min_x, road_max_x = game_map.get_road_borders()
            if player_car.rect.left < road_min_x or player_car.rect.right > road_max_x:
                player_car.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 120)
                player_car.velocity_x = 0

            if pygame.sprite.spritecollide(player_car, game_map.obstacles, True):
                player_car.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 120)
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

        if show_settings:
            draw_settings_menu(
                screen, font, settings, selected_setting, setting_options
            )

        pygame.display.flip()
        clock.tick(settings.max_fps)

    detector.stop_stream()
    cv2.destroyAllWindows()
    pygame.quit()


if __name__ == "__main__":
    main()
