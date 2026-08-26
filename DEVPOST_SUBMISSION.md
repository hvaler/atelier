# Devpost Official Submission Form — Atelier

> **Target Hackathon**: Google Devpost All Things Agentic Hackathon  
> **Chosen Category Track**: **The Collaborative Partner**  
> **Submission Window**: August 29-30, 2026 (Hard Deadline: August 31, 2026 at 17:00 PT / 02:00 CEST Sep 1)

---

## 📌 Form Fields (Copy & Paste Ready)

### 1. Project Title
```text
Atelier — AI Studio Master for Remote Art Students
```

### 2. Elevator Pitch / Tagline (1-2 sentences)
```text
An isometric axis is at 30° or it is not: no published rubric says how close is close enough. OpenCV measures three systems of representation; Gemini teaches, and may not invent a single figure.
```

### 3. Built With (Tags for Devpost)
```text
gemini-3.5-flash, google-genai, google-cloud-vertex-ai, google-cloud-run, google-cloud-firestore, google-cloud-storage, eventarc, cloud-scheduler, opencv, python, fastapi, dotnet-10, blazor-server, csharp, docker
```

### 4. Category Track Selection
- [x] **The Collaborative Partner**
- [ ] The Explorer
- [ ] The Specialist

---

## 📖 Project Story (Full Markdown for Devpost Description)

```markdown
## Inspiration

My daughter studies Animation online. She submits a perspective drawing and waits weeks for instructor feedback — practicing blind in between, repeating the same construction mistakes with nobody there to catch them. The cost isn't the grade; it's that practice without correction consolidates the error.

So I built her the studio master who reviews her sketchbook every day. Then it turned out to work just as well for our youngest tester (age 9, drawings used with permission) drawing her first one-point boxes: the same agent, the same geometry, a different voice.

## What it does

**The geometry measures, the AI teaches, the student grows.**

A student uploads a phone photo of a perspective exercise — or simply drops it into a private folder — and gets back, in minutes:

- Their drawing with the **real geometry overlaid**: RANSAC-estimated vanishing points, horizon line ($LH$), and every line color-coded by its convergence error in degrees (green $<2.5^\circ$, yellow $2.5^\circ-6.0^\circ$, red $>6.0^\circ$).
- A **studio-master critique** written over those measurements, calibrated against real instructor rubrics from formal perspective-drawing coursework — and **level-aware**: the 9-year-old hears about *"lines meeting at the little dot on the horizon"*; the animation student hears about convergence, $F_1/F_2$ focal alignment, and dimensional fidelity.
- The **next exercise**, derived from her recurring error pattern.

The agent runs the four Collaborative Partner verbs: it **asks** before judging (*"What were you practicing? Which part felt hardest?"*), **guides** the next step, **captures** explicit feedback on every critique (`helpful: bool` + note), and **adapts** its tone and focus from that feedback history. Weekly, Cloud Scheduler produces a progress digest — the tutor works while everyone sleeps.

## How we built it

Two services with a clean boundary:
- `atelier-agent` (Python 3.12, **Google GenAI SDK**, FastAPI on **Cloud Run**) owns the tools: `analyze_geometry` (deterministic OpenCV — Canny, probabilistic Hough, RANSAC vanishing-point estimation, per-line angular error), `critique` (**Gemini 3.5 Flash on Vertex AI**, two-plane structured output), a **Gemini pre-router** classifying incoming exercises, and memory over **Cloud Firestore** as append-only events from which each student's profile is *derived*, never edited.
- `Atelier.Web` (Blazor Server, .NET 10) is the UI featuring an interactive multimodal overlay viewer and native SVG progress tracking.

The architectural spine is an **anti-hallucination gate**: the critique may only cite numbers present in the geometry payload — an in-code validator rejects and retries anything else. What's measured is measured; what's judged is judged; the agent never confuses the two.

Async-first by design: a private **GCS** inbox per student (`gs://atelier-hack-inbox/{studentId}/`), **Eventarc** firing the pipeline in the background, **Cloud Scheduler** for digests. Everything scales to zero.

## Challenges we ran into

