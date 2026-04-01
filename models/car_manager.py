"""Car management system including save/load functionality."""

import json
import os
from typing import List, Optional
from models.car_data import Car, CARS, get_car_by_id, get_unlocked_cars


class CarManager:
    """Manages car selection, unlocking, and persistence."""
    
    SAVE_FILE = "logs/car_save.json"
    BEST_RECORDS_FILE = "logs/best_records.json"
    
    def __init__(self):
        """Initialize the car manager."""
        self.selected_car_id: int = 1  # Default to first car
        self.best_score: float = 0.0
        self.unlocked_cars: List[int] = [1]  # First car always unlocked
        self.load()
    
    def load(self) -> None:
        """Load car selection and best score from files."""
        # Load best score
        if os.path.exists(self.BEST_RECORDS_FILE):
            try:
                with open(self.BEST_RECORDS_FILE, 'r') as f:
                    data = json.load(f)
                    self.best_score = float(data.get("survival", 0.0))
            except (json.JSONDecodeError, IOError):
                self.best_score = 0.0
        
        # Load car save data
        if os.path.exists(self.SAVE_FILE):
            try:
                with open(self.SAVE_FILE, 'r') as f:
                    data = json.load(f)
                    self.selected_car_id = int(data.get("selected_car", 1))
                    self.unlocked_cars = list(data.get("unlocked_cars", [1]))
            except (json.JSONDecodeError, IOError):
                self.selected_car_id = 1
                self.unlocked_cars = [1]
        
        # Ensure the selected car is actually unlocked
        if self.selected_car_id not in self.unlocked_cars:
            self.selected_car_id = self.unlocked_cars[0] if self.unlocked_cars else 1
        
        # Sync unlocked cars with best score
        self._update_unlocked_cars()
    
    def save(self) -> None:
        """Save car selection to file."""
        os.makedirs("logs", exist_ok=True)
        
        data = {
            "selected_car": self.selected_car_id,
            "unlocked_cars": self.unlocked_cars
        }
        
        try:
            with open(self.SAVE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Failed to save car data: {e}")
    
    def _update_unlocked_cars(self) -> None:
        """Update unlocked cars based on best score."""
        unlocked = get_unlocked_cars(int(self.best_score))
        self.unlocked_cars = [car.id for car in unlocked]
        self.save()
    
    def update_best_score(self, new_score: float) -> List[Car]:
        """
        Update best score and return newly unlocked cars.
        
        Args:
            new_score: The new best score
            
        Returns:
            List of newly unlocked cars
        """
        if new_score <= self.best_score:
            return []
        
        old_best = int(self.best_score)
        self.best_score = new_score
        
        old_unlocked = set(get_unlocked_cars(old_best))
        new_unlocked = set(get_unlocked_cars(int(self.best_score)))
        
        newly_unlocked = [car for car in new_unlocked if car not in old_unlocked]
        
        self._update_unlocked_cars()
        
        return newly_unlocked
    
    def get_selected_car(self) -> Optional[Car]:
        """Get the currently selected car."""
        return get_car_by_id(self.selected_car_id)
    
    def select_car(self, car_id: int) -> bool:
        """
        Select a car (only if unlocked).
        
        Args:
            car_id: ID of car to select
            
        Returns:
            True if selection was successful
        """
        if car_id in self.unlocked_cars:
            self.selected_car_id = car_id
            self.save()
            return True
        return False
    
    def is_car_unlocked(self, car_id: int) -> bool:
        """Check if a car is unlocked."""
        return car_id in self.unlocked_cars
    
    def get_unlocked_cars(self) -> List[Car]:
        """Get all unlocked cars."""
        return get_unlocked_cars(int(self.best_score))
    
    def get_unlock_progress(self, car_id: int) -> dict:
        """
        Get unlock progress for a specific car.
        
        Args:
            car_id: ID of the car
            
        Returns:
            Dict with unlock_score, current_score, is_unlocked
        """
        car = get_car_by_id(car_id)
        if not car:
            return {}
        
        return {
            "unlock_score": car.unlock_score,
            "current_score": int(self.best_score),
            "is_unlocked": self.is_car_unlocked(car_id),
            "progress": min(100, int((self.best_score / car.unlock_score * 100))) if car.unlock_score > 0 else 100
        }
