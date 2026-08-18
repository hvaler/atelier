"""Generate synthetic calibration dataset with deliberate perspective errors for testing and demo."""

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

    cv2.putText(canvas, title, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (60, 60, 60), 2)
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

    cv2.putText(canvas, title, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (60, 60, 60), 2)
    cv2.imwrite(str(output_path), canvas)


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

    print(f"[OK] Calibration dataset generated at: {dataset_dir}")


if __name__ == "__main__":
    main()
