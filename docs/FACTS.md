# Facts

Measured on **2026-08-26** against commit `cfa62f4`. Nothing here is quoted from another document.
Every row was produced by running something or by reading the file named beside it.

This file exists to be checked, not believed. Where a claim could not be verified, the row says so
instead of softening it.

---

## 1. The test suites, counted

```bash
cd atelier-agent && .venv/Scripts/python -m pytest tests -rs -q
dotnet test Atelier.slnx
```

| Suite | File | Tests |
|---|---|---:|
| Axonometric geometry | `atelier-agent/tests/test_axonometry.py` | 23 |
| Orthographic (Monge) geometry | `atelier-agent/tests/test_dihedral.py` | 20 |
| Pre-router | `atelier-agent/tests/test_pre_router.py` | 11 |
| Localisation | `atelier-agent/tests/test_localisation.py` | 11 |
| Conic geometry | `atelier-agent/tests/test_geometry.py` | 9 |
| Async ingestion and digest | `atelier-agent/tests/test_async_digest.py` | 8 |
| Memory and the four verbs | `atelier-agent/tests/test_memory_collaborative.py` | 6 |
| Critique and validator | `atelier-agent/tests/test_critique.py` | 12 |
| Health | `atelier-agent/tests/test_health.py` | 2 |
| **Python total** | | **102** |
| Typed agent client | `Atelier.Web.Tests/AgentClientTests.cs` | 8 |
| **.NET total** | | **8** |
| **Total** | | **110** |

**Skipped: zero.** Run with `-rs`, which prints a reason for every skip; the run printed none.
`102 passed, 1 warning in 222.87s`. The warning is a Starlette deprecation notice from
`fastapi.testclient`, not a failure. Six of those tests were added on 2026-08-26 to close gaps
this file had found — §3.1 and §3.2.

**These suites are verified on Linux, not only on Windows.** `.github/workflows/ci.yml` runs both
jobs on `ubuntu-latest` — `dotnet test` and `pytest` — on every push. The last run passed.

---

## 2. Every capability the README claims

| Claim | Implementation | Test | Verified |
|---|---|---|:---:|
| ASK — clarifying questions before critique | `tools/collaborative.py:76` `ask_clarification`, endpoint `main.py:219` | `test_memory_collaborative.py:89` | **yes** |
| GUIDE — exercise from the recurring deviation | `tools/collaborative.py:100` `guide_next_exercise`, endpoint `main.py:225` | `test_memory_collaborative.py:160` | **yes** |
| CAPTURE — feedback as an immutable event | `tools/collaborative.py:106` `capture_feedback`, endpoint `main.py:257` | `test_memory_collaborative.py:170` | **yes** |
| ADAPT — tone derived from the event stream | `tools/collaborative.py:124` `adapt_profile`, endpoint `main.py:271` | `test_memory_collaborative.py:105` | **yes** |
| Anti-hallucination validator | `tools/validator.py:34` `validate_critique_measurements` | `test_critique.py` (6 tests) | **yes, with three holes — §3.2** |
| Validator retry loop | `tools/critique.py:335-341`, `max_retries = 2` (three attempts) | `test_critique.py` | **yes** |
| Gemma pre-router | `tools/pre_router.py:155` `route_from_intent`, model `gemma-4-26b-a4b-it` (`config.py:42`), endpoint `main.py:334` | `test_pre_router.py` (11 tests) | **yes — but see §3.3** |
| Gemini vision gate | `tools/pre_router.py:305` `classify_drawing`, model `gemini-3.5-flash` (`config.py:16`), endpoint `main.py:343` | `test_pre_router.py` | **yes** |
| GCS inbox with Eventarc | `tools/async_ingest.py:60` `process_gcs_upload_event`, endpoint `main.py:295` | `test_async_digest.py:133`, `:204` | **yes** — trigger `gcs-inbox-trigger` deployed, targets `atelier-agent /api/async/gcs-upload` |
| Weekly digest by Cloud Scheduler | `main.py:304`, job `weekly-digest-job` | `test_async_digest.py:162`, `:223` | **yes, since 2026-08-26** — it failed every Monday before that. §3.4 |
| Progress curve | `Atelier.Web/Components/Shared/ProgressChart.razor` | `AgentClientTests.cs` `GetDerivedProfileAsync_MapsTheProgressionCurve` | partial — the client mapping is tested, the rendering is not |
| Interactive overlay | `tools/geometry.py:407` overlay encoder, viewer components under `Atelier.Web/Components/Shared/` | none | **no automated test** |
| A figure that is not measurable renders as a dash | `ProgressChart.razor:18`, `DihedralViewer.razor:81-83`, `ExerciseHistory.razor:49` | none | **yes by reading** — `is double x ? … : "—"` |

