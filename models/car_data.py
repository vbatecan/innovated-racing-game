"""Car definitions and data for the car selection system."""

from dataclasses import dataclass
from typing import List


@dataclass
class CarStats:
    """Car performance statistics."""
    speed: float        # 0-100 (max speed multiplier)
    handling: float     # 0-100 (turn responsiveness)
    acceleration: float # 0-100 (how quickly it speeds up)
    weight: float       # 0-100 (affects braking and collision)


@dataclass
class Car:
    """Individual car definition."""
    id: int
    name: str
    stats: CarStats
    unlock_score: int   # Score needed to unlock this car
    color_hex: str      # Hex color for the car
    rarity: str         # Common, Rare, Epic, Legendary
    description: str    # Short description


# Define all available cars
CARS: List[Car] = [
    Car(
        id=1,
        name="Triky",
        stats=CarStats(speed=65, handling=75, acceleration=70, weight=48),
        unlock_score=0,
        color_hex="#8B7BB8",
        rarity="Common",
        description="Swift and reliable utility robot"
    ),
    Car(
        id=2,
        name="Speedster",
        stats=CarStats(speed=85, handling=60, acceleration=80, weight=40),
        unlock_score=5000,
        color_hex="#FF0000",
        rarity="Common",
        description="Fast and light, high speed"
    ),
    Car(
        id=3,
        name="Tank",
        stats=CarStats(speed=50, handling=55, acceleration=45, weight=95),
        unlock_score=10000,
        color_hex="#0066FF",
        rarity="Rare",
        description="Heavy and durable"
    ),
    Car(
        id=4,
        name="Phantom",
        stats=CarStats(speed=90, handling=85, acceleration=88, weight=35),
        unlock_score=15000,
        color_hex="#00FF00",
        rarity="Rare",
        description="Agile and responsive"
    ),
    Car(
        id=5,
        name="Thunderbolt",
        stats=CarStats(speed=95, handling=75, acceleration=92, weight=45),
        unlock_score=20000,
        color_hex="#FFFF00",
        rarity="Epic",
        description="Lightning fast acceleration"
    ),
    Car(
        id=6,
        name="Titan",
        stats=CarStats(speed=70, handling=65, acceleration=70, weight=85),
        unlock_score=25000,
        color_hex="#FF6600",
        rarity="Epic",
        description="Power and control balanced"
    ),
    Car(
        id=7,
        name="Shadow",
        stats=CarStats(speed=100, handling=95, acceleration=90, weight=30),
        unlock_score=30000,
        color_hex="#330066",
        rarity="Legendary",
        description="Ultimate performance machine"
    ),
    Car(
        id=8,
        name="Phoenix",
        stats=CarStats(speed=88, handling=90, acceleration=85, weight=38),
        unlock_score=40000,
        color_hex="#FF00FF",
        rarity="Legendary",
        description="Mythical beast of the road"
    ),
]


def get_car_by_id(car_id: int) -> Car | None:
    """Get a car by its ID."""
    for car in CARS:
        if car.id == car_id:
            return car
    return None


def get_unlocked_cars(best_score: int) -> List[Car]:
    """Get all cars unlocked for the given best score."""
    return [car for car in CARS if car.unlock_score <= best_score]


def get_next_unlock(best_score: int) -> Car | None:
    """Get the next car to unlock."""
    for car in CARS:
        if car.unlock_score > best_score:
            return car
    return None
