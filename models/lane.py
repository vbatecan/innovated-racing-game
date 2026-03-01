from dataclasses import dataclass


@dataclass(frozen=True)
class Lane:
    """Immutable lane segment defined by horizontal boundaries."""

    index: int
    left: int
    right: int

    @property
    def width(self) -> int:
        """Return the pixel width of the lane."""
        return max(1, self.right - self.left)
