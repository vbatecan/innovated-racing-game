"""Steering input handling for keyboard overrides.

Provides keyboard-based steering control that can override or supplement
hand gesture-based steering input.
"""

from typing import Tuple
import pygame
from pygame.key import ScancodeWrapper


class TurnDirection:
    """Constants for turn direction labels."""

    LEFT = "LEFT"
    CENTER = "CENTER"
    RIGHT = "RIGHT"


class SteeringHandler:
    """Handles keyboard steering input and direction determination."""

    @staticmethod
    def calculate_steering(
        keys: ScancodeWrapper,
        steering_sensitivity: float,
        current_steer: float
    ) -> Tuple[float, str]:
        """Calculate steering value based on keyboard input.

        Applies keyboard overrides to the current steering value and
        determines the turn direction label.

        Args:
            keys: Current keyboard state from pygame.key.get_pressed().
            steering_sensitivity: Multiplier applied to keyboard steering input.
            current_steer: The current steering value from hand gesture input.

        Returns:
            A tuple containing:
                - The final steering value (-1.0 to 1.0, scaled by sensitivity)
                - The turn direction label ("LEFT", "CENTER", or "RIGHT")

        Note:
            If both LEFT and RIGHT keys are pressed, RIGHT takes precedence.
        """
        turn = TurnDirection.CENTER
        target_steer = current_steer

        if keys[pygame.K_LEFT]:
            target_steer = -1.0 * steering_sensitivity
            turn = TurnDirection.LEFT

        if keys[pygame.K_RIGHT]:
            target_steer = 1.0 * steering_sensitivity
            turn = TurnDirection.RIGHT

        return target_steer, turn


def steer(
    keys: ScancodeWrapper,
    steering_sensitivity: float,
    target_steer: float
) -> Tuple[float, str]:
    """Apply keyboard steering overrides and return steer value plus turn label.

    This is the legacy function interface preserved for backward compatibility.
    Consider using SteeringHandler.calculate_steering() for new code.

    Args:
        keys: Current keyboard state from pygame.key.get_pressed().
        steering_sensitivity: Steering multiplier used for keyboard input.
        target_steer: Current steering value from hand input.

    Returns:
        Tuple[float, str]: Final steering value and one of LEFT/CENTER/RIGHT.

    Example:
        >>> keys = pygame.key.get_pressed()
        >>> steer(keys, 1.0, 0.0)
        (0.0, 'CENTER')
    """
    return SteeringHandler.calculate_steering(keys, steering_sensitivity, target_steer)
