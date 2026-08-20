# Components: what each one is, and why it and not the alternative

The topology is in [`ARCHITECTURE.md`](ARCHITECTURE.md) and the diagram is
[`img/architecture.png`](img/architecture.png). This document answers a different question, one a
diagram cannot: **why is this component here rather than the obvious other one**, and **which
hackathon requirement does it satisfy**.

Requirements are quoted verbatim from the Official Rules and from the organisers' own self-check
post, and marked **[REQ]**.

---

## The three mandatory requirements, and the single line that satisfies each

| Requirement, verbatim | Satisfied by | Where to see it |
|---|---|---|
| **[REQ]** *"Gemini 3.5 or newer accessed through Gemini API or Vertex AI"* | `gemini-3.5-flash` on **Vertex AI** | `src/config.py`, and `/api/health` returns the model id in production |
| **[REQ]** *"At least one Google Agent Framework: Google ADK, GenAI SDK, Antigravity SDK or GenKit"* | the **Google GenAI SDK** (`google-genai`) — every model call in the project | `requirements.txt`; every call site is `genai.Client(...)` |
| **[REQ]** *"At least one Google Cloud infrastructure service"*, from the enumerated list *Cloud Run · Cloud SQL · Firestore · GKE · Pub/Sub* | **Cloud Run** (both services) and **Firestore** (all state) | `infra/deploy.sh`, `src/tools/firestore_repo.py` |

Everything below is either one of those three, or something that exists to make one of them
defensible.

---

## The models

### Gemini 3.5 Flash — on Vertex AI, in europe-west3

**What it does.** Two jobs, and they are deliberately separate calls. First a **vision gate**: it
looks at the photograph and answers *is this an exercise at all, and which of the three systems of
representation is it?* That verdict chooses which OpenCV engine runs. Then, after the measurement,
it **writes the critique** — with the measured numbers handed to it, never asked for.

**Why Vertex AI rather than the Gemini API.** Both are accepted by the rules. Vertex was chosen
because the rest of the state and the compute are already inside one Google Cloud project with one
IAM boundary: the service account that runs the agent is the identity that calls the model, so
there is no long-lived key to hold for the main path. The Gemini API needs an API key, and a key is
a thing that has to live somewhere.

**Why europe-west3, when the services run in europe-west1.** This looks like an error and is the
fix for one. The region was originally a single variable set from the Cloud Run region — and
`gemini-3.5-flash` **is not published in europe-west1**. Every call in production returned
`404 NOT_FOUND`, the exception was swallowed, and the critique fell back to a hand-written
deterministic template that stamped itself `validated`. The mandatory Gemini requirement was met by
the code and broken by the deployment, invisibly, for days. Two things came out of that: the region
is now its own setting, and **provenance is stamped by the server rather than claimed by the
model** — the green *Validated* badge is gated on `source == "vertex"`, so deleting Vertex from the
project would now change what the screen says.

europe-west3 rather than `global`: both serve the model, and west3 keeps a student's drawings inside
the EU and co-located with the Firestore database (`eur3`).

### Gemma 4 — on the Gemini API

**What it does.** Reads the student's own words — the free text from the ASK step — and infers which
case of conic projection they meant. A beginner who writes *"the corner of a building"* is measured
as two-point **because they said so**, not as one-point because of a field in their profile.

**Why a second model at all.** The routing step it replaced returned `k` derived from
`student.level`, a value the caller had just passed in. A router that hands back its own input is
not a router. This one reads something the caller does not know.

**Why on the Gemini API and not Vertex AI.** Because Gemma is not reachable on Vertex here:
`gemma-3-27b-it`, `-12b-it`, `-4b-it` and the Gemma 4 line all return `404 NOT_FOUND` there without
a deployed, billed Model Garden endpoint. It **is** served by the Gemini API, which is where this
reaches it, with a key from Secret Manager.

**Why words and not the picture.** Gemma's vision path was measured and rejected: with an image
attached it spends the whole output budget reasoning and returns empty text at 80 and 300 output
tokens, and at 800 it does not return for over six minutes. `thinking_budget` is not supported on
Gemma, so the reasoning cannot be capped. A pre-router that takes minutes has defeated its own
purpose. **Gemma reads words; Gemini looks at pictures.**

**[REQ]** This is also the additional-model bonus: *"+0.2 for each additional Google AI model
(Gemma, Veo, Lyria)"*. It is claimed on a real runtime path, not on an import.

### When the two disagree

The measurement wins, and **nothing is changed**. An early version re-measured on the router's
say-so, and a one-point box described as *"the corner of a building"* came back as two-point with
29.9° of average error. The measurement is evidence; the description is a claim. Atelier now reports
the disagreement and leaves the numbers alone.

---

## The framework

### Google GenAI SDK (`google-genai`)

**[REQ]** This is the Agent Framework the rules require. Every model call in the project goes
through it — `genai.Client(...)` for both Vertex AI and the Gemini API, with the same call shape
either way.