---

## 3. What does not work, or is not proven

### 3.1 If Vertex AI does not answer

Three different failures, three different screens. They are not interchangeable.

| Situation | Where | What the student sees |
|---|---|---|
| The gate refuses the page | `Home.razor:452` | Amber panel, *"This does not look like a perspective exercise."* Nothing measured |
| Gemini fails, OpenCV succeeded | `critique.py:355-361`, badge `TwoPlaneCritique.razor:37` | Measurements and overlay render; amber pill *"Deterministic fallback — no model answered"*, `source=fallback`, `validated=false` |
| The agent is unreachable | `Home.razor:462` | **Red** panel, *"Nothing is shown rather than something invented."* No figures at all |

Invalid JSON from the model is handled by the same retry as a validation failure: three attempts,
then the deterministic template.

**A server error is now covered too.** `test_critique.py` `test_a_server_error_from_vertex_serves_the_template_and_says_so` raises from `genai.Client` and
asserts what the student gets: `source=fallback`, `model_version=deterministic-template`, the
geometry still present, `cached=False`, `validation_retries=3`. It patches at the SDK boundary
on purpose — replacing `call_vertex_ai_critique` would delete the handler the test exists to pin.

### 3.2 The validator can be fooled, in three ways

Read from `tools/validator.py`. This is the mechanism the README leans on hardest, so it is worth
being exact about what it does not do.

1. **It checks values, never what they are predicated of.** `validator.py:67` asks whether the
   cited number is close to *any* measured number. A critique that reports a correct 6.0° against
   the wrong edge, or calls a horizon tilt an axis error, passes.
2. **The tolerance is ±0.5 by default, not exact** (`validator.py:43`). Any invented figure that
   lands within half a degree of any measured value is accepted, and with ten or so values on the
   whitelist that is a wide target. **It is now an operator setting**: `VALIDATOR_TOLERANCE_DEG`
   (`config.py`), passed at the one production call site (`critique.py:346`). `0.0` demands an
   exact match. The default stays 0.5 because the model rounds and phrases; a deployment that
   wants a stricter gate no longer needs a code change. Three tests pin it, including one that
   asserts the configured value is the one production actually passes — a setting nothing reads
   is decoration.
3. ~~**Plane B only blocks degrees.**~~ **Fixed 2026-08-26.** The regex — now
   `_MEASUREMENT_IN_PROSE` — also matches `px`, `pixel`, `pixels`, `píxel`, `píxeles`, which
   matters because the orthographic system reports its error in pixels. Two tests pin it:
   one rejects *"the plan sits about 18 px to the left"*, and one checks the gate did not
   become so wide that prose without figures is blocked.

**A fourth hole, found while writing the test for the third — and fixed on 2026-08-26.** The
three deterministic fallbacks disagreed. The conic one returned `validated=True`; the
orthographic and axonometric ones returned `False`. No validator passes any of the three, and
the field's own definition is *"whether the critique passed all anti-hallucination validation
gates"* (`models/critique.py:97`, default `False`). All three now return `False`.

**Three existing tests failed when it was fixed, and that is the interesting part.** They
asserted `critique.validated is True` while running without Vertex credentials — so they always
took the fallback path, and what they pinned was the bug. They now assert the invariant that
holds either way: `validated is (source == "vertex")`. The comment at `critique.py:235`
describes an earlier version of this same fault as *"deleting Vertex AI from the project would
have changed nothing anyone could observe"*. These tests were part of why nobody observed it.

