import pygame
import os
from pathlib import Path

class SoundManager:
    def __init__(self, sfx_dir="resources/sfx/processed"):
        self.sfx_dir = Path(sfx_dir)
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
                if file.endswith(('.wav', '.ogg')):
                    path = Path(root) / file
                    # Use the filename without extension as the key, 
                    # but prepend the folder name for clarity (e.g., 'engine/engine_loop')
                    category = path.parent.relative_to(self.sfx_dir).name
                    name = path.stem
                    key = f"{category}/{name}"
                    try:
                        self.sounds[key] = pygame.mixer.Sound(str(path))
                    except Exception as e:
                        print(f"Error loading sound {path}: {e}")

    def play_sfx(self, key, volume=1.0):
        """Plays a one-shot sound effect."""
        sound = self.sounds.get(key)
        if sound:
            channel = pygame.mixer.find_channel()
            if channel:
                channel.set_volume(volume)
                channel.play(sound)
        else:
            print(f"Sound not found: {key}")

    def start_engine(self):
        """Starts the engine loop at idle."""
        # We'll use engine_loop as the base
        loop = self.sounds.get("engine/engine_loop")
        if loop:
            channel = pygame.mixer.find_channel()
            if channel:
                channel.play(loop, loops=-1)
                self.engine_channels["idle"] = channel
                self.current_engine_state = "idle"

    def update_engine(self, speed):
        """
        Adjusts engine sound based on speed.
        In a simple implementation, we modulate volume or switch loops.
        """
        if not self.engine_channels["idle"]:
            return

        # Example: Map speed to volume or switch loops
        # speed is assumed to be 0 to 1.0
        vol = 0.3 + (speed * 0.7)
        self.engine_channels["idle"].set_volume(vol)

    def stop_all(self):
        pygame.mixer.stop()

    def get_available_sounds(self):
        return list(self.sounds.keys())

# Singleton instance
sound_manager = None

def init_sound_manager():
    global sound_manager
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    sound_manager = SoundManager()
    return sound_manager
