"""
publish_news.py
---------------
Publish an approved news draft to Instagram.

Usage:
    python publish_news.py news/drafts/2026-08-29_120000/
    python publish_news.py news/drafts/2026-08-29_120000/ --dry-run

Steps:
    1. Load manifest.json
    2. Upload graphic to GitHub Releases
    3. Post to Instagram feed with caption
    4. Post graphic to Stories
    5. Post comments with source URLs
    6. Move draft to news/archived/
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from src.image_host import upload_image
from src import instagram


ARCHIVED_DIR = Path(__file__).parent / "news" / "archived"


def main():
    parser = argparse.ArgumentParser(description="Publish a news draft to Instagram")
    parser.add_argument("draft_path", type=Path, help="Path to approved draft folder")
    parser.add_argument("--dry-run", action="store_true", help="Preview without publishing")
    args = parser.parse_args()

    draft_dir = args.draft_path

    # ── Validate draft ─────────────────────────────────────────────────────────
    if not draft_dir.exists():
        print(f"[publish] Error: Draft not found: {draft_dir}")
        sys.exit(1)

    manifest_path = draft_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"[publish] Error: manifest.json not found in {draft_dir}")
        sys.exit(1)

    graphic_path = draft_dir / "graphic.png"
    if not graphic_path.exists():
        print(f"[publish] Error: graphic.png not found in {draft_dir}")
        sys.exit(1)

    caption_path = draft_dir / "caption.txt"
    if not caption_path.exists():
        print(f"[publish] Error: caption.txt not found in {draft_dir}")
        sys.exit(1)

    # ── Load manifest ──────────────────────────────────────────────────────────
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    stories = manifest.get("stories", [])
    skipped = manifest.get("skipped", [])

    print(f"\n[publish] Draft: {draft_dir}")
    print(f"[publish] Stories: {len(stories)}")
    print(f"[publish] Skipped: {len(skipped)}")
    print(f"[publish] Status: {manifest.get('status', 'unknown')}")

    for i, s in enumerate(stories, 1):
        print(f"  {i}. [{s['source']}] {s['title'][:60]}")

    # ── Step 1: Upload graphic ─────────────────────────────────────────────────
    print("\n=== Step 1: Uploading graphic ===")
    if args.dry_run:
        print("[dry-run] Would upload:", graphic_path)
        image_url = "https://example.com/dry-run.png"
    else:
        try:
            image_url = upload_image(graphic_path)
            print(f"[publish] Uploaded: {image_url}")
        except Exception as e:
            print(f"[publish] Error uploading: {e}")
            sys.exit(1)

    # ── Step 2: Post to feed ───────────────────────────────────────────────────
    print("\n=== Step 2: Posting to Instagram feed ===")
    caption = caption_path.read_text(encoding="utf-8")

    if args.dry_run:
        print("[dry-run] Would post caption:")
        print("-" * 40)
        print(caption)
        print("-" * 40)
        media_id = "dry-run-media-id"
    else:
        try:
            media_id = instagram.publish(image_url, caption)
            print(f"[publish] Posted! Media ID: {media_id}")
        except Exception as e:
            print(f"[publish] Error posting: {e}")
            sys.exit(1)

    # ── Step 3: Post to Stories ────────────────────────────────────────────────
    print("\n=== Step 3: Posting to Stories ===")
    if args.dry_run:
        print("[dry-run] Would post to Stories:", image_url)
    else:
        try:
            instagram.post_stories_image(image_url)
            print("[publish] Stories post complete!")
        except Exception as e:
            print(f"[publish] Warning: Failed to post to Stories: {e}")

    # ── Step 4: Post comments with source URLs ─────────────────────────────────
    print("\n=== Step 4: Posting source URL comments ===")
    comments_dir = draft_dir / "comments"
    if comments_dir.exists():
        comment_files = sorted(comments_dir.glob("*.txt"))
        for i, comment_file in enumerate(comment_files):
            comment_text = comment_file.read_text(encoding="utf-8").strip()
            if args.dry_run:
                print(f"[dry-run] Would post comment {i}: {comment_text}")
            else:
                try:
                    instagram.post_comment(media_id, comment_text)
                    print(f"[publish] Comment {i} posted: {comment_text[:60]}...")
                except Exception as e:
                    print(f"[publish] Warning: Failed to post comment {i}: {e}")

    # ── Step 5: Archive draft ──────────────────────────────────────────────────
    if args.dry_run:
        print("\n[dry-run] Stopping before archive.")
        return

    print("\n=== Step 5: Archiving draft ===")
    ARCHIVED_DIR.mkdir(parents=True, exist_ok=True)
    archive_dest = ARCHIVED_DIR / draft_dir.name
    try:
        shutil.move(str(draft_dir), str(archive_dest))
        print(f"[publish] Draft archived: {archive_dest}")
    except Exception as e:
        print(f"[publish] Warning: Failed to archive draft: {e}")

    print("\n[publish] Done!")


if __name__ == "__main__":
    main()
