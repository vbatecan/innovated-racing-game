import pygame
import random


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, speed):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill((255, 50, 50))  # Red obstacles
        pygame.draw.rect(self.image, (255, 255, 0), (0, 0, width, 10))

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.y > 2000:
            self.kill()


class Map:
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height

        self.road_width = 400
        self.road_x = (self.width - self.road_width) // 2

        self.scroll_y = 0
        self.speed = 10

        self.BG_COLOR = (20, 20, 30)
        self.ROAD_COLOR = (30, 30, 40)
        self.LINE_COLOR = (0, 255, 255)
        self.MARKER_COLOR = (255, 255, 0)

        self.marker_height = 50
        self.marker_gap = 50
        self.total_marker_segment = self.marker_height + self.marker_gap

        self.obstacles = pygame.sprite.Group()
        self.obstacle_timer = 0
        self.obstacle_frequency = 30  # Bawat game max frame merong isang obstacle (60 fps = 1 obstacle) if kalahati merong dalawa

    def update(self):
        self.scroll_y += self.speed
        if self.scroll_y >= self.total_marker_segment:
            self.scroll_y -= self.total_marker_segment

        self.obstacle_timer += 1
        if self.obstacle_timer >= self.obstacle_frequency:
            self.obstacle_timer = 0
            if len(self.obstacles) < 5:  # Limit active obstacles
                # Spawn in one of 3 lanes roughly
                lane_width = self.road_width // 3
                lane = random.randint(0, 2)
                # Add some randomness to x
                spawn_x = (
                    self.road_x
                    + (lane * lane_width)
                    + random.randint(10, lane_width - 60)
                )
                spawn_y = -100  # Above screen

                obs = Obstacle(spawn_x, spawn_y, 50, 50, self.speed)
                self.obstacles.add(obs)

        for obs in self.obstacles:
            obs.speed = self.speed

        self.obstacles.update()

        # Kapag outside the boundary na, tatanggalin natin yung obstacle para hindi maipon at makasave ng memory.
        for obs in self.obstacles:
            if obs.rect.y > self.height:
                obs.kill()

    def draw(self, surface):
        surface.fill(self.BG_COLOR)

        pygame.draw.rect(
            surface, self.ROAD_COLOR, (self.road_x, 0, self.road_width, self.height)
        )

        # ito yung marker sa center
        center_x = self.road_x + self.road_width // 2

        start_y = -self.total_marker_segment + self.scroll_y

        while start_y < self.height:
            pygame.draw.rect(
                surface,
                self.MARKER_COLOR,
                (center_x - 5, start_y, 10, self.marker_height),
            )
            start_y += self.total_marker_segment

        # Draw Obstacles (under side lines potentially? No, above road, below UI)
        self.obstacles.draw(surface)

        # Draw Side Lines (thick neon glow) - Draw these last to cover obstacles potentially? No, obstacles should be on top.
        # Actually in a 2D game, lines usually are flat on ground. Obstacles on top.
        pygame.draw.line(
            surface, self.LINE_COLOR, (self.road_x, 0), (self.road_x, self.height), 5
        )
        pygame.draw.line(
            surface,
            self.LINE_COLOR,
            (self.road_x + self.road_width, 0),
            (self.road_x + self.road_width, self.height),
            5,
        )

    def get_road_borders(self):
        return self.road_x, self.road_x + self.road_width
