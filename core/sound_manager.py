import pygame
import os
from pathlib import Path


class SoundManager:
    def __init__(self, sfx_dir="resources/sfx/processed", settings=None):
        self.sfx_dir = Path(sfx_dir)
        self._settings = settings
        self._sfx_enabled = True
        self.sounds = {}
        self.engine_channels = {
            "idle": None,
            "mid": None,
            "high": None
        }
        self.current_engine_state = None
        self._load_assets()

    def _load_assets(self):
        """Recursively loads all sound files from the processed directory."""
        for root, _, files in os.walk(self.sfx_dir):
            for file in files:
                path = Path(root) / file
                if path.suffix.lower() not in (".wav", ".ogg", ".mp3"):
                    continue

                category = str(path.parent.relative_to(self.sfx_dir)).replace("\\", "/")
                name = path.stem
                key = f"{category}/{name}" if category != "." else name
                try:
                    self.sounds[key] = pygame.mixer.Sound(str(path))
                except Exception as e:
                    print(f"Error loading sound {path}: {e}")

    @staticmethod
    def _clamp01(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def _sfx_output_scale(self) -> float:
        """Compute effective SFX scale from runtime settings.

        A slight boost keeps SFX punchy even when source assets are quiet.
        """
        if self._settings is None:
            return 1.0

        master = self._clamp01(getattr(self._settings, "master_volume", 1.0))
        sfx = self._clamp01(getattr(self._settings, "sfx_volume", 1.0))
        boost = 1.35
        return self._clamp01(master * sfx * boost)

    def _effective_sfx_volume(self, volume: float) -> float:
        return self._clamp01(float(volume) * self._sfx_output_scale())

    def set_sfx_enabled(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled == self._sfx_enabled:
            return

        self._sfx_enabled = enabled
        if not enabled:
            self.stop_all()
            self.stop_engine()

    @staticmethod
    def _normalize_key(key: str) -> str:
        normalized = str(key).strip().replace("\\", "/")
        if normalized.startswith("./"):
            normalized = normalized[2:]
        return normalized.lstrip("/")

    def _resolve_key(self, key: str) -> str:
        normalized = self._normalize_key(key)
        if normalized in self.sounds:
            return normalized

        stem, _ext = os.path.splitext(normalized)
        if stem in self.sounds:
            return stem

        return normalized

    def play_sfx(self, key, volume=1.0):
        """Plays a one-shot sound effect."""
        if not self._sfx_enabled:
            return

        resolved_key = self._resolve_key(key)
        sound = self.sounds.get(resolved_key)
        if sound:
            channel = pygame.mixer.find_channel()
            if channel:
                channel.set_volume(self._effective_sfx_volume(volume))
                channel.play(sound)
        else:
            print(f"Sound not found: {key} (resolved: {resolved_key})")

    def play_ui_click(self, volume: float = 1.0) -> None:
        """Play the standard UI click/toggle sound."""
        for key in ("ui/toggle", "ui/click", "ui/button_click"):
            if key in self.sounds:
                self.play_sfx(key, volume)
                return

        self.play_sfx("ui/toggle", volume)

    def start_engine(self):
        """Starts the engine loop at idle."""
        if not self._sfx_enabled:
            return

        if self.engine_channels["idle"] and self.engine_channels["idle"].get_busy():
            return

        loop = self.sounds.get("engine/engine_loop")
        if loop:
            channel = pygame.mixer.find_channel()
            if channel:
                channel.play(loop, loops=-1)
                self.engine_channels["idle"] = channel
                self.current_engine_state = "idle"

    def stop_engine(self) -> None:
        idle_channel = self.engine_channels.get("idle")
        if idle_channel:
            idle_channel.stop()
        self.engine_channels["idle"] = None
        self.current_engine_state = None

    def update_engine(self, speed):
        """
        Adjusts engine sound based on speed.
        In a simple implementation, we modulate volume or switch loops.
        """
        if not self._sfx_enabled:
            return

        if not self.engine_channels["idle"] or not self.engine_channels["idle"].get_busy():
            self.start_engine()
        if not self.engine_channels["idle"]:
            return

        normalized_speed = self._clamp01(speed)
        base_volume = 0.32 + (normalized_speed * 0.68)
        self.engine_channels["idle"].set_volume(self._effective_sfx_volume(base_volume))

    def stop_all(self):
        pygame.mixer.stop()

    def get_available_sounds(self):
        return list(self.sounds.keys())

sound_manager = None

def init_sound_manager(settings=None):
    global sound_manager
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    sound_manager = SoundManager(settings=settings)
    return sound_manager
