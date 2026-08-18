# The Geometry Measures, the AI Teaches: Building an Art Studio Tutor with ADK, Vertex AI & OpenCV

> *This project was created for the Devpost All Things Agentic Hackathon.*

---

## 1. The Origin: A 9-Year-Old Daughter's Perspective Notebook

When my 9-year-old daughter began practicing drawing cubes and perspective boxes in her sketchbook, I noticed a universal paradox in remote art education:

- **Students can't see their own angular deviations** (a $4^\circ$ or $7^\circ$ misalignment to the horizon line makes a box look subtly "off" or deformed, but beginners don't know *why*).
- **Generic LLMs hallucinate visual measurements**: If you ask a multi-modal LLM to critique a drawing, it often invents arbitrary numbers ("your angle is off by 15 degrees") without any spatial ground truth.

To bridge this gap, I designed **Atelier** around a single strict invariant:

> **"The geometry measures, the AI teaches, the student grows." (ADR-001)**

Atelier is an agentic AI studio master for remote art students that decouples deterministic geometric calculation (via OpenCV) from high-empathy pedagogical critique (via Gemini 3.5 Flash on Vertex AI).

---

## 2. Architecture: Deterministic Rigor Meets Pedagogical Empathy

```
                                  ATELIER ARCHITECTURE
 ┌──────────────────────┐         ┌────────────────────────┐         ┌───────────────────────┐
 │   Atelier.Web        │         │   Gemma Router         │         │  OpenCV Geometry      │
 │   (Blazor / .NET 10) │ ──────> │   (Vertex AI 2B/9B)    │ ──────> │  - Deskew / Canny     │
 │   - Multimodal UX    │         │   - Exercise Classify  │         │  - RANSAC VPs (k=1,2) │
 │   - Annotated Overlay│         │   - Pre-Gemini Tuning  │         │  - Horizon Line (LH)  │
 └──────────────────────┘         └────────────────────────┘         │  - Error in Degrees   │
            │                                                        └───────────────────────┘
            │                                                                    │
            ▼                                                                    ▼
 ┌──────────────────────┐         ┌────────────────────────┐         ┌───────────────────────┐
 │  Collaborative Loop  │ <────── │  Anti-Hallucination    │ <────── │  Gemini 3.5 Flash     │
 │  - ASK Clarification │         │  Validator (ADR-001)   │         │  (Google Vertex AI)   │
 │  - GUIDE Next Drill  │         │  - Verifies degrees    │         │  - Level-Aware Rubric │
 │  - CAPTURE Feedback  │         │  - Rejects fakes       │         │  - Two-Plane Critique │
 │  - ADAPT Profile     │         └────────────────────────┘         └───────────────────────┘
```

### The Two-Plane Critique Model
Atelier divides every critique into two distinct, validated planes:
1. **Plane A (Measured Findings)**: 100% strictly derived from OpenCV metrics. It reports exact vanishing points ($VP$ or $F_1, F_2$), horizon line tilt, and per-line angular deviation in degrees.
2. **Plane B (Studio Observations)**: Qualitative criteria where the LLM evaluates the drawing like a human master instructor (line weight contrast between construction traces and definitive contours, spatial legibility, and cleanliness).

An **Anti-Hallucination Validator** intercepts the critique. If the model mentions any numerical measurement not found in the OpenCV payload, the response is rejected and regenerated with corrective feedback.

---

## 3. The 4 Verbs of "The Collaborative Partner"

Atelier is not a one-shot chatbot; it acts as a proactive studio partner orchestrating 4 collaborative verbs:

1. **ASK**: Before analyzing, Atelier asks the student: *"What were you practicing today? Which part felt hardest?"* The answers calibrate the feedback depth.
2. **GUIDE**: Instead of generic advice, Atelier prescribes specific follow-up drills targeted at the student's primary recurring deviation (e.g., *Targeted $F_1$ Convergence Drill*).
3. **CAPTURE**: After every review, the student provides explicit feedback (`helpful: bool` + note). This is persisted as an immutable event in Google Cloud Firestore (ADR-005).
4. **ADAPT**: Learning profiles are never edited manually. Atelier dynamically derives the student's `tone_preference` (adapting from technical to encouraging if recent feedback indicates frustration) and tracks the convergence error reduction curve over time.

---

## 4. Asynchronous Pipeline & Cloud Run Deployment

- **Async-first Ingestion**: Students or parents drop sketchbook photos into a private Google Cloud Storage bucket (`atelier-inbox/{studentId}/`). Eventarc fires a CloudEvent to the Cloud Run agent service, executing geometry calculation and critique in the background.
- **Weekly Digest**: Cloud Scheduler triggers weekly aggregations, calculating the error reduction percentage and prescribing a 3-day practice plan (Monday, Wednesday, Friday) for the upcoming week.
- **Production Hardening**: Deployed on Google Cloud Run with `.NET 10` (using `KnownIPNetworks.Clear()` for proxy header termination) and Python FastAPI microservices.

---

## 5. What We Learned

Building Atelier demonstrated that the future of agentic AI in technical disciplines (art, engineering, surgery, architecture) requires **hybrid intelligence**:
- Use computer vision for math, physics, and ground truth.
- Use generative LLMs for language, empathy, pedagogy, and inspiration.

When these two forces combine, students of all ages can see their invisible mistakes and grow with confidence.

---
*Built with Google Agent Development Kit (ADK), Vertex AI (Gemini 3.5 Flash & Gemma), Google Cloud Run, Cloud Storage, Eventarc, Firestore, OpenCV, and .NET 10.*