**And the disk cache keeps entries from older code.** `.cache/critiques/` still holds critiques
stamped `source=fallback` with `validated=True` from before the provenance work. Nothing
invalidates them on a code change, so a cached answer can be older than the rules that produced
it. The directory is gitignored, so this is a local-machine effect, not something shipped.

### 3.3 The Gemma pre-router is on the interactive path only

It is genuinely called — this is not an endpoint that exists for the README:
`Atelier.Web/Components/Pages/Home.razor:389` calls `RouteIntentAsync`
(`AtelierAgentClient.cs:248`), which posts to `/api/router/classify`.

**But the autonomous path never reaches it.** `async_ingest.py:82` calls `classify_drawing` — the
*Gemini vision gate* — and nothing else. A drawing dropped into the GCS inbox is routed by
`gate.recommended_k`, falling back to the profile level (`async_ingest.py:88`). Gemma reads the
student's words, and on that path there are no words.

### 3.4 The weekly digest failed every Monday until 2026-08-26

The centrepiece of the asynchronous story, and it was broken in production the whole time. What
followed is recorded here because the fault is more instructive than the fix.

```
$ gcloud scheduler jobs describe weekly-digest-job --location europe-west1
state          ENABLED
schedule       0 9 * * 1  (UTC)
lastAttemptTime 2026-08-24T09:00:00.850625Z
status         {"code": 9}          # FAILED_PRECONDITION
uri            .../api/digest/weekly
body (base64)  e1wic3R1ZGVudF9pZFwiOlwieW91bmctdGVzdGVyLTAxXCJ9
```

That body decodes to `{\"student_id\":\"young-tester-01\"}` — with literal backslashes. It is not
valid JSON, `WeeklyDigestRequest.student_id` is required (`models/digest.py:47`), and FastAPI
rejects it. The job has been firing every Monday and failing every Monday.

**And the reproduction script would have recreated it.** `infra/setup.sh:169` created the job with
`--http-method=POST` and **no `--message-body` at all**, which fails the same validation for the
same reason. The deployed job and the script disagreed, and both were wrong. The script now sends
the body too.

**A second fault underneath the first.** Even with a valid body the job would have returned 404: it named `young-tester-01`, and that profile does not exist on the deployed service. `GET /api/students` returns exactly two, `level-basic` and `level-advanced` — difficulty levels rather than people, which is the profile model the project describes.

**Fixed on 2026-08-26, and verified rather than assumed:**

```
$ gcloud scheduler jobs update http weekly-digest-job \
    --message-body='{"student_id":"level-basic"}'
$ gcloud scheduler jobs run weekly-digest-job

lastAttemptTime  2026-08-26T20:32:36Z
status           (empty — was {"code": 9})

$ curl .../api/students/level-basic/digests
2026-W35 | total_drawings=23 | created_at=2026-08-26T20:32:38Z
```

The digest appeared two seconds after the job fired, with 23 drawings, a weekly average convergence error of 5.51° and a reduction of 5.16°. `infra/setup.sh:169` now creates the job with the same body, so a fresh project does not inherit the fault.

**Still wrong in the README**: it says the digest arrives on **Sunday**. The cron is `0 9 * * 1` — **Monday**. That is a documentation fix, not a code one.

**Still unproven**: the job has now succeeded when triggered by hand. It has not yet completed a scheduled Monday fire. The next one is **2026-08-31 09:00 UTC**.

### 3.5 What is not verified on Linux

CI covers both test suites on `ubuntu-latest`. It does not follow the Quickstart, so the
Quickstart was run separately, verbatim, in two clean containers on **2026-08-26**.

`python:3.12-slim` — steps 1 to 4 as written, using the documented Linux paths:

```
Python 3.12.14 · git 2.47.3
step 2: python -m venv .venv && pip install -r requirements.txt   OK
step 3: atelier-agent/.venv/bin/python demo/generate_calibration_dataset.py
        [OK] Calibration dataset generated at: demo/dataset   -> 11 plates
step 4: /api/health -> 200 {'status':'healthy', ..., 'memory_backend':'memory'}
```

