"""
caption.py
----------
Generates the Instagram caption for a chess puzzle post.
"""

import random

_OPENERS = [
    "Your move.",
    "Think you can crack it?",
    "Find the best continuation.",
    "Only one path leads to victory.",
    "Can you spot the winning idea?",
    "Solve before you scroll.",
    "This one trips up most players.",
]

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

_DIFFICULTY_HASHTAGS: dict[str, list[str]] = {
    "Beginner":     ["#chessbeginners", "#learnchess", "#chesskids"],
    "Intermediate": ["#chessplayer", "#chesstraining", "#chesspuzzle"],
    "Advanced":     ["#chessadvanced", "#chessimprovement", "#tacticalchess"],
    "Expert":       ["#chessexpert", "#chessmasters", "#chesstactics"],
    "Master":       ["#chessgrandmaster", "#elitechess", "#chessmasters"],
}

_BASE_HASHTAGS = [
    "#chess", "#chessdaily", "#dailypuzzle", "#chesscom",
    "#lichess", "#chesslife", "#chesslove", "#chesscommunity",
    "#chessgame", "#chessboard", "#chessislife",
]


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


def build_caption(puzzle: dict) -> str:
    """Return a ready-to-post Instagram caption string."""
    rating      = puzzle.get("Rating", "1500")
    themes      = puzzle.get("Themes", "").split()
    puzzle_id   = puzzle.get("PuzzleId", "")
    moves_uci   = puzzle.get("Moves", "").split()

    difficulty  = _difficulty_label(rating)
    opener      = random.choice(_OPENERS)
    theme_line  = _theme_line(themes)

    # Number of moves in the solution (all moves minus the opponent's first move)
    n_solution_moves = max(0, len(moves_uci) - 1)
    move_hint = f"Solution: {n_solution_moves} move{'s' if n_solution_moves != 1 else ''}" \
                if n_solution_moves > 0 else ""

    # Hashtags
    diff_tags   = random.sample(_DIFFICULTY_HASHTAGS.get(difficulty, []), k=min(2, len(_DIFFICULTY_HASHTAGS.get(difficulty, []))))
    theme_tags  = [f"#{t}" for t in themes if t not in ("puzzleId",)][:3]
    all_tags    = list(dict.fromkeys(_BASE_HASHTAGS + diff_tags + theme_tags))  # dedup, keep order
    hashtag_str = " ".join(all_tags[:20])  # Instagram cap is 30, stay safe

    lines = [
        opener,
        "",
        theme_line,
        move_hint,
        f"Difficulty: {difficulty}  |  Rating: {rating}",
        "",
        f"Solution in the comments tomorrow.",
        f"Practice on Lichess: lichess.org/training/{puzzle_id}",
        "",
        hashtag_str,
    ]

    return "\n".join(line for line in lines if line is not None)
