"""Render docs/assets/architecture-pipeline.png — orthogonal Studio Nocturne schematic.

Requires Pillow:  pip install pillow
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "assets" / "architecture-pipeline.png"

BG = (14, 12, 10)
LANE = (18, 16, 14)
CARD = (32, 28, 24)
AMBER = (232, 168, 124)
MUTED = (184, 138, 108)
SPEAK = (110, 186, 140)
FEEDBACK = (120, 170, 210)

W, H = 1920, 1080
PAD = 36
GUTTER = 88
HEADER = 102
FOOTER = 112
LANE_TOP = HEADER
LANE_BOT = H - FOOTER
LANE_HEAD = 48


def font(size: int, bold: bool = False):
    for name in (
        "segoeuib.ttf" if bold else "segoeui.ttf",
        "calibrib.ttf" if bold else "calibri.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
    ):
        path = Path("C:/Windows/Fonts") / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def tsize(draw, text, fnt):
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[2] - b[0], b[3] - b[1]


def txt(draw, xy, text, fnt, fill=AMBER, anchor="lt"):
    draw.text(xy, text, font=fnt, fill=fill, anchor=anchor)


def rr(draw, box, r, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def chevron(draw, x, y, ang, color=AMBER, size=9, width=2):
    draw.line(
        (
            x - size * math.cos(ang - 0.42),
            y - size * math.sin(ang - 0.42),
            x,
            y,
            x - size * math.cos(ang + 0.42),
            y - size * math.sin(ang + 0.42),
        ),
        fill=color,
        width=width,
    )


def line(draw, a, b, color=AMBER, width=2):
    draw.line((*a, *b), fill=color, width=width)


def hseg(draw, x0, x1, y, color=AMBER, width=2, arrow="end"):
    direction = 1 if x1 >= x0 else -1
    if arrow == "end":
        draw.line((x0, y, x1 - 8 * direction, y), fill=color, width=width)
        chevron(draw, x1, y, 0 if direction > 0 else math.pi, color, width=width)
    else:
        draw.line((x0, y, x1, y), fill=color, width=width)


def vseg(draw, y0, y1, x, color=AMBER, width=2, arrow="end"):
    direction = 1 if y1 >= y0 else -1
    if arrow == "end":
        draw.line((x, y0, x, y1 - 8 * direction), fill=color, width=width)
        chevron(draw, x, y1, math.pi / 2 if direction > 0 else -math.pi / 2, color, width=width)
    else:
        draw.line((x, y0, x, y1), fill=color, width=width)


def caption(draw, x, y, text, fnt, fill=MUTED):
    """Label sitting in empty space; opaque pill so it never sits on a stroke."""
    tw, th = tsize(draw, text, fnt)
    pad_x, pad_y = 7, 3
    box = (x - tw / 2 - pad_x, y - th - pad_y, x + tw / 2 + pad_x, y + pad_y)
    rr(draw, box, 4, fill=BG, outline=None)
    txt(draw, (x, y - th / 2 + 1), text, fnt, fill=fill, anchor="mm")


def dash_h(draw, x0, x1, y, color=AMBER, width=2, arrow_at="left"):
    lo, hi = (x0, x1) if x0 < x1 else (x1, x0)
    x = lo
    while x < hi:
        nx = min(x + 7, hi)
        draw.line((x, y, nx, y), fill=color, width=width)
        x = nx + 6
    if arrow_at == "left":
        chevron(draw, lo, y, math.pi, color, width=width)
    else:
        chevron(draw, hi, y, 0, color, width=width)


def mid(box, edge="c"):
    x0, y0, x1, y1 = box
    if edge == "r":
        return x1, (y0 + y1) / 2
    if edge == "l":
        return x0, (y0 + y1) / 2
    if edge == "b":
        return (x0 + x1) / 2, y1
    if edge == "t":
        return (x0 + x1) / 2, y0
    return (x0 + x1) / 2, (y0 + y1) / 2


# icons 24x24
def ic_mic(d, x, y, c=AMBER):
    d.rounded_rectangle((x + 8, y + 2, x + 16, y + 14), 4, outline=c, width=2)
    d.arc((x + 5, y + 8, x + 19, y + 20), 0, 180, fill=c, width=2)
    d.line((x + 12, y + 20, x + 12, y + 23), fill=c, width=2)
    d.line((x + 8, y + 23, x + 16, y + 23), fill=c, width=2)


def ic_orb(d, x, y, c=AMBER):
    d.ellipse((x + 3, y + 3, x + 21, y + 21), outline=c, width=2)
    d.ellipse((x + 8, y + 8, x + 16, y + 16), outline=c, width=1)


def ic_wave(d, x, y, c=AMBER):
    for i, h in enumerate((7, 14, 10, 16, 8)):
        xx = x + 5 + i * 4
        d.line((xx, y + 12 - h / 2, xx, y + 12 + h / 2), fill=c, width=2)


def ic_note(d, x, y, c=AMBER):
    d.rounded_rectangle((x + 5, y + 3, x + 19, y + 21), 2, outline=c, width=2)
    d.line((x + 8, y + 9, x + 16, y + 9), fill=c, width=1)
    d.line((x + 8, y + 13, x + 16, y + 13), fill=c, width=1)
    d.line((x + 8, y + 17, x + 14, y + 17), fill=c, width=1)


def ic_bub(d, x, y, c=AMBER):
    d.rounded_rectangle((x + 3, y + 4, x + 21, y + 16), 4, outline=c, width=2)
    d.line((x + 8, y + 16, x + 8, y + 21), fill=c, width=2)
    d.line((x + 8, y + 21, x + 13, y + 16), fill=c, width=2)


def ic_ws(d, x, y, c=AMBER):
    d.ellipse((x + 10, y + 17, x + 14, y + 21), outline=c, width=2)
    d.arc((x + 6, y + 10, x + 18, y + 22), 200, 340, fill=c, width=2)
    d.arc((x + 2, y + 5, x + 22, y + 23), 200, 340, fill=c, width=2)


def ic_stt(d, x, y, c=AMBER):
    d.arc((x + 3, y + 6, x + 11, y + 18), 90, 270, fill=c, width=2)
    d.arc((x + 13, y + 6, x + 21, y + 18), 270, 90, fill=c, width=2)


def ic_split(d, x, y, c=AMBER):
    d.line((x + 12, y + 3, x + 12, y + 12), fill=c, width=2)
    d.line((x + 12, y + 12, x + 5, y + 21), fill=c, width=2)
    d.line((x + 12, y + 12, x + 19, y + 21), fill=c, width=2)


def ic_spk(d, x, y, c=AMBER):
    d.polygon(
        [(x + 4, y + 9), (x + 9, y + 9), (x + 14, y + 5), (x + 14, y + 19), (x + 9, y + 15), (x + 4, y + 15)],
        outline=c,
    )
    d.arc((x + 15, y + 8, x + 21, y + 16), 280, 80, fill=c, width=2)


def ic_chip(d, x, y, c=AMBER):
    d.rounded_rectangle((x + 6, y + 6, x + 18, y + 18), 2, outline=c, width=2)
    for i in range(3):
        d.line((x + 8 + i * 4, y + 3, x + 8 + i * 4, y + 6), fill=c, width=1)
        d.line((x + 8 + i * 4, y + 18, x + 8 + i * 4, y + 21), fill=c, width=1)


def ic_db(d, x, y, c=AMBER):
    d.ellipse((x + 6, y + 3, x + 18, y + 9), outline=c, width=2)
    d.line((x + 6, y + 6, x + 6, y + 18), fill=c, width=2)
    d.line((x + 18, y + 6, x + 18, y + 18), fill=c, width=2)
    d.ellipse((x + 6, y + 15, x + 18, y + 21), outline=c, width=2)


def ic_folder(d, x, y, c=AMBER):
    d.rectangle((x + 4, y + 10, x + 20, y + 20), outline=c, width=2)
    d.rectangle((x + 4, y + 7, x + 11, y + 10), outline=c, width=2)


ICONS = {
    "mic": ic_mic,
    "orb": ic_orb,
    "wave": ic_wave,
    "note": ic_note,
    "bub": ic_bub,
    "ws": ic_ws,
    "stt": ic_stt,
    "split": ic_split,
    "spk": ic_spk,
    "chip": ic_chip,
    "db": ic_db,
    "folder": ic_folder,
}


def card(draw, box, title, icon, f_title, sub=None, f_sub=None):
    x0, y0, x1, y1 = box
    rr(draw, box, 10, fill=CARD, outline=AMBER, width=1)
    cy = (y0 + y1) / 2
    ICONS[icon](draw, x0 + 10, cy - 12)
    tx = x0 + 42
    if sub and f_sub:
        txt(draw, (tx, cy - 9), title, f_title, anchor="lm")
        txt(draw, (tx, cy + 11), sub, f_sub, fill=MUTED, anchor="lm")
    else:
        txt(draw, (tx, cy), title, f_title, anchor="lm")
    return box


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = font(34, True)
    f_sub = font(15)
    f_lane = font(16, True)
    f_card = font(15, True)
    f_tiny = font(12)
    f_llm = font(22, True)

    title = "Eloquence  —  100% Local Voice Pipeline"
    txt(d, (W / 2, 28), title, f_title, anchor="mt")
    txt(
        d,
        (W / 2, 70),
        "RTX 3060    ·    STT + LLM + TTS    ·    Dual Channel    ·    SQLite Memory",
        f_sub,
        fill=MUTED,
        anchor="mt",
    )
    tw, _ = tsize(d, title, f_title)
    for ox in (W / 2 - tw / 2 - 64, W / 2 + tw / 2 + 22):
        for i, h in enumerate((7, 15, 10, 18, 11, 6)):
            x = ox + i * 6
            d.line((x, 40 - h / 2, x, 40 + h / 2), fill=AMBER, width=2)

    inner = W - 2 * PAD
    col_w = (inner - 3 * GUTTER) / 4.0
    xs = [PAD + i * (col_w + GUTTER) for i in range(4)]
    lanes = [(x, LANE_TOP, x + col_w, LANE_BOT) for x in xs]
    for box, name in zip(
        lanes,
        ("Browser / React UI", "FastAPI Backend  :8000", "Ollama  :11434", "Local disk"),
    ):
        rr(d, box, 16, fill=LANE, outline=AMBER, width=2)
        txt(d, ((box[0] + box[2]) / 2, box[1] + 14), name, f_lane, anchor="mt")
        d.line((box[0] + 20, box[1] + LANE_HEAD - 4, box[2] - 20, box[1] + LANE_HEAD - 4), fill=AMBER, width=1)

    inset = 16
    cols = [(b[0] + inset, b[1] + LANE_HEAD, b[2] - inset, b[3] - inset) for b in lanes]
    c0, c1, c2, c3 = cols

    def rows(bounds, n, gap=14):
        x0, y0, x1, y1 = bounds
        h = ((y1 - y0) - gap * (n - 1)) / n
        return [(x0, y0 + i * (h + gap), x1, y0 + i * (h + gap) + h) for i in range(n)]

    # Same 5-row grid in UI and backend so horizontals hit card midlines.
    r0 = rows(c0, 5, gap=16)
    r1 = rows(c1, 5, gap=16)
    mic = card(d, r0[0], "Mic + AudioWorklet", "mic", f_card)
    orb = card(d, r0[1], "Voice Orb", "orb", f_card)
    vad = card(d, r0[2], "Energy VAD  →  END_TURN", "wave", f_card)
    notes = card(d, r0[3], "Coach Notes sidebar", "note", f_card)
    trans = card(d, r0[4], "Transcript", "bub", f_card)

    ws = card(d, r1[0], "WebSocket  /ws/audio", "ws", f_card)
    stt = card(d, r1[1], "Faster-Whisper STT (GPU)", "stt", f_card)
    split = card(d, r1[2], "Dual splitter", "split", f_card, "SPEAK  |  FEEDBACK", f_tiny)

    # Row 4: TTS | Coach side by side (SPEAK left, FEEDBACK right)
    x0, y0, x1, y1 = r1[3]
    gap = 12
    half = (x1 - x0 - gap) / 2
    tts = card(d, (x0, y0, x0 + half, y1), "Kokoro TTS (GPU)", "spk", f_card, "sentence stream", f_tiny)
    coach = card(d, (x0 + half + gap, y0, x1, y1), "Coach notes", "note", f_card, "JSON sidebar", f_tiny)
    mem = card(d, r1[4], "MemoryService", "chip", f_card)

    # Ollama: one LLM card spanning rows 1–2 of the 5-row rhythm (align STT + splitter)
    llm = (c2[0] + 6, r1[1][1], c2[2] - 6, r1[2][3])
    rr(d, llm, 12, fill=CARD, outline=AMBER, width=2)
    ic_chip(d, (llm[0] + llm[2]) / 2 - 12, llm[1] + 18)
    txt(d, ((llm[0] + llm[2]) / 2, llm[1] + 72), "Llama 3.1 8B", f_llm, anchor="mt")
    txt(d, ((llm[0] + llm[2]) / 2, llm[1] + 108), "receives text only, never SQL", f_tiny, fill=MUTED, anchor="mt")

    # Disk: tables in top 3 rows, SQLite on MemoryService row
    sessions = card(d, (c3[0], r0[0][1], c3[2], r0[0][3]), "sessions", "folder", f_card)
    errors = card(d, (c3[0], r0[1][1], c3[2], r0[1][3]), "errors", "folder", f_card)
    vocab = card(d, (c3[0], r0[2][1], c3[2], r0[2][3]), "vocab", "folder", f_card)
    db = (c3[0], r1[4][1], c3[2], r1[4][3])
    rr(d, db, 10, fill=CARD, outline=AMBER, width=2)
    ic_db(d, db[0] + 10, (db[1] + db[3]) / 2 - 12)
    txt(d, (db[0] + 42, (db[1] + db[3]) / 2 - 8), "SQLite", f_card, anchor="lm")
    txt(d, (db[0] + 42, (db[1] + db[3]) / 2 + 12), "data/elevate.db", f_tiny, fill=MUTED, anchor="lm")

    # Gutters: two x-rails so return paths don't sit on outbound paths
    g1 = (lanes[0][2] + lanes[1][0]) / 2
    g2 = (lanes[1][2] + lanes[2][0]) / 2
    g1_out = g1 + 10  # UI → API

    # 1. PCM (row 0, outbound)
    y = mid(mic, "r")[1]
    hseg(d, mic[2], ws[0], y)
    caption(d, g1_out, y - 12, "PCM audio", f_tiny)

    # 2. Backend vertical spine (center of full-width cards)
    spine = mid(ws, "b")[0]
    vseg(d, ws[3], stt[1], spine)
    vseg(d, stt[3], split[1], spine)

    # 3. SPEAK / FEEDBACK fork — two shorts, no cross
    xs = mid(tts, "t")[0]
    xf = mid(coach, "t")[0]
    vseg(d, split[3], tts[1], xs, color=SPEAK)
    vseg(d, split[3], coach[1], xf, color=FEEDBACK)
    fork_y = (split[3] + tts[1]) / 2
    txt(d, (xs - 6, fork_y), "SPEAK", f_tiny, fill=SPEAK, anchor="rm")
    txt(d, (xf + 6, fork_y), "FEEDBACK", f_tiny, fill=FEEDBACK, anchor="lm")
    vseg(d, coach[3], mem[1], mid(coach, "b")[0])

    # 4. STT → Llama (row 1)
    y = mid(stt, "r")[1]
    hseg(d, stt[2], llm[0], y)
    caption(d, g2, y - 12, "text", f_tiny)

    # 5. Llama → splitter (row 2) — parallel, lower, never crosses #4
    y = mid(split, "r")[1]
    hseg(d, llm[0], split[2], y, arrow="end")  # leftward: x0=llm left, x1=split right? 
    # split is LEFT of llm, so tokens go right-to-left: from llm[0] to split[2]
    # hseg x0=llm[0], x1=split[2] with split[2] < llm[0], arrow end at split
    caption(d, g2, y - 12, "tokens", f_tiny)

    # 6. Audio playback: climb FastAPI left margin, cross gutter 1 only on the Orb row.
    x_up = c1[0] - 8
    yt = mid(tts, "l")[1]
    yo = mid(orb, "r")[1]
    line(d, (tts[0], yt), (x_up, yt))
    vseg(d, yt, yo, x_up, arrow=None)
    hseg(d, x_up, orb[2], yo)
    caption(d, g1, yo - 12, "Audio playback", f_tiny)

    # 7. FEEDBACK JSON: Coach → Notes (same row)
    y = mid(notes, "r")[1]
    hseg(d, coach[0], notes[2], y)
    caption(d, g1_out, y - 12, "JSON", f_tiny)

    # 8. Spoken text → Transcript (same row as MemoryService)
    y = mid(trans, "r")[1]
    hseg(d, mem[0], trans[2], y)
    caption(d, g1_out, y - 12, "spoken text", f_tiny)

    # 9. Footer rails — never enter the Ollama lane
    y_write = LANE_BOT + 26
    y_brief = LANE_BOT + 64
    mx = mid(mem, "b")[0]
    dx = mid(db, "b")[0]
    line(d, (mx, mem[3]), (mx, y_write))
    hseg(d, mx, dx, y_write)
    line(d, (dx, y_write), (dx, db[3]))
    chevron(d, dx, db[3], -math.pi / 2)
    caption(d, (mx + dx) / 2, y_write - 12, "writes  ·  app only", f_tiny)

    line(d, (dx, db[3]), (dx, y_brief))
    dash_h(d, dx, mx, y_brief, arrow_at="left")
    line(d, (mx, y_brief), (mx, mem[3] + 8))
    chevron(d, mx, mem[3], -math.pi / 2)
    caption(d, (mx + dx) / 2, y_brief - 12, "memory brief  (text only, never SQL)", f_tiny)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG")
    print(f"Wrote {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
