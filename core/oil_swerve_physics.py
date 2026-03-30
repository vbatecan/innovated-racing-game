"""Oil swerve physics calculations.

Implements the sine-wave based swerve effect when driving over oil spills,
including dual-wave interference patterns and amplitude envelopes.
"""

import math
import random
import pygame
from core.enums import OilSwerveConstants


class OilSwervePhysics:
    """Manages the physics calculations for oil spill swerve effects.

    When a player drives over an oil spill, this system generates a chaotic
    swerve pattern using two interfering sine waves with randomized phase
    and decaying amplitude over time.
    """

    def __init__(self) -> None:
        """Initialize the oil swerve system in inactive state."""
        self._swerve_until: int = 0
        self._started_at: int = 0
        self._phase: float = 0.0
        self._duration_ms: int = 0

    @property
    def is_active(self) -> bool:
        """Check if oil swerve effect is currently active.

        Returns:
            True if the swerve period has not yet expired.
        """
        return pygame.time.get_ticks() < self._swerve_until

    @property
    def swerve_until(self) -> int:
        """Get the timestamp when swerve effect ends.

        Returns:
            Milliseconds timestamp when swerve expires.
        """
        return self._swerve_until

    def trigger(self, duration_ms: int) -> None:
        """Trigger a new oil swerve effect.

        Initializes the randomized phase and timing for a new swerve.
        If already swerving, extends the swerve duration.

        Args:
            duration_ms: Duration of the swerve effect in milliseconds.
        """
        now = pygame.time.get_ticks()

        # Randomize phase on first trigger
        if now >= self._swerve_until:
            self._started_at = now
            self._phase = random.uniform(0.0, math.tau)

        # Extend swerve duration
        self._swerve_until = max(self._swerve_until, now + duration_ms)
        self._duration_ms = duration_ms

    def calculate_steering(
        self,
        base_frequency: float,
        base_strength: float,
        is_out_of_control: bool
    ) -> float:
        """Calculate the current swerve steering value.

        Uses dual sine waves with frequency modulation and decaying amplitude
        envelope to create a chaotic but controlled swerve effect.

        Args:
            base_frequency: Base frequency from config.OIL_SWERVE_FREQUENCY.
            base_strength: Base strength from config.OIL_SWERVE_STRENGTH.
            is_out_of_control: If True, inverts the steering direction.

        Returns:
            The calculated steering value (-strength to +strength).
        """
        now = pygame.time.get_ticks()
        swerve_duration = max(1, self._duration_ms)
        elapsed = max(0, now - self._started_at)
        progress = min(1.0, elapsed / float(swerve_duration))

        # Amplitude envelope decays over time: 0.35 + (0.65 * (1.0 - progress))
        envelope = (
            OilSwerveConstants.ENVELOPE_BASE
            + (OilSwerveConstants.ENVELOPE_PROGRESS_MULTIPLIER * (1.0 - progress))
        )

        # Frequency increases slightly as effect decays
        frequency = base_frequency * (
            OilSwerveConstants.FREQUENCY_BASE_MULTIPLIER
            - (OilSwerveConstants.FREQUENCY_PROGRESS_MULTIPLIER * progress)
        )

        # Primary sine wave
        base_wave = math.sin((now * frequency) + self._phase)

        # Secondary sine wave (higher frequency, phase offset)
        secondary_wave = OilSwerveConstants.SECONDARY_WAVE_AMPLITUDE * math.sin(
            (now * frequency * OilSwerveConstants.SECONDARY_WAVE_FREQUENCY_MULT)
            + (self._phase * OilSwerveConstants.SECONDARY_WAVE_PHASE_MULT)
        )

        # Combined wave with envelope and strength
        target_steer = (base_wave + secondary_wave) * base_strength * envelope

        # Invert if out of control
        if is_out_of_control:
            target_steer = -target_steer

        return target_steer

    def reset(self) -> None:
        """Reset swerve system to inactive state."""
        self._swerve_until = 0
        self._started_at = 0
        self._phase = 0.0
        self._duration_ms = 0
