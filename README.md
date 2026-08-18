# 🎨 Atelier — An AI Studio Master for Remote Art Students

> **The geometry measures, the AI teaches, the student grows.**

My daughter studies Animation online. She submits a perspective drawing and waits weeks for
feedback — practicing blind in between, repeating the same construction mistakes with nobody
to catch them. So I built her the studio master who reviews her sketchbook every day.

Atelier is a collaborative AI agent that analyzes drawing exercises with **deterministic
computer vision** (vanishing point estimation, convergence error in degrees), teaches through
**Gemini-powered critique grounded in those measurements**, remembers each student's
progression, and adapts to how they learn — asking before judging, and changing its approach
when told a critique didn't help.

Built for the [All Things Agentic Hackathon](https://allthingsagentichackathon.devpost.com/)
(Google Cloud) — **The Collaborative Partner** category.

![Gemini](https://img.shields.io/badge/AI-Gemini%203.5%20via%20Vertex-4285F4)
![ADK](https://img.shields.io/badge/agents-Google%20ADK-34A853)
![.NET 10](https://img.shields.io/badge/UI-Blazor%20%2F%20.NET%2010-512BD4)
![License](https://img.shields.io/badge/license-Apache--2.0-green)

## Why a hybrid, and not "just ask Gemini"?

A vision LLM asked "how's my perspective?" produces plausible, unmeasurable prose. Atelier
splits the job:

- **OpenCV measures.** Line detection, vanishing-point clustering, horizon estimation,
  per-line convergence error *in degrees*, with an explicit confidence score. Deterministic,
  tested against drawings with deliberately constructed errors of known magnitude. When
  confidence is low, the tool says so — it never invents geometry.
- **Gemini teaches.** It receives the image *plus the measurements* and produces pedagogy in
  studio vocabulary: what's working, the one thing to focus on, the next exercise. A validator
  rejects any critique citing numbers that aren't in the measurement payload — the LLM cannot
  hallucinate a metric.
- **The student decides.** Every critique captures explicit feedback (helpful or not, plus
  notes). The agent's tone and focus derive from that event stream — append-only, never
  hand-edited.

## The Collaborative Partner loop

1. **Ask** — before critiquing: *"What were you practicing? Which part felt hardest?"*
2. **Guide** — the next exercise is derived from the student's recurring error pattern.
3. **Capture** — one-tap feedback per critique, persisted as immutable events.
4. **Adapt** — tone preference and focus area are computed from feedback history.

Plus the part that runs while everyone sleeps: drop a phone photo into the student's folder
and **Eventarc + Cloud Run process it in the background** — the critique is waiting next time
they open Atelier. Every week, **Cloud Scheduler** produces a digest: progress curve
(average convergence error over time), recurring issues, and an adapted practice plan.
Multiple student profiles from day one — I have more than one kid.

## Architecture

```
  phone photo ──► GCS inbox ──► Eventarc ──┐
                                           ▼
  Blazor UI (Atelier.Web, .NET 10) ◄──► atelier-agent (Python / Google ADK, Cloud Run)
        │ signed URLs                        │ tools:
        ▼                                    ├─ analyze_geometry (OpenCV, deterministic)
   GCS (private)                             ├─ critique (Gemini 3.5 Flash via Vertex AI)
                                             ├─ memory (Firestore, append-only events)
  Cloud Scheduler ──► weekly digest ─────────┘  └─ classify (Gemma, exercise routing)
```

Google Cloud: **Vertex AI (Gemini 3.5 Flash, Gemma) · Google ADK · Cloud Run · Firestore ·
GCS · Eventarc · Cloud Scheduler · Secret Manager · Workload Identity Federation** (no
long-lived keys anywhere in CI or runtime).

## Quickstart

> Verified on a clean machine before submission.

```bash
# Prerequisites: gcloud CLI, .NET 10 SDK, Python 3.12+, a GCP project with billing

git clone https://github.com/hvaler/atelier.git && cd atelier
./infra/setup.sh <gcp-project-id>     # APIs, service accounts, Firestore, buckets, Eventarc
./infra/deploy.sh                      # agent + web to Cloud Run
./demo/seed.sh                         # sample student profiles + demo drawings
```

Open the printed URL, pick a student, upload a drawing — or drop one into the inbox bucket
and watch the background pipeline do its thing.

## Privacy

This is a family tool built with a real student. Images live in a private bucket behind
signed URLs; profiles use first names only; every drawing in the demo dataset is used with
explicit permission (or was drawn — badly, on purpose — by the author).

## Development notes

Developed with AI assistance (Claude Code) under an internal engineering standard —
explicitly permitted by the hackathon rules ("Participants may use standard development
tools, including … AI coding assistants"). All runtime AI is Google: Gemini and Gemma on
Vertex AI, orchestrated with Google ADK.

## License

[Apache-2.0](LICENSE)
