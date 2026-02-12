from __future__ import annotations

from typing import Optional
import math

import pygame

from car import Car
from controller import Controller


class PlayerHUD:
    def __init__(
        self,
        player_car: Car,
        controller: Controller,
        font: pygame.font.Font,
        position: tuple[int, int] = (10, 10),
        size: tuple[int, int] = (360, 190),
        camera_preview_size: tuple[int, int] = (200, 150),
        show_camera_preview: bool = True,
    ) -> None:
        self.speed = player_car.current_speed
        self.max_speed = player_car.max_speed
        self.is_braking = controller.breaking
        self.steer = controller.steer
        self.gear: str = self._compute_gear(self.speed, self.max_speed)
        self.acceleration = 0.0
        self._last_speed = float(self.speed)
        self.score: Optional[int] = None
        self.fps: Optional[int] = None
        self.max_fps: Optional[int] = None
        self._camera_frame = None

        self.font = font
        self.position = position
        self.size = size
        self.camera_preview_size = camera_preview_size
        self.show_camera_preview = show_camera_preview

        self._panel_color = (0, 0, 0, 160)
        self._text_color = (255, 255, 255)
        self._accent_color = (0, 200, 255)
        self._warn_color = (255, 80, 80)
        self._muted_color = (120, 120, 120)

    def update_from_game(
        self,
        player_car: Car,
        controller: Controller,
        score: Optional[int] = None,
        fps: Optional[int] = None,
        max_fps: Optional[int] = None,
    ) -> None:
        self.speed = player_car.current_speed
        delta_speed = float(self.speed) - self._last_speed
        self.max_speed = player_car.max_speed
        self.is_braking = controller.breaking
        self.steer = controller.steer
        self.gear = self._compute_gear(self.speed, self.max_speed)
        self.score = score
        self.fps = fps
        self.max_fps = max_fps
        if self.fps is not None and self.fps > 0:
            self.acceleration = delta_speed * float(self.fps)
        else:
            self.acceleration = delta_speed
        self._last_speed = float(self.speed)
        self._camera_frame = (
            controller.get_frame() if self.show_camera_preview else None
        )

    def set_speed(self, current_speed: float, max_speed: float) -> None:
        self.speed = current_speed
        self.max_speed = max_speed

    def draw(self, screen: pygame.Surface) -> None:
        panel = pygame.Surface(self.size, pygame.SRCALPHA)
        panel.fill(self._panel_color)
        screen.blit(panel, self.position)

        x, y = self.position
        padding = 10
        line_height = self.font.get_linesize()
        text_y = y + padding

        # Layout: left = telemetry + speedometer + gesture icons, right = camera preview.
        camera_w, _camera_h = self.camera_preview_size
        right_x = x + self.size[0] - padding - camera_w
        left_w = max(0, right_x - (x + padding) - padding)

        if self.show_camera_preview:
            self._draw_camera_preview(
                screen, (right_x, y + padding), self.camera_preview_size
            )

        speed_text = f"Speed: {self.speed:.1f} / {self.max_speed:.1f}"
        screen.blit(
            self.font.render(speed_text, True, self._text_color),
            (x + padding, text_y),
        )
        text_y += line_height

        gear_text = f"Gear: {self.gear}"
        screen.blit(
            self.font.render(gear_text, True, self._text_color),
            (x + padding, text_y),
        )
        text_y += line_height

        steer_text = f"Steer: {self.steer:+.2f}"
        screen.blit(
            self.font.render(steer_text, True, self._text_color),
            (x + padding, text_y),
        )
        text_y += line_height

        brake_color = self._warn_color if self.is_braking else self._accent_color
        brake_text = "BRAKE" if self.is_braking else "THROTTLE"
        screen.blit(
            self.font.render(f"State: {brake_text}", True, brake_color),
            (x + padding, text_y),
        )
        text_y += line_height

        if self.score is not None:
            screen.blit(
                self.font.render(f"Score: {self.score}", True, self._text_color),
                (x + padding, text_y),
            )
            text_y += line_height

        if self.fps is not None and self.max_fps is not None:
            fps_text = f"FPS: {self.fps} / {self.max_fps}"
            screen.blit(
                self.font.render(fps_text, True, self._text_color),
                (x + padding, text_y),
            )

        # Gesture recognized icons within the HUD panel.
        icon_size = 46
        icon_x = x + padding
        icon_y = y + self.size[1] - padding - 8 - icon_size - 10
        self._draw_gesture_icons(screen, (icon_x, icon_y))

        self._draw_speed_bar(
            screen, x + padding, y + self.size[1] - padding - 8, max_width=left_w
        )

        # Speedometer + acceleration dial at the top center of the screen, side-by-side.
        screen_w = screen.get_width()
        speed_radius = 48
        accel_radius = 36
        top_margin = 10
        horizontal_gap = 20

        # Arrange dials horizontally: speed on left, accel on right, centered overall
        total_width = speed_radius * 2 + accel_radius * 2 + horizontal_gap
        left_x = (screen_w - total_width) // 2
        center_y = top_margin + speed_radius

        speed_center = (left_x + speed_radius, center_y)
        accel_center = (
            left_x + speed_radius * 2 + horizontal_gap + accel_radius,
            center_y,
        )

        self._draw_speedometer(screen, speed_center, speed_radius)
        self._draw_accelometer(screen, accel_center, accel_radius)

    def _draw_speed_bar(
        self, screen: pygame.Surface, x: int, y: int, max_width: Optional[int] = None
    ) -> None:
        bar_width = self.size[0] - 2 * 10
        if max_width is not None and max_width > 0:
            bar_width = min(bar_width, max_width)
        bar_height = 8
        ratio = 0.0 if self.max_speed <= 0 else min(self.speed / self.max_speed, 1.0)
        fill_width = int(bar_width * ratio)

        pygame.draw.rect(screen, (40, 40, 40), (x, y, bar_width, bar_height))
        pygame.draw.rect(screen, self._accent_color, (x, y, fill_width, bar_height))

    def _compute_gear(self, speed: float, max_speed: float) -> str:
        if speed <= 0.1:
            return "N"
        if max_speed <= 0:
            return "1"
        ratio = max(0.0, min(speed / max_speed, 1.0))
        gear = 1 + int(ratio * 4.999)
        return str(min(5, max(1, gear)))

    def _draw_speedometer(
        self, screen: pygame.Surface, center: tuple[int, int], radius: int
    ) -> None:
        cx, cy = center
        rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)

        # Background dial.
        pygame.draw.circle(screen, (20, 20, 20), center, radius)
        pygame.draw.circle(screen, self._accent_color, center, radius, 2)

        # Arc from 225deg to -45deg (i.e. 270deg sweep).
        start_angle = math.radians(225)
        end_angle = math.radians(-45)
        pygame.draw.arc(screen, self._muted_color, rect, end_angle, start_angle, 3)

        ratio = (
            0.0
            if self.max_speed <= 0
            else max(0.0, min(self.speed / self.max_speed, 1.0))
        )
        needle_angle = start_angle - ratio * (start_angle - end_angle)
        nx = cx + int((radius - 8) * math.cos(needle_angle))
        ny = cy - int((radius - 8) * math.sin(needle_angle))
        needle_color = self._warn_color if self.is_braking else self._accent_color
        pygame.draw.line(screen, needle_color, center, (nx, ny), 3)
        pygame.draw.circle(screen, self._text_color, center, 4)

        speed_value = self.font.render(f"{self.speed:.0f}", True, self._text_color)
        screen.blit(speed_value, speed_value.get_rect(center=(cx, cy + 8)))

    def _draw_accelometer(
        self, screen: pygame.Surface, center: tuple[int, int], radius: int
    ) -> None:
        cx, cy = center
        rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)

        pygame.draw.circle(screen, (20, 20, 20), center, radius)
        pygame.draw.circle(screen, self._accent_color, center, radius, 2)

        start_angle = math.radians(225)
        end_angle = math.radians(-45)
        pygame.draw.arc(screen, self._muted_color, rect, end_angle, start_angle, 3)

        # Normalize around 0 (deceleration to the left, acceleration to the right).
        max_abs = max(5.0, float(self.max_speed) * 1.5)
        value = max(-max_abs, min(max_abs, float(self.acceleration)))
        normalized = value / max_abs  # [-1, 1]
        t = (normalized + 1.0) / 2.0  # [0, 1]
        needle_angle = start_angle - t * (start_angle - end_angle)
        nx = cx + int((radius - 7) * math.cos(needle_angle))
        ny = cy - int((radius - 7) * math.sin(needle_angle))
        needle_color = self._warn_color if value < 0 else self._accent_color
        pygame.draw.line(screen, needle_color, center, (nx, ny), 3)
        pygame.draw.circle(screen, self._text_color, center, 3)

        label = self.font.render("ACC", True, self._muted_color)
        screen.blit(label, label.get_rect(center=(cx, cy - 8)))
        value_text = self.font.render(f"{value:+.0f}", True, self._text_color)
        screen.blit(value_text, value_text.get_rect(center=(cx, cy + 10)))

    def _draw_gesture_icons(
        self, screen: pygame.Surface, top_left: tuple[int, int]
    ) -> None:
        x, y = top_left
        size = 46
        gap = 10

        # Brake / Stop icon.
        if self.is_braking:
            self._draw_stop_sign(screen, (x, y), size)
        else:
            self._draw_throttle_icon(screen, (x, y), size)

        # Steering direction icon.
        steer_x = x + size + gap
        if self.steer < -0.6:
            self._draw_arrow_icon(screen, (steer_x, y), size, direction="left")
        elif self.steer > 0.6:
            self._draw_arrow_icon(screen, (steer_x, y), size, direction="right")
        else:
            self._draw_arrow_icon(screen, (steer_x, y), size, direction="center")

    def _draw_stop_sign(
        self, screen: pygame.Surface, top_left: tuple[int, int], size: int
    ) -> None:
        x, y = top_left
        cx = x + size // 2
        cy = y + size // 2
        r = size // 2
        points = []
        for i in range(8):
            angle = math.radians(22.5 + i * 45)
            px = cx + int(r * math.cos(angle))
            py = cy + int(r * math.sin(angle))
            points.append((px, py))
        pygame.draw.polygon(screen, self._warn_color, points)
        pygame.draw.polygon(screen, self._text_color, points, 2)
        label = self.font.render("STOP", True, self._text_color)
        screen.blit(label, label.get_rect(center=(cx, cy)))

    def _draw_throttle_icon(
        self, screen: pygame.Surface, top_left: tuple[int, int], size: int
    ) -> None:
        x, y = top_left
        rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(screen, (20, 20, 20), rect)
        pygame.draw.rect(screen, self._accent_color, rect, 2)
        # Simple "pedal" bar.
        inner = pygame.Rect(x + size // 3, y + size // 5, size // 3, int(size * 0.6))
        pygame.draw.rect(screen, self._accent_color, inner)

    def _draw_arrow_icon(
        self,
        screen: pygame.Surface,
        top_left: tuple[int, int],
        size: int,
        direction: str,
    ) -> None:
        x, y = top_left
        rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(screen, (20, 20, 20), rect)
        pygame.draw.rect(screen, self._accent_color, rect, 2)

        cx = x + size // 2
        cy = y + size // 2
        color = self._accent_color
        if direction == "left":
            pts = [(cx - 14, cy), (cx + 10, cy - 12), (cx + 10, cy + 12)]
            pygame.draw.polygon(screen, color, pts)
        elif direction == "right":
            pts = [(cx + 14, cy), (cx - 10, cy - 12), (cx - 10, cy + 12)]
            pygame.draw.polygon(screen, color, pts)
        else:
            pygame.draw.circle(screen, self._muted_color, (cx, cy), 6)

    def _draw_camera_preview(
        self,
        screen: pygame.Surface,
        top_left: tuple[int, int],
        size: tuple[int, int],
    ) -> None:
        x, y = top_left
        w, h = size
        border = pygame.Rect(x - 2, y - 2, w + 4, h + 4)
        pygame.draw.rect(screen, (20, 20, 20), border)
        pygame.draw.rect(screen, self._accent_color, border, 2)

        if self._camera_frame is None:
            label = self.font.render("Camera…", True, self._muted_color)
            screen.blit(label, (x + 8, y + 8))
            return

        try:
            import cv2
        except ImportError:
            return

        try:
            frame_rgb = cv2.cvtColor(self._camera_frame, cv2.COLOR_BGR2RGB)
        except cv2.error:
            return

        # Convert numpy array (H, W, 3) into a pygame surface.
        surf = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
        surf = pygame.transform.smoothscale(surf, (w, h))
        screen.blit(surf, (x, y))
