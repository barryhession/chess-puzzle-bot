"""
create_reel.py
--------------
Render a chess puzzle as an Instagram Reel (MP4).

Usage:
    python create_reel.py                    # random puzzle
    python create_reel.py --puzzle-id abc123 # specific puzzle
"""

import argparse
import csv
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from src.puzzle_picker import pick_puzzle, _find_csv
from src.reel_renderer import render_reel

OUTPUT_DIR = Path(__file__).parent / "output"


def _find_puzzle_by_id(puzzle_id: str) -> dict:
    csv_path = _find_csv()
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["PuzzleId"] == puzzle_id:
                return dict(row)
    raise ValueError(f"Puzzle ID '{puzzle_id}' not found in CSV.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a chess puzzle Reel.")
    parser.add_argument("--puzzle-id", default="",
                        help="Force a specific Lichess puzzle ID.")
    args = parser.parse_args()

    # Pick puzzle
    if args.puzzle_id:
        puzzle = _find_puzzle_by_id(args.puzzle_id)
        print(f"Using puzzle: {puzzle['PuzzleId']}")
    else:
        puzzle = pick_puzzle()
        print(f"Selected puzzle: {puzzle['PuzzleId']}  "
              f"(rating {puzzle['Rating']}, themes: {puzzle['Themes']})")

    # Render reel
    output_path = OUTPUT_DIR / f"{puzzle['PuzzleId']}_reel.mp4"
    print(f"Rendering reel -> {output_path}")
    print("This may take 20-40 seconds...")

    render_reel(puzzle, output_path)

    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"Done! Reel saved -> {output_path}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
