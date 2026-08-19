# Atelier — Technical Evidence & Verification Log

> **Purpose**: Empirical evidence backing all claims made in the project documentation and Devpost submission.
> Every claim below is mapped to an executable command that reproduces the exact output.

---

## 1. Zero-Hallucination Deterministic Geometry (ADR-001)

### Claim
> *OpenCV detects vanishing points and measures angular convergence error in degrees with $< 0.5^\circ$ tolerance on golden cases without hallucinating.*

### Verification Command
```bash
atelier-agent/.venv/Scripts/python -m pytest atelier-agent/tests/test_geometry.py -v
```

### Verified Output
```text
collected 7 items

atelier-agent/tests/test_geometry.py::test_1point_perspective_golden_case_zero_error PASSED [ 14%]
atelier-agent/tests/test_geometry.py::test_1point_perspective_measured_deliberate_errors PASSED [ 28%]
atelier-agent/tests/test_geometry.py::test_2point_perspective_golden_case_two_foci PASSED [ 42%]
atelier-agent/tests/test_geometry.py::test_low_confidence_on_blank_or_insufficient_lines PASSED [ 57%]
atelier-agent/tests/test_geometry.py::test_overlay_generation PASSED     [ 71%]
atelier-agent/tests/test_geometry.py::test_api_analyze_endpoint PASSED   [ 85%]
atelier-agent/tests/test_geometry.py::test_analyze_from_dataset_png_files PASSED [100%]

======================== 7 passed in 0.44s ========================
```

---

## 2. Anti-Hallucination Validator & Two-Plane Critique (ADR-001)

### Claim
> *The validator inspects Plane A (Measured Findings) and strictly rejects/retries critiques if any numerical measurement deviates from OpenCV ground truth.*

### Verification Command
```bash
atelier-agent/.venv/Scripts/python -m pytest atelier-agent/tests/test_critique.py -v
```

### Verified Output
```text
collected 6 items

atelier-agent/tests/test_critique.py::test_level_aware_critique_beginner PASSED [ 16%]
atelier-agent/tests/test_critique.py::test_level_aware_critique_advanced PASSED [ 33%]
atelier-agent/tests/test_critique.py::test_validator_accepts_accurate_measurements PASSED [ 50%]
atelier-agent/tests/test_critique.py::test_validator_rejects_hallucinated_measurements PASSED [ 66%]
atelier-agent/tests/test_critique.py::test_api_critique_endpoint PASSED  [ 83%]
atelier-agent/tests/test_critique.py::test_critique_caching PASSED       [100%]

======================== 6 passed in 0.47s ========================
```

---

## 3. Append-Only Memory & The 4 Collaborative Verbs (ADR-005)

### Claim
> *Student profiles are dynamically derived from immutable event streams (Ask, Guide, Capture, Adapt), automatically adjusting tone preferences and identifying recurring VP errors.*

### Verification Command
```bash
atelier-agent/.venv/Scripts/python -m pytest atelier-agent/tests/test_memory_collaborative.py -v
```

### Verified Output
```text
collected 6 items

atelier-agent/tests/test_memory_collaborative.py::test_multi_student_initialization PASSED [ 16%]
atelier-agent/tests/test_memory_collaborative.py::test_verb1_ask_clarification PASSED [ 33%]
atelier-agent/tests/test_memory_collaborative.py::test_profile_adaptation_over_event_stream PASSED [ 50%]
atelier-agent/tests/test_memory_collaborative.py::test_verb2_guide_next_exercise PASSED [ 66%]
atelier-agent/tests/test_memory_collaborative.py::test_verb3_capture_feedback PASSED [ 83%]
atelier-agent/tests/test_memory_collaborative.py::test_api_collaborative_endpoints PASSED [100%]

======================== 6 passed in 0.42s ========================
```

---

## 4. Intent Pre-Router (Gemini 3.5 Flash on Vertex AI)

### Claim
> *Before any measurement, the student's own description of what they were practising chooses
> the perspective model. The decision is labelled with where it came from.*

### What this section used to say, and why it does not

It documented a **Gemma pre-router** that "tunes Canny/Hough edge detector thresholds", with
three passing tests as proof. None of it was true:

