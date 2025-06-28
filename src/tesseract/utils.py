"""Utility functions."""

import json
import subprocess
import time
from pathlib import Path
from types import TracebackType
from typing import Any, List, Optional, Tuple, Type

import cv2
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from .models import BarState, CutEvent


class VideoAnalysisProgress:
    """Progress tracker for video analysis with TUI progress bar."""

    def __init__(self, total_frames: int, show_progress: bool = True) -> None:
        """Initialize progress tracker.

        Args:
            total_frames: Total number of frames to process
            show_progress: Whether to show the progress bar
        """
        self.total_frames = total_frames
        self.show_progress = show_progress
        self.start_time = time.time()
        self.console = Console()
        self.progress: Optional[Progress] = None
        self.task_id: Optional[TaskID] = None

        if self.show_progress:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=40),
                TaskProgressColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                TextColumn("•"),
                TimeRemainingColumn(),
                console=self.console,
                expand=True,
            )

    def start(self, description: str = "Analyzing video") -> None:
        """Start the progress tracking."""
        if self.progress:
            self.progress.start()
            self.task_id = self.progress.add_task(description, total=self.total_frames)

    def update(self, frame_number: int) -> None:
        """Update progress.

        Args:
            frame_number: Current frame number being processed
        """
        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, completed=frame_number)

    def finish(self) -> None:
        """Finish progress tracking."""
        if self.progress:
            self.progress.stop()

        if self.show_progress:
            elapsed_time = time.time() - self.start_time
            self.console.print(
                f"\n[green]✓[/green] Analysis completed in {elapsed_time:.2f} seconds"
            )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Context manager exit."""
        self.finish()


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def print_results(cuts: List[CutEvent], verbose: bool = False) -> None:
    """Print analysis results."""
    print(f"Detected {len(cuts)} potential cuts:")
    print("-" * 80)

    for i, cut in enumerate(cuts, 1):
        print(f"Cut {i}: {format_timestamp(cut.timestamp)} (frame {cut.frame_number})")

        if verbose:
            before = cut.before_state
            after = cut.after_state
            print(
                f"  Before: L={before.left_width}, R={before.right_width}, "
                f"T={before.top_height}, B={before.bottom_height}"
            )
            print(
                f"  After:  L={after.left_width}, R={after.right_width}, "
                f"T={after.top_height}, B={after.bottom_height}"
            )
            print()


def save_results_json(cuts: List[CutEvent], output_path: str) -> None:
    """Save results to JSON file."""
    data: list[dict[str, Any]] = []
    for cut in cuts:
        data.append(
            {
                "timestamp": cut.timestamp,
                "formatted_time": format_timestamp(cut.timestamp),
                "frame_number": cut.frame_number,
                "before_state": {
                    "left_width": cut.before_state.left_width,
                    "right_width": cut.before_state.right_width,
                    "top_height": cut.before_state.top_height,
                    "bottom_height": cut.before_state.bottom_height,
                },
                "after_state": {
                    "left_width": cut.after_state.left_width,
                    "right_width": cut.after_state.right_width,
                    "top_height": cut.after_state.top_height,
                    "bottom_height": cut.after_state.bottom_height,
                },
            }
        )

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)


def split_video_by_cuts(
    video_path: str,
    cuts: List[CutEvent],
    output_dir: str,
    fps: Optional[float] = None,
    show_progress: bool = True,
    crop_black_bars: bool = True,
) -> List[str]:
    """
    Split video into segments based on detected cuts.

    Args:
        video_path: Path to the original video file
        cuts: List of detected cut events
        output_dir: Directory to save split video files
        fps: Frame rate of the video (auto-detected if None)
        show_progress: Whether to show progress bar
        crop_black_bars: Whether to crop detected black bars from output videos

    Returns:
        List of paths to created video segments
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get video properties
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    if fps is None:
        fps = cap.get(cv2.CAP_PROP_FPS)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Calculate segment boundaries with associated bar states
    segments: List[Tuple[int, int, str, Optional[BarState]]] = []
    video_name = Path(video_path).stem

    # Add segment from start to first cut (if any)
    if cuts:
        # Use the "before_state" of the first cut for the initial segment
        segments.append((0, cuts[0].frame_number, "segment_01", cuts[0].before_state))

        # Add segments between cuts
        for i in range(len(cuts) - 1):
            start_frame = cuts[i].frame_number
            end_frame = cuts[i + 1].frame_number
            segment_name = f"segment_{i + 2:02d}"
            # Use the "after_state" of the cut that starts this segment
            segments.append((start_frame, end_frame, segment_name, cuts[i].after_state))

        # Add segment from last cut to end
        last_cut_frame = cuts[-1].frame_number
        if last_cut_frame < total_frames:
            # Use the "after_state" of the last cut
            segments.append(
                (
                    last_cut_frame,
                    total_frames,
                    f"segment_{len(cuts) + 1:02d}",
                    cuts[-1].after_state,
                )
            )
    else:
        # No cuts found, copy entire video without cropping
        segments.append((0, total_frames, "segment_01", None))

    created_files: List[str] = []

    with VideoAnalysisProgress(len(segments), show_progress) as progress:
        progress.start("Splitting video into segments")

        for i, (start_frame, end_frame, segment_name, bar_state) in enumerate(segments):
            # Create output filename
            output_file = output_path / f"{video_name}_{segment_name}.mp4"
            created_files.append(str(output_file))

            # Use ffmpeg for better performance and quality
            if _has_ffmpeg():
                # Use frame-accurate splitting for precise cuts with optional cropping
                _split_with_ffmpeg_frame_accurate(
                    video_path,
                    str(output_file),
                    start_frame,
                    end_frame,
                    fps,
                    bar_state if crop_black_bars else None,
                    width,
                    height,
                )
            else:
                # Fallback to OpenCV (no cropping support in fallback)
                _split_with_opencv(
                    cap,
                    str(output_file),
                    start_frame,
                    end_frame,
                    fourcc,
                    fps,
                    width,
                    height,
                )

            progress.update(i + 1)

    cap.release()
    return created_files


