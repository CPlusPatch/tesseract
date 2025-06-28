#!/usr/bin/env python3
"""Development utility script for formatting and linting."""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"🔍 {description}...")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False


def main():
    """Run all development checks."""
    project_root = Path(__file__).parent
    src_dir = project_root / "src"
    tests_dir = project_root / "tests"

    # Change to project directory
    original_cwd = Path.cwd()
    try:
        os.chdir(project_root)

        all_passed = True

        # Run Black formatter
        if "--fix" in sys.argv:
            all_passed &= run_command(
                ["black", str(src_dir), str(tests_dir)], "Black formatting (fixing)"
            )
        else:
            all_passed &= run_command(
                ["black", "--check", str(src_dir), str(tests_dir)],
                "Black formatting check",
            )

        # Run isort
        if "--fix" in sys.argv:
            all_passed &= run_command(
                ["isort", str(src_dir), str(tests_dir)], "Import sorting (fixing)"
            )
        else:
            all_passed &= run_command(
                ["isort", "--check-only", str(src_dir), str(tests_dir)],
                "Import sorting check",
            )

        # Run flake8
        all_passed &= run_command(
            [
                "flake8",
                str(src_dir),
                str(tests_dir),
                "--max-line-length=100",
                "--extend-ignore=E203,W503",
            ],
            "Flake8 linting",
        )

        # Run tests
        all_passed &= run_command(
            ["python", "-m", "pytest", str(tests_dir), "-v"], "Tests"
        )

        if all_passed:
            print("\n🎉 All checks passed!")
            return 0
        else:
            print("\n💥 Some checks failed!")
            return 1

    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print("Development utility script")
        print("Usage:")
        print("  python dev.py        # Run all checks")
        print("  python dev.py --fix  # Run checks and fix formatting issues")
        sys.exit(0)

    sys.exit(main())
