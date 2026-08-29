"""
test_content_posts.py
---------------------
Test script to post chess term, historical event, book recommendation, and opening to Instagram.

Usage:
    python test_content_posts.py              # post all four
    python test_content_posts.py --dry-run    # preview without posting
"""

import argparse
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from src.chess_terms import get_term_of_the_day
from src.history import get_today_in_history
from src.books import get_book_of_the_week
from src.openings import get_opening_of_the_day
from src.text_renderer import render_chess_term, render_historical_event, render_book, render_opening
from src.image_host import upload_image
from src import instagram

OUTPUT_DIR = Path(__file__).parent / "output"


def post_chess_term(dry_run: bool = False) -> None:
    """Generate and post chess term of the day."""
    print("=== Chess Term of the Day ===\n")

    term = get_term_of_the_day()
    print(f"Term: {term['term']}")
    print(f"Definition: {term['definition']}")
    print(f"Example: {term['example']}")

    # Render graphic
    output_path = OUTPUT_DIR / "chess_term.png"
    render_chess_term(term, output_path)

    # Build caption
    hashtags = [
        "#chess", "#chessterm", "#lichess", "#chesspuzzle", "#chesscom",
        "#chessdaily", "#chesslife", "#chesslove", "#chessgame", "#chessboard",
        "#chessislife", "#chesscommunity", "#chessclub", "#chessstrategy",
        "#chessplayer", "#chessmaster", "#chesstraining", "#chessworld",
        "#chessmoves", "#chessgrandmaster",
    ]
    caption = f"♟️ Chess Term: {term['term']}\n\n{term['definition']}\n\n{term['example']}\n\n{' '.join(hashtags)}"

    print("\nCaption preview:")
    print("-" * 40)
    print(caption)
    print("-" * 40)

    if dry_run:
        print("\n[dry-run] Stopping. Graphic at:", output_path)
        return

    # Upload
    print("\nUploading...")
    image_url = upload_image(output_path)

    # Post
    print("Posting to Instagram...")
    media_id = instagram.publish(image_url, caption)
    print(f"Posted! Media ID: {media_id}")

    # Post to Stories
    print("Posting to Stories...")
    try:
        instagram.post_stories_image(image_url)
    except Exception as e:
        print(f"Warning: Stories post failed: {e}")

    print("Done!\n")


def post_history(dry_run: bool = False) -> None:
    """Generate and post historical event."""
    print("=== On This Day in Chess History ===\n")

    event = get_today_in_history()
    if not event:
        print("No historical event for today. Skipping.")
        return

    print(f"Event: {event['event']}")
    print(f"Detail: {event['detail']}")

    # Render graphic
    output_path = OUTPUT_DIR / "history.png"
    render_historical_event(event, output_path)

    # Build caption
    month, day = event["date"].split("-")
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    date_str = f"{months[int(month)-1]} {int(day)}"

    hashtags = [
        "#chess", "#chesstrivia", "#lichess", "#chesspuzzle", "#chesscom",
        "#chessdaily", "#chesslife", "#chesslove", "#chessgame", "#chessboard",
        "#chessislife", "#chesscommunity", "#chessclub", "#chesshistory",
        "#chessplayer", "#chessmaster", "#chesstraining", "#chessworld",
        "#chessmoves", "#chessgrandmaster",
    ]
    caption = f"📅 On This Day: {date_str}\n\n{event['event']}\n\n{event['detail']}\n\n{' '.join(hashtags)}"

    print("\nCaption preview:")
    print("-" * 40)
    print(caption)
    print("-" * 40)

    if dry_run:
        print("\n[dry-run] Stopping. Graphic at:", output_path)
        return

    # Upload
    print("\nUploading...")
    image_url = upload_image(output_path)

    # Post
    print("Posting to Instagram...")
    media_id = instagram.publish(image_url, caption)
    print(f"Posted! Media ID: {media_id}")

    # Post to Stories
    print("Posting to Stories...")
    try:
        instagram.post_stories_image(image_url)
    except Exception as e:
        print(f"Warning: Stories post failed: {e}")

    print("Done!\n")


