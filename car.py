import pygame


class Car(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y):
        super().__init__()
        # Car dimensions
        self.width = 60
        self.height = 100

        # Create a surface for the car
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.center = (start_x, start_y)

        # Physics / Control
        self.max_speed = 10
        self.velocity_x = 0
        self.smoothing = 0.2  # Smooth movement

        self.draw_car()

    def draw_car(self):
        # Clear surface
        self.image.fill((0, 0, 0, 0))

        # Colors (Neon/Cyberpunk Theme)
        BODY_COLOR = (255, 0, 128)  # Neon Pink/Magenta
        WINDSHIELD_COLOR = (0, 255, 255, 200)  # Cyan with alpha
        GLOW_COLOR = (255, 0, 128, 50)

        # Draw Glow (larger rect behind)
        # We can simulate glow by drawing multiple translucent rects if we wanted,
        # but for now let's keep the shape sharp.

        # Main Body (Slightly rounded)
        pygame.draw.rect(self.image, BODY_COLOR, (10, 0, 40, 100), border_radius=10)

        # Side pods / Rear wheels area
        pygame.draw.rect(self.image, (200, 0, 100), (0, 60, 10, 30), border_radius=5)
        pygame.draw.rect(self.image, (200, 0, 100), (50, 60, 10, 30), border_radius=5)

        # Front wheels area
        pygame.draw.rect(self.image, (200, 0, 100), (0, 10, 10, 20), border_radius=5)
        pygame.draw.rect(self.image, (200, 0, 100), (50, 10, 10, 20), border_radius=5)

        # Windshield
        pygame.draw.polygon(
            self.image, WINDSHIELD_COLOR, [(15, 30), (45, 30), (40, 50), (20, 50)]
        )

        # Headlights
        pygame.draw.circle(self.image, (255, 255, 255), (15, 5), 3)
        pygame.draw.circle(self.image, (255, 255, 255), (45, 5), 3)

        # Rear lights
        pygame.draw.rect(self.image, (255, 50, 50), (15, 95, 30, 5), border_radius=2)

    def update(self, steering, screen_width):
        """
        Update car position based on steering value [-1, 1]
        """
        # Map steering to velocity
        target_vx = steering * self.max_speed

        # Smooth interpolation
        self.velocity_x += (target_vx - self.velocity_x) * self.smoothing

        # Apply movement
        self.rect.x += int(self.velocity_x)

        # Boundaries
        if self.rect.left < 0:
            self.rect.left = 0
            self.velocity_x = 0
        if self.rect.right > screen_width:
            self.rect.right = screen_width
            self.velocity_x = 0
