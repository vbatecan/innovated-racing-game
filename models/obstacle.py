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
    ) -> None:
        """
        Move the obstacle and delete if off-screen.

        Vehicle speed is independent per obstacle (`traffic_speed`) and
        on-screen movement is based on signed relative speed.

        - If player is faster than traffic, obstacles move toward the player.
        - If player brakes and becomes slower than traffic, obstacles move up.

        Returns:
            None: Updates sprite position in place.
        """
        capped_player_speed = max(0.0, float(player_speed))
        traffic_world_speed = min(self.traffic_speed, 24.0)
        relative_speed = capped_player_speed - traffic_world_speed
        self.speed = min(24.0, abs(relative_speed))
        target_direction = 1.0 if relative_speed >= 0.0 else -1.0
        self.direction_factor += (target_direction - self.direction_factor) * 0.18
        self._y_pos += self.speed * self.direction_factor
        self.rect.y = int(self._y_pos)

        if self.rect.top > screen_height + self.rect.height or self.rect.bottom < -self.rect.height:
            self.kill()
