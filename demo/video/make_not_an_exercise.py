"""A page that is plainly not a descriptive-geometry exercise, for the vision gate.

    atelier-agent/.venv/Scripts/python demo/video/make_not_an_exercise.py

Writes `demo/video/not-an-exercise.png`, which is what segment 5 of the video uploads. No
construction lines, no ground line, no converging edges — the point of the shot is that the gate
declines before anything is measured, and says why in its own words.

A photograph of a real shopping list is better on camera, and the gate does not care which. This
exists so the shot is reproducible by someone who does not have one to hand.
"""

from pathlib import Path

import cv2
import numpy as np

W, H = 1000, 1300

#: (text, scale, thickness). A blank line is a paragraph break rather than a drawn line.
LINES = [
    ("SHOPPING", 1.9, 3),
    ("", 0, 0),
    ("bread", 1.2, 2),
    ("milk  x2", 1.2, 2),
    ("olive oil", 1.2, 2),
    ("tomatoes", 1.2, 2),
    ("coffee beans", 1.2, 2),
    ("rice", 1.2, 2),
    ("", 0, 0),
    ("call the plumber", 1.2, 2),
    ("book train tickets", 1.2, 2),
    ("return the library books", 1.2, 2),
]


def main() -> int:
    img = np.full((H, W, 3), 252, np.uint8)
    y = 140
    for text, scale, thickness in LINES:
        if text:
            cv2.putText(img, text, (110, y), cv2.FONT_HERSHEY_SIMPLEX, scale, (35, 35, 45),
                        thickness, cv2.LINE_AA)
        y += 95 if scale else 45

    out = Path(__file__).parent / "not-an-exercise.png"
    cv2.imwrite(str(out), img)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
