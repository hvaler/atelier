# Pedagogical grounding

Atelier measures technical drawings. This document places what it measures against what published
curricula actually require, so that the critique's vocabulary and its "next exercise" recommendation
are traceable to a taught discipline rather than invented in a prompt.

**The reference discipline is not artistic drawing.** It is **descriptive geometry** — *geometría
descriptiva* / *sistemas de representación*, the Monge tradition, taught as a first-year technical
subject in architecture, engineering, design and animation degrees. That distinction is the whole
argument of this document, because it changes what "correct" means. In artistic drawing a critique
is a judgement. In descriptive geometry a construction is either right or wrong, and the check is
itself a construction, not an opinion.

The studio rubric the agent applies derives from **real instructor rubrics for formal
descriptive-geometry coursework**, and is deliberately not attributed to any named institution or
individual. This document gives that rubric something public to be checked against, and something
to cite.

---

## 1. The discipline, and where perspective sits inside it

A **system of representation** is a rule for mapping three-dimensional space onto a plane such that
the mapping can be inverted: the drawing is not a picture of the object, it is a *notation* for it,
and a reader must be able to recover measurements from it. Gaspard Monge formalised this in the
1790s. Carnegie Mellon's notes for *48-175 Descriptive Geometry* state it plainly:

> "Descriptive geometry deals with manually solving problems in three-dimensional geometry by
> generating two-dimensional views."

Spanish technical faculties teach four systems, as **one subject** rather than four. The
Universidad de Granada's *Geometría Descriptiva* for the Grado en Edificación is organised as
exactly that:

| Block | System | What it is for |
|---|---|---|
| II | **Sistema diédrico** (Monge / orthographic) | Two or three mutually perpendicular views. The metric workhorse: true dimensions recoverable by construction |
| III | **Sistema de planos acotados** | One view plus numeric heights. Terrain, roofs, earthworks — the third dimension as a label rather than a second view |
| IV | **Sistema axonométrico** | One parallel projection showing three axes at once. Reads as a solid and stays measurable, at fixed axis angles |
| VI | **Sistema cónico** | Central projection. The only one that reproduces how the eye sees, and the only one where parallels converge |

Granada adds a fifth block for oblique projections — *"Proyección Caballera. Proyección Militar.
Sombras"* — which most curricula fold into the axonometric family.

**Conic perspective is one of four, and it is not the first.** Granada places it in Block VI, last.
The Universidad de Salamanca's *Geometría Descriptiva* at the Escuela Politécnica Superior de Zamora
never reaches it: its *temas* run diédrico → planos acotados → axonométrico ortogonal → axonométrico
oblicuo, and stop. Worth stating plainly, because a tool that began with perspective began at the
edge of the subject rather than its centre.

### What Atelier measures today

| System | Status | Where |
|---|---|---|
| **Cónico** (1- and 2-point) | ✅ Measured | `tools/geometry.py` — RANSAC vanishing-point estimation, per-line convergence error |
| **Axonométrico** (isometric, dimetric, cavalier) | ✅ Measured | `tools/axonometry.py` — every edge against the fixed axis angles of the system |
| **Diédrico** (two views) | ✅ Measured | `tools/dihedral.py` — correspondence between plan and elevation about the ground line |
| **Planos acotados** | ❌ Not measured | Needs numeric annotations read off the page: OCR, not line geometry |

Three of the four. Everything below that exceeds the engine's reach is recorded in the README's
gaps table and **deliberately not implemented**.

### The three references, ranked

The implemented systems differ in *where the thing being measured against comes from*, and that is
the honest way to rank how far each measurement can be trusted:

| System | Where the reference comes from | Trust |
|---|---|---|
| **Cónico** | **Inferred.** RANSAC estimates a vanishing point from the student's own lines | Weakest. A consistently wrong drawing yields a vanishing point that agrees with it, and the reported error shrinks |
| **Diédrico** | **Read off the page.** The ground line is a line the student drew | Middle. Nothing is guessed — but a crooked ground line skews everything measured against it, so its tilt is reported as a figure in its own right |
| **Axonométrico** | **Given.** The axes are constants of the projection system | Strongest. Nothing is estimated; an error injected at 6.00° returns as 6.00°, asserted to within 0.05° |

