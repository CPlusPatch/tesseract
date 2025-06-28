"""Tests for tesseract models."""

from tesseract.models import BarState, CutEvent


def test_bar_state_equality():
    """Test BarState equality comparison."""
    state1 = BarState(10, 15, 5, 8)
    state2 = BarState(10, 15, 5, 8)
    state3 = BarState(10, 15, 5, 9)

    assert state1 == state2
    assert state1 != state3
    assert state1 != "not a bar state"


def test_cut_event_creation():
    """Test CutEvent creation."""
    before_state = BarState(10, 15, 5, 8)
    after_state = BarState(12, 18, 3, 6)

    cut = CutEvent(
        timestamp=123.45,
        frame_number=3000,
        before_state=before_state,
        after_state=after_state,
    )

    assert cut.timestamp == 123.45
    assert cut.frame_number == 3000
    assert cut.before_state == before_state
    assert cut.after_state == after_state
