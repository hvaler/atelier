# Pedagogical grounding

Atelier grades perspective drawings. This document places what it measures against what published
art curricula actually ask of a student, so that the critique's vocabulary and its "next exercise"
recommendation are traceable to teaching practice rather than invented in a prompt.

It does **not** replace the studio rubric the agent already uses. It gives that rubric something
to be checked against, and something to cite.

---

## 1. Sources, and what could be stored

Licence was verified before anything was downloaded. **Nothing from these sources is versioned in
this repository** — see the reason against each.

| Source | Licence | Stored here? |
|---|---|---|
| **Drawing Perspectives, Volume 2 (Art‑005B)** — Kristen Kennedy, College of the Sequoias / Lemoore College, 2024. 121 pp. [PDF](https://lemoorecollege.edu/oer/documents/2024-drawing-perspectives-art-005b-oer-textbook.pdf) | **CC BY‑SA 4.0** for the text | **No.** The licence excludes itself from the images: *"Images and figures within this text are openly licensed, in the Public Domain, or used based on fair use principles. Some images are student work; all rights are reserved."* Redistributing the PDF would redistribute that student work. Cited and quoted only. |
| **ART 110 Basic Perspective** — BYU‑Idaho, Winter 2015 course site. [Syllabus](https://courses.byui.edu/art110_new/Art110_S15/HTML/syllabus.html) · [Rubric](https://courses.byui.edu/art110_new/Art110_S15/HTML/rubric.html) | **None stated** on any page of the course site | **No.** Absent a licence, the default is all rights reserved. Short criterion wordings are quoted below as quotation for commentary. |
| **Grado en Animación (Fundamentos del Dibujo & Perspectiva Espacial)** — U‑tad (Centro Universitario de Tecnología y Arte Digital, Madrid). [Plan de Estudios](https://www.u-tad.com/estudios/grado-en-animacion/) | **Programa académico universitario** | **No.** La guía docente y competencias de layout/perspectiva para animación son citadas como base pedagógica del benchmark de 2 puntos de fuga y jerarquía gráfica. |
| **Introduction to Architecture, ARCH 1101, Course Outline** — Michael Duddy, CUNY New York City College of Technology, 2017. [Record](https://academicworks.cuny.edu/ny_oers/58/) | **CC BY 4.0** | **No — could not be retrieved.** The download endpoint answers scripted requests with HTTP 202/403. Its record also describes a *course outline*, not a perspective chapter; the abstract mentions "drafting, sketching" and perspective coverage is unconfirmed. It is cited for completeness and **not used** in the comparison below, because comparing against a document nobody has read would be the exact failure this project exists to avoid. |

> On the CC BY‑SA text specifically: this repository is Apache‑2.0, and ShareAlike would extend to
> a derivative. The Lemoore material is therefore **paraphrased and cited**, with verbatim
> fragments kept short and marked as quotations, rather than reproduced at length.

A fourth source is worth naming because the CUNY OER points at it and it is genuinely free of
restriction: Andrea Pozzo, *Rules and Examples of Perspective proper for Painters and Architects*
(1693), [Project Gutenberg #56312](http://www.gutenberg.org/files/56312/56312-h/56312-h.htm),
public domain. Not stored here either — it is a 17th‑century treatise, and linking is enough.

---

## 2. Public criteria against Atelier's

The left column quotes or paraphrases the source. The right column names what Atelier computes,
and where.

### 2.1 Convergence to the vanishing point

| Public criterion | Atelier |
|---|---|
| BYU‑Idaho, *Foreshortened Lines (20 pts)*: "All foreshortened lines go to the correct vanishing points. (20 pts.)" / "1‑3 foreshortened lines go to incorrect vanishing points. (15 pts.)" / "4 or more … (5 pts.)" | `LineSegment.convergence_error_deg` — the angular deviation of **each** segment from the line that would reach the estimated vanishing point, in degrees (`tools/geometry.py`). Aggregated as `avg_convergence_error_deg` and `max_convergence_error_deg`. |
| Lemoore, Ch. 4: orthogonals are described as the lines that "extend from the edges of objects to these vanishing points" and "illustrate how objects diminish in size as they recede into space" — described, never scored | The overlay colours every line by severity: **< 2.5°** accurate, **2.5–6.0°** slight drift, **> 6.0°** diverging (`geometry.py`). The bands are the teaching judgement; the number underneath is measured. |

**The difference is not rigour, it is resolution.** BYU counts how many lines are wrong. It never
says how wrong any of them is, so a line 1° off and a line 30° off both fall in the same bucket,
and the count itself is eyeballed.

### 2.2 The horizon

| Public criterion | Atelier |
|---|---|
| BYU‑Idaho, *Horizon Line & Vanishing Points (20 pts)*: "Horizon line is parallel with the page and vanishing points are correct. (20 pts.)" / "…not parallel … slightly incorrect. (15 pts.)" / "…definitely incorrect. (5 pts.)" | `HorizonLine.angle_deg` — the tilt of the line through the detected vanishing points, in degrees. "Slightly" and "definitely" become a figure. |
| Lemoore, Ch. 4: "The horizon line is where the sky meets the ground or sea, representing the viewer's eye level." | Derived, not assumed: for k=2 the horizon is constructed through F1 and F2 rather than taken as the middle of the page. |

Worth stating because it is not obvious: **in two‑point perspective a consistent rotation of every
receding edge does not scatter convergence — it lifts one vanishing point off the horizon.** The
measurement that moves is horizon tilt, not average error. Atelier reports both, and the two
answer different questions.

### 2.3 Verticals

| Public criterion | Atelier |
|---|---|
| BYU‑Idaho, *Vertical lines (10 pts)*: "Vertical lines are exactly vertical. (10 pts.)" / "1‑3 Vertical lines are not exactly vertical. (7 pts.)" | Verticals are **excluded from the convergence average** (`is_structural_line`, `geometry.py`): a vertical is parallel to the picture plane and was never going to converge. They are drawn on the overlay and marked *structural*. Their deviation from true vertical is **not yet scored** — see gaps. |

### 2.4 Qualitative craft

| Public criterion | Atelier |
|---|---|
| Lemoore, *Assessment Criteria*: "Accuracy of Observation (30%) — Precision and detail in capturing the forms and spatial relationships"; "Technical Skill (30%) — Proficiency in using graphite to achieve varied line quality and tonal values. Cleanliness and clarity of the drawings, with minimal extraneous marks"; "Composition & Design (20%)" | **Plane B** of the critique: `line_weight`, `spatial_clarity`, `construction_cleanliness`, `volumetrics`, `composition` (`models/critique.py`). Written by Gemini **with the drawing attached**, and forbidden by the validator from containing any figure in degrees — every number belongs to Plane A, where it is checked against OpenCV. |

### 2.5 What the public rubrics score that Atelier does not

| Public criterion | Atelier |
|---|---|
| BYU‑Idaho, *Ellipses (20 pts)*: "All ellipses are correctly shaped? (no footballs or hot‑dogs)"; *Major and Minor Axis (10 pts)* | Not measured. No ellipse detection exists. |
| BYU‑Idaho, *Peer Interaction (20 pts)*: "Peer interaction is substantive and demonstrates learning/teaching." | Out of scope: Atelier is one student and one tutor. |
| Lemoore, Ch. 5 *Atmospheric Perspective*; Ch. 6 *The Art Critique* (peer critique protocol) | Not measured. Atmospheric depth is tonal, not geometric. |

---

## 3. Consolidated vocabulary

The terms the critique is allowed to use, defined once so the agent, the overlay legend and this
document agree. Definitions follow the Lemoore text where it defines a term, and standard usage
where it does not.

| Term | Definition | In the code |
|---|---|---|
| **Horizon line** | "Where the sky meets the ground or sea, representing the viewer's eye level" (Lemoore, Ch. 4). The locus of every vanishing point for horizontal planes. | `HorizonLine` |
| **Eye level** | The height of the observer's eye, which is what the horizon line records. Synonymous with the horizon in single‑plane perspective. | implied by `HorizonLine.intercept` |
| **Vanishing point** | The point at which lines parallel in the subject appear to meet. One in frontal (one‑point) views, two in oblique (two‑point), a third above or below for tall structures seen from extreme angles (Lemoore, Ch. 4). | `VanishingPoint`, `k_detected` |
| **Orthogonals** | The receding edges that run to a vanishing point — the lines that "extend from the edges of objects to these vanishing points" (Lemoore, Ch. 4). These, and only these, carry convergence error. | lines with `vp_index` set |
| **Foreshortening** | The apparent compression of a form as it recedes from the viewer. BYU's rubric uses "foreshortened lines" for what this document calls orthogonals. | not separately measured |
| **Construction lines** | The light guide lines a student draws to place a form, intended to be subordinate to the finished edge. | Plane B: `construction_cleanliness` |
| **Contour lines** | The definitive outline of the form, intended to read more strongly than construction. | Plane B: `line_weight` |
| **Line weight** | The deliberate difference in darkness and thickness between construction and contour. Lemoore scores this under "varied line quality and tonal values". | Plane B: `line_weight` |
| **Cast shadow** | The shadow a form throws onto another surface. | not measured |
| **Form shadow** | The shaded side of the form itself, where it turns away from the light. | not measured |
| **Structural line** | *Atelier's own term.* A segment parallel to the picture plane — verticals always, and in one‑point perspective the horizontals of the front face. It never converges, so it is excluded from the convergence average. | `is_structural_line` |

The last row is the one term in this table that is not standard vocabulary. It is named here
because the engine needs a word for "a line that is not supposed to meet the vanishing point",
and averaging those in was a real defect: a drawing built with zero error measured 29° until they
were separated out.

---

## 4. The documented exercise progression

Lemoore, Ch. 4 sets three exercises in this order:

1. **"Draw a simple interior scene using a one-point perspective."**
2. **"Create a street scene using a two-point perspective."**
3. **"Illustrate a tall building viewed from a low angle using a three-point perspective."**

BYU‑Idaho's ART 110 runs five modules whose stated outcomes move the same way: "Draw simple
3‑dimensional objects in accurate 1 and 2 pt. perspective" and then "Draw complex interior (room)
scenes and exterior (landscape) scenes."

**U‑tad (Degree in Animation — Spatial Drawing & Layout)** structures foundational draftsmanship
around progressive scene construction:
1. **Primary solids & one-point frontal boxes** (verifying horizontal parallelism to $LT$).
2. **Two-point oblique clusters ($30^\circ/60^\circ$ & $45^\circ/45^\circ$)** (locating $F_1, F_2$ and true elevations from the ground line).
3. **Line weight hierarchy for layout artists** (subordinate 2H/3H construction traces vs bold HB/2B definitive contours).

Consolidated across all three curricula, the published sequence guides a student as:

```
simple solids in one-point (frontal)
        ↓
combined volumes in one-point
        ↓
oblique subjects & clusters in two-point (30°/60°)
        ↓
cylinders and ellipses
        ↓
interior scenes & background layouts
        ↓
exterior scenes
        ↓
three-point, tall subjects from extreme angles
```

**This sequence is the citable basis for the agent's `next_exercise` recommendation.** Where the
agent proposes a next step, it should propose the next step *on this ladder* from wherever the
student's measured error places them — not an exercise invented for the sentence.

### Where the ladder runs past what Atelier can measure

The rungs below are documented pedagogy that the engine cannot yet assess. They are recorded in
the README's gaps table and are **deliberately not implemented**: the scope is frozen with the
submission deadline days away, and shipping a recommendation the system cannot then measure would
reintroduce exactly the gap this document exists to close.

| Rung | Why it is not recommendable yet |
|---|---|
| Cylinders and ellipses | No ellipse detection. BYU scores ellipse shape and major/minor axis; Atelier measures neither. |
| Interior scenes | Measurable in principle — an interior is one‑point with more orthogonals — but untested against real room drawings. |
| Exterior / landscape scenes | Depth here is largely atmospheric, which is tonal rather than geometric. Outside the CV engine's remit. |
| Three‑point perspective | `k=3` is unimplemented; the solver handles k=1 and k=2 only. |

---

## 5. The finding

**Published drawing rubrics do not measure. They count, and they describe.**

Lemoore's assessment criteria are percentages over qualities: *"Accuracy of Observation (30%)"*,
*"Technical Skill (30%)"*, *"Composition & Design (20%)"*, with descriptors like *"precision and
detail in capturing the forms"* and *"cleanliness and clarity … with minimal extraneous marks"*.
BYU‑Idaho's is the more geometric of the two and still resolves only to a count: *"1‑3
foreshortened lines go to incorrect vanishing points"* against *"4 or more"*, and a horizon that is
*"slightly incorrect"* against *"definitely incorrect"*.

**Neither states an angular tolerance anywhere.** Nowhere in either does a number in degrees
appear. A line one degree off the vanishing point and a line thirty degrees off are both simply
"incorrect", and which bucket a drawing lands in depends on an instructor's eye at the end of a
stack of them.

That is the gap Atelier occupies, and it is a narrow one on purpose. It does not replace the
qualitative half — line weight, spatial clarity and craftsmanship are what a studio master is for,
and Atelier hands that half to a model with the drawing in front of it. What it adds is the half
that was never quantified: **"this edge misses F1 by 8.7 degrees"** instead of "this edge is
incorrect", and the same answer whether it is the first drawing of the evening or the fortieth.

The deliberate separation matters as much as the measurement. Plane A carries only numbers OpenCV
produced, and a validator rejects any figure the model did not get from it. Plane B carries only
what a teacher would say, and is forbidden from containing a number at all. The published rubrics
mix the two — *"vanishing points are correct"* is a geometric claim scored by eye — and that mixing
is precisely what makes them unrepeatable.

---

## Attribution

- Kennedy, Kristen. *Drawing Perspectives, Volume 2 (Art‑005B)*. College of Lemoore, Lemoore,
  California, 2024. Licensed **CC BY‑SA 4.0**; images excluded from that licence. Paraphrased and
  quoted here under the licence's attribution requirement.
- *ART 110 Basic Perspective*, BYU‑Idaho, Winter 2015. Rubric criteria quoted for commentary; no
  licence is stated by the source.
- *Grado en Animación (Fundamentos del Dibujo & Perspectiva Espacial)*, U‑tad (Centro Universitario
  de Tecnología y Arte Digital, Madrid). Learning outcomes and layout perspective criteria cited
  for pedagogical curriculum mapping.
- Duddy, Michael. *Introduction to Architecture, ARCH 1101, Course Outline*. CUNY New York City
  College of Technology, 2017. **CC BY 4.0**. Cited; document not retrievable and not used.
- Pozzo, Andrea. *Rules and Examples of Perspective proper for Painters and Architects*, 1693.
  Public domain, via Project Gutenberg.
