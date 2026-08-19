# Video Recording & Submission Runbook — Atelier

> **Hackathon Requirement**: Video demo $\le 4$ minutes (recommended 3:00 - 3:30), uploaded to YouTube as **PUBLIC**.  
> **Mandatory Visual**: Live UNCUT section showing the Google Cloud Platform Console (Cloud Run, Eventarc, Firestore, and Vertex AI logs).

---

## 🎬 Step-by-Step Recording Plan (Total: 3:30 min)

### Phase 1: The Vision & Daughter's Sketchbook (0:00 - 0:45)
- **Visual**: Speaker on webcam holding a physical sketchbook page with a hand-drawn 3D box.
- **Narrative**: Explain the core problem: children and remote art students cannot see why their boxes look deformed ($4^\circ$ angular error). Standard AI chatbots hallucinate measurements.
- **Key Catchphrase**: *"The geometry measures, the AI teaches, the student grows." (ADR-001)*.

---

### Phase 2: Live UI Demonstration — Blazor Server (0:45 - 2:15)
- **Visual**: Screen recording of `Atelier.Web` running live.
- **Demonstrate**:
  1. **Student Switcher**: Switch to **Young Tester (Age 9, Beginner)**.
  2. **Verb 1 (ASK)**: Show the clarifying dialogue card (*"What kind of 3D box were you practicing today? Which corner felt hardest?"*).
  3. **Multimodal Overlay (The Star UX)**:
     - Click **🎨 Annotated Overlay**: show the traffic-light color-coded lines (Green $<2.5^\circ$, Yellow, Red $>6.0^\circ$), horizon line ($LH$) in cyan, and vanishing points.
     - Click **↔️ Side-by-Side Comparison** to highlight student sketch vs AI overlay.
     - Click **🔍 Line Inspection Table** to show deterministic line coordinates and degree errors.
  4. **Two-Plane Critique**:
     - Point out **Plane A (Measured Findings)**: exact OpenCV degree numbers with zero hallucinations.
     - Point out **Plane B (Studio Observations)**: gentle, encouraging feedback on line weight and box faces.
  5. **Verb 3 (CAPTURE) & Verb 4 (ADAPT)**:
     - Click **👍 Helpful** + enter a brief note. Show the profile adaptation banner.
  6. **Level-Aware Shift**: Switch to **Sofia (Advanced)**:
     - Show how vocabulary instantly switches to studio master technical terms ($LH$, $LT$, true magnitude, $F_1/F_2$ oblique convergence).
     - Navigate to **📈 Student Progression**. Read the figures off the page as they are — they come
       from Firestore and they are low because they are real. **Do not promise a smooth improvement
       curve**: an earlier version of this runbook told you to show 4.8° falling to 1.8°, which was a
       hardcoded fallback in the web client, not a student's history. It has been deleted.

  7. **The refusal — the strongest ten seconds available.** Upload something that is *not* a
     drawing (a page of handwriting works). Gemini 3.5 Flash looks at it before anything is
     measured and declines, in its own words: *"only repeated lines of text and no perspective
     drawings or construction lines."* **Nothing is measured and nothing is critiqued.** Say why
     that matters: without the gate the page goes through RANSAC, finds a vanishing point among
     whatever edges exist, and spends real tokens telling a child their line weight is confident.
  8. **The honesty beat.** Point at the green **Anti-Hallucination: Validated** badge and say what
     gates it: it appears only when Gemini actually answered. When the model is unreachable the
     same panel turns amber — *"Deterministic fallback — no model answered"* — with the real
     `model_version` beneath it. The badge is earned per critique, not painted on.
  9. *(If it fires)* **Description against drawing.** Type "the corner of a building" over a
     one-point sketch. Gemma reads the words, the engine has measured the drawing, and they
     disagree — so Atelier says so and **changes nothing**: *"You described a 2-point-oblique.
     This drawing was measured as 1-point, which is what it looks like."* The measurement is
     evidence; the description is a claim. Do not re-shoot to force this one — it depends on how
     the router reads the sentence, and a take chosen because it went your way is the thing this
     project is against.

---

### Phase 3: Live Google Cloud Console Inspection [MANDATORY ATA] (2:15 - 3:00)
- **Visual**: Switch browser tab to the live Google Cloud Platform Console (`console.cloud.google.com`).
- **Showcase**:
  1. **Cloud Run Services**:
     - `atelier-agent` (Python/FastAPI) and `atelier-web` (.NET 10) active revisions and metrics.
     - Open **Logs Tab** showing incoming `/api/analyze`, `/api/critique`, and `/api/router/classify` requests.
  2. **Cloud Storage & Eventarc**:
     - `gs://atelier-hack-inbox/` bucket and the Eventarc trigger (`google.cloud.storage.object.v1.finalized`).
  3. **Cloud Firestore**:
     - Show the `students/{studentId}/exercises/` and `feedback/` collection tree demonstrating the append-only event-sourcing model.
  4. **Vertex AI Studio**:
     - Quick view of the Gemini 3.5 Flash endpoint in europe-west3.

---

### Phase 4: Wrap-Up & Open Source Invitation (3:00 - 3:30)
- **Visual**: GitHub repository page (`https://github.com/hvaler/atelier`).
- **Narrative**:
  - 44 automated tests (36 Python + 8 .NET), Apache 2.0 open-source, architecture documentation, and live demo URL.
  - Closing sentence: *"Atelier makes invisible perspective errors visible, empowering art students everywhere to grow with confidence."*

---

## ⚠️ Critical Submission Instructions

1. **YouTube Upload**:
   - Title: `Atelier — AI Studio Master for Remote Art Students | All Things Agentic Hackathon`
   - Privacy: **Public** (Do NOT set to Private or Unlisted).
   - Create a **FRESH new video** (do not reuse or replace old links).
2. **Submission Timing Advisory**:
   - **Recommended Submission Date**: **August 29 or August 30, 2026**.
   - **Hard Deadline**: August 31, 2026 at 17:00 PT (= September 1, 2026 at 02:00 CEST).
   - *Warning*: Do NOT wait for European August 31 evening, as the deadline expires in the early morning of September 1st CEST. Submit at least 24 hours in advance.
3. **Checklist Before Clicking "Submit Project" on Devpost**:
   - [ ] Public GitHub repo URL (`https://github.com/hvaler/atelier`)
   - [ ] Hosted public demo URL
   - [ ] Public YouTube video link
   - [ ] Architecture diagram attached
   - [ ] Category track: *The Collaborative Partner* checked
   - [ ] Bonus claims listed with direct links
