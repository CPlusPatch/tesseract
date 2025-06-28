"""Video analysis functionality."""

from typing import List

import cv2

from .detector import BlackBarDetector
from .models import CutEvent
from .utils import VideoAnalysisProgress


def analyze_video(
    video_path: str,
    detector: BlackBarDetector,
    sample_rate: int = 1,
    show_progress: bool = True,
) -> List[CutEvent]:
    """
    Analyze video for black bar changes indicating cuts.

    Args:
        video_path: Path to video file
        detector: BlackBarDetector instance
        sample_rate: Analyze every Nth frame (1 = every frame)
        show_progress: Whether to show progress bar

    Returns:
        List of detected cut events
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    cuts: list[CutEvent] = []
    previous_state = None
    frame_number = 0

    with VideoAnalysisProgress(total_frames, show_progress) as progress:
        progress.start("Analyzing video frames")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_number % sample_rate == 0:
                current_state = detector.get_frame_bar_state(frame)

                if previous_state is not None:
                    if detector.states_significantly_different(previous_state, current_state):
                        timestamp = frame_number / fps
                        cuts.append(
                            CutEvent(
                                timestamp=timestamp,
                                frame_number=frame_number,
                                before_state=previous_state,
                                after_state=current_state,
                            )
                        )

                previous_state = current_state

            frame_number += 1

            # Update progress every 100 frames
            if frame_number % 100 == 0:
                progress.update(frame_number)

    cap.release()
    return cuts


def analyze_and_split_video(
    video_path: str,
    detector: BlackBarDetector,
    output_dir: str,
    sample_rate: int = 1,
    show_progress: bool = True,
) -> tuple[List[CutEvent], List[str]]:
    """
    Analyze video for cuts and split into segments.

    Args:
        video_path: Path to video file
        detector: BlackBarDetector instance
        output_dir: Directory to save split video files
        sample_rate: Analyze every Nth frame (1 = every frame)
        show_progress: Whether to show progress bar

    Returns:
        Tuple of (detected cuts, list of created segment files)
    """
    from .utils import split_video_by_cuts

    # First analyze the video
    cuts = analyze_video(video_path, detector, sample_rate, show_progress)

    # Then split the video
    if cuts or True:  # Always split even if no cuts found (creates single segment)
        import cv2

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()

        split_files = split_video_by_cuts(
            video_path, cuts, output_dir, fps=fps, show_progress=show_progress
        )
    else:
        split_files = []

    return cuts, split_files
