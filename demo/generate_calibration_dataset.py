"""Generate the synthetic calibration dataset: conic perspective and axonometric projection,
each with deliberate angular errors of a known size, for the golden tests and the demo."""

import math
from pathlib import Path
import cv2
import numpy as np


def generate_1point_drawing(
    output_path: Path,
    vp: tuple[int, int] = (400, 250),
    error_deg: float = 0.0,
    title: str = "1-Point Perspective",
):
    """Generate a 1-point perspective box drawing on notebook-like canvas."""
    canvas = np.ones((600, 800, 3), dtype=np.uint8) * 248  # Warm white paper
    vp_x, vp_y = vp

    # Draw faint horizon line
    cv2.line(canvas, (0, vp_y), (800, vp_y), (220, 220, 220), 1)

    # Front face of the box (true vertical and horizontal)
    box_x1, box_y1 = 280, 380
    box_x2, box_y2 = 520, 520
    cv2.rectangle(canvas, (box_x1, box_y1), (box_x2, box_y2), (40, 40, 40), 2)

    # Converging edges from corners to vanishing point
    corners = [
        (box_x1, box_y1),
        (box_x2, box_y1),
        (box_x1, box_y2),
        (box_x2, box_y2),
    ]

    for idx, (cx, cy) in enumerate(corners):
        true_angle = math.atan2(vp_y - cy, vp_x - cx)
        # Apply deliberate error to top-right corner if error_deg > 0
        current_err = error_deg if idx == 1 else 0.0
        angle = true_angle + math.radians(current_err)

        depth = 0.55  # Box depth ratio
        back_x = int(cx + depth * (vp_x - cx) * math.cos(math.radians(current_err)))
        back_y = int(cy + depth * (vp_y - cy) * math.sin(math.radians(current_err)))

        # Construction line extending towards VP
        cv2.line(canvas, (cx, cy), (int(cx + 180 * math.cos(angle)), int(cy + 180 * math.sin(angle))), (60, 60, 60), 2)

    # Back face
    cv2.rectangle(canvas, (330, 320), (470, 400), (80, 80, 80), 2)

    # No caption is burned into the canvas. It used to be, and Hough joined the letter
    # strokes into 25 segments of ~61px — more than half of everything the estimator saw,
    # which is why the two-point vanishing points landed hundreds of pixels off-frame. A
    # student's drawing has no title written across the top of it; neither should the
    # calibration set that stands in for one. The label lives in the filename.
    cv2.imwrite(str(output_path), canvas)


def generate_2point_drawing(
    output_path: Path,
    f1: tuple[int, int] = (100, 250),
    f2: tuple[int, int] = (700, 250),
    error_f1_deg: float = 0.0,
    title: str = "2-Point Perspective",
):
    """Generate a 2-point perspective building drawing with known deliberate errors."""
    canvas = np.ones((600, 800, 3), dtype=np.uint8) * 248
    f1_x, f1_y = f1
    f2_x, f2_y = f2

    # Draw horizon
    cv2.line(canvas, (0, 250), (800, 250), (220, 220, 220), 1)

    # Leading vertical edge of the building
    lead_x = 400
    top_y = 300
    bot_y = 480
    cv2.line(canvas, (lead_x, top_y), (lead_x, bot_y), (30, 30, 30), 2)

    # Left face converging to F1
    angle_top_left = math.atan2(f1_y - top_y, f1_x - lead_x) + math.radians(error_f1_deg)
    angle_bot_left = math.atan2(f1_y - bot_y, f1_x - lead_x) + math.radians(error_f1_deg)

    cv2.line(canvas, (lead_x, top_y), (int(lead_x + 180 * math.cos(angle_top_left)), int(top_y + 180 * math.sin(angle_top_left))), (50, 50, 50), 2)
    cv2.line(canvas, (lead_x, bot_y), (int(lead_x + 180 * math.cos(angle_bot_left)), int(bot_y + 180 * math.sin(angle_bot_left))), (50, 50, 50), 2)

    # Right face converging to F2
    angle_top_right = math.atan2(f2_y - top_y, f2_x - lead_x)
    angle_bot_right = math.atan2(f2_y - bot_y, f2_x - lead_x)

    cv2.line(canvas, (lead_x, top_y), (int(lead_x + 180 * math.cos(angle_top_right)), int(top_y + 180 * math.sin(angle_top_right))), (50, 50, 50), 2)
    cv2.line(canvas, (lead_x, bot_y), (int(lead_x + 180 * math.cos(angle_bot_right)), int(bot_y + 180 * math.sin(angle_bot_right))), (50, 50, 50), 2)

    # Side vertical edges
    cv2.line(canvas, (260, 335), (260, 440), (40, 40, 40), 2)
    cv2.line(canvas, (540, 335), (540, 440), (40, 40, 40), 2)

    cv2.imwrite(str(output_path), canvas)


