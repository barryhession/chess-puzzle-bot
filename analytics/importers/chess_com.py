"""
chess_com.py
------------
Chess.com PubAPI client for Chess Signal analytics.

Read-only API — no authentication required.
Serial requests only (respect rate limits).

Docs: https://www.chess.com/news/view/published-data-api
"""

import os
import re
import time
from datetime import datetime

import requests

BASE_URL = "https://api.chess.com/pub"

# Rate limit: be polite, wait between requests
REQUEST_DELAY = 1.0  # seconds between requests


def _get(path: str) -> dict | list:
    """Make a GET request to the Chess.com API."""
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, headers={"User-Agent": "ChessSignalAnalytics/1.0"})
    if resp.status_code == 429:
        print("[chess_com] Rate limited, waiting 10s...")
        time.sleep(10)
        resp = requests.get(url, headers={"User-Agent": "ChessSignalAnalytics/1.0"})
    resp.raise_for_status()
    time.sleep(REQUEST_DELAY)
    return resp.json()


def get_player_profile(username: str) -> dict:
    """
    Get player profile.

    Returns dict with: username, player_id, title, status, joined, last_online,
    followers, is_streamer, fide, avatar, country, etc.
    """
    return _get(f"/player/{username.lower()}")


def get_player_stats(username: str) -> dict:
    """
    Get player stats across all time controls.

    Returns dict with keys like: chess_rapid, chess_blitz, chess_bullet,
    chess_daily, tactics, puzzle_rush. Each has 'last' (current rating),
    'best' (peak), 'record' (win/loss/draw).
    """
    return _get(f"/player/{username.lower()}/stats")


def get_available_archives(username: str) -> list[str]:
    """
    Get list of monthly archives available for this player.

    Returns list of URL paths like: ["/player/kingcelt/games/2026/08", ...]
    Sorted chronologically (oldest first).
    """
    data = _get(f"/player/{username.lower()}/games/archives")
    return data.get("archives", [])


def get_monthly_games(username: str, year: int, month: int) -> list[dict]:
    """
    Get all finished games for a specific month.

    Returns list of game dicts with: white, black, pgn, time_control,
    time_class, end_time, accuracies, etc.
    """
    data = _get(f"/player/{username.lower()}/games/{year}/{month:02d}")
    return data.get("games", []) if isinstance(data, dict) else data


def _parse_result(result: str) -> str:
    """Normalize game result to 'win', 'loss', or 'draw'."""
    if result in ("win",):
        return "win"
    elif result in ("lose", "checkmated", "resigned", "timeout",
                    "abandoned", "kingofthehill", "threecheck",
                    "insufficient", "bughousepartnerlose"):
        return "loss"
    else:
        return "draw"  # draw, stalemate, repetition, agreement, etc.


def _extract_game_id(url: str) -> str:
    """Extract game ID from Chess.com game URL."""
    # URL format: https://www.chess.com/game/live/1234567890
    # or: https://www.chess.com/daily-chess-puzzle/2026-08-30
    parts = url.rstrip("/").split("/")
    return parts[-1] if parts else url


def _parse_timestamp(ts: int) -> str:
    """Convert Unix timestamp to ISO format."""
    return datetime.utcfromtimestamp(ts).isoformat()


