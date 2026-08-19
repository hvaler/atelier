# Video Recording & Submission Runbook — Atelier

> **Hackathon requirement**: video ≤ 4 minutes (aim for 3:15–3:40), uploaded to YouTube as **public**.
> **Mandatory**: a live, **uncut** segment of the agent doing its job, plus proof of the Google Cloud
> deployment (Cloud Run, Eventarc, Firestore, Vertex AI).

Phase 2 is the uncut take. Everything else may be cut together.

---

## Before you press record

1. **Warm the services.** Both Cloud Run services scale to zero. Hit them twice, a minute apart:
   ```bash
   curl -s https://atelier-agent-3hacbhowpq-ew.a.run.app/api/health
   curl -s https://atelier-web-3hacbhowpq-ew.a.run.app/api/health
   ```
   A cold start in the middle of an uncut take costs you thirty seconds of silence.
2. **Open the studio once and run one analysis** to warm the Vertex path, then reload. The take
   starts from a clean page.
3. **Set the interface to the language you will narrate in.** The picker is top-right; the choice
   writes a cookie and reloads.
4. **Pick your theme.** Dark reads better against a screen recording; light reads better if you are
   also showing paper. Decide before, not during.
5. **Collapse or expand the rail deliberately.** It remembers, so whatever you leave it as is what
   the take opens with.
6. **Have a page of handwriting ready** as an image file, for the refusal beat.
7. **Do not clear Firestore.** `level-basic` carries real accumulated history, and the history panel
   and progression page are worth more full than empty.

---

## Phase 1 — The problem (0:00 – 0:35)

- **Visual**: you on webcam, holding a drawing on paper. A technical drawing, not a sketch — an
  isometric cube or a two-view plate reads better than a doodle.
- **Say**, in your own words, the argument the project rests on:
  - The reference discipline is **descriptive geometry** — *sistemas de representación* — taught in
    the first year of architecture, engineering and animation degrees.
  - In that discipline **correctness is objective**. A construction is right or wrong; an isometric
    axis is at 30° or it is not.
  - **And yet no published syllabus states a tolerance.** Eighteen sources were checked
    (`docs/PEDAGOGY.md`); not one gives a figure in degrees. The checking is handed to a person with
    a set square at the end of a stack of plates.
- **The line**: *"Atelier automates the objective verification the discipline already defines. It
  does not invent a new criterion."*

---

## Phase 2 — The live, uncut run (0:35 – 2:15) ⏺ **ONE TAKE**

Screen recording of the deployed app. Do not cut inside this phase.

### 2.1 Step one — choose (0:35 – 0:50)

- The studio opens on **Dibujo**, step one of three. The indicator is in the top bar.
- Show the calibration grid. Say what the labels under each thumbnail mean: **cónica /
  axonométrica / diédrico** — three of the four systems of representation, each measured against a
  different reference.
- Pick **`07_isometric_error_6deg.png`** — *"Isométrica (eje X colocado 6° mal)"*.

### 2.2 Step two — context (0:50 – 1:05)

- The page advances to **Contexto** with the measurement already on screen beside the questions.
- Point at the axis table while you talk:
  - **X: nominal 30,0° · measured 36,0° · systematic +6,0°**, and Y and Z at 0,0°.
- **This is the beat that sells the project.** Say it plainly:
  > *"The error was injected at exactly six degrees, and it comes back at exactly six degrees. There
  > is no estimator here — the axes of an isometric projection are 30, 90 and 150 by definition of
  > the system, so nothing is guessed."*
- Then the pedagogical half, which is the part a rubric cannot do:
  > *"A whole family off by the same amount is a set square placed wrong, not an unsteady hand. One
  > correction, before drawing — not edge by edge."*
- Type a short answer in the first textarea and press **Analizar mi dibujo**.

### 2.3 Step three — the critique (1:05 – 1:30)

- While Gemini answers, say what is being enforced: **Plane A carries only numbers OpenCV produced**,
  and a validator rejects any figure the model did not get from it. **Plane B is forbidden a number
  at all**, in either language.
- When it lands, read one Plane A finding aloud and point at the green
  **Sin alucinaciones: verificado ✓** badge with `gemini-3.5-flash` under it.
- **The honesty beat**: the badge is earned per critique. When the model is unreachable the same
  panel turns amber — *"Plantilla determinista — ningún modelo respondió"* — with the real
  `model_version` beneath. Say that it appears only when Gemini actually answered.

### 2.4 The refusal (1:30 – 1:45)

- Click **Analizar otro dibujo**, then upload the page of handwriting.
- Gemini looks at it **before anything is measured** and declines in its own words.
- Say why it matters: without the gate the page goes through RANSAC, finds a vanishing point among
  whatever edges exist, and spends real tokens telling a student their line weight is confident.
  **Measuring the wrong thing carefully is worse than not measuring it.**