---

## 2. Sources, and what could be stored

Licence was verified before anything was downloaded. **Nothing from these sources is versioned in
this repository** — see the reason against each.

### The reference discipline: descriptive geometry

| Source | Licence | Stored here? |
|---|---|---|
| **Geometría Descriptiva (2301113)** — E.T.S. de Ingeniería de Edificación, Universidad de Granada. Grado en Edificación, 6 ECTS, 1st year, 1st semester. [Guía docente](https://etsie.ugr.es/docencia/grados/grado-edificacion/geometria-descriptiva/11/guia-docente) | **None stated** | **No.** Competences, the six-block *temario* and the published assessment weighting are quoted for commentary. |
| **Geometría Descriptiva (101002)** — E. Politécnica Superior de Zamora, Universidad de Salamanca. Grado en Arquitectura Técnica, 6 ECTS, 1st year. [Guía docente](https://guias.usal.es/node/141231) | **None stated** | **No.** *Temario* and assessment split quoted for commentary. |
| **Representació Arquitectònica I** — E.T.S. d'Arquitectura de Barcelona, Universitat Politècnica de Catalunya. [Course page](https://ra.upc.edu/ca/docencia/graus/asignatures-troncals/representacio-arquitectonica-i-etsab/representacio-arquitectonica-i-etsab) | **None stated** | **No.** Learning outcomes quoted in Catalan for commentary. |
| **Geometría Descriptiva (16002)** — Universidad de Alicante, Grado en Arquitectura Técnica, 6 ECTS, 1st year. [Ficha](https://cvnet.cpd.ua.es/Guia-Docente/?wlengua=es&wcodasi=16002&scaca=2018-19) | **None stated** | **No.** Competence G3 quoted; the published record carries no *temario*. |
| **E.T.S. de Arquitectura, Universidad Politécnica de Madrid** — published *guía de aprendizaje* competence framework. [PDF](https://www.upm.es/comun_gauss/publico/guias/2022-23/1S/GA_03AQ_35001901_1S_2022-23.pdf) | **None stated** | **No.** Only the CE-series competence wording is cited. **The document retrieved is a design-studio guide, not a descriptive-geometry one**, and is used for the competence framework and nothing else. |
| **48-175 Descriptive Geometry, Ch. 2** — Carnegie Mellon University. [Lecture notes PDF](https://www.andrew.cmu.edu/user/ramesh/teaching/course/48-175/lectures/2.BasicsOfDescriptiveGeometry.pdf) | **None stated** | **No.** Retrieved and read in full; formal definitions quoted. An institutional lecture note with no licence is all rights reserved. |
| **Sistema de Análisis de la Forma y la Representación (2651116)** — Facultad de Bellas Artes, Universidad de Granada. [Guía docente](https://bellasartes.ugr.es/docencia/grados/graduadoa-conservacion-y-restauracion-bienes-cultural/sistema-analisis-la-forma-y-la-representacion/11/guia-docente) | **None stated** | **No.** Shows the same discipline reaching a fine-arts faculty: *"Sistemas de Proyección Cilíndrica"* (Tema 5) before *"Perspectiva Cónica"* (Tema 6). |
| **Engineering Graphics and Design** — University of Washington, Pressbooks. [Book](https://uw.pressbooks.pub/enggraphics/chapter/orthographic-projection/) | **Not verified** | **No — could not be retrieved.** The host answers scripted requests with HTTP 403. A search result described it as CC BY-NC-SA 4.0, but **a licence nobody has read is not a licence**, so it is cited as unverified and not used. |

### Where the discipline reaches design and animation

| Source | Licence | Stored here? |
|---|---|---|
| **Honours Bachelor of Animation** — Sheridan College, Ontario. [Programme](https://www.sheridancollege.ca/programs/bachelor-of-animation) | **None stated** | **No.** Course sequence and programme learning outcomes quoted for commentary. |
| **BFA Character Animation** — CalArts. [Programme](https://catalog.calarts.edu/programs/UvzOg8mt3npdQQJrTCkI) · [FVCA‑140](https://catalog.calarts.edu/courses/FVCA140) · [FVCA‑240](https://catalog.calarts.edu/courses/FVCA240) | **None stated** | **No.** Two one-sentence catalogue entries quoted in full. |
| **BA Character Animation and Animated Filmmaking** — GOBELINS Paris. [Programme](https://www.gobelins-school.com/animated-filmmaking/programmes/ca30-bachelor-arts-character-animation-animated-filmmaking) | **None stated** | **No.** Subject list and entry aptitudes quoted for commentary. |
| **Bachelor in Animation — Study Program** — The Animation Workshop, VIA University College, 2016. [PDF](https://animationworkshop.via.dk/-/media/taw/pdf/ANIM/bachelor-in-animation-study-program-2016.pdf) | **None stated** | **No.** Retrieved and read; competency wording and ECTS structure quoted. |
| **Perspectiva y Técnicas de Representación / Fundamentos del dibujo** — Universitat Politècnica de València. [Subject](https://dibujo.webs.upv.es/asignatura/tecnicas-de-representacion-y-perspectiva/) · [Foundation](https://dibujo.webs.upv.es/asignatura/fundamentos-del-dibujo/) | **None stated** | **No.** Quoted in the original Spanish for commentary. |
| **CG Animation programme** — ESMA Montreal. [Programme](https://www.esma-3d.ca/en/formations/cg-animation-program/) | **None stated** | **No.** Only the portfolio requirement is quoted; the main site returns HTTP 403 to scripted requests. |

### The artistic counterpoint, used only as contrast in §7

| Source | Licence | Stored here? |
|---|---|---|
| **Drawing Perspectives, Volume 2 (Art‑005B)** — Kristen Kennedy, College of Lemoore, 2024. [PDF](https://lemoorecollege.edu/oer/documents/2024-drawing-perspectives-art-005b-oer-textbook.pdf) | **CC BY‑SA 4.0** for the text | **No.** The licence excludes the images: *"Some images are student work; all rights are reserved."* Redistributing the PDF would redistribute that. This repository is Apache‑2.0 and ShareAlike would extend to a derivative, so the material is paraphrased and cited rather than reproduced. |
| **ART 110 Basic Perspective** — BYU‑Idaho, Winter 2015. [Syllabus](https://courses.byui.edu/art110_new/Art110_S15/HTML/syllabus.html) · [Rubric](https://courses.byui.edu/art110_new/Art110_S15/HTML/rubric.html) | **None stated** | **No.** Short criterion wordings quoted as quotation for commentary. |
| **Introduction to Architecture, ARCH 1101** — Michael Duddy, CUNY City Tech, 2017. [Record](https://academicworks.cuny.edu/ny_oers/58/) | **CC BY 4.0** | **No — could not be retrieved.** The download endpoint answers scripted requests with HTTP 202/403. Cited for completeness and **not used**. |
| Pozzo, *Rules and Examples of Perspective*, 1693. [Gutenberg #56312](http://www.gutenberg.org/files/56312/56312-h/56312-h.htm) | **Public domain** | **No.** Freely storable; a link is enough for a 17th-century treatise nobody needs offline. |

**The pattern is worth naming.** Of eighteen sources, exactly two carry an open licence and neither
could be stored — the CC BY‑SA textbook excludes its own figures, and the CC BY course outline
cannot be downloaded. Every other source is an institutional page, programme specification or
lecture note with no licence statement, which means all rights reserved. **Published curricula are
public to read and not free to redistribute**, and the two are easy to confuse.

---

## 3. Assessment criteria: the public sources against Atelier's

The left column quotes or closely paraphrases a source. The right names what Atelier computes, and
where.

| Public criterion | Source | Atelier |
|---|---|---|
| CE13 *"Conocimiento de los distintos sistemas de representación espacial propios de la Geometría Descriptiva"* | UGR Edificación | Three of the four systems implemented as separate engines with separate result shapes; the vision gate picks which before anything is measured |
| Learning outcome: *"Capacidad para aplicar los sistemas de representación espacial"* | UGR Edificación | The measurement is of the *application*: does this construction obey the system it claims to be in |
| CE3 *"Capacidad para aplicar los sistemas de representación espacial, el desarrollo del croquis, la proporcionalidad, el lenguaje y las técnicas de la representación gráfica"* | USAL Zamora | Convergence, axis angle and correspondence are measured. **Proportionality is not** |
| *"Reconèixer i interpretar els objectes a partir d'imatges representades en axonometria, cònica, planta, alçats i/o seccions"* | UPC ETSAB | This recognition step is exactly what the gate performs — conic vs axonometric vs orthographic — before measuring |
| CE3 *"Conocimiento adecuado y aplicado a la arquitectura y al urbanismo de los sistemas de representación espacial"* | UPM ETSAM | — |
| G3 *"Capacidad para aplicar los sistemas de representación espacial…"* | U. Alicante | — |
| Definition 2‑9: *"Two views obtained from two perpendicular picture planes are called adjacent"* | CMU 48‑175 | `tools/dihedral.py` measures the consequence: a point's projections in adjacent views must correspond, on a line perpendicular to the ground line |
| Block I: *"cambios de plano, abatimientos, giros y verdaderas magnitudes"* | UGR Edificación | **Not measured.** Recovering a true length by rabatment has a checkable result, and the engine does not check it |
| Assessment weighting published per block: 40 / 40 / 10 / 5 / 5 | UGR Edificación | Atelier weights nothing. It reports per-metric figures and leaves weighting to a teacher |
| *"Es necesario superar cada bloque de forma independiente para superar la asignatura"* | USAL Zamora | Mirrored by construction: each system has its own engine, its own metrics and its own validator whitelist. A pass in one says nothing about another |
| Theory tests 60% of the mark, **minimum 5/10 required in each section** | UGR Edificación | The architectural echo of the same idea — systems are not matters of degree, and are not compensable |
| Programme outcome: *"Design layouts and backgrounds that incorporate principles of composition, **perspective** and colour, with speed, **accuracy** and dexterity"* | Sheridan College | The only source in the whole set that names *accuracy* as a graded outcome — and it still states no tolerance |

### What the public criteria assess that Atelier does not

Recorded here, and in the README's gaps table, as **not implemented**:

- **Proportionality and dimensional fidelity.** Named by USAL and UPM; needs a known scale on the page.
- **Abatimientos, giros, cambios de plano, verdaderas magnitudes.** Named by UGR and USAL. Checkable in principle — a rabatment either recovers the true length or it does not — and unimplemented.
- **Planos acotados.** Contours, slopes, roof solutions, earthworks. Needs numeric annotations read off the page.
- **Sombras.** Named by UGR in the oblique-projection block. Cast-shadow construction converges on its own points and is geometric, so measurable in principle.
- **Intersections of surfaces and solids.** Named by UGR in Block I.
- **CAD deliverables.** UGR assesses DWG submissions. Atelier reads a photograph of a drawing.

---

## 4. Canonical vocabulary, bilingual

The critique must use the discipline's terms, in the student's language. These are the terms as the
sources above use them; the agent's prompts and the interface's string table both follow this list.

| Español | English | What it denotes |
|---|---|---|
| Sistema de representación | System of representation | An invertible rule mapping space onto the plane |
| Sistema diédrico | Dihedral / orthographic (Monge) system | Two or three mutually perpendicular views |
| Sistema axonométrico | Axonometric system | A single parallel projection showing three axes |
| Sistema de planos acotados | Contoured-plane system | One view plus numeric heights |
| Sistema cónico | Conic / central-projection system | Perspective; the only system where parallels converge |
| Perspectiva cónica frontal | One-point (frontal) perspective | One vanishing point; picture plane parallel to a principal face |
| Perspectiva cónica oblicua | Two-point (oblique) perspective | Two vanishing points on the horizon |
| Línea de tierra (LT) | Ground line | The fold between projection planes; the reference for orthographic correspondence |
| Línea de horizonte (LH) | Horizon line | The locus of vanishing points, at eye level |
| Puntos de fuga (F1, F2) | Vanishing points | Where a family of parallel receding edges meets |
| Punto de vista; punto principal | Station point; principal point | The observer, and the foot of the perpendicular from it to the picture plane |
| Puntos métricos; puntos de distancia | Measuring points; distance points | Auxiliary points that carry true dimensions into a perspective |
| Verdadera magnitud | True length / true size | A dimension recovered without foreshortening |
| Abatimiento | Rabatment | Rotating a plane into the picture plane to read true size |
| Giro; cambio de plano | Rotation; change of reference plane | The other two routes to true size |
| Trazas de un plano | Traces of a plane | Where a plane meets the projection planes |
| Planta, alzado, perfil | Plan, elevation, profile | The three principal orthographic views |
| Línea de referencia | Reference / projector line | Carries a point between adjacent views, perpendicular to the LT |
| Coeficiente de reducción | Foreshortening coefficient | The scale factor along an axonometric axis |
| Peso de línea | Line weight | Light construction traces against dark definitive edges |

Two notes on how this list is used. First, **the metric identifiers on the wire stay English**
(`average_convergence_error`, `axis_x_systematic_error`, `systematic_offset`) because the validator
matches on them; they are looked up for display, so a Spanish reader sees Spanish. Second,
**Plane B may not contain a number at all**, in either language — the prose gate recognises
*grados* as well as *degrees*, because a gate that only reads English stops being a gate the moment
the interface is translated.

---

## 5. The documented exercise progression

This is the citable basis for the agent's `next_exercise` recommendation. It is not a sequence
invented to fill a field in a JSON schema; it is the order the sources publish.

**Universidad de Granada** orders its blocks: planar geometry and true magnitudes → **diédrico** →
planos acotados → **axonométrico** → oblique projections and shadows → **cónico, last**.

**Universidad de Salamanca** orders its *temas*: geometric transformations → **diédrico** (point,
line, plane; then intersection, parallelism, perpendicularity, distances, rotations, *abatimientos*,
changes of plane) → surfaces → **planos acotados** → **axonométrico ortogonal** → **axonométrico
oblicuo** (caballera, militar).

**Universidad de Granada, Bellas Artes** confirms the ordering in a different faculty: Tema 5
*"Sistemas de Proyección Cilíndrica"* — parallel projection — precedes Tema 6
*"Perspectiva Cónica"*.

**Within conic perspective specifically**, the sequence the sources document runs:

```
one-point frontal: a box, picture plane parallel to its front face
        ↓
one-point: combined volumes, interiors
        ↓
two-point oblique: a solid at an angle, F1 and F2 on the horizon
        ↓
measuring points and distance points: true dimensions inside the perspective
        ↓
rabatment and true magnitudes
        ↓
cast shadows
        ↓
complex scenes; three-point for tall subjects
```

Two facts about this ladder matter for the agent:

1. **Parallel projection is taught before central projection.** Both Spanish technical sources put
   diédrico first and cónico last or not at all, and the fine-arts faculty agrees. A tool that only
   measured perspective would be grading the end of the course.
2. **Atelier can currently recommend the first three rungs and no further.** Measuring points,
   rabatment, shadows and three-point are documented pedagogy the engine cannot assess, so the agent
   must not prescribe them. They are in the README's gaps table.

---

## 6. The same discipline in design and animation degrees

Descriptive geometry is not confined to architecture and engineering, which matters because it is
where Atelier's own users are. Every cell below is quoted or closely paraphrased from the page
linked in §2. Where a programme does not name a topic, that is recorded as an absence.

| Institution | Subject / module | Competency, as published | Progression |
|---|---|---|---|
| **Sheridan College** (Canada, public) — Honours Bachelor of Animation | *Principles of Layout 1* → *2* → *2D Layouts* → *CG Layouts* → *Layout: Pre-Production* → *Layout: Production* | *"Design layouts and backgrounds that incorporate principles of composition, **perspective** and colour, with speed, **accuracy** and dexterity"* | Six consecutive semesters of layout, spiralling |
| **CalArts** (USA) — BFA Character Animation | **FVCA‑140 *Perspective I*** (BFA1 spring, 1.5 cr); **FVCA‑240 *Animation Layout*** (BFA2 autumn) | FVCA‑140 in full: *"Basic rendering and perspective drawing."* | A discrete first-year course, never revisited under that name |
| **GOBELINS Paris** (France) | *Drawing for animation* | *"Drawing for animation: volume construction, perspective, image composition, movement analysis."* | Perspective never isolated; bundled with volume construction from the outset |
| **The Animation Workshop / VIA** (Denmark, public) | Common modules include *Drawing* and *Layout*; CG line adds *Digital Layout*, *Environment Design and Construction* | **Perspective is never named.** The nearest published competency is *"relevant design and composition theories"* | Spatial construction taught as *layout*, with perspective assumed inside it |
| **Universitat Politècnica de València** (Spain, public) — Bellas Artes | *Fundamentos del dibujo* → *Perspectiva y Técnicas de Representación* | *"…tomando como base el estudio y práctica de la Perspectiva cónica geométrica"* | Perspective **frontal → oblicua → de plano inclinado**, then applied work |
| **ESMA** (France / Canada) | Not a subject of the 3D degree | Screened at admission: portfolio must show observation drawings of *"Faces, Bodies / Anatomy, Sceneries, **Perspectives**, Architecture"* | A prerequisite competency, taught in the preparatory year |

**What is common.** Perspective is a first- or second-year competency everywhere, and it is assessed
as part of spatial construction rather than as drafting. Sheridan binds it to composition and colour
in one sentence; GOBELINS to volume construction and movement analysis; Denmark folds it into
*Layout* without naming it. This is a direct argument for the two-plane split: the trade does not
separate the geometry from the picture, so a tool reporting only the geometry must hand the rest to
something that can talk about the picture.

**What is specific — and therefore what "next" could mean.** Valencia adds *plano inclinado*
(three-point) and anamorphosis; Granada adds shadows and reflections; Sheridan adds CG layout as
distinct from 2D; The Animation Workshop adds whole-scene environment construction. None are
implemented; each is a rung with a named source rather than an opinion.

---

## 7. The finding

**In this discipline, correctness is objective — and the feedback is still manual.**

That is the whole argument, and it has two halves.

### Correctness is objective

Artistic drawing rubrics score qualities. Lemoore's assessment criteria are percentages over
judgements — *"Accuracy of Observation (30%)"*, *"Technical Skill (30%)"* — with descriptors like
*"precision and detail in capturing the forms"*. BYU‑Idaho's is the more geometric of the two and
still resolves only to a count: *"1‑3 foreshortened lines go to incorrect vanishing points"* against
*"4 or more"*.

Descriptive geometry is not like that. A construction is right or wrong, and the check is itself a
construction: a rabatment either recovers the true length or it does not; a point's plan either lies
on the reference line dropped from its elevation or it does not; an isometric axis is at 30° or it
is not. Nothing here depends on an examiner's taste. Granada's assessment reads accordingly — theory
tests at **60%**, with a **minimum of 5/10 required in each section independently**, and Salamanca's
rule that *"es necesario superar cada bloque de forma independiente"*. A strong system cannot
compensate a failed one, because these are not matters of degree.

### And yet nobody quantifies the error

**Not one of the eighteen sources states a numerical tolerance.** Nowhere does a figure in degrees
or millimetres appear as a pass mark. Sheridan comes closest and is worth quoting again — *"with
speed, **accuracy** and dexterity"* — where accuracy is a graded outcome of a four-year honours
degree and the curriculum never says how accurate.

The discipline defines correctness exactly, and then hands the checking to a person with a set
square at the end of a stack of plates.

That is the gap Atelier occupies, and it is narrow on purpose:

> **Atelier automates the objective verification the discipline already defines. It does not invent
> a new criterion.**

The distinction matters. Nothing in this project decides what *good* means in descriptive geometry —
the syllabi above decided, and decided precisely. What did not exist was a way to answer *"is this
edge on the axis?"* in under a second, a hundred times, with the same answer every time:

- **"This edge misses F1 by 8.7 degrees"** instead of *this edge is incorrect*.
- **"The X family is 6.00° off, all of it, the same way"** instead of *the axonometric is careless* —
  a systematic error is a set square placed wrong, and it is fixed once, before drawing.
- **"The plan sits 18 px to the right"** instead of *the views do not correspond* — one placement
  mistake rather than one broken vertex per corner.

The two-plane split follows from the same idea. Plane A carries only numbers OpenCV produced, and a
validator rejects any figure the model did not get from it. Plane B carries only what a teacher
would say and is forbidden a number at all. The published rubrics mix the two — *"vanishing points
are correct"* is a geometric claim scored by eye — and that mixing is what makes them unrepeatable.
Separating them is not a presentation decision; it is the difference between a measurement and an
impression.

---

## Attribution

**Descriptive geometry sources**

- *Geometría Descriptiva* (2301113), E.T.S. de Ingeniería de Edificación, Universidad de Granada. Competences, *temario* and assessment weighting quoted for commentary; no licence stated.
- *Geometría Descriptiva* (101002), E. Politécnica Superior de Zamora, Universidad de Salamanca. *Temario* and assessment split quoted for commentary; no licence stated.
- *Representació Arquitectònica I*, E.T.S. d'Arquitectura de Barcelona, Universitat Politècnica de Catalunya. Learning outcomes quoted in Catalan for commentary.
- *Geometría Descriptiva* (16002), Universidad de Alicante. Competence G3 quoted for commentary.
- *Guía de aprendizaje*, E.T.S. de Arquitectura, Universidad Politécnica de Madrid. CE-series competence wording quoted; the retrieved document is a design-studio guide and is used for nothing else.
- *48-175 Descriptive Geometry*, Carnegie Mellon University. Definitions quoted for commentary; no licence stated.
- *Sistema de Análisis de la Forma y la Representación* (2651116), Facultad de Bellas Artes, Universidad de Granada. *Temario* quoted in Spanish for commentary.
- *Engineering Graphics and Design*, University of Washington. Cited as unverified; could not be retrieved and is not used.

**Design and animation programmes**

- *Honours Bachelor of Animation*, Sheridan College, Ontario. Course sequence and programme learning outcomes quoted for commentary.
- *BFA Character Animation*, California Institute of the Arts. Catalogue entries for FVCA‑140 and FVCA‑240 quoted for commentary.
- *BA Character Animation and Animated Filmmaking*, GOBELINS Paris. Subject list and entry aptitudes quoted for commentary.
- *Bachelor in Animation — Study Program*, The Animation Workshop, VIA University College, 2016. Competency wording and ECTS structure quoted for commentary.
- *Perspectiva y Técnicas de Representación* and *Fundamentos del dibujo*, Departamento de Dibujo, Universitat Politècnica de València. Quoted in Spanish for commentary.
- *CG Animation programme*, ESMA Montreal. Portfolio requirement quoted for commentary.

**Artistic counterpoint**

- Kennedy, Kristen. *Drawing Perspectives, Volume 2 (Art‑005B)*. College of Lemoore, 2024. **CC BY‑SA 4.0**, images excluded. Paraphrased and quoted under the licence's attribution requirement.
- *ART 110 Basic Perspective*, BYU‑Idaho, Winter 2015. Rubric criteria quoted for commentary; no licence stated.
- Duddy, Michael. *Introduction to Architecture, ARCH 1101*. CUNY City Tech, 2017. **CC BY 4.0**. Cited; document not retrievable and not used.
- Pozzo, Andrea. *Rules and Examples of Perspective*, 1693. Public domain, via Project Gutenberg.

**Internal**

- The studio rubric the agent applies derives from real instructor rubrics for formal
  descriptive-geometry coursework. It is not reproduced here and its source is not named.
