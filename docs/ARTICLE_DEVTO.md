# The Geometry Measures, the AI Teaches: Building an Art Studio Tutor with the Google GenAI SDK, Vertex AI & OpenCV

> *This project was created for the Devpost All Things Agentic Hackathon.*

---

## 1. The origin: a discipline that defines correctness and never measures it

**Descriptive geometry** — *sistemas de representación*, the tradition Gaspard Monge formalised in
the 1790s — is a first-year subject in architecture, engineering and animation degrees. It has a
property most drawing subjects do not: **correctness is objective.**

An isometric axis is at 30° or it is not. A point's plan lies on the reference line dropped from its
elevation or it does not. A rabatment recovers the true length or it does not. Nothing here depends
on an examiner's taste, and the check is itself a construction rather than an opinion. The
assessment rules reflect that: the Universidad de Granada requires a **minimum of 5/10 in each block
independently**, and the Universidad de Salamanca states plainly that *"es necesario superar cada
bloque de forma independiente"*. You cannot compensate a failed system with a strong one, because
these are not matters of degree.

So I went and read the syllabi — eighteen published sources across Spanish public engineering and
architecture schools, international animation programmes, and open courseware. The finding is in
[`docs/PEDAGOGY.md`](PEDAGOGY.md), and it is this:

> **Not one of them states a numerical tolerance.**

Nowhere does a figure in degrees or millimetres appear as a pass mark. The closest any source comes
is a Canadian animation degree that grades *"composition, perspective and colour, with speed,
**accuracy** and dexterity"* — accuracy as a graded outcome of a four-year honours degree, with the
curriculum never saying how accurate.

The discipline defines correctness exactly, and then hands the checking to a person with a set
square at the end of a stack of plates. Meanwhile a general-purpose multimodal model asked to
critique a drawing will happily invent the number — *"your angle is off by about 15 degrees"* — with
no spatial ground truth behind it at all.

Atelier sits in that gap, and the scope is narrow on purpose:

> **It automates the objective verification the discipline already defines. It does not invent a new
> criterion.**

The invariant the whole system is built on:

> **"The geometry measures, the AI teaches, the student grows." (ADR-001)**

---

## 2. Architecture: three systems, three kinds of reference

```
                              ATELIER ARCHITECTURE

 ┌────────────────────────┐      ┌──────────────────────────────────────────────┐
 │  Atelier.Web           │      │  Vision gate — Gemini 3.5 Flash (Vertex AI)  │
 │  Blazor Server/.NET 10 │ ───> │  Is this an exercise at all?                 │
 │  - 3-step flow         │      │  Conic / axonometric / orthographic?         │
 │  - per-system viewers  │      └──────────────────────────────────────────────┘
 │  - append-only history │                            │
 └────────────────────────┘        ┌───────────────────┼───────────────────┐
             ▲                     ▼                   ▼                   ▼
             │            ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
             │            │ geometry.py    │  │ axonometry.py  │  │ dihedral.py    │
             │            │ CONIC          │  │ AXONOMETRIC    │  │ ORTHOGRAPHIC   │
             │            │ RANSAC VPs     │  │ fixed axes     │  │ ground line +  │
             │            │ k = 1, 2       │  │ 30 / 90 / 150  │  │ correspondence │
             │            └────────────────┘  └────────────────┘  └────────────────┘
             │                     └───────────────────┼───────────────────┘
             │                                         ▼
 ┌────────────────────────┐      ┌──────────────────────────┐   ┌────────────────────┐
 │  Collaborative loop    │ <─── │  Anti-hallucination      │ <─│  Gemini 3.5 Flash  │
 │  ASK / GUIDE           │      │  validator               │   │  Two-plane critique│
 │  CAPTURE / ADAPT       │      │  measured_values()       │   │  Level-aware rubric│
 └────────────────────────┘      └──────────────────────────┘   └────────────────────┘
```

Atelier measures **three of the four systems of representation**. The fourth, *planos acotados*,
needs the numeric annotations read off the page — OCR rather than line geometry — and is documented
as not implemented.

What makes them worth having together is that they are not one tool three times. **They differ in
where the reference comes from**, and that determines how far each measurement can be trusted:

| System | Where the reference comes from | Trust |
|---|---|---|
| **Conic** | **Inferred.** RANSAC estimates a vanishing point from the student's own lines | Weakest — a consistently wrong drawing yields a vanishing point that agrees with it, and the reported error shrinks |
| **Orthographic** | **Read off the page.** The ground line is a line the student drew | Middle — nothing is guessed, but a crooked ground line skews everything, so its tilt is reported as a figure in its own right |
| **Axonometric** | **Given.** The axes are constants of the projection system | Strongest — nothing is estimated at all |

