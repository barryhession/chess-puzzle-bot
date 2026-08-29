"""
reel_renderer.py
----------------
Renders a chess puzzle solution as a 1080×1920 MP4 Reel.

Frame sequence:
  1. Intro      (2.0s) — puzzle position + "Can you solve this?"
  2. Think      (1.5s) — same board + "Here's the solution..."
  3. Move 1..N  (1.5s each) — board after each move + SAN notation
  4. Outro      (2.0s) — final board + follow CTA

Dependencies: imageio[ffmpeg], Pillow, python-chess, svglib, reportlab
"""

import io
import tempfile
from pathlib import Path

import chess
import chess.svg
import imageio.v3 as iio
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

# ---------------------------------------------------------------------------
# Canvas constants
# ---------------------------------------------------------------------------
REEL_W  = 1080
REEL_H  = 1920
BOARD_SIZE = 1080          # full-width square board
BOARD_Y    = 380           # board starts here (leaves room for header)

BG_COLOR       = (18, 18, 18)
ACCENT         = (139, 90, 43)
TEXT_PRIMARY   = (240, 240, 240)
TEXT_SECONDARY = (160, 160, 160)
HIGHLIGHT      = (255, 213, 79)   # yellow for move notation

FPS = 30

# ---------------------------------------------------------------------------
# Shared helpers (mirrors board_renderer.py)
# ---------------------------------------------------------------------------
def _load_font(size: int) -> ImageFont.FreeTypeFont:
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


def _board_to_png(board: chess.Board, flipped: bool, size: int,
                  last_move: chess.Move = None) -> Image.Image:
    """Render a chess board to a Pillow Image."""
    svg_str = chess.svg.board(
        board,
        flipped=flipped,
        size=size,
        lastmove=last_move,
        colors={
            "square light": "#f0d9b5",
            "square dark":  "#b58863",
            "arrow":        "#cc0000cc",
        },
    )
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False,
                                     mode="w", encoding="utf-8") as f:
        f.write(svg_str)
        tmp_svg = f.name
    try:
        drawing = svg2rlg(tmp_svg)
        scale = size / max(drawing.width, drawing.height)
        drawing.width  = int(drawing.width  * scale)
        drawing.height = int(drawing.height * scale)
        drawing.scale(scale, scale)
        buf = io.BytesIO()
        renderPM.drawToFile(drawing, buf, fmt="PNG")
        return Image.open(buf).convert("RGBA")
    finally:
        Path(tmp_svg).unlink(missing_ok=True)


def _rating_label(rating: str) -> str:
    try:
        r = int(rating)
        if r < 1200: return "Beginner"
        if r < 1500: return "Intermediate"
        if r < 1800: return "Advanced"
        if r < 2100: return "Expert"
        return "Master"
    except ValueError:
        return ""


def _side_label(board: chess.Board) -> str:
    return "White to move" if board.turn == chess.WHITE else "Black to move"


# ---------------------------------------------------------------------------
# Frame builders
# ---------------------------------------------------------------------------
def _base_canvas(board_img: Image.Image, board_y: int = BOARD_Y) -> Image.Image:
    """Create a canvas with the board pasted in."""
    canvas = Image.new("RGB", (REEL_W, REEL_H), BG_COLOR)
    bx = (REEL_W - BOARD_SIZE) // 2
    canvas.paste(board_img, (bx, board_y), board_img)
    return canvas


