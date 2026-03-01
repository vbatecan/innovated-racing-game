from __future__ import annotations

import random

import config
from models.question import MultipleChoiceQuestion, Question, TrueOrFalseQuestion


class QuestionManager:
    def __init__(
        self,
        true_false_questions: list[dict] | None = None,
        multiple_choice_questions: list[dict] | None = None,
    ) -> None:
        tf_source = (
            true_false_questions
            if true_false_questions is not None
            else list(config.TRUE_FALSE_QUESTIONS)
        )
        mc_source = (
            multiple_choice_questions
            if multiple_choice_questions is not None
            else list(config.MULTIPLE_CHOICE_QUESTIONS)
        )

        self._questions: list[Question] = []
        self._questions.extend(self._load_true_false(tf_source))
        self._questions.extend(self._load_multiple_choice(mc_source))

        if not self._questions:
            self._questions.append(
                TrueOrFalseQuestion(
                    prompt="Driving within lane borders helps avoid collisions.",
                    answer=True,
                )
            )

    def get_random_question(self) -> Question:
        return random.choice(self._questions)

    @staticmethod
    def validate_answer(question: Question, selected_index: int) -> bool:
        return question.is_correct(selected_index)

    def _load_true_false(self, payload: list[dict]) -> list[Question]:
        loaded: list[Question] = []
        for raw in payload:
            prompt = str(raw.get("prompt", "")).strip()
            if not prompt:
                continue
            answer = bool(raw.get("answer", True))
            loaded.append(TrueOrFalseQuestion(prompt=prompt, answer=answer))
        return loaded

    def _load_multiple_choice(self, payload: list[dict]) -> list[Question]:
        loaded: list[Question] = []
        for raw in payload:
            prompt = str(raw.get("prompt", "")).strip()
            options = raw.get("options", [])
            correct_index = int(raw.get("correct_index", 0))
            if not prompt or not isinstance(options, list) or len(options) < 2:
                continue
            try:
                loaded.append(
                    MultipleChoiceQuestion(
                        prompt=prompt,
                        options=options,
                        correct_index=correct_index,
                    )
                )
            except ValueError:
                continue
        return loaded
