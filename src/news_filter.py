"""
news_filter.py
--------------
Content safety filter for chess news.

Core principle: "When in doubt, skip."

Rejects stories containing:
  - cheating allegations, scandals, legal disputes
  - deaths, obituaries, suicides
  - rumours, gossip, unconfirmed reports
  - political content, crimes, fraud
  - sexual content, harassment, abuse
  - any uncertain or flagged material

Freshness: stories older than 7 days are rejected.
"""

import re
from datetime import datetime, timezone

FRESHNESS_WINDOW_DAYS = 7

# ── Hard block patterns — ALWAYS rejected ──────────────────────────────────────
# Word boundaries (\b) prevent false positives like "Award" matching "war"
_HARD_BLOCK = [
    r"\bcheat",
    r"caught cheating",
    r"\bscandal",
    r"\bcontroversy",
    r"\blawsuit",
    r"legal action",
    r"\bcourt\b",
    r"\bcharged\b",
    r"\bdeath\b",
    r"\bdied\b",
    r"passed away",
    r"\bobituary",
    r"\balleg",
    r"\baccused",
    r"\ballegation",
    r"\bbanned?\b",
    r"\bsuspension\b",
    r"\binvestigation\b",
    r"under investigation",
    r"\bresign",
    r"\bresignation",
    r"\bwar\b",
    r"\bconflict\b",
    r"\bpolitical\b",
    r"\bcrime\b",
    r"\bcriminal\b",
    r"\bfraud\b",
    r"\brumou?r\b",
    r"\bgossip\b",
    r"\bsuicide\b",
    r"self.harm",
    r"\bsexual\b",
    r"\bharass",
    r"\babuse\b",
]

# ── Soft flag patterns — rejected and logged for review ────────────────────────
_SOFT_FLAG = [
    r"\bdispute\b",
    r"\bcontroversial\b",
    r"\bquestionable\b",
    r"\bunconfirmed\b",
    r"\breportedly\b",
    r"\ballegedly\b",
]


def is_safe(story: dict) -> tuple[bool, str]:
    """
    Evaluate whether a story is safe to publish.

    Returns:
        (True, "safe") if the story passes all checks.
        (False, "reason") if the story should be skipped.

    When in doubt: returns (False, "skipped: uncertain").
    """
    text = f"{story.get('title', '')} {story.get('summary', '')}".lower()

    # ── Hard block check ──────────────────────────────────────────────────────
    for pattern in _HARD_BLOCK:
        if re.search(pattern, text):
            return False, f"hard block: {pattern}"

    # ── Soft flag check ───────────────────────────────────────────────────────
    for pattern in _SOFT_FLAG:
        if re.search(pattern, text):
            return False, f"soft flag: {pattern}"

    # ── Freshness check ───────────────────────────────────────────────────────
    date_str = story.get("date")
    if not date_str or date_str == "unknown":
        return False, "skipped: no date"
    try:
        story_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - story_date).days
        if age_days > FRESHNESS_WINDOW_DAYS:
            return False, f"stale: {age_days} days old"
    except ValueError:
        return False, "skipped: unparseable date"

    # ── Summary quality check ─────────────────────────────────────────────────
    summary = story.get("summary", "")
    if len(summary) < 20:
        return False, "skipped: summary too short"

    return True, "safe"


def filter_stories(stories: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Filter a list of stories through the safety filter.

    Returns:
        (safe_stories, skipped_stories)

    Each skipped story gets an extra "reason" key.
    """
    safe = []
    skipped = []

    for story in stories:
        is_ok, reason = is_safe(story)
        if is_ok:
            safe.append(story)
        else:
            skipped.append({**story, "reason": reason})
            print(f"[news_filter] SKIPPED: {story.get('title', '?')[:60]} — {reason}")

    print(f"[news_filter] {len(safe)} safe, {len(skipped)} skipped")
    return safe, skipped
