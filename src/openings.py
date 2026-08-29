"""
openings.py
-----------
Chess opening of the day for Instagram posts.

Each opening includes:
  - name: opening name
  - moves: main line moves
  - idea: brief explanation
  - level: who should play it
"""

from datetime import datetime

OPENINGS: list[dict[str, str]] = [
    {
        "name": "Sicilian Defense",
        "moves": "1. e4 c5",
        "idea": "The most popular response to 1. e4. Black fights for the center and creates an asymmetric position full of tactical chances.",
        "level": "All levels"
    },
    {
        "name": "Queen's Gambit",
        "moves": "1. d4 d5 2. c4",
        "idea": "White offers a pawn to gain central control. Black can accept (dxc4) or decline with solid setups.",
        "level": "All levels"
    },
    {
        "name": "Italian Game",
        "moves": "1. e4 e5 2. Nf3 Nc6 3. Bc4",
        "idea": "One of the oldest openings. White develops quickly and targets the f7 square.",
        "level": "Beginner"
    },
    {
        "name": "Ruy Lopez",
        "moves": "1. e4 e5 2. Nf3 Nc6 3. Bb5",
        "idea": "The 'Spanish Game' — White puts pressure on the knight defending e5. A favorite of World Champions.",
        "level": "Intermediate"
    },
    {
        "name": "French Defense",
        "moves": "1. e4 e6",
        "idea": "A solid, strategic response. Black builds a strong pawn chain and counterattacks in the center.",
        "level": "Intermediate"
    },
    {
        "name": "Caro-Kann Defense",
        "moves": "1. e4 c6",
        "idea": "Solid and reliable. Black prepares d5 to challenge the center without creating weaknesses.",
        "level": "Intermediate"
    },
    {
        "name": "King's Indian Defense",
        "moves": "1. d4 Nf6 2. c4 g6",
        "idea": "A hypermodern defense. Black allows White to build a center, then counterattacks it.",
        "level": "Advanced"
    },
    {
        "name": "Nimzo-Indian Defense",
        "moves": "1. d4 Nf6 2. c4 e6 3. Nc3 Bb4",
        "idea": "Black pins the knight and creates immediate tension. One of the most respected defenses.",
        "level": "Advanced"
    },
    {
        "name": "Scotch Game",
        "moves": "1. e4 e5 2. Nf3 Nc6 3. d4",
        "idea": "White immediately opens the center. Kasparov revived this opening at the top level.",
        "level": "Intermediate"
    },
    {
        "name": "Vienna Game",
        "moves": "1. e4 e5 2. Nc3",
        "idea": "A flexible system where White can transpose to gambits or solid positions.",
        "level": "Intermediate"
    },
    {
        "name": "English Opening",
        "moves": "1. c4",
        "idea": "A flank opening that controls d5 without committing the central pawns. Very flexible.",
        "level": "Intermediate"
    },
    {
        "name": "Reti Opening",
        "moves": "1. Nf3",
        "idea": "A hypermodern approach — White controls the center with pieces rather than pawns.",
        "level": "Advanced"
    },
    {
        "name": "Pirc Defense",
        "moves": "1. e4 d6 2. d4 Nf6 3. Nc3 g6",
        "idea": "Black lets White build a big center, then attacks it with pieces and pawns.",
        "level": "Advanced"
    },
    {
        "name": "Alekhine's Defense",
        "moves": "1. e4 Nf6",
        "idea": "Black provokes White's pawns forward, then attacks the overextended center.",
        "level": "Advanced"
    },
    {
        "name": "Owen's Defense",
        "moves": "1. e4 b6",
        "idea": "A rare, hypermodern setup. Black fianchettoes the bishop and controls the center from afar.",
        "level": "Advanced"
    },
    {
        "name": "Larsen's Opening",
        "moves": "1. b3",
        "idea": "White fianchettoes the bishop and plays flexibly. Named after Danish GM Bent Larsen.",
        "level": "Intermediate"
    },
    {
        "name": "Bird's Opening",
        "moves": "1. f4",
        "idea": "A aggressive flank opening. White controls e5 and prepares kingside attack.",
        "level": "Intermediate"
    },
    {
        "name": "Sokolsky Opening",
        "moves": "1. b4",
        "idea": "An uncommon opening aiming to control c5 and develop the bishop to b2.",
        "level": "Advanced"
    },
    {
        "name": "Van Geet Opening",
        "moves": "1. Nc3",
        "idea": "A rare, flexible system. White develops the knight and keeps options open.",
        "level": "Advanced"
    },
    {
        "name": "Four Knights Game",
        "moves": "1. e4 e5 2. Nf3 Nc6 3. Nc3 Nf6",
        "idea": "Both sides develop all four knights. Solid and symmetrical, but can lead to sharp play.",
        "level": "Beginner"
    },
    {
        "name": "Philidor Defense",
        "moves": "1. e4 e5 2. Nf3 d6",
        "idea": "A solid but passive defense. Black supports e5 but blocks the bishop.",
        "level": "Beginner"
    },
    {
        "name": "Petrov's Defense",
        "moves": "1. e4 e5 2. Nf3 Nf6",
        "idea": "A solid, symmetrical defense. Popular at top level for its drawing tendencies.",
        "level": "Intermediate"
    },
    {
        "name": "Scandinavian Defense",
        "moves": "1. e4 d5",
        "idea": "Black immediately challenges the center. Simple to learn but slightly inferior for Black.",
        "level": "Beginner"
    },
    {
        "name": "Center Game",
        "moves": "1. e4 e5 2. d4 exd4 3. Qxd4",
        "idea": "White recaptures with the queen early. Simple but gives Black easy development.",
        "level": "Beginner"
    },
    {
        "name": "Danish Gambit",
        "moves": "1. e4 e5 2. d4 exd4 3. c3",
        "idea": "White sacrifices pawns for rapid development and open lines. Aggressive but risky.",
        "level": "Intermediate"
    },
    {
        "name": "King's Gambit",
        "moves": "1. e4 e5 2. f4",
        "idea": "One of the oldest and most aggressive openings. White sacrifices a pawn for attack.",
        "level": "Intermediate"
    },
    {
        "name": "Evans Gambit",
        "moves": "1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. b4",
        "idea": "White sacrifices a pawn to gain time and open lines. A favorite of Morphy and Kasparov.",
        "level": "Intermediate"
    },
    {
        "name": "Two Knights Defense",
        "moves": "1. e4 e5 2. Nf3 Nc6 3. Bc4 Nf6",
        "idea": "Black immediately attacks e4. Leads to sharp, tactical positions.",
        "level": "Intermediate"
    },
    {
        "name": "Bishop's Opening",
        "moves": "1. e4 e5 2. Bc4",
        "idea": "White develops the bishop early, targeting f7. Flexible system with many options.",
        "level": "Beginner"
    },
    {
        "name": "London System",
        "moves": "1. d4 d5 2. Nf3 Nf6 3. Bf4",
        "idea": "A solid, universal system. White develops naturally without studying specific theory.",
        "level": "Beginner"
    },
]


def get_opening_of_the_day() -> dict:
    """Select an opening based on the day of year (rotates daily)."""
    day_of_year = datetime.now().timetuple().tm_yday
    idx = day_of_year % len(OPENINGS)
    return OPENINGS[idx]
