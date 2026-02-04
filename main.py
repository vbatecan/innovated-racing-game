import time
import cv2
import pygame
import logging
from controller import Controller
from car import Car
from map import Map

logging.basicConfig(level=logging.INFO)


def main():
    pygame.init()
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Hand Gesture Racing Game")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)

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

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        frame = detector.get_frame()
        if frame is not None:
            cv2.imshow("Hand Tracker (Press 'q' to quit)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                running = False

        steer_input = detector.steer

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            steer_input = -1.0
        if keys[pygame.K_RIGHT]:
            steer_input = 1.0

        game_map.update()
        player_car.update(steer_input, SCREEN_WIDTH)

        road_min_x, road_max_x = game_map.get_road_borders()
        if player_car.rect.left < road_min_x or player_car.rect.right > road_max_x:
            player_car.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 120)
            player_car.velocity_x = 0

        if pygame.sprite.spritecollide(player_car, game_map.obstacles, True):
            player_car.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 120)
            player_car.velocity_x = 0

        game_map.draw(screen)
        sprite_group.draw(screen)

        # Display Info
        steer_text = font.render(f"Steer: {steer_input:.2f}", True, (255, 255, 255))
        screen.blit(steer_text, (10, 10))

        # Display FPS
        fps = clock.get_fps()
        fps_text = font.render(f"FPS: {int(fps)}", True, (0, 255, 0))
        screen.blit(fps_text, (10, 50))

        pygame.display.flip()
        clock.tick(60)

    detector.stop_stream()
    cv2.destroyAllWindows()
    pygame.quit()


if __name__ == "__main__":
    main()
