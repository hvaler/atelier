# Social Media Posts for Atelier — All Things Agentic Hackathon (+0.2 bonus)

> Both posts must carry **#AllThingsAgenticHackathon** — the bonus is conditional on the hashtag.
> Post them before submitting, and keep the links: the Devpost form asks for them.

---

## 🐦 X / Twitter — under 280 characters

```text
Descriptive geometry is a subject where correctness is objective — an isometric axis is at 30° or
it isn't. I read 18 published syllabi. Not one states a tolerance.

Atelier measures it: OpenCV for ground truth, Gemini 3.5 Flash via the Google GenAI SDK for the
teaching.

https://github.com/hvaler/atelier

#AllThingsAgenticHackathon
```

*Alternative, if you would rather lead with the result:*

```text
I injected a 6° error into an isometric drawing. Atelier reported 6.00°, and said it was a set
square placed wrong rather than an unsteady hand.

OpenCV measures, Gemini 3.5 Flash (Google GenAI SDK, Vertex AI) teaches. Neither does the other's
job.

https://github.com/hvaler/atelier

#AllThingsAgenticHackathon
```

---

## 💼 LinkedIn

```text
My submission for the Google Devpost All Things Agentic Hackathon: Atelier — an agent that verifies
descriptive-geometry constructions.

Descriptive geometry (sistemas de representación) is a first-year subject in architecture,
engineering and animation degrees, and it has a property most drawing subjects do not: correctness
is objective. An isometric axis is at 30° or it is not. A point's plan sits under its elevation or
it does not.

So I read eighteen published syllabi and rubrics. Not one of them states a numerical tolerance. The
discipline defines correctness exactly, and then hands the checking to a person with a set square at
the end of a stack of plates. Meanwhile a general-purpose multimodal model asked to critique a
drawing will happily invent the number.

Atelier automates the verification the discipline already defines. It does not invent a new
criterion.

How it works:

1. A vision gate (Gemini 3.5 Flash on Vertex AI) answers two questions before anything is measured:
   is this an exercise at all, and which system of representation is it?
2. Three OpenCV engines, and the interesting part is that they are not one tool three times — they
   differ in where the reference comes from:
   • Conic: the vanishing point is INFERRED by RANSAC from the student's own lines. Weakest, and
     documented as such — a consistently wrong drawing yields a reference that agrees with it.
   • Orthographic (Monge): the ground line is READ OFF THE PAGE. A displaced plan is reported as one
     placement error that every vertex inherits, not four broken corners.
   • Axonometric: the axes are GIVEN by the projection system. Nothing is estimated, and an error
     injected at 6° comes back at 6.00°.
3. Gemma 4 reads the student's own description to infer which case they meant. When it disagrees
   with the measurement, Atelier reports the disagreement and changes nothing. The measurement is
   evidence; the description is a claim.
4. Every critique is split in two planes that may not mix: Plane A carries only figures OpenCV
   produced, Plane B is forbidden a number at all. A validator asks the analysis what it measured
   and rejects anything else — in English and in Spanish, because a gate that only recognises
   "degrees" stops being a gate the moment the interface is translated.
5. Cloud Storage + Eventarc ingest drawings with nobody at the keyboard; Cloud Scheduler sends a
   weekly digest; Firestore stores everything append-only.

The lesson I did not expect: the mean of an empty set is not zero. Twice, an average computed over
nothing was printed as 0.00 — which reads as perfect. A plate whose two views did not correspond at
all reported a correspondence error of zero. A worse drawing produced a better number. Both
aggregates are nullable now and render as a dash.

Built with the Google GenAI SDK, Gemini 3.5 Flash and Gemma 4, Cloud Run, Firestore, Cloud Storage,
Eventarc, Cloud Scheduler, OpenCV and .NET 10. Apache 2.0, 104 automated tests.

Repo, architecture and the pedagogy sources: https://github.com/hvaler/atelier

#AllThingsAgenticHackathon #GoogleCloud #VertexAI #Gemini #AgenticAI #OpenCV #Blazor #DotNet
```
