"""Tesseract: Video analysis tool for detecting cuts by analyzing black bar changes."""

from .analyzer import analyze_and_split_video, analyze_video
from .detector import BlackBarDetector
from .models import BarState, CutEvent
from .utils import (
    VideoAnalysisProgress,
    format_timestamp,
    has_ffmpeg,
    split_video_by_cuts,
)

__version__ = "0.1.0"
__all__ = [
    "BlackBarDetector",
    "BarState",
    "CutEvent",
    "analyze_video",
    "analyze_and_split_video",
    "format_timestamp",
    "has_ffmpeg",
    "VideoAnalysisProgress",
    "split_video_by_cuts",
]
