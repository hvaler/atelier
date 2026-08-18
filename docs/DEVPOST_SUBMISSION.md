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
"The geometry measures, the AI teaches, the student grows." An AI studio tutor that decouples deterministic OpenCV computer vision from Gemini on Google Cloud Vertex AI to deliver zero-hallucination, level-aware perspective drawing critique and dynamic progression.
```

### 3. Category Track Selection
- [x] **The Collaborative Partner**
- [ ] The Explorer
- [ ] The Specialist

### 4. About the Project (Full Description)

#### 💡 Inspiration
When our youngest tester (age 9, drawings used with permission) began practicing 3D perspective boxes and buildings in her sketchbook, she hit a universal roadblock in remote art education: she knew her drawings looked slightly "off", but couldn't identify the subtle 4-degree angle error causing the distortion. 

When we tested generic multi-modal AI chatbots, they hallucinated measurements—inventing arbitrary degrees or claiming straight lines were curved. Remote art students don't need a chatbot guessing angles; they need a **Studio Master**: an agent that grounds its feedback in mathematical truth while teaching with warmth and pedagogical empathy.

That sparked our core architectural invariant:
> **"The geometry measures, the AI teaches, the student grows." (ADR-001)**

---

#### 🛠️ What It Does
Atelier is an agentic AI studio master for perspective drawing:
1. **Deterministic Geometry Engine (OpenCV)**: Analyzes student sketches, deskews notebook pages, runs RANSAC clustering to solve vanishing points ($VP$ or $F_1, F_2$), detects the horizon line ($LH$), and computes per-line convergence error in degrees ($^\circ$).
2. **Multimodal Interactive Overlay (Best Multimodal UX)**: An interactive canvas allowing students to toggle between their raw sketch, a color-coded annotated overlay (Green $<2.5^\circ$, Yellow $2.5^\circ-6.0^\circ$, Red $>6.0^\circ$), side-by-side comparison, and line inspection tables.
3. **The 4 Collaborative Verbs ("The Collaborative Partner")**:
   - **ASK**: Clarifying questions before analysis (*"What were you practicing today? Which corner felt hardest?"*) to contextualize feedback.
   - **GUIDE**: Targeted follow-up exercises derived from recurring deviation patterns (e.g. *Targeted $F_1$ Convergence Drill*).
   - **CAPTURE**: Explicit student feedback (`helpful: bool` + note) saved as immutable events in Cloud Firestore.
   - **ADAPT**: Dynamic profile derivation that shifts tone (from technical to encouraging) and tracks the convergence error reduction curve over time.
4. **Two-Plane Critique Model**: 
   - *Plane A (Measured Findings)*: 100% strictly verified by OpenCV.
   - *Plane B (Studio Observations)*: Qualitative feedback on line weight (construction vs definitive solution), spatial legibility, and cleanliness.
5. **Anti-Hallucination Validator**: An in-code gate that rejects and retries any LLM response containing fabricated numbers not present in the geometric ground truth.
6. **Async Ingestion & Weekly Digest**: Background photo processing via GCS and Eventarc on Cloud Run, plus weekly progress digests with 3-day practice prescriptions synthesized via Cloud Scheduler.

---

#### ⚙️ How We Built It
- **AI & Models**: Google Vertex AI (`gemini-2.5-flash` / `gemini-2.0-flash` for level-aware pedagogical critiques and `gemma` for lightweight pre-routing and parameter tuning).
- **Backend Service (`atelier-agent`)**: Python 3.12, FastAPI, OpenCV (`opencv-python-headless`), NumPy, Pydantic v2, and Google Cloud ADK.
- **Frontend Service (`Atelier.Web`)**: .NET 10, Blazor Server, C#, responsive dark studio aesthetic with native SVG progression charts.
- **Cloud Infrastructure**: Google Cloud Run (microservices hosting), Google Cloud Storage (`gs://atelier-inbox/{studentId}/`), Eventarc (CloudEvents), Cloud Scheduler (cron digests), and Cloud Firestore (append-only event store).
- **CI/CD & Governance**: GitHub Actions, Workload Identity Federation (WIF), and automated testing suites (29 Python tests + 7 .NET integration tests).

---

#### 🧗 Challenges We Ran Into
- **Line Direction Normalization**: In perspective drawing, pencil lines have unoriented directions $\theta \in [-\pi, \pi]$. Calculating true angular error to a vanishing point required modulo $\pi$ acute wrapping ($[0, 90^\circ]$) to avoid false $180^\circ$ inversion penalties.
- **Cloud Run Proxy Header Termination (TEC-007)**: Ensuring ASP.NET Core correctly recognized HTTPS behind Cloud Run's reverse proxy by configuring `ForwardedHeadersOptions` with `KnownIPNetworks.Clear()` and `KnownProxies.Clear()`.
- **Anti-Hallucination Guardrails**: Designing a strict regex/set validator that parses the LLM's quantitative output and triggers automated retries with corrective error messages if invented numbers appear.

---

#### 🏆 Accomplishments We're Proud Of
- **Zero Hallucination Guarantee (ADR-001)**: Mathematical proof and 36 automated unit/integration tests confirming that the AI never fabricates measurements.
- **True Level-Awareness**: The exact same agent seamlessly critiques our youngest tester (age 9) using intuitive language about *"lines heading towards the horizon dot"* and an advanced animation student (Sofia) using rigorous studio master terminology (*$LH$, $LT$, true magnitude, and $F_1/F_2$ convergence*).
- **Golden Case Benchmark**: A comprehensive dataset with deliberate known errors ($0^\circ, 4^\circ, 6^\circ, 9^\circ$) validating OpenCV detection accuracy.

---

#### 📚 What We Learned
Hybrid intelligence is essential for technical agentic applications. Large language models should not be forced to do raw trigonometry; instead, computer vision should provide the ground truth physics and geometry, while generative models provide the language, empathy, and pedagogy.

---

#### 🔮 What's Next for Atelier
- 📐 **3-Point Curvilinear Perspective ($k=3$)**: Expanding the RANSAC clustering to 3-point perspective (worm's-eye and bird's-eye views).
- 📹 **Live WebRTC Camera Ingestion**: Streaming video frames directly from the student's phone camera with real-time HUD overlays.
- 🏫 **Classroom Cohort Mode**: Aggregating progress curves across entire art school cohorts for studio professors.

---

### 5. Links & Bonus Submissions (+0.6 pts Total)

- **GitHub Repository (Public & Apache 2.0)**: `https://github.com/hvaler/atelier`
- **Hosted Public Demo URL**: `https://atelier-web-1065181741517.europe-west3.run.app`
- **Architecture Documentation**: `https://github.com/hvaler/atelier/blob/main/docs/ARCHITECTURE.md`
- **Evidence & Verification Log**: `https://github.com/hvaler/atelier/blob/main/docs/EVIDENCE.md`
- **Bonus 1 (+0.2 pts): Gemma Pre-Router**: Implemented in `atelier-agent/src/tools/gemma_router.py` with endpoint `/api/router/classify`.
- **Bonus 2 (+0.2 pts): Technical Article on Dev.to**: Draft ready in `docs/ARTICLE_DEVTO.md` (*"The geometry measures, the AI teaches: building an art tutor for my daughters with ADK + OpenCV"*).
- **Bonus 3 (+0.2 pts): Social Media Posts**: Ready in `docs/SOCIAL_POSTS.md` with `#AllThingsAgenticHackathon`.
