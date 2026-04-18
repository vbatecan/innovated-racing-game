"""Car management system including save/load functionality."""

import json
import os
from typing import List, Optional

from models.car_data import Car, get_car_by_id, get_unlocked_cars
from models.upgrades import Car as UpgradeCar
from models.upgrades import UPGRADES, calculate_effective_stats


class CarManager:
    """Manages car selection, progression, upgrades, and persistence."""

    SAVE_FILE = "logs/car_save.json"
    BEST_RECORDS_FILE = "logs/best_records.json"
    LEGACY_SHOP_KEYS = (
        "owned_skins",
        "owned_boosts",
        "selected_skin",
        "equipped_boost",
        "skins_inventory",
        "boost_inventory",
    )

    def __init__(self):
        self.selected_car_id: int = 1
        self.best_score: float = 0.0
        self.unlocked_cars: List[int] = [1]

        # Shop economy + persistent upgrades.
        self.credits: int = 2400
        self.owned_upgrades: List[str] = []

        self.load()

    def load(self) -> None:
        """Load car selection, progression, and upgrade data."""
        if os.path.exists(self.BEST_RECORDS_FILE):
            try:
                with open(self.BEST_RECORDS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.best_score = float(data.get("survival", 0.0))
            except (json.JSONDecodeError, IOError, ValueError):
                self.best_score = 0.0

        legacy_fields_detected = False
        if os.path.exists(self.SAVE_FILE):
            try:
                with open(self.SAVE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    legacy_fields_detected = any(key in data for key in self.LEGACY_SHOP_KEYS)
                    self.selected_car_id = int(data.get("selected_car", 1))
                    self.unlocked_cars = list(data.get("unlocked_cars", [1]))
                    self.credits = int(data.get("credits", 2400 + int(self.best_score / 30)))

                    owned = data.get("owned_upgrades", [])
                    if isinstance(owned, list):
                        self.owned_upgrades = [u for u in owned if u in UPGRADES]
            except (json.JSONDecodeError, IOError, ValueError):
                self.selected_car_id = 1
                self.unlocked_cars = [1]
                self.credits = 2400 + int(self.best_score / 30)
                self.owned_upgrades = []
        else:
            self.credits = 2400 + int(self.best_score / 30)

        if self.selected_car_id not in self.unlocked_cars:
            self.selected_car_id = self.unlocked_cars[0] if self.unlocked_cars else 1

        self._update_unlocked_cars()

        if legacy_fields_detected:
            # Rewrite save without deprecated shop categories.
            self.save()

    def save(self) -> None:
        """Persist car, upgrade, and currency state."""
        os.makedirs("logs", exist_ok=True)
        data = {
            "selected_car": self.selected_car_id,
            "unlocked_cars": self.unlocked_cars,
            "credits": self.credits,
            "owned_upgrades": self.owned_upgrades,
        }

        try:
            with open(self.SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except IOError as exc:
            print(f"Failed to save car data: {exc}")

    def _update_unlocked_cars(self) -> None:
        unlocked = get_unlocked_cars(int(self.best_score))
        self.unlocked_cars = [car.id for car in unlocked]
        self.save()

    def update_best_score(self, new_score: float) -> List[Car]:
        """Update best score and grant small credit rewards for progression."""
        if new_score <= self.best_score:
            return []

        old_best = int(self.best_score)
        self.best_score = new_score

        # Reward incremental progress to support upgrade purchases.
        gained = max(0, int((new_score - old_best) / 10))
        if gained:
            self.credits += gained

        old_unlocked = {car.id for car in get_unlocked_cars(old_best)}
        new_unlocked = get_unlocked_cars(int(self.best_score))
        newly_unlocked = [car for car in new_unlocked if car.id not in old_unlocked]

        self._update_unlocked_cars()
        return newly_unlocked

    def get_selected_car(self) -> Optional[Car]:
        return get_car_by_id(self.selected_car_id)

    def select_car(self, car_id: int) -> bool:
        if car_id in self.unlocked_cars:
            self.selected_car_id = car_id
            self.save()
            return True
        return False

    def is_car_unlocked(self, car_id: int) -> bool:
        return car_id in self.unlocked_cars

    def get_unlocked_cars(self) -> List[Car]:
        return get_unlocked_cars(int(self.best_score))

    def get_unlock_progress(self, car_id: int) -> dict:
        car = get_car_by_id(car_id)
        if not car:
            return {}

        return {
            "unlock_score": car.unlock_score,
            "current_score": int(self.best_score),
            "is_unlocked": self.is_car_unlocked(car_id),
            "progress": min(100, int((self.best_score / car.unlock_score * 100))) if car.unlock_score > 0 else 100,
        }

    def has_upgrade(self, upgrade_id: str) -> bool:
        return upgrade_id in self.owned_upgrades

    def get_owned_upgrades(self) -> list[str]:
        return list(self.owned_upgrades)

    def purchase_upgrade(self, upgrade_id: str) -> tuple[bool, str]:
        upgrade = UPGRADES.get(upgrade_id)
        if upgrade is None:
            return False, "Unknown upgrade."
        if upgrade_id in self.owned_upgrades:
            return False, f"{upgrade.name} already installed."
        if self.credits < upgrade.price:
            return False, "Not enough credits."

        self.credits -= upgrade.price
        self.owned_upgrades.append(upgrade_id)
        self.save()
        return True, f"Installed {upgrade.name}."

    def get_base_performance_car(self) -> UpgradeCar:
        selected = self.get_selected_car()
        if selected is None:
            return UpgradeCar(speed=70.0, acceleration=70.0, handling=70.0, braking=70.0)

        return UpgradeCar(
            speed=float(selected.stats.speed),
            acceleration=float(selected.stats.acceleration),
            handling=float(selected.stats.handling),
            braking=float(selected.stats.braking),
        )

    def get_effective_performance_car(self) -> UpgradeCar:
        base = self.get_base_performance_car()
        return calculate_effective_stats(base, self.owned_upgrades)

    def get_upgrade_stat_comparison(self, preview_upgrade_id: str | None = None) -> tuple[UpgradeCar, UpgradeCar]:
        base = self.get_base_performance_car()
        owned = list(self.owned_upgrades)
        if preview_upgrade_id and preview_upgrade_id not in owned and preview_upgrade_id in UPGRADES:
            owned.append(preview_upgrade_id)
        return base, calculate_effective_stats(base, owned)