def generate_axonometric_drawing(
    output_path: Path,
    system: str = "isometric",
    error_deg: float = 0.0,
    perturbed_axis: str = "X",
    receding_angle_deg: float = 45.0,
):
    """
    Generate an axonometric wireframe box with a known angular error injected into one axis family.

    The error is injected per *family*, not per edge, because that is the mistake axonometry
    actually produces: a student who sets the 30-degree axis with a badly placed set square draws
    every edge of that family at the same wrong angle. The corners then fail to close by an amount
    proportional to the error, which is what the drawing looks like on paper and what the engine
    must be able to name.

    Nothing is written on the canvas. Burned-in titles were once the majority of the segments the
    detector found, and the headline measurement of the whole product was reading them.
    """
    canvas = np.ones((600, 800, 3), dtype=np.uint8) * 248  # Warm white paper
    ink = (40, 40, 40)

    # Drawing-space axis directions (y up), in degrees.
    if system == "isometric":
        nominal = {"X": 30.0, "Y": 150.0, "Z": 90.0}
    elif system == "cavalier":
        nominal = {"X": 0.0, "Y": receding_angle_deg, "Z": 90.0}
    else:
        raise ValueError(f"Unsupported system for the calibration set: {system}")

    drawn = dict(nominal)
    drawn[perturbed_axis] = nominal[perturbed_axis] + error_deg

    def unit(axis_label: str, angles: dict) -> tuple[float, float]:
        rad = math.radians(angles[axis_label])
        return math.cos(rad), math.sin(rad)

    side = 190.0
    origin = (330.0, 430.0)  # image coordinates of the near-bottom vertex

    def vertex(a: int, b: int, c: int) -> tuple[float, float]:
        """Cube vertex at a*X + b*Y + c*Z, placed with the *true* axis directions."""
        dx = dy = 0.0
        for count, label in ((a, "X"), (b, "Y"), (c, "Z")):
            if count:
                ux, uy = unit(label, nominal)
                dx += side * count * ux
                dy += side * count * uy
        return origin[0] + dx, origin[1] - dy  # y flips back into image space

    # The twelve edges of the box, each as (start vertex, axis family it runs along).
    edges: list[tuple[tuple[int, int, int], str]] = []
    for b in (0, 1):
        for c in (0, 1):
            edges.append(((0, b, c), "X"))
    for a in (0, 1):
        for c in (0, 1):
            edges.append(((a, 0, c), "Y"))
    for a in (0, 1):
        for b in (0, 1):
            edges.append(((a, b, 0), "Z"))

    for start, label in edges:
        sx, sy = vertex(*start)
        ux, uy = unit(label, drawn)
        ex, ey = sx + side * ux, sy - side * uy
        cv2.line(canvas, (int(sx), int(sy)), (int(ex), int(ey)), ink, 2, cv2.LINE_AA)

    cv2.imwrite(str(output_path), canvas)
    return output_path


