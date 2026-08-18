# ADR-003 — Firestore over Cloud SQL

**Status:** Accepted · 2026-08-03

## Context
The data is naturally hierarchical (students → exercises → analysis/critique/feedback →
digests), the project runs on spare time, and cost must approach zero when idle.

## Decision
Firestore (Native mode). No relational schema, no ORM version families to pin, no instance
to stop and start; scales to zero with the rest of the stack.

## Consequences
- Satisfies the mandated Google Cloud infrastructure requirement.
- Aggregations (progress curves) are computed by the digest job, not by queries.
