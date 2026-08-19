# Atelier — System Architecture & Infrastructure Design

> **Invariants**: ADR-001 (Deterministic OpenCV vs Gemini Pedagogy), ADR-002 (Two-Service Clean Architecture), ADR-003 (Firestore NoSQL Append-Only), ADR-004 (Async Ingestion + Weekly Digest).

---

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        User["🎨 Student / Instructor"]
        WebUI["💻 Atelier.Web\n(Blazor Server / .NET 10)\n- Multimodal Overlay Viewer\n- Two-Plane Critique View\n- Student Switcher & Analytics"]
    end

    subgraph "Google Cloud Platform (GCP)"
        subgraph "Ingestion & Storage"
            GCS["🗄️ Google Cloud Storage\ngs://atelier-hack-inbox/{studentId}/\n(Private Bucket)"]
            Eventarc["⚡ Eventarc\nStorage Object Finalized"]
            Scheduler["⏰ Cloud Scheduler\nWeekly Digest Cron"]
        end

        subgraph "Compute: Google Cloud Run"
            AgentService["🤖 atelier-agent\n(FastAPI / Python 3.12)\n- Gemma Pre-Router\n- OpenCV Deterministic Geometry\n- Gemini Flash Client\n- Anti-Hallucination Validator"]
        end

        subgraph "Google Vertex AI"
            Gemma["🧠 Gemma 2B/9B\n(Lightweight Pre-Routing)"]
            Gemini["✨ Gemini Flash\n(Level-Aware Two-Plane Critique)"]
        end

        subgraph "Memory & State"
            Firestore["📦 Cloud Firestore\n(Append-Only Event Store)\nstudents/{id}/exercises/{id}\n/feedback/{id}"]
        end
    end

    User -->|Interactive Web Session| WebUI
    User -->|Direct Photo Drop| GCS

    WebUI -->|REST API /api/*| AgentService
    GCS -->|Object Finalize Trigger| Eventarc
    Eventarc -->|CloudEvents POST /api/events/gcs-upload| AgentService
    Scheduler -->|Weekly POST /api/digest/weekly| AgentService

    AgentService -->|Pre-Classify Drawing| Gemma
    AgentService -->|Generate Studio Critique| Gemini
    AgentService -->|Persist Exercises & Read Profile| Firestore

    AgentService -->|Return Annotated Overlay & Critique| WebUI
```

---

## 2. Component Breakdown

### 2.1. `atelier-agent` (Python 3.12 / FastAPI)
- **Deterministic Geometry Engine (`src/tools/geometry.py`)**:
  - Image deskewing and adaptive thresholding via OpenCV.
  - Probabilistic Hough Transform (`cv2.HoughLinesP`).
  - Pairwise intersection clustering with RANSAC for vanishing point estimation ($k=1$ and $k=2$).
  - Horizon line ($LH$) estimation and angle deviation calculations in degrees ($^\circ$).
  - Generation of Base64 annotated overlays with traffic-light color encoding (Green: $<2.5^\circ$, Yellow: $2.5^\circ - 6.0^\circ$, Red: $>6.0^\circ$).
- **Gemma Pre-Router (`src/tools/gemma_router.py`)**:
  - Pre-classifies exercise types and tunes Canny edge thresholds to minimize compute before heavy LLM execution.
- **Gemini Flash Client (`src/tools/critique.py`)**:
  - Prompts calibrated with authentic studio master rubrics (RUNBOOK §2).
  - Level-aware tone differentiation (`beginner` for 9-year-olds vs `advanced` for animation university students).
- **Anti-Hallucination Validator (`src/tools/validator.py`)**:
  - Enforces ADR-001 by guaranteeing that Plane A (Measured Findings) only contains numbers directly derived from OpenCV. Rejects and retries if fabricated metrics are detected.
- **Append-Only Memory Engine (`src/tools/memory.py` & `collaborative.py`)**:
  - Implements the 4 verbs: **ASK**, **GUIDE**, **CAPTURE**, and **ADAPT**.
  - Dynamically calculates student learning curves and shifts tone based on explicit feedback events.

### 2.2. `Atelier.Web` (.NET 10 / Blazor Server)
- **Multimodal Overlay Component (`Components/Shared/OverlayViewer.razor`)**:
  - Instant toggle between *Annotated Overlay*, *Original Drawing*, *Side-by-Side Split View*, and *Metric Data Table*.
- **Two-Plane Critique Component (`Components/Shared/TwoPlaneCritique.razor`)**:
  - Clear visual demarcation of quantitative measurements (Plane A) vs qualitative instructor feedback (Plane B).
- **Progression Dashboard (`Components/Shared/ProgressChart.razor`)**:
  - Native SVG progress curve showing convergence error reduction over sequential drawings.
  - Weekly 3-day practice prescription plan (Monday, Wednesday, Friday).

---

## 3. Data Flow Diagram (Sync & Async)

```mermaid
sequenceDiagram
    autonumber
    actor Student as 🎨 Student (Young Tester / Sofia)
    participant Web as 💻 Atelier.Web (Blazor)
    participant Agent as 🤖 atelier-agent (Cloud Run)
    participant CV as 📐 OpenCV Engine
    participant Vertex as ✨ Vertex AI (Gemini Flash)
    participant DB as 📦 Cloud Firestore

    Student->>Web: Uploads drawing photo
    Web->>Student: Verb 1 (ASK): "What were you practicing today?"
    Student->>Web: Submits intent context
    Web->>Agent: POST /api/analyze & POST /api/critique
    Agent->>CV: Compute RANSAC VPs & Angular Error (deg)
    CV-->>Agent: Exact metrics & Annotated Base64 Overlay
    Agent->>Vertex: Generate Level-Aware Two-Plane Critique
    Vertex-->>Agent: Structured Critique JSON
    Agent->>Agent: Validate: Check numbers match OpenCV (ADR-001)
    Agent->>DB: Append ExerciseRecord
    Agent-->>Web: Complete Result (Overlay + Critique)
    Web->>Student: Displays Multimodal Overlay & Two-Plane Critique
    Student->>Web: Verb 3 (CAPTURE): "Helpful 👍" + note
    Web->>Agent: POST /api/exercises/{id}/feedback
    Agent->>DB: Append FeedbackEvent
    Agent->>Agent: Verb 4 (ADAPT): Recompute profile & progress curve
```
