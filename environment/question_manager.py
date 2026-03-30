from __future__ import annotations

import random

import config
from models.question import MultipleChoiceQuestion, Question, TrueOrFalseQuestion


class QuestionManager:
    """Manages a pool of quiz questions and provides random selection with validation."""

    def __init__(
        self,
        true_false_questions: list[dict] | None = None,
        multiple_choice_questions: list[dict] | None = None,
    ) -> None:
        """
        Initialize the question pool from provided or default question sources.

        Loads true/false and multiple choice questions from provided dictionaries
        or falls back to config defaults. Ensures at least one fallback question
        exists if no valid questions are provided.

        Args:
            true_false_questions: List of dicts with "prompt" and "answer" keys,
                or None to use config.TRUE_FALSE_QUESTIONS.
            multiple_choice_questions: List of dicts with "prompt", "options",
                and "correct_index" keys, or None to use config.MULTIPLE_CHOICE_QUESTIONS.
        """
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
        """
        Select a random question from the loaded pool.

        Returns:
            A randomly selected Question instance from the internal pool.
        """
        return random.choice(self._questions)

    @staticmethod
    def validate_answer(question: Question, selected_index: int) -> bool:
        """
        Validate whether the selected answer index is correct for the given question.

        Args:
            question: The Question instance to validate against.
            selected_index: The zero-based index of the user's selected answer.

        Returns:
            True if the selected index matches the correct answer, False otherwise.
        """
        return question.is_correct(selected_index)

    def _load_true_false(self, payload: list[dict]) -> list[Question]:
        """
        Parse and instantiate TrueOrFalseQuestion objects from raw dictionaries.

        Filters out entries with empty prompts. Non-boolean answers are coerced
        to boolean values.

        Args:
            payload: List of dictionaries containing "prompt" and "answer" keys.

        Returns:
            List of validated TrueOrFalseQuestion instances.
        """
        loaded: list[Question] = []
        for raw in payload:
            prompt = str(raw.get("prompt", "")).strip()
            if not prompt:
                continue
            answer = bool(raw.get("answer", True))
            loaded.append(TrueOrFalseQuestion(prompt=prompt, answer=answer))
        return loaded

    def _load_multiple_choice(self, payload: list[dict]) -> list[Question]:
        """
        Parse and instantiate MultipleChoiceQuestion objects from raw dictionaries.

        Filters out entries with empty prompts, non-list options, or fewer than 2 options.
        Invalid correct_index values are handled by the MultipleChoiceQuestion constructor.

        Args:
            payload: List of dictionaries containing "prompt", "options", and
                "correct_index" keys.

        Returns:
            List of validated MultipleChoiceQuestion instances.
        """
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
