# ADR-006 — Privacy

**Status:** Accepted · 2026-08-03 · **amended 2026-08-21**

## Context
Drawings, and possibly the likeness of whoever made them, may appear in a public demo.

## Decision
Images live in a private bucket behind signed URLs; any drawing or on-camera appearance requires
the explicit consent of the person who made it. The public demo dataset consists of drawings shared
with permission plus drawings generated with deliberate, known errors.

## Consequences
- The public repository and the video contain nothing whose author did not agree to share it.

---

## Amendment — 2026-08-21: profiles are levels, and the demo has no accounts

Two things in the decision above no longer describe the system, and one thing it never said needs
saying.

**Profiles no longer carry names of any kind.** The original wording was *"profiles carry first
names only"*, which was the weaker of two possible designs and has been replaced by the stronger
one: a profile is a **difficulty level** — `level-basic` or `level-advanced` — and nothing anywhere
interpolates a person into anything. There is no field to leak because there is no field. The
critique header used to render a stored display name and no longer does.

**The deployed demo has no authentication, and this ADR did not say so.** `CurrentStudentId` is one
of two compile-time constants. Everyone who opens the public URL reads and writes the same two
profiles, so:

- An exercise uploaded by one visitor is counted in the history that the next visitor sees.
- What the history panel shows is the date, the projection system, one measured figure and the
  headline of the critique. **It does not re-display the uploaded image**, so a drawing is not
  served back to anybody.
- The exercise records in Firestore do hold the analysis and the critique. They do not hold a name,
  an email, an IP or any other identifier, because none is ever collected.

That is an acceptable position for a public demonstration whose data is technical drawings and
their measurements. It is **not** an acceptable position for a product with real students, and
saying so here is the point of this amendment: the absence of accounts is a deliberate scope
decision for the demo, not an oversight that happens to be harmless.

**What real accounts would require**, recorded so the gap is a known one rather than a surprise:

- Identity — the cheapest correct answer is Google Sign-In through Firebase Authentication, which
  is one more Google Cloud service and no new secret to hold.
- Firestore security rules keyed on the authenticated uid, so a student's subcollection is readable
  only by that student. Today the agent's service account reads everything, because there is nothing
  to separate.
- A migration for the existing shared history, which belongs to nobody in particular.
- A decision about what an instructor may see, which is a pedagogical question rather than a
  technical one and is the reason this is not simply "add auth".

None of that is in scope before the submission deadline. The demo is a demo, and the honest thing is
for the ADR to say which one it is.
