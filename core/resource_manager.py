import os
import pygame
from typing import Dict

class ResourceManager:
    _images: Dict[str, pygame.Surface] = {}
    _sounds: Dict[str, pygame.mixer.Sound] = {}
    _fonts: Dict[str, pygame.font.Font] = {}

    @classmethod
    def load_image(cls, path: str, scale=None, convert_alpha=True) -> pygame.Surface:
        key = f"{path}_{scale}_{convert_alpha}"
        if key not in cls._images:
            if not os.path.exists(path):
                # Return an empty surface if not found to prevent crash
                surface = pygame.Surface((32, 32))
                surface.fill((255, 0, 255))
                cls._images[key] = surface
                return surface

            image = pygame.image.load(path)
            
            if scale:
                image = pygame.transform.smoothscale(image, scale)
                
            if convert_alpha:
                cls._images[key] = image.convert_alpha()
            else:
                cls._images[key] = image.convert()
                
        return cls._images[key]

    @classmethod
    def clear_cache(cls):
        """Free up memory by removing unused assets."""
        cls._images.clear()
        cls._sounds.clear()
        cls._fonts.clear()
