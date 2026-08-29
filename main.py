"""
main.py
-------
Entry point for the chess puzzle Instagram bot.

Usage:
    python main.py              # pick puzzle, render, upload, post, record
    python main.py --dry-run    # stop before posting (saves image locally only)
    python main.py --puzzle-id <ID>  # force a specific Lichess puzzle ID
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env before importing src modules (they read os.getenv at import time)
load_dotenv()

from src.puzzle_picker import pick_puzzle, mark_used
from src.board_renderer import render_puzzle_image
from src.caption import build_caption
from src.image_host import upload_image
from src import instagram


OUTPUT_DIR = Path(__file__).parent / "output"


def _force_puzzle(puzzle_id: str) -> dict:
    """Load a specific puzzle by ID from the CSV (linear scan, for debugging)."""
    import csv
    from src.puzzle_picker import _find_csv  # noqa: PLC0415

    csv_path = _find_csv()
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["PuzzleId"] == puzzle_id:
                return dict(row)
    raise ValueError(f"Puzzle ID '{puzzle_id}' not found in CSV.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Post a chess puzzle to Instagram.")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Render and save the image but do NOT upload or post.",
    )
    parser.add_argument(
        "--puzzle-id", default="",
        help="Force a specific Lichess puzzle ID (overrides random selection).",
    )
    args = parser.parse_args()

    # 1. Pick puzzle
    print("=== Step 1: Picking puzzle ===")
    if args.puzzle_id:
        puzzle = _force_puzzle(args.puzzle_id)
        print(f"Using forced puzzle: {puzzle['PuzzleId']}")
    else:
        puzzle = pick_puzzle()
        print(f"Selected puzzle: {puzzle['PuzzleId']}  "
              f"(rating {puzzle['Rating']}, themes: {puzzle['Themes']})")

    # 2. Render image
    print("\n=== Step 2: Rendering board image ===")
    output_path = OUTPUT_DIR / f"{puzzle['PuzzleId']}.png"
    render_puzzle_image(puzzle, output_path)
    print(f"Image saved -> {output_path}")

    if args.dry_run:
        print("\n[dry-run] Stopping before upload/post. Image is at:", output_path)
        sys.exit(0)

    # 3. Build caption
    print("\n=== Step 3: Building caption ===")
    caption = build_caption(puzzle)
    print("Caption preview:\n" + "-" * 40)
    print(caption)
    print("-" * 40)

    # 4. Upload image
    print("\n=== Step 4: Uploading image ===")
    image_url = upload_image(output_path)

    # 5. Publish to Instagram
    print("\n=== Step 5: Publishing to Instagram ===")
    media_id = instagram.publish(image_url, caption)

    # 6. Mark puzzle as used
    print("\n=== Step 6: Recording puzzle as used ===")
    mark_used(puzzle["PuzzleId"])
    print(f"Puzzle {puzzle['PuzzleId']} marked as used.")

    print(f"\nDone! Post published. Media ID: {media_id}")


if __name__ == "__main__":
    main()
