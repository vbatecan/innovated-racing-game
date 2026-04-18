from __future__ import annotations

import glob
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pygame


@dataclass
class RadioTrack:
    source: str
    title: str
    artist: str
    path: str


class RadioPlayer:
    """Handles local radio playback for soundtrack tracks."""

    TARGET_TRACK = "Hawak mo ang beat"
    TARGET_URL = "https://www.youtube.com/watch?v=9Tyq9k5FdYU&list=RD9Tyq9k5FdYU&start_radio=1"
    CACHE_DIR = "logs/radio_cache"

    def __init__(self, settings) -> None:
        self._settings = settings
        self._tracks: list[RadioTrack] = []
        self._current_index = 0
        self._target_index: Optional[int] = None
        self._paused = False
        self._status = "Radio ready"

        self._ensure_mixer()
        self._load_local_tracks()

        self._settings.radio_enabled = bool(getattr(self._settings, "radio_enabled", True))
        self._settings.radio_volume = float(getattr(self._settings, "radio_volume", 0.70))
        self._settings.radio_volume = max(0.0, min(1.0, self._settings.radio_volume))
        self._apply_volume()

        # Ensure the requested song exists locally, using the provided source URL as fallback.
        matched = self._index_of_track(self.TARGET_TRACK)
        if matched is None:
            downloaded = self._download_target_track()
            if downloaded is not None:
                self._tracks.append(
                    RadioTrack(
                        source="youtube",
                        title=self.TARGET_TRACK,
                        artist="YouTube",
                        path=downloaded,
                    )
                )
                matched = len(self._tracks) - 1

        if not self._tracks:
            self._status = "No playable tracks found."
            return

        if matched is not None:
            self._target_index = matched
            self._current_index = matched
            self._status = f"Ready: {self.TARGET_TRACK}"
        else:
            self._target_index = 0
            self._current_index = 0
            self._status = f"{self.TARGET_TRACK} not found. Using first track."

        if self._settings.radio_enabled:
            self._start_track(self._current_index, fade_ms=250)

    @property
    def status(self) -> str:
        return self._status

    @property
    def is_on(self) -> bool:
        return bool(self._settings.radio_enabled)

    @property
    def volume(self) -> float:
        return float(self._settings.radio_volume)

    @property
    def current_track(self) -> Optional[RadioTrack]:
        if not self._tracks:
            return None
        return self._tracks[self._current_index]

    def update(self) -> None:
        if not self._settings.radio_enabled or self._paused:
            return
        if not self._tracks:
            return
        if not pygame.mixer.get_init():
            return

        self._enforce_target_index()
        if not pygame.mixer.music.get_busy():
            # Always replay the selected target track.
            self._start_track(self._current_index, fade_ms=220)

    def toggle_power(self) -> None:
        self._settings.radio_enabled = not self._settings.radio_enabled
        if self._settings.radio_enabled:
            self._enforce_target_index()
            if self._tracks:
                self._start_track(self._current_index, fade_ms=400)
            self._status = "Radio on"
        else:
            if pygame.mixer.get_init():
                pygame.mixer.music.fadeout(350)
            self._status = "Radio off"
        self._settings.save()

    def toggle_pause(self) -> None:
        if not self._settings.radio_enabled:
            self._status = "Radio is off"
            return
        if not pygame.mixer.get_init() or not self._tracks:
            self._status = "No track available"
            return

        if self._paused:
            pygame.mixer.music.unpause()
            self._paused = False
            self._status = "Playback resumed"
        else:
            pygame.mixer.music.pause()
            self._paused = True
            self._status = "Playback paused"

    def next_track(self) -> None:
        if not self._tracks:
            self._status = "No tracks in queue"
            return
        # Locked playback: keep this one track always.
        self._enforce_target_index()
        if self._settings.radio_enabled:
            self._start_track(self._current_index, fade_ms=250)

    def previous_track(self) -> None:
        if not self._tracks:
            self._status = "No tracks in queue"
            return
        # Locked playback: keep this one track always.
        self._enforce_target_index()
        if self._settings.radio_enabled:
            self._start_track(self._current_index, fade_ms=250)

    def adjust_volume(self, delta: float) -> None:
        self._settings.radio_volume = max(0.0, min(1.0, float(self._settings.radio_volume) + delta))
        self._apply_volume()
        self._settings.save()

    def _normalize(self, text: str) -> str:
        return " ".join(text.lower().replace("_", " ").replace("-", " ").split())

    def _index_of_track(self, query: str) -> Optional[int]:
        needle = self._normalize(query)
        for idx, track in enumerate(self._tracks):
            if self._normalize(track.title) == needle:
                return idx
        for idx, track in enumerate(self._tracks):
            if needle in self._normalize(track.title):
                return idx
        return None

    def _enforce_target_index(self) -> None:
        if not self._tracks:
            return
        if self._target_index is None:
            self._target_index = 0
        self._target_index = max(0, min(self._target_index, len(self._tracks) - 1))
        self._current_index = self._target_index

    def _ensure_mixer(self) -> None:
        if pygame.mixer.get_init():
            return
        try:
            pygame.mixer.init()
        except pygame.error:
            self._status = "Audio device unavailable"

    def _load_local_tracks(self) -> None:
        music_dir = Path("resources") / "music"
        if not music_dir.exists():
            return

        exts = ("*.mp3", "*.ogg", "*.wav")
        files: list[str] = []
        for ext in exts:
            files.extend(glob.glob(str(music_dir / ext)))

        for path in sorted(files):
            title = Path(path).stem.replace("_", " ")
            self._tracks.append(
                RadioTrack(
                    source="local",
                    title=title,
                    artist="Game Soundtrack",
                    path=path,
                )
            )

    def _download_target_track(self) -> Optional[str]:
        try:
            from yt_dlp import YoutubeDL
        except Exception:
            self._status = "yt-dlp missing; cannot fetch target track"
            return None

        os.makedirs(self.CACHE_DIR, exist_ok=True)
        outtmpl = os.path.join(self.CACHE_DIR, "hawak-mo-ang-beat.%(ext)s")
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "restrictfilenames": True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(self.TARGET_URL, download=True)
        except Exception as exc:
            self._status = f"Track fetch failed: {exc}"
            return None

        candidates = sorted(glob.glob(os.path.join(self.CACHE_DIR, "hawak-mo-ang-beat.*")))
        for c in candidates:
            if c.lower().endswith((".mp3", ".ogg", ".wav", ".m4a", ".webm")):
                return c
        self._status = "Fetched track file missing"
        return None

    def _start_track(self, index: int, fade_ms: int = 500) -> None:
        if not pygame.mixer.get_init():
            self._status = "Audio device unavailable"
            return
        if not self._tracks:
            self._status = "No tracks in queue"
            return

        track = self._tracks[index]
        if not os.path.exists(track.path):
            self._status = "Track file not found"
            return

        try:
            pygame.mixer.music.fadeout(220)
            pygame.mixer.music.load(track.path)
            self._apply_volume()
            pygame.mixer.music.play(loops=-1, fade_ms=fade_ms)
            self._paused = False
            self._status = f"Now playing: {track.title}"
        except pygame.error as exc:
            self._status = f"Playback failed: {exc}"

    def _apply_volume(self) -> None:
        if not pygame.mixer.get_init():
            return
        master = float(getattr(self._settings, "master_volume", 1.0))
        music = float(getattr(self._settings, "music_volume", 1.0))
        radio = float(getattr(self._settings, "radio_volume", 0.7))
        pygame.mixer.music.set_volume(max(0.0, min(1.0, master * music * radio)))

    def shutdown(self) -> None:
        self._settings.save()