def post_book(dry_run: bool = False) -> None:
    """Generate and post book recommendation."""
    print("=== Book of the Week ===\n")

    book = get_book_of_the_week()
    print(f"Title: {book['title']}")
    print(f"Author: {book['author']}")
    print(f"Description: {book['description']}")
    print(f"Level: {book['level']}")

    # Render graphic
    output_path = OUTPUT_DIR / "book.png"
    render_book(book, output_path)

    # Build caption
    hashtags = [
        "#chess", "#chessbooks", "#lichess", "#chesspuzzle", "#chesscom",
        "#chessdaily", "#chesslife", "#chesslove", "#chessgame", "#chessboard",
        "#chessislife", "#chesscommunity", "#chessclub", "#chessreading",
        "#chessplayer", "#chessmaster", "#chesstraining", "#chessworld",
        "#chessmoves", "#chessgrandmaster",
    ]
    caption = f"📚 Book of the Week: {book['title']}\n\nby {book['author']}\n\n{book['description']}\n\nLevel: {book['level']}\n\n{' '.join(hashtags)}"

    print("\nCaption preview:")
    print("-" * 40)
    print(caption)
    print("-" * 40)

    if dry_run:
        print("\n[dry-run] Stopping. Graphic at:", output_path)
        return

    # Upload
    print("\nUploading...")
    image_url = upload_image(output_path)

    # Post
    print("Posting to Instagram...")
    media_id = instagram.publish(image_url, caption)
    print(f"Posted! Media ID: {media_id}")

    # Post to Stories
    print("Posting to Stories...")
    try:
        instagram.post_stories_image(image_url)
    except Exception as e:
        print(f"Warning: Stories post failed: {e}")

    print("Done!\n")


def post_opening(dry_run: bool = False) -> None:
    """Generate and post opening of the day."""
    print("=== Opening of the Day ===\n")

    opening = get_opening_of_the_day()
    print(f"Opening: {opening['name']}")
    print(f"Moves: {opening['moves']}")
    print(f"Idea: {opening['idea']}")
    print(f"Level: {opening['level']}")

    # Render graphic
    output_path = OUTPUT_DIR / "opening.png"
    render_opening(opening, output_path)

    # Build caption
    hashtags = [
        "#chess", "#chessopening", "#lichess", "#chesspuzzle", "#chesscom",
        "#chessdaily", "#chesslife", "#chesslove", "#chessgame", "#chessboard",
        "#chessislife", "#chesscommunity", "#chessclub", "#chesstheory",
        "#chessplayer", "#chessmaster", "#chesstraining", "#chessworld",
        "#chessmoves", "#chessgrandmaster",
    ]
    caption = f"♟️ Opening of the Day: {opening['name']}\n\n{opening['moves']}\n\n{opening['idea']}\n\nLevel: {opening['level']}\n\n{' '.join(hashtags)}"

    print("\nCaption preview:")
    print("-" * 40)
    print(caption)
    print("-" * 40)

    if dry_run:
        print("\n[dry-run] Stopping. Graphic at:", output_path)
        return

    # Upload
    print("\nUploading...")
    image_url = upload_image(output_path)

    # Post
    print("Posting to Instagram...")
    media_id = instagram.publish(image_url, caption)
    print(f"Posted! Media ID: {media_id}")

    # Post to Stories
    print("Posting to Stories...")
    try:
        instagram.post_stories_image(image_url)
    except Exception as e:
        print(f"Warning: Stories post failed: {e}")

    print("Done!\n")


def main():
    parser = argparse.ArgumentParser(description="Test content posts")
    parser.add_argument("--dry-run", action="store_true", help="Preview without posting")
    args = parser.parse_args()

    post_chess_term(dry_run=args.dry_run)
    post_history(dry_run=args.dry_run)
    post_book(dry_run=args.dry_run)
    post_opening(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
