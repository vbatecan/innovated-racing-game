import pygame

from models.vehicle import Vehicle


class PlayerCar(Vehicle):
    def __init__(self, start_x: int, start_y: int, car_manager=None) -> None:
        """
        Create a car sprite at the given position.

        Initializes the car's geometry, physics state, and draws its initial
        appearance onto its surface.
        
        Args:
            start_x: Starting X position
            start_y: Starting Y position
            car_manager: Optional CarManager instance for car stats
        """
        super().__init__(start_x=start_x, start_y=start_y)

        self.car_manager = car_manager
        
        # Physics / Control
        self.current_speed = 0
        self.max_speed = 10  # This will be overridden or used as a cap
        self.velocity_x = 0
        self.smoothing = 0.2  # Smooth movement
        self.turn_smoothing = 0.15  # Smooth turning
        self.x = float(start_x)  # Float position for sub-pixel accuracy
        
        # Apply car stats if manager available
        self._apply_car_stats()

    def _apply_car_stats(self) -> None:
        """Apply selected car stats to this vehicle."""
        if not self.car_manager:
            return
        
        selected_car = self.car_manager.get_selected_car()
        if not selected_car:
            return
        
        stats = selected_car.stats
        
        # Apply stats with reasonable multipliers
        # Speed: 0-100 -> affects max_speed (scale to 10-30 range)
        self.max_speed = 10 + (stats.speed / 100.0) * 20
        
        # Handling: 0-100 -> affects turn_smoothing (higher handling = faster response)
        max_smoothing = 0.3
        min_smoothing = 0.08
        self.turn_smoothing = max_smoothing - (stats.handling / 100.0) * (max_smoothing - min_smoothing)
        
        # Acceleration and weight will be used in physics updates

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
            max_speed_ref = max(1.0, float(max_speed))
            speed_ratio = max(0.0, min(1.0, self.current_speed / max_speed_ref))
            dynamic_brake = float(brake_strength) * (0.35 + (0.65 * speed_ratio))
            self.current_speed -= dynamic_brake
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