def _draw_header(draw: ImageDraw.Draw, title: str) -> None:
    draw.text((REEL_W // 2, 40),  "@thechesssignal",
              font=_load_font(36), fill=TEXT_SECONDARY, anchor="mt")
    draw.text((REEL_W // 2, 90), title,
              font=_load_font(60), fill=TEXT_PRIMARY, anchor="mt")


def _draw_footer_puzzle(draw: ImageDraw.Draw, side: str, rating: str, themes: list[str]) -> None:
    """Footer for intro/think frames."""
    footer_y = BOARD_Y + BOARD_SIZE + 30
    draw.text((REEL_W // 2, footer_y), side,
              font=_load_font(48), fill=TEXT_PRIMARY, anchor="mt")
    diff = _rating_label(rating)
    draw.text((REEL_W // 2, footer_y + 65),
              f"{diff}  -  Rating {rating}",
              font=_load_font(34), fill=ACCENT, anchor="mt")
    display_themes = [t for t in themes if t not in ("mate", "puzzleId")][:3]
    if display_themes:
        draw.text((REEL_W // 2, footer_y + 115),
                  "  ".join(f"#{t}" for t in display_themes),
                  font=_load_font(28), fill=TEXT_SECONDARY, anchor="mt")


def _build_move_pairs(moves_so_far: list[tuple[str, str]]) -> list[str]:
    """
    Convert list of (label, san) tuples into display rows.
    Each row is one move pair: "1. e4 e5" or if black-started: "1... e5 2. Nf3 Nc6"
    White move label: "1. e4"   Black move label: "e5" (no number)
    Pairs are grouped: white + black = one row.
    If puzzle starts with black, first entry is "1... san" and white follows.
    """
    rows = []
    i = 0
    while i < len(moves_so_far):
        label, san = moves_so_far[i]
        row = f"{label} {san}"
        # If white move, try to append black's response on same row
        if not label.endswith("...") and i + 1 < len(moves_so_far):
            _, black_san = moves_so_far[i + 1]
            row += f"  {black_san}"
            i += 2
        else:
            i += 1
        rows.append(row)
    return rows


def _draw_footer_move(draw: ImageDraw.Draw, moves_so_far: list[tuple[str, str]], total: int) -> None:
    """
    Footer for solution move frames.
    Stacked rows of move pairs. Current move token highlighted yellow, rest grey.
    """
    footer_y = BOARD_Y + BOARD_SIZE + 24
    font_label   = _load_font(40)
    line_h       = 52

    draw.text((REEL_W // 2, footer_y),
              f"Solution  ({len(moves_so_far)} / {total})",
              font=_load_font(32), fill=TEXT_SECONDARY, anchor="mt")

    y = footer_y + 48

    # Build rows but track which token is the latest
    current_label, current_san = moves_so_far[-1]
    current_token = f"{current_label} {current_san}"

    i = 0
    while i < len(moves_so_far):
        label, san = moves_so_far[i]
        is_last = (i == len(moves_so_far) - 1)

        # Determine if black follows on same row
        has_black = (not label.endswith("...") and i + 1 < len(moves_so_far))
        black_label, black_san = moves_so_far[i + 1] if has_black else (None, None)
        black_is_last = has_black and (i + 1 == len(moves_so_far) - 1)

        # Draw white portion
        white_text  = f"{label} {san}"
        white_color = HIGHLIGHT if is_last else TEXT_SECONDARY

        # Measure to position side by side
        if has_black:
            black_text  = f"  {black_san}"
            black_color = HIGHLIGHT if black_is_last else TEXT_SECONDARY

            # Draw white + black on same line, left-aligned from centre
            w_bbox  = draw.textbbox((0, 0), white_text, font=font_label)
            b_bbox  = draw.textbbox((0, 0), black_text,  font=font_label)
            total_w = (w_bbox[2] - w_bbox[0]) + (b_bbox[2] - b_bbox[0])
            start_x = (REEL_W - total_w) // 2

            draw.text((start_x, y), white_text, font=font_label, fill=white_color, anchor="lt")
            draw.text((start_x + (w_bbox[2] - w_bbox[0]), y), black_text,
                      font=font_label, fill=black_color, anchor="lt")
            i += 2
        else:
            draw.text((REEL_W // 2, y), white_text,
                      font=font_label, fill=white_color, anchor="mt")
            i += 1

        y += line_h


def _draw_footer_outro(draw: ImageDraw.Draw, puzzle_id: str,
                       moves_so_far: list[tuple[str, str]]) -> None:
    """Outro footer — full move list in grey then CTA."""
    footer_y = BOARD_Y + BOARD_SIZE + 24
    font_moves = _load_font(38)
    line_h     = 50

    draw.text((REEL_W // 2, footer_y), "Full solution:",
              font=_load_font(32), fill=TEXT_SECONDARY, anchor="mt")

    y = footer_y + 44
    i = 0
    while i < len(moves_so_far):
        label, san = moves_so_far[i]
        has_black = (not label.endswith("...") and i + 1 < len(moves_so_far))

        if has_black:
            _, black_san = moves_so_far[i + 1]
            row = f"{label} {san}  {black_san}"
            i += 2
        else:
            row = f"{label} {san}"
            i += 1

        draw.text((REEL_W // 2, y), row,
                  font=font_moves, fill=TEXT_SECONDARY, anchor="mt")
        y += line_h

    y += 24
    draw.text((REEL_W // 2, y), "Follow for daily puzzles",
              font=_load_font(44), fill=TEXT_PRIMARY, anchor="mt")
    draw.text((REEL_W // 2, y + 58), "@thechesssignal",
              font=_load_font(42), fill=ACCENT, anchor="mt")
    draw.text((REEL_W // 2, y + 112),
              f"lichess.org/training/{puzzle_id}",
              font=_load_font(26), fill=TEXT_SECONDARY, anchor="mt")


def _frame_to_array(img: Image.Image) -> np.ndarray:
    return np.array(img.convert("RGB"))


def _make_frames(img: Image.Image, duration_secs: float) -> list[np.ndarray]:
    arr = _frame_to_array(img)
    return [arr] * int(FPS * duration_secs)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def render_reel(puzzle: dict, output_path: Path) -> Path:
    """
    Render a puzzle solution Reel and save as MP4.

    Args:
        puzzle:      dict with FEN, Moves, Rating, PuzzleId, Themes
        output_path: where to write the .mp4

    Returns:
        output_path
    """
    fen       = puzzle["FEN"]
    moves_uci = puzzle["Moves"].split()
    rating    = puzzle.get("Rating", "?")
    puzzle_id = puzzle.get("PuzzleId", "")
    themes    = puzzle.get("Themes", "").split()

    # Set up board — apply opponent's first move to get the puzzle position
    board = chess.Board(fen)
    opponent_move = None
    if moves_uci:
        try:
            opponent_move = board.parse_uci(moves_uci[0])
            board.push(opponent_move)
        except (chess.InvalidMoveError, chess.IllegalMoveError):
            pass

    flipped   = (board.turn == chess.BLACK)
    side      = _side_label(board)
    board_img = _board_to_png(board, flipped, BOARD_SIZE, last_move=opponent_move)

    all_frames: list[np.ndarray] = []

    # --- Frame 1: Intro ---
    canvas = _base_canvas(board_img)
    draw = ImageDraw.Draw(canvas)
    _draw_header(draw, "Can you solve this?")
    _draw_footer_puzzle(draw, side, rating, themes)
    all_frames += _make_frames(canvas, 2.0)

    # --- Frame 2: Think ---
    canvas = _base_canvas(board_img)
    draw = ImageDraw.Draw(canvas)
    _draw_header(draw, "Here's the solution...")
    _draw_footer_puzzle(draw, side, rating, themes)
    all_frames += _make_frames(canvas, 1.5)

    # --- Solution move frames ---
    solver_moves_uci = moves_uci[1:]  # skip opponent's first move
    total_moves = len(solver_moves_uci)

    # Rebuild board from puzzle position for move animation
    board2 = chess.Board(fen)
    if moves_uci:
        try:
            board2.push_uci(moves_uci[0])
        except (chess.InvalidMoveError, chess.IllegalMoveError):
            pass

    # Determine starting move number and whose turn it is at puzzle start
    start_move_num  = board2.fullmove_number
    starts_with_black = (board2.turn == chess.BLACK)

    # moves_so_far: list of (label, san) tuples
    # label = "1." for white, "1..." for black
    moves_so_far: list[tuple[str, str]] = []
    last_bimg = board_img

    for i, uci in enumerate(solver_moves_uci):
        try:
            move = board2.parse_uci(uci)
            san  = board2.san(move)
            # Determine label BEFORE pushing (board2.turn is the side about to move)
            is_black_move = (board2.turn == chess.BLACK)
            move_num = board2.fullmove_number
            label = f"{move_num}..." if is_black_move else f"{move_num}."
            board2.push(move)
        except (chess.InvalidMoveError, chess.IllegalMoveError):
            continue

        moves_so_far.append((label, san))

        last_bimg = _board_to_png(board2, flipped, BOARD_SIZE, last_move=move)
        canvas = _base_canvas(last_bimg)
        draw = ImageDraw.Draw(canvas)
        _draw_header(draw, "Solution")
        _draw_footer_move(draw, list(moves_so_far), total_moves)
        all_frames += _make_frames(canvas, 1.5)

    # --- Outro frame (4.0s) ---
    canvas = _base_canvas(last_bimg)
    draw = ImageDraw.Draw(canvas)
    _draw_header(draw, "Did you get it?")
    _draw_footer_outro(draw, puzzle_id, moves_so_far)
    all_frames += _make_frames(canvas, 4.0)

    # --- Write MP4 ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(
        str(output_path),
        all_frames,
        fps=FPS,
        codec="libx264",
        quality=8,
        pixelformat="yuv420p",  # required for Instagram compatibility
        macro_block_size=None,
    )
    return output_path
