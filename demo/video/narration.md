# Narration — Atelier

Written to be read by a synthetic voice, so it avoids what trips one up: no parentheses, no
em-dashes mid-clause, no numbers a voice would read wrongly. Every figure is spelled the way it
should be said.

**This file is the source.** `make_voiceover.py` reads it to synthesise the audio and to write
`subtitles.srt`, so the words spoken, the words captioned and the words here cannot drift apart.

**The headings are measured, not planned.** Each one is where that segment's voice actually starts
and ends, read back from the generated audio with a two and a half second gap between segments.
Ends are rounded up to the whole second, so a window never reads as an overrun against the very
recording it was taken from. Change a sentence and the script tells you which window it broke,
before you record rather than after.

**Total: 3:41**, nineteen seconds inside the four-minute limit — plus a five-second closing card,
which makes the film 3:46.

**This went through two rounds of cutting.** The first draft ran to 6:23 against a four-minute
limit, the second to 4:27. Both were true; neither fitted. What survived is what a judge cannot get
from the README: the six degrees injected coming back as six, the refusal, and the admission that
the conic engine is the weakest of the three. Everything else is in the repository, where a judge
scoring from the repo will find it.

**`{{spoken|shown}}` writes two things at once.** The voice reads the left half, the captions show
the right. `Gen A.I. S.D.K.` with stops is what makes the voice spell the letters out; `GenAI SDK`
is what a person should have to read. Before this existed the subtitles said *"Gen A. I. S. D. K."*,
which is the spelling meant for a synthesiser leaking into the artefact meant for a human.

**No Spanish in the spoken text, on purpose.** The subject is Spanish — *sistemas de
representación*, *diédrico*, *línea de tierra* — and an English synthetic voice mangles all three.
The interface on screen carries the Spanish; the voice says the English. The one exception is
*Monge*, which the voice handles, and which the method is named after.

**Segment 1 is on camera and segment 2 is on screen**, which is why one beat is written as two.
The cut between them is a source change, and a source change deserves its own clip rather than an
OBS scene switch in the middle of a take. Segment 2 exists to put the *evidence* on screen while the
claim is being made: `docs/PEDAGOGY.md`, its fourteen-row table of public criteria with their
sources, and §7 with the sentence in bold. The architecture diagram is deliberately **not** here —
see `shot-list.md`.

**The stack is named twice**, in segment 1 and again in segment 9. That is not redundancy: the
organisers' checklist asks the video for *"clear identification of which Gemini model and agent
framework used"*, and segment 1 is the part most likely to be trimmed for time.

**Recording order that works**: capture the screen silently first, generate the voice second,
align third. A slow page then costs you a trim, not a retake. `shot-list.md` has the measured
waits, so you know how long the dead air is before you hit record.

---

## 0:00 – 0:17 · The gap, on paper

> Atelier is an agent built on {{Gemini three point five Flash|Gemini 3.5 Flash}}, called through the
> {{Google Gen A.I. S.D.K.|Google GenAI SDK}}.
>
> Descriptive geometry is a first year subject in architecture and engineering. Correctness in it is
> objective. An isometric axis is at {{thirty degrees|30°}} or it is not.

## 0:19 – 0:36 · The finding

> I read eighteen published syllabi and rubrics. Not one states a tolerance. The discipline defines
> correctness exactly, then hands the checking to a person with a set square at the end of a stack
> of plates.
>
> Atelier automates that check. It does not invent a new criterion.

## 0:37 – 0:52 · Choose

> Three steps. Drawing, context, critique.
>
> Every sample carries the system it belongs to. Conic, axonometric, orthographic. Each is measured
> against a completely different reference.
>
> An isometric cube whose X axis was set six degrees wrong.

## 0:54 – 1:25 · The measurement

> X should be {{thirty degrees|30°}}. Measured, {{thirty six|36°}}. Systematic deviation, {{plus six point zero|+6.0°}}. Y
> and Z at zero.
>
> Injected at exactly six degrees, and it comes back at exactly six. Nothing is guessed. The axes
> of an isometric projection are {{thirty, ninety and one hundred and fifty|30°, 90° and 150°}} by
> definition.
>
> And separating those two numbers says what a published rubric cannot. A whole family off by the
> same amount is a set square placed wrong, not an unsteady hand. One correction before drawing,
> instead of edge by edge.

## 1:27 – 1:48 · The critique and its guard

> Plane A carries only numbers OpenCV produced. A validator asks the analysis what it measured and
> rejects any figure the model did not get from that set. Plane B is forbidden a number at all, in
> either language.
>
> Validated, with the model version underneath. That badge is earned per critique. When no model
> answers, the panel turns amber and says so.

## 1:50 – 2:11 · The refusal

> A shopping list, uploaded by mistake. Gemini looks at the page before anything is measured, and
> declines in its own words.
>
> Without this gate the page goes through RANSAC, finds a vanishing point among whatever edges
> exist, and spends real tokens describing nothing. Measuring the wrong thing carefully is worse
> than declining to measure it.

## 2:13 – 2:49 · Three systems, three references

> Conic. The reference is inferred. RANSAC estimates the vanishing point from the student's own
> lines.
>
> Orthographic, the Monge method. Here the reference is read off the page, because the ground line
> is a line the student drew. This plan sits {{eighteen pixels|18 px}} sideways. One placement mistake every
> vertex inherits, not four broken corners.
>
> The three are not equal, and the first is the weakest. A drifted drawing produces vanishing points
> that agree with it, so the reported error shrinks. One plate here has {{six degrees|6°}} of drift injected
> and scores better than the perfect one. Axonometry cannot: its axes are constants.

## 2:51 – 2:59 · History and level

> A figure that was not measurable renders as a dash, never a zero. And the profile is a difficulty
> level, not a person.

## 3:01 – 3:23 · Google Cloud, live

> Two Cloud Run services, and these are the requests the run you just watched made.
>
> A private Cloud Storage inbox with an Eventarc trigger. Cloud Scheduler for the weekly digest.
> Firestore, append only, where all of the state lives.
>
> And {{Gemini three point five Flash|Gemini 3.5 Flash}} on {{Vertex A.I.|Vertex AI}}, every call
> made through the {{Google Gen A.I. S.D.K.|Google GenAI SDK}}. In
> {{europe west three|europe-west3}}, deliberately not the Cloud Run region.

## 3:25 – 3:41 · Close

> {{Apache two point zero|Apache 2.0}}. One hundred automated tests. The golden case asserts that a
> {{six degree|6°}} error comes back as {{six degrees|6°}} to within
> {{five hundredths of a degree|0.05°}}, and the perspective suite cannot hold a bound that tight. We state the difference instead of hiding it.
