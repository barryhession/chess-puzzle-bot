"""
test_connection.py
------------------
CLI to test Chess.com and Lichess API connections and import games.

Usage:
    # Full import (first time)
    python analytics/test_connection.py --source chess_com --import
    python analytics/test_connection.py --source lichess --import

    # Update (append new games only)
    python analytics/test_connection.py --source chess_com --import --update
    python analytics/test_connection.py --source lichess --import --update

    # View stats
    python analytics/test_connection.py --source chess_com --stats
    python analytics/test_connection.py --source lichess --stats
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Add parent dir to path so we can import analytics
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from analytics.db import get_db, get_games


# ── Chess.com helpers ────────────────────────────────────────────────────────

def test_chess_com(username: str) -> None:
    """Test Chess.com API connection."""
    from analytics.importers.chess_com import get_player_profile, get_available_archives

    print(f"=== Chess.com Connection Test: {username} ===\n")
    try:
        profile = get_player_profile(username)
        print(f"Profile found!")
        print(f"  Username:  {profile.get('username')}")
        print(f"  Player ID: {profile.get('player_id')}")
        print(f"  Title:     {profile.get('title', 'N/A')}")
        print(f"  Joined:    {profile.get('joined')}")
        print(f"  Status:    {profile.get('status')}")
        print(f"  Followers: {profile.get('followers')}")
        print(f"  FIDE:      {profile.get('fide', 'N/A')}")
    except Exception as e:
        print(f"Error fetching profile: {e}")
        return

    print()
    time.sleep(1)

    try:
        archives = get_available_archives(username)
        print(f"Archives: {len(archives)} months available")
        if archives:
            oldest = archives[0].split("/")[-2:]
            newest = archives[-1].split("/")[-2:]
            print(f"  Range: {oldest[0]}-{oldest[1]} to {newest[0]}-{newest[1]}")
    except Exception as e:
        print(f"Error fetching archives: {e}")
    print()


def show_chess_com_stats(username: str) -> None:
    """Show Chess.com stats summary."""
    from analytics.importers.chess_com import get_stats_summary

    print(f"=== Chess.com Stats for {username} ===\n")
    try:
        summary = get_stats_summary(username)
        if not summary:
            print("No stats found.")
            return
        for time_class, data in summary.items():
            if time_class == "tactics":
                print(f"Tactics: highest {data.get('highest')}, lowest {data.get('lowest')}")
            elif time_class == "puzzle_rush":
                print(f"Puzzle Rush best: {data}")
            else:
                rating = data.get("rating", "?")
                win = data.get("win", 0)
                loss = data.get("loss", 0)
                draw = data.get("draw", 0)
                total = win + loss + draw
                pct = (win / total * 100) if total > 0 else 0
                print(f"{time_class.capitalize():>8}: {rating}  "
                      f"W:{win} L:{loss} D:{draw}  "
                      f"({pct:.0f}% win rate)")
    except Exception as e:
        print(f"Error fetching stats: {e}")
    print()


def import_chess_com(username: str, time_class: str | None = None, update: bool = False) -> None:
    """Import Chess.com games into the local database."""
    from analytics.importers.chess_com import import_games_to_db

    print(f"=== Importing Chess.com games for {username} ===\n")
    conn = get_db()
    try:
        result = import_games_to_db(username, conn, time_class_filter=time_class, update=update)
        print(f"\nImport complete!")
        print(f"  Months processed: {result['months_processed']}")
        print(f"  Games imported:   {result['games_imported']}")
        print(f"  Games skipped:    {result['games_skipped']}")
    finally:
        conn.close()


# ── Lichess helpers ──────────────────────────────────────────────────────────

def test_lichess(username: str) -> None:
    """Test Lichess API connection."""
    from analytics.importers.lichess import get_user_profile

    print(f"=== Lichess Connection Test: {username} ===\n")
    try:
        profile = get_user_profile(username)
        print(f"Profile found!")
        print(f"  Username:  {profile.get('username')}")
        print(f"  User ID:   {profile.get('id')}")
        print(f"  Title:     {profile.get('title', 'N/A')}")
        print(f"  Created:   {profile.get('createdAt')}")
        print(f"  Seen:      {profile.get('seenAt')}")
        print(f"  Games:     {profile.get('count', {}).get('all', '?')} total")

        # Show perfs
        perfs = profile.get("perfs", {})
        print(f"\nRatings:")
        for tc in ("rapid", "blitz", "bullet", "classical", "correspondence"):
            if tc in perfs:
                p = perfs[tc]
                print(f"  {tc.capitalize():>15}: {p.get('rating', '?')}  "
                      f"({p.get('games', 0)} games)")
    except Exception as e:
        print(f"Error fetching profile: {e}")
    print()


def show_lichess_stats(username: str) -> None:
    """Show Lichess stats summary."""
    from analytics.importers.lichess import get_stats_summary

    print(f"=== Lichess Stats for {username} ===\n")
    try:
        summary = get_stats_summary(username)
        if not summary:
            print("No stats found.")
            return
        for time_class, data in summary.items():
            rating = data.get("rating", "?")
            games = data.get("games", 0)
            print(f"{time_class.capitalize():>15}: {rating}  ({games} games)")
    except Exception as e:
        print(f"Error fetching stats: {e}")
    print()


def import_lichess(username: str, time_class: str | None = None,
                   max_games: int | None = None, update: bool = False) -> None:
    """Import Lichess games into the local database."""
    from analytics.importers.lichess import import_games_to_db

    print(f"=== Importing Lichess games for {username} ===\n")
    conn = get_db()
    try:
        result = import_games_to_db(username, conn, time_class_filter=time_class,
                                    max_games=max_games, update=update)
        print(f"\nImport complete!")
        print(f"  Games imported: {result['games_imported']}")
        print(f"  Games skipped:  {result['games_skipped']}")
    finally:
        conn.close()


# ── Shared helpers ───────────────────────────────────────────────────────────

def show_recent_games(source: str, username: str, limit: int = 10) -> None:
    """Show recent games from the database."""
    print(f"=== Recent {source} games for {username} ===\n")
    conn = get_db()
    try:
        games = get_games(conn, source=source, account=username.lower(), limit=limit)
        if not games:
            print("No games in database. Run --import first.")
            return
        for g in games:
            result_icon = {"win": "W", "loss": "L", "draw": "D"}.get(g["result"], "?")
            print(f"  [{result_icon}] {g['my_rating'] or '?'} vs {g['opponent']}"
                  f" ({g['opponent_rating'] or '?'}) "
                  f"- {g['time_class'] or '?'} "
                  f"- {g['played_at'] or '?'}")
    finally:
        conn.close()
    print()


def main():
    parser = argparse.ArgumentParser(description="Chess analytics API connection test")
    parser.add_argument("--source", choices=["chess_com", "lichess"], default="chess_com",
                        help="Which API to test (default: chess_com)")
    parser.add_argument("--username", help="Username (default: from .env)")
    parser.add_argument("--import", dest="do_import", action="store_true",
                        help="Import games into local database")
    parser.add_argument("--update", action="store_true",
                        help="Only fetch new games since last import")
    parser.add_argument("--time-class", choices=["rapid", "blitz", "bullet", "daily"],
                        help="Filter import by time class")
    parser.add_argument("--max-games", type=int, default=None,
                        help="Max games to import (Lichess only, default: all)")
    parser.add_argument("--stats", action="store_true",
                        help="Show player stats summary")
    parser.add_argument("--games", action="store_true",
                        help="Show recent games from database")
    args = parser.parse_args()

    # Get username from args or .env
    if args.username:
        username = args.username
    elif args.source == "chess_com":
        username = os.environ.get("CHESS_COM_USERNAME")
    else:
        username = os.environ.get("LICHESS_USERNAME")

    if not username:
        env_var = "CHESS_COM_USERNAME" if args.source == "chess_com" else "LICHESS_USERNAME"
        print(f"Error: No username. Use --username or set {env_var} in .env")
        sys.exit(1)

    # Run appropriate functions
    if args.source == "chess_com":
        test_chess_com(username)
        if args.stats:
            show_chess_com_stats(username)
        if args.do_import:
            import_chess_com(username, time_class=args.time_class, update=args.update)
            show_recent_games("chess_com", username)
        if args.games:
            show_recent_games("chess_com", username)
    else:
        test_lichess(username)
        if args.stats:
            show_lichess_stats(username)
        if args.do_import:
            import_lichess(username, time_class=args.time_class, max_games=args.max_games,
                          update=args.update)
            show_recent_games("lichess", username)
        if args.games:
            show_recent_games("lichess", username)


if __name__ == "__main__":
    main()
