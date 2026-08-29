"""
caption.py
----------
Generates the Instagram caption for a chess puzzle post.
"""

import random
import sqlite3
from datetime import datetime
from pathlib import Path

# ── Openers by time of day ────────────────────────────────────────────────────
_TIME_OPENERS: dict[int, list[str]] = {
    8:  ["Morning puzzle to start your day.",
         "Rise and solve.",
         "Coffee + chess = perfect morning."],
    12: ["Lunchtime challenge.",
         "Midday puzzle break.",
         "Quick tactical break before lunch."],
    17: ["Afternoon puzzle.",
         "Time for a tactical break.",
         "End the workday with a solve."],
    21: ["Evening puzzle before bed.",
         "End the day with a solve.",
         "One puzzle before sleep."],
}

_FALLBACK_OPENERS = [
    "Your move.",
    "Think you can crack it?",
    "Find the best continuation.",
    "Only one path leads to victory.",
    "Can you spot the winning idea?",
    "Solve before you scroll.",
    "This one trips up most players.",
]

# ── Theme labels ──────────────────────────────────────────────────────────────
_THEME_LABELS: dict[str, str] = {
    "mate":              "Checkmate in sight",
    "mateIn1":          "Mate in 1",
    "mateIn2":          "Mate in 2",
    "mateIn3":          "Mate in 3",
    "mateIn4":          "Mate in 4",
    "mateIn5":          "Mate in 5+",
    "fork":             "Fork",
    "pin":              "Pin",
    "skewer":           "Skewer",
    "discoveredAttack": "Discovered attack",
    "doubleCheck":      "Double check",
    "sacrifice":        "Sacrifice",
    "deflection":       "Deflection",
    "decoy":            "Decoy",
    "zugzwang":         "Zugzwang",
    "endgame":          "Endgame",
    "opening":          "Opening trap",
    "middlegame":       "Middlegame",
    "quietMove":        "Quiet move",
    "promotion":        "Promotion",
    "underPromotion":   "Underpromotion",
    "hangingPiece":     "Hanging piece",
    "trappedPiece":     "Trapped piece",
    "xRayAttack":       "X-ray attack",
    "attackingF2F7":    "Attack on f2/f7",
    "backRankMate":     "Back-rank mate",
    "smotheredMate":    "Smothered mate",
    "bodenMate":        "Boden's mate",
    "anastasiasMate":   "Anastasia's mate",
}

# ── Difficulty hashtags ───────────────────────────────────────────────────────
_DIFFICULTY_HASHTAGS: dict[str, list[str]] = {
    "Beginner":     ["#chessbeginners", "#learnchess", "#chesskids"],
    "Intermediate": ["#chessplayer", "#chesstraining", "#chesspuzzle"],
    "Advanced":     ["#chessadvanced", "#chessimprovement", "#tacticalchess"],
    "Expert":       ["#chessexpert", "#chessmasters", "#chesstactics"],
    "Master":       ["#chessgrandmaster", "#elitechess", "#chessmasters"],
}

# ── Chess quotes (20% chance to include) ─────────────────────────────────────
_QUOTES: list[tuple[str, str]] = [
    ("Chess is the gymnasium of the mind.", "Blaise Pascal"),
    ("Every chess master was once a beginner.", "Irving Chernev"),
    ("Chess is the struggle against the error.", "Johannes Zukertort"),
    ("Chess is mental torture.", "Garry Kasparov"),
    ("Chess helps you to concentrate.", "Anatoly Karpov"),
    ("I like the moment when I break a man's ego.", "Bobby Fischer"),
    ("Life is like a game of chess.", "George Bernard Shaw"),
    ("Chess is the art of analysis.", "Mikhail Botvinnik"),
    ("Chess is the register of ambition.", "Mikhail Tal"),
    ("Chess is the sport of the intellect.", "Emanuel Lasker"),
    ("Chess is the test of a gentleman.", "Emanuel Lasker"),
    ("The essence of chess is thinking about what chess is.", "David Bronstein"),
    ("Chess is a game of kings.", "Unknown"),
    ("A chess game is a dialogue between two players.", "Unknown"),
    ("Chess is the art of knowing yourself.", "Unknown"),
    ("Chess is war over the board.", "Bobby Fischer"),
    ("Chess is the most intelligent sport.", "Garry Kasparov"),
    ("Chess is a game of patience.", "Johannes Zukertort"),
    ("All I want to do is play chess.", "Bobby Fischer"),
    ("Chess is the poetry of logic.", "Unknown"),
]

