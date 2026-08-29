"""
chess_terms.py
--------------
Daily chess term explanations for Instagram posts.

Each term includes:
  - term: the chess term
  - definition: clear explanation
  - example: practical usage context
"""

from datetime import datetime

TERMS: list[dict[str, str]] = [
    {
        "term": "Zugzwang",
        "definition": "A position where any move worsens your position. You'd prefer to pass, but can't.",
        "example": "Common in endgames where the side to move loses."
    },
    {
        "term": "Pin",
        "definition": "A piece that cannot move without exposing a more valuable piece behind it.",
        "example": "A bishop pinning a knight to the king."
    },
    {
        "term": "Fork",
        "definition": "A single piece attacks two or more enemy pieces simultaneously.",
        "example": "A knight forking the king and queen."
    },
    {
        "term": "Skewer",
        "definition": "Like a pin, but reversed — the valuable piece is in front and must move, exposing the piece behind.",
        "example": "A bishop skewering a king and rook."
    },
    {
        "term": "Discovered Attack",
        "definition": "Moving one piece reveals an attack from another piece behind it.",
        "example": "Moving a knight reveals a bishop attack on the queen."
    },
    {
        "term": "Double Check",
        "definition": "Two pieces deliver check simultaneously. The king must move — no block or capture can stop both.",
        "example": "A knight and bishop both giving check."
    },
    {
        "term": "Sacrifice",
        "definition": "Giving up material intentionally for a tactical or positional advantage.",
        "example": "A queen sacrifice leading to checkmate."
    },
    {
        "term": "Deflection",
        "definition": "Forcing a defending piece away from its critical square.",
        "example": "Sacrificing a rook to pull the king away from defense."
    },
    {
        "term": "Decoy",
        "definition": "Luring an enemy piece to a specific square where it becomes vulnerable.",
        "example": "Sacrificing a queen to lure the king to a fatal square."
    },
    {
        "term": "Overloading",
        "definition": "A piece is tasked with too many defensive duties and cannot cover everything.",
        "example": "A rook defending both a knight and a back-rank mate."
    },
    {
        "term": "Back Rank Mate",
        "definition": "Checkmate on the first rank, where the king is trapped by its own pawns.",
        "example": "A rook delivering mate on the back rank."
    },
    {
        "term": "Smothered Mate",
        "definition": "A checkmate where the king is surrounded by its own pieces and cannot escape.",
        "example": "The classic Philidor position with knight mate."
    },
    {
        "term": "X-Ray Attack",
        "definition": "A piece attacks through another piece, influencing squares beyond it.",
        "example": "A rook attacking through an enemy rook to the piece behind."
    },
    {
        "term": "Outpost",
        "definition": "A square in enemy territory that cannot be attacked by pawns.",
        "example": "A knight on d5 supported by a pawn on c4."
    },
    {
        "term": "Passed Pawn",
        "definition": "A pawn with no enemy pawns blocking or guarding its path to promotion.",
        "example": "A pawn on the 7th rank with a clear path to queen."
    },
    {
        "term": "Fianchetto",
        "definition": "Developing a bishop to the long diagonal by placing it on b2 or g2.",
        "example": "The King's Indian setup with bishop on g2."
    },
    {
        "term": "Candidate Move",
        "definition": "A move that deserves further calculation before making a decision.",
        "example": "Always consider at least 2-3 candidate moves."
    },
    {
        "term": "Prophylaxis",
        "definition": "A move that prevents the opponent's plan before executing your own.",
        "example": "Playing h3 to prevent Ng4."
    },
    {
        "term": "Weak Square",
        "definition": "A square that can no longer be defended by pawns.",
        "example": "A hole on f6 after the g-pawn advances."
    },
    {
        "term": "Battery",
        "definition": "Two or more pieces lined up on the same file, rank, or diagonal.",
        "example": "Two rooks doubled on the d-file."
    },
    {
        "term": "Tempo",
        "definition": "A unit of time in chess — gaining a tempo means making a useful move while the opponent wastes one.",
        "example": "Developing with threat gains a tempo."
    },
    {
        "term": "Activity",
        "definition": "How well your pieces control squares and participate in the game.",
        "example": "Active rooks on open files are worth more."
    },
    {
        "term": "Space Advantage",
        "definition": "Controlling more squares than your opponent, especially in their territory.",
        "example": "Pawns on c5 and e5 claiming space."
    },
    {
        "term": "Weak Color Complex",
        "definition": "A group of squares of one color that can no longer be defended by pawns.",
        "example": "Dark-square weaknesses after trading the dark-squared bishop."
    },
    {
        "term": " zwischenzug",
        "definition": "An intermediate move that creates a threat before responding to the opponent's threat.",
        "example": "Instead of recapturing, playing a check first."
    },
    {
        "term": "Exchange",
        "definition": "Trading pieces of equal value, or sacrificing a rook for a bishop/knight (the 'exchange').",
        "example": "Winning the exchange means winning a rook for a minor piece."
    },
    {
        "term": "Two Bishops",
        "definition": "Having both bishops while your opponent has only one or none. A long-term advantage.",
        "example": "The bishop pair is worth roughly 0.5 pawns extra."
    },
    {
        "term": "Opposition",
        "definition": "When kings face each other with one square between, the side NOT to move has the opposition.",
        "example": "Critical in king and pawn endgames."
    },
    {
        "term": "Lucena Position",
        "definition": "A fundamental rook endgame where the stronger side can force a win.",
        "example": "Building a 'bridge' with the rook to shield the king."
    },
    {
        "term": "Philidor Position",
        "definition": "A defensive rook endgame technique to hold a draw against a pawn on the 7th rank.",
        "example": "Rook on the 3rd rank cutting off the enemy king."
    },
]


def get_term_of_the_day() -> dict:
    """Select a chess term based on the day of year (rotates daily)."""
    day_of_year = datetime.now().timetuple().tm_yday
    idx = day_of_year % len(TERMS)
    return TERMS[idx]
