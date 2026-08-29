"""
solution.py
-----------
Formats a chess puzzle solution as a readable Instagram comment.

Takes the puzzle dict (with FEN, Moves, Themes, PuzzleId) and returns
a multi-line comment string with:
  - Theme label (e.g. "Mate in 2", "Fork")
  - Numbered moves in Standard Algebraic Notation with brief descriptions
  - Full move line
  - Lichess practice link
  - Call to action
"""

import chess
import chess.pgn

# ---------------------------------------------------------------------------
# Theme label mapping
# ---------------------------------------------------------------------------
_THEME_LABELS: dict[str, str] = {
    "mateIn1":          "Mate in 1",
    "mateIn2":          "Mate in 2",
    "mateIn3":          "Mate in 3",
    "mateIn4":          "Mate in 4",
    "mateIn5":          "Mate in 5+",
    "mate":             "Checkmate",
    "fork":             "Fork",
    "pin":              "Pin",
    "skewer":           "Skewer",
    "discoveredAttack": "Discovered Attack",
    "doubleCheck":      "Double Check",
    "sacrifice":        "Sacrifice",
    "deflection":       "Deflection",
    "decoy":            "Decoy",
    "zugzwang":         "Zugzwang",
    "promotion":        "Promotion",
    "underPromotion":   "Underpromotion",
    "endgame":          "Endgame",
    "opening":          "Opening Trap",
    "middlegame":       "Middlegame",
    "backRankMate":     "Back-rank Mate",
    "smotheredMate":    "Smothered Mate",
    "hangingPiece":     "Hanging Piece",
    "trappedPiece":     "Trapped Piece",
    "xRayAttack":       "X-ray Attack",
    "quietMove":        "Quiet Move",
    "kingsideAttack":   "Kingside Attack",
    "queensideAttack":  "Queenside Attack",
    "attraction":       "Attraction",
    "clearance":        "Clearance",
    "interference":     "Interference",
    "crushing":         "Crushing Move",
}

# Brief descriptions to append to each move number
_MOVE_HINTS: dict[str, list[str]] = {
    "mateIn1":          ["delivering checkmate"],
    "mateIn2":          ["forcing the king out", "delivering checkmate"],
    "mateIn3":          ["tightening the net", "cutting off the king", "delivering checkmate"],
    "fork":             ["winning material with a fork", "collecting the piece"],
    "pin":              ["pinning the piece", "exploiting the pin"],
    "skewer":           ["skewering the pieces", "collecting material"],
    "sacrifice":        ["sacrificing for the attack", "following up the sacrifice"],
    "discoveredAttack": ["unleashing the discovered attack", "collecting material"],
    "promotion":        ["advancing the pawn", "queening for the win"],
    "backRankMate":     ["exploiting the back rank", "delivering checkmate"],
    "smotheredMate":    ["cutting off the king's escape", "delivering smothered mate"],
}

_GENERIC_HINTS = [
    "finding the best move",
    "following up accurately",
    "converting the advantage",
    "finishing the combination",
    "completing the tactic",
]


def _get_theme_label(themes: list[str]) -> str:
    """Return the best label for the puzzle themes."""
    priority = [
        "mateIn1", "mateIn2", "mateIn3", "mateIn4", "mateIn5",
        "smotheredMate", "backRankMate", "mate",
        "fork", "pin", "skewer", "sacrifice", "discoveredAttack",
        "deflection", "decoy", "promotion", "zugzwang",
        "attraction", "clearance", "interference",
        "kingsideAttack", "queensideAttack", "crushing",
        "endgame", "middlegame", "opening",
    ]
    for t in priority:
        if t in themes:
            return _THEME_LABELS.get(t, t)
    return "Tactical Puzzle"


def _get_move_hint(themes: list[str], move_index: int) -> str:
    """Return a brief description for a move at the given index."""
    for theme in ["mateIn1", "mateIn2", "mateIn3", "fork", "pin", "skewer",
                  "sacrifice", "discoveredAttack", "promotion",
                  "backRankMate", "smotheredMate"]:
        if theme in themes and theme in _MOVE_HINTS:
            hints = _MOVE_HINTS[theme]
            if move_index < len(hints):
                return hints[move_index]
    return _GENERIC_HINTS[move_index % len(_GENERIC_HINTS)]


def _uci_to_san_list(fen: str, uci_moves: list[str]) -> list[str]:
    """
    Convert a list of UCI moves to SAN strings starting from the given FEN.
    The first move in uci_moves is the opponent's move (already played in the puzzle).
    Returns only the solver's moves (every other move starting from index 1).
    """
    board = chess.Board(fen)
    san_moves = []
    for i, uci in enumerate(uci_moves):
        try:
            move = board.parse_uci(uci)
            san = board.san(move)
            board.push(move)
            san_moves.append(san)
        except (chess.InvalidMoveError, chess.IllegalMoveError):
            san_moves.append(uci)
    return san_moves


def format_solution_comment(puzzle: dict, full_puzzle_row: dict = None) -> str:
    """
    Format a solution comment for an Instagram post.

    Args:
        puzzle: dict with at least puzzle_id and optionally FEN/Moves/Themes
        full_puzzle_row: full CSV row dict if available (has FEN, Moves, Themes)

    Returns:
        Formatted comment string.
    """
    data = full_puzzle_row or puzzle
    fen       = data.get("FEN", "")
    moves_uci = data.get("Moves", "").split()
    themes    = data.get("Themes", "").split()
    puzzle_id = data.get("PuzzleId", puzzle.get("puzzle_id", ""))

    theme_label = _get_theme_label(themes)

    # Convert all moves to SAN
    all_san = _uci_to_san_list(fen, moves_uci)

    # The puzzle shows the position AFTER the opponent's first move.
    # So the solver's moves start at index 1 of moves_uci (index 1 of all_san).
    solver_san = all_san[1:]  # skip opponent's move

    # Build the full SAN line (opponent move + solution)
    full_line = " ".join(all_san)

    # Determine starting move number from FEN
    board = chess.Board(fen)
    start_move_num = board.fullmove_number
    # After opponent's move, it's the solver's turn
    if board.turn == chess.WHITE:
        # Opponent was black, so move number stays
        current_move_num = start_move_num
    else:
        # Opponent was white, move number increments
        current_move_num = start_move_num + 1

    # Build numbered move lines
    move_lines = []
    for i, san in enumerate(solver_san):
        hint = _get_move_hint(themes, i)
        # Determine move number
        move_num = current_move_num + i
        move_lines.append(f"{move_num}. {san} — {hint}")

    n_moves = len(solver_san)
    move_word = "move" if n_moves == 1 else "moves"

    lines = [
        f"Solution ({theme_label} — {n_moves} {move_word}):",
        "",
    ] + move_lines + [
        "",
        f"Full line: {full_line}",
        f"Practice: lichess.org/training/{puzzle_id}",
        "",
        "Did you get it? Let us know below!",
    ]

    return "\n".join(lines)
