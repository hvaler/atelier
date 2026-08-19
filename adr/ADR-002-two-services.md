# ADR-002 — Two services with a clean boundary

**Status:** Accepted · 2026-08-03 · **Amended 2026-08-19** (see *Amendment*)

## Context
OpenCV is native to Python; the author's UI velocity is .NET/Blazor. The hackathon mandates a
Google Agent Framework.

## Decision
`atelier-agent`: Python on Cloud Run, owning orchestration and all tools (analyze_geometry,
critique via Vertex AI, memory, classification). `Atelier.Web`: Blazor Server (.NET 10) UI. The
boundary is HTTP; the UI holds no domain logic.

## Consequences
- Each language does what it is best at.
- The UI is replaceable without touching the agent.

## Amendment — 2026-08-19: the framework is the GenAI SDK, not ADK

This ADR originally read *"Python + Google ADK"*, and the Consequences claimed *"the agent layer
satisfies the ADK requirement end-to-end"*. **Neither was ever true.** `google-adk` has never been
a dependency of this project — it is absent from `atelier-agent/pyproject.toml` and
`requirements.txt`, and `google.adk` is imported nowhere.

What the project actually uses, and has used from the first commit, is the **Google GenAI SDK**
(`google-genai`), calling Gemini on Vertex AI at `atelier-agent/src/tools/critique.py`. The
hackathon's requirement names four acceptable frameworks — *ADK, GenAI SDK, Antigravity SDK or
GenKit* — so the requirement is met. It was simply met by a different one than this document
claimed.

The decision is left standing because the decision was right: two services, HTTP boundary, no
domain logic in the UI. Only the technology named in it was wrong. It is corrected here rather
than quietly overwritten, because an ADR that edits its own history is worth less than one that
records having been wrong.
