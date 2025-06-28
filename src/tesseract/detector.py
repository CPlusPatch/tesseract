"""Black bar detection functionality."""

from typing import Tuple

import cv2
import numpy as np

from .models import BarState


class BlackBarDetector:
    """Detector for black bars in video frames."""

    def __init__(
        self,
        black_threshold: int = 10,
        min_bar_size: int = 10,
        tolerance_pixels: int = 5,
    ) -> None:
        """
        Initialize black bar detector.

        Args:
            black_threshold: Maximum pixel value considered "black"
            min_bar_size: Minimum size in pixels for a bar to be considered significant
            tolerance_pixels: Tolerance for bar size changes to avoid noise
        """
        self.black_threshold = black_threshold
        self.min_bar_size = min_bar_size
        self.tolerance_pixels = tolerance_pixels

    def detect_vertical_bars(self, frame: np.ndarray) -> Tuple[int, int]:
        """
        Detect left and right vertical black bars.

        Returns:
            Tuple of (left_bar_width, right_bar_width)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        width = gray.shape[1]

        # Detect left bar
        left_width = 0
        for col in range(width):
            column_mean = np.mean(gray[:, col])
            if column_mean > self.black_threshold:
                break
            left_width = col + 1

        # Detect right bar
        right_width = 0
        for col in range(width - 1, -1, -1):
            column_mean = np.mean(gray[:, col])
            if column_mean > self.black_threshold:
                break
            right_width = width - col

        # Apply minimum size filter
        left_width = left_width if left_width >= self.min_bar_size else 0
        right_width = right_width if right_width >= self.min_bar_size else 0

        return left_width, right_width

    def detect_horizontal_bars(self, frame: np.ndarray) -> Tuple[int, int]:
        """
        Detect top and bottom horizontal black bars.

        Returns:
            Tuple of (top_bar_height, bottom_bar_height)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        height = gray.shape[0]

        # Detect top bar
        top_height = 0
        for row in range(height):
            row_mean = np.mean(gray[row, :])
            if row_mean > self.black_threshold:
                break
            top_height = row + 1

        # Detect bottom bar
        bottom_height = 0
        for row in range(height - 1, -1, -1):
            row_mean = np.mean(gray[row, :])
            if row_mean > self.black_threshold:
                break
            bottom_height = height - row

        # Apply minimum size filter
        top_height = top_height if top_height >= self.min_bar_size else 0
        bottom_height = bottom_height if bottom_height >= self.min_bar_size else 0

        return top_height, bottom_height

    def get_frame_bar_state(self, frame: np.ndarray) -> BarState:
        """Get the complete bar state for a frame."""
        left_width, right_width = self.detect_vertical_bars(frame)
        top_height, bottom_height = self.detect_horizontal_bars(frame)

        return BarState(left_width, right_width, top_height, bottom_height)

    def states_significantly_different(self, state1: BarState, state2: BarState) -> bool:
        """Check if two bar states are significantly different."""
        return (
            abs(state1.left_width - state2.left_width) > self.tolerance_pixels
            or abs(state1.right_width - state2.right_width) > self.tolerance_pixels
            or abs(state1.top_height - state2.top_height) > self.tolerance_pixels
            or abs(state1.bottom_height - state2.bottom_height) > self.tolerance_pixels
        )