**Why not ADK.** ADK is the more obvious answer to *"Google Agent Framework"*, and this project
claimed it for a while in an ADR, in the README and in the architecture diagram. **`google-adk` was
never installed.** The claim was corrected rather than the code: the amendment is recorded in
`adr/ADR-002-two-services.md`, and the rules name four acceptable frameworks rather than one.

The honest reason the GenAI SDK fits better here: the orchestration this project needs is a fixed
pipeline — gate, then measure, then critique, then validate — with a hard rule that the model is
never in the measuring path. ADK's strength is letting a model decide what to call next. Handing
that decision to a model is precisely what this project is built not to do.

---

## The measurement, which is not a model

### OpenCV — three engines, three kinds of reference

**Why deterministic computer vision at all**, when a multimodal model will happily describe a
drawing. Because it will happily describe it *wrongly*: asked to critique a drawing, a
general-purpose model invents the number — *"your angle is off by about 15 degrees"* — with no
spatial ground truth behind it. The whole project is the boundary between what is measured and what
is said, and that boundary has to be enforced by code rather than requested in a prompt.

The three engines are not one tool three times. They differ in **where the reference comes from**,
and that sets a ceiling on how far each result can be trusted:

| Engine | Reference | Trust |
|---|---|---|
| `geometry.py` — conic | **Inferred.** RANSAC estimates a vanishing point from the student's own lines | Weakest. A consistently drifted drawing yields a vanishing point that agrees with it, and the reported error *shrinks*. A plate in the calibration set with 6° of injected drift scores better than the perfect one |
| `dihedral.py` — orthographic | **Read off the page.** The ground line is a line the student drew | Middle. Nothing is guessed, but a crooked ground line skews everything — so its tilt is reported as a figure in its own right |
| `axonometry.py` — axonometric | **Given.** The axes are constants of the projection system | Strongest. Nothing is estimated. An error injected at 6.00° comes back at 6.00°, asserted to within 0.05° |

That ranking is stated in the documentation rather than buried in it, because a measurement whose
weakness is undocumented is worse than a weaker measurement whose limits are known.

### `validator.py` — the anti-hallucination gate

**What it does.** Intercepts the model's answer and asks the analysis what it actually measured —
`measured_values()` — rather than reading named fields. Any figure in Plane A that is not in that
set is rejected and the critique is regenerated with corrective feedback. Plane B is forbidden a
number at all.

**Why a component and not a prompt instruction.** Because a prompt is a request and this is a rule.
And because asking the analysis what it measured, rather than checking a list of field names, is
what let a third projection system be added without arriving unguarded.

**Why it is bilingual.** A detector that only recognises `degrees` stops being a detector the moment
the interface is translated. It recognises `grados` too.

---

## The infrastructure

### Cloud Run — two services **[REQ]**

**[REQ]** On the enumerated list. Both services run on it, in europe-west1.

**Why two and not one.** `Atelier.Web` is Blazor Server on .NET 10; `atelier-agent` is FastAPI on
Python 3.12 with OpenCV. One container would mean one runtime hosting the other, and the boundary
between them is exactly where the interesting rule lives: the web client can only ever see what the
agent's HTTP response contains, so it cannot accidentally read a model's raw output. They scale
independently, and either can be redeployed mid-session without losing anything, because neither
holds state.

**Why scale-to-zero, given cold starts cost 5–10 seconds.** The judging window is five weeks long
and the demo is watched once. Paying for an idle container for a month to save eight seconds on a
first visit is the wrong trade.

**How a deploy is promoted.** `infra/deploy.sh` deploys a **candidate** revision with 0% traffic,
runs a smoke test against it, and only then promotes. A deployment that fails its smoke test never
serves anybody.

### Firestore — all of the state **[REQ]**

**[REQ]** On the enumerated list. This is the answer to *"where is state stored"*, which the
organisers' checklist asks the architecture diagram to make explicit.

**Why NoSQL document storage rather than Cloud SQL**, which is also on the list. The data is a
per-student event stream — exercises, and feedback events under them — read almost always by
student and almost never across students. There are no joins to do. Cloud SQL would also mean a
provisioned instance billed by the hour, which contradicts the scale-to-zero decision above.

**Why append-only, and what that buys.** Nothing is ever updated in place. The profile — the
student's level, the adapted tone, the recurring issues — is **derived** from the event stream, not
edited. So the history is the record and the profile is a view of it, and a wrong adaptation is a
bug in a function rather than a corrupted row.

**Why aggregates are nullable.** Because the mean of an empty set is not zero. Twice in this
project an average computed over nothing was reported as `0.00`, which reads as *perfect*: a plate
whose two views did not correspond at all reported a correspondence error of zero, and a **worse
drawing produced a better number**. Every aggregate that can be computed over nothing is
`float | None` and renders as a dash.

### Cloud Storage + Eventarc — the asynchronous path

**What it does.** A photograph dropped into `gs://atelier-hack-inbox/{studentId}/` fires an Eventarc
`object.v1.finalized` event at the agent, which downloads it, measures it, critiques it and files it
with nobody touching the app.

