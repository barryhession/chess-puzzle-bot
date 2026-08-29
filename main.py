"""
main.py
-------
Entry point for the chess puzzle Instagram bot.

Usage:
    python main.py              # post solution comment on last puzzle, then post new puzzle
    python main.py --dry-run    # stop before uploading or posting
    python main.py --puzzle-id <ID>  # force a specific Lichess puzzle ID
"""

import argparse
import csv
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env before importing src modules (they read os.getenv at import time)
load_dotenv()

from src.puzzle_picker import pick_puzzle, mark_used, get_pending_solution, mark_solution_posted
from src.board_renderer import render_puzzle_image
from src.caption import build_caption
from src.image_host import upload_image
from src.solution import format_solution_comment
from src import instagram


OUTPUT_DIR = Path(__file__).parent / "output"


def _find_puzzle_by_id(puzzle_id: str) -> dict:
    """Load a specific puzzle by ID from the CSV (linear scan, for debugging)."""
    from src.puzzle_picker import _find_csv

    csv_path = _find_csv()
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["PuzzleId"] == puzzle_id:
                return dict(row)
    raise ValueError(f"Puzzle ID '{puzzle_id}' not found in CSV.")


def post_solution_comment(dry_run: bool = False) -> None:
    """Check for a pending solution comment and post it if one is due."""
    pending = get_pending_solution()
    if not pending:
        print("[solution] No pending solution comments.")
        return

    puzzle_id = pending["puzzle_id"]
    media_id  = pending["media_id"]
    print(f"[solution] Posting solution for puzzle {puzzle_id} on media {media_id}...")

    # Look up the full puzzle data from the CSV for move formatting
    try:
        full_puzzle = _find_puzzle_by_id(puzzle_id)
    except ValueError:
        print(f"[solution] Puzzle {puzzle_id} not found in CSV — skipping.")
        mark_solution_posted(puzzle_id)
        return

    comment = format_solution_comment(puzzle=pending, full_puzzle_row=full_puzzle)
    print("Solution comment preview:\n" + "-" * 40)
    print(comment)
    print("-" * 40)

    if dry_run:
        print("[solution] Dry-run — skipping comment post.")
        return

    try:
        instagram.post_comment(media_id, comment)
        mark_solution_posted(puzzle_id)
        print(f"[solution] Solution comment posted and recorded.")
    except Exception as e:
        print(f"[solution] Failed to post comment: {e}")
        # Don't crash the whole run — new puzzle post should still proceed


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

    # 0. Post solution comment on the previous puzzle
    print("=== Step 0: Solution comment on previous puzzle ===")
    post_solution_comment(dry_run=args.dry_run)

    # 1. Pick puzzle
    print("\n=== Step 1: Picking puzzle ===")
    if args.puzzle_id:
        puzzle = _find_puzzle_by_id(args.puzzle_id)
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

    # 6. Mark puzzle as used (with media_id for solution comment later)
    print("\n=== Step 6: Recording puzzle as used ===")
    mark_used(puzzle["PuzzleId"], media_id=media_id)
    print(f"Puzzle {puzzle['PuzzleId']} marked as used (media_id: {media_id}).")

    print(f"\nDone! Post published. Media ID: {media_id}")


if __name__ == "__main__":
    main()
