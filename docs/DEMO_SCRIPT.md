# Atelier — 3-Minute Timed Demo Video Script

> **Target duration**: 3:15–3:30
> **Structure**: four beats — the gap, the live run, the cloud, the close.
> Beat 2 is a **single uncut take**; everything else may be cut.
> Companion document: `VIDEO_RECORDING_RUNBOOK.md` (setup, warm-up, submission checklist).

---

## ⏱️ Beat 1 — The gap (0:00 – 0:35)

**[Visual: speaker on camera, holding a technical drawing on paper — an isometric cube or a two-view
plate reads better than a sketch. Then screen share.]**

> *"Descriptive geometry — sistemas de representación — is a first-year subject in architecture,
> engineering and animation degrees. It has a property most drawing subjects do not: **correctness
> is objective.** An isometric axis is at thirty degrees or it is not. A point's plan sits under its
> elevation or it does not. Nothing depends on an examiner's taste.*
>
> *So I read eighteen published syllabi and rubrics. **Not one of them states a tolerance.** Not a
> single figure in degrees, anywhere. The discipline defines correctness exactly, and then hands the
> checking to a person with a set square at the end of a stack of plates.*
>
> *That is the gap Atelier fills, and it is a narrow one on purpose:*
>
> ***Atelier automates the objective verification the discipline already defines. It does not invent
> a new criterion.***"

---

## ⏱️ Beat 2 — The live run (0:35 – 2:15) ⏺ **ONE TAKE, NO CUTS**

**[Visual: screen recording of the deployed app.]**

### 2.1 Choose (0:35 – 0:50)

> *"Three steps: drawing, context, critique. Step one is choosing.*
>
> *Every calibration sample carries the system it belongs to — **conic, axonometric, orthographic**.
> Three of the four systems of representation, and each is measured against a completely different
> reference. Let's take an isometric cube whose X axis was set six degrees wrong."*

**[Click `07_isometric_error_6deg.png`.]**

### 2.2 The measurement (0:50 – 1:10)

**[The page advances to Context with the axis table already on screen. Point at it.]**

> *"X: nominal thirty degrees. Measured thirty-six. Systematic deviation **plus six point zero.**
> Y and Z at zero.*
>
> *The error was injected at exactly six degrees and it comes back at exactly six. There is no
> estimator here — the axes of an isometric projection are thirty, ninety and one-fifty **by
> definition of the system**. Nothing is guessed.*
>
> *And look at what that separation buys. A whole family off by the same amount is **a set square
> placed wrong, not an unsteady hand.** One correction, made once before drawing — not edge by edge.
> A published rubric cannot make that distinction, because making it means measuring each family's
> mean direction separately."*

**[Type a short answer, press *Analizar mi dibujo*.]**

### 2.3 The critique, and what guards it (1:10 – 1:35)

> *"While Gemini answers: **Plane A carries only numbers OpenCV produced**, and a validator rejects
> any figure the model did not get from it. **Plane B is forbidden a number at all** — in either
> language; the gate recognises 'grados' as well as 'degrees'.*
>
> *There's the green badge — **anti-hallucination: validated** — with the model version under it.
> It is earned per critique. When the model is unreachable the same panel turns amber and says so:
> deterministic fallback, no model answered."*

### 2.4 The refusal (1:35 – 1:50)

**[*Analizar otro dibujo* → upload a page of handwriting.]**

> *"Gemini looks at the photograph **before anything is measured**, and declines — in its own words.*
>
> *Without this, the page goes through RANSAC, finds a vanishing point among whatever edges exist,
> and spends real tokens telling a student their line weight is confident. **Measuring the wrong
> thing carefully is worse than not measuring it.**"*

### 2.5 Three systems, three references (1:50 – 2:08)

**[Back to step one. Click `03_1point_error_9deg.png`, then `10_diedrico_error_18px.png`.]**

> *"Conic perspective: the reference is **inferred** — RANSAC estimates the vanishing point from the
> student's own lines.*
>
> *Orthographic — sistema diédrico. Two flat views, no solid at all. The reference is **read off the
> page**: the ground line is a line the student drew. This plan is displaced eighteen pixels, and
> that is reported as **one placement mistake that every vertex inherits** — not four broken corners.*
>
> *Here is the part worth saying out loud: the three differ in where the reference comes from, and
> **the first one is the weakest.** A consistently wrong perspective drawing produces a vanishing
> point that agrees with it. Axonometry has no such problem, because nothing is estimated. We say
> that in the documentation rather than hide it."*

### 2.6 History and level (2:08 – 2:15)

> *"Every exercise is here — system, figure, and the critique headline written at the time. A figure
> that was not measurable shows a dash, never a zero.*
>
> *And the profile is a **difficulty level**, not a person. It sets the register of the rubric and
> the tone of the critique. Nothing else."*

**[End the uncut take.]**

---

## ⏱️ Beat 3 — Google Cloud, live [MANDATORY] (2:15 – 2:55)

**[Visual: `console.cloud.google.com`. May be cut.]**

> *"Two Cloud Run services: the Python agent and the .NET 10 Blazor front end. These are the requests
> the run you just watched made — analyze, analyze/axonometric, analyze/dihedral, router/gate,
> critique.*
>
> *A private Cloud Storage inbox with an Eventarc trigger, so a photograph dropped in a folder is
> analysed with nobody touching the app. Firestore, **append-only** — nothing is ever updated in
> place. And Gemini 3.5 Flash on Vertex AI in europe-west3, which is deliberately not the Cloud Run
> region: the model is not published there, and pointing Vertex at the service's own region made
> every critique fail into a silent fallback for days before we caught it."*

---

## ⏱️ Beat 4 — Close (2:55 – 3:20)

**[Visual: the GitHub repository.]**

> *"Open source under Apache 2.0. **Ninety-eight automated tests** — ninety Python, eight .NET. The
> golden case asserts that a six-degree error comes back as six degrees **to within five hundredths
> of a degree**, and the perspective suite cannot hold a bound that tight. We state the difference
> instead of hiding it.*
>
> *Atelier measures what the discipline already defines as correct — in under a second, the same way
> every time."*

---

## Do not

- **Do not force the description-versus-drawing mismatch.** Typing "the corner of a building" over a
  one-point sketch *sometimes* makes the router disagree with the measurement, and Atelier then says
  so and changes nothing. Lovely when it fires. Re-shooting until it does is the thing this project
  is against.
- **Do not promise an improvement curve.** Read the progression figures off the page as they are.
- **Do not narrate a number before it renders.**
- **Do not cut inside Beat 2.**