def has_ffmpeg() -> bool:
    """Check if ffmpeg is available."""
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=False)
        return result.returncode == 0
    except FileNotFoundError:
        return False


# Keep the private version for backward compatibility
_has_ffmpeg = has_ffmpeg


def _split_with_ffmpeg_frame_accurate(
    input_path: str,
    output_path: str,
    start_frame: int,
    end_frame: int,
    fps: float,
    bar_state: Optional[BarState] = None,
    width: int = 0,
    height: int = 0,
) -> None:
    """Split video using ffmpeg with frame-accurate timing and proper audio sync."""
    # Calculate precise timestamps
    start_time = start_frame / fps
    duration = (end_frame - start_frame) / fps

    cmd = [
        "ffmpeg",
        "-ss",
        str(start_time),  # Seek to start time BEFORE input for accuracy
        "-i",
        input_path,
        "-t",
        str(duration),  # Duration to extract
    ]

    # Add cropping filter if black bars are detected
    if bar_state is not None and width > 0 and height > 0:
        crop_filter = _calculate_crop_filter(bar_state, width, height)
        if crop_filter:
            cmd.extend(["-vf", crop_filter])

    cmd.extend(
        [
            "-c:v",
            "libx264",  # Re-encode video for frame accuracy
            "-c:a",
            "aac",  # Re-encode audio
            "-preset",
            "medium",  # Balance between speed and quality
            "-crf",
            "18",  # High quality
            "-avoid_negative_ts",
            "make_zero",  # Handle timestamp issues
            "-fflags",
            "+genpts",  # Generate presentation timestamps
            "-y",  # Overwrite output file
            output_path,
        ]
    )

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")


def _split_with_opencv(
    cap: cv2.VideoCapture,
    output_path: str,
    start_frame: int,
    end_frame: int,
    fourcc: int,
    fps: float,
    width: int,
    height: int,
) -> None:
    """Split video using OpenCV (fallback method)."""
    # Create video writer
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Seek to start frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    # Write frames
    for _ in range(start_frame, end_frame):
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)

    out.release()


def _calculate_crop_filter(bar_state: BarState, width: int, height: int) -> str:
    """Calculate FFmpeg crop filter string from black bar state.

    Args:
        bar_state: The black bar state containing bar dimensions
        width: Original video width
        height: Original video height

    Returns:
        FFmpeg crop filter string, or empty string if no cropping needed
    """
    # Calculate cropped dimensions
    crop_width = width - bar_state.left_width - bar_state.right_width
    crop_height = height - bar_state.top_height - bar_state.bottom_height

    # Check if there are any black bars to crop
    has_bars = (
        bar_state.left_width > 0
        or bar_state.right_width > 0
        or bar_state.top_height > 0
        or bar_state.bottom_height > 0
    )

    # Only crop if there are actual black bars and the result would be reasonable
    if (
        has_bars and crop_width > 0 and crop_height > 0 and crop_width >= 64 and crop_height >= 64
    ):  # Minimum reasonable size

        # FFmpeg crop filter: crop=width:height:x:y
        return f"crop={crop_width}:{crop_height}:{bar_state.left_width}:{bar_state.top_height}"

    return ""
