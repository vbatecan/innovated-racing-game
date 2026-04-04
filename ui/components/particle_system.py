"""Particle system for animated background effects.

Provides particle emitters for creating dynamic, immersive background
animations with minimal performance impact.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

from ui.core.types import Color, Surface


@dataclass
class Particle:
    """Represents a single particle in the system."""
    x: float
    y: float
    vx: float  # Velocity X
    vy: float  # Velocity Y
    life: float  # Remaining lifetime (0.0 to 1.0)
    max_life: float
    color: Color
    size: float

    @property
    def alpha(self) -> int:
        """Calculate particle opacity based on remaining life."""
        return int((self.life / self.max_life) * 255)

    def update(self, delta_time: float) -> None:
        """Update particle position and lifetime.
        
        Args:
            delta_time: Time elapsed since last update in seconds.
        """
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time
        self.vy += 20 * delta_time  # Slight gravity
        self.life -= delta_time

    def draw(self, surface: Surface) -> None:
        """Draw the particle with fade effect.
        
        Args:
            surface: The pygame surface to draw on.
        """
        # Create particle surface with alpha
        particle_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(
            particle_surf,
            self.color + (self.alpha,),
            (int(self.size), int(self.size)),
            int(self.size)
        )
        surface.blit(particle_surf, (int(self.x - self.size), int(self.y - self.size)))


class ParticleSystem:
    """Manages a collection of particles for background effects."""

    def __init__(self, max_particles: int = 100) -> None:
        """Initialize the particle system.
        
        Args:
            max_particles: Maximum number of particles to maintain.
        """
        self.particles: list[Particle] = []
        self.max_particles: int = max_particles
        self.emission_rate: float = 10.0

    def emit(
        self,
        x: float,
        y: float,
        count: int = 1,
        velocity_range: tuple[float, float] = (-30, 30),
        color: Color = (92, 220, 255),
        size_range: tuple[float, float] = (1, 3),
        life: float = 2.0,
    ) -> None:
        """Emit particles from a position.
        
        Args:
            x: X position of emission.
            y: Y position of emission.
            count: Number of particles to emit.
            velocity_range: (min, max) velocity in pixels/sec.
            color: Particle color.
            size_range: (min, max) particle size.
            life: Particle lifetime in seconds.
        """
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break

            particle = Particle(
                x=x + random.uniform(-5, 5),
                y=y + random.uniform(-5, 5),
                vx=random.uniform(velocity_range[0], velocity_range[1]),
                vy=random.uniform(velocity_range[0] * 0.5, velocity_range[1] * 0.5),
                life=life,
                max_life=life,
                color=color,
                size=random.uniform(size_range[0], size_range[1]),
            )
            self.particles.append(particle)

    def update(self, delta_time: float) -> None:
        """Update all particles and remove dead ones.
        
        Args:
            delta_time: Time elapsed since last update in seconds.
        """
        # Update particles
        for particle in self.particles:
            particle.update(delta_time)

        # Remove dead particles
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surface: Surface) -> None:
        """Draw all active particles.
        
        Args:
            surface: The pygame surface to draw on.
        """
        for particle in self.particles:
            particle.draw(surface)


class BackgroundEffect:
    """Creates ambient particle effects for immersive backgrounds."""

    def __init__(self, width: int, height: int) -> None:
        """Initialize background effect.
        
        Args:
            width: Screen width.
            height: Screen height.
        """
        self.width: int = width
        self.height: int = height
        self.particle_system: ParticleSystem = ParticleSystem(max_particles=200)
        self.emission_timer: float = 0.0
        self.emission_interval: float = 0.1
        self._setup_emitters()

    def _setup_emitters(self) -> None:
        """Set up emission points around the screen."""
        # Emitters will be triggered periodically
        pass

    def update(self, delta_time: float) -> None:
        """Update background effects.
        
        Args:
            delta_time: Time elapsed since last update in seconds.
        """
        self.emission_timer += delta_time

        # Emit particles periodically from random positions
        if self.emission_timer >= self.emission_interval:
            self.emission_timer = 0.0

            # Create floating particles from edges
            if random.random() < 0.6:
                x = random.uniform(0, self.width)
                y = random.uniform(-20, self.height + 20)

                # Determine color (cyan, purple, or green)
                colors = [
                    (92, 220, 255),    # Cyan
                    (160, 100, 255),   # Purple
                    (80, 220, 160),    # Green
                ]
                color = random.choice(colors)

                self.particle_system.emit(
                    x, y,
                    count=random.randint(1, 3),
                    velocity_range=(-10, 10),
                    color=color,
                    size_range=(0.5, 2),
                    life=random.uniform(1.5, 3.0),
                )

        self.particle_system.update(delta_time)

    def draw(self, surface: Surface) -> None:
        """Draw background effects.
        
        Args:
            surface: The pygame surface to draw on.
        """
        self.particle_system.draw(surface)
