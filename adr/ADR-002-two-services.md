# ADR-002 — Two services with a clean boundary

**Status:** Accepted · 2026-08-03

## Context
OpenCV is native to Python; the author's UI velocity is .NET/Blazor. The hackathon mandates a
Google Agent Framework.

## Decision
`atelier-agent`: Python + Google ADK on Cloud Run, owning orchestration and all tools
(analyze_geometry, critique via Vertex AI, memory over Firestore, classify via Gemma).
`Atelier.Web`: Blazor Server (.NET 10) UI. The boundary is HTTP; the UI holds no domain
logic.

## Consequences
- Each language does what it is best at; the agent layer satisfies the ADK requirement
  end-to-end.
- The UI is replaceable without touching the agent.
