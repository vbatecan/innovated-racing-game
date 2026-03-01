import pygame

from models.vehicle import Vehicle


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
        self.turn_smoothing = 0.15  # Smooth turning
        self.x = float(start_x)  # Float position for sub-pixel accuracy

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

        # Apply movement with float precision
        self.x += self.velocity_x
        self.rect.x = int(self.x)

        # Boundaries
        if self.rect.left < 0:
            self.rect.left = 0
            self.x = float(self.rect.x)
            self.velocity_x = 0
        if self.rect.right > screen_width:
            self.rect.right = screen_width
            self.x = float(self.rect.x)
            self.velocity_x = 0

    def set_max_speed(self, max_speed):
        self.max_speed = max_speed

    def add_max_speed(self, speed_increment):
        self.max_speed += speed_increment

