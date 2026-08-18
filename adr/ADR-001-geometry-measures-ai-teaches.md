# ADR-001 — The geometry measures, the AI teaches

**Status:** Accepted · 2026-08-03

## Context
A vision LLM asked to assess perspective produces plausible but unmeasurable prose, and may
hallucinate quantities. Judging criteria reward production-minded systems over brittle
LLM-only scripts.

## Decision
All quantitative claims about a drawing (vanishing points, horizon, convergence error in
degrees, confidence) come from a deterministic OpenCV tool, tested against drawings with
deliberately constructed errors of known magnitude. Gemini receives the image plus the
measurement payload and produces pedagogy only. A validator rejects any critique citing
numbers absent from the payload; low CV confidence yields an explicit "please retake the
photo" instead of invented geometry.

## Consequences
- Measurable, testable core; the LLM cannot fabricate metrics.
- Clear failure mode for bad photos (a judged architecture point, not a bug).
