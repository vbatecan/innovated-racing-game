"""Question state management system.

Handles the question/answer overlay state including input lock timing,
option selection via keyboard or gesture, and answer resolution.
"""

from typing import Optional
import pygame
from core.enums import GameState, QuestionConstants


class QuestionStateManager:
    """Manages the question/answer overlay state and input handling.

    This class encapsulates all question-related state that was previously
    scattered across the main() function, providing a clean interface for
    question lifecycle management.
    """

    def __init__(self) -> None:
        """Initialize question state manager in inactive state."""
        self._active_question: Optional[object] = None
        self._selected_option: int = 0
        self._question_input_unlock_at: int = 0
        self._heart_question_active: bool = False

    @property
    def active_question(self) -> Optional[object]:
        """Get the currently active question, if any."""
        return self._active_question

    @active_question.setter
    def active_question(self, question: Optional[object]) -> None:
        """Set the active question and reset selection."""
        self._active_question = question
        self._selected_option = 0
        if question is not None:
            self._question_input_unlock_at = (
                pygame.time.get_ticks() + QuestionConstants.INPUT_LOCK_MS
            )

    @property
    def selected_option(self) -> int:
        """Get the currently selected option index."""
        return self._selected_option

    @property
    def is_input_locked(self) -> bool:
        """Check if question input is currently locked."""
        return pygame.time.get_ticks() < self._question_input_unlock_at

    @property
    def is_input_ready(self) -> bool:
        """Check if question input is unlocked and ready."""
        return not self.is_input_locked

    @property
    def is_heart_question(self) -> bool:
        """Check if this is a heart bonus question."""
        return self._heart_question_active

    def set_heart_question(self, is_heart: bool) -> None:
        """Mark the current question as a heart bonus question."""
        self._heart_question_active = is_heart

    def clear(self) -> None:
        """Clear the active question and reset state."""
        self._active_question = None
        self._selected_option = 0
        self._question_input_unlock_at = 0
        self._heart_question_active = False

    def move_selection_up(self) -> None:
        """Move selection up (decrement) if input is ready."""
        if self.is_input_ready and self._active_question is not None:
            self._selected_option = max(0, self._selected_option - 1)

    def move_selection_down(self) -> None:
        """Move selection down (increment) if input is ready."""
        if self.is_input_ready and self._active_question is not None:
            self._selected_option = min(
                self._active_question.answer_count - 1,
                self._selected_option + 1
            )

    def select_current_option(self) -> Optional[int]:
        """Get the current selection if input is ready."""
        if self.is_input_ready and self._active_question is not None:
            return self._selected_option
        return None

    def check_key_selection(self, event_key: int, key_mapper: object) -> Optional[int]:
        """Check if a key press corresponds to a valid option selection.

        Args:
            event_key: The Pygame key constant from a KEYDOWN event.
            key_mapper: An object with get_option_index method.
        """
        if not self.is_input_ready or self._active_question is None:
            return None

        selected = key_mapper.get_option_index(event_key)
        if selected is not None and selected < self._active_question.answer_count:
            return selected
        return None
