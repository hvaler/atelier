"""
The last fifteen seconds: the argument as one picture, and where to go and see it.

    atelier-agent/.venv/Scripts/python -m pip install Pillow
    python demo/video/make_closing_card.py     ->  demo/video/closing-card.png  (1920x1080)

**Why a card and not the ASCII diagram from the README.** That diagram is built to be read at a
terminal, and at video bitrates its box-drawing characters turn to mush. This says the one thing
worth carrying away, sized to be legible on a laptop at 1080p by a viewer who is not leaning in.

**Why the three references and not the architecture.** The obvious instinct is to close on the
service topology. But two Cloud Run services over HTTP is the least surprising thing here, and
segment 8 has already shown it live in the console. What a viewer will not have absorbed in three
minutes is the ranking: that the three engines differ in *where the reference comes from*, and that
this sets a ceiling on each one which the project states rather than hides. That is the card.

**Why it goes at the end and not the start.** A diagram before the demonstration is three
rectangles nobody has a reason to care about, and every second spent on it is a second not spent
showing the thing work. Placed last, the same rectangles summarise what the viewer just watched —
which is when a diagram earns its keep.

Dark, because the shots before it are the light-background web app and the eye needs a full stop.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080

INK = (16, 17, 20)
PAPER = (243, 241, 236)
MUTED = (138, 140, 148)
CYAN = (56, 189, 214)          # the accent the app itself uses
AMBER = (222, 164, 44)
GREEN = (78, 190, 132)

URL = "atelier-web-3hacbhowpq-ew.a.run.app"
REPO = "github.com/hvaler/atelier"

#: (system, where the reference comes from, the ceiling that follows, colour)
#: Ordered weakest first, which is the order the narration says them in and the opposite of the
#: order a pitch would choose.
COLUMNS = [
    ("CONIC", "reference INFERRED", "RANSAC estimates the vanishing\npoint from the student's own lines.\nA drifted drawing yields one that\nagrees with it.", AMBER),
    ("ORTHOGRAPHIC", "reference READ OFF THE PAGE", "The ground line is a line the\nstudent drew. Nothing is guessed,\nbut a crooked one skews everything\n— so its tilt is reported too.", CYAN),
    ("AXONOMETRIC", "reference GIVEN", "The axes are constants of the\nprojection. Nothing is estimated.\nSix degrees injected comes back\nas six point zero zero.", GREEN),
]


def font(size: int, bold: bool = False, mono: bool = False):
    if mono:
        names = ("consolab.ttf", "consola.ttf", "cour.ttf")
    elif bold:
        names = ("segoeuib.ttf", "arialbd.ttf")
    else:
        names = ("segoeui.ttf", "arial.ttf")
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def centred(draw, text, f, cx, y, fill, spacing=10):
    left, top, right, bottom = draw.multiline_textbbox((0, 0), text, font=f, spacing=spacing)
    draw.multiline_text((cx - (right - left) / 2, y), text, font=f, fill=fill,
                        spacing=spacing, align="center")
    return bottom - top


def main() -> int:
    card = Image.new("RGB", (W, H), INK)
    draw = ImageDraw.Draw(card)

    centred(draw, "ATELIER", font(58, bold=True), W / 2, 96, PAPER)
    centred(draw, "an agent that verifies descriptive-geometry constructions",
            font(30), W / 2, 178, MUTED)

    # A hairline rule, because the three columns below need a horizon to hang from.
    draw.line([(200, 250), (W - 200, 250)], fill=(48, 50, 56), width=2)

    centred(draw, "Three systems. Three kinds of reference. Three different ceilings.",
            font(34, bold=True), W / 2, 288, PAPER)

    box_w, gap = 500, 60
    total = box_w * 3 + gap * 2
    top, box_h = 380, 400
    for i, (system, reference, body, colour) in enumerate(COLUMNS):
        x = (W - total) / 2 + i * (box_w + gap)
        draw.rounded_rectangle([x, top, x + box_w, top + box_h], radius=14,
                               outline=(52, 54, 60), width=2, fill=(22, 23, 27))
        # The colour is carried by a rule at the top of the box rather than the border: a full
        # coloured outline reads as a status, and none of these three is a status.
        draw.rounded_rectangle([x + 1, top + 1, x + box_w - 1, top + 7], radius=3, fill=colour)

        cx = x + box_w / 2
        centred(draw, system, font(36, bold=True), cx, top + 46, PAPER)
        centred(draw, reference, font(21, mono=True), cx, top + 104, colour)
        centred(draw, body, font(23), cx, top + 168, MUTED, spacing=14)

    centred(draw, "The ranking is in the documentation, not buried in it.",
            font(27), W / 2, 828, MUTED)

    centred(draw, URL, font(30, mono=True), W / 2, 906, CYAN)
    centred(draw, REPO + "   ·   Apache 2.0   ·   100 automated tests",
            font(24, mono=True), W / 2, 956, MUTED)

    out = Path(__file__).parent / "closing-card.png"
    card.save(out)
    print(f"wrote {out}  {W}x{H}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
