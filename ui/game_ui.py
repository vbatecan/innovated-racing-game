"""
Modern UI/HUD system for the racing game.
Includes HUD display, pause menu, settings, and interactive elements.
"""

from __future__ import annotations

import os
from typing import Optional, Callable

import cv2
import numpy as np
import pygame
import pygame.gfxdraw


def draw_rounded_rect(surface, color, rect, width=0):
    if width == 0:
        pygame.gfxdraw.box(surface, rect, color)
    else:
        pygame.gfxdraw.rectangle(
            surface,
            (
                rect[0] + width // 2,
                rect[1] + width // 2,
                rect[2] - width,
                rect[3] - width,
            ),
            color,
        )


class Button:
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        callback: Callable | None = None,
        font: pygame.font.Font | None = None,
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.font = font or pygame.font.Font(None, 28)

        self.bg_color = (30, 40, 60)
        self.hover_color = (0, 180, 255)
        self.text_color = (235, 235, 245)
        self.border_color = (60, 80, 120)
        self.is_hovered = False
        self.is_active = False

    def update(self, mouse_pos: tuple, mouse_pressed: tuple) -> None:
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        if self.is_hovered and mouse_pressed[0] and self.callback:
            self.callback()

    def draw(self, surface: pygame.Surface) -> None:
        color = self.hover_color if self.is_hovered else self.bg_color

        draw_rounded_rect(surface, color, self.rect)
        draw_rounded_rect(surface, self.border_color, self.rect, 2)

        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class Slider:
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        min_val: float,
        max_val: float,
        value: float,
        label: str = "",
        font: pygame.font.Font | None = None,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.label = label
        self.font = font or pygame.font.Font(None, 24)

        self.track_rect = pygame.Rect(x, y + height // 2 - 3, width, 6)
        self.thumb_radius = 10
        self.is_dragging = False

        self.accent_color = (0, 180, 255)
        self.track_color = (40, 50, 70)
        self.text_color = (200, 200, 220)

    def update(self, mouse_pos: tuple, mouse_pressed: tuple) -> None:
        if self.track_rect.collidepoint(mouse_pos) and mouse_pressed[0]:
            self.is_dragging = True

        if not mouse_pressed[0]:
            self.is_dragging = False

        if self.is_dragging:
            rel_x = max(0, min(mouse_pos[0] - self.x, self.width))
            pct = rel_x / self.width
            self.value = self.min_val + pct * (self.max_val - self.min_val)

    def draw(self, surface: pygame.Surface) -> None:
        draw_rounded_rect(surface, self.track_color, self.track_rect)

        pct = (self.value - self.min_val) / (self.max_val - self.min_val)
        fill_width = int(self.width * pct)
        fill_rect = pygame.Rect(self.x, self.y + self.height // 2 - 3, fill_width, 6)
        draw_rounded_rect(surface, self.accent_color, fill_rect)

        thumb_x = self.x + fill_width
        thumb_y = self.y + self.height // 2
        pygame.draw.circle(
            surface, self.accent_color, (thumb_x, thumb_y), self.thumb_radius
        )

        if self.label:
            label_surf = self.font.render(self.label, True, self.text_color)
            surface.blit(label_surf, (self.x, self.y - 20))

        value_surf = self.font.render(f"{self.value:.0f}", True, self.text_color)
        surface.blit(value_surf, (self.x + self.width + 10, self.y))

    def get_value(self) -> float:
        return self.value


class HUDManager:
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.font_large = pygame.font.Font(None, 56)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 22)

        self.accent_color = (0, 200, 255)
        self.text_color = (240, 240, 250)
        self.muted_color = (120, 140, 170)
        self.warn_color = (255, 80, 80)
        self.success_color = (80, 255, 140)
        self.gold_color = (255, 200, 60)

        self._speed_display = 0.0
        self._speed_anim_speed = 0.15

        self._load_life_images()

        self.speed = 0.0
        self.max_speed = 30.0
        self.score = 0
        self.lives = 3
        self.distance = 0.0
        self.gear = 1
        self.is_braking = False
        self.boost_energy = 100.0
        self.hearts_collected = 0

        self.camera_frame = None
        self.show_camera = True
        self.camera_size = (180, 135)
        self.camera_pos = ("right", "bottom")

    def _load_life_images(self) -> None:
        self.life_images = {}
        base_path = os.path.join("resources", "models")
        image_files = {
            3: "full hp.png",
            2: "hp minus 1.png",
            1: "hp minus 2.png",
            0: "deds.png",
        }
        for lives, filename in image_files.items():
            filepath = os.path.join(base_path, filename)
            if os.path.exists(filepath):
                try:
                    img = pygame.image.load(filepath).convert_alpha()
                    self.life_images[lives] = img
                except:
                    self.life_images[lives] = None
            else:
                self.life_images[lives] = None

    def update(
        self,
        speed: float,
        max_speed: float,
        score: int,
        lives: int,
        distance: float,
        gear: int,
        is_braking: bool,
        boost_energy: float = 100.0,
        hearts_collected: int = 0,
        dt: float = 0.016,
    ) -> None:
        self.speed = speed
        self.max_speed = max_speed
        self.score = score
        self.lives = lives
        self.distance = distance
        self.gear = gear
        self.is_braking = is_braking
        self.boost_energy = boost_energy
        self.hearts_collected = hearts_collected

        self._speed_display += (speed - self._speed_display) * self._speed_anim_speed

    def set_camera_frame(self, frame) -> None:
        self.camera_frame = frame

    def set_camera_visibility(self, visible: bool) -> None:
        self.show_camera = visible

    def draw(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_width(), screen.get_height()

        self._draw_speed_top_center(screen, sw)
        self._draw_score_top_right(screen, sw)
        self._draw_lives_top_left(screen)
        self._draw_stats_bottom_left(screen, sh)
        self._draw_boost_bar_bottom_center(screen, sw, sh)
        if self.show_camera and self.camera_frame is not None:
            self._draw_camera_preview(screen, sw, sh)

    def _draw_glass_panel(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        w: int,
        h: int,
        border: bool = True,
    ) -> None:
        draw_rounded_rect(surface, (15, 20, 35, 200), (x, y, w, h))
        if border:
            draw_rounded_rect(surface, self.accent_color, (x, y, w, h), 1)

    def _draw_speed_top_center(self, screen: pygame.Surface, sw: int) -> None:
        w, h = 180, 80
        x = sw // 2 - w // 2
        y = 20

        self._draw_glass_panel(screen, x, y, w, h)
        draw_rounded_rect(screen, self.accent_color, (x, y, w, 3))

        speed = int(self._speed_display)
        color = self.warn_color if self.is_braking else self.text_color

        speed_text = self.font_large.render(f"{speed}", True, color)
        unit_text = self.font_small.render("km/h", True, self.muted_color)

        screen.blit(speed_text, (x + w // 2 - speed_text.get_width() // 2, y + 10))
        screen.blit(unit_text, (x + w // 2 - unit_text.get_width() // 2, y + 50))

    def _draw_score_top_right(self, screen: pygame.Surface, sw: int) -> None:
        margin = 25
        w, h = 200, 70
        x = sw - w - margin
        y = margin

        self._draw_glass_panel(screen, x, y, w, h)

        score_text = f"{self.score:,}"
        score_surf = self.font_medium.render(score_text, True, self.text_color)
        label_surf = self.font_small.render("SCORE", True, self.muted_color)

        screen.blit(label_surf, (x + 15, y + 10))
        screen.blit(score_surf, (x + 15, y + 30))

    def _draw_lives_top_left(self, screen: pygame.Surface) -> None:
        margin = 25
        x, y = margin, margin

        lives = max(0, min(3, int(self.lives)))
        img = self.life_images.get(lives)

        if img:
            scale = 0.55
            new_w = int(img.get_width() * scale)
            new_h = int(img.get_height() * scale)
            scaled = pygame.transform.smoothscale(img, (new_w, new_h))
            screen.blit(scaled, (x, y))

        if self.hearts_collected > 0:
            heart_text = self.font_small.render(
                f"+{self.hearts_collected}", True, (255, 120, 160)
            )
            screen.blit(heart_text, (x + 90, y + 25))

    def _draw_stats_bottom_left(self, screen: pygame.Surface, sh: int) -> None:
        margin = 25
        w, h = 200, 90
        x, y = margin, sh - h - margin

        self._draw_glass_panel(screen, x, y, w, h)

        items = [
            ("DISTANCE", f"{int(self.distance)}m"),
            ("SPEED", f"{self.speed:.0f}"),
            ("GEAR", f"{self.gear}"),
        ]

        for i, (label, value) in enumerate(items):
            label_surf = self.font_small.render(label, True, self.muted_color)
            value_surf = self.font_medium.render(value, True, self.text_color)

            screen.blit(label_surf, (x + 15, y + 12 + i * 25))
            screen.blit(value_surf, (x + 120, y + 8 + i * 25))

    def _draw_boost_bar_bottom_center(
        self, screen: pygame.Surface, sw: int, sh: int
    ) -> None:
        margin = 25
        bar_w, bar_h = 280, 14
        x = sw // 2 - bar_w // 2
        y = sh - bar_h - margin

        bg = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        bg.fill((15, 20, 35, 180))
        screen.blit(bg, (x, y))
        pygame.draw.rect(
            screen, self.accent_color, (x, y, bar_w, bar_h), 1, border_radius=8
        )

        pct = self.boost_energy / 100.0
        fill_w = int((bar_w - 4) * pct)

        if pct > 0.6:
            fill_color = self.accent_color
        elif pct > 0.3:
            fill_color = self.gold_color
        else:
            fill_color = self.warn_color

        if fill_w > 0:
            fill_rect = pygame.Rect(x + 2, y + 2, fill_w, bar_h - 4)
            draw_rounded_rect(screen, fill_color, fill_rect)

        label = self.font_small.render("BOOST", True, self.muted_color)
        screen.blit(label, (sw // 2 - label.get_width() // 2, y - 18))

    def _draw_camera_preview(self, screen: pygame.Surface, sw: int, sh: int) -> None:
        try:
            w, h = self.camera_size
            margin = 20

            x = sw - w - margin
            y = sh - h - margin - 80

            frame = cv2.cvtColor(self.camera_frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (w, h))
            frame = np.rot90(frame)
            frame = np.flipud(frame)
            frame_surface = pygame.surfarray.make_surface(frame)

            panel = pygame.Surface((w + 8, h + 8), pygame.SRCALPHA)
            panel.fill((0, 0, 0, 180))
            screen.blit(panel, (x - 4, y - 4))

            pygame.draw.rect(screen, self.accent_color, (x - 4, y - 4, w + 8, h + 8), 2)
            screen.blit(frame_surface, (x, y))
        except Exception as e:
            print(f"Camera draw error: {e}")


class PauseMenu:
    def __init__(self):
        self.font_title = pygame.font.Font(None, 64)
        self.font_option = pygame.font.Font(None, 36)
        self.font_hint = pygame.font.Font(None, 22)

        self.accent_color = (0, 200, 255)
        self.text_color = (240, 240, 250)
        self.muted_color = (120, 140, 170)

        self.options = ["Resume", "Restart", "Settings", "Quit"]
        self.buttons: list[Button] = []
        self._clicked_option = None

        self.visible = False
        self.anim_progress = 0.0

    def show(self) -> None:
        self.visible = True
        self.anim_progress = 0.0

    def hide(self) -> None:
        self.visible = False

    def update_layout(self, screen_width: int, screen_height: int) -> None:
        menu_w, menu_h = 340, 380
        menu_x = screen_width // 2 - menu_w // 2
        menu_y = screen_height // 2 - menu_h // 2

        self.buttons = []
        for i, option in enumerate(self.options):
            btn = Button(
                menu_x + 40,
                menu_y + 120 + i * 60,
                menu_w - 80,
                48,
                option,
            )
            self.buttons.append(btn)

    def handle_input(self, event: pygame.event.Event) -> Optional[str]:
        if not self.visible:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "Resume"
            elif event.key == pygame.K_UP:
                self.selected_index = (getattr(self, "selected_index", 0) - 1) % len(
                    self.options
                )
                setattr(
                    self,
                    "selected_index",
                    (getattr(self, "selected_index", 0) - 1) % len(self.options),
                )
            elif event.key == pygame.K_DOWN:
                setattr(
                    self,
                    "selected_index",
                    (getattr(self, "selected_index", 0) + 1) % len(self.options),
                )
            elif event.key == pygame.K_RETURN:
                idx = getattr(self, "selected_index", 0)
                return self.options[idx]

        if event.type == pygame.MOUSEBUTTONDOWN:
            for btn in self.buttons:
                if btn.rect.collidepoint(event.pos):
                    return btn.text

        return None

    def update(self, mouse_pos: tuple, mouse_pressed: tuple) -> None:
        if not self.visible:
            return

        clicked = None
        for btn in self.buttons:
            was_hovered = btn.is_hovered
            btn.update(mouse_pos, mouse_pressed)
            if mouse_pressed[0] and btn.is_hovered and not was_hovered:
                clicked = btn.text

        if clicked:
            self._clicked_option = clicked

    def draw(self, screen: pygame.Surface, dt: float = 0.016) -> None:
        if not self.visible:
            return

        self.anim_progress = min(1.0, self.anim_progress + dt * 5)

        sw, sh = screen.get_width(), screen.get_height()

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(180 * self.anim_progress)))
        screen.blit(overlay, (0, 0))

        menu_w, menu_h = 340, 380
        menu_x = sw // 2 - menu_w // 2
        menu_y = sh // 2 - menu_h // 2

        draw_rounded_rect(screen, (20, 30, 50, 240), (menu_x, menu_y, menu_w, menu_h))
        draw_rounded_rect(screen, self.accent_color, (menu_x, menu_y, menu_w, 4))
        draw_rounded_rect(
            screen, self.accent_color, (menu_x, menu_y, menu_w, menu_h), 1
        )

        title = self.font_title.render("PAUSED", True, self.accent_color)
        screen.blit(title, (sw // 2 - title.get_width() // 2, menu_y + 25))

        self.update_layout(sw, sh)

        for btn in self.buttons:
            btn.draw(screen)

        hint = self.font_hint.render(
            "↑↓ Navigate  |  ENTER Select  |  ESC Resume", True, self.muted_color
        )
        screen.blit(hint, (sw // 2 - hint.get_width() // 2, menu_y + menu_h - 30))


class SettingsMenu:
    def __init__(self):
        self.font_title = pygame.font.Font(None, 48)
        self.font_option = pygame.font.Font(None, 28)
        self.font_label = pygame.font.Font(None, 22)
        self.font_hint = pygame.font.Font(None, 20)

        self.accent_color = (0, 200, 255)
        self.text_color = (240, 240, 250)
        self.muted_color = (120, 140, 170)

        self.categories = ["Gameplay", "Graphics", "Controls"]
        self.selected_category = 0
        self.selected_option = 0

        self.settings = {
            "Gameplay": [
                ("Difficulty", 1, ["Easy", "Normal", "Hard"]),
                ("Traffic Density", 50, 0, 100),
                ("Show FPS", True),
            ],
            "Graphics": [
                ("Fullscreen", False),
                ("Show Camera", True),
                ("VSync", True),
            ],
            "Controls": [
                ("Steering Sens", 1.0, 0.1, 5.0),
                ("Brake Sens", 5, 1, 10),
            ],
        }

        self.sliders: dict[str, Slider] = {}
        self._hovered_category = None
        self._hovered_option = None
        self._close_button = None

    def handle_input(
        self, event: pygame.event.Event, mouse_pos: tuple = None
    ) -> Optional[dict]:
        if event.type == pygame.KEYDOWN:
            cat = self.categories[self.selected_category]
            options = self.settings[cat]

            if event.key == pygame.K_LEFT:
                self._adjust_value(cat, options[self.selected_option][0], -1)
                return {"action": "changed"}
            elif event.key == pygame.K_RIGHT:
                self._adjust_value(cat, options[self.selected_option][0], 1)
                return {"action": "changed"}
            elif event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(options)
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(options)
            elif event.key == pygame.K_TAB:
                self.selected_category = (self.selected_category + 1) % len(
                    self.categories
                )
                self.selected_option = 0
            elif event.key == pygame.K_ESCAPE:
                return {"action": "close"}

        if event.type == pygame.MOUSEBUTTONDOWN and mouse_pos:
            sw, sh = pygame.display.get_surface().get_size()
            panel_w, panel_h = 720, 520
            panel_x = sw // 2 - panel_w // 2
            panel_y = sh // 2 - panel_h // 2

            close_btn = pygame.Rect(panel_x + panel_w - 50, panel_y + 15, 35, 35)
            if close_btn.collidepoint(mouse_pos):
                return {"action": "close"}

            sidebar_w = 160
            sidebar_x = panel_x + 20
            sidebar_y = panel_y + 80

            for i in range(len(self.categories)):
                cat_rect = pygame.Rect(
                    sidebar_x + 5, sidebar_y + 25 + i * 60, sidebar_w - 10, 45
                )
                if cat_rect.collidepoint(mouse_pos):
                    self.selected_category = i
                    self.selected_option = 0
                    return {"action": "changed"}

            cat = self.categories[self.selected_category]
            opts = self.settings[cat]
            content_x = panel_x + sidebar_w + 35
            content_y = panel_y + 80

            for i in range(len(opts)):
                opt_y = content_y + 25 + i * 75
                bar_rect = pygame.Rect(content_x, opt_y + 28, 350, 20)
                if bar_rect.collidepoint(mouse_pos):
                    self.selected_option = i
                    return {"action": "changed"}

                if i == self.selected_option:
                    val = self.get_value(cat, opts[i][0])
                    if isinstance(val, bool):
                        toggle_rect = pygame.Rect(content_x + 280, opt_y, 50, 25)
                        if toggle_rect.collidepoint(mouse_pos):
                            self._adjust_value(cat, opts[i][0], 1)
                            return {"action": "changed"}
                    elif isinstance(val, str):
                        left_rect = pygame.Rect(content_x + 200, opt_y, 30, 25)
                        right_rect = pygame.Rect(content_x + 320, opt_y, 30, 25)
                        if left_rect.collidepoint(mouse_pos):
                            self._adjust_value(cat, opts[i][0], -1)
                            return {"action": "changed"}
                        elif right_rect.collidepoint(mouse_pos):
                            self._adjust_value(cat, opts[i][0], 1)
                            return {"action": "changed"}

        return None

    def update(self, mouse_pos: tuple) -> None:
        sw, sh = pygame.display.get_surface().get_size()
        panel_w, panel_h = 720, 520
        panel_x = sw // 2 - panel_w // 2
        panel_y = sh // 2 - panel_h // 2

        sidebar_w = 160
        sidebar_x = panel_x + 20
        sidebar_y = panel_y + 80

        self._hovered_category = None
        self._hovered_option = None

        for i in range(len(self.categories)):
            cat_rect = pygame.Rect(
                sidebar_x + 5, sidebar_y + 25 + i * 60, sidebar_w - 10, 45
            )
            if cat_rect.collidepoint(mouse_pos):
                self._hovered_category = i
                return

        cat = self.categories[self.selected_category]
        opts = self.settings[cat]
        content_x = panel_x + sidebar_w + 35
        content_y = panel_y + 80

        for i in range(len(opts)):
            opt_y = content_y + 25 + i * 75
            bar_rect = pygame.Rect(content_x, opt_y + 28, 350, 20)
            if bar_rect.collidepoint(mouse_pos):
                self._hovered_option = i
                return

            val = self.get_value(cat, opts[i][0])
            if isinstance(val, bool):
                toggle_rect = pygame.Rect(content_x + 280, opt_y, 50, 25)
                if toggle_rect.collidepoint(mouse_pos):
                    self._hovered_option = i
                    return
            elif isinstance(val, str):
                left_rect = pygame.Rect(content_x + 200, opt_y, 30, 25)
                right_rect = pygame.Rect(content_x + 320, opt_y, 30, 25)
                if left_rect.collidepoint(mouse_pos) or right_rect.collidepoint(
                    mouse_pos
                ):
                    self._hovered_option = i
                    return

    def _adjust_value(self, category: str, option: str, delta: int) -> None:
        opts = self.settings[category]
        for i, opt in enumerate(opts):
            if opt[0] == option:
                if len(opt) == 3 and isinstance(opt[2], list):
                    new_idx = (opt[1] + delta) % len(opt[2])
                    self.settings[category][i] = (opt[0], new_idx, opt[2])
                elif len(opt) == 4:
                    new_val = opt[1] + delta * (5 if "Density" in option else 0.5)
                    new_val = max(opt[2], min(opt[3], new_val))
                    self.settings[category][i] = (opt[0], new_val, opt[2], opt[3])
                elif len(opt) == 2:
                    self.settings[category][i] = (opt[0], not opt[1])
                break

    def get_value(self, category: str, option: str):
        for opt in self.settings[category]:
            if opt[0] == option:
                if len(opt) == 3 and isinstance(opt[2], list):
                    return opt[2][opt[1]]
                return opt[1]
        return None

    def apply_to_game(self, game_settings) -> None:
        cat = self.categories[0]
        opts = self.settings[cat]
        for opt in opts:
            if opt[0] == "Difficulty":
                game_settings.difficulty = self.get_value(cat, "Difficulty")
            elif opt[0] == "Traffic Density":
                game_settings.obstacle_frequency = self.get_value(
                    cat, "Traffic Density"
                )
            elif opt[0] == "Show FPS":
                game_settings.show_fps = self.get_value(cat, "Show FPS")

        cat = self.categories[1]
        opts = self.settings[cat]
        for opt in opts:
            if opt[0] == "Fullscreen":
                game_settings.set_fullscreen(self.get_value(cat, "Fullscreen"))
            elif opt[0] == "Show Camera":
                game_settings.show_camera = self.get_value(cat, "Show Camera")
            elif opt[0] == "VSync":
                game_settings.vsync = self.get_value(cat, "VSync")

        cat = self.categories[2]
        opts = self.settings[cat]
        for opt in opts:
            if opt[0] == "Steering Sens":
                game_settings.steering_sensitivity = self.get_value(
                    cat, "Steering Sens"
                )
            elif opt[0] == "Brake Sens":
                game_settings.brake_threshold = self.get_value(cat, "Brake Sens")

    def draw(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_width(), screen.get_height()

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        panel_w, panel_h = 720, 520
        panel_x = sw // 2 - panel_w // 2
        panel_y = sh // 2 - panel_h // 2

        draw_rounded_rect(
            screen, (20, 30, 50, 245), (panel_x, panel_y, panel_w, panel_h)
        )
        draw_rounded_rect(screen, self.accent_color, (panel_x, panel_y, panel_w, 4))
        draw_rounded_rect(
            screen, self.accent_color, (panel_x, panel_y, panel_w, panel_h), 1
        )

        title = self.font_title.render("SETTINGS", True, self.accent_color)
        screen.blit(title, (panel_x + 30, panel_y + 20))

        close_btn = pygame.Rect(panel_x + panel_w - 50, panel_y + 15, 35, 35)
        draw_rounded_rect(screen, (200, 80, 80), close_btn)
        close_x = self.font_title.render("X", True, (255, 255, 255))
        screen.blit(close_x, (close_btn.x + 10, close_btn.y + 2))
        self._close_button = close_btn

        sidebar_w = 160
        sidebar_x = panel_x + 20
        sidebar_y = panel_y + 80
        sidebar_h = panel_h - 110

        sb = pygame.Surface((sidebar_w, sidebar_h), pygame.SRCALPHA)
        sb.fill((25, 35, 55, 120))
        screen.blit(sb, (sidebar_x, sidebar_y))

        for i, cat in enumerate(self.categories):
            cat_y = sidebar_y + 25 + i * 60
            is_sel = i == self.selected_category
            is_hover = i == self._hovered_category

            bg_col = (
                (0, 180, 255, 60)
                if is_sel
                else ((0, 180, 255, 30) if is_hover else (0, 0, 0, 0))
            )
            sb2 = pygame.Surface((sidebar_w - 10, 45), pygame.SRCALPHA)
            sb2.fill(bg_col)
            screen.blit(sb2, (sidebar_x + 5, cat_y))

            color = self.accent_color if is_sel else self.text_color
            cat_text = self.font_option.render(cat, True, color)
            screen.blit(cat_text, (sidebar_x + 25, cat_y + 10))

        content_x = panel_x + sidebar_w + 35
        content_w = panel_w - sidebar_w - 55
        content_y = panel_y + 80

        cat = self.categories[self.selected_category]
        opts = self.settings[cat]

        for i, opt in enumerate(opts):
            opt_y = content_y + 25 + i * 75
            is_sel = i == self.selected_option
            is_hover = i == self._hovered_option

            if is_hover or is_sel:
                hover_bg = pygame.Surface((content_w - 20, 60), pygame.SRCALPHA)
                hover_bg.fill((0, 180, 255, 20))
                screen.blit(hover_bg, (content_x - 5, opt_y - 5))

            color = self.accent_color if is_sel else self.text_color
            label = self.font_label.render(opt[0], True, color)
            screen.blit(label, (content_x, opt_y))

            value = self.get_value(cat, opt[0])

            if isinstance(value, bool):
                val_str = "ON" if value else "OFF"
                val_color = self.accent_color if value else self.muted_color
            elif isinstance(value, str):
                val_str = value
                val_color = self.text_color
            else:
                val_str = f"{value:.0f}" if isinstance(value, float) else str(value)
                val_color = self.text_color

            val_text = self.font_option.render(val_str, True, val_color)
            screen.blit(val_text, (content_x + content_w - 100, opt_y))

            bar_y = opt_y + 30
            bar_h = 10
            pygame.draw.rect(
                screen,
                (40, 50, 70),
                (content_x, bar_y, content_w - 20, bar_h),
                border_radius=5,
            )

            if isinstance(opt[1], int) and len(opt) == 4:
                pct = (opt[1] - opt[2]) / (opt[3] - opt[2])
                fill_w = int((content_w - 20) * pct)
                if fill_w > 0:
                    pygame.draw.rect(
                        screen,
                        self.accent_color,
                        (content_x, bar_y, fill_w, bar_h),
                        border_radius=5,
                    )

        hint = self.font_hint.render(
            "← → Adjust  |  ↑ ↓ Navigate  |  TAB Category  |  ESC Close",
            True,
            self.muted_color,
        )
        screen.blit(
            hint,
            (panel_x + panel_w // 2 - hint.get_width() // 2, panel_y + panel_h - 30),
        )
