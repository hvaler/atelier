# Video production rig

One job: make every duration in the film a measured quantity instead of a hope.

| File | What it is |
|---|---|
| `narration.md` | **The words. The only copy of them.** Headings carry the measured time windows; the blockquotes carry the script |
| `_narration.py` | The shared bits: the narration format, the MP3 frame walker, and the 2.5-second gap. Defined once so two scripts cannot disagree |
| `make_voiceover.py` | Synthesises one MP3 per segment with Google Cloud Text-to-Speech, times each one, and writes `subtitles.srt` from those measurements |
| `shot-list.md` | What is on screen, in order, with the app's **measured** response times and how long each of the nine clips has to be |
| `assemble.py --check` | **Before recording**: how long each clip must be. **After**: what you actually got, and where it falls short |
| `align.py` | **After editing**: finds where each voice segment really landed in the exported film, and retimes `subtitles.srt` against the film rather than the plan |
| `make_closing_card.py` | The final still, 1920×1080 |
| `make_not_an_exercise.py` | The page the vision gate refuses, so that shot is reproducible |

Generated, not edited by hand: `audio/*.mp3`, `subtitles.srt`, `closing-card.png`,
`not-an-exercise.png`. Gitignored because they are footage rather than source:
`takes/`, `*.mp4`, `subtitles.srt.planned`.

**The Spanish operational version** lives outside the repository, at
`nexus/dev/GUION_RODAJE_ATELIER.md`. It is the one to work from with the screen in front of you: OBS
canvas settings, the per-clip lengths, and the lessons a sibling project paid for in retakes.

---

## The path this expects

1. **Record** nine clips with OBS into `takes/`, silently. Clip 1 is the webcam; segments 3 to 8 go
   in one continuous pass, cut into clips afterwards.
2. **`assemble.py --check`** — clip by clip, needs versus has.
3. **Assemble in Clipchamp**: the ten MP3s in order with 2.5 s between them, each clip fitted to
   its voice. Export 1920×1080.
4. **`align.py <export>`** — measures the drift between where the subtitles expect each voice and
   where it is. `--write-srt` retimes them against the film.
5. **Import `subtitles.srt` last.**

`assemble.py` without `--check` does steps 3 and 4 itself, cropping 16:10 → 16:9 if a take needs it.
It exists as the alternative, not the plan.

---

## Running it

```bash
atelier-agent/.venv/Scripts/python -m pip install google-cloud-texttospeech Pillow
gcloud auth application-default login
gcloud services enable texttospeech.googleapis.com --project atelier-hack

GOOGLE_CLOUD_PROJECT=atelier-hack atelier-agent/.venv/Scripts/python demo/video/make_voiceover.py
atelier-agent/.venv/Scripts/python demo/video/make_closing_card.py
```

Neither dependency is in `atelier-agent/requirements.txt`, deliberately: they are editing tools and
have no business inside the deployed image.

`ffprobe` is optional. Lengths are computed from the MP3's own frame headers, which is exact;
ffprobe is only a cross-check, and a disagreement of more than a tenth of a second is printed rather
than averaged away. If you want the cross-check on Windows after `winget install Gyan.FFmpeg`, its
`bin` is under `%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_*\ffmpeg-*-full_build\bin`
and is not added to `PATH` for you.

---

## The order that works

1. **Warm the services and rehearse once.** `shot-list.md` opens with this. A cold container in the
   middle of a continuous take costs you the take.
2. **Capture the screen silently.** No narration, no retakes for stumbles — there is nothing to
   stumble over.
3. **Generate the voice.** It comes back with every segment's length measured.
4. **Align.** A page that loaded slowly now costs a trim rather than a retake.

Doing it in the other order — narrating live while clicking — is how you end up re-recording three
minutes because the app took sixteen seconds instead of twelve.

---

## Three things this rig gets right, because it got them wrong first

**The length was a guess and the guess was wrong.** A sibling project computed spoken length as file
size over an assumed bitrate, was wrong by a factor of two, and believed for a week that a
two-minute narration ran to four and a half. Here the frames are counted.

**The captions drifted from the voice.** Three copies of the same sentences — script, synthesiser
input, hand-typed SRT — is a guarantee that the captions eventually say something the voice does
not. Silently, and only visible to someone watching with the sound off, which on a judging panel is
most of them. `narration.md` is now the only copy.

**A renamed segment left its old audio behind.** `04-the-critique-and-what-guards-it.mp3` sat in
`audio/` next to `04-the-critique-and-its-guard.mp3`, indistinguishable in a file listing and one
drag away from being cut into the video. The script now deletes what no segment claims, and says
which file it removed.

And one it gets right on purpose: **`{{spoken|shown}}`**. The voice needs `Gen A.I. S.D.K.` to say
the letters; a reader needs `GenAI SDK`. One source, two renderings — the first version leaked the
synthesiser's spelling into the subtitles, which is the artefact meant for a human.

---

## Why Google's own speech API

Nothing in the hackathon rules restricts editing tools; the mandatory-stack requirement is about
what the product calls at runtime. But a project whose entire claim is that the measurement is never
guessed at has no reason to narrate itself with a vendor it does not otherwise use. If a judge asks
what the voice was, the answer should add to the story rather than need explaining.

The voice is `en-GB-Studio-B`. Studio voices read long-form prose with sentence rhythm instead of
the word-by-word cadence that makes a demo sound automated. There are four in English:
`en-GB-Studio-B`, `en-GB-Studio-C`, `en-US-Studio-O`, `en-US-Studio-Q`. Change `VOICE` to audition
the others; the timings will move, and the script will tell you by how much.
