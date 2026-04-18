from __future__ import annotations

import pygame

from core.radio_player import RadioPlayer


class RadioOverlay:
    """Bottom-center radio overlay with playback controls only."""

    def __init__(self, settings, player: RadioPlayer, window_size: dict[str, int]) -> None:
        self._settings = settings
        self._player = player

        self._font_title = pygame.font.Font(None, 24)
        self._font_small = pygame.font.Font(None, 20)

        self._focus_index = 0
        self._controls = ["power", "prev", "play", "next", "vol-", "vol+"]

        self._status = ""
        self._status_timer = 0.0

        self._control_rects: list[pygame.Rect] = []

    def update(self, dt: float) -> None:
        if self._status_timer > 0.0:
            self._status_timer = max(0.0, self._status_timer - dt)
            if self._status_timer == 0.0:
                self._status = ""

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                step = -1 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1
                self._focus_index = (self._focus_index + step) % len(self._controls)
                return True

            if event.key in (pygame.K_LEFT, pygame.K_a):
                self._focus_index = (self._focus_index - 1) % len(self._controls)
                return True
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                self._focus_index = (self._focus_index + 1) % len(self._controls)
                return True
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate_focused()
                return True

        if event.type == pygame.JOYHATMOTION:
            hat_x, _ = event.value
            if hat_x < 0:
                self._focus_index = (self._focus_index - 1) % len(self._controls)
                return True
            if hat_x > 0:
                self._focus_index = (self._focus_index + 1) % len(self._controls)
                return True

        if event.type == pygame.JOYBUTTONDOWN and event.button == 0:
            self._activate_focused()
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for idx, rect in enumerate(self._control_rects):
                if rect.collidepoint(pos):
                    self._focus_index = idx
                    self._activate_focused()
                    return True

        return False

    def _activate_focused(self) -> None:
        action = self._controls[self._focus_index]
        if action == "power":
            self._player.toggle_power()
        elif action == "prev":
            self._player.previous_track()
        elif action == "play":
            self._player.toggle_pause()
        elif action == "next":
            self._player.next_track()
        elif action == "vol-":
            self._player.adjust_volume(-0.05)
        elif action == "vol+":
            self._player.adjust_volume(0.05)
        self._flash_status(self._player.status)

    def _flash_status(self, text: str, duration: float = 2.4) -> None:
        self._status = text
        self._status_timer = duration

    def draw(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_size()
        panel_w = min(760, sw - 60)
        panel_h = 104
        panel_x = sw // 2 - panel_w // 2
        panel_y = sh - panel_h - 14

        panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(screen, (10, 16, 28, 228), panel, border_radius=14)
        pygame.draw.rect(screen, (76, 184, 240), panel, 2, border_radius=14)

        track = self._player.current_track
        title = track.title if track else "No track"
        artist = track.artist if track else ""
        title_text = self._font_title.render(title[:64], True, (240, 247, 255))
        artist_text = self._font_small.render(artist[:64], True, (174, 194, 220))
        screen.blit(title_text, (panel_x + 14, panel_y + 10))
        screen.blit(artist_text, (panel_x + 14, panel_y + 32))

        controls = ["On/Off", "<<", "Play/Pause", ">>", "Vol-", "Vol+"]
        self._control_rects = []
        cx = panel_x + 14
        cy = panel_y + 58
        for i, label in enumerate(controls):
            if i in (1, 3):
                w = 70
            elif i == 2:
                w = 130
            else:
                w = 100
            rect = pygame.Rect(cx, cy, w, 30)
            self._control_rects.append(rect)
            focused = i == self._focus_index
            fill = (31, 52, 76) if not focused else (52, 90, 128)
            border = (86, 132, 182) if not focused else (255, 212, 116)
            pygame.draw.rect(screen, fill, rect, border_radius=8)
            pygame.draw.rect(screen, border, rect, 2, border_radius=8)
            txt = self._font_small.render(label, True, (244, 248, 255))
            screen.blit(txt, txt.get_rect(center=rect.center))
            cx += w + 8

        vol_pct = int(self._player.volume * 100)
        state_text = "ON" if self._player.is_on else "OFF"
        status_line = f"Radio {state_text} | Volume {vol_pct}%"
        if self._status:
            status_line = self._status
        status_txt = self._font_small.render(status_line[:90], True, (255, 226, 132))
        screen.blit(status_txt, (panel_x + panel_w - status_txt.get_width() - 12, panel_y + 34))
