# ADR-004 — Async-first ingestion

**Status:** Accepted · 2026-08-03

## Context
The category demands agents that operate "beyond standard chat loops" and "run
asynchronously in the background" (quoted from the hackathon requirements — the qualified-use
clause is read first and cited verbatim, a lesson inherited from a sibling project).

## Decision
The primary entry is a private GCS inbox per student: object finalize → Eventarc → Cloud Run
pipeline (geometry → critique → memory), with the critique waiting in the UI. A weekly Cloud
Scheduler job produces the progress digest. The UI upload is the second door, not the first.

## Consequences
- The background requirement is met by the main flow, not by a bolt-on.
- The live demo shows the pipeline firing in the GCP console, as the video rules require.