# ── Hashtag rotation sets ─────────────────────────────────────────────────────
_HASHTAG_SETS: list[list[str]] = [
    ["#chess", "#chesspuzzle", "#lichess", "#dailypuzzle", "#chessdaily",
     "#chesslife", "#chesslove", "#chesscommunity"],
    ["#chesstactics", "#chessboard", "#chessmaster", "#chessgame",
     "#chessislife", "#chessclub", "#chessstrategy"],
    ["#chessplayer", "#chesstraining", "#chesscom", "#chessworld",
     "#chessmaster", "#chessmoves", "#chessgame"],
    ["#chessdaily", "#chesslove", "#chesscommunity", "#chessboard",
     "#chessislife", "#chesspuzzle", "#chesslife"],
]

# ── Database path ─────────────────────────────────────────────────────────────
_DB_PATH = Path(__file__).parent.parent / "used_puzzles.db"


def _difficulty_label(rating: str) -> str:
    try:
        r = int(rating)
    except ValueError:
        return "Intermediate"
    if r < 1200:
        return "Beginner"
    if r < 1500:
        return "Intermediate"
    if r < 1800:
        return "Advanced"
    if r < 2100:
        return "Expert"
    return "Master"


def _theme_line(themes: list[str]) -> str:
    labels = []
    for t in themes:
        if t in _THEME_LABELS:
            labels.append(_THEME_LABELS[t])
    if labels:
        return "Theme: " + " · ".join(labels[:2])
    return ""


def _time_opener() -> str:
    """Select opener based on current hour (8, 12, 17, 21)."""
    hour = datetime.now().hour
    # Find the closest scheduled hour
    scheduled = sorted(_TIME_OPENERS.keys())
    closest = min(scheduled, key=lambda h: abs(h - hour))
    if abs(closest - hour) <= 2:
        return random.choice(_TIME_OPENERS[closest])
    return random.choice(_FALLBACK_OPENERS)


def _puzzle_stats() -> str:
    """Query used_puzzles.db for stats."""
    if not _DB_PATH.exists():
        return ""
    try:
        conn = sqlite3.connect(str(_DB_PATH))
        row = conn.execute(
            "SELECT COUNT(*), ROUND(AVG(CAST(rating AS INTEGER)), 0) "
            "FROM used_puzzles WHERE rating IS NOT NULL AND rating != ''"
        ).fetchone()
        conn.close()
        if row and row[0] > 0:
            count, avg_rating = row[0], row[1]
            return f"📊 {count} puzzles posted | Avg rating: {int(avg_rating)}"
    except Exception:
        pass
    return ""


def _rotating_hashtags() -> list[str]:
    """Select hashtag set based on day of year (rotates daily)."""
    day_of_year = datetime.now().timetuple().tm_yday
    idx = day_of_year % len(_HASHTAG_SETS)
    return _HASHTAG_SETS[idx]


def build_caption(puzzle: dict, hour: int | None = None) -> str:
    """Return a ready-to-post Instagram caption string."""
    rating      = puzzle.get("Rating", "1500")
    themes      = puzzle.get("Themes", "").split()
    puzzle_id   = puzzle.get("PuzzleId", "")
    moves_uci   = puzzle.get("Moves", "").split()

    difficulty  = _difficulty_label(rating)
    opener      = _time_opener() if hour is None else random.choice(
        _TIME_OPENERS.get(hour, _FALLBACK_OPENERS)
    )
    theme_line  = _theme_line(themes)

    # Number of moves in the solution (all moves minus the opponent's first move)
    n_solution_moves = max(0, len(moves_uci) - 1)
    move_hint = f"Solution: {n_solution_moves} move{'s' if n_solution_moves != 1 else ''}" \
                if n_solution_moves > 0 else ""

    # Hashtags — rotate daily + difficulty + theme
    base_tags   = _rotating_hashtags()
    diff_tags   = random.sample(
        _DIFFICULTY_HASHTAGS.get(difficulty, []),
        k=min(2, len(_DIFFICULTY_HASHTAGS.get(difficulty, [])))
    )
    theme_tags  = [f"#{t}" for t in themes if t not in ("puzzleId",)][:3]
    all_tags    = list(dict.fromkeys(base_tags + diff_tags + theme_tags))
    hashtag_str = " ".join(all_tags[:20])

    # Stats
    stats = _puzzle_stats()

    # Quote (20% chance)
    quote_line = ""
    if random.random() < 0.2:
        quote, author = random.choice(_QUOTES)
        quote_line = f'"{quote}" — {author}'

    lines = [
        opener,
        "",
        quote_line,
        theme_line,
        move_hint,
        f"Difficulty: {difficulty}  |  Rating: {rating}",
    ]

    if stats:
        lines.append(stats)

    lines.extend([
        "",
        "Solution revealed in the comments soon.",
        f"🔗 Solve it: https://lichess.org/training/{puzzle_id}",
        "",
        hashtag_str,
    ])

    return "\n".join(line for line in lines if line is not None)
