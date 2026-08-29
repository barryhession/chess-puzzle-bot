"""
backfill.py
-----------
One-time script to backfill media IDs for posts made before solution comments
were implemented. Safe to run multiple times (uses INSERT OR REPLACE).

Run this locally or add as a step in GitHub Actions once.
"""

import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path(__file__).parent / "used_puzzles.db"

conn = sqlite3.connect(DB_PATH)
conn.execute(
    "CREATE TABLE IF NOT EXISTS used_puzzles "
    "(puzzle_id TEXT PRIMARY KEY, "
    " used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
    " media_id TEXT, "
    " solution_posted INTEGER DEFAULT 0)"
)
existing = {row[1] for row in conn.execute("PRAGMA table_info(used_puzzles)")}
if "media_id" not in existing:
    conn.execute("ALTER TABLE used_puzzles ADD COLUMN media_id TEXT")
if "solution_posted" not in existing:
    conn.execute("ALTER TABLE used_puzzles ADD COLUMN solution_posted INTEGER DEFAULT 0")

posts = [
    ("def456", "18133144768711944", "2026-08-29 15:17:42"),
    ("laU3o",  "18087113606678668", "2026-08-29 15:37:44"),
    ("AU05b",  "18066495470753711", "2026-08-29 17:17:00"),
    ("0ERUy",  "18128646610668936", "2026-08-29 17:36:00"),
]

for puzzle_id, media_id, used_at in posts:
    conn.execute(
        "INSERT OR REPLACE INTO used_puzzles (puzzle_id, media_id, solution_posted, used_at) "
        "VALUES (?, ?, 0, ?)",
        (puzzle_id, media_id, used_at),
    )
    print(f"Backfilled: {puzzle_id} -> {media_id}")

conn.commit()
conn.close()
print("Backfill complete.")
