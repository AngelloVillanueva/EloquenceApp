"""Render docs/assets/architecture-pipeline.png (Studio Nocturne booth palette).

Requires Pillow in the venv:  pip install pillow
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "assets" / "architecture-pipeline.png"

BG = (14, 12, 10)
AMBER = (232, 168, 124)
INK = (232, 168, 124)
MUTED = (200, 150, 115)
SPEAK = (110, 186, 140)
FEEDBACK = (120, 170, 210)
W, H = 1600, 900


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def rounded(draw: ImageDraw.ImageDraw, box, radius: int, fill=None, outline=None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def center_text(draw, xy, text, fnt, fill=INK):
    x, y = xy
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((x - tw / 2, y - th / 2), text, font=fnt, fill=fill)


def box_label(draw, box, title: str, subtitle: str | None = None, title_font=None, sub_font=None):
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if subtitle:
        center_text(draw, (cx, cy - 9), title, title_font)
        center_text(draw, (cx, cy + 12), subtitle, sub_font, fill=MUTED)
    else:
        center_text(draw, (cx, cy), title, title_font)


def arrow(draw, x0, y0, x1, y1, color=AMBER, width=2):
    draw.line((x0, y0, x1, y1), fill=color, width=width)
    # simple chevron
    import math

    ang = math.atan2(y1 - y0, x1 - x0)
    size = 8
    for da in (2.5, -2.5):
        draw.line(
            (
                x1,
                y1,
                x1 - size * math.cos(ang + da * 0.35),
                y1 - size * math.sin(ang + da * 0.35),
            ),
            fill=color,
            width=width,
        )


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    f_title = font(32, bold=True)
    f_sub = font(15)
    f_col = font(16, bold=True)
    f_box = font(14, bold=True)
    f_small = font(12)
    f_tiny = font(11)

    # header
    center_text(d, (W / 2, 42), "Eloquence  —  100% Local Voice Pipeline", f_title)
    center_text(
        d,
        (W / 2, 78),
        "RTX 3060  ·  STT + LLM + TTS  ·  Dual Channel  ·  SQLite Memory",
        f_sub,
        fill=MUTED,
    )
    # waveform ticks
    for ox in (210, 1390):
        for i, h in enumerate((10, 18, 12, 22, 14, 8)):
            x = ox + i * 7
            d.line((x, 42 - h / 2, x, 42 + h / 2), fill=AMBER, width=2)

    cols = [
        (36, "Browser / React UI"),
        (424, "FastAPI Backend  :8000"),
        (812, "Ollama  :11434"),
        (1200, "Local disk"),
    ]
    col_w, col_top, col_bot = 364, 110, 860
    inner = []

    for x, title in cols:
        rounded(d, (x, col_top, x + col_w, col_bot), 18, fill=(20, 17, 14), outline=AMBER, width=2)
        d.line((x + 24, col_top + 48, x + col_w - 24, col_top + 48), fill=(*AMBER, 90), width=1)
        center_text(d, (x + col_w / 2, col_top + 26), title, f_col)
        inner.append((x + 18, col_top + 62, x + col_w - 18, col_bot - 18))

    b0, b1, b2, b3 = inner

    def node(bounds, y, h, title, subtitle=None):
        x0, _, x1, _ = bounds
        box = (x0, y, x1, y + h)
        rounded(d, box, 10, fill=(28, 24, 20), outline=AMBER, width=1)
        box_label(d, box, title, subtitle, f_box, f_tiny)
        return box

    # --- Browser ---
    mic = node(b0, 188, 70, "Mic + AudioWorklet")
    node(b0, 278, 88, "Voice Orb")
    # orb circle
    d.ellipse((b0[0] + 148, 292, b0[0] + 186, 330), outline=AMBER, width=2)
    node(b0, 386, 58, "Energy VAD  →  END_TURN")
    notes = node(b0, 560, 70, "Coach Notes sidebar")
    trans = node(b0, 650, 70, "Transcript")

    # --- FastAPI ---
    ws = node(b1, 188, 58, "WebSocket  /ws/audio")
    stt = node(b1, 278, 58, "Faster-Whisper STT (GPU)")
    split = node(b1, 386, 70, "Dual splitter", "SPEAK  |  FEEDBACK")
    tts = node(b1, 490, 58, "Sentence TTS  Kokoro (GPU)")
    coach = node(b1, 575, 58, "Coach Notes + MemoryService")
    mem = node(b1, 720, 70, "MemoryService")

    # SPEAK / FEEDBACK tags
    d.text((split[0] + 12, split[3] + 6), "SPEAK", font=f_tiny, fill=SPEAK)
    d.text((split[2] - 86, split[3] + 6), "FEEDBACK", font=f_tiny, fill=FEEDBACK)

    # --- Ollama ---
    llm = node(b2, 330, 160, "Llama 3.1 8B", "receives text only, never SQL")
    d.ellipse((b2[0] + 148, 348, b2[0] + 186, 386), outline=AMBER, width=2)

    # --- Disk ---
    db = (b3[0] + 40, 280, b3[2] - 40, 430)
    # cylinder
    d.ellipse((db[0], db[1], db[2], db[1] + 36), outline=AMBER, width=2)
    d.ellipse((db[0], db[3] - 36, db[2], db[3]), outline=AMBER, width=2)
    d.line((db[0], db[1] + 18, db[0], db[3] - 18), fill=AMBER, width=2)
    d.line((db[2], db[1] + 18, db[2], db[3] - 18), fill=AMBER, width=2)
    center_text(d, ((db[0] + db[2]) / 2, 355), "SQLite", f_box)
    center_text(d, ((db[0] + db[2]) / 2, 378), "data/elevate.db", f_small, fill=MUTED)

    tables = [
        (470, "sessions"),
        (545, "errors"),
        (620, "vocab"),
    ]
    table_boxes = []
    for y, name in tables:
        box = node(b3, y, 48, name)
        table_boxes.append(box)

    # arrows
    def mid(box, edge: str):
        x0, y0, x1, y1 = box
        if edge == "r":
            return x1, (y0 + y1) / 2
        if edge == "l":
            return x0, (y0 + y1) / 2
        if edge == "b":
            return (x0 + x1) / 2, y1
        return (x0 + x1) / 2, y0

    # mic -> ws
    mx, my = mid(mic, "r")
    wx, wy = mid(ws, "l")
    arrow(d, mx, my, wx, wy)
    center_text(d, ((mx + wx) / 2, my - 14), "PCM audio", f_tiny)

    # vertical fastapi
    arrow(d, *mid(ws, "b"), *mid(stt, "t"))
    arrow(d, *mid(stt, "b"), *mid(split, "t"))
    arrow(d, split[0] + 70, split[3], *mid(tts, "t"), color=SPEAK)
    arrow(d, split[2] - 70, split[3], *mid(coach, "t"), color=FEEDBACK)
    arrow(d, *mid(coach, "b"), *mid(mem, "t"))

    # tts -> playback
    tx, ty = mid(tts, "l")
    arrow(d, tx, ty, b0[2], notes[1] - 8)
    d.text((b0[2] + 8, notes[1] - 28), "Audio playback", font=f_tiny, fill=MUTED)

    # coach -> notes
    cx, cy = mid(coach, "l")
    nx, ny = mid(notes, "r")
    arrow(d, cx, cy, nx, ny)

    # transcript from coach-ish
    arrow(d, cx, trans[1] + 20, *mid(trans, "r"))

    # stt <-> llm
    sx, sy = mid(stt, "r")
    lx, ly = mid(llm, "l")
    arrow(d, sx, sy - 10, lx, ly - 28)
    arrow(d, lx, ly + 28, split[2], split[1] + 20)

    # MemoryService <-> SQLite (LLM never runs SQL)
    arrow(d, *mid(mem, "r"), db[0], (db[1] + db[3]) / 2)

    # dashed memory brief (text injected into the prompt)
    vx, vy = mid(table_boxes[-1], "l")
    mx2, my2 = mid(mem, "r")
    steps = 24
    for i in range(steps):
        t0, t1 = i / steps, (i + 0.5) / steps
        d.line(
            (vx + (mx2 - vx) * t0, vy + (my2 - vy) * t0, vx + (mx2 - vx) * t1, vy + (my2 - vy) * t1),
            fill=AMBER,
            width=1,
        )
    center_text(d, ((vx + mx2) / 2, (vy + my2) / 2 - 12), "memory brief (text only)", f_tiny, fill=MUTED)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG")
    print(f"Wrote {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
