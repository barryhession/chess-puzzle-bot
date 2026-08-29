"""
board_renderer.py
-----------------
Renders a chess position as a 1080×1350 PNG suitable for Instagram portrait posts.

Pipeline:
  FEN + first move  →  python-chess board  →  SVG  →  svglib/reportlab PNG  →  Pillow composite

We use svglib + reportlab (pure Python, no native Cairo DLL required) instead of cairosvg
so the code works on Windows without extra system packages.  On Linux (GitHub Actions) the
same libraries also work without sudo apt installs.
"""

import io
import tempfile
from pathlib import Path

import chess
import chess.svg
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Layout constants  (all sizes in px at 1×)
# ---------------------------------------------------------------------------
CANVAS_W = 1080
CANVAS_H = 1350

BOARD_SIZE = 960          # square board rendered to this px size
BOARD_TOP  = 120          # y offset of the board on the canvas

HEADER_H   = BOARD_TOP    # space above the board for branding / title
FOOTER_H   = CANVAS_H - BOARD_TOP - BOARD_SIZE   # space below

BG_COLOR        = (18, 18, 18)       # near-black background
BOARD_BG        = BG_COLOR
ACCENT          = (139, 90, 43)      # warm brown accent (matches chess board)
TEXT_PRIMARY    = (240, 240, 240)
TEXT_SECONDARY  = (160, 160, 160)

PIECE_COLORS = {
    "square light": "#f0d9b5",
    "square dark":  "#b58863",
    "arrow":        "#cc0000cc",
}

BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """Try to load a system/bundled font; fall back to default."""
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def _side_to_move_label(fen: str) -> str:
    parts = fen.split()
    if len(parts) >= 2:
        return "White to move" if parts[1] == "w" else "Black to move"
    return ""


def _rating_label(rating: str) -> str:
    try:
        r = int(rating)
        if r < 1200:
            return "Beginner"
        if r < 1500:
            return "Intermediate"
        if r < 1800:
            return "Advanced"
        if r < 2100:
            return "Expert"
        return "Master"
    except ValueError:
        return ""


def _board_to_svg(board: chess.Board, flipped: bool = False) -> str:
    """Return an SVG string for the board position."""
    return chess.svg.board(
        board,
        flipped=flipped,
        size=BOARD_SIZE,
        colors={
            "square light": PIECE_COLORS["square light"],
            "square dark":  PIECE_COLORS["square dark"],
        },
    )


def _svg_to_png_bytes(svg: str, size: int) -> bytes:
    """Convert SVG string to PNG bytes using svglib + reportlab (pure Python)."""
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False, mode="w", encoding="utf-8") as f:
        f.write(svg)
        tmp_svg = f.name
    try:
        drawing = svg2rlg(tmp_svg)
        if drawing is None:
            raise RuntimeError("svg2rlg returned None — SVG could not be parsed.")
        # Scale drawing to the requested pixel size
        scale = size / max(drawing.width, drawing.height)
        drawing.width  = int(drawing.width  * scale)
        drawing.height = int(drawing.height * scale)
        drawing.scale(scale, scale)
        buf = io.BytesIO()
        renderPM.drawToFile(drawing, buf, fmt="PNG")
        return buf.getvalue()
    finally:
        Path(tmp_svg).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def render_puzzle_image(puzzle: dict, output_path: Path) -> Path:
    """
    Render the puzzle position and save a 1080×1350 PNG to `output_path`.

    Args:
        puzzle: dict with at least FEN, Moves, Rating, PuzzleId, Themes
        output_path: where to write the PNG

    Returns:
        The same output_path for chaining.
    """
    fen = puzzle["FEN"]
    moves_uci = puzzle["Moves"].split()
    rating = puzzle.get("Rating", "?")
    puzzle_id = puzzle.get("PuzzleId", "")
    themes = puzzle.get("Themes", "").split()

    # The puzzle FEN is the position BEFORE the opponent's first move.
    # Apply that move so we show the position the solver actually faces.
    board = chess.Board(fen)
    if moves_uci:
        try:
            board.push_uci(moves_uci[0])
        except (chess.InvalidMoveError, chess.IllegalMoveError):
            pass  # show pre-move position if the move is somehow invalid

    # Who needs to solve it?
    flipped = (board.turn == chess.BLACK)
    side_label = _side_to_move_label(board.fen())

    # --- Render board SVG → PNG bytes ---
    svg_str = _board_to_svg(board, flipped=flipped)
    board_png_bytes = _svg_to_png_bytes(svg_str, BOARD_SIZE)
    board_img = Image.open(io.BytesIO(board_png_bytes)).convert("RGBA")

    # --- Build canvas ---
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)

    # Paste board (centred horizontally)
    board_x = (CANVAS_W - BOARD_SIZE) // 2
    canvas.paste(board_img, (board_x, BOARD_TOP), board_img)

    draw = ImageDraw.Draw(canvas)

    # --- Header: account name / branding ---
    font_brand  = _load_font(36)
    font_title  = _load_font(52)
    font_sub    = _load_font(34)
    font_small  = _load_font(26)

    brand_text = "@thechesssignal"
    draw.text((CANVAS_W // 2, 30), brand_text, font=font_brand,
              fill=TEXT_SECONDARY, anchor="mt")

    # Title: "Can you solve this?"
    draw.text((CANVAS_W // 2, 68), "Can you solve this?", font=font_title,
              fill=TEXT_PRIMARY, anchor="mt")

    # --- Footer area ---
    footer_y = BOARD_TOP + BOARD_SIZE + 20

    # Side to move
    draw.text((CANVAS_W // 2, footer_y), side_label, font=font_sub,
              fill=TEXT_PRIMARY, anchor="mt")

    # Difficulty label + rating
    diff_label = _rating_label(rating)
    rating_text = f"{diff_label}  ·  Rating {rating}" if diff_label else f"Rating {rating}"
    draw.text((CANVAS_W // 2, footer_y + 50), rating_text, font=font_small,
              fill=ACCENT, anchor="mt")

    # Theme tags (show up to 3)
    display_themes = [t for t in themes if t not in ("mate", "puzzleId")][:3]
    if display_themes:
        tags_text = "  ".join(f"#{t}" for t in display_themes)
        draw.text((CANVAS_W // 2, footer_y + 90), tags_text, font=font_small,
                  fill=TEXT_SECONDARY, anchor="mt")

    # Puzzle ID (small, bottom-right)
    id_text = f"lichess.org/training/{puzzle_id}"
    draw.text((CANVAS_W - 20, CANVAS_H - 20), id_text, font=_load_font(22),
              fill=(80, 80, 80), anchor="rb")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(str(output_path), "PNG")
    return output_path
