from config import *


class Settings:
    def __init__(self):
        self.car_speed = CAR_SPEED
        self.max_fps = MAX_FPS
        self.show_camera = True
        self.obstacle_frequency = OBSTACLE_FREQUENCY
        self.steering_sensitivity = STEERING_SENSITIVITY
        self._vals = AVAILABLE_FPS

        # Physics
        self.ACCELERATION = ACCELERATION
        self.FRICTION = FRICTION
        self.BRAKE_STRENGTH = BRAKE_STRENGTH
        self.brake_sensitivity = BRAKE_SENSITIVITY  # 1 (Hard) to 10 (Easy)

    def get_brake_threshold(self):
        return 0.07 - (self.brake_sensitivity * 0.01)

    def increase_brake_sensitivity(self):
        self.brake_sensitivity = min(self.brake_sensitivity + 1, 10)

    def decrease_brake_sensitivity(self):
        self.brake_sensitivity = max(self.brake_sensitivity - 1, 1)

    def increase_speed(self):
        self.car_speed = min(self.car_speed + 1, 50)

    def decrease_speed(self):
        self.car_speed = max(self.car_speed - 1, 1)

    def toggle_camera(self):
        self.show_camera = not self.show_camera

    def increase_fps(self):
        vals = [30, 60, 120]
        try:
            idx = vals.index(self.max_fps)
            self.max_fps = vals[min(idx + 1, len(vals) - 1)]
        except ValueError:
            self.max_fps = 30

    def decrease_fps(self):
        try:
            idx = self._vals.index(self.max_fps)
            self.max_fps = self._vals[max(idx - 1, 0)]
        except ValueError:
            self.max_fps = 30

    def increase_obstacle_frequency(self):
        self.obstacle_frequency = min(self.obstacle_frequency + 1, 100)

    def decrease_obstacle_frequency(self):
        self.obstacle_frequency = max(self.obstacle_frequency - 1, 1)

    def increase_sensitivity(self):
        self.steering_sensitivity = min(self.steering_sensitivity + 0.1, 5.0)

    def decrease_sensitivity(self):
        self.steering_sensitivity = max(self.steering_sensitivity - 0.1, 0.1)
