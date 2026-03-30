"""Key mapping utilities for keyboard input handling.

This module provides functions to map Pygame key events to option indices
for question answering interfaces.
"""

from typing import Dict, Optional
import pygame


class KeyMapper:
    """Maps Pygame key codes to option indices.

    Supports both standard number keys (1-9) and numpad keys (KP1-KP9).
    """

    _KEY_MAP: Dict[int, int] = {
        pygame.K_1: 0,
        pygame.K_KP1: 0,
        pygame.K_2: 1,
        pygame.K_KP2: 1,
        pygame.K_3: 2,
        pygame.K_KP3: 2,
        pygame.K_4: 3,
        pygame.K_KP4: 3,
        pygame.K_5: 4,
        pygame.K_KP5: 4,
        pygame.K_6: 5,
        pygame.K_KP6: 5,
        pygame.K_7: 6,
        pygame.K_KP7: 6,
        pygame.K_8: 7,
        pygame.K_KP8: 7,
        pygame.K_9: 8,
        pygame.K_KP9: 8,
    }

    @classmethod
    def get_option_index(cls, event_key: int) -> Optional[int]:
        """Map a Pygame key code to an option index.

        Args:
            event_key: The Pygame key constant (e.g., pygame.K_1).

        Returns:
            The zero-based option index if the key is mapped, else None.
        """
        return cls._KEY_MAP.get(event_key)


def key_to_option_index(event_key: int) -> Optional[int]:
    """Map a Pygame key code to an option index.

    Supports number keys 1-9 and their numpad equivalents.

    Args:
        event_key: The Pygame key constant from a KEYDOWN event.

    Returns:
        The zero-based option index (0-8) if mapped, otherwise None.

    Example:
        >>> key_to_option_index(pygame.K_1)
        0
        >>> key_to_option_index(pygame.K_KP5)
        4
        >>> key_to_option_index(pygame.K_a) is None
        True
    """
    return KeyMapper.get_option_index(event_key)
