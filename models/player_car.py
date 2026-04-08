import pygame

from models.vehicle import Vehicle
from models.car_data import get_car_by_id


class PlayerCar(Vehicle):
    SPRITE_CANVAS_SIZE = (96, 96)

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

        if self.car_manager:
            self._apply_selected_car_sprite()
        
        # Physics / Control
        self.current_speed = 0
        self.max_speed = 10  # This will be overridden or used as a cap
        self.velocity_x = 0
        self.smoothing = 0.2  # Smooth movement
        self.turn_smoothing = 0.15  # Smooth turning
        self.x = float(start_x)  # Float position for sub-pixel accuracy
        
        # Apply car stats if manager available
        self._apply_car_stats()

    def _apply_selected_car_sprite(self) -> None:
        """Load the selected car image for the driving sprite."""
        if not self.car_manager:
            return

        selected_car = self.car_manager.get_selected_car()
        if selected_car is None:
            return

        car_data = get_car_by_id(selected_car.id)
        if car_data is None:
            return

        try:
            image = pygame.image.load(car_data.image_path).convert_alpha()
            self.image = self._fit_image_to_canvas(image, self.SPRITE_CANVAS_SIZE)
            self.original_image = self.image.copy()
            # FIX: Preserve position when updating rect after sprite change
            self.rect = self.image.get_rect(center=(self.rect.centerx, self.rect.centery))
            # FIX: Update mask after image change
            self.mask = pygame.mask.from_surface(self.image)
        except (pygame.error, FileNotFoundError):
            # Keep the default sprite if the selected car image cannot be loaded.
            pass

    def _fit_image_to_canvas(
        self,
        image: pygame.Surface,
        canvas_size: tuple[int, int],
    ) -> pygame.Surface:
        """Scale an image to fit inside a fixed canvas while keeping its aspect ratio."""
        canvas_width, canvas_height = canvas_size
        source_width, source_height = image.get_size()

        if source_width == 0 or source_height == 0:
            return pygame.Surface(canvas_size, pygame.SRCALPHA)

        scale = min(
            canvas_width / float(source_width),
            canvas_height / float(source_height),
        )
        scaled_width = max(1, int(source_width * scale))
        scaled_height = max(1, int(source_height * scale))
        scaled_image = pygame.transform.smoothscale(image, (scaled_width, scaled_height))

        canvas = pygame.Surface(canvas_size, pygame.SRCALPHA)
        canvas.blit(
            scaled_image,
            scaled_image.get_rect(center=canvas.get_rect().center),
        )
        return canvas

    def _apply_car_stats(self) -> None:
        """Apply selected car stats to this vehicle."""
        if not self.car_manager:
            return
        
        selected_car = self.car_manager.get_selected_car()
        if not selected_car:
            return

        self._apply_selected_car_sprite()
        
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
        # CRITICAL FIX: Update mask when rect position changes
        self.mask = pygame.mask.from_surface(self.image)

        # Boundaries
        if self.rect.left < 0:
            self.rect.left = 0
            self.x = float(self.rect.x)
            self.velocity_x = 0
            # CRITICAL FIX: Update mask when rect position is adjusted
            self.mask = pygame.mask.from_surface(self.image)
        if self.rect.right > screen_width:
            self.rect.right = screen_width
            self.x = float(self.rect.x)
            self.velocity_x = 0
            # CRITICAL FIX: Update mask when rect position is adjusted
            self.mask = pygame.mask.from_surface(self.image)

    def set_max_speed(self, max_speed):
        self.max_speed = max_speed

    def add_max_speed(self, speed_increment):
        self.max_speed += speed_increment

