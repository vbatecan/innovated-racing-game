"""Car definitions and data for the car selection system."""

from dataclasses import dataclass
from typing import List


@dataclass
class CarStats:
    """Car performance statistics."""

    speed: float        # 0-100 (max speed multiplier)
    handling: float     # 0-100 (turn responsiveness)
    acceleration: float # 0-100 (how quickly it speeds up)
    braking: float      # 0-100 (brake control and stopping power)
    weight: float       # 0-100 (visual/legacy display value)


@dataclass
class Car:
    """Individual car definition."""

    id: int
    name: str
    stats: CarStats
    unlock_score: int
    color_hex: str
    rarity: str
    description: str
    image_path: str


CARS: List[Car] = [
    Car(
        id=1,
        name="Triky",
        stats=CarStats(speed=100, handling=75, acceleration=70, braking=72, weight=48),
        unlock_score=0,
        color_hex="#8B7BB8",
        rarity="Common",
        description="Swift and reliable utility robot",
        image_path="resources/models/transparent/tricy.png",
    ),
    Car(
        id=2,
        name="Speedster",
        stats=CarStats(speed=85, handling=60, acceleration=80, braking=62, weight=40),
        unlock_score=5000,
        color_hex="#FF0000",
        rarity="Common",
        description="Fast and light, high speed",
        image_path="resources/models/sports_car.png",
    ),
    Car(
        id=3,
        name="Tank",
        stats=CarStats(speed=50, handling=55, acceleration=45, braking=84, weight=95),
        unlock_score=10000,
        color_hex="#0066FF",
        rarity="Rare",
        description="Heavy and durable",
        image_path="resources/models/transparent/truck1.png",
    ),
    Car(
        id=4,
        name="Phantom",
        stats=CarStats(speed=90, handling=85, acceleration=88, braking=74, weight=35),
        unlock_score=15000,
        color_hex="#00FF00",
        rarity="Rare",
        description="Agile and responsive",
        image_path="resources/models/police.png",
    ),
    Car(
        id=5,
        name="Thunderbolt",
        stats=CarStats(speed=95, handling=75, acceleration=92, braking=70, weight=45),
        unlock_score=20000,
        color_hex="#FFFF00",
        rarity="Epic",
        description="Lightning fast acceleration",
        image_path="resources/models/car5.png",
    ),
    Car(
        id=6,
        name="Titan",
        stats=CarStats(speed=70, handling=65, acceleration=70, braking=82, weight=85),
        unlock_score=25000,
        color_hex="#FF6600",
        rarity="Epic",
        description="Power and control balanced",
        image_path="resources/models/van.png",
    ),
    Car(
        id=7,
        name="Shadow",
        stats=CarStats(speed=100, handling=95, acceleration=90, braking=78, weight=30),
        unlock_score=30000,
        color_hex="#330066",
        rarity="Legendary",
        description="Ultimate performance machine",
        image_path="resources/models/transparent/car2.png",
    ),
    Car(
        id=8,
        name="Phoenix",
        stats=CarStats(speed=88, handling=90, acceleration=85, braking=76, weight=38),
        unlock_score=40000,
        color_hex="#FF00FF",
        rarity="Legendary",
        description="Mythical beast of the road",
        image_path="resources/models/ambulance.png",
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
