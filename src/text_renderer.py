"""
text_renderer.py
----------------
Generic 1080×1350 text graphic renderer for chess content posts.

Renders:
  - Chess terms of the day
  - Historical events
  - Book recommendations
  - Chess openings of the day

Uses same visual style as news_renderer.py (black/gold/white branding).
"""

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ── Canvas dimensions ─────────────────────────────────────────────────────────
CANVAS_W = 1080
CANVAS_H = 1350

# ── Color palette (matches existing branding) ─────────────────────────────────
BG_COLOR      = (18, 18, 18)
ACCENT        = (201, 160, 56)   # gold
TEXT_PRIMARY   = (255, 255, 255)  # white
TEXT_SECONDARY = (160, 160, 160)  # grey
DIVIDER       = (60, 60, 60)     # subtle grey line

# ── Font loading ──────────────────────────────────────────────────────────────
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


def render_text_graphic(
    title: str,
    heading: str,
    body: str,
    subtitle: str = "",
    output_path: Path | None = None,
) -> Path:
    """
    Render a 1080×1350 text graphic.

    Args:
        title: header text (e.g. "CHESS TERM")
        heading: main heading (e.g. "Zugzwang")
        body: main body text
        subtitle: optional subtitle (e.g. "Level: Beginner")
        output_path: where to save the PNG

    Returns:
        The output path.
    """
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # ── Fonts ──────────────────────────────────────────────────────────────────
    font_brand    = _load_font(30)
    font_title    = _load_font(64)
    font_heading  = _load_font(52)
    font_body     = _load_font(34)
    font_subtitle = _load_font(30)
    font_cta      = _load_font(30)

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

    # ── Title: CHESS TERM / ON THIS DAY / BOOK OF THE WEEK ────────────────────
    draw.text(
        (CANVAS_W // 2, y),
        title,
        fill=TEXT_PRIMARY,
        font=font_title,
        anchor="mt",
    )
    y += 80

    # ── Divider line ───────────────────────────────────────────────────────────
    draw.line(
        [(margin_left, y), (CANVAS_W - margin_right, y)],
        fill=DIVIDER,
        width=2,
    )
    y += 50

    # ── Heading ────────────────────────────────────────────────────────────────
    heading_lines = _wrap_text(heading, font_heading, content_width)
    for line in heading_lines:
        draw.text(
            (CANVAS_W // 2, y),
            line,
            fill=ACCENT,
            font=font_heading,
            anchor="mt",
        )
        y += 65

    y += 20

    # ── Body ───────────────────────────────────────────────────────────────────
    body_lines = _wrap_text(body, font_body, content_width)
    for line in body_lines:
        draw.text(
            (margin_left, y),
            line,
            fill=TEXT_PRIMARY,
            font=font_body,
            anchor="lt",
        )
        y += 48

    # ── Subtitle (if provided) ─────────────────────────────────────────────────
    if subtitle:
        y += 20
        draw.text(
            (margin_left, y),
            subtitle,
            fill=TEXT_SECONDARY,
            font=font_subtitle,
            anchor="lt",
        )
        y += 50

    # ── Footer ─────────────────────────────────────────────────────────────────
    y = CANVAS_H - 120

    draw.line(
        [(margin_left, y), (CANVAS_W - margin_right, y)],
        fill=DIVIDER,
        width=2,
    )
    y += 40

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
        font=font_subtitle,
        anchor="mt",
    )

    # ── Save ───────────────────────────────────────────────────────────────────
    if output_path is None:
        output_path = Path("output") / "text_graphic.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(str(output_path), "PNG")
    print(f"[text_renderer] Saved: {output_path}")
    return output_path


def render_chess_term(term_data: dict, output_path: Path | None = None) -> Path:
    """Render a chess term graphic."""
    if output_path is None:
        output_path = Path("output") / "chess_term.png"

    title = "CHESS TERM"
    heading = term_data["term"]
    body = term_data["definition"]
    subtitle = term_data.get("example", "")

    return render_text_graphic(title, heading, body, subtitle, output_path)


def render_historical_event(event_data: dict, output_path: Path | None = None) -> Path:
    """Render a historical event graphic."""
    if output_path is None:
        output_path = Path("output") / "history.png"

    title = "ON THIS DAY"
    # Parse date from "08-29" format to "August 29"
    month, day = event_data["date"].split("-")
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    heading = f"{months[int(month)-1]} {int(day)}"
    body = event_data["event"]
    subtitle = event_data.get("detail", "")

    return render_text_graphic(title, heading, body, subtitle, output_path)


def render_book(book_data: dict, output_path: Path | None = None) -> Path:
    """Render a book recommendation graphic."""
    if output_path is None:
        output_path = Path("output") / "book.png"

    title = "BOOK OF THE WEEK"
    heading = book_data["title"]
    body = book_data["description"]
    subtitle = f"by {book_data['author']}  ·  {book_data['level']}"

    return render_text_graphic(title, heading, body, subtitle, output_path)


def render_opening(opening_data: dict, output_path: Path | None = None) -> Path:
    """Render a chess opening graphic with board position."""
    from src.opening_renderer import render_opening_with_board
    if output_path is None:
        output_path = Path("output") / "opening.png"
    return render_opening_with_board(opening_data, board_size=720, output_path=output_path)


def render_opening_stories(opening_data: dict, output_path: Path | None = None) -> Path:
    """Render a chess opening graphic padded to 1080×1920 for Stories."""
    from src.opening_renderer import render_opening_with_board
    if output_path is None:
        output_path = Path("output") / "opening_stories.png"
    render_opening_with_board(opening_data, board_size=720, output_path=output_path)
    # Pad 1080×1350 → 1080×1920 (9:16) with black bars
    img = Image.open(output_path)
    canvas = Image.new("RGB", (CANVAS_W, 1920), BG_COLOR)
    y_offset = (1920 - CANVAS_H) // 2
    canvas.paste(img, (0, y_offset))
    canvas.save(str(output_path), "PNG")
    return output_path
