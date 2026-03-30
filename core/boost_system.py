"""Boost/nitro system management.

Handles the boost state machine including rising-edge detection,
cooldown management, and duration tracking.
"""

import pygame
from core.enums import BoostConstants


class BoostSystem:
    """Manages the boost/nitro gameplay mechanic.

    The boost system requires a rising edge on the boost input (thumbs up)
    and enforces a cooldown period between activations. While active, it
    modifies both acceleration and maximum speed.
    """

    def __init__(self) -> None:
        """Initialize the boost system with default inactive state."""
        self._active: bool = False
        self._end_time: int = 0
        self._cooldown_end: int = 0
        self._prev_boosting: bool = False

    @property
    def is_active(self) -> bool:
        """Check if boost is currently active.

        Returns:
            True if boost is active and duration has not expired.
        """
        return self._active

    @property
    def cooldown_end(self) -> int:
        """Get the timestamp when boost cooldown ends.

        Returns:
            Milliseconds timestamp when boost can next be activated.
        """
        return self._cooldown_end

    def update(self, is_boosting: bool) -> None:
        """Update boost state based on current input.

        This method implements rising-edge detection for boost activation,
        ensuring boost only triggers on a new thumbs-up gesture, not while
        holding the gesture continuously.

        Args:
            is_boosting: Current boost input state from controller.
        """
        now = pygame.time.get_ticks()

        if (
            is_boosting
            and not self._prev_boosting
            and not self._active
            and now > self._cooldown_end
        ):
            self._active = True
            self._end_time = now + BoostConstants.DURATION_MS
            self._cooldown_end = now + BoostConstants.COOLDOWN_MS

        if self._active and now > self._end_time:
            self._active = False

        self._prev_boosting = is_boosting

    def get_acceleration_multiplier(self) -> float:
        """Get the acceleration multiplier based on boost state.

        Returns:
            3.0 if boost is active, 1.0 otherwise.
        """
        return BoostConstants.ACCELERATION_MULTIPLIER if self._active else 1.0

    def get_speed_multiplier(self) -> float:
        """Get the speed multiplier based on boost state.

        Returns:
            1.7 if boost is active, 1.0 otherwise.
        """
        return BoostConstants.SPEED_MULTIPLIER if self._active else 1.0

    def reset(self) -> None:
        """Reset boost system to initial inactive state."""
        self._active = False
        self._end_time = 0
        self._cooldown_end = 0
        self._prev_boosting = False
