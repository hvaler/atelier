# Pedagogical grounding

Atelier grades perspective drawings. This document places what it measures against what published
art curricula actually ask of a student, so that the critique's vocabulary and its "next exercise"
recommendation are traceable to teaching practice rather than invented in a prompt.

It does **not** replace the studio rubric the agent already uses — which derives from real
instructor rubrics for formal perspective‑drawing coursework, and is deliberately not attributed to
any named institution or individual. This document gives that rubric something to be checked
against, and something to cite.

---

## 1. Sources, and what could be stored

Licence was verified before anything was downloaded. **Nothing from these sources is versioned in
this repository** — see the reason against each.

| Source | Licence | Stored here? |
|---|---|---|
| **Drawing Perspectives, Volume 2 (Art‑005B)** — Kristen Kennedy, College of the Sequoias / Lemoore College, 2024. 121 pp. [PDF](https://lemoorecollege.edu/oer/documents/2024-drawing-perspectives-art-005b-oer-textbook.pdf) | **CC BY‑SA 4.0** for the text | **No.** The licence excludes itself from the images: *"Images and figures within this text are openly licensed, in the Public Domain, or used based on fair use principles. Some images are student work; all rights are reserved."* Redistributing the PDF would redistribute that student work. Cited and quoted only. |
| **ART 110 Basic Perspective** — BYU‑Idaho, Winter 2015 course site. [Syllabus](https://courses.byui.edu/art110_new/Art110_S15/HTML/syllabus.html) · [Rubric](https://courses.byui.edu/art110_new/Art110_S15/HTML/rubric.html) | **None stated** on any page of the course site | **No.** Absent a licence, the default is all rights reserved. Short criterion wordings are quoted below as quotation for commentary. |
| **Honours Bachelor of Animation** — Sheridan College, Ontario. [Programme page and course sequence](https://www.sheridancollege.ca/programs/bachelor-of-animation) | **None stated** | **No.** Course sequence and the programme's own learning outcomes quoted for commentary. |
| **BFA Character Animation** — California Institute of the Arts. [Programme](https://catalog.calarts.edu/programs/UvzOg8mt3npdQQJrTCkI) · [FVCA‑140 *Perspective I*](https://catalog.calarts.edu/courses/FVCA140) · [FVCA‑240 *Animation Layout*](https://catalog.calarts.edu/courses/FVCA240) | **None stated** | **No.** Two one‑sentence catalogue descriptions quoted in full; there is nothing else to store. |
| **Bachelor in Character Animation and Animated Filmmaking** — GOBELINS Paris. [Programme](https://www.gobelins-school.com/animated-filmmaking/programmes/ca30-bachelor-arts-character-animation-animated-filmmaking) | **None stated** | **No.** Subject list and entry aptitudes quoted for commentary. |
| **Bachelor in Animation — Study Program, Animation and CG Arts** — The Animation Workshop, VIA University College, Denmark, 2016. [PDF](https://animationworkshop.via.dk/-/media/taw/pdf/ANIM/bachelor-in-animation-study-program-2016.pdf) | **None stated** | **No.** An 18‑page institutional programme specification with no licence. Retrieved and read; competency wording and the ECTS structure are quoted, the file is not versioned. |
| **Grado en Bellas Artes — *Perspectiva y Técnicas de Representación* y *Fundamentos del dibujo*** — Universitat Politècnica de València (public). [Departamento de Dibujo](https://dibujo.webs.upv.es/asignatura/tecnicas-de-representacion-y-perspectiva/) · [Fundamentos del dibujo](https://dibujo.webs.upv.es/asignatura/fundamentos-del-dibujo/) | **None stated** | **No.** Subject descriptions quoted in the original Spanish for commentary. |
| **Guía docente de *Sistema de Análisis de la Forma y la Representación* (2651116)** — Facultad de Bellas Artes, Universidad de Granada (public). [Guía docente](https://bellasartes.ugr.es/docencia/grados/graduadoa-conservacion-y-restauracion-bienes-cultural/sistema-analisis-la-forma-y-la-representacion/11/guia-docente) | **None stated** | **No.** Competences and *temario* quoted in the original Spanish for commentary. |
| **CG Animation programme (Montreal campus)** — ESMA. [Programme](https://www.esma-3d.ca/en/formations/cg-animation-program/) | **None stated** | **No.** Only the portfolio requirement is quoted; the school's main site returns HTTP 403 to scripted requests, so its richer preparatory‑year syllabus **could not be retrieved and is not cited**. |
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

The Universitat Politècnica de València sets the same order inside a single subject. Its
*Perspectiva y Técnicas de Representación* is built on *"el estudio y práctica de la Perspectiva
cónica geométrica"* and works through perspective **frontal → oblicua → de plano inclinado** — which
is one‑point, then two‑point, then three‑point, in the vocabulary of a Spanish fine‑arts faculty.

Consolidated across these curricula, the published sequence guides a student as:

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
| Three‑point perspective | `k=3` is unimplemented; the solver handles k=1 and k=2 only. Valencia teaches it as *perspectiva de plano inclinado*, in the same subject as the other two. |
| Cast shadows and reflections | Granada's Tema 7 is *"Perspectiva aplicada. Luz y sombra. Reflejos"*. Shadow construction converges on its own points and is geometric, so it is measurable in principle — but nothing in the engine looks for it. |
| Whole‑scene layout | The Animation Workshop teaches *Environment Design and Construction* and *Shot Production: 2D Backgrounds*. Atelier measures one construction at a time. |

Two of these rungs became citable only after §5 widened the source base: three‑point perspective
and shadow construction are now named in a public Spanish syllabus rather than inferred.

---

## 5. Cross-institutional curriculum comparison

The two sources in §2 are a Californian community college and an American university's online
course. Both are American, both are general studio drawing, and a progression derived from two
such sources could fairly be called parochial. This section widens the base to **seven programmes
across five countries**, mixing animation schools with public fine‑arts faculties, to test whether
the ladder in §4 is the trade's or this project's.

Every cell below is quoted or closely paraphrased from the page linked in §1. Where a programme
does not name perspective, that is recorded as an absence rather than filled in.

| Institution | Subject / module | Perspective competency, as published | Progression |
|---|---|---|---|
| **Sheridan College** (Canada, public college) — Honours Bachelor of Animation | *Principles of Layout 1* (Sem 1) and *2* (Sem 2); *2D Layouts* (Sem 3); *CG Layouts* (Sem 4); *Layout: Pre‑Production* (Sem 5); *Layout: Production* (Sem 6) | Programme learning outcome: *"Design layouts and backgrounds that incorporate principles of composition, **perspective** and colour, **with speed, accuracy and dexterity**, using a variety of media"* | Six consecutive semesters of layout, spiralling: principles → 2D → CG → pre‑production → production. Drawing runs in parallel: *Introduction to Life Drawing* → *Introduction to Dynamic Anatomy* → *Intermediate Figure Analysis* → *Exploration of Figure Analysis* |
| **CalArts** (USA) — BFA Character Animation | **FVCA‑140 *Perspective I*** (BFA1, spring, 1.5 credits); **FVCA‑240 *Animation Layout*** (BFA2, autumn, 1.5 credits) | FVCA‑140 in full: *"Basic rendering and perspective drawing."* FVCA‑240 in full: *"Basic composition and design of layout animation techniques."* | Perspective is a discrete first‑year course and does not recur under that name; layout follows in year 2, then *Advanced Life Drawing* (FVCA‑311–316) in years 3–4 |
| **GOBELINS Paris** (France) — BA Character Animation and Animated Filmmaking | *Drawing for animation* | *"Drawing for animation: volume construction, perspective, image composition, movement analysis."* Entry aptitude: *"A regular draughtsman with a predisposition for expressing movement, volume and perspective."* | 3 years. Perspective is never isolated — it is bundled with volume construction, composition and movement analysis from the outset |
| **The Animation Workshop / VIA University College** (Denmark, public) — Bachelor in Animation | Common modules (60 ECTS) include *Drawing* and *Layout*; the CG Arts line (90 ECTS) adds *Digital Layout* and *Environment Design and Construction*; electives add *Advanced Digital Layout* and *Shot Production: 2D Backgrounds* | **Perspective is never named.** The nearest published competency is knowledge of *"relevant design and composition theories and the ability to reflect on the implementation of these theories within animation media"* | Common modules → study line → electives. Spatial construction is taught as *layout*, and perspective is assumed inside it |
| **Universitat Politècnica de València** (Spain, public) — Grado en Bellas Artes | *Fundamentos del dibujo* (1st year) → *Perspectiva y Técnicas de Representación* | *"Esta asignatura atiende a las diferentes maneras de ver y representar el espacio tridimensional en el plano, tomando como base el estudio y práctica de la Perspectiva cónica geométrica"*; the foundation subject *"enseña a ver"* and teaches *"la representación gráfica objetiva del mundo de las formas"* | Perspective **frontal → oblicua → de plano inclinado** (one‑, two‑ and three‑point), then natural/observational perspective, then applied work in comic, illustration, mural and floor painting, ending at anamorphosis and impossible figures |
| **Universidad de Granada** (Spain, public) — Facultad de Bellas Artes | *Sistema de Análisis de la Forma y la Representación* (2651116), 6 ECTS, **curso 1, semestre 2** | CE13: *"Comprender y aplicar los fundamentos de dibujo, color y volumen."* Learning outcomes: *"Conocer los sistemas de representación del espacio"* and *"la percepción espacial tridimensional desde las representaciones bidimensionales"* | Bloque III *"Geometría descriptiva, Sistemas de Representación y el Espacio Perspectivo"* → Tema 5 *"La Geometría Proyectiva. Sistemas de Proyección Cilíndrica. Representación de cuerpos"* → Tema 6 *"La Perspectiva* Artificialis *y el Sistema de Proyección Central: Perspectiva Cónica"* → Tema 7 *"Perspectiva aplicada. Luz y sombra. Reflejos"* |
| **ESMA** (France / Canada) — CG Animation programme, Montreal | Six sessions; perspective is not a listed subject of the 3D programme | Screened at the door instead: the portfolio must show *"good skills in traditional drawing"* and observation drawings of *"Faces, Bodies / Anatomy, Sceneries, Animals, **Perspectives**, Architecture"* | Perspective is a prerequisite competency, taught in the preparatory year and assumed thereafter |

### What every programme has in common

**One. Perspective is a first‑ or second‑year competency, everywhere.** CalArts places it in the
spring of year one. Granada places it in *curso 1, semestre 2*. Sheridan opens semester one with
*Principles of Layout 1*. ESMA does not teach it in the degree at all because it expects it at
admission. No programme in this table treats perspective as advanced material.

**Two. It is assessed as part of spatial construction, not as drafting.** Sheridan's outcome binds
perspective to composition and colour in the same sentence; GOBELINS binds it to volume
construction and movement analysis; Denmark does not name it at all and folds it into *Layout*.
This is a direct argument for Atelier's two‑plane split: the trade does not separate the geometry
from the picture, so a tool that reports only the geometry has to hand the rest to something that
can talk about the picture.

**Three — and this is the one that matters — not one of the seven states a numerical tolerance.**
Sheridan gets closest and is worth quoting again: *"with speed, accuracy and dexterity."* **Accuracy**
appears as a graded programme outcome across a four‑year honours degree, and nowhere in the
published curriculum does anything say how accurate. §6 draws that conclusion from two American
sources; it holds across all seven, in five countries, quoted in two languages, spanning public
universities and private animation schools alike. It is not an artefact of the sample.

**Four. The taught order is the same order.** Foundation drawing, then one‑point, then two‑point,
then applied scenes. Valencia states it as *frontal → oblicua → de plano inclinado*; Granada as
descriptive geometry → central projection → applied perspective; Lemoore as interior → street →
tall building. Three curricula written independently, in two languages, in the same sequence.

**This is what licenses the agent's `next_exercise` recommendation.** The ladder in §4 is not a
sequence invented to fill a field in a JSON schema. It is the sequence seven institutions publish.

### What is specific to each — and therefore what "next" could mean

The differences are as useful as the agreement, because each one names a rung beyond where Atelier
currently reaches. None of these are implemented; they are recorded here so that the gaps table in
the README has a source rather than an opinion.

| Programme | What it adds that the others do not | Where it sits relative to Atelier |
|---|---|---|
| Universitat Politècnica de València | *Perspectiva de plano inclinado* — three‑point — plus anamorphosis and impossible figures | `k=3` is unimplemented; the solver handles k=1 and k=2 |
| Universidad de Granada | *"Perspectiva aplicada. Luz y sombra. Reflejos"* — shadow and reflection construction in perspective | Not measured. Cast‑shadow convergence is geometric and would be measurable in principle |
| Sheridan College | *CG Layouts* as a competency distinct from *2D Layouts* | Out of scope: Atelier measures a photograph of a drawing |
| The Animation Workshop | *Environment Design and Construction*, *Shot Production: 2D Backgrounds* | Whole‑scene layout rather than a single construction; untested |
| GOBELINS Paris | Perspective tied explicitly to **movement analysis** | Out of scope: single still images |
| CalArts | Perspective as a closed 1.5‑credit unit, then never revisited under that name | Matches Atelier's scope almost exactly — this is the rung the tool occupies |

The last row is the useful one for positioning. CalArts spends 1.5 credits on *"basic rendering and
perspective drawing"* in the first year and then assumes it forever. That single course, assessed by
eye once and never re‑measured, is precisely the interval where a student either acquires accurate
convergence or does not — and it is the interval Atelier instruments.

---

### The subject that contains perspective

Everything above treats conic perspective as the subject. In the Spanish public syllabi it is not:
it is one topic inside **Sistemas de Representación**, and it is not the first one.

Granada's *temario* orders it plainly. **Tema 5** is *"La Geometría Proyectiva. Sistemas de
Proyección Cilíndrica. Representación de cuerpos"* — cylindrical projection is parallel projection,
which is to say axonometry — and only **Tema 6** reaches *"el Sistema de Proyección Central:
Perspectiva Cónica"*. The complementary bibliography names it outright: Bonet Minguet, *Perspectiva
axonométrica y caballera*, and Thomae, *Perspectiva y axonometría*. Valencia's subject works the
same ground from the other side, covering perspective **frontal, oblicua y de plano inclinado**.

**Parallel projection is taught before conic perspective, not after it.** That ordering is a
finding, not a detail, and it has a consequence for what a measuring tool should cover first.

**Atelier now measures all three.** `tools/axonometry.py` compares every detected edge against the
fixed axes of isometric, dimetric or cavalier projection; `tools/dihedral.py` checks the two views
of a Monge plate against each other about the ground line. The vision gate decides which of the
three a photograph is before anything is measured — because running a parallel projection through
the perspective path finds a vanishing point among edges that were never meant to meet, and then
reports an error about it, and running an orthographic plate through either is worse still, since
there is no solid in it to measure at all.

The three differ in **where their reference comes from**, and that is the useful way to rank them:

| System | Where the reference comes from | How much to trust it |
|---|---|---|
| Conic perspective | **Inferred.** RANSAC estimates a vanishing point from the student's own lines | Weakest. A consistently wrong drawing yields a vanishing point that agrees with it |
| Orthographic (Monge) | **Read off the page.** The ground line is a line the student drew | Middle. Nothing is guessed, but a crooked ground line skews everything, so its tilt is reported as a figure in its own right |
| Axonometric | **Given.** The axes are constants of the projection system | Strongest. Nothing is estimated; an error injected at 6.00° returns as 6.00° |

The interesting part is that the second mode is **more** trustworthy than the first, which is the
opposite of what a bolted-on feature usually is. Section 6 states the weakness of the conic path
honestly: RANSAC estimates the vanishing point from the student's own lines, so a drawing that is
consistently wrong yields a vanishing point that agrees with it. Axonometry has no such estimator.
The axes of an isometric projection are at 30, 90 and 150 degrees **by definition of the system**.
Nothing is inferred; every edge is compared against a constant. In the golden case, an error
injected at exactly 6 degrees is recovered as exactly 6 degrees, and the test asserts it to within
0.05 — a bound the perspective suite could never hold.

It also separates two errors that a single average hides, and which need different corrections:

| What the numbers say | What it means | What the student does |
|---|---|---|
| Low per-line error, low systematic error | The axes were set right and followed steadily | Move on |
| Low per-line error, **high systematic error** | Every edge of one family is off by the same amount — the set square was placed wrong | Fix the axis once, before drawing |
| **High per-line error**, low systematic error | The axis was right and the hand wandered | Steadier construction, edge by edge |

The orthographic engine draws the same distinction with a different pair. A plan displaced sideways
as a whole is **one** mistake that every vertex inherits — the plan was placed wrong on the page —
and it is reported once, as a systematic offset, then removed before the per-vertex check runs. What
survives that is a genuinely unmatched vertex: a corner drawn in one view and never answered in the
other, which is a construction error rather than a placement one and the more serious of the two.
Averaged together the two are indistinguishable, and the correction for each is different.

A published rubric cannot make that distinction, because making it requires measuring each family's
mean direction separately and comparing it against a constant. This is the same argument as §6,
one level sharper: the gap is not that instructors are imprecise, it is that the distinction is
invisible without measurement.

---

## 6. The finding

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
- *Honours Bachelor of Animation*, Sheridan College, Ontario. Course sequence and programme
  learning outcomes quoted for commentary; no licence is stated by the source.
- *BFA Character Animation*, California Institute of the Arts. Catalogue entries for FVCA‑140
  *Perspective I* and FVCA‑240 *Animation Layout* quoted for commentary.
- *Bachelor in Character Animation and Animated Filmmaking*, GOBELINS Paris. Subject list and entry
  aptitudes quoted for commentary.
- *Bachelor in Animation — Study Program, Animation and CG Arts*, The Animation Workshop, VIA
  University College, Denmark, 2016. Competency wording and ECTS structure quoted for commentary.
- *Perspectiva y Técnicas de Representación* and *Fundamentos del dibujo*, Departamento de Dibujo,
  Universitat Politècnica de València. Subject descriptions quoted in Spanish for commentary.
- *Sistema de Análisis de la Forma y la Representación* (2651116), Facultad de Bellas Artes,
  Universidad de Granada. Competences and *temario* quoted in Spanish for commentary.
- *CG Animation programme*, ESMA Montreal. Portfolio requirement quoted for commentary.
- The studio rubric the agent applies derives from real instructor rubrics for formal
  perspective‑drawing coursework. It is not reproduced here and its source is not named.
- Duddy, Michael. *Introduction to Architecture, ARCH 1101, Course Outline*. CUNY New York City
  College of Technology, 2017. **CC BY 4.0**. Cited; document not retrievable and not used.
- Pozzo, Andrea. *Rules and Examples of Perspective proper for Painters and Architects*, 1693.
  Public domain, via Project Gutenberg.
