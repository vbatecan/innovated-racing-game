class Settings:
    def __init__(self):
        self.car_speed = 10
        self.max_fps = 30
        self.show_camera = True
        self.obstacle_frequency = 30
        self.steering_sensitivity = 1.0
        self._vals = [30, 60, 120]

        # Physics
        self.ACCELERATION = 0.2
        self.FRICTION = 0.05
        self.BRAKE_STRENGTH = 0.5
        self.brake_sensitivity = 5  # 1 (Hard) to 10 (Easy)

    def get_brake_threshold(self):
        # Map sensitivity 1-10 to threshold 0.06 to -0.03
        # High sens = Low threshold (easier to trigger)
        # 5 -> 0.02
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
        self.obstacle_frequency = min(self.obstacle_frequency + 5, 120)

    def decrease_obstacle_frequency(self):
        self.obstacle_frequency = max(self.obstacle_frequency - 5, 5)

    def increase_sensitivity(self):
        self.steering_sensitivity = min(self.steering_sensitivity + 0.1, 5.0)

    def decrease_sensitivity(self):
        self.steering_sensitivity = max(self.steering_sensitivity - 0.1, 0.1)