def generate_dihedral_drawing(
    output_path: Path,
    correspondence_error_px: int = 0,
    reference_slant_deg: float = 0.0,
    lt_tilt_deg: float = 0.0,
    omit_plan_vertex: bool = False,
):
    """
    Generate a Monge (sistema diédrico) plate: elevation above the ground line, plan below.

    Three separate errors can be injected, because they are three different mistakes and a single
    "wrong" figure cannot tell them apart:

    - `correspondence_error_px`: the plan shifted sideways, so its vertices no longer sit under the
      elevation's. The classic failure of the system.
    - `reference_slant_deg`: the reference lines drawn off square to the ground line.
    - `lt_tilt_deg`: the ground line itself drawn crooked, which quietly rotates the reference
      every other measurement is taken against.
    - `omit_plan_vertex`: a corner drawn in the elevation and never answered in the plan.

    No text is written on the canvas; burned-in labels were once the majority of what the detector
    found.
    """
    canvas = np.ones((600, 800, 3), dtype=np.uint8) * 248
    ink = (40, 40, 40)
    faint = (150, 150, 150)

    lt_y = 300.0
    lt_x1, lt_x2 = 60.0, 740.0
    tilt = math.radians(lt_tilt_deg)
    # Rotate the ground line about its midpoint so the plate stays centred.
    mid_x = (lt_x1 + lt_x2) / 2.0
    lt_p1 = (lt_x1, lt_y - (lt_x1 - mid_x) * math.tan(tilt))
    lt_p2 = (lt_x2, lt_y - (lt_x2 - mid_x) * math.tan(tilt))
    cv2.line(canvas, (int(lt_p1[0]), int(lt_p1[1])), (int(lt_p2[0]), int(lt_p2[1])), ink, 2, cv2.LINE_AA)

    # Elevation: a rectangle above the ground line.
    ex1, ex2 = 260, 520
    ey1, ey2 = 140, 260
    cv2.rectangle(canvas, (ex1, ey1), (ex2, ey2), ink, 2)

    # Plan: a rectangle below it, shifted by the injected correspondence error.
    shift = correspondence_error_px
    px1, px2 = ex1 + shift, ex2 + shift
    py1, py2 = 350, 450
    if omit_plan_vertex:
        # Draw three sides only: the right-hand edge of the plan is never closed, so the
        # elevation's right corner has nothing under it.
        cv2.line(canvas, (px1, py1), (px2, py1), ink, 2, cv2.LINE_AA)
        cv2.line(canvas, (px1, py1), (px1, py2), ink, 2, cv2.LINE_AA)
        cv2.line(canvas, (px1, py2), (px2 - 90, py2), ink, 2, cv2.LINE_AA)
    else:
        cv2.rectangle(canvas, (px1, py1), (px2, py2), ink, 2)

    # Reference lines carrying each vertex across the fold, drawn faint as construction lines are.
    #
    # They drop from the *elevation* vertex and stay square unless `reference_slant_deg` says
    # otherwise. Anchoring their lower end to the shifted plan instead would have tilted them by
    # the correspondence error, so a plate injected with one mistake would have carried two, and
    # neither golden case would isolate what it claims to.
    slant = math.radians(reference_slant_deg)
    for x_top in (ex1, ex2):
        top = (float(x_top), float(ey2))
        bottom_y = float(py2)
        dx = (bottom_y - top[1]) * math.tan(slant)
        bottom = (float(x_top) + dx, bottom_y)
        cv2.line(canvas, (int(top[0]), int(top[1])), (int(bottom[0]), int(bottom[1])), faint, 2, cv2.LINE_AA)

    cv2.imwrite(str(output_path), canvas)
    return output_path


def main():
    dataset_dir = Path("demo/dataset")
    dataset_dir.mkdir(parents=True, exist_ok=True)

    # 1. 1-Point perspective drawings (Beginner level)
    generate_1point_drawing(dataset_dir / "01_1point_perfect.png", error_deg=0.0, title="1-Point Perfect (0deg error)")
    generate_1point_drawing(dataset_dir / "02_1point_error_4deg.png", error_deg=4.0, title="1-Point Slight Error (4deg)")
    generate_1point_drawing(dataset_dir / "03_1point_error_9deg.png", error_deg=9.0, title="1-Point Noticeable Error (9deg)")

    # 2. 2-Point perspective drawings (Advanced level)
    generate_2point_drawing(dataset_dir / "04_2point_perfect.png", error_f1_deg=0.0, title="2-Point Perfect Oblique")
    generate_2point_drawing(dataset_dir / "05_2point_error_6deg.png", error_f1_deg=6.0, title="2-Point Left VP Error (6deg)")

    # 3. Axonometric drawings (parallel projection: the axes are fixed, nothing is estimated)
    generate_axonometric_drawing(dataset_dir / "06_isometric_perfect.png", system="isometric", error_deg=0.0)
    generate_axonometric_drawing(dataset_dir / "07_isometric_error_6deg.png", system="isometric", error_deg=6.0, perturbed_axis="X")
    generate_axonometric_drawing(dataset_dir / "08_cavalier_perfect.png", system="cavalier", error_deg=0.0)

    # 4. Orthographic plates (sistema diedrico): two views folded about the ground line
    generate_dihedral_drawing(dataset_dir / "09_diedrico_perfect.png")
    generate_dihedral_drawing(dataset_dir / "10_diedrico_error_18px.png", correspondence_error_px=18)
    generate_dihedral_drawing(dataset_dir / "11_diedrico_vertice_huerfano.png", omit_plan_vertex=True)

    print(f"[OK] Calibration dataset generated at: {dataset_dir}")


if __name__ == "__main__":
    main()