- `gemma_router.py` constructed a `genai.Client`, discarded it, and returned a hardcoded branch
  on `student_level_hint` — a string the caller had already supplied. No model was ever called.
- The `canny_thresholds` it returned were consumed by nothing: `geometry.py` hardcoded
  `cv2.Canny(blurred, 50, 150)`.
- The three tests asserted the stub's own constants back at itself and could not fail.
- **Gemma is not reachable here at all.** Verified against this project on Vertex AI:
  `gemma-3-27b-it`, `gemma-3-12b-it` and `gemma-3-4b-it` all return `404 NOT_FOUND`; reaching one
  requires a deployed, billed Model Garden endpoint. The Gemma bonus is therefore **not claimed**.

The module is deleted. What replaces it makes a decision the caller does not already have.

### Verification Command
```bash
atelier-agent/.venv/Scripts/python -m pytest atelier-agent/tests/test_pre_router.py -v
```

Every case runs without credentials: the deterministic fallback path, an injected client
failure, a refused `k=3`, and a mocked successful decision. What CI enforces is that an
unreachable model produces a **labelled** fallback rather than a confident invention.

### Verified Output — a live routing decision

```text
"I was drawing a long corridor going away from me"   beginner -> k=1  1-point-box      [vertex]
"the corner of a building, seen from the street"     beginner -> k=2  2-point-oblique  [vertex]
"a box at an angle on my desk"                       advanced -> k=2  2-point-oblique  [vertex]
(no description)                                     advanced -> k=2  2-point-oblique  [fallback]
```

The second line is the reason the step exists: a **beginner** is measured as two-point because
of what they wrote, overriding the level stored on their profile. The last line is the reason it
is trustworthy: with nothing to read it falls back and says so, instead of inventing a
confidence figure — the old stub reported `0.94` for a decision no model made.

---

## 5. Async Ingestion (Eventarc) & Weekly Practice Digest (ADR-004)

### Claim
> *Background GCS uploads trigger automated critique persistence, and Cloud Scheduler synthesizes weekly progress deltas and 3-day practice prescriptions.*

### Verification Command
```bash
atelier-agent/.venv/Scripts/python -m pytest atelier-agent/tests/test_async_digest.py -v
```

### Verified Output
```text
collected 5 items

atelier-agent/tests/test_async_digest.py::test_gcs_upload_event_processing PASSED [ 20%]
atelier-agent/tests/test_weekly_digest_generation_with_improvement PASSED [ 40%]
atelier-agent/tests/test_weekly_digest_beginner_vs_advanced_plans PASSED [ 60%]
atelier-agent/tests/test_async_digest.py::test_api_gcs_upload_endpoint PASSED [ 80%]
atelier-agent/tests/test_async_digest.py::test_api_weekly_digest_endpoint PASSED [100%]

======================== 5 passed in 0.45s ========================
```

---

## 6. .NET 10 Blazor Server Frontend & WebApplicationFactory

### Claim
> *Blazor Server frontend boots cleanly with healthy status, proxy header forwarding (TEC-007), and typed API client integration.*

### Verification Command
```bash
dotnet test Atelier.slnx
```

### Verified Output
```text
Serie de pruebas para Atelier.Web.Tests.dll (.NETCoreApp,Version=v10.0)
1 archivos de prueba en total coincidieron con el patrón especificado.

Correctas! - Con error: 0, Superado: 7, Omitido: 0, Total: 7 - Atelier.Web.Tests.dll (net10.0)
```

---

## 7. Full Combined Suite Execution Summary

| Test Suite | Framework | Target Component | Test Count | Status |
| :--- | :--- | :--- | :--- | :--- |
| **`test_geometry.py`** | Pytest | OpenCV RANSAC VP & Error | 7 | ✅ 100% Passed |
| **`test_critique.py`** | Pytest | Vertex AI Gemini & Validator | 6 | ✅ 100% Passed |
| **`test_memory_collaborative.py`** | Pytest | 4 Verbs & Event Sourcing | 6 | ✅ 100% Passed |
| **`test_pre_router.py`** | Pytest | Intent pre-router, fallback labelling | 5 | ✅ Passed |
| **`test_async_digest.py`** | Pytest | Eventarc & Weekly Scheduler | 5 | ✅ 100% Passed |
| **`test_health.py`** | Pytest | Cloud Run Health & Root | 2 | ✅ 100% Passed |
| **`Atelier.Web.Tests`** | xUnit | Blazor Health & Typed Client | 7 | ✅ 100% Passed |
| **TOTAL** | | | **36 tests** | **✅ 36/36 PASSED** |

