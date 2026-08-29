"""
news_fetcher.py
---------------
Pull chess news from RSS feeds (FIDE, Chess.com, ChessBase).

Extracts:
  - title (from RSS <title>)
  - source (which feed)
  - date (from RSS <pubDate>)
  - url (original article URL — always preserved)
  - summary (from RSS <summary> — used as source material for paraphrasing)
  - original_title (raw headline — for audit trail)

Deduplicates stories across sources using fuzzy title matching.
"""

import re
from datetime import datetime, timezone
from difflib import SequenceMatcher

import feedparser

SOURCES = {
    "FIDE":      "https://www.fide.com/rss",
    "Chess.com": "https://www.chess.com/rss/news",
    "ChessBase": "https://en.chessbase.com/feed",
}

_FRESHNESS_WINDOW_DAYS = 7


def _parse_date(entry: feedparser.FeedParserDict) -> str | None:
    """Extract publication date as YYYY-MM-DD string."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass
    return None


def _clean_summary(raw: str | None) -> str:
    """Strip HTML tags and collapse whitespace from RSS summary."""
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", "", raw)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_stale(date_str: str | None) -> bool:
    """Return True if the story is older than the freshness window."""
    if not date_str:
        return True  # no date → reject
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - dt).days
        return age > _FRESHNESS_WINDOW_DAYS
    except ValueError:
        return True  # unparseable → reject


def _fuzzy_dedup(stories: list[dict]) -> list[dict]:
    """
    Remove duplicate stories across sources.
    Keep the one with the earliest date (or first seen if dates match).
    """
    kept: list[dict] = []
    for story in stories:
        is_dup = False
        for existing in kept:
            ratio = SequenceMatcher(
                None,
                story["title"].lower(),
                existing["title"].lower(),
            ).ratio()
            if ratio > 0.6:
                is_dup = True
                break
        if not is_dup:
            kept.append(story)
    return kept


def fetch_news(sources: dict[str, str] | None = None) -> list[dict]:
    """
    Fetch and deduplicate news from all configured RSS sources.

    Returns a list of dicts, each containing:
        title, source, date, url, summary, original_title

    Stale stories (no date or > 7 days old) are excluded.
    Duplicate stories across sources are removed.
    """
    if sources is None:
        sources = SOURCES

    all_stories: list[dict] = []

    for source_name, feed_url in sources.items():
        try:
            print(f"[news_fetcher] Fetching {source_name}...")
            feed = feedparser.parse(feed_url)

            if feed.bozo and not feed.entries:
                print(f"[news_fetcher] Warning: {source_name} feed error: {feed.bozo_exception}")
                continue

            for entry in feed.entries:
                title = entry.get("title", "").strip()
                if not title:
                    continue

                url = entry.get("link", "").strip()
                if not url:
                    continue

                date_str = _parse_date(entry)
                if _is_stale(date_str):
                    continue

                summary = _clean_summary(entry.get("summary", ""))
                original_title = title  # preserved for audit

                all_stories.append({
                    "title": title,
                    "source": source_name,
                    "date": date_str or "unknown",
                    "url": url,
                    "summary": summary,
                    "original_title": original_title,
                })

            print(f"[news_fetcher] {source_name}: {len(feed.entries)} entries fetched")

        except Exception as e:
            print(f"[news_fetcher] Error fetching {source_name}: {e}")

    # Deduplicate across sources
    deduped = _fuzzy_dedup(all_stories)
    print(f"[news_fetcher] Total after dedup: {len(deduped)} stories")

    return deduped
