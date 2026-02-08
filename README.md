# Features & Todo List

## Core Controls

- [x] **Reliable Braking**: Implement a distinct braking gesture (e.g., Crossed Arms, Open Palms, or specific hand sign).
- [ ] **Dynamic Throttle**: Control speed based on hand distance from camera or body lean angle.
- [ ] **Gear Shifting**: Add immersive gestures for shifting (e.g., "Punch" forward to upshift, tap shoulder to downshift).
- [ ] **Handbrake**: Extreme turn mechanic triggered by a specific gesture (e.g., both hands raised).

## Multiplayer (Single Camera)

- [ ] **Split-Screen Implementation**:
  - Divide single webcam feed vertically into two active zones.
  - Track two distinct player skeletons.
- [ ] **Interference Handling**: Visual divider in camera feed to prevent players from entering each other's control zones.

## Gameplay Loop

- [ ] **Dynamic Obstacles**:
  - Static: Rocks, Barriers.
  - Dynamic: Traffic, crossing animals.
  - Hazards: Oil slicks (inverts controls).
- [ ] **Power-ups**: Collectibles that require specific gestures to activate (e.g., "Boost", "Shield").
- [ ] **Biomes & Progression**: Procedural environment changes (City -> Highway -> Desert) to convey distance.
- [ ] **Game Modes**: Time Attack, Survival (Distance Run), and Head-to-Head Rivals.

## User Experience (UX) & Quality of Life

- [ ] **Calibration Screen**: Pre-game scene to record user specific "Neutral", "Max Left", and "Max Right" positions.
- [ ] **Visual Feedback (HUD)**:
  - Real-time skeleton overlay showing what the computer sees.
  - "Gesture Recognized" icons (e.g., Stop sign appears when braking).
  - Speedometer and gear indicator.
- [ ] **Menu Navigation**: Full gesture control for menus (Hover-to-select or Grab-to-select).

## Technical & Settings

- [ ] **Performance Tuning**: Graphics settings for 720p/1080p and FPS limits.
- [ ] **Model Sensitivity**: Options to adjust detection strictness for different lighting conditions.