**[REQ]** The Collaborative Partner track asks for an agent that *"operates beyond standard chat
loops"*. This is that, literally: no session, no request, no user waiting.

**Why not Pub/Sub**, which is on the enumerated list and Eventarc is not. Because the trigger *is* a
storage event, and Eventarc delivers it as a typed CloudEvent to an HTTP endpoint with no topic and
no subscription to maintain. Pub/Sub would be a second thing to keep correct in exchange for
nothing. Cloud Run and Firestore already satisfy the enumerated-service requirement, so there is
nothing to gain by picking the listed service over the right one.

### Cloud Scheduler — the weekly digest

**What it does.** `weekly-digest-job`, Mondays at 09:00 UTC, calls `/api/digest/weekly`: aggregates
the week and prescribes a three-day practice plan.

**Why it is worth naming as a component.** Because it is the part that had never run. The job was
created on a Tuesday, so its first Monday had not arrived — and when it did arrive it would have
returned **500**, because the digest read a conic-only field off every exercise and that field is
`None` on axonometric and orthographic records. A scheduled job that fails does so into a log nobody
reads. It is fixed, it has two regression tests, and the fix is the same one as above: filter to
what was actually measured, and let the aggregate be `None` rather than `0.0`.

### Secret Manager

The Gemini API key, mounted into the agent at deploy time as `GEMINI_API_KEY=gemini-api-key:latest`.
Never in an image, never in a `.env` committed anywhere, never printed. The web service is given
**no** secret at all: it only speaks HTTP to the agent.

### Artifact Registry

Both container images. Relevant because of the promote step: the candidate revision that gets smoke
tested and the revision that serves traffic are the same digest, not two builds of the same tag.

---

## The frontend

### Blazor Server on .NET 10

**Why Blazor Server rather than WebAssembly.** The interesting work is server-side — three OpenCV
engines and two models — so there is nothing to gain from shipping a runtime to the browser, and a
server-rendered circuit keeps the agent's URL and every response server-side.

**One production wrinkle worth recording**, because it is the kind of thing that looks like a
framework bug: Cloud Run terminates TLS at its proxy, so the app needs
`ForwardedHeaders` with `KnownIPNetworks.Clear()` or every request appears to arrive over HTTP from
a load-balancer address.

**Why the culture travels with the analysis request.** So Gemini *writes* the critique in the
student's language rather than having it translated afterwards. The number formatting follows too —
`0,8°` rather than `0.8°` — because a measurement should read the way the person reads.

**Three separate viewers, never two at once.** `OverlayViewer`, `AxonometricViewer` and
`DihedralViewer` render different measurements of different things, and the page holds exactly one
analysis at a time. A screen showing one while holding another is how a stale reading gets read as
fresh.

---

## Considered and rejected

| Option | Why not |
|---|---|
| **Google ADK** as the agent framework | Never installed, despite being claimed. And the orchestration here is a fixed pipeline whose whole point is that a model does not choose the next step |
| **Gemma for the vision gate** | Measured: empty output at 80 and 300 tokens, no return at all in six minutes at 800. `thinking_budget` unsupported |
| **Gemini for the intent router** | It would work. Gemma is cheaper for a words-only structured answer, and using it claims the additional-model bonus on a path that earns it |
| **Cloud SQL** for state | No joins to do, and an hourly-billed instance against a project designed to scale to zero |
| **Pub/Sub** instead of Eventarc | The trigger is a storage event; Eventarc delivers it typed with nothing to maintain. The enumerated-service requirement is already met twice |
| **One Cloud Run service** | Two runtimes in one container, and the loss of the HTTP boundary that keeps raw model output away from the browser |
| **`min-instances=1`** to hide cold starts | Five weeks of idle billing to save eight seconds on a first visit |
| **Asking the model for the measurements** | The entire premise. It answers confidently and it has no ground truth |

---

## Requirement → evidence

| # | Requirement | Evidence a judge can check without running anything |
|---|---|---|
| 1 | Gemini 3.5+ via Gemini API or Vertex AI | `src/config.py`; the compliance table at the top of the README; `curl /api/health` |
| 2 | ≥1 Google Agent Framework | `requirements.txt` names `google-genai`; every call site; `adr/ADR-002` records the ADK correction |
| 3 | ≥1 Google Cloud infrastructure service | `infra/deploy.sh` (Cloud Run), `src/tools/firestore_repo.py` (Firestore) |
| 4 | Architecture diagram showing Gemini ↔ backend ↔ frontend, **where state is stored**, **which Google Cloud services** | [`img/architecture.png`](img/architecture.png), generated by `make_architecture_diagram.py` |
| 5 | Agent operates beyond standard chat loops | `src/tools/async_ingest.py` (GCS + Eventarc) and `src/tools/digest.py` (Cloud Scheduler) |
| 6 | Additional Google AI model | Gemma 4 in `src/tools/pre_router.py`, on the Gemini API |
| 7 | Reproducible spin-up | README §Quickstart |
| 8 | No pre-existing code; AI assistants disclosed | README §Tooling disclosure; first commit 18 August 2026 |
