# 🎨 Atelier — AI Studio Master for Remote Art Students

> *"The geometry measures, the AI teaches, the student grows." (ADR-001)*

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![.NET](https://img.shields.io/badge/.NET-10.0-purple.svg)](https://dotnet.microsoft.com/)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org/)
[![Google Cloud](https://img.shields.io/badge/GCP-Cloud_Run_%7C_Vertex_AI_%7C_Firestore-4285F4.svg)](https://cloud.google.com/)
[![Google GenAI SDK](https://img.shields.io/badge/Google_GenAI_SDK-google--genai-4285F4.svg)](https://pypi.org/project/google-genai/)
[![Gemini](https://img.shields.io/badge/Gemini-3.5_Flash-8E24AA.svg)](https://deepmind.google/technologies/gemini/)

**Atelier** is an agentic AI studio master designed for remote art students. It pairs **deterministic OpenCV computer vision** (for calculating vanishing points, horizon lines, and per-line angular convergence errors in degrees) with **Gemini 3.5 Flash on Google Cloud Vertex AI** (for empathetic, level-aware pedagogical critiques).

---

## ✅ Mandatory Stack Compliance (Hackathon Requirements)

| Requirement | How Atelier satisfies it | Where |
| :--- | :--- | :--- |
| **Gemini 3.5+ via Gemini API or Vertex AI** | Gemini 3.5 Flash on Vertex AI (critique + dialogue) | [`atelier-agent/src/tools/critique.py`](atelier-agent/src/tools/critique.py) |
| **≥1 Google Agent Framework** | Google GenAI SDK (`google-genai`) — every model call | [`atelier-agent/requirements.txt`](atelier-agent/requirements.txt) · [`src/tools/`](atelier-agent/src/tools/) |
| **≥1 Google Cloud infrastructure service** | Cloud Run · Firestore · GCS · Eventarc · Cloud Scheduler | [`infra/`](infra/) · [`src/tools/`](atelier-agent/src/tools/) |

---

## 🌐 Live Demo & Hosted Deployment

- 💻 **Studio Web Client (Blazor / .NET 10)**: `https://atelier-web-773993294789.europe-west1.run.app`
- 🤖 **Agent Backend API (FastAPI / Cloud Run)**: `https://atelier-agent-773993294789.europe-west1.run.app`
- 📚 **Interactive Swagger API Docs**: `https://atelier-agent-773993294789.europe-west1.run.app/docs`

> 💡 *Note on Cold Starts*: To conserve Google Cloud student budget, Cloud Run services scale to 0 instances when idle. The initial load request may take ~5-10 seconds to spin up containers.

---

## 🏛️ System Architecture

```text
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                   ATELIER STUDIO SYSTEM                                   │
└───────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
 ┌─────────────────────────────────────┐             ┌─────────────────────────────────────┐
 │       STUDENT WEB CLIENT            │             │      BACKGROUND GCS INGESTION       │
 │  Atelier.Web (Blazor Server .NET10) │             │  gs://atelier-hack-inbox/{studentId}/    │
 │  - Multimodal Overlay (Original/AI) │             │  - Private Family Bucket (ADR-006)  │
 │  - Two-Plane Level-Aware Critique   │             │  - Eventarc Object Finalized        │
 │  - Progress Curve (Native SVG)      │             │  - Cloud Scheduler Weekly Digest    │
 └─────────────────────────────────────┘             └─────────────────────────────────────┘
                    │                                                   │
                    └─────────────────────────┬─────────────────────────┘
                                              ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │            ATELIER AGENT BACKEND (Google GenAI SDK + FastAPI / Cloud Run)               │
 │                                                                                         │
 │   ┌───────────────────────────┐                     ┌───────────────────────────────┐   │
 │   │    Intent Pre-Router      │ ──(Chooses k)─────> │   OpenCV Deterministic Engine │   │
 │   │    (Vertex AI 2B/9B)      │                     │   - Deskew & Hough Lines      │   │
 │   │    - Exercise Classification                    │   - RANSAC Vanishing Points   │   │
 │   │    - Canny Threshold Tuning                     │   - Horizon Line & Error (°)  │   │
 │   └───────────────────────────┘                     │   - Base64 Annotated Overlay  │   │
 │                                                     └───────────────────────────────┘   │
 │                                                                     │                   │
 │                                                                     ▼                   │
 │   ┌───────────────────────────┐                     ┌───────────────────────────────┐   │
 │   │ Anti-Hallucination Gate   │ <──(Validates)───── │   Gemini 3.5 Flash Studio     │   │
 │   │ (ADR-001 Validator)       │                     │   (Google Vertex AI)          │   │
 │   │ - Rejects invented metrics│                     │   - Level-Aware Rubric        │   │
 │   │ - Retries with feedback   │                     │   - Two-Plane Structured JSON │   │
 │   └───────────────────────────┘                     └───────────────────────────────┘   │
 └─────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │                 APPEND-ONLY MEMORY & EVENT STORE (Cloud Firestore)                      │
 │   - students/{studentId}/exercises/{id}      (Immutable geometry & critique)            │
 │   - students/{studentId}/exercises/{id}/feedback/{id} (Helpful bool + note: CAPTURE)    │
 │   - Dynamic Profile Derivation               (Tone adaptation & progress curve: ADAPT)  │
 └─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🌟 Key Highlights

- 📐 **Zero Hallucination Architecture (ADR-001)**: Deterministic OpenCV calculates all geometric ground truth ($VP$, $F_1, F_2$, $LH$, degree errors). Gemini teaches and mentors. Gemini *never* estimates or invents measurements.
- 🎨 **Multimodal Interactive Overlay (Best Multimodal UX)**: Instant toggle between original student sketches, color-coded geometric overlays (Green $<2.5^\circ$, Yellow $2.5^\circ-6.0^\circ$, Red $>6.0^\circ$), side-by-side comparison, and line inspection tables.
- 💬 **The 4 Collaborative Verbs ("The Collaborative Partner")**:
  1. **ASK**: Clarifying pre-critique questions to contextualize intent (*"What were you practicing today? Which part felt hardest?"*).
  2. **GUIDE**: Targeted exercise prescriptions driven by recurring deviation patterns.
  3. **CAPTURE**: Explicit student feedback (`helpful: bool` + note) saved as immutable events.
  4. **ADAPT**: Dynamic profile derivation (shifting tone from technical to encouraging automatically).
- 🧠 **Intent Pre-Router on Vertex AI**: before any measurement, the student's own description of what they were practising chooses the perspective model. A beginner who writes *"the corner of a building"* is measured as two-point, because they said so — not as one-point because of a field in their profile. Falls back to the profile level when there is nothing to read, and **says which happened** (`source: vertex | fallback`).
- 📈 **Append-Only Memory & Weekly Digests**: Event-sourced progression tracking in Google Cloud Firestore with automated weekly practice plans synthesized via Cloud Scheduler.
- 🔒 **Async-First & Privacy-Preserving (ADR-004, ADR-006)**: Private Google Cloud Storage inbox (`gs://atelier-hack-inbox/{studentId}/`), Eventarc triggers, signed URLs, and first-names-only privacy model for young students.

---

## 🔍 Honest Technical Gaps Table (Stripboard Pattern)

In the spirit of radical technical honesty, here is what is 100% implemented versus architectural roadmap:

| Feature / Domain Area | Current Implementation Status | Notes & Roadmap |
| :--- | :--- | :--- |
| **1-Point Perspective ($k=1$)** | ✅ **100% Complete & Benchmarked** | Tested on our youngest tester (age 9, drawings used with permission) and golden cases ($0^\circ-9^\circ$ deliberate error). |
| **2-Point Oblique Perspective ($k=2$)** | ✅ **100% Complete & Benchmarked** | RANSAC vanishing point clustering for $F_1$ and $F_2$, horizon tilt, and error per line. |
| **Two-Plane Critique Model** | ✅ **100% Complete & Validated** | Plane A (OpenCV measured) + Plane B (Studio qualitative rubric) strictly separated. |
| **Anti-Hallucination Validator** | ✅ **100% Complete & Tested** | In-code gate rejecting fabricated numerical measurements with feedback retry loop. |
| **Collaborative Loop (4 Verbs)** | ✅ **100% Complete** | Ask, Guide, Capture & Adapt with dynamic tone shift and Firestore append-only models. |
| **Intent Pre-Router** | ✅ Complete | `/api/router/classify` chooses k=1 or k=2 from the student's description, labelled with its own provenance. **The Gemma bonus is not claimed**: Gemma is not a publisher model on Vertex AI and reaching it needs a billed Model Garden endpoint. |
| **Async GCS Ingestion (Eventarc + Scheduler)** | ✅ **Verified on GCP (2026-08-18)** | Object finalize triggers Cloud Run pipeline and persists immutable events in Firestore. |
| **Multimodal Blazor UI** | ✅ **100% Complete** | Interactive overlay viewer, side-by-side comparison, and SVG progress curve. |
| **3-Point Curvilinear Perspective ($k=3$)** | ⏳ *Planned for Phase 2* | 3-point worm/bird's-eye perspective is planned for high-level architectural rendering. |
| **Live Camera WebRTC Stream** | ⏳ *Planned for Phase 2* | Current version operates on uploaded photos and GCS inbox drops; live video streaming planned. |

---

## 🚀 Quickstart: Clean-Machine Setup

### Prerequisites
- [.NET 10 SDK](https://dotnet.microsoft.com/download)
- [Python 3.12+](https://python.org/)

### 1. Clone the Repository
```bash
git clone https://github.com/hvaler/atelier.git
cd atelier
```

### 2. Seed the Calibration Benchmark Dataset
```bash
# Windows:
atelier-agent\.venv\Scripts\python demo/generate_calibration_dataset.py
# Linux / macOS:
# python demo/generate_calibration_dataset.py
```

### 3. Start the Backend (`atelier-agent`)
```bash
cd atelier-agent
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
python -m uvicorn src.main:app --reload --port 8000
```
*API docs available at:* `http://localhost:8000/docs`

### 4. Start the Web UI (`Atelier.Web`)
In a separate terminal:
```bash
cd Atelier.Web
dotnet run
```
*Open your browser at:* `http://localhost:5000` (or the URL shown in console).

---

## 🧪 Running the Test Suites

All claims are backed by executable tests logged in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

```bash
# Run Python backend tests (29 tests)
cd atelier-agent
.venv\Scripts\python -m pytest tests -v

# Run .NET Blazor tests (7 tests)
dotnet test Atelier.slnx
```

---

## 📄 License
This project is licensed under the [Apache 2.0 License](LICENSE).
