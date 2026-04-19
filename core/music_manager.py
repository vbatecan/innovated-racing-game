from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pygame


@dataclass(frozen=True)
class MusicTrack:
    path: Path
    title: str


class MusicManager:
    """Playlist-based music playback manager.

    Controls:
    - F: previous track
    - G: play/pause
    - H: next track
    """

    SUPPORTED_EXTENSIONS = (".mp3", ".ogg", ".wav")

    def __init__(self, settings, music_dir: str | Path = "resources/music") -> None:
        self._settings = settings
        self._music_dir = Path(music_dir)
        self._tracks: list[MusicTrack] = []
        self._current_index = 0
        self._paused = False
        self._status = "Music ready"
        self._cached_volume: float | None = None

        self._load_tracks()
        self._restore_last_track()
        self._ensure_mixer()
        self.apply_volume(force=True)

    @property
    def status(self) -> str:
        return self._status

    @property
    def current_track(self) -> MusicTrack | None:
        if not self._tracks:
            return None
        return self._tracks[self._current_index]

    def start(self) -> None:
        if not self._tracks:
            self._status = "No tracks found in resources/music"
            return
        self._play_current(fade_ms=250)

    def update(self) -> None:
        self.apply_volume()
        if self._paused or not self._tracks:
            return
        if not pygame.mixer.get_init():
            return
        if not pygame.mixer.music.get_busy():
            self._current_index = (self._current_index + 1) % len(self._tracks)
            self._play_current(fade_ms=150)

    def handle_keydown(self, event_key: int) -> bool:
        if event_key == pygame.K_f:
            self.previous_track()
            return True
        if event_key == pygame.K_g:
            self.toggle_pause()
            return True
        if event_key == pygame.K_h:
            self.next_track()
            return True
        return False

    def previous_track(self) -> None:
        if not self._tracks:
            self._status = "No tracks in playlist"
            return
        self._current_index = (self._current_index - 1) % len(self._tracks)
        self._play_current(fade_ms=220)

    def next_track(self) -> None:
        if not self._tracks:
            self._status = "No tracks in playlist"
            return
        self._current_index = (self._current_index + 1) % len(self._tracks)
        self._play_current(fade_ms=220)

    def toggle_pause(self) -> None:
        if not self._tracks:
            self._status = "No tracks in playlist"
            return

        self._ensure_mixer()
        if not pygame.mixer.get_init():
            self._status = "Audio device unavailable"
            return

        if self._paused:
            pygame.mixer.music.unpause()
            self._paused = False
            track = self.current_track
            if track is not None:
                self._status = f"Resumed: {track.title}"
            else:
                self._status = "Playback resumed"
            return

        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self._paused = True
            self._status = "Playback paused"
            return

        self._play_current(fade_ms=120)

    def stop(self) -> None:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()

    def apply_volume(self, force: bool = False) -> None:
        if not pygame.mixer.get_init():
            return

        master = max(0.0, min(1.0, float(getattr(self._settings, "master_volume", 1.0))))
        music = max(0.0, min(1.0, float(getattr(self._settings, "music_volume", 0.7))))
        volume = max(0.0, min(1.0, master * music))

        if force or self._cached_volume is None or abs(volume - self._cached_volume) > 0.001:
            pygame.mixer.music.set_volume(volume)
            self._cached_volume = volume

    def _load_tracks(self) -> None:
        if not self._music_dir.exists():
            return

        for path in sorted(self._music_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue

            title = path.stem.replace("_", " ").strip()
            self._tracks.append(MusicTrack(path=path, title=title))

    def _restore_last_track(self) -> None:
        if not self._tracks:
            return

        last_track = str(getattr(self._settings, "last_music_track", "")).strip().lower()
        if not last_track:
            return

        for index, track in enumerate(self._tracks):
            if track.path.name.lower() == last_track:
                self._current_index = index
                return

    def _play_current(self, fade_ms: int = 200) -> None:
        self._ensure_mixer()
        if not pygame.mixer.get_init():
            self._status = "Audio device unavailable"
            return
        if not self._tracks:
            self._status = "No tracks in playlist"
            return

        track = self._tracks[self._current_index]
        if not track.path.exists():
            self._status = "Track file not found"
            return

        try:
            pygame.mixer.music.fadeout(120)
            pygame.mixer.music.load(str(track.path))
            self.apply_volume(force=True)
            pygame.mixer.music.play(loops=0, fade_ms=fade_ms)
            self._paused = False
            self._status = f"Now playing: {track.title}"
            self._settings.last_music_track = track.path.name
            self._settings.save()
        except pygame.error as exc:
            self._status = f"Playback failed: {exc}"

    def _ensure_mixer(self) -> None:
        if pygame.mixer.get_init():
            return
        try:
            pygame.mixer.init()
        except pygame.error:
            self._status = "Audio device unavailable"
