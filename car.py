import pygame


class Car(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y):
        """
        Create a car sprite at the given position.

        Initializes the car's geometry, physics state, and draws its initial
        appearance onto its surface.
        """
        super().__init__()
        self.width = 64
        self.height = 64

        # Create a surface for the car
        self.image = pygame.transform.scale(
            pygame.image.load("resources/car.png").convert_alpha(), (64, 64)
        )
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = (start_x, start_y)

        # Physics / Control
        self.current_speed = 0
        self.max_speed = 10  # This will be overridden or used as a cap
        self.velocity_x = 0
        self.smoothing = 0.2  # Smooth movement

        # Control
        self.steer = 0

    def turn(self, steer: float = 0.0):
        TURN_STEER_SENS = 30
        self.image = pygame.transform.rotate(self.original_image, -steer * TURN_STEER_SENS)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.steer = -steer * TURN_STEER_SENS

    def update(
            self,
            steering,
            is_braking,
            max_speed,
            acceleration,
            friction,
            brake_strength,
            screen_width,
    ):
        """
        Update the car's speed and position for a frame.

        Applies acceleration/braking and friction, clamps to bounds, smooths the
        steering response, and keeps the car within the screen width.
        """
        if is_braking:
            self.current_speed -= brake_strength
        else:
            self.current_speed += acceleration

        self.current_speed -= friction

        # Clamp Speed
        if self.current_speed < 0:
            self.current_speed = 0
        if self.current_speed > max_speed:
            self.current_speed = max_speed

        effective_speed = max(self.current_speed, 2)
        target_vx = steering * effective_speed

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