### 2.5 Three systems, three references (1:45 – 2:05)

Back to step one. Pick two more samples in quick succession and let the panel change under you:

| Sample | What appears | What to say |
|---|---|---|
| `03_1point_error_9deg.png` | Conic overlay, vanishing point, per-line colours | *"Conic. The reference is **inferred** — RANSAC estimates the vanishing point from the student's own lines."* |
| `10_diedrico_error_18px.png` | Ground line, correspondence marks, **systematic offset 18 px** | *"Orthographic. Two flat views. The reference is **read off the page** — the ground line is a line the student drew."* |

- Then the sentence that ties it together, and it is an unusual one to say out loud:
  > *"The three differ in where the reference comes from, and the first one is the weakest. A
  > consistently wrong perspective drawing yields a vanishing point that agrees with it. Axonometry
  > has no such problem, because nothing is estimated."*
- For the orthographic plate, make the distinction explicit: **a displaced plan is one placement
  mistake that every vertex inherits**, reported once — not four broken corners.

### 2.6 History (2:05 – 2:15)

- On step one, the panel on the right is the reader's own history: date, system, the one figure worth
  showing, and the headline of the critique written at the time.
- Point out that a figure that was not measurable renders as a dash, **never as zero**.
- Switch **Nivel: Básico → Avanzado**. Say what the profile is: a **difficulty level**, not a person.
  It sets the register of the rubric and the tone of the critique, and nothing interpolates a name.

**End the uncut take here.**

---

## Phase 3 — Google Cloud, live [MANDATORY] (2:15 – 3:00)

Switch to `console.cloud.google.com`. This may be cut.

1. **Cloud Run** — `atelier-agent` (Python/FastAPI) and `atelier-web` (.NET 10), active revisions.
   Open the agent's **Logs** and show the requests your own take just made:
   `/api/analyze`, `/api/analyze/axonometric`, `/api/analyze/dihedral`, `/api/router/gate`,
   `/api/critique`.
2. **Cloud Storage + Eventarc** — `gs://atelier-hack-inbox/` and the
   `google.cloud.storage.object.v1.finalized` trigger.
3. **Firestore** — the tree `students/level-basic/exercises/{id}/feedback/`. Say the word:
   **append-only**. Nothing is ever updated in place.
4. **Vertex AI** — the Gemini 3.5 Flash endpoint in **europe-west3**. Worth one sentence: the model
   is not in the Cloud Run region, and pointing Vertex at the service's region made every critique
   404 into a silent fallback for days. The two are configured separately now.

---

## Phase 4 — Wrap (3:00 – 3:30)

- **Visual**: the GitHub repository.
- **Say**: **98 automated tests** (90 Python + 8 .NET), Apache 2.0, architecture and pedagogy
  documentation, live demo URL.
- Worth one line, because it is the project's whole character: the golden tests assert an injected
  6° error returns as 6° **to within 0.05°**, and the perspective suite cannot hold a bound that
  tight — the difference is stated rather than hidden.
- **Closing**: *"Atelier measures what the discipline already defines as correct, in under a second,
  the same way every time."*

---

## Things not to do

- **Do not re-shoot to force the description-versus-drawing mismatch.** Typing "the corner of a
  building" over a one-point sketch *sometimes* makes Gemma disagree with the measurement, and
  Atelier then says so and changes nothing. It is a lovely beat when it fires. Choosing a take
  because it went your way is the thing this project is against.
- **Do not promise a smooth improvement curve.** An earlier version of this runbook told you to show
  4.8° falling to 1.8°; that was a hardcoded fallback in the web client, not a student's history, and
  it has been deleted. Read the progression figures off the page as they are.
- **Do not cut inside Phase 2.** The rules ask for an uncut execution and that is the phase that
  provides it.
- **Do not narrate a number before it appears.** Let the panel render, then read it.

---

## ⚠️ Submission

1. **YouTube**
   - Title: `Atelier — AI Studio Master for Remote Art Students | All Things Agentic Hackathon`
   - Privacy: **Public**. Not private, not unlisted.
   - Upload a **fresh** video; do not replace an existing link.
2. **Timing**
   - Submit **29 or 30 August 2026**.
   - Hard deadline: **31 August 2026, 17:00 PT** = **1 September, 02:00 CEST**. The European 31st
     evening is already too late. Leave 24 hours.
3. **Before clicking Submit on Devpost**
   - [ ] Public GitHub repo (`https://github.com/hvaler/atelier`)
   - [ ] Hosted demo URL, opened once in a private window to confirm it is warm
   - [ ] Public YouTube link
   - [ ] Architecture diagram attached
   - [ ] Screenshots attached (`docs/img/`)
   - [ ] Track: *The Collaborative Partner*
   - [ ] Bonus claims listed with direct links
