"""
books.py
--------
Chess book recommendations for Instagram posts.

Each book includes:
  - title: book title
  - author: author name
  - description: brief summary
  - level: Beginner / Intermediate / Advanced
"""

from datetime import datetime

BOOKS: list[dict[str, str]] = [
    # Beginner
    {
        "title": "Bobby Fischer Teaches Chess",
        "author": "Bobby Fischer",
        "description": "A beginner-friendly introduction to tactical chess. Perfect for new players.",
        "level": "Beginner"
    },
    {
        "title": "Chess Fundamentals",
        "author": "Jose Raul Capablanca",
        "description": "The 4th World Champion's guide to basic chess principles.",
        "level": "Beginner"
    },
    {
        "title": "Logical Chess: Move by Move",
        "author": "Irving Chernev",
        "description": "Explains every move in 33 complete games for developing players.",
        "level": "Beginner"
    },
    {
        "title": "The Complete Idiot's Guide to Chess",
        "author": "Patrick Wolff",
        "description": "A gentle introduction covering rules, tactics, and strategy.",
        "level": "Beginner"
    },
    {
        "title": "Chess for Dummies",
        "author": "James Eade",
        "description": "Covers everything from basics to tournament play.",
        "level": "Beginner"
    },
    # Intermediate
    {
        "title": "My System",
        "author": "Aron Nimzowitsch",
        "description": "Foundational book on positional chess. Changed how we think about strategy.",
        "level": "Intermediate"
    },
    {
        "title": "How to Reassess Your Chess",
        "author": "Jeremy Silman",
        "description": "Improves your thinking process and positional understanding.",
        "level": "Intermediate"
    },
    {
        "title": "The Complete Chess Course",
        "author": "Fred Reinfeld",
        "description": "A comprehensive guide from beginner to tournament player.",
        "level": "Intermediate"
    },
    {
        "title": "200 Modern Chess Puzzles",
        "author": "Graham Burgess",
        "description": "Tactical puzzles with varying difficulty for improvement.",
        "level": "Intermediate"
    },
    {
        "title": "Pawn Structure Chess",
        "author": "Andrew Soltis",
        "description": "Understanding how pawn structures shape the game.",
        "level": "Intermediate"
    },
    # Advanced
    {
        "title": "My Great Predecessors",
        "author": "Garry Kasparov",
        "description": "A deep analysis of the games of previous world champions.",
        "level": "Advanced"
    },
    {
        "title": "Dvoretsky's Endgame Manual",
        "author": "Mark Dvoretsky",
        "description": "The definitive guide to endgame technique for serious players.",
        "level": "Advanced"
    },
    {
        "title": "Life and Games of Mikhail Tal",
        "author": "Mikhail Tal",
        "description": "The 8th World Champion's autobiography and game collection.",
        "level": "Advanced"
    },
    {
        "title": "Zurich International 1953",
        "author": "David Bronstein",
        "description": "One of the greatest tournament books ever written.",
        "level": "Advanced"
    },
    {
        "title": "Systematic Chess Training",
        "author": "Pál Benkő",
        "description": "A structured approach to improving all aspects of your game.",
        "level": "Advanced"
    },
    # Classics
    {
        "title": "The Immortal Game",
        "author": "David Shenk",
        "description": "A history of chess and its cultural impact through the ages.",
        "level": "All Levels"
    },
    {
        "title": "The Queen's Gambit",
        "author": "Walter Tevis",
        "description": "The novel behind the Netflix series. A gripping chess fiction.",
        "level": "All Levels"
    },
    {
        "title": "Bobby Fischer Against the World",
        "author": "Elizabeth Spiegel",
        "description": "A biography of the most controversial chess champion.",
        "level": "All Levels"
    },
    {
        "title": "The Chess Artist",
        "author": "J.C. Hall",
        "description": "A journey through chess culture and beautiful compositions.",
        "level": "All Levels"
    },
    {
        "title": "King's Gambit",
        "author": "Paul Hoffman",
        "description": "An adventure story of chess, obsession, and genius.",
        "level": "All Levels"
    },
]


def get_book_of_the_week() -> dict:
    """Select a book based on the week of year (rotates weekly)."""
    from datetime import datetime
    now = datetime.now()
    week_of_year = now.isocalendar()[1]
    idx = week_of_year % len(BOOKS)
    return BOOKS[idx]


def get_book_by_level(level: str) -> dict | None:
    """Get a random book for a specific level."""
    import random
    matching = [b for b in BOOKS if b["level"] == level]
    if matching:
        return random.choice(matching)
    return None
