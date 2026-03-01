import pygame

class Obstacle(pygame.sprite.Sprite):
    def __init__(
            self,
            x: int,
            y: int,
            width: int,
            height: int,
            speed: int,
            image: pygame.Surface | None = None,
            traffic_speed: float = 0.0,
    ):
        """
        Create an obstacle sprite.

        Args:
            x (int): Initial X position (left) of the obstacle sprite.
            y (int): Initial Y position (top) of the obstacle sprite.
            width (int): Obstacle width in pixels.
            height (int): Obstacle height in pixels.
            speed (int): Initial vertical movement speed per frame.
            image (pygame.Surface | None): Optional pre-built obstacle image.
            traffic_speed (float): World traffic speed used for relative movement.
        """
        super().__init__()
        # Always create the image at the correct size for the obstacle
        if image is None:
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
            self.image.fill((255, 50, 50))
            pygame.draw.rect(self.image, (255, 255, 0), (0, 0, width, 10))
        else:
            # Defensive: ensure the image is the correct size for the rect
            if image.get_width() != width or image.get_height() != height:
                self.image = pygame.transform.smoothscale(image, (width, height))
            else:
                self.image = image

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        # Always update the mask after scaling
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = float(speed)
        # Per-vehicle base approach speed so traffic always moves on-screen.
        self.traffic_speed = max(0.5, float(traffic_speed))
        self._y_pos = float(y)
        self.direction_factor = 1.0

    def update(
            self,
            player_speed: float,
            screen_height: int,
            is_braking: bool = False,
    ) -> None:
        """
        Move the obstacle using relative speed and delete if off-screen.

        The traffic vehicle's screen speed is computed from:
        `player_speed - traffic_speed`.

        Returns:
            None: Updates sprite position in place.
        """
        if is_braking:
            return

        # Blend player speed with per-vehicle traffic speed so traffic remains active
        # even at low player speed and scales up as gameplay gets faster.
        blended_speed = self.traffic_speed + (0.2 * float(player_speed))
        self.speed = max(1.0, min(24.0, blended_speed))
        target_direction = 1.0
        self.direction_factor += (target_direction - self.direction_factor) * 0.18
        self._y_pos += self.speed * self.direction_factor
        self.rect.y = int(self._y_pos)

        if (
                self.rect.top > screen_height + self.rect.height
                or self.rect.bottom < -self.rect.height
        ):
            self.kill()
