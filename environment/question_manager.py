from __future__ import annotations

import random

import config
from models.question import MultipleChoiceQuestion, Question, TrueOrFalseQuestion


class QuestionManager:
    """Manages a pool of quiz questions and provides random selection with validation."""

    _DIFFICULTY_ORDER = ("EASY", "MEDIUM", "HARD")

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
                    difficulty="EASY",
                )
            )

        self._questions_by_difficulty: dict[str, list[Question]] = {
            level: [] for level in self._DIFFICULTY_ORDER
        }
        for question in self._questions:
            difficulty = getattr(question, "difficulty", "EASY")
            if difficulty not in self._questions_by_difficulty:
                difficulty = "EASY"
            self._questions_by_difficulty[difficulty].append(question)

        self._served_question_count = 0

    def get_random_question(self) -> Question:
        """
        Select a random question with progression from EASY to HARD.

        Progression is based on how many questions have been served in this run:
        early questions prefer EASY, middle questions prefer MEDIUM, and late
        questions prefer HARD. If a preferred tier is empty, the next available
        tier is selected as fallback.

        Returns:
            A randomly selected Question instance from the internal pool.
        """
        target_difficulty = self._get_target_difficulty()
        difficulty_index = self._DIFFICULTY_ORDER.index(target_difficulty)
        difficulty_search_order = (
            list(self._DIFFICULTY_ORDER[difficulty_index:])
            + list(self._DIFFICULTY_ORDER[:difficulty_index])
        )

        selected_pool = self._questions
        for difficulty in difficulty_search_order:
            pool = self._questions_by_difficulty.get(difficulty, [])
            if pool:
                selected_pool = pool
                break

        self._served_question_count += 1
        return random.choice(selected_pool)

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
        to boolean values. Difficulty is read from an optional "difficulty"
        field, or auto-assigned from EASY to HARD by list order.

        Args:
            payload: List of dictionaries containing "prompt" and "answer" keys.

        Returns:
            List of validated TrueOrFalseQuestion instances.
        """
        loaded: list[Question] = []
        total = len(payload)
        for index, raw in enumerate(payload):
            prompt = str(raw.get("prompt", "")).strip()
            if not prompt:
                continue
            answer = bool(raw.get("answer", True))
            difficulty = self._resolve_question_difficulty(raw, index, total)
            loaded.append(
                TrueOrFalseQuestion(
                    prompt=prompt,
                    answer=answer,
                    difficulty=difficulty,
                )
            )
        return loaded

    def _load_multiple_choice(self, payload: list[dict]) -> list[Question]:
        """
        Parse and instantiate MultipleChoiceQuestion objects from raw dictionaries.

        Filters out entries with empty prompts, non-list options, or fewer than 2 options.
        Invalid correct_index values are handled by the MultipleChoiceQuestion constructor.
        Difficulty is read from an optional "difficulty" field, or auto-assigned
        from EASY to HARD by list order.

        Args:
            payload: List of dictionaries containing "prompt", "options", and
                "correct_index" keys.

        Returns:
            List of validated MultipleChoiceQuestion instances.
        """
        loaded: list[Question] = []
        total = len(payload)
        for index, raw in enumerate(payload):
            prompt = str(raw.get("prompt", "")).strip()
            options = raw.get("options", [])
            correct_index = int(raw.get("correct_index", 0))
            if not prompt or not isinstance(options, list) or len(options) < 2:
                continue
            difficulty = self._resolve_question_difficulty(raw, index, total)
            try:
                loaded.append(
                    MultipleChoiceQuestion(
                        prompt=prompt,
                        options=options,
                        correct_index=correct_index,
                        difficulty=difficulty,
                    )
                )
            except ValueError:
                continue
        return loaded

    def _get_target_difficulty(self) -> str:
        """Get target difficulty tier based on how far the run has progressed."""
        total_questions = max(1, len(self._questions))
        progress = self._served_question_count / total_questions

        if progress < (1 / 3):
            return "EASY"
        if progress < (2 / 3):
            return "MEDIUM"
        return "HARD"

    def _resolve_question_difficulty(self, raw: dict, index: int, total: int) -> str:
        """Resolve raw difficulty value or auto-assign one by question position."""
        raw_difficulty = str(raw.get("difficulty", "")).strip().upper()
        if raw_difficulty in self._DIFFICULTY_ORDER:
            return raw_difficulty
        return self._difficulty_for_position(index, total)

    @staticmethod
    def _difficulty_for_position(index: int, total: int) -> str:
        """Auto-assign question difficulty from EASY to HARD using list order."""
        if total <= 0:
            return "EASY"

        progress = index / max(1, total - 1)
        if progress < (1 / 3):
            return "EASY"
        if progress < (2 / 3):
            return "MEDIUM"
        return "HARD"
