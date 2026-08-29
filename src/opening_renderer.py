"""
opening_renderer.py
-------------------
Renders chess opening graphics with a board showing the position after the opening moves.

Uses the same SVG-to-PNG pipeline as board_renderer.py.
"""

import tempfile
from pathlib import Path

import chess
import chess.svg
from PIL import Image, ImageDraw, ImageFont
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

# ── Canvas dimensions ─────────────────────────────────────────────────────────
CANVAS_W = 1080
CANVAS_H = 1350

# ── Color palette ─────────────────────────────────────────────────────────────
BG_COLOR      = (18, 18, 18)
ACCENT        = (201, 160, 56)   # gold
TEXT_PRIMARY   = (255, 255, 255)  # white
TEXT_SECONDARY = (160, 160, 160)  # grey
DIVIDER       = (60, 60, 60)

# ── Board colors (same as board_renderer.py) ──────────────────────────────────
SQUARE_LIGHT = "#f0d9b5"
SQUARE_DARK  = "#b58863"

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


def _board_to_svg(board: chess.Board, size: int, flipped: bool = False) -> str:
    """Render a chess.Board to an SVG string."""
    colors = chess.svg.DEFAULT_COLORS.copy()
    colors["square light"] = SQUARE_LIGHT
    colors["square dark"] = SQUARE_DARK
    return chess.svg.board(board, size=size, flipped=flipped, colors=colors)


def _svg_to_png_bytes(svg: str, size: int) -> bytes:
    """Convert an SVG string to PNG bytes."""
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp_svg:
        tmp_svg.write(svg.encode("utf-8"))
        tmp_svg_path = tmp_svg.name

    drawing = svg2rlg(tmp_svg_path)
    if drawing is None:
        raise RuntimeError("Failed to parse SVG")

    scale = size / max(drawing.width, drawing.height)
    drawing.width = size
    drawing.height = size
    drawing.scale(scale, scale)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_png:
        tmp_png_path = tmp_png.name

    renderPM.drawToFile(drawing, tmp_png_path, fmt="PNG")

    with open(tmp_png_path, "rb") as f:
        png_bytes = f.read()

    Path(tmp_svg_path).unlink(missing_ok=True)
    Path(tmp_png_path).unlink(missing_ok=True)

    return png_bytes


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


def render_opening_with_board(
    opening: dict,
    board_size: int = 640,
    output_path: Path | None = None,
) -> Path:
    """
    Render a 1080x1350 graphic with opening info and a chess board.

    Args:
        opening: dict with name, moves, fen, idea, level
        board_size: size of the chess board in pixels (640, 720, or 800)
        output_path: where to save the PNG

    Returns:
        The output path.
    """
    if output_path is None:
        output_path = Path("output") / "opening.png"

    # ── Create canvas ─────────────────────────────────────────────────────────
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # ── Fonts ─────────────────────────────────────────────────────────────────
    font_brand    = _load_font(28)
    font_title    = _load_font(52)
    font_heading  = _load_font(44)
    font_moves    = _load_font(30)
    font_body     = _load_font(30)
    font_subtitle = _load_font(26)
    font_cta      = _load_font(28)

    margin_left = 80
    margin_right = 80
    content_width = CANVAS_W - margin_left - margin_right

    y = 50

    # ── Header: @thechesssignal ───────────────────────────────────────────────
    draw.text(
        (CANVAS_W // 2, y),
        "@thechesssignal",
        fill=ACCENT,
        font=font_brand,
        anchor="mt",
    )
    y += 45

    # ── Title: OPENING OF THE DAY ────────────────────────────────────────────
    draw.text(
        (CANVAS_W // 2, y),
        "OPENING OF THE DAY",
        fill=TEXT_PRIMARY,
        font=font_title,
        anchor="mt",
    )
    y += 60

    # ── Divider ───────────────────────────────────────────────────────────────
    draw.line(
        [(margin_left, y), (CANVAS_W - margin_right, y)],
        fill=DIVIDER,
        width=2,
    )
    y += 25

    # ── Opening name ──────────────────────────────────────────────────────────
    draw.text(
        (CANVAS_W // 2, y),
        opening["name"],
        fill=ACCENT,
        font=font_heading,
        anchor="mt",
    )
    y += 55

    # ── Moves ─────────────────────────────────────────────────────────────────
    draw.text(
        (CANVAS_W // 2, y),
        opening["moves"],
        fill=TEXT_SECONDARY,
        font=font_moves,
        anchor="mt",
    )
    y += 40

    # ── Chess board ───────────────────────────────────────────────────────────
    board = chess.Board(opening["fen"])
    svg = _board_to_svg(board, board_size)
    png_bytes = _svg_to_png_bytes(svg, board_size)

    board_img = Image.open(Path(__name__).parent.parent / "output" / "_tmp_board.png") if False else None

    # Save PNG bytes to temp file and open
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(png_bytes)
        tmp_path = tmp.name

    board_img = Image.open(tmp_path)

    # Center the board horizontally
    board_x = (CANVAS_W - board_size) // 2
    canvas.paste(board_img, (board_x, y))

    Path(tmp_path).unlink(missing_ok=True)

    y += board_size + 25

    # ── Idea (wrapped) ────────────────────────────────────────────────────────
    idea_lines = _wrap_text(opening["idea"], font_body, content_width)
    for line in idea_lines[:3]:  # max 3 lines
        draw.text(
            (margin_left, y),
            line,
            fill=TEXT_PRIMARY,
            font=font_body,
            anchor="lt",
        )
        y += 38

    y += 10

    # ── Level ─────────────────────────────────────────────────────────────────
    draw.text(
        (margin_left, y),
        f"Level: {opening['level']}",
        fill=TEXT_SECONDARY,
        font=font_subtitle,
        anchor="lt",
    )
    y += 40

    # ── Footer ────────────────────────────────────────────────────────────────
    y = CANVAS_H - 100

    draw.line(
        [(margin_left, y), (CANVAS_W - margin_right, y)],
        fill=DIVIDER,
        width=2,
    )
    y += 30

    draw.text(
        (CANVAS_W // 2, y),
        "Follow @thechesssignal",
        fill=ACCENT,
        font=font_cta,
        anchor="mt",
    )
    y += 40

    draw.text(
        (CANVAS_W // 2, y),
        "Questions? DM us",
        fill=TEXT_SECONDARY,
        font=font_subtitle,
        anchor="mt",
    )

    # ── Save ──────────────────────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(str(output_path), "PNG")
    print(f"[opening_renderer] Saved: {output_path}")
    return output_path
