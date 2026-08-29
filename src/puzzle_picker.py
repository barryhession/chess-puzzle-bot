"""
puzzle_picker.py
----------------
Selects a random, unused Lichess puzzle from the local CSV database,
respecting rating and theme filters from environment variables.

Lichess puzzle CSV columns (as of 2024):
  PuzzleId, FEN, Moves, Rating, RatingDeviation, Popularity,
  NbPlays, Themes, GameUrl, OpeningTags
"""

import csv
import os
import random
import sqlite3
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Config (from environment)
# ---------------------------------------------------------------------------
RATING_MIN = int(os.getenv("PUZZLE_RATING_MIN", "") or "1200")
RATING_MAX = int(os.getenv("PUZZLE_RATING_MAX", "") or "2200")
_raw_themes = os.getenv("PUZZLE_THEMES", "").strip()
REQUIRED_THEMES: list[str] = [t.strip() for t in _raw_themes.split(",") if t.strip()]

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
PUZZLES_DIR = BASE_DIR / "puzzles"
DB_PATH = BASE_DIR / "used_puzzles.db"


def _find_csv() -> Path:
    """Return the first .csv file found in the puzzles/ directory."""
    csvs = list(PUZZLES_DIR.glob("*.csv"))
    if not csvs:
        raise FileNotFoundError(
            "No puzzle CSV found in puzzles/. "
            "Download it from https://database.lichess.org/#puzzles and place it there."
        )
    return csvs[0]


# ---------------------------------------------------------------------------
# Used-puzzle tracking (SQLite)
# ---------------------------------------------------------------------------
def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS used_puzzles "
        "(puzzle_id TEXT PRIMARY KEY, used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.commit()
    return conn


def _is_used(conn: sqlite3.Connection, puzzle_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM used_puzzles WHERE puzzle_id = ?", (puzzle_id,)
    ).fetchone()
    return row is not None


def mark_used(puzzle_id: str) -> None:
    """Record a puzzle as used so it won't be picked again."""
    conn = _get_db()
    conn.execute(
        "INSERT OR IGNORE INTO used_puzzles (puzzle_id) VALUES (?)", (puzzle_id,)
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Puzzle selection
# ---------------------------------------------------------------------------
def _matches_filters(row: dict) -> bool:
    try:
        rating = int(row["Rating"])
    except (ValueError, KeyError):
        return False
    if not (RATING_MIN <= rating <= RATING_MAX):
        return False
    if REQUIRED_THEMES:
        puzzle_themes = row.get("Themes", "").split()
        if not any(t in puzzle_themes for t in REQUIRED_THEMES):
            return False
    return True


def pick_puzzle(sample_size: int = 5000) -> dict:
    """
    Return a random unused puzzle dict that satisfies the configured filters.

    Strategy: reservoir-sample `sample_size` matching rows from the CSV
    (avoids loading millions of rows into RAM), then pick one that hasn't
    been used yet.  Falls back to used puzzles if everything has been seen.
    """
    csv_path = _find_csv()
    conn = _get_db()

    reservoir: list[dict] = []
    seen = 0

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not _matches_filters(row):
                continue
            seen += 1
            if len(reservoir) < sample_size:
                reservoir.append(dict(row))
            else:
                # Reservoir sampling (Algorithm R)
                j = random.randint(0, seen - 1)
                if j < sample_size:
                    reservoir[j] = dict(row)

    if not reservoir:
        raise RuntimeError(
            "No puzzles matched the current filters "
            f"(rating {RATING_MIN}–{RATING_MAX}, themes={REQUIRED_THEMES}). "
            "Try widening PUZZLE_RATING_MIN / PUZZLE_RATING_MAX."
        )

    random.shuffle(reservoir)

    # Prefer unused; fall back to any if all have been used
    unused = [p for p in reservoir if not _is_used(conn, p["PuzzleId"])]
    pool = unused if unused else reservoir

    conn.close()
    return random.choice(pool)
