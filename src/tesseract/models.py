"""Data models for tesseract."""

from dataclasses import dataclass


@dataclass
class BarState:
    """Represents the state of black bars in a frame."""

    left_width: int
    right_width: int
    top_height: int
    bottom_height: int

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BarState):
            return NotImplemented
        return (
            self.left_width == other.left_width
            and self.right_width == other.right_width
            and self.top_height == other.top_height
            and self.bottom_height == other.bottom_height
        )


@dataclass
class CutEvent:
    """Represents a detected cut event."""

    timestamp: float
    frame_number: int
    before_state: BarState
    after_state: BarState
