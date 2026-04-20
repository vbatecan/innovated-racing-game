# Car Selection System

## Overview

The car selection system provides a progressive unlock mechanism for racing cars based on player performance. Players can unlock new cars by reaching score milestones, each with unique stats affecting gameplay.

## Features

### 🔹 Car Selection Menu

- **Keyboard Controls**: Arrow Keys / A-D for navigation
- **Direct Selection**: Enter / Space to select or purchase
- **Mouse Support**: Click on cars or navigation arrows
- **Visual Feedback**: Highlight current selection with ★ indicator

### 🔹 Progressive Unlock System

- **Default**: First car (Starter) is unlocked by default
- **Unlock Intervals**: New cars unlock every 5,000 score points
- **Example Progression**:
  - Car 1 (Starter): 0 points ✓ Unlocked
  - Car 2 (Speedster): 5,000 points
  - Car 3 (Tank): 10,000 points
  - Car 4 (Phantom): 15,000 points
  - Car 5 (Thunderbolt): 20,000 points
  - Car 6 (Titan): 25,000 points
  - Car 7 (Shadow): 30,000 points
  - Car 8 (Phoenix): 40,000 points

### 🔹 Car Stats System

Each car has 4 main stats (0-100 scale):

- **Speed**: Affects maximum velocity
- **Handling**: Turn responsiveness
- **Acceleration**: Speed increase rate
- **Weight**: Vehicle mass (affects braking)

### 🔹 Rarity Tiers

- **Common**: Basic vehicles
- **Rare**: Enhanced stats
- **Epic**: High performance
- **Legendary**: Maximum power

### 🔹 Lock Mechanics

When a car is locked:

- Shows 🔒 lock symbol
- Appears grayed out
- Displays progress bar toward unlock
- Shows required score in format: "REACH {score} POINTS TO UNLOCK"

### 🔹 Unlock Animations

- Pulses 🎉 "NEW CAR UNLOCKED! 🎉" animation
- 3-second display duration
- Automatic dismissal

## Usage

### Opening Car Selection Menu

**During Gameplay:**

```
Press C - Open car selection menu
```

**After Game Over:**

```
Press ESC - Open car selection menu to pick a new car before respawning
```

### Controlling the Menu

```
← or A      - Select previous car
→ or D      - Select next car
ENTER       - Confirm selection
ESC         - Close menu without changing
Mouse       - Click on car or arrows to navigate
```

## Data Persistence

### Save File Location

`logs/car_save.json`

### Saved Data

```json
{
  "selected_car": 1,
  "unlocked_cars": [1, 2, 3]
}
```

### Best Score Storage

`logs/best_records.json` (existing system)

```json
{
  "survival": 25000
}
```

## Car Stats Impact

### Speed

- Range: 60-100
- Applied as: `max_speed = 10 + (stats.speed / 100) * 20`
- Example: Speedster (85) → max_speed = 27

### Handling

- Range: 55-95
- Applied as turn responsiveness smoothing
- Higher handling = faster steering response

### Acceleration

- Used in physics calculations
- Affects speed gain per frame
- Combined with gear ratios

### Weight

- Affects braking dynamics
- Higher weight = longer stopping distance
- Visual indicator of vehicle type

## Integration Points

### main.py

- Initialize `CarManager`
- Create `CarSelectionUI`
- Pass to `GameLoop`

### PlayerCar

- `_apply_car_stats()` method
- Applies selected car stats on creation
- Called when car is switched

### GameLoop

- `_initialize_car_selection()` - Setup callbacks
- `_check_and_handle_car_unlocks()` - Monitor for unlocks
- `_handle_events()` - Process menu input
- `_render()` - Draw menu overlay

### Scoring System

- Current score tracked in `_scoring_system`
- Best score stored in `CarManager`
- Unlocks triggered at score milestones

## API Reference

### CarManager

```python
# Initialize
car_manager = CarManager()

# Check unlock status
is_unlocked = car_manager.is_car_unlocked(car_id=2)

# Get selected car
selected = car_manager.get_selected_car()

# Select car
car_manager.select_car(car_id=3)  # Returns bool

# Get all unlocked cars
unlocked_list = car_manager.get_unlocked_cars()

# Update best score and get newly unlocked
newly_unlocked = car_manager.update_best_score(new_score=15000)

# Get unlock progress
progress = car_manager.get_unlock_progress(car_id=2)
# Returns: {
#   "unlock_score": 5000,
#   "current_score": 3500,
#   "is_unlocked": False,
#   "progress": 70
# }
```

### CarSelectionUI

```python
# Initialize
ui = CarSelectionUI(window_size, car_manager, font_large, font_small)

# Control
ui.open()           # Show menu
ui.close()          # Hide menu
ui.next_car()       # Navigate right
ui.previous_car()   # Navigate left

# Handle events
ui.handle_event(pygame.event.Event)

# Update and render
ui.update(delta_time)
ui.draw(surface)

# Callbacks
ui.selected_callback = lambda car: print(f"Selected {car.name}")
ui.close_callback = lambda: print("Menu closed")
```

### CarData

```python
from models.car_data import CARS, get_car_by_id

# Get specific car
car = get_car_by_id(2)
print(car.name, car.stats.speed)

# Get cars unlocked at score
unlocked = get_unlocked_cars(best_score=10000)

# Get next car to unlock
next_car = get_next_unlock(best_score=3500)
```

## Customization

### Adding New Cars

Edit `models/car_data.py`:

```python
Car(
    id=9,
    name="DeadBolt",
    stats=CarStats(
        speed=92,
        handling=88,
        acceleration=86,
        weight=42
    ),
    unlock_score=50000,
    color_hex="#FF0099",
    rarity="Legendary",
    description="Ultimate fusion of speed and control"
)
```

### Changing Unlock Intervals

Modify `unlock_score` values in car definitions or change the progression formula in `CarManager`.

### Adjusting Stats Impact

Modify the `_apply_car_stats()` method in `PlayerCar` class to change how stats affect gameplay.

### Customizing UI Colors

Edit `CarSelectionUI` class constants:

```python
self.COLOR_ACCENT = (0, 200, 255)      # Highlight color
self.COLOR_LOCKED = (100, 100, 100)    # Locked text
self.COLOR_UNLOCKED = (0, 255, 100)    # Unlocked indicator
```

## Performance Considerations

- Car assets are loaded once at game start
- UI rendering optimized with single-frame updates
- Save/load files use JSON for quick access
- Score checking happens every frame (minimal overhead)

## Future Enhancements

- Custom car paint colors
- Car upgrade system (buy performance upgrades with coins)
- Cosmetic customization (wheels, decals, etc.)
- Prestige/reset system
- Leaderboard integration
- Car-specific achievements
