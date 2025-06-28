"""Command line interface for tesseract."""

import argparse
import sys

from .analyzer import analyze_video
from .detector import BlackBarDetector
from .utils import print_results, save_results_json, split_video_by_cuts


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Detect cuts in video compilations by analyzing black bar changes"
    )
    parser.add_argument("video_path", help="Path to video file")
    parser.add_argument(
        "--black-threshold",
        type=int,
        default=10,
        help="Maximum pixel value considered black (default: 10)",
    )
    parser.add_argument(
        "--min-bar-size",
        type=int,
        default=10,
        help="Minimum bar size in pixels (default: 10)",
    )
    parser.add_argument(
        "--tolerance",
        type=int,
        default=5,
        help="Tolerance for bar size changes (default: 5)",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=1,
        help="Analyze every Nth frame (default: 1)",
    )
    parser.add_argument("--output-json", type=str, help="Save results to JSON file")
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed bar state information"
    )
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bar")
    parser.add_argument(
        "--split-output",
        type=str,
        help="Directory to save split video segments (enables video splitting)",
    )
    parser.add_argument(
        "--no-crop",
        action="store_true",
        help="Disable automatic cropping of black bars in split videos",
    )

    args = parser.parse_args()

    detector = BlackBarDetector(
        black_threshold=args.black_threshold,
        min_bar_size=args.min_bar_size,
        tolerance_pixels=args.tolerance,
    )

    print(f"Analyzing video: {args.video_path}")
    print(
        f"Settings: threshold={args.black_threshold}, min_size={args.min_bar_size}, "
        f"tolerance={args.tolerance}, sample_rate={args.sample_rate}"
    )
    print()

    try:
        cuts = analyze_video(
            args.video_path,
            detector,
            args.sample_rate,
            show_progress=not args.no_progress,
        )

        print_results(cuts, args.verbose)

        if args.output_json:
            save_results_json(cuts, args.output_json)
            print(f"\nResults saved to {args.output_json}")

        if args.split_output:
            print("\nSplitting video into segments...")
            try:
                import cv2

                cap = cv2.VideoCapture(args.video_path)
                fps = cap.get(cv2.CAP_PROP_FPS)
                cap.release()

                split_files = split_video_by_cuts(
                    args.video_path,
                    cuts,
                    args.split_output,
                    fps=fps,
                    show_progress=not args.no_progress,
                    crop_black_bars=not args.no_crop,
                )

                print(f"\n✅ Created {len(split_files)} video segments in " f"{args.split_output}")
                if not args.no_crop:
                    print("📐 Black bars were automatically cropped from each segment")
                if args.verbose:
                    for i, file_path in enumerate(split_files, 1):
                        print(f"  {i}: {file_path}")

            except Exception as e:
                print(f"\n❌ Error splitting video: {e}")
                return 1

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
