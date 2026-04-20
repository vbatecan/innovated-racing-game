"""Game overlay rendering for quiz questions, life bonuses, and game over screens.

Provides visual overlays for educational question prompts during gameplay,
including "last chance" survival questions and heart bonus life-ups.
"""

from __future__ import annotations

import pygame

from models.question import Question
from ui.game_ui import draw_rounded_rect


def draw_question_overlay(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    body_font: pygame.font.Font,
    question: Question,
    selected_option: int = 0,
    is_heart_question: bool = False,
) -> None:
    """Render a question overlay for educational prompts during gameplay.

    Displays a centered panel with question text, multiple choice options,
    and input instructions. Different styling is applied for heart bonus
    questions versus survival/last chance questions.

    Args:
        screen: Pygame surface to render on.
        title_font: Font for the overlay title ("LIFE UP!" or "LAST CHANCE!").
        body_font: Font for question text and options.
        question: Question object containing prompt and answer options.
        selected_option: Currently selected option index (0-based).
        is_heart_question: True for life bonus question, False for survival question.
    """
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
    draw_rounded_rect(screen, (20, 20, 20), panel)

    if is_heart_question:
        border_color = (255, 100, 150)
        title = title_font.render("LIFE UP!", True, (255, 150, 180))
        subtitle = body_font.render(
            "Answer correctly to gain 1 life!", True, (255, 200, 220)
        )
    else:
        border_color = (255, 200, 0)
        title = title_font.render("LAST CHANCE!", True, (255, 220, 120))
        subtitle = body_font.render(
            "Answer correctly to survive!", True, (255, 200, 150)
        )

    draw_rounded_rect(screen, border_color, panel, 3)

    difficulty = getattr(question, "difficulty", "EASY")
    difficulty_color = {
        "EASY": (120, 255, 150),
        "MEDIUM": (255, 220, 120),
        "HARD": (255, 140, 140),
    }.get(difficulty, (200, 200, 200))
    difficulty_text = body_font.render(
        f"Difficulty: {difficulty}",
        True,
        difficulty_color,
    )

    prompt = body_font.render(question.prompt, True, (255, 255, 255))
    key_range = ", ".join(str(i) for i in range(1, question.answer_count + 1))
    hint = body_font.render(
        f"Press {key_range} / Swipe up/down / Close index finger to confirm",
        True,
        (180, 180, 180),
    )

    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 24))
    screen.blit(subtitle, (panel.centerx - subtitle.get_width() // 2, panel.y + 60))
    screen.blit(
        difficulty_text,
        (panel.centerx - difficulty_text.get_width() // 2, panel.y + 96),
    )
    screen.blit(prompt, (panel.centerx - prompt.get_width() // 2, panel.y + 130))

    option_y = panel.y + 185
    for index, option in enumerate(question.options, start=1):
        is_selected = (index - 1) == selected_option
        option_color = (255, 255, 100) if is_selected else (240, 240, 240)
        prefix = "> " if is_selected else "  "
        option_text = body_font.render(f"{prefix}{index}) {option}", True, option_color)
        screen.blit(option_text, (panel.x + 64, option_y))
        option_y += 42

    screen.blit(hint, (panel.centerx - hint.get_width() // 2, panel.bottom - 52))


def draw_last_chance_overlay(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    body_font: pygame.font.Font,
    question: Question,
    selected_option: int = 0,
) -> None:
    """Render a survival question overlay when player would otherwise lose.

    Convenience wrapper around draw_question_overlay for "last chance" scenarios
    where answering correctly allows the player to continue after taking damage.

    Args:
        screen: Pygame surface to render on.
        title_font: Font for the overlay title.
        body_font: Font for question text and options.
        question: Question object containing prompt and answer options.
        selected_option: Currently selected option index (0-based).
    """
    draw_question_overlay(
        screen, title_font, body_font, question, selected_option, False
    )


def draw_game_over_overlay(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    body_font: pygame.font.Font,
    final_score: int,
) -> None:
    """Render the game over screen with final score display.

    Args:
        screen: Pygame surface to render on.
        title_font: Font for the "GAME OVER" title.
        body_font: Font for the score and retry instructions.
        final_score: Player's final score to display.
    """
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
    draw_rounded_rect(screen, (25, 25, 25), panel)
    draw_rounded_rect(screen, (255, 80, 80), panel, 3)

    title = title_font.render("GAME OVER", True, (255, 90, 90))
    score_text = body_font.render(f"Currency Earned: CR {final_score}", True, (255, 255, 255))
    retry_text = body_font.render("Press R to restart", True, (200, 200, 200))

    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 34))
    screen.blit(
        score_text, (panel.centerx - score_text.get_width() // 2, panel.y + 128)
    )
    screen.blit(
        retry_text, (panel.centerx - retry_text.get_width() // 2, panel.y + 188)
    )
