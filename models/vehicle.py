import pygame
from core.resource_manager import ResourceManager

import config


class Vehicle(pygame.sprite.Sprite):
    def __init__(
            self,
            start_x: int,
            start_y: int,
            width: int = 80,
            height: int = 80,
            image_path: str = "resources/car.png",
    ) -> None:
        """
        Create a generic vehicle sprite that can be reused by player/NPC classes.
        """
        super().__init__()
        self.width = width
        self.height = height
        self.image = pygame.transform.scale(
            ResourceManager.load_image(image_path, convert_alpha=True), (self.width, self.height)
        )
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = (start_x, start_y)
        self.mask = pygame.mask.from_surface(self.image)
        self.steer = 0.0
        self.current_angle = 0.0

    def turn(self, steer: float = 0.0, smoothing: float = 0.0) -> None:
        """
        Rotate the vehicle sprite to reflect steering input.
        
        Args:
            steer: Target steering value (-2 to 2 typically)
            smoothing: Smoothing factor for rotation (0 = instant, higher = smoother)
        """
        target_angle = -steer * config.TURN_STEER_SENS

        if smoothing > 0:
            self.current_angle += (target_angle - self.current_angle) * smoothing
        else:
            self.current_angle = target_angle

        self.image = pygame.transform.rotate(self.original_image, self.current_angle)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)
        self.steer = self.current_angle
