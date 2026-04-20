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

    # Improve layout for long prompts by wrapping text and expanding panel width when necessary.
    screen_w, screen_h = screen.get_width(), screen.get_height()
    max_panel_w = min(screen_w - 80, 1100)
    min_panel_w = 700

    def wrap_text(text: str, font: pygame.font.Font, max_width: int):
        words = text.split()
        lines = []
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    # Determine candidate widths based on rendered option widths and prompt width
    option_texts = [f"{i}) {o}" for i, o in enumerate(question.options, start=1)]
    option_w = 0
    for ot in option_texts:
        option_w = max(option_w, body_font.size(ot)[0])

    # Reserve some padding inside the panel
    inner_padding = 80
    candidate_w = max(min_panel_w, option_w + inner_padding)

    # Try to wrap prompt to a comfortable width
    tentative_wrap_width = min(max_panel_w - inner_padding, max(candidate_w - inner_padding, 520))
    prompt_lines = wrap_text(question.prompt, body_font, tentative_wrap_width)
    prompt_w = 0
    for line in prompt_lines:
        prompt_w = max(prompt_w, body_font.size(line)[0])

    panel_w = max(candidate_w, prompt_w + inner_padding)
    panel_w = min(panel_w, max_panel_w)

    # Compute height dynamically based on number of lines and options
    line_height = body_font.get_linesize()
    title_h = title_font.get_height() + 12
    subtitle_h = body_font.get_height() + 8
    difficulty_h = body_font.get_height() + 8
    prompt_h = len(prompt_lines) * line_height + 12
    options_h = len(question.options) * (line_height + 6) + 12
    hint_h = body_font.get_height() + 20

    panel_h = 120 + prompt_h + options_h + hint_h
    panel_h = max(panel_h, 320)

    panel = pygame.Rect((screen_w - panel_w) // 2, (screen_h - panel_h) // 2, panel_w, panel_h)
    draw_rounded_rect(screen, (20, 20, 20), panel)

    if is_heart_question:
        border_color = (255, 100, 150)
        title = title_font.render("LIFE UP!", True, (255, 150, 180))
        subtitle = body_font.render("Answer correctly to gain 1 life!", True, (255, 200, 220))
    else:
        border_color = (255, 200, 0)
        title = title_font.render("LAST CHANCE!", True, (255, 220, 120))
        subtitle = body_font.render("Answer correctly to survive!", True, (255, 200, 150))

    draw_rounded_rect(screen, border_color, panel, 3)

    difficulty = getattr(question, "difficulty", "EASY")
    difficulty_color = {
        "EASY": (120, 255, 150),
        "MEDIUM": (255, 220, 120),
        "HARD": (255, 140, 140),
    }.get(difficulty, (200, 200, 200))
    difficulty_text = body_font.render(f"Difficulty: {difficulty}", True, difficulty_color)

    # Render title, subtitle, difficulty
    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 18))
    screen.blit(subtitle, (panel.centerx - subtitle.get_width() // 2, panel.y + 18 + title.get_height() + 8))
    screen.blit(difficulty_text, (panel.centerx - difficulty_text.get_width() // 2, panel.y + 18 + title.get_height() + 8 + subtitle.get_height() + 6))

    # Render wrapped prompt
    prompt_start_y = panel.y + 18 + title.get_height() + 8 + subtitle.get_height() + 6 + difficulty_text.get_height() + 12
    cur_y = prompt_start_y
    for line in prompt_lines:
        rendered = body_font.render(line, True, (255, 255, 255))
        screen.blit(rendered, (panel.x + inner_padding // 2, cur_y))
        cur_y += line_height

    # Render options
    option_x = panel.x + 48
    option_y = cur_y + 12
    for index, option in enumerate(question.options, start=1):
        is_selected = (index - 1) == selected_option
        option_color = (255, 255, 100) if is_selected else (240, 240, 240)
        prefix = "> " if is_selected else "  "
        # Wrap option text if it's too long
        option_lines = wrap_text(f"{prefix}{index}) {option}", body_font, panel_w - inner_padding)
        for ol in option_lines:
            option_text = body_font.render(ol, True, option_color)
            screen.blit(option_text, (option_x, option_y))
            option_y += line_height
        option_y += 6

    key_range = ", ".join(str(i) for i in range(1, question.answer_count + 1))
    hint_lines = wrap_text(f"Press {key_range} / Swipe up/down / Close index finger to confirm", body_font, panel_w - inner_padding)
    hint_y = panel.bottom - 40
    for i, hl in enumerate(hint_lines):
        hint_render = body_font.render(hl, True, (180, 180, 180))
        screen.blit(hint_render, (panel.centerx - hint_render.get_width() // 2, hint_y + i * line_height))


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
    lobby_text = body_font.render("Press L to go back to lobby", True, (200, 200, 200))

    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 34))
    screen.blit(
        score_text, (panel.centerx - score_text.get_width() // 2, panel.y + 128)
    )
    screen.blit(
        retry_text, (panel.centerx - retry_text.get_width() // 2, panel.y + 188)
    )
    screen.blit(
        lobby_text, (panel.centerx - lobby_text.get_width() // 2, panel.y + 224)
    )
