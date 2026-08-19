"""
The Atelier mark: a vanishing point, drawn the way the engine sees one.

    python demo/make_logo.py     ->  docs/img/logo.png (1024x1024)
                                     docs/img/logo-wide.png (1200x630, for link previews)

**Why this and not a paintbrush.** The subject of this project is not art in general; it is the
one measurable thing inside a perspective drawing — whether the receding edges actually meet
where they claim to. So the mark is that: a horizon, a vanishing point, and four edges running
to it. Three of them land. One misses by nine degrees, drawn in the same amber the overlay uses
for a line between 2.5 and 6 degrees off.

That deliberate wrong line is the whole product in one shape. A logo of a perfect star burst
would describe a drawing app; this describes a tutor that measures.

Colours are the app's: the dark studio ground, warm paper for construction lines, and the
overlay's own green/amber severity code — so the mark and the product agree.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

INK = (17, 20, 26)            # studio ground, matching the UI's bg-dark
PAPER = (233, 226, 214)       # warm construction-line grey
HORIZON = (86, 96, 112)
ACCURATE = (0, 200, 120)      # the overlay's "< 2.5°" green
DRIFT = (245, 176, 48)        # the overlay's "2.5–6.0°" amber
VP_GLOW = (255, 255, 255)


def font(size: int, bold: bool = False):
    for name in (("segoeuib.ttf", "arialbd.ttf") if bold else ("segoeui.ttf", "arial.ttf")):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_mark(size: int, with_text: bool) -> Image.Image:
    img = Image.new("RGB", (size, size), INK)
    d = ImageDraw.Draw(img)
    s = size / 1024.0

    vp = (size * 0.5, size * 0.50)
    horizon_y = vp[1]

    # Horizon: the locus of every vanishing point, and the line students forget to draw.
    d.line([(size * 0.08, horizon_y), (size * 0.92, horizon_y)], fill=HORIZON, width=max(1, int(3 * s)))

    # Four receding edges from the corners of a box that is not drawn — the construction is the
    # subject, not the finished object.
    corners = [
        (size * 0.26, size * 0.70),
        (size * 0.74, size * 0.70),
        (size * 0.26, size * 0.88),
        (size * 0.74, size * 0.88),
    ]
    # One edge is deliberately wrong. Kept small — a near miss beside the vanishing point reads
    # as a measurement; a line slashing across the frame reads as a mistake in the logo.
    errors = [0.0, 6.0, 0.0, 0.0]

    for (cx, cy), err in zip(corners, errors):
        true_angle = math.atan2(vp[1] - cy, vp[0] - cx)
        angle = true_angle + math.radians(err)
        # Stop just short of the vanishing point, so the gap the error opens is the thing you see.
        length = math.hypot(vp[0] - cx, vp[1] - cy) * 0.97
        end = (cx + length * math.cos(angle), cy + length * math.sin(angle))
        colour = ACCURATE if err < 2.5 else DRIFT
        d.line([(cx, cy), end], fill=colour, width=max(2, int(7 * s)))

    # The front face: verticals and horizontals, which never converge and are drawn in paper grey
    # to say so.
    d.rectangle([size * 0.26, size * 0.70, size * 0.74, size * 0.88],
                outline=PAPER, width=max(2, int(6 * s)))

    # The vanishing point itself.
    r = max(3, int(13 * s))
    d.ellipse([vp[0] - r * 2.4, vp[1] - r * 2.4, vp[0] + r * 2.4, vp[1] + r * 2.4],
              outline=(58, 64, 78), width=max(1, int(3 * s)))
    d.ellipse([vp[0] - r, vp[1] - r, vp[0] + r, vp[1] + r], fill=VP_GLOW)

    if with_text:
        f = font(int(96 * s), bold=True)
        text = "ATELIER"
        left, top, right, bottom = d.textbbox((0, 0), text, font=f)
        d.text(((size - (right - left)) / 2, size * 0.27), text, font=f, fill=PAPER)

    return img


def main() -> int:
    out = Path(__file__).resolve().parents[1] / "docs" / "img"
    out.mkdir(parents=True, exist_ok=True)

    square = draw_mark(1024, with_text=True)
    square.save(out / "logo.png", optimize=True)

    # A wide card for link previews: the same mark, off-centre, with the thesis beside it.
    wide = Image.new("RGB", (1200, 630), INK)
    mark = draw_mark(560, with_text=False)
    wide.paste(mark, (40, 35))
    d = ImageDraw.Draw(wide)
    d.text((650, 250), "Atelier", font=font(76, bold=True), fill=PAPER)
    d.text((650, 340), "The geometry measures.", font=font(34), fill=ACCURATE)
    d.text((650, 384), "The AI teaches.", font=font(34), fill=PAPER)
    d.text((650, 428), "The student grows.", font=font(34), fill=HORIZON)
    wide.save(out / "logo-wide.png", optimize=True)

    for f in ("logo.png", "logo-wide.png"):
        p = out / f
        print(f"{f}: {Image.open(p).size[0]}x{Image.open(p).size[1]}, {p.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
