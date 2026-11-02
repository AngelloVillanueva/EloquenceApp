import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
S = 4


def render(text, path, size=72, sx=0.85, stroke=1.3, W=1094, H=233, x0=58, base=131, seed=1):
    rng = np.random.default_rng(seed)
    f = ImageFont.truetype(FONT, size * S)
    wide = Image.new("L", (W * S * 2, H * S), 0)
    d = ImageDraw.Draw(wide)
    d.text((0, base * S), text, font=f, fill=255, anchor="ls",
           stroke_width=int(round(stroke * S)))
    bbox = wide.getbbox()
    glyphs = wide.crop((bbox[0], 0, bbox[2], H * S))
    gw = int(glyphs.width * sx)
    glyphs = glyphs.resize((gw, H * S), Image.LANCZOS)
    mask = Image.new("L", (W * S, H * S), 0)
    mask.paste(glyphs, (x0 * S, 0))
    mask = mask.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
    m = np.array(mask).astype(float) / 255

    yy, xx = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
    base_col = np.array([240, 236, 226], float)
    grad = 1 - 0.07 * (xx / W * 0.3 + (yy / H) * 0.5)
    bg = base_col[None, None, :] * grad[..., None]
    bg = bg + rng.normal(0, 1.6, (H, W, 1))
    ink = np.array([4, 2, 1], float)
    img = bg * (1 - m[..., None]) + ink * m[..., None]
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(path, quality=95)
    return x0 + gw / S


if __name__ == "__main__":
    print(render("Sr. (a) RESIDENTE PROPIEDAD", "out/test_orig.png"))
    print(render("Sr. (a) MARGOT FRANCO EPUYAO", "out/sr_a_margot_franco_epuyao.png", W=1180))