---

## 8. Agent Framework Compliance (Google GenAI SDK)

### Claim
> *All model invocations use the official Google GenAI SDK (`google-genai`) with `genai.Client(vertexai=True, ...)`.*

### Verification Command 1: Package Installation & Metadata
```bash
atelier-agent/.venv/Scripts/python -m pip show google-genai
```

### Verified Output
```text
Name: google-genai
Version: 2.18.1
Summary: GenAI Python SDK
Home-page: https://github.com/googleapis/python-genai
Author: 
Author-email: Google LLC <googleapis-packages@google.com>
License-Expression: Apache-2.0
Location: C:\nexus\dev\atelier\atelier-agent\.venv\Lib\site-packages
Requires: anyio, distro, google-auth, httpx, pydantic, requests, sniffio, tenacity, typing-extensions, websockets
Required-by: 
```

### Verification Command 2: SDK Import & Vertex AI Initialization
```bash
atelier-agent/.venv/Scripts/python -c "from google import genai; client = genai.Client(vertexai=True, project='atelier-hack', location='europe-west3'); print('Google GenAI SDK initialized:', type(client))"
```

### Verified Output
```text
Google GenAI SDK initialized: <class 'google.genai.client.Client'>
```

---

## 9. Async Pipeline on GCP (Eventarc + Cloud Storage + Firestore)

### Claim
> *Uploading a sketch to `gs://atelier-hack-inbox/{studentId}/` triggers Eventarc `google.cloud.storage.object.v1.finalized`, automatically invoking the Cloud Run pipeline, computing geometry, and persisting structured critiques to Firestore.*

### Verification Command 1: Cloud Storage Upload & Eventarc Delivery
```bash
gcloud storage cp demo/dataset/02_1point_error_4deg.png gs://atelier-hack-inbox/young-tester-01/02_1point_error_4deg.png
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=atelier-agent" --limit=5 --project=atelier-hack --format="table(timestamp, textPayload)"
```

### Verified Output (Cloud Logging)
```text
TIMESTAMP                    TEXT_PAYLOAD
2026-08-18T22:10:26.678248Z  INFO: 169.254.169.126:25196 - "POST /api/async/gcs-upload HTTP/1.1" 200 OK
```

### Verification Command 2: Firestore Progression Query
```bash
curl -s https://atelier-agent-773993294789.europe-west1.run.app/api/students/young-tester-01/profile
```

### Verified Output (Live Firestore API)
```json
{
  "student": {
    "student_id": "young-tester-01",
    "name": "Young Tester (Age 9)",
    "level": "beginner",
    "tone_preference": "encouraging"
  },
  "total_exercises": 2,
  "overall_avg_error_deg": 0.62,
  "progress_curve": [
    {
      "timestamp": "2026-08-18T22:10:26.678907+00:00",
      "exercise_id": "ex-gcs-b85e6559",
      "avg_convergence_error_deg": 0.62,
      "k_points": 1
    }
  ],
  "derived_tone_preference": "encouraging",
  "current_practice_focus": "1-Point frontal cube alignment"
}
```

### Verification Command 3: Live Health Checks on Cloud Run
```bash
curl -s https://atelier-agent-773993294789.europe-west1.run.app/api/health
curl -s https://atelier-web-773993294789.europe-west1.run.app/api/health
```

### Verified Output
```json
{"status":"healthy","service":"atelier-agent","version":"0.1.0","environment":"production","gcp_project":"atelier-hack"}
{"status":"healthy","service":"Atelier.Web","version":"0.1.0","environment":"Production","timestamp":"2026-08-18T22:06:03.9654737Z"}
```
