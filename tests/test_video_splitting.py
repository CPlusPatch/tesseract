"""Tests for video splitting functionality."""

from tesseract.utils import has_ffmpeg


def test_ffmpeg_detection():
    """Test FFmpeg detection functionality."""
    # The actual result depends on system configuration
    # Just test that it doesn't crash and returns a boolean
    result = has_ffmpeg()
    assert isinstance(result, bool)


def test_split_video_by_cuts_import():
    """Test that the video splitting function can be imported."""
    from tesseract.utils import split_video_by_cuts

    # Just test that the function exists and is callable
    assert callable(split_video_by_cuts)
