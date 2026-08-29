"""
puzzle_of_week.py
-----------------
Reposts the most-engaged puzzle from the past 7 days every Sunday.

Usage:
    python puzzle_of_week.py
    python puzzle_of_week.py --dry-run

Engagement = likes + comments (queried via Instagram Graph API).
"""

import argparse
import csv
import random
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from src.board_renderer import render_puzzle_image
from src.image_host import upload_image
from src import instagram

OUTPUT_DIR = Path(__file__).parent / "output"
_DB_PATH = Path(__file__).parent / "used_puzzles.db"
_CSV_PATH = Path(__file__).parent / "puzzles" / "lichess_db_puzzle.csv"


def _find_puzzle_by_id(puzzle_id: str) -> dict:
    """Load a specific puzzle by ID from the CSV."""
    with open(_CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["PuzzleId"] == puzzle_id:
                return dict(row)
    raise ValueError(f"Puzzle ID '{puzzle_id}' not found in CSV.")


def get_most_engaged_puzzle(days: int = 7) -> dict | None:
    """
    Query Instagram API for engagement on recent posts.
    Returns the puzzle with highest likes + comments.
    """
    if not _DB_PATH.exists():
        print("[potw] No database found.")
        return None

    conn = sqlite3.connect(str(_DB_PATH))
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    rows = conn.execute(
        "SELECT puzzle_id, media_id, rating FROM used_puzzles "
        "WHERE used_at >= ? AND media_id IS NOT NULL AND media_id != '' "
        "ORDER BY used_at DESC",
        (cutoff,),
    ).fetchall()
    conn.close()

    if not rows:
        print("[potw] No recent puzzles found.")
        return None

    print(f"[potw] Checking engagement for {len(rows)} recent puzzles...")

    best = None
    best_score = -1

    for puzzle_id, media_id, rating in rows:
        try:
            # Fetch engagement data from Instagram API
            from src.instagram import _token, _BASE, _TIMEOUT
            import requests

            resp = requests.get(
                f"{_BASE}/{media_id}",
                params={
                    "fields": "like_count,comments_count",
                    "access_token": _token(),
                },
                timeout=_TIMEOUT,
            )
            data = resp.json()
            likes = data.get("like_count", 0)
            comments = data.get("comments_count", 0)
            score = likes + comments

            print(f"[potw]   {puzzle_id}: {likes} likes + {comments} comments = {score}")

            if score > best_score:
                best_score = score
                best = {"puzzle_id": puzzle_id, "media_id": media_id,
                        "rating": rating, "likes": likes, "comments": comments,
                        "score": score}

        except Exception as e:
            print(f"[potw]   {puzzle_id}: Error fetching engagement: {e}")

    if best:
        print(f"[potw] Winner: {best['puzzle_id']} (score: {best['score']})")
    return best


def render_weekly_graphic(puzzle: dict, output_path: Path) -> Path:
    """
    Render a special 'Puzzle of the Week' graphic.
    Same 1080x1350 format, but with gold trophy header.
    """
    from PIL import Image, ImageDraw, ImageFont

    # Use the standard board renderer for the chess position
    render_puzzle_image(puzzle, output_path)

    # Overlay a gold banner at the top
    canvas = Image.open(str(output_path))
    draw = ImageDraw.Draw(canvas)

    # Gold banner background
    draw.rectangle([(0, 0), (1080, 80)], fill=(201, 160, 56))

    # Trophy text
    try:
        import sys
        if sys.platform == "win32":
            font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 40)
        else:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
    except Exception:
        font = ImageFont.load_default()

    draw.text(
        (540, 40),
        "PUZZLE OF THE WEEK",
        fill=(18, 18, 18),
        font=font,
        anchor="mm",
    )

    canvas.save(str(output_path), "PNG")
    print(f"[potw] Weekly graphic saved: {output_path}")
    return output_path


def build_weekly_caption(puzzle: dict, engagement: dict) -> str:
    """Generate caption for Puzzle of the Week."""
    rating = puzzle.get("Rating", "1500")
    themes = puzzle.get("Themes", "").split()
    puzzle_id = puzzle.get("PuzzleId", "")

    theme_labels = []
    theme_map = {
        "mateIn1": "Mate in 1", "mateIn2": "Mate in 2", "mateIn3": "Mate in 3",
        "fork": "Fork", "pin": "Pin", "skewer": "Skewer",
        "sacrifice": "Sacrifice", "endgame": "Endgame",
    }
    for t in themes:
        if t in theme_map:
            theme_labels.append(theme_map[t])
    theme_str = " · ".join(theme_labels[:2]) if theme_labels else "Tactical puzzle"

    hashtags = [
        "#chess", "#puzzleoftheweek", "#chessmaster", "#lichess",
        "#chesspuzzle", "#chessdaily", "#chesslife", "#dailypuzzle",
    ]

    lines = [
        "Puzzle of the Week",
        "",
        f"The most-engaged puzzle from this week.",
        f"{engagement['likes']} likes + {engagement['comments']} comments",
        "",
        f"Rating: {rating} | {theme_str}",
        f"Can you solve it?",
        "",
        f"Solution revealed in the comments soon.",
        f"🔗 Solve it: https://lichess.org/training/{puzzle_id}",
        "",
        " ".join(hashtags),
    ]
    return "\n".join(lines)


def post_puzzle_of_week(dry_run: bool = False) -> None:
    """Full flow: get most engaged -> render -> upload -> post -> Stories."""
    print("=== Puzzle of the Week ===\n")

    # 1. Find most engaged puzzle
    engagement = get_most_engaged_puzzle()
    if not engagement:
        print("[potw] No engagement data found. Skipping.")
        return

    # 2. Load full puzzle data from CSV
    try:
        puzzle = _find_puzzle_by_id(engagement["puzzle_id"])
    except ValueError as e:
        print(f"[potw] Error: {e}")
        return

    print(f"\n[potw] Puzzle: {puzzle['PuzzleId']} (Rating: {puzzle['Rating']})")

    # 3. Render graphic
    output_path = OUTPUT_DIR / f"weekly_{puzzle['PuzzleId']}.png"
    render_weekly_graphic(puzzle, output_path)

    if args.dry_run:
        print(f"\n[dry-run] Stopping. Graphic at: {output_path}")
        return

    # 4. Build caption
    caption = build_weekly_caption(puzzle, engagement)
    print("\nCaption preview:")
    print("-" * 40)
    print(caption)
    print("-" * 40)

    # 5. Upload
    print("\n=== Uploading ===")
    image_url = upload_image(output_path)

    # 6. Publish
    print("\n=== Publishing to Instagram ===")
    media_id = instagram.publish(image_url, caption)
    print(f"Published! Media ID: {media_id}")

    # 7. Post engagement comment
    print("\n=== Posting engagement comment ===")
    try:
        instagram.post_comment(media_id, "💡 Drop your first move in the comments!")
    except Exception as e:
        print(f"Warning: Failed to post engagement comment: {e}")

    # 8. Post to Stories
    print("\n=== Posting to Stories ===")
    try:
        instagram.post_stories_image(image_url)
    except Exception as e:
        print(f"Warning: Failed to post to Stories: {e}")

    print(f"\nDone! Puzzle of the Week posted. Media ID: {media_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post Puzzle of the Week")
    parser.add_argument("--dry-run", action="store_true", help="Preview without posting")
    args = parser.parse_args()
    post_puzzle_of_week(dry_run=args.dry_run)
