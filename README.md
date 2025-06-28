# Tesseract

A video analysis tool for detecting cuts by analyzing black bar changes in videos.

## Requirements

- Python 3.12 or higher
- OpenCV
- NumPy

## Installation

```bash
pip install -e .

# Or, with Nix:
nix run github:CPlusPatch/tesseract -h
```

## Usage

### Command Line

```bash
# Basic usage with progress bar
tesseract path/to/video.mp4 --verbose --output-json results.json

# Disable progress bar for scripting
tesseract path/to/video.mp4 --no-progress --output-json results.json

# Split video into segments at detected cuts
tesseract path/to/video.mp4 --split-output ./output_segments --verbose
```

### Python API

```python
from tesseract import (
    BlackBarDetector, 
    analyze_video, 
    analyze_and_split_video,
    split_video_by_cuts,
    VideoAnalysisProgress
)

# Basic usage with automatic progress bar
detector = BlackBarDetector(black_threshold=10, min_bar_size=10)
cuts = analyze_video("video.mp4", detector)

# Disable progress bar
cuts = analyze_video("video.mp4", detector, show_progress=False)

# Analyze and split video in one step
cuts, segment_files = analyze_and_split_video(
    "video.mp4", detector, output_dir="./segments"
)

# Split existing cuts into video segments
segment_files = split_video_by_cuts(
    "video.mp4", cuts, output_dir="./segments"
)

# Manual progress bar usage
with VideoAnalysisProgress(total_frames, show_progress=True) as progress:
    progress.start("Custom analysis")
    # ... your analysis code ...
    progress.update(current_frame)

for cut in cuts:
    print(f"Cut at {cut.timestamp}s (frame {cut.frame_number})")

for segment in segment_files:
    print(f"Created segment: {segment}")
```

## Options

- `--black-threshold`: Maximum pixel value considered black (default: 30)
- `--min-bar-size`: Minimum bar size in pixels (default: 10)
- `--tolerance`: Tolerance for bar size changes (default: 5)
- `--sample-rate`: Analyze every Nth frame (default: 1)
- `--output-json`: Save results to JSON file
- `--verbose`: Show detailed bar state information
- `--no-progress`: Disable progress bar (useful for scripting)
- `--split-output`: Directory to save split video segments (enables automatic video splitting)

## Development

```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run all formatting and linting checks
python dev.py

# Fix formatting issues automatically
python dev.py --fix
```

### Pre-commit Workflow

Before committing, run:
```bash
python dev.py --fix  # Fix formatting
python dev.py        # Verify all checks pass
```