`mcr.microsoft.com/dotnet/sdk:10.0` — `dotnet build -c Release` **0 warnings, 0 errors**, and
`dotnet test` **8 passed, 0 skipped**.

Eleven plates is what the README claims, and `memory_backend: memory` is what it says step 4
should report. Both matched. `git` had to be installed in each image, and the prerequisites
already list it.

**Still not covered**: step 5, `dotnet run` of the Blazor app, and the browser flow. A container
can build it; nobody has clicked through it on a machine that never had the repository.

### 3.6 How many people's drawings

**One.** Everything committed under `demo/dataset/` and `Atelier.Web/wwwroot/samples/` is
synthetic, generated by `demo/generate_calibration_dataset.py` — eleven plates. Beyond that, the
system has been exercised on drawings from a single 9-year-old beginner, and none of those are in
the repository. Handwriting, paper, lighting and camera angle have not been sampled across people.

---

## 4. What the video claims, measured

Reproduce with `analyze_geometry` over `demo/dataset/`:

```python
from src.tools.geometry import analyze_geometry
analyze_geometry(cv2.imread("../demo/dataset/04_2point_perfect.png"), k_points=2,
                 generate_overlay_flag=False)
```

| Video claim | Measured | Verdict |
|---|---|---|
| A plate with 6° injected scores better than the clean one | `04_2point_perfect` avg **0.480°** / max **1.590°**; `05_2point_error_6deg` avg **0.420°** / max **0.970°** | **true** — lower on both |
| …because the vanishing points agree with the drift | Horizon tilt moves **−0.51° → +2.08°** while convergence error falls. The fit follows the drift; the tilt is the signal that survives | **true** |
| The conic system is the weakest | **Only the two-point fit.** One-point degrades correctly: `01` **0.820°**, `02` (4° injected) **1.360°**, `03` (9° injected) **4.470°** | **refined** — the claim is too broad as stated |
| Axonometry holds 6° ±0.05° and the perspective suite cannot | `test_axonometry.py:106` `test_injected_six_degrees_comes_back_as_six_degrees` asserts `pytest.approx(6.0, abs=0.05)` on the X axis and `0.0 ± 0.05` on Y and Z. No conic test asserts a bound near that | **true** |
| A figure that cannot be measured renders as a dash, never zero | `ProgressChart.razor:18`, `DihedralViewer.razor:81-83`, `ExerciseHistory.razor:49` | **true** |
| The gate declines to measure a shopping list | `classify_drawing` (`pre_router.py:305`) runs before any geometry; refusal surfaces at `Home.razor:452`; screenshot `docs/img/04-gate.png` | **true** |

---

## 5. Open, in one list

1. ~~`weekly-digest-job` fails every Monday~~ — **fixed 2026-08-26**, verified by a manual run that produced digest `2026-W35`. Two faults: a body with escaped quotes, and a `student_id` that no longer existed. A scheduled Monday fire has still not been observed.
2. The README says the digest arrives on **Sunday**; the cron says **Monday**.
3. The validator accepts a correct value attached to the wrong metric.
4. The validator's tolerance is ±0.5° by default, not exact — now settable with
   `VALIDATOR_TOLERANCE_DEG`, `0.0` for an exact match.
5. ~~Plane B blocks degrees but not pixels.~~ **Fixed 2026-08-26**, two tests.
6. ~~The conic fallback reports `validated=True`.~~ **Fixed 2026-08-26.** All three fallbacks now
   report `False`, and three tests that were pinning the fault were rewritten to assert
   `validated is (source == "vertex")`.
7. **The critique cache holds entries stamped by older code** and nothing invalidates them.
8. Gemma never runs on the autonomous path — a consequence of the design, not a defect.
9. The interactive overlay has no automated test.
10. ~~The Quickstart has not been run on a clean machine.~~ **Done 2026-08-26**, two containers,
    steps 1–4 and the .NET build. Step 5 and the browser flow are still unexercised.
11. Drawings from exactly one person, none of them in the repository.
12. ~~No test covers a 5xx from Vertex.~~ **Added 2026-08-26.**
