"""
create_news_draft.py
--------------------
Create a news draft for manual review.

Usage:
    python create_news_draft.py              # fetch latest, filter, render
    python create_news_draft.py --dry-run    # preview without saving
    python create_news_draft.py --limit 3    # max stories (default 3)

Output:
    news/drafts/YYYY-MM-DD_HHMMSS/
        ├── graphic.png
        ├── caption.txt
        ├── comments/0.txt, 1.txt, 2.txt
        └── manifest.json
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from src.news_fetcher import fetch_news
from src.news_filter import filter_stories
from src.news_renderer import render_news_graphic
from src.news_caption import build_news_caption, build_news_comments

DRAFTS_DIR = Path(__file__).parent / "news" / "drafts"


def main():
    parser = argparse.ArgumentParser(description="Create a chess news draft")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    parser.add_argument("--limit", type=int, default=3, help="Max stories to include")
    args = parser.parse_args()

    # ── Step 1: Fetch news from RSS feeds ──────────────────────────────────────
    print("\n=== Step 1: Fetching news from RSS feeds ===")
    stories = fetch_news()
    if not stories:
        print("[draft] No stories found from any source.")
        sys.exit(0)

    print(f"[draft] Fetched {len(stories)} stories total")

    # ── Step 2: Filter through safety layer ────────────────────────────────────
    print("\n=== Step 2: Content safety filter ===")
    safe_stories, skipped_stories = filter_stories(stories)
    if not safe_stories:
        print("[draft] No safe stories after filtering.")
        sys.exit(0)

    # ── Step 3: Select top stories ─────────────────────────────────────────────
    selected = safe_stories[: args.limit]
    print(f"\n=== Step 3: Selected {len(selected)} stories ===")
    for i, s in enumerate(selected, 1):
        print(f"  {i}. [{s['source']}] {s['title'][:70]}")
        print(f"     Date: {s['date']}  URL: {s['url'][:60]}...")

    # ── Step 4: Generate caption and comments ──────────────────────────────────
    print("\n=== Step 4: Generating caption and comments ===")
    caption = build_news_caption(selected)
    comments = build_news_comments(selected)

    print("\nCaption preview:")
    print("-" * 40)
    print(caption)
    print("-" * 40)

    # ── Step 5: Render graphic ─────────────────────────────────────────────────
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    draft_dir = DRAFTS_DIR / timestamp

    if args.dry_run:
        graphic_path = Path("output") / f"news_draft_{timestamp}.png"
        print(f"\n=== Step 5: Rendering graphic (dry-run) ===")
    else:
        graphic_path = draft_dir / "graphic.png"
        print(f"\n=== Step 5: Rendering graphic ===")

    render_news_graphic(selected, graphic_path)

    # ── Step 6: Save draft ─────────────────────────────────────────────────────
    if args.dry_run:
        print("\n[dry-run] Stopping before save. Graphic is at:", graphic_path)
        return

    print(f"\n=== Step 6: Saving draft to {draft_dir} ===")
    draft_dir.mkdir(parents=True, exist_ok=True)

    # Save graphic (already rendered above)
    # Save caption
    (draft_dir / "caption.txt").write_text(caption, encoding="utf-8")

    # Save comments
    comments_dir = draft_dir / "comments"
    comments_dir.mkdir(exist_ok=True)
    for i, comment in enumerate(comments):
        (comments_dir / f"{i}.txt").write_text(comment, encoding="utf-8")

    # Save manifest
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "puzzle_source": "Lichess open puzzle database (CC0)",
        "stories": selected,
        "skipped": skipped_stories,
        "status": "draft",
    }
    (draft_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\n[draft] Draft saved: {draft_dir}")
    print(f"  - graphic.png")
    print(f"  - caption.txt")
    print(f"  - comments/ ({len(comments)} files)")
    print(f"  - manifest.json")
    print(f"\nReview the draft, then run:")
    print(f"  python publish_news.py {draft_dir}")


if __name__ == "__main__":
    main()
