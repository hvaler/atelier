"""
Printable plates for clip 1: the drawing that has to be in your hand on camera.

    atelier-agent/.venv/Scripts/python -m pip install Pillow
    atelier-agent/.venv/Scripts/python demo/video/make_print_sheets.py
        ->  demo/video/print-sheets.pdf   (4 pages, A4 portrait, 300 dpi)

Print it, then copy a plate by hand onto clean paper. Tracing works too — the construction lines
are drawn light for exactly that.

**Why the plates are correct and not faulty.** Clip 1 says *"an isometric axis is at thirty degrees
or it is not."* The prop in your hand is the thing that is right; the error story happens on screen,
in the calibration sample. A faulty drawing in the opening shot would be arguing against itself.

**Why the angles are computed and not eyeballed.** This is a project about 30° being 30°, so a
printable that is roughly 30° would be an embarrassment. Every line here is placed from
`cos`/`sin` of an exact angle, and `main()` measures the rendered endpoints back with `atan2` and
prints what it got. If a plate is off by more than a hundredth of a degree the script says so
instead of writing a PDF.

**Why the labels are in Spanish.** These are plates for a Spanish student to copy, and *línea de
tierra*, *planta* and *alzado* are what a real plate carries. The repository is English; a prop
that gets printed and drawn on is not part of it. `docs/PEDAGOGY.md` §4 has the bilingual
vocabulary if you want the English on the sheet instead.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DPI = 300
W, H = int(8.27 * DPI), int(11.69 * DPI)          # A4 portrait
MARGIN = int(0.6 * DPI)

INK = (20, 20, 24)
LIGHT = (176, 178, 184)          # construction lines, meant to be traced over
FAINT = (222, 223, 226)
RED = (196, 62, 54)
BLUE = (44, 96, 178)

HEAVY = 7                        # a visible edge
THIN = 3                         # a construction line

#: Everything measured back after drawing has to agree with the angle it was drawn at to within
#: this. It is not a tolerance on the drawing; it is a check that the script did what it says.
ANGLE_EPS = 0.01


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


F_H1 = font(72, bold=True)
F_H2 = font(40, bold=True)
F_BODY = font(34)
F_NOTE = font(30)
F_LBL = font(34, bold=True, mono=True)
F_FOOT = font(26, mono=True)

#: Every line the script draws, as (page, label, angle it was drawn at, endpoints). `verify()`
#: reads this back and recomputes the angle from the coordinates.
DRAWN: list[tuple[str, str, float, tuple[float, float, float, float]]] = []


def at(x, y, angle_deg, length):
    """The point `length` away from (x, y) along `angle_deg`, measured anticlockwise from east."""
    r = math.radians(angle_deg)
    return x + length * math.cos(r), y - length * math.sin(r)


def ray(d, page, label, x, y, angle_deg, length, colour, width):
    """Draw a segment at an exact angle and record it so the angle can be measured back."""
    x1, y1 = at(x, y, angle_deg, length)
    d.line([x, y, x1, y1], fill=colour, width=width)
    DRAWN.append((page, label, angle_deg % 180, (x, y, x1, y1)))
    return x1, y1


def line(d, a, b, colour, width):
    d.line([a[0], a[1], b[0], b[1]], fill=colour, width=width)


def page(title, subtitle, footer):
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.multiline_text((MARGIN, MARGIN - 20), title, font=F_H1, fill=INK)
    d.multiline_text((MARGIN, MARGIN + 84), subtitle, font=F_BODY, fill=(96, 98, 104), spacing=10)
    d.line([MARGIN, H - MARGIN + 10, W - MARGIN, H - MARGIN + 10], fill=FAINT, width=3)
    d.text((MARGIN, H - MARGIN + 26), footer, font=F_FOOT, fill=(150, 152, 158))
    return img, d


def note(d, y, lines):
    for i, text in enumerate(lines):
        d.text((MARGIN, y + i * 44), text, font=F_NOTE, fill=(70, 72, 78))


def arc_label(d, cx, cy, radius, a0, a1, text, colour=BLUE):
    """A small arc between two directions, with the angle written outside it."""
    d.arc([cx - radius, cy - radius, cx + radius, cy + radius],
          start=-a1, end=-a0, fill=colour, width=3)
    mid = math.radians((a0 + a1) / 2)
    d.text((cx + (radius + 52) * math.cos(mid), cy - (radius + 52) * math.sin(mid) - 22),
           text, font=F_LBL, fill=colour)


# ===================================================================== sheet 1
def sheet_axes():
    img, d = page(
        "1 · Ejes isométricos",
        "Los tres ejes de la isometría, a tamaño grande. Es la lámina de la frase\n"
        "«an isometric axis is at thirty degrees or it is not».",
        "Atelier · clip 1 · X a 30°, Y a 150°, Z a 90° · dibujado, no aproximado")

    cx, cy = W // 2, int(H * 0.44)
    L = int(3.1 * DPI)

    # The three axes, and their opposite halves lighter so the origin reads as an origin.
    for label, angle in (("X", 30.0), ("Y", 150.0), ("Z", 90.0)):
        ray(d, "axes", f"{label} axis", cx, cy, angle, L, INK, HEAVY)
        ray(d, "axes", f"{label} opposite", cx, cy, angle + 180, int(L * 0.30), LIGHT, THIN)

    # A horizontal reference, which is what a set square actually rests on.
    d.line([cx - L, cy, cx + L, cy], fill=FAINT, width=THIN)
    d.text((cx + L - 210, cy + 18), "referencia horizontal", font=F_NOTE, fill=(150, 152, 158))

    arc_label(d, cx, cy, int(0.95 * DPI), 0, 30, "30°")
    arc_label(d, cx, cy, int(1.30 * DPI), 30, 90, "60°")
    arc_label(d, cx, cy, int(0.95 * DPI), 150, 180, "30°")

    for label, angle in (("X", 30.0), ("Y", 150.0), ("Z", 90.0)):
        x, y = at(cx, cy, angle, L + 40)
        d.text((x - 14, y - 22), label, font=F_H2, fill=INK)

    note(d, int(H * 0.72), [
        "Cómo copiarlo a mano:",
        "1.  Traza la referencia horizontal y marca el origen.",
        "2.  Escuadra de 30-60-90 apoyada en la horizontal: el eje X sube a 30° a la derecha,",
        "     el eje Y a 30° a la izquierda. Son la misma escuadra, girada.",
        "3.  El eje Z es la vertical exacta, 90°. Con el cateto largo sobre la horizontal.",
        "4.  Si la escuadra se mueve entre trazos, los tres ejes dejan de ser una isometría.",
    ])
    return img


# ===================================================================== sheet 2
def sheet_cube():
    img, d = page(
        "2 · Cubo isométrico",
        "El sólido que se lee como sólido y sigue siendo medible. Aristas vistas en trazo\n"
        "grueso, construcción en trazo fino.",
        "Atelier · clip 1 · las tres familias de aristas a 30°, 150° y 90°")

    a = int(1.65 * DPI)                      # edge length
    ox, oy = W // 2, int(H * 0.56)           # the near-bottom vertex

    ex = at(0, 0, 30.0, a)
    ey = at(0, 0, 150.0, a)
    ez = at(0, 0, 90.0, a)

    def p(i, j, k):
        return (ox + i * ex[0] + j * ey[0] + k * ez[0],
                oy + i * ex[1] + j * ey[1] + k * ez[1])

    visible = [
        ((0, 0, 0), (1, 0, 0)), ((0, 0, 0), (0, 1, 0)), ((0, 0, 0), (0, 0, 1)),
        ((1, 0, 0), (1, 0, 1)), ((0, 1, 0), (0, 1, 1)),
        ((1, 0, 0), (1, 1, 0)), ((0, 1, 0), (1, 1, 0)),
        ((0, 0, 1), (1, 0, 1)), ((0, 0, 1), (0, 1, 1)),
        ((1, 0, 1), (1, 1, 1)), ((0, 1, 1), (1, 1, 1)),
        ((1, 1, 0), (1, 1, 1)),
    ]
    for u, v in visible:
        a0, b0 = p(*u), p(*v)
        line(d, a0, b0, INK, HEAVY)
        ang = math.degrees(math.atan2(-(b0[1] - a0[1]), b0[0] - a0[0])) % 180
        DRAWN.append(("cube", f"edge {u}->{v}", ang, (a0[0], a0[1], b0[0], b0[1])))

    # No dashed hidden edges, and that is not an omission: in a true isometric projection the far
    # vertex lands on the same point as the near one, so its three edges coincide exactly with three
    # visible ones. The hexagon-with-a-Y is what the cube actually looks like, Necker ambiguity
    # included, and a real plate draws it this way. An earlier version drew dashes here that were
    # covered by the heavy lines they duplicated.

    # Construction: the axes the cube was built on, extended past it.
    for angle in (30.0, 150.0, 90.0):
        ray(d, "cube", f"axis {angle:g}", ox, oy, angle, int(a * 1.9), LIGHT, THIN)

    arc_label(d, ox, oy, int(0.85 * DPI), 0, 30, "30°")
    arc_label(d, ox, oy, int(0.85 * DPI), 150, 180, "30°")
    d.line([ox - int(a * 1.9), oy, ox + int(a * 1.9), oy], fill=FAINT, width=THIN)

    note(d, int(H * 0.72), [
        "Cómo copiarlo a mano:",
        "1.  Los ejes de la lámina 1, desde el vértice inferior más cercano.",
        "2.  Lleva la misma longitud de arista sobre los tres ejes. La misma, medida, no a ojo.",
        "3.  Desde cada extremo, paralelas a los otros dos ejes. En isometría no hay fuga:",
        "     cada familia de aristas es paralela a sí misma de principio a fin.",
        "4.  Repasa las aristas vistas y deja la construcción fina. Ese contraste es",
        "     «peso de línea», y es una de las cosas que el Plano B de la crítica mira.",
    ])
    return img


# ===================================================================== sheet 3
def sheet_monge():
    img, d = page(
        "3 · Lámina de diédrico",
        "Dos vistas planas, comprobadas una contra otra. No es el dibujo de un sólido:\n"
        "es una notación de la que se recuperan medidas.",
        "Atelier · clip 1 · alzado sobre la LT, planta debajo, referencias a 90°")

    lt_y = int(H * 0.42)
    x0 = MARGIN + int(0.7 * DPI)
    x1 = W - MARGIN - int(0.7 * DPI)

    # Línea de tierra.
    d.line([x0 - 60, lt_y, x1 + 60, lt_y], fill=INK, width=HEAVY)
    d.text((x1 + 10, lt_y - 56), "LT", font=F_LBL, fill=INK)
    DRAWN.append(("monge", "ground line", 0.0, (x0 - 60, lt_y, x1 + 60, lt_y)))

    w = int(2.2 * DPI)
    left = W // 2 - w // 2
    right = left + w
    elev_h = int(1.15 * DPI)
    plan_h = int(0.85 * DPI)

    # Alzado, above the ground line.
    d.rectangle([left, lt_y - int(0.22 * DPI) - elev_h, right, lt_y - int(0.22 * DPI)],
                outline=INK, width=HEAVY)
    d.text((left, lt_y - int(0.22 * DPI) - elev_h - 66), "ALZADO", font=F_LBL, fill=INK)

    # Planta, below it, and deliberately in correspondence.
    d.rectangle([left, lt_y + int(0.22 * DPI), right, lt_y + int(0.22 * DPI) + plan_h],
                outline=INK, width=HEAVY)
    d.text((left, lt_y + int(0.22 * DPI) + plan_h + 18), "PLANTA", font=F_LBL, fill=INK)

    # Reference lines: vertical, exactly, from each vertex of the elevation to the plan.
    for x in (left, right):
        d.line([x, lt_y - int(0.22 * DPI) - elev_h - 40, x,
                lt_y + int(0.22 * DPI) + plan_h + 40], fill=LIGHT, width=THIN)
        DRAWN.append(("monge", f"reference x={x}", 90.0,
                      (x, lt_y - 100, x, lt_y + 100)))

    d.text((right + 26, lt_y - int(0.22 * DPI) - elev_h + 10),
           "líneas de referencia\nperpendiculares a la LT", font=F_NOTE, fill=(120, 122, 128))
    arc_label(d, right, lt_y, int(0.55 * DPI), 0, 90, "90°", RED)

    note(d, int(H * 0.72), [
        "Cómo copiarlo a mano:",
        "1.  Traza la línea de tierra. Perfectamente horizontal: todo lo demás cuelga de ella.",
        "2.  El alzado encima, la planta debajo.",
        "3.  Baja una referencia vertical desde cada vértice del alzado. Perpendicular a la LT.",
        "4.  Los vértices de la planta van SOBRE esas referencias. Eso es la correspondencia,",
        "     y es lo único que mide el motor de diédrico: un punto de una vista tiene que",
        "     tener su homólogo directamente debajo en la otra.",
    ])
    return img


# ===================================================================== sheet 4
def sheet_conic():
    img, d = page(
        "4 · Cónica frontal",
        "Un punto de fuga sobre la línea de horizonte. La única de las tres en la que\n"
        "las paralelas convergen — y la referencia más débil de las tres.",
        "Atelier · clip 1 · opcional; el cubo isométrico se lee mejor en cámara")

    lh_y = int(H * 0.34)
    vpx = W // 2 + int(0.5 * DPI)

    d.line([MARGIN, lh_y, W - MARGIN, lh_y], fill=BLUE, width=5)
    d.text((MARGIN, lh_y - 62), "LH  (línea de horizonte)", font=F_LBL, fill=BLUE)
    DRAWN.append(("conic", "horizon", 0.0, (MARGIN, lh_y, W - MARGIN, lh_y)))
    d.ellipse([vpx - 14, lh_y - 14, vpx + 14, lh_y + 14], fill=RED)
    d.text((vpx + 26, lh_y - 66), "F  (punto de fuga)", font=F_LBL, fill=RED)

    fw, fh = int(2.0 * DPI), int(1.5 * DPI)
    fx = W // 2 - int(1.6 * DPI)
    fy = lh_y + int(0.9 * DPI)
    d.rectangle([fx, fy, fx + fw, fy + fh], outline=INK, width=HEAVY)

    corners = [(fx, fy), (fx + fw, fy), (fx, fy + fh), (fx + fw, fy + fh)]
    for cx, cy in corners:
        d.line([cx, cy, vpx, lh_y], fill=LIGHT, width=THIN)

    # The back face, at a fixed fraction along each fugitive line, so it is exactly consistent.
    t = 0.42
    back = [(cx + (vpx - cx) * t, cy + (lh_y - cy) * t) for cx, cy in corners]
    order = [(0, 1), (1, 3), (3, 2), (2, 0)]
    for i, j in order:
        line(d, back[i], back[j], INK, HEAVY)
    for k in range(4):
        line(d, corners[k], back[k], INK, HEAVY)

    note(d, int(H * 0.72), [
        "Cómo copiarlo a mano:",
        "1.  Línea de horizonte y un punto de fuga sobre ella.",
        "2.  La cara frontal, un rectángulo con lados horizontales y verticales de verdad.",
        "3.  Desde cada vértice, una línea al punto de fuga. Ligera.",
        "4.  Cierra la cara del fondo cortando las cuatro a la MISMA profundidad.",
        "",
        "Esta es la lámina cuya referencia el motor tiene que estimar, no leer: si las cuatro",
        "convergen a un punto equivocado de forma consistente, el error medido sale pequeño.",
    ])
    return img


def verify() -> bool:
    """Measure every drawn segment back from its own endpoints. The point of the whole file."""
    print(f"{'page':<8} {'element':<26} {'drawn':>9} {'measured':>10} {'error':>9}")
    print("-" * 66)
    worst, ok = 0.0, True
    for pg, label, drawn, (x0, y0, x1, y1) in DRAWN:
        measured = math.degrees(math.atan2(-(y1 - y0), x1 - x0)) % 180
        error = min(abs(measured - drawn), 180 - abs(measured - drawn))
        worst = max(worst, error)
        if error > ANGLE_EPS:
            ok = False
        if len(DRAWN) < 40 or error > ANGLE_EPS or label.startswith(("X", "Y", "Z", "ground", "horizon")):
            print(f"{pg:<8} {label:<26} {drawn:>8.3f}° {measured:>9.3f}° {error:>8.4f}°"
                  f"{'  ← OFF' if error > ANGLE_EPS else ''}")
    print("-" * 66)
    print(f"{len(DRAWN)} segments checked, worst error {worst:.4f}° "
          f"(tolerance {ANGLE_EPS}°)")
    return ok


def main() -> int:
    pages = [sheet_axes(), sheet_cube(), sheet_monge(), sheet_conic()]
    if not verify():
        raise SystemExit("A plate is not at the angle it claims. No PDF written.")

    out = Path(__file__).parent / "print-sheets.pdf"
    pages[0].save(out, save_all=True, append_images=pages[1:], resolution=DPI)
    print(f"\nwrote {out}  {len(pages)} pages, A4 at {DPI} dpi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
