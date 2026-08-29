"""
news_renderer.py
----------------
Renders a branded 1080×1350 Instagram graphic for chess news digests.

Layout:
  - Black background, gold accents, white text
  - @thechesssignal branding at top
  - "CHESS NEWS" title
  - Numbered list of stories with visible Source + Date
  - CTA and DM contact at bottom

Consistent with board_renderer.py style (same color palette, font handling).
"""

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ── Canvas dimensions (matches puzzle posts) ───────────────────────────────────
CANVAS_W = 1080
CANVAS_H = 1350

# ── Color palette ──────────────────────────────────────────────────────────────
BG_COLOR     = (18, 18, 18)
ACCENT       = (201, 160, 56)   # gold
TEXT_PRIMARY  = (255, 255, 255)  # white
TEXT_SECONDARY = (160, 160, 160) # grey
DIVIDER      = (60, 60, 60)     # subtle grey line

# ── Font loading (matches board_renderer.py) ───────────────────────────────────
_FONT_CANDIDATES_WINDOWS = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
_FONT_CANDIDATES_LINUX = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

_CACHE: dict[int, ImageFont.FreeTypeFont] = {}


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if size in _CACHE:
        return _CACHE[size]

    import sys
    candidates = _FONT_CANDIDATES_WINDOWS if sys.platform == "win32" else _FONT_CANDIDATES_LINUX
    for path in candidates:
        try:
            font = ImageFont.truetype(path, size)
            _CACHE[size] = font
            return font
        except Exception:
            continue

    font = ImageFont.load_default(size)
    _CACHE[size] = font
    return font


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines: list[str] = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines or [""]


def render_news_graphic(stories: list[dict], output_path: Path) -> Path:
    """
    Generate a branded 1080×1350 PNG with chess news stories.

    Args:
        stories: list of dicts with "title", "source", "date" keys
        output_path: where to save the PNG

    Returns:
        The output_path for convenience.
    """
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # ── Fonts ──────────────────────────────────────────────────────────────────
    font_brand   = _load_font(30)
    font_title   = _load_font(64)
    font_subtitle = _load_font(34)
    font_number  = _load_font(56)
    font_headline = _load_font(38)
    font_meta    = _load_font(28)
    font_cta     = _load_font(30)

    # ── Layout constants ───────────────────────────────────────────────────────
    margin_left = 80
    margin_right = 80
    content_width = CANVAS_W - margin_left - margin_right

    y = 80  # starting y position

    # ── Header: @thechesssignal ────────────────────────────────────────────────
    draw.text(
        (CANVAS_W // 2, y),
        "@thechesssignal",
        fill=ACCENT,
        font=font_brand,
        anchor="mt",
    )
    y += 60

    # ── Title: CHESS NEWS ──────────────────────────────────────────────────────
    draw.text(
        (CANVAS_W // 2, y),
        "CHESS NEWS",
        fill=TEXT_PRIMARY,
        font=font_title,
        anchor="mt",
    )
    y += 80

    # ── Subtitle ───────────────────────────────────────────────────────────────
    draw.text(
        (CANVAS_W // 2, y),
        f"{len(stories)} stories worth your time",
        fill=ACCENT,
        font=font_subtitle,
        anchor="mt",
    )
    y += 60

    # ── Divider line ───────────────────────────────────────────────────────────
    draw.line(
        [(margin_left, y), (CANVAS_W - margin_right, y)],
        fill=DIVIDER,
        width=2,
    )
    y += 40

    # ── Stories ────────────────────────────────────────────────────────────────
    for i, story in enumerate(stories, 1):
        # Number
        draw.text(
            (margin_left, y),
            f"{i}.",
            fill=ACCENT,
            font=font_number,
            anchor="lt",
        )

        # Headline (wrapped)
        headline_lines = _wrap_text(story["title"], font_headline, content_width - 60)
        headline_y = y + 4
        for line in headline_lines:
            draw.text(
                (margin_left + 50, headline_y),
                line,
                fill=TEXT_PRIMARY,
                font=font_headline,
                anchor="lt",
            )
            headline_y += 48

        # Source + Date
        source_text = f"Source: {story['source']}  ·  {story['date']}"
        draw.text(
            (margin_left + 50, headline_y + 4),
            source_text,
            fill=TEXT_SECONDARY,
            font=font_meta,
            anchor="lt",
        )
        y = headline_y + 50

        # Small gap between stories
        y += 30

    # ── Divider line ───────────────────────────────────────────────────────────
    y += 10
    draw.line(
        [(margin_left, y), (CANVAS_W - margin_right, y)],
        fill=DIVIDER,
        width=2,
    )
    y += 40

    # ── Footer: CTA ────────────────────────────────────────────────────────────
    draw.text(
        (CANVAS_W // 2, y),
        "Follow @thechesssignal",
        fill=ACCENT,
        font=font_cta,
        anchor="mt",
    )
    y += 50

    draw.text(
        (CANVAS_W // 2, y),
        "Questions? DM us",
        fill=TEXT_SECONDARY,
        font=font_meta,
        anchor="mt",
    )

    # ── Save ───────────────────────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(str(output_path), "PNG")
    print(f"[news_renderer] Saved: {output_path}")
    return output_path
