"""Gear system management.

Handles manual gear shifting with specific speed and acceleration ratios
for each gear level.
"""

from core.enums import GearConstants


class GearSystem:
    """Manages the manual gear shifting system.

    Provides 5 gears with distinct speed and acceleration multipliers,
    allowing players to optimize their acceleration and top speed.
    """

    def __init__(self) -> None:
        """Initialize gear system in first gear."""
        self._current_gear: int = GearConstants.DEFAULT_GEAR

    @property
    def current_gear(self) -> int:
        """Get the current gear level (1-5)."""
        return self._current_gear

    def shift_down(self) -> None:
        """Shift down by one gear."""
        self._current_gear = max(1, self._current_gear - 1)

    def shift_up(self) -> None:
        """Shift up by one gear."""
        self._current_gear = min(
            GearConstants.MAX_MANUAL_GEAR,
            self._current_gear + 1
        )

    def handle_shift_request(self, shift_down_requested: bool, shift_up_requested: bool) -> None:
        """Process shift requests from input.

        Ensures mutual exclusivity - if both are requested, no shift occurs.

        Args:
            shift_down_requested: True if downshift was requested.
            shift_up_requested: True if upshift was requested.
        """
        if shift_down_requested and not shift_up_requested:
            self.shift_down()
        elif shift_up_requested and not shift_down_requested:
            self.shift_up()

    def get_speed_ratio(self) -> float:
        """Get the speed multiplier for the current gear."""
        return GearConstants.SPEED_RATIOS.get(self._current_gear, 1.0)

    def get_acceleration_ratio(self) -> float:
        """Get the acceleration multiplier for the current gear."""
        return GearConstants.ACCEL_RATIOS.get(self._current_gear, 1.0)

    def get_max_speed(self, base_max_speed: float) -> float:
        """Calculate maximum speed for current gear.

        Args:
            base_max_speed: The car's base maximum speed.
        """
        return base_max_speed * self.get_speed_ratio()

    def get_acceleration(self, base_acceleration: float) -> float:
        """Calculate acceleration for current gear.

        Args:
            base_acceleration: The base acceleration value.
        """
        return base_acceleration * self.get_acceleration_ratio()

    def reset(self) -> None:
        """Reset to first gear."""
        self._current_gear = GearConstants.DEFAULT_GEAR
