"""Upgrade system data and stat computation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Car:
    """Runtime car performance profile used for physics and comparison UI."""

    speed: float
    acceleration: float
    handling: float
    braking: float


@dataclass(frozen=True)
class Upgrade:
    """Defines additive and multiplicative bonuses for a performance upgrade."""

    id: str
    name: str
    price: int
    speed_bonus: float = 0.0
    acceleration_bonus: float = 0.0
    handling_bonus: float = 0.0
    braking_bonus: float = 0.0
    speed_multiplier: float = 1.0
    acceleration_multiplier: float = 1.0
    handling_multiplier: float = 1.0
    braking_multiplier: float = 1.0


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


UPGRADES: dict[str, Upgrade] = {
    "turbo_charger": Upgrade(
        id="turbo_charger",
        name="Turbo Charger",
        price=980,
        speed_bonus=10.0,
        acceleration_bonus=16.0,
        speed_multiplier=1.10,
        acceleration_multiplier=1.22,
    ),
    "sport_suspension": Upgrade(
        id="sport_suspension",
        name="Sport Suspension",
        price=740,
        handling_bonus=18.0,
        braking_bonus=4.0,
        handling_multiplier=1.16,
    ),
    "precision_brakes": Upgrade(
        id="precision_brakes",
        name="Precision Brakes",
        price=620,
        braking_bonus=22.0,
        handling_bonus=5.0,
        braking_multiplier=1.18,
    ),
}


def get_upgrade(upgrade_id: str) -> Upgrade | None:
    """Return a configured upgrade by ID."""
    return UPGRADES.get(upgrade_id)


def calculate_effective_stats(base: Car, upgrade_ids: Iterable[str]) -> Car:
    """Apply all upgrade bonuses to a base car profile."""
    speed = base.speed
    acceleration = base.acceleration
    handling = base.handling
    braking = base.braking

    speed_mul = 1.0
    accel_mul = 1.0
    handling_mul = 1.0
    braking_mul = 1.0

    for upgrade_id in upgrade_ids:
        upgrade = get_upgrade(upgrade_id)
        if upgrade is None:
            continue
        speed += upgrade.speed_bonus
        acceleration += upgrade.acceleration_bonus
        handling += upgrade.handling_bonus
        braking += upgrade.braking_bonus
        speed_mul *= upgrade.speed_multiplier
        accel_mul *= upgrade.acceleration_multiplier
        handling_mul *= upgrade.handling_multiplier
        braking_mul *= upgrade.braking_multiplier

    return Car(
        speed=_clamp(speed * speed_mul),
        acceleration=_clamp(acceleration * accel_mul),
        handling=_clamp(handling * handling_mul),
        braking=_clamp(braking * braking_mul),
    )