That ranking is stated in the documentation rather than hidden, and it is measurable: in the golden
case an error injected at exactly 6° comes back at **6.00°**, asserted to within 0.05°. The
perspective suite cannot hold a bound that tight, and says so.

### The two-plane critique

Every critique is split into two planes that may not mix:

1. **Plane A — measured findings.** Every figure comes from OpenCV, verbatim.
2. **Plane B — studio observations.** Line weight, spatial legibility, cleanliness. **Forbidden a
   number at all.**

An **anti-hallucination validator** intercepts the model's answer. It asks the analysis what it
measured — `measured_values()` — rather than reading named fields, which is what lets a new
projection system be added without silently arriving unguarded. Any figure the model did not get
from that set is rejected and regenerated with corrective feedback.

The prose gate is bilingual for a reason that is easy to miss: a detector that only recognises
`degrees` stops being a gate the moment the interface is translated. It recognises `grados` too.

### Two models, two jobs

- **Gemini 3.5 Flash** (Vertex AI, `europe-west3`) looks at the photograph twice: once as a gate —
  *is this an exercise, and which system?* — and once to write the critique.
- **Gemma 4** (`gemma-4-26b-a4b-it`, via the Gemini API — it is not published on Vertex AI) reads
  the student's own description and infers which perspective they meant.

When the two disagree, **the words do not win.** An early version re-measured on the router's
say-so, and a one-point box described as "the corner of a building" came back as two-point with 29.9°
of average error. The measurement is evidence; the description is a claim. Atelier now reports the
disagreement and changes nothing.

---

## 3. The four verbs of "The Collaborative Partner"

1. **ASK** — before analysing: *"What were you practising today? Which part felt hardest?"* The
   answers set the register of the critique. They never change the measurement.
2. **GUIDE** — the next exercise comes from a ladder documented in published curricula, not invented
   to fill a JSON field. Rungs the engine cannot yet assess are recorded as gaps and deliberately
   not prescribed.
3. **CAPTURE** — explicit feedback (`helpful: bool` + note) persisted as an immutable event in
   Firestore (ADR-005).
4. **ADAPT** — the profile is derived from the event stream, never edited. Note that the profile is a
   **difficulty level**, not a person: it sets the rubric's register and nothing else.

---

## 4. Asynchronous pipeline and Cloud Run deployment

- **Async-first ingestion** — a photograph dropped into a private Cloud Storage inbox
  (`atelier-hack-inbox/{studentId}/`) fires an Eventarc CloudEvent at the Cloud Run agent, which
  downloads the object, measures it and stores the result with nobody touching the app.
- **Weekly digest** — Cloud Scheduler aggregates the week and prescribes a three-day practice plan.
- **The measurement API** — `POST /api/analyze`, `/api/analyze/axonometric`, `/api/analyze/dihedral`,
  plus `/api/router/gate` and `/api/router/classify` for the two routing decisions, and
  `GET /api/students/{id}/exercises` for the student's own history.
- **Production hardening** — Cloud Run with .NET 10 (`KnownIPNetworks.Clear()` for proxy header
  termination) and Python FastAPI.

---

## 5. What we learned

Three lessons, and the useful ones are all about honesty rather than about models.

**The mean of an empty set is not zero.** Twice — in the orthographic engine and again in the
progress profile — an average computed over nothing was reported as `0.00`, which reads as *perfect*.
A plate whose two views did not correspond at all reported a correspondence error of zero. **A worse
drawing produced a better number.** Both aggregates are nullable now, and render as a dash. If your
system can produce a figure that looks like success when nothing was measured, that is not a
formatting detail — it is the failure mode.

**A single average hides the mistake that matters.** In axonometry, a per-line error and a
*systematic* error are different faults with different corrections: an unsteady hand versus a set
square placed at the wrong angle. Averaged together they are indistinguishable. Reporting them apart
is what lets the critique say *"your hand is excellent, you just need to set the axis before you
start"* — which a published rubric cannot say, because saying it requires measuring each family's
mean direction separately.

**Silent fallbacks make a broken system look healthy.** The critique path once caught every exception
and returned a hand-written template stamped `validated=true` with the real model's name on it.
Deleting Vertex AI from the project would have changed nothing observable. Now provenance is stamped
by the server, never by the model, and the green badge is gated on it — when no model answered, the
panel turns amber and says so.

The general shape: for technical disciplines — drawing, engineering, surgery — **use computer vision
for ground truth and a language model for teaching**, and make the boundary between them something
the code enforces rather than something the prompt requests.

---

*Built with the Google GenAI SDK (`google-genai`), Vertex AI (Gemini 3.5 Flash), Gemma 4, Google
Cloud Run, Cloud Storage, Eventarc, Firestore, Cloud Scheduler, OpenCV and .NET 10. Apache 2.0,
98 automated tests (90 Python + 8 .NET).*
