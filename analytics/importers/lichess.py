"""
lichess.py
----------
Lichess API client for Chess Signal analytics.

Read-only API — no authentication required for public data.
Rate limit: 1 request per second.

Docs: https://lichess.org/api
"""

import json
import os
import time
from datetime import datetime

import requests

BASE_URL = "https://lichess.org"
REQUEST_DELAY = 1.1  # seconds between requests (Lichess allows 1/sec)


def _get(path: str, accept: str = "application/json", params: dict | None = None) -> requests.Response:
    """Make a GET request to the Lichess API."""
    url = f"{BASE_URL}{path}"
    headers = {"Accept": accept, "User-Agent": "ChessSignalAnalytics/1.0"}
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code == 429:
        print("[lichess] Rate limited, waiting 10s...")
        time.sleep(10)
        resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    time.sleep(REQUEST_DELAY)
    return resp


def get_user_profile(username: str) -> dict:
    """
    Get user profile and stats.

    Returns dict with: id, username, perfs (ratings), count (games),
    createdAt, seenAt, title, etc.
    """
    resp = _get(f"/api/user/{username}")
    return resp.json()


def get_user_stats(username: str) -> dict:
    """
    Get ratings by time control from user profile.

    Returns dict like: {"rapid": {"rating": 1500, "games": 100}, ...}
    """
    profile = get_user_profile(username)
    perfs = profile.get("perfs", {})
    stats = {}

    for time_class in ("rapid", "blitz", "bullet", "correspondence", "classical"):
        if time_class in perfs:
            perf = perfs[time_class]
            stats[time_class] = {
                "rating": perf.get("rating"),
                "rd": perf.get("rd"),
                "games": perf.get("games", 0),
            }

    return stats


def get_games(username: str, since: int | None = None, until: int | None = None,
              max_games: int | None = None) -> list[dict]:
    """
    Export user games as NDJSON (one JSON object per line).

    Args:
        username: Lichess username
        since: Unix timestamp (ms) - filter games after this
        until: Unix timestamp (ms) - filter games before this
        max_games: Max number of games to return

    Returns:
        List of game dicts
    """
    params = {"moves": "true", "pgnInJson": "true", "opening": "true"}
    if since:
        params["since"] = since
    if until:
        params["until"] = until
    if max_games:
        params["max"] = max_games

    resp = _get(f"/api/games/user/{username}", accept="application/x-ndjson", params=params)

    games = []
    for line in resp.text.strip().split("\n"):
        if line.strip():
            try:
                games.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return games


def get_puzzle_activity(username: str, since: int | None = None) -> list[dict]:
    """
    Get puzzle activity (requires auth token).

    Note: This endpoint requires a Lichess API token with puzzle:read scope.
    Without auth, returns empty list.
    """
    token = os.environ.get("LICHESS_API_TOKEN")
    if not token:
        print("[lichess] No LICHESS_API_TOKEN set, skipping puzzle activity")
        return []

    headers = {"Authorization": f"Bearer {token}", "User-Agent": "ChessSignalAnalytics/1.0"}
    params = {}
    if since:
        params["since"] = since

    try:
        resp = requests.get(f"{BASE_URL}/api/user/{username}/puzzle-activity",
                          headers=headers, params=params)
        resp.raise_for_status()

        activities = []
        for line in resp.text.strip().split("\n"):
            if line.strip():
                try:
                    activities.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return activities
    except Exception as e:
        print(f"[lichess] Puzzle activity error: {e}")
        return []


def _parse_result(game: dict, username: str) -> str:
    """Determine if the user won, lost, or drew."""
    winner = game.get("winner")
    players = game.get("players", {})

    # Determine which color the user played
    white_name = players.get("white", {}).get("user", {}).get("name", "").lower()
    black_name = players.get("black", {}).get("user", {}).get("name", "").lower()

    if white_name == username.lower():
        my_color = "white"
    elif black_name == username.lower():
        my_color = "black"
    else:
        return "unknown"

    if winner is None:
        return "draw"
    elif winner == my_color:
        return "win"
    else:
        return "loss"


def _parse_timestamp(ts_ms: int) -> str:
    """Convert Lichess timestamp (ms) to ISO format."""
    return datetime.utcfromtimestamp(ts_ms / 1000).isoformat()


def import_games_to_db(username: str, conn, time_class_filter: str | None = None,
                       max_games: int | None = None, update: bool = False) -> dict:
    """
    Import games for a player into the database.

    Args:
        username: Lichess username
        conn: SQLite connection from analytics.db
        time_class_filter: Optional filter ('rapid', 'blitz', 'bullet')
        max_games: Max number of games to fetch (None = all)
        update: If True, only fetch games since last import

    Returns:
        dict with import stats
    """
    from analytics.db import game_exists, get_last_played_at, insert_game

    username_lower = username.lower()

    # Calculate since timestamp for update mode
    since_ms = None
    if update:
        last = get_last_played_at(conn, "lichess", username_lower)
        if last:
            # Convert ISO timestamp to ms
            dt = datetime.fromisoformat(last)
            since_ms = int(dt.timestamp() * 1000)
            print(f"[lichess] Updating since {last}...")
        else:
            print("[lichess] No previous games found, importing all...")

    print(f"[lichess] Fetching games for {username}...")
    games = get_games(username, since=since_ms, max_games=max_games)
    print(f"[lichess] Found {len(games)} games")

    stats = {"games_imported": 0, "games_skipped": 0}

    for game in games:
        game_id = game.get("id", "")

        # Check if already imported
        if game_exists(conn, "lichess", username_lower, game_id):
            stats["games_skipped"] += 1
            continue

        # Get time class from speed field
        time_class = game.get("speed", "").replace("rated", "").replace("casual", "").strip()

        # Filter by time class if specified
        if time_class_filter and time_class != time_class_filter:
            stats["games_skipped"] += 1
            continue

        # Parse game data
        result = _parse_result(game, username_lower)
        players = game.get("players", {})
        white_data = players.get("white", {})
        black_data = players.get("black", {})

        white_name = white_data.get("user", {}).get("name", "").lower()
        if white_name == username_lower:
            my_data = white_data
            opponent_data = black_data
        else:
            my_data = black_data
            opponent_data = white_data

        # Build PGN from moves
        moves = game.get("moves", "")
        pgn_moves = " ".join(moves.split()) if moves else ""

        game_record = {
            "source": "lichess",
            "account": username_lower,
            "game_id": game_id,
            "opponent": opponent_data.get("user", {}).get("name", "unknown"),
            "my_rating": my_data.get("rating"),
            "opponent_rating": black_data.get("rating") if white_name == username_lower else white_data.get("rating"),
            "result": result,
            "time_control": game.get("timeControl", {}).get("show", game.get("clock", {}).get("initial", "")),
            "time_class": time_class,
            "opening": game.get("opening", {}).get("name", ""),
            "played_at": _parse_timestamp(game.get("createdAt", 0)),
            "pgn": pgn_moves,
        }

        insert_game(conn, game_record)
        stats["games_imported"] += 1

    return stats


def get_stats_summary(username: str) -> dict:
    """Get a clean summary of player stats."""
    return get_user_stats(username)
