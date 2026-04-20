"""Modern tabbed settings menu with live application support."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import pygame
import core.sound_manager as sound_manager_module

from ui.core.types import Event, MousePos, Surface


def _play_ui_click_sfx() -> None:
    manager = sound_manager_module.sound_manager
    if manager is not None:
        manager.play_ui_click()


@dataclass
class OptionDef:
    key: str
    label: str
    kind: str
    description: str
    min_val: float = 0.0
    max_val: float = 1.0
    step: float = 0.05
    choices: tuple[str, ...] = ()


class SettingsMenu:
    """Tabbed settings menu with keyboard/controller/mouse support."""

    def __init__(self) -> None:
        self.categories = ["Audio", "Graphics", "Gameplay"]
        self.selected_category = 0
        self.selected_option = 0

        self.font_title = pygame.font.Font(None, 56)
        self.font_tab = pygame.font.Font(None, 34)
        self.font_label = pygame.font.Font(None, 30)
        self.font_value = pygame.font.Font(None, 28)
        self.font_desc = pygame.font.Font(None, 22)
        self.font_hint = pygame.font.Font(None, 24)

        self._definitions: Dict[str, list[OptionDef]] = {
            "Audio": [
                OptionDef("master_volume", "Master Volume", "slider", "Global audio level for all sounds.", 0.0, 1.0, 0.01),
                OptionDef("music_volume", "Music Volume", "slider", "Background music loudness.", 0.0, 1.0, 0.01),
                OptionDef("sfx_volume", "SFX Volume", "slider", "Sound effects loudness.", 0.0, 1.0, 0.01),
            ],
            "Graphics": [
                OptionDef("fullscreen", "Fullscreen", "toggle", "Toggle fullscreen display mode."),
                OptionDef("vsync", "VSync", "toggle", "Reduce tearing by syncing frames to monitor."),
                OptionDef(
                    "resolution",
                    "Resolution",
                    "select",
                    "Display resolution. Applies instantly with confirmation.",
                    choices=("1280x720", "1366x768", "1600x900", "1920x1080"),
                ),
                OptionDef(
                    "graphics_preset",
                    "Quality Preset",
                    "select",
                    "Preset quality profile for performance and visuals.",
                    choices=("Low", "Medium", "High", "Ultra"),
                ),
            ],
            "Gameplay": [
                OptionDef(
                    "difficulty",
                    "Difficulty",
                    "select",
                    "Adjust race intensity and handling challenge.",
                    choices=("Easy", "Normal", "Hard"),
                ),
                OptionDef("auto_brake_assist", "Auto-Brake Assist", "toggle", "Automatically brakes during risky turns."),
                OptionDef("steering_assist", "Steering Assist", "toggle", "Stabilizes steering to reduce drift."),
                OptionDef(
                    "camera_mode",
                    "Camera Mode",
                    "select",
                    "Camera preview style in race HUD.",
                    choices=("Close", "Chase", "Far", "Off"),
                ),
            ],
        }

        self._values: dict[str, Any] = {}
        self._hovered_option: Optional[int] = None
        self._hovered_tab: Optional[int] = None
        self._dragging_key: Optional[str] = None
        self._dirty = False

        self._bound_settings: Any = None

        self._confirm_resolution = False
        self._confirm_started_ms = 0
        self._confirm_timeout_ms = 12000
        self._previous_resolution: tuple[int, int] | None = None

        self._tab_rects: list[pygame.Rect] = []
        self._option_rects: list[pygame.Rect] = []
        self._close_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self._reset_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self._dialog_keep_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self._dialog_revert_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)

    def bind_settings(self, game_settings: Any) -> None:
        """Bind runtime settings object so UI can initialize and apply changes instantly."""
        self._bound_settings = game_settings
        if not self._values:
            self._sync_from_settings(game_settings)

    def _sync_from_settings(self, game_settings: Any) -> None:
        if self._values:
            return

        self._values = {
            "master_volume": float(getattr(game_settings, "master_volume", 0.8)),
            "music_volume": float(getattr(game_settings, "music_volume", 0.7)),
            "sfx_volume": float(getattr(game_settings, "sfx_volume", 1.0)),
            "fullscreen": bool(getattr(game_settings, "fullscreen", False)),
            "vsync": bool(getattr(game_settings, "vsync", False)),
            "resolution": f"{int(game_settings.resolution[0])}x{int(game_settings.resolution[1])}",
            "graphics_preset": str(getattr(game_settings, "graphics_preset", "High")),
            "difficulty": str(getattr(game_settings, "difficulty", "Normal")),
            "auto_brake_assist": bool(getattr(game_settings, "auto_brake_assist", False)),
            "steering_assist": bool(getattr(game_settings, "steering_assist", True)),
            "camera_mode": str(getattr(game_settings, "camera_mode", "Chase")),
        }

    def _ensure_values(self) -> None:
        if self._values:
            return
        if self._bound_settings is not None:
            self._sync_from_settings(self._bound_settings)
            return
        self._values = {
            "master_volume": 0.80,
            "music_volume": 0.70,
            "sfx_volume": 1.00,
            "fullscreen": False,
            "vsync": False,
            "resolution": "1920x1080",
            "graphics_preset": "High",
            "difficulty": "Normal",
            "auto_brake_assist": False,
            "steering_assist": True,
            "camera_mode": "Chase",
        }

    def handle_input(self, event: Event, mouse_pos: Optional[MousePos] = None) -> Optional[Dict[str, str]]:
        self._ensure_values()

        if event.type == pygame.KEYDOWN:
            if self._confirm_resolution:
                return self._handle_confirm_key(event.key)

            if event.key == pygame.K_ESCAPE:
                return {"action": "close"}
            if event.key in (pygame.K_TAB, pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                step = -1 if event.key == pygame.K_PAGEUP else 1
                self.selected_category = (self.selected_category + step) % len(self.categories)
                self.selected_option = 0
                return {"action": "navigate"}
            if event.key == pygame.K_UP:
                self.selected_option = max(0, self.selected_option - 1)
                return {"action": "navigate"}
            if event.key == pygame.K_DOWN:
                self.selected_option = min(len(self._active_options()), self.selected_option + 1)
                return {"action": "navigate"}
            if event.key == pygame.K_LEFT and self.selected_option < len(self._active_options()):
                self._nudge_option(self._active_options()[self.selected_option], -1)
                return {"action": "changed"}
            if event.key == pygame.K_RIGHT and self.selected_option < len(self._active_options()):
                self._nudge_option(self._active_options()[self.selected_option], 1)
                return {"action": "changed"}
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.selected_option == len(self._active_options()):
                    self._reset_current_section()
                    return {"action": "changed"}
                self._nudge_option(self._active_options()[self.selected_option], 1)
                return {"action": "changed"}

        if event.type == pygame.JOYHATMOTION:
            if self._confirm_resolution:
                hat_x, _hat_y = event.value
                if hat_x < 0:
                    return self._handle_confirm_key(pygame.K_LEFT)
                if hat_x > 0:
                    return self._handle_confirm_key(pygame.K_RIGHT)
                return None

            hat_x, hat_y = event.value
            if hat_y > 0:
                self.selected_option = max(0, self.selected_option - 1)
                return {"action": "navigate"}
            if hat_y < 0:
                self.selected_option = min(len(self._active_options()), self.selected_option + 1)
                return {"action": "navigate"}
            if hat_x < 0 and self.selected_option < len(self._active_options()):
                self._nudge_option(self._active_options()[self.selected_option], -1)
                return {"action": "changed"}
            if hat_x > 0 and self.selected_option < len(self._active_options()):
                self._nudge_option(self._active_options()[self.selected_option], 1)
                return {"action": "changed"}

        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == 1:
                return {"action": "close"}
            if event.button == 0:
                if self.selected_option == len(self._active_options()):
                    self._reset_current_section()
                else:
                    self._nudge_option(self._active_options()[self.selected_option], 1)
                return {"action": "changed"}

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and mouse_pos:
            if self._confirm_resolution:
                if self._dialog_keep_rect.collidepoint(mouse_pos):
                    _play_ui_click_sfx()
                    self._keep_resolution()
                    return {"action": "changed"}
                if self._dialog_revert_rect.collidepoint(mouse_pos):
                    _play_ui_click_sfx()
                    self._revert_resolution()
                    return {"action": "changed"}
                return None

            if self._close_rect.collidepoint(mouse_pos):
                _play_ui_click_sfx()
                return {"action": "close"}

            for idx, rect in enumerate(self._tab_rects):
                if rect.collidepoint(mouse_pos):
                    _play_ui_click_sfx()
                    self.selected_category = idx
                    self.selected_option = 0
                    return {"action": "navigate"}

            if self._reset_rect.collidepoint(mouse_pos):
                _play_ui_click_sfx()
                self._reset_current_section()
                return {"action": "changed"}

            for idx, rect in enumerate(self._option_rects):
                if rect.collidepoint(mouse_pos):
                    _play_ui_click_sfx()
                    self.selected_option = idx
                    option = self._active_options()[idx]
                    if option.kind == "slider":
                        self._dragging_key = option.key
                        self._set_slider_value_from_mouse(option, mouse_pos)
                    else:
                        self._nudge_option(option, 1)
                    return {"action": "changed"}

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging_key = None

        if event.type == pygame.MOUSEMOTION and self._dragging_key and mouse_pos:
            option = next((o for o in self._active_options() if o.key == self._dragging_key), None)
            if option is not None:
                self._set_slider_value_from_mouse(option, mouse_pos)
                return {"action": "changed"}

        return None

    def _handle_confirm_key(self, key: int) -> Optional[Dict[str, str]]:
        if key in (pygame.K_ESCAPE, pygame.K_RIGHT, pygame.K_d):
            self._revert_resolution()
            return {"action": "changed"}
        if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_LEFT, pygame.K_a):
            self._keep_resolution()
            return {"action": "changed"}
        return None

    def update(self, mouse_pos: MousePos) -> None:
        self._hovered_option = None
        self._hovered_tab = None

        for idx, rect in enumerate(self._tab_rects):
            if rect.collidepoint(mouse_pos):
                self._hovered_tab = idx
                break

        for idx, rect in enumerate(self._option_rects):
            if rect.collidepoint(mouse_pos):
                self._hovered_option = idx
                break

        if self._confirm_resolution and pygame.time.get_ticks() - self._confirm_started_ms > self._confirm_timeout_ms:
            self._revert_resolution()
            self._dirty = True

    def consume_dirty(self) -> bool:
        was_dirty = self._dirty
        self._dirty = False
        return was_dirty

    def _active_options(self) -> list[OptionDef]:
        return self._definitions[self.categories[self.selected_category]]

    def _nudge_option(self, option: OptionDef, direction: int) -> None:
        key = option.key
        if option.kind == "toggle":
            self._values[key] = not bool(self._values.get(key, False))
        elif option.kind == "select":
            choices = option.choices
            if choices:
                current = str(self._values.get(key, choices[0]))
                idx = choices.index(current) if current in choices else 0
                self._values[key] = choices[(idx + direction) % len(choices)]
        elif option.kind == "slider":
            current = float(self._values.get(key, option.min_val))
            next_val = current + direction * option.step
            self._values[key] = max(option.min_val, min(option.max_val, next_val))

        self._dirty = True

    def _set_slider_value_from_mouse(self, option: OptionDef, mouse_pos: MousePos) -> None:
        for idx, rect in enumerate(self._option_rects):
            if self._active_options()[idx].key != option.key:
                continue
            slider_rect = pygame.Rect(rect.x + 300, rect.y + 28, rect.width - 340, 12)
            rel = max(0.0, min(float(mouse_pos[0] - slider_rect.x), float(slider_rect.width)))
            pct = 0.0 if slider_rect.width <= 0 else rel / float(slider_rect.width)
            self._values[option.key] = option.min_val + (option.max_val - option.min_val) * pct
            self._dirty = True
            return

    def _reset_current_section(self) -> None:
        section = self.categories[self.selected_category]
        defaults = {
            "Audio": {"master_volume": 0.80, "music_volume": 0.70, "sfx_volume": 1.00},
            "Graphics": {"fullscreen": False, "vsync": False, "resolution": "1920x1080", "graphics_preset": "High"},
            "Gameplay": {"difficulty": "Normal", "auto_brake_assist": False, "steering_assist": True, "camera_mode": "Chase"},
        }
        for key, value in defaults.get(section, {}).items():
            self._values[key] = value
        self._dirty = True

    def apply_to_game(self, game_settings: Any) -> None:
        self._bound_settings = game_settings
        self._ensure_values()

        game_settings.master_volume = float(self._values["master_volume"])
        game_settings.music_volume = float(self._values["music_volume"])
        game_settings.sfx_volume = float(self._values["sfx_volume"])
        game_settings.apply_audio_settings()

        previous_fullscreen = bool(game_settings.fullscreen)
        previous_vsync = bool(game_settings.vsync)

        desired_fullscreen = bool(self._values["fullscreen"])
        desired_vsync = bool(self._values["vsync"])
        game_settings.fullscreen = desired_fullscreen
        game_settings.vsync = desired_vsync
        game_settings.graphics_preset = str(self._values["graphics_preset"])

        game_settings.difficulty = str(self._values["difficulty"])
        game_settings.auto_brake_assist = bool(self._values["auto_brake_assist"])
        game_settings.steering_assist = bool(self._values["steering_assist"])
        game_settings.camera_mode = str(self._values["camera_mode"])

        preset = game_settings.graphics_preset
        if preset == "Low":
            game_settings.max_fps = 30
            game_settings.show_camera = False
        elif preset == "Medium":
            game_settings.max_fps = 60
            game_settings.show_camera = True
        elif preset == "High":
            game_settings.max_fps = 120
            game_settings.show_camera = True
        elif preset == "Ultra":
            game_settings.max_fps = 120
            game_settings.show_camera = True

        width_s, height_s = str(self._values["resolution"]).split("x")
        selected_resolution = (int(width_s), int(height_s))
        current_resolution = (int(game_settings.resolution[0]), int(game_settings.resolution[1]))

        display_changed = (
            selected_resolution != current_resolution
            or desired_fullscreen != previous_fullscreen
            or desired_vsync != previous_vsync
        )

        if selected_resolution != current_resolution and not self._confirm_resolution:
            self._previous_resolution = current_resolution
            game_settings.apply_display_settings(
                resolution=selected_resolution,
                fullscreen=desired_fullscreen,
                vsync=desired_vsync,
            )
            self._confirm_resolution = True
            self._confirm_started_ms = pygame.time.get_ticks()
        elif display_changed and not self._confirm_resolution:
            game_settings.apply_display_settings(fullscreen=desired_fullscreen, vsync=desired_vsync)

        game_settings.save()

    def _keep_resolution(self) -> None:
        self._confirm_resolution = False
        self._previous_resolution = None
        if self._bound_settings is not None:
            self._bound_settings.save()

    def _revert_resolution(self) -> None:
        if self._bound_settings is not None and self._previous_resolution is not None:
            self._bound_settings.apply_display_settings(
                resolution=self._previous_resolution,
                fullscreen=self._bound_settings.fullscreen,
                vsync=self._bound_settings.vsync,
            )
            self._values["resolution"] = f"{self._previous_resolution[0]}x{self._previous_resolution[1]}"
            self._bound_settings.resolution = [self._previous_resolution[0], self._previous_resolution[1]]
            self._bound_settings.save()

        self._confirm_resolution = False
        self._previous_resolution = None

    def draw(self, screen: Surface) -> None:
        self._ensure_values()

        sw, sh = screen.get_width(), screen.get_height()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        panel_w, panel_h = 1060, 700
        panel_x, panel_y = sw // 2 - panel_w // 2, sh // 2 - panel_h // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        pygame.draw.rect(screen, (17, 24, 38), panel_rect, border_radius=18)
        pygame.draw.rect(screen, (95, 202, 255), panel_rect, 2, border_radius=18)

        title = self.font_title.render("SETTINGS", True, (236, 243, 255))
        screen.blit(title, (panel_x + 32, panel_y + 24))

        self._close_rect = pygame.Rect(panel_x + panel_w - 64, panel_y + 22, 38, 38)
        pygame.draw.rect(screen, (120, 48, 48), self._close_rect, border_radius=8)
        x_txt = self.font_tab.render("X", True, (255, 255, 255))
        screen.blit(x_txt, x_txt.get_rect(center=self._close_rect.center))

        self._tab_rects.clear()
        tab_y = panel_y + 86
        tab_w = 210
        for idx, category in enumerate(self.categories):
            tab_rect = pygame.Rect(panel_x + 28 + idx * (tab_w + 12), tab_y, tab_w, 44)
            self._tab_rects.append(tab_rect)
            active = idx == self.selected_category
            hovered = idx == self._hovered_tab
            fill = (38, 56, 84) if active else ((31, 44, 65) if hovered else (24, 34, 52))
            border = (95, 202, 255) if active else (66, 92, 128)
            pygame.draw.rect(screen, fill, tab_rect, border_radius=10)
            pygame.draw.rect(screen, border, tab_rect, 2, border_radius=10)
            tab_text = self.font_tab.render(category, True, (236, 243, 255))
            screen.blit(tab_text, tab_text.get_rect(center=tab_rect.center))

        content_rect = pygame.Rect(panel_x + 28, panel_y + 146, panel_w - 56, panel_h - 208)
        pygame.draw.rect(screen, (22, 32, 50), content_rect, border_radius=12)
        pygame.draw.rect(screen, (58, 82, 114), content_rect, 1, border_radius=12)

        self._option_rects.clear()
        options = self._active_options()
        row_h = 96
        row_x = content_rect.x + 16
        row_w = content_rect.width - 32

        for idx, option in enumerate(options):
            row_y = content_rect.y + 12 + idx * row_h
            row_rect = pygame.Rect(row_x, row_y, row_w, row_h - 8)
            self._option_rects.append(row_rect)

            selected = idx == self.selected_option
            hovered = idx == self._hovered_option
            fill = (30, 43, 66) if selected else ((27, 39, 58) if hovered else (24, 35, 54))
            border = (255, 203, 101) if selected else (55, 78, 109)

            pygame.draw.rect(screen, fill, row_rect, border_radius=10)
            pygame.draw.rect(screen, border, row_rect, 1, border_radius=10)

            label = self.font_label.render(option.label, True, (234, 242, 255))
            desc = self.font_desc.render(option.description, True, (159, 177, 206))
            screen.blit(label, (row_rect.x + 14, row_rect.y + 10))
            screen.blit(desc, (row_rect.x + 14, row_rect.y + 40))

            self._draw_value_control(screen, row_rect, option)

        reset_y = content_rect.bottom + 12
        self._reset_rect = pygame.Rect(panel_x + 28, reset_y, 190, 42)
        pygame.draw.rect(screen, (76, 56, 32), self._reset_rect, border_radius=10)
        pygame.draw.rect(screen, (228, 186, 108), self._reset_rect, 2, border_radius=10)
        reset_text = self.font_hint.render("Reset Section", True, (255, 244, 221))
        screen.blit(reset_text, reset_text.get_rect(center=self._reset_rect.center))

        hint = self.font_hint.render("Tab/PageUp/PageDown: switch tabs | Arrows: navigate/adjust | Enter: toggle", True, (155, 174, 204))
        screen.blit(hint, (panel_x + 240, reset_y + 11))

        if self._confirm_resolution:
            self._draw_resolution_dialog(screen)

    def _draw_value_control(self, screen: Surface, row_rect: pygame.Rect, option: OptionDef) -> None:
        key = option.key
        value = self._values.get(key)

        if option.kind == "slider":
            slider_rect = pygame.Rect(row_rect.x + 300, row_rect.y + 30, row_rect.width - 340, 12)
            pygame.draw.rect(screen, (58, 74, 102), slider_rect, border_radius=6)

            pct = 0.0
            if option.max_val > option.min_val:
                pct = (float(value) - option.min_val) / (option.max_val - option.min_val)
            pct = max(0.0, min(1.0, pct))

            fill_width = int(slider_rect.width * pct)
            if fill_width > 0:
                pygame.draw.rect(screen, (95, 202, 255), (slider_rect.x, slider_rect.y, fill_width, slider_rect.height), border_radius=6)

            thumb_x = slider_rect.x + fill_width
            pygame.draw.circle(screen, (255, 214, 122), (thumb_x, slider_rect.centery), 8)

            pct_text = self.font_value.render(f"{int(float(value) * 100)}%", True, (234, 242, 255))
            screen.blit(pct_text, (row_rect.right - 72, row_rect.y + 8))
            return

        if option.kind == "toggle":
            toggle_rect = pygame.Rect(row_rect.right - 130, row_rect.y + 20, 96, 38)
            on = bool(value)
            fill = (48, 134, 88) if on else (88, 76, 76)
            pygame.draw.rect(screen, fill, toggle_rect, border_radius=18)
            pygame.draw.rect(screen, (220, 230, 245), toggle_rect, 1, border_radius=18)

            knob_x = toggle_rect.right - 18 if on else toggle_rect.x + 18
            pygame.draw.circle(screen, (245, 248, 255), (knob_x, toggle_rect.centery), 14)

            val_text = self.font_value.render("ON" if on else "OFF", True, (234, 242, 255))
            screen.blit(val_text, (toggle_rect.x - 58, toggle_rect.y + 6))
            return

        if option.kind == "select":
            value_rect = pygame.Rect(row_rect.right - 220, row_rect.y + 22, 190, 34)
            pygame.draw.rect(screen, (44, 58, 82), value_rect, border_radius=8)
            pygame.draw.rect(screen, (104, 132, 168), value_rect, 1, border_radius=8)

            val_text = self.font_value.render(str(value), True, (236, 243, 255))
            screen.blit(val_text, val_text.get_rect(center=value_rect.center))

            left = self.font_value.render("<", True, (255, 210, 118))
            right = self.font_value.render(">", True, (255, 210, 118))
            screen.blit(left, (value_rect.x - 24, value_rect.y + 4))
            screen.blit(right, (value_rect.right + 8, value_rect.y + 4))

    def _draw_resolution_dialog(self, screen: Surface) -> None:
        sw, sh = screen.get_width(), screen.get_height()
        dialog = pygame.Rect(sw // 2 - 250, sh // 2 - 120, 500, 240)

        pygame.draw.rect(screen, (16, 23, 36), dialog, border_radius=12)
        pygame.draw.rect(screen, (94, 202, 255), dialog, 2, border_radius=12)

        elapsed = pygame.time.get_ticks() - self._confirm_started_ms
        remaining = max(0, (self._confirm_timeout_ms - elapsed) // 1000)

        title = self.font_tab.render("Keep This Resolution?", True, (236, 243, 255))
        line1 = self.font_hint.render("New resolution applied instantly.", True, (166, 185, 212))
        line2 = self.font_hint.render(f"Auto-revert in {remaining}s", True, (255, 210, 118))

        screen.blit(title, title.get_rect(center=(dialog.centerx, dialog.y + 44)))
        screen.blit(line1, line1.get_rect(center=(dialog.centerx, dialog.y + 88)))
        screen.blit(line2, line2.get_rect(center=(dialog.centerx, dialog.y + 116)))

        self._dialog_keep_rect = pygame.Rect(dialog.centerx - 170, dialog.bottom - 72, 140, 44)
        self._dialog_revert_rect = pygame.Rect(dialog.centerx + 30, dialog.bottom - 72, 140, 44)

        pygame.draw.rect(screen, (44, 128, 90), self._dialog_keep_rect, border_radius=10)
        pygame.draw.rect(screen, (180, 102, 102), self._dialog_revert_rect, border_radius=10)

        keep = self.font_hint.render("Keep", True, (242, 248, 255))
        revert = self.font_hint.render("Revert", True, (242, 248, 255))
        screen.blit(keep, keep.get_rect(center=self._dialog_keep_rect.center))
        screen.blit(revert, revert.get_rect(center=self._dialog_revert_rect.center))