1. **RANSAC Calibration & Angle Normalization**: Real student drawings have natural pencil stroke wobble and unoriented lines $\theta \in [-\pi, \pi]$. Standard Cartesian angle formulas produced false $180^\circ$ inversion penalties. We resolved this by formulating acute convergence angles modulo $\pi$ ($[0, 90^\circ]$) with adaptive Hough thresholding ($50/150$).
2. **Deterministic Anti-Hallucination Gate (ADR-001)**: Early prompt iterations allowed Gemini to occasionally invent numbers (e.g. citing $7.5^\circ$ when OpenCV computed $4.2^\circ$). We built a strict programmatic validator in Python that parses all numeric claims from the structured JSON and validates them against the OpenCV measurement payload. If an unverified number appears, the gate rejects the critique and triggers an automated retry with corrective feedback (`"Reject: number 7.5 not found in geometry payload"`).
3. **Cloud Run Reverse Proxy Headers (TEC-007)**: Blazor Server's WebSocket circuit failed to terminate HTTPS correctly behind Cloud Run's Envoy proxy. We resolved this by clearing `KnownIPNetworks` and `KnownProxies` in ASP.NET Core's `ForwardedHeadersOptions`.
4. **Eventarc Regional Co-Location**: Cloud Storage object-finalized triggers required exact regional co-location (`europe-west1`) between the GCS bucket, Eventarc trigger, and Cloud Run service, along with granting `roles/pubsub.publisher` to the Cloud Storage service agent.

## What we learned

1. **Decouple Measurement from Pedagogy (ADR-001)**: LLMs should not do raw trigonometry on raster images. Decoupling deterministic OpenCV vision for ground truth from Gemini for empathetic pedagogy means every figure in a critique is checked against the set the geometry actually produced, and the model is asked again when one is not — a gate with a retry rather than a guarantee, and the README says where it can still be fooled.
2. **Two-Plane Structured Schemas**: Separating critiques into Plane A (OpenCV Measured Findings) and Plane B (Qualitative Studio Observations) allowed students and instructors to immediately distinguish between provable mathematical facts and artistic advice (line weight, spatial depth).
3. **Append-Only Memory beats Mutable State (ADR-005)**: Rather than maintaining a mutable "skill rating", storing raw exercise and feedback events in Cloud Firestore allowed the agent to derive tone preferences and error reduction trends dynamically over time.
4. **The 4 Collaborative Verbs Transform UX**: Asking clarifying questions before analyzing work transformed the interaction from an intimidating automated grader into a supportive, human-centric studio partner.

## What's next for Atelier

Three-point and curvilinear perspective ($k=3$), more exercise families behind the intent router (anatomy proportion ratios, ellipse circularity, value histograms), live camera capture with real-time HUD overlays, and classroom cohort analytics for remote art schools.
```

---

## 📋 Submission Checklist & Links

| Field / Asset | Production Value / Link | Status |
| :--- | :--- | :--- |
| **Category Track** | **The Collaborative Partner** | ✅ Confirmed |
| **GitHub Repository** | `https://github.com/hvaler/atelier` | ✅ Public (Apache 2.0) |
| **Live Hosted Web UI** | `https://atelier-web-773993294789.europe-west1.run.app` | ✅ Live on Cloud Run |
| **Backend API (Swagger)** | `https://atelier-agent-773993294789.europe-west1.run.app/docs` | ✅ Live on Cloud Run |
| **Architecture** | `https://github.com/hvaler/atelier/blob/main/docs/ARCHITECTURE.md` | Mermaid system + sequence diagrams |
| **Bonus 1 (+0.2 pts)** | **Gemma 4 pre-router** (`/api/router/classify`) — `gemma-4-26b-a4b-it` on the Gemini API routes 1-point vs 2-point from the student's own description in ~1.6s. Gemma is *not* on Vertex AI (`gemma-*` returns 404 there), so this is the Gemini API backend, keyed from Secret Manager. | ✅ |
| **Bonus 2 (+0.2 pts)** | [Dev.to Article](https://dev.to/hugo_valer_79d0d94e00804b/the-geometry-measures-the-ai-teaches-building-an-art-studio-tutor-with-adk-vertex-ai-opencv-551m) | ✅ Published |
| **Bonus 3 (+0.2 pts)** | [X / Twitter Post](https://x.com/hugo_valer/status/2089965500713296311?s=20) | ✅ Published |
| **Video Demo (≤4 min)** | **<https://youtu.be/uIwx3I5ZpeI>** — 3:41, public, recorded against this deployment. Runbook: `docs/VIDEO_RECORDING_RUNBOOK.md` | ✅ Published |
