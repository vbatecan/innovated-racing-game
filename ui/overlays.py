from __future__ import annotations

import pygame

from models.question import Question


def draw_last_chance_overlay(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    body_font: pygame.font.Font,
    question: Question,
) -> None:
    overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    panel_w, panel_h = 700, 380
    panel = pygame.Rect(
        (screen.get_width() - panel_w) // 2,
        (screen.get_height() - panel_h) // 2,
        panel_w,
        panel_h,
    )
    pygame.draw.rect(screen, (20, 20, 20), panel, border_radius=12)
    pygame.draw.rect(screen, (255, 200, 0), panel, width=3, border_radius=12)

    title = title_font.render("LAST CHANCE!", True, (255, 220, 120))
    prompt = body_font.render(question.prompt, True, (255, 255, 255))
    key_range = ", ".join(str(i) for i in range(1, question.answer_count + 1))
    hint = body_font.render(f"Press {key_range} to answer", True, (180, 180, 180))

    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 24))
    screen.blit(prompt, (panel.centerx - prompt.get_width() // 2, panel.y + 92))

    option_y = panel.y + 150
    for index, option in enumerate(question.options, start=1):
        option_text = body_font.render(f"{index}) {option}", True, (240, 240, 240))
        screen.blit(option_text, (panel.x + 64, option_y))
        option_y += 42

    screen.blit(hint, (panel.centerx - hint.get_width() // 2, panel.bottom - 52))


def draw_game_over_overlay(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    body_font: pygame.font.Font,
    final_score: int,
) -> None:
    overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))

    panel_w, panel_h = 640, 300
    panel = pygame.Rect(
        (screen.get_width() - panel_w) // 2,
        (screen.get_height() - panel_h) // 2,
        panel_w,
        panel_h,
    )
    pygame.draw.rect(screen, (25, 25, 25), panel, border_radius=12)
    pygame.draw.rect(screen, (255, 80, 80), panel, width=3, border_radius=12)

    title = title_font.render("GAME OVER", True, (255, 90, 90))
    score_text = body_font.render(f"Final Score: {final_score}", True, (255, 255, 255))
    retry_text = body_font.render("Press R to restart", True, (200, 200, 200))

    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 34))
    screen.blit(score_text, (panel.centerx - score_text.get_width() // 2, panel.y + 128))
    screen.blit(retry_text, (panel.centerx - retry_text.get_width() // 2, panel.y + 188))
