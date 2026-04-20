from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Question:
    prompt: str
    options: tuple[str, ...]
    correct_index: int
    difficulty: str = "EASY"

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("Question prompt cannot be empty")
        if len(self.options) < 2:
            raise ValueError("Question must have at least 2 options")
        if not (0 <= self.correct_index < len(self.options)):
            raise ValueError("Correct index is out of bounds")

        normalized_difficulty = str(self.difficulty).strip().upper()
        if normalized_difficulty not in {"EASY", "MEDIUM", "HARD"}:
            normalized_difficulty = "EASY"
        object.__setattr__(self, "difficulty", normalized_difficulty)

    @property
    def answer_count(self) -> int:
        return len(self.options)

    def is_correct(self, selected_index: int) -> bool:
        return int(selected_index) == self.correct_index


@dataclass(frozen=True)
class TrueOrFalseQuestion(Question):
    def __init__(self, prompt: str, answer: bool, difficulty: str = "EASY"):
        correct_index = 0 if bool(answer) else 1
        super().__init__(
            prompt=prompt,
            options=("True", "False"),
            correct_index=correct_index,
            difficulty=difficulty,
        )


@dataclass(frozen=True)
class MultipleChoiceQuestion(Question):
    def __init__(
        self,
        prompt: str,
        options: Sequence[str],
        correct_index: int,
        difficulty: str = "EASY",
    ):
        normalized_options = tuple(str(option) for option in options)
        super().__init__(
            prompt=prompt,
            options=normalized_options,
            correct_index=int(correct_index),
            difficulty=difficulty,
        )
