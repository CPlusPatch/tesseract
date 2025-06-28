"""Tests for utility functions."""

from tesseract.utils import format_timestamp


def test_format_timestamp():
    """Test timestamp formatting."""
    # Test simple cases
    assert format_timestamp(0) == "00:00:00.000"
    assert format_timestamp(61.5) == "00:01:01.500"
    assert format_timestamp(3661.123) == "01:01:01.123"

    # Test edge cases
    assert format_timestamp(59.999) == "00:00:59.999"
    assert format_timestamp(3600) == "01:00:00.000"
