import pygame

from models.vehicle import Vehicle
from models.car_data import get_car_by_id


class PlayerCar(Vehicle):
    SPRITE_CANVAS_SIZE = (96, 96)

    def __init__(self, start_x: int, start_y: int, car_manager=None) -> None:
        super().__init__(start_x=start_x, start_y=start_y)

        self.car_manager = car_manager

        self.current_speed = 0.0
        self.max_speed = 10.0
        self.velocity_x = 0.0
        self.smoothing = 0.2
        self.turn_smoothing = 0.15
        self.x = float(start_x)

        # Upgrade-influenced runtime physics factors.
        self.acceleration_factor = 1.0
        self.brake_factor = 1.0
        self.cornering_grip = 1.0

        # Visual cue state.
        self._has_turbo = False
        self._has_suspension = False
        self._has_brakes = False
        self._boost_visual_active = False
        self._braking_visual_active = False

        self._base_car_image = self.image.copy()
        self._composed_dirty = True

        self.refresh_configuration()

    def refresh_configuration(self) -> None:
        """Refresh selected sprite, stat modifiers, and upgrade visuals."""
        self._apply_selected_car_sprite()
        self._apply_car_stats()
        self._compose_visual_sprite()

    def set_visual_cues(self, boost_active: bool, is_braking: bool) -> None:
        """Update visual cue state for active upgrades and rebuild sprite when needed."""
        changed = False
        if self._boost_visual_active != boost_active:
            self._boost_visual_active = boost_active
            changed = True
        if self._braking_visual_active != is_braking:
            self._braking_visual_active = is_braking
            changed = True

        if changed:
            self._compose_visual_sprite()

    def _apply_selected_car_sprite(self) -> None:
        if not self.car_manager:
            self._base_car_image = self.image.copy()
            return

        selected_car = self.car_manager.get_selected_car()
        if selected_car is None:
            self._base_car_image = self.image.copy()
            return

        car_data = get_car_by_id(selected_car.id)
        if car_data is None:
            self._base_car_image = self.image.copy()
            return

        try:
            image = pygame.image.load(car_data.image_path).convert_alpha()
            fitted = self._fit_image_to_canvas(image, self.SPRITE_CANVAS_SIZE)
            self._base_car_image = fitted
            self.image = fitted.copy()
            self.original_image = self.image.copy()
            self.rect = self.image.get_rect(center=(self.rect.centerx, self.rect.centery))
            self.mask = pygame.mask.from_surface(self.image)
        except (pygame.error, FileNotFoundError):
            self._base_car_image = self.image.copy()

    def _fit_image_to_canvas(
        self,
        image: pygame.Surface,
        canvas_size: tuple[int, int],
    ) -> pygame.Surface:
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
        if not self.car_manager:
            return

        performance = self.car_manager.get_effective_performance_car()

        self.max_speed = 10 + (performance.speed / 100.0) * 20

        max_smoothing = 0.3
        min_smoothing = 0.07
        self.turn_smoothing = max_smoothing - (performance.handling / 100.0) * (max_smoothing - min_smoothing)

        self.acceleration_factor = 0.65 + (performance.acceleration / 100.0) * 0.95
        self.brake_factor = 0.60 + (performance.braking / 100.0) * 1.00
        self.cornering_grip = 0.70 + (performance.handling / 100.0) * 0.55

        owned = set(self.car_manager.get_owned_upgrades())
        self._has_turbo = "turbo_charger" in owned
        self._has_suspension = "sport_suspension" in owned
        self._has_brakes = "precision_brakes" in owned

    def _compose_visual_sprite(self) -> None:
        base = self._base_car_image
        canvas = pygame.Surface(self.SPRITE_CANVAS_SIZE, pygame.SRCALPHA)

        if self._has_suspension:
            width, height = base.get_size()
            lowered = pygame.transform.smoothscale(base, (max(1, int(width * 1.02)), max(1, int(height * 0.93))))
            rect = lowered.get_rect(center=canvas.get_rect().center)
            rect.y += 3
            canvas.blit(lowered, rect)
        else:
            canvas.blit(base, base.get_rect(center=canvas.get_rect().center))

        if self._has_brakes:
            intensity = 220 if self._braking_visual_active else 150
            left_caliper = pygame.Rect(24, 58, 8, 16)
            right_caliper = pygame.Rect(64, 58, 8, 16)
            pygame.draw.rect(canvas, (220, 44, 44, intensity), left_caliper, border_radius=3)
            pygame.draw.rect(canvas, (220, 44, 44, intensity), right_caliper, border_radius=3)

        if self._has_turbo and self._boost_visual_active:
            for radius, alpha, color in (
                (18, 90, (82, 220, 255)),
                (11, 160, (255, 164, 74)),
            ):
                flame = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.ellipse(flame, (*color, alpha), flame.get_rect())
                canvas.blit(flame, (20 - radius // 2, 72 - radius // 2))
                canvas.blit(flame, (58 - radius // 2, 72 - radius // 2))

        center = self.rect.center
        self.image = canvas
        self.original_image = canvas.copy()
        self.rect = self.image.get_rect(center=center)
        self.mask = pygame.mask.from_surface(self.image)

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
        effective_accel = float(acceleration) * self.acceleration_factor
        effective_brake_strength = float(brake_strength) * self.brake_factor

        if is_braking:
            max_speed_ref = max(1.0, float(max_speed))
            speed_ratio = max(0.0, min(1.0, self.current_speed / max_speed_ref))
            dynamic_brake = effective_brake_strength * (0.35 + (0.65 * speed_ratio))
            self.current_speed -= dynamic_brake

            # Precision brakes reduce lateral slide while stopping.
            if self._has_brakes:
                self.velocity_x *= 0.82
        else:
            self.current_speed += effective_accel

        self.current_speed -= float(friction)

        if self.current_speed < 0:
            self.current_speed = 0
        if self.current_speed > max_speed:
            self.current_speed = max_speed

        effective_speed = max(self.current_speed, 2)
        target_vx = steering * effective_speed * self.cornering_grip

        steer_smoothing = self.smoothing * (0.9 + 0.2 * self.cornering_grip)
        self.velocity_x += (target_vx - self.velocity_x) * steer_smoothing

        if abs(steering) < 0.12:
            self.velocity_x *= 0.84 + (0.12 * self.cornering_grip)

        self.x += self.velocity_x
        self.rect.x = int(self.x)
        self.mask = pygame.mask.from_surface(self.image)

        if self.rect.left < 0:
            self.rect.left = 0
            self.x = float(self.rect.x)
            self.velocity_x = 0
            self.mask = pygame.mask.from_surface(self.image)
        if self.rect.right > screen_width:
            self.rect.right = screen_width
            self.x = float(self.rect.x)
            self.velocity_x = 0
            self.mask = pygame.mask.from_surface(self.image)

    def set_max_speed(self, max_speed):
        self.max_speed = max_speed

    def add_max_speed(self, speed_increment):
        self.max_speed += speed_increment