def import_games_to_db(
    username: str,
    conn,
    time_class_filter: str | None = None,
    update: bool = False,
) -> dict:
    """
    Import games for a player into the database.

    Args:
        username: Chess.com username
        conn: SQLite connection from analytics.db
        time_class_filter: Optional filter ('rapid', 'blitz', 'bullet', 'daily')
        update: If True, only fetch months after last import

    Returns:
        dict with import stats: {games_imported, games_skipped, months_processed}
    """
    from analytics.db import game_exists, get_last_played_at, insert_game

    username_lower = username.lower()
    archives = get_available_archives(username_lower)
    print(f"[chess_com] Found {len(archives)} monthly archives for {username}")

    # In update mode, only check current month (past months don't change)
    if update:
        last = get_last_played_at(conn, "chess_com", username_lower)
        if last:
            dt = datetime.fromisoformat(last)
            now = datetime.utcnow()
            # Only check current month (and maybe previous if last game was recent)
            if dt.year == now.year and dt.month == now.month:
                # Same month — already checked, nothing new
                print(f"[chess_com] Last game was this month ({last}), nothing to update")
                return {"games_imported": 0, "games_skipped": 0, "months_processed": 0}
            # Check current month only
            cutoff_ym = f"{now.year}/{now.month:02d}"
            archives = [a for a in archives if a.split("/")[-2] + "/" + a.split("/")[-1] >= cutoff_ym]
            print(f"[chess_com] Updating — checking {len(archives)} month(s)")
        else:
            print("[chess_com] No previous games found, importing all...")

    stats = {"games_imported": 0, "games_skipped": 0, "months_processed": 0}

    for archive_path in archives:
        # Extract year/month from URL path like "/player/kingcelt/games/2026/08"
        parts = archive_path.split("/")
        try:
            year = int(parts[-2])
            month = int(parts[-1])
        except (ValueError, IndexError):
            print(f"[chess_com] Skipping invalid archive path: {archive_path}")
            continue

        print(f"[chess_com] Importing {year}-{month:02d}...")
        games = get_monthly_games(username_lower, year, month)
        stats["months_processed"] += 1

        for game in games:
            game_id = _extract_game_id(game.get("url", ""))

            # Check if already imported
            if game_exists(conn, "chess_com", username_lower, game_id):
                stats["games_skipped"] += 1
                continue

            # Determine which side the player is on
            white_data = game.get("white", {})
            black_data = game.get("black", {})

            white_name = white_data.get("username", "").lower()
            black_name = black_data.get("username", "").lower()

            if white_name == username_lower:
                my_data = white_data
                opponent_data = black_data
            elif black_name == username_lower:
                my_data = black_data
                opponent_data = white_data
            else:
                # Username not in this game (shouldn't happen)
                continue

            # Filter by time class if specified
            game_time_class = game.get("time_class", "")
            if time_class_filter and game_time_class != time_class_filter:
                stats["games_skipped"] += 1
                continue

            # Parse result
            my_result = _parse_result(my_data.get("result", ""))
            opponent_result = _parse_result(opponent_data.get("result", ""))

            # If I won, opponent lost (and vice versa)
            if my_result == "win":
                final_result = "win"
            elif my_result == "loss":
                final_result = "loss"
            else:
                final_result = "draw"

            game_record = {
                "source": "chess_com",
                "account": username_lower,
                "game_id": game_id,
                "opponent": opponent_data.get("username", "unknown"),
                "my_rating": my_data.get("rating"),
                "opponent_rating": opponent_data.get("rating"),
                "result": final_result,
                "time_control": game.get("time_control"),
                "time_class": game_time_class,
                "opening": game.get("eco"),
                "played_at": _parse_timestamp(game.get("end_time", 0)),
                "pgn": game.get("pgn", ""),
            }

            insert_game(conn, game_record)
            stats["games_imported"] += 1

    return stats


def get_stats_summary(username: str) -> dict:
    """
    Get a clean summary of player stats.

    Returns dict with ratings and records by time class.
    """
    raw = get_player_stats(username)
    summary = {}

    for key in ("chess_rapid", "chess_blitz", "chess_bullet", "chess_daily"):
        if key in raw:
            time_class = key.replace("chess_", "")
            last = raw[key].get("last", {})
            record = raw[key].get("record", {})
            summary[time_class] = {
                "rating": last.get("rating"),
                "rd": last.get("rd"),
                "win": record.get("win", 0),
                "loss": record.get("loss", 0),
                "draw": record.get("draw", 0),
            }

    if "tactics" in raw:
        summary["tactics"] = {
            "highest": raw["tactics"].get("highest", {}).get("rating"),
            "lowest": raw["tactics"].get("lowest", {}).get("rating"),
        }

    if "puzzle_rush" in raw:
        summary["puzzle_rush"] = raw["puzzle_rush"].get("best", {}).get("score")

    return summary
