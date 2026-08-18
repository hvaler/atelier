# ADR-005 — Append-only memory; adaptation is derived, never edited

**Status:** Accepted · 2026-08-03

## Context
The Collaborative Partner category requires capturing feedback and adapting to the student.
Hand-edited "learning profiles" rot and cannot be audited.

## Decision
Every exercise, measurement, critique and feedback item is an immutable event. Tone
preference, recurring issues and focus areas are pure derivations over the event stream.
Multiple student profiles from day one.

## Consequences
- Adaptation is explainable: any behavior change traces to specific feedback events.
- The weekly digest is a fold over events — no extra bookkeeping.
