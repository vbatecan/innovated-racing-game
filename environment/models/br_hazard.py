import pygame

class BRHazard(pygame.sprite.Sprite):
    """BR hazard that scrolls toward the player."""

    def __init__(
            self,
            x: int,
            y: int,
            width: int,
            height: int,
            image: pygame.Surface | None = None,
    ):
        super().__init__()
        if image is None:
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(
                self.image, (200, 30, 30), (0, 0, width, height), border_radius=5
            )
        else:
            if image.get_width() != width or image.get_height() != height:
                self.image = pygame.transform.smoothscale(image, (width, height))
            else:
                self.image = image

        self.rect = self.image.get_rect(topleft=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self._y_pos = float(y)

    def update(
            self, map_speed: int, screen_height: int, is_braking: bool = False
    ) -> None:
        if is_braking:
            return

        self._y_pos += max(1.0, float(map_speed))
        self.rect.y = int(self._y_pos)
        if self.rect.top > screen_height + self.rect.height:
            self.kill()
