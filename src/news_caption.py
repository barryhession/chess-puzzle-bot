"""
news_caption.py
---------------
Caption and comment builder for chess news digest posts.

Generates:
  - Instagram caption with numbered headlines + hashtags
  - One comment per story with original source URL (preserved for audit)
"""

import random

# ── Hashtags ───────────────────────────────────────────────────────────────────
_BASE_HASHTAGS = [
    "#chess",
    "#chesstactics",
    "#chessnews",
    "#chesscom",
    "#fide",
    "#lichess",
    "#chessplayer",
    "#chesstournament",
    "#chessgrandmaster",
    "#chessmoves",
    "#chessboard",
    "#chessstrategy",
    "#chessgame",
    "#chesslove",
    "#chessclub",
    "#chesstraining",
    "#chesspuzzle",
    "#chessworld",
    "#chesslife",
    "#chessmaster",
]


def build_news_caption(stories: list[dict]) -> str:
    """
    Generate an Instagram caption for a news digest post.

    Includes:
      - Teaser line
      - Numbered paraphrased headlines
      - Source links teaser
      - Contact CTA
      - Hashtags
    """
    lines = [
        "Chess news worth your time:",
        "",
    ]

    for i, story in enumerate(stories, 1):
        lines.append(f"{i}. {story['title']}")

    lines.extend([
        "",
        "Source links in the comments below.",
        "Questions? DM us anytime.",
        "",
    ])

    # Shuffle and cap hashtags
    hashtags = list(_BASE_HASHTAGS)
    random.shuffle(hashtags)
    hashtags = hashtags[:20]
    lines.append(" ".join(hashtags))

    return "\n".join(lines)


def build_news_comments(stories: list[dict]) -> list[str]:
    """
    Generate one comment per story with the original source URL.

    Returns a list of comment strings, one per story.
    These should be posted in order after the feed post.
    """
    comments = []
    for i, story in enumerate(stories, 1):
        comment = f"Story {i}: {story['url']}"
        comments.append(comment)
    return comments
