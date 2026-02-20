import pygame

import config


class Vehicle(pygame.sprite.Sprite):
    def __init__(
        self,
        start_x: int,
        start_y: int,
        width: int = 96,
        height: int = 96,
        image_path: str = "resources/car.png",
    ) -> None:
        """
        Create a generic vehicle sprite that can be reused by player/NPC classes.
        """
        super().__init__()
        self.width = width
        self.height = height
        self.image = pygame.transform.scale(
            pygame.image.load(image_path).convert_alpha(), (self.width, self.height)
        )
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = (start_x, start_y)
        self.mask = pygame.mask.from_surface(self.image)
        self.steer = 0.0

    def turn(self, steer: float = 0.0) -> None:
        """
        Rotate the vehicle sprite to reflect steering input.
        """
        angle = -steer * config.TURN_STEER_SENS
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)
        self.steer = angle


class PlayerCar(Vehicle):
    def __init__(self, start_x: int, start_y: int) -> None:
        """
        Create a car sprite at the given position.

        Initializes the car's geometry, physics state, and draws its initial
        appearance onto its surface.
        """
        super().__init__(start_x=start_x, start_y=start_y)

        # Physics / Control
        self.current_speed = 0
        self.max_speed = 10  # This will be overridden or used as a cap
        self.velocity_x = 0
        self.smoothing = 0.2  # Smooth movement

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

    def set_max_speed(self, max_speed):
        self.max_speed = max_speed

    def add_max_speed(self, speed_increment):
        self.max_speed += speed_increment


# Backwards compatibility alias.
Car = PlayerCar
