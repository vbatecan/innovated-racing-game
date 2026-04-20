from __future__ import annotations

import json
import os
from typing import Any

import pygame
from pygame.event import Event

from config import (
    ACCELERATION,
    AVAILABLE_FPS,
    BRAKE_SENSITIVITY,
    BRAKE_STRENGTH,
    CAR_SPEED,
    FRICTION,
    LANE_COUNT,
    MAX_FPS,
    MAX_LANE_COUNT,
    MIN_LANE_COUNT,
    OBSTACLE_FREQUENCY,
    STEERING_SENSITIVITY,
    WINDOW_SIZE,
)


class Settings:
    """Runtime settings with persistence and instant-apply helpers."""

    SAVE_FILE = "logs/user_settings.json"

    def __init__(self):
        self._vals = AVAILABLE_FPS

        defaults = self._defaults()
        for key, value in defaults.items():
            setattr(self, key, value)

        self.load()
        self.apply_audio_settings()

    @staticmethod
    def _defaults() -> dict[str, Any]:
        return {
            "car_speed": CAR_SPEED,
            "max_fps": MAX_FPS,
            "show_camera": True,
            "obstacle_frequency": OBSTACLE_FREQUENCY,
            "lane_count": LANE_COUNT,
            "steering_sensitivity": STEERING_SENSITIVITY,
            "ACCELERATION": ACCELERATION,
            "FRICTION": FRICTION,
            "BRAKE_STRENGTH": BRAKE_STRENGTH,
            "brake_sensitivity": BRAKE_SENSITIVITY,
            "visible": False,
            "fullscreen": False,
            "vsync": False,
            "resolution": [WINDOW_SIZE["width"], WINDOW_SIZE["height"]],
            "master_volume": 1.00,
            "music_volume": 1.00,
            "sfx_volume": 0.50,
            "difficulty": "Normal",
            "auto_brake_assist": False,
            "steering_assist": True,
            "camera_mode": "Chase",
            "graphics_preset": "High",
            "show_fps": False,
            "last_music_track": "",
            "_bonus": 50,
            "car_collision_deduction_pts": 100,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "car_speed": self.car_speed,
            "max_fps": self.max_fps,
            "show_camera": self.show_camera,
            "obstacle_frequency": self.obstacle_frequency,
            "lane_count": self.lane_count,
            "steering_sensitivity": self.steering_sensitivity,
            "ACCELERATION": self.ACCELERATION,
            "FRICTION": self.FRICTION,
            "BRAKE_STRENGTH": self.BRAKE_STRENGTH,
            "brake_sensitivity": self.brake_sensitivity,
            "fullscreen": self.fullscreen,
            "vsync": self.vsync,
            "resolution": list(self.resolution),
            "master_volume": self.master_volume,
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            "difficulty": self.difficulty,
            "auto_brake_assist": self.auto_brake_assist,
            "steering_assist": self.steering_assist,
            "camera_mode": self.camera_mode,
            "graphics_preset": self.graphics_preset,
            "show_fps": self.show_fps,
            "last_music_track": self.last_music_track,
        }

    def load(self) -> None:
        defaults = self._defaults()
        if not os.path.exists(self.SAVE_FILE):
            return

        try:
            with open(self.SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        for key, default_value in defaults.items():
            if key not in data:
                continue
            setattr(self, key, data[key])

        self.resolution = [int(self.resolution[0]), int(self.resolution[1])]
        self.max_fps = int(self.max_fps)
        self.car_speed = float(self.car_speed)
        self.obstacle_frequency = max(1, int(self.obstacle_frequency))
        self.lane_count = max(MIN_LANE_COUNT, min(MAX_LANE_COUNT, int(self.lane_count)))
        self.last_music_track = str(self.last_music_track)
        if "last_music_track" not in data and "last_radio_track" in data:
            self.last_music_track = str(data.get("last_radio_track", ""))

    def save(self) -> None:
        os.makedirs("logs", exist_ok=True)
        try:
            with open(self.SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
        except OSError:
            pass

    def reset_section(self, section: str) -> None:
        defaults = self._defaults()
        section_map = {
            "Audio": ["master_volume", "music_volume", "sfx_volume"],
            "Graphics": ["fullscreen", "vsync", "resolution", "graphics_preset", "max_fps", "show_camera"],
            "Gameplay": [
                "difficulty",
                "auto_brake_assist",
                "steering_assist",
                "camera_mode",
                "obstacle_frequency",
                "brake_sensitivity",
                "steering_sensitivity",
            ],
        }
        for key in section_map.get(section, []):
            setattr(self, key, defaults[key])

    def apply_audio_settings(self) -> None:
        if not pygame.mixer.get_init():
            return

        master = max(0.0, min(1.0, float(self.master_volume)))
        music = max(0.0, min(1.0, float(self.music_volume)))
        sfx = max(0.0, min(1.0, float(self.sfx_volume)))

        pygame.mixer.music.set_volume(master * music)
        channel_count = pygame.mixer.get_num_channels()
        for idx in range(channel_count):
            pygame.mixer.Channel(idx).set_volume(master * sfx)

    def apply_display_settings(
        self,
        resolution: tuple[int, int] | None = None,
        fullscreen: bool | None = None,
        vsync: bool | None = None,
    ) -> None:
        surface = pygame.display.get_surface()

        if resolution is not None:
            self.resolution = [int(resolution[0]), int(resolution[1])]
        if fullscreen is not None:
            self.fullscreen = bool(fullscreen)
        if vsync is not None:
            self.vsync = bool(vsync)

        if surface is None:
            return

        flags = pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
        size = (int(self.resolution[0]), int(self.resolution[1]))

        current_size = surface.get_size()
        current_fullscreen = bool(surface.get_flags() & pygame.FULLSCREEN)
        if current_size == size and current_fullscreen == self.fullscreen:
            return

        try:
            pygame.display.set_mode(size, flags, vsync=1 if self.vsync else 0)
        except TypeError:
            pygame.display.set_mode(size, flags)

    def set_fullscreen(self, fullscreen: bool):
        self.apply_display_settings(fullscreen=fullscreen)

    def get_difficulty_obstacle_multiplier(self) -> float:
        return {
            "Easy": 1.25,
            "Normal": 1.0,
            "Hard": 0.8,
        }.get(self.difficulty, 1.0)

    def get_difficulty_acceleration_multiplier(self) -> float:
        return {
            "Easy": 1.06,
            "Normal": 1.0,
            "Hard": 0.94,
        }.get(self.difficulty, 1.0)

    def get_camera_preview_size(self) -> tuple[int, int]:
        return {
            "Close": (220, 165),
            "Chase": (180, 135),
            "Far": (145, 100),
            "Off": (0, 0),
        }.get(self.camera_mode, (180, 135))

    def get_brake_threshold(self):
        return 0.07 - (self.brake_sensitivity * 0.01)

    def increase_brake_sensitivity(self):
        self.brake_sensitivity = min(self.brake_sensitivity + 1, 10)

    def decrease_brake_sensitivity(self):
        self.brake_sensitivity = max(self.brake_sensitivity - 1, 1)

    def increase_car_speed(self):
        self.car_speed = min(self.car_speed + 1, 50)

    def decrease_car_speed(self):
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
        self.obstacle_frequency += 1

    def decrease_obstacle_frequency(self):
        if self.obstacle_frequency > 1:
            self.obstacle_frequency -= 1

    def increase_lane_count(self):
        self.lane_count = min(self.lane_count + 1, MAX_LANE_COUNT)

    def decrease_lane_count(self):
        self.lane_count = max(self.lane_count - 1, MIN_LANE_COUNT)

    def increase_sensitivity(self):
        self.steering_sensitivity = min(self.steering_sensitivity + 0.1, 5.0)

    def decrease_sensitivity(self):
        self.steering_sensitivity = max(self.steering_sensitivity - 0.1, 0.1)

    def increase_points__increment(self, points):
        self._bonus += points

    def decrease_points__increment(self, deduct):
        self._bonus -= deduct

    def draw_settings_menu(self, *args, **kwargs):
        _ = args
        _ = kwargs

    def handle_event(
        self,
        event: Event,
        running: bool,
        selected_setting: int | Any,
        setting_options: list[str],
        show_settings: bool,
    ) -> tuple[bool, int | Any, bool]:
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

        _ = selected_setting
        _ = setting_options
        return running, selected_setting, show_settings







