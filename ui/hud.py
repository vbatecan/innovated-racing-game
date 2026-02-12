from __future__ import annotations

from typing import Optional

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
    size: tuple[int, int] = (260, 130),
  ) -> None:
    self.speed = player_car.current_speed
    self.max_speed = player_car.max_speed
    self.is_braking = controller.breaking
    self.steer = controller.steer
    self.score: Optional[int] = None
    self.fps: Optional[int] = None
    self.max_fps: Optional[int] = None

    self.font = font
    self.position = position
    self.size = size

    self._panel_color = (0, 0, 0, 160)
    self._text_color = (255, 255, 255)
    self._accent_color = (0, 200, 255)
    self._warn_color = (255, 80, 80)

  def update_from_game(
    self,
    player_car: Car,
    controller: Controller,
    score: Optional[int] = None,
    fps: Optional[int] = None,
    max_fps: Optional[int] = None,
  ) -> None:
    self.speed = player_car.current_speed
    self.max_speed = player_car.max_speed
    self.is_braking = controller.breaking
    self.steer = controller.steer
    self.score = score
    self.fps = fps
    self.max_fps = max_fps

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

    speed_text = f"Speed: {self.speed:.1f} / {self.max_speed:.1f}"
    screen.blit(
      self.font.render(speed_text, True, self._text_color),
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

    self._draw_speed_bar(screen, x + padding, y + self.size[1] - padding - 8)

  def _draw_speed_bar(self, screen: pygame.Surface, x: int, y: int) -> None:
    bar_width = self.size[0] - 2 * 10
    bar_height = 8
    ratio = 0.0 if self.max_speed <= 0 else min(self.speed / self.max_speed, 1.0)
    fill_width = int(bar_width * ratio)

    pygame.draw.rect(screen, (40, 40, 40), (x, y, bar_width, bar_height))
    pygame.draw.rect(screen, self._accent_color, (x, y, fill_width, bar_height))
