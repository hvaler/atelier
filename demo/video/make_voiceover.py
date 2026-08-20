"""
Turns the narration into one audio file per segment, plus the subtitles, with Google Cloud
Text-to-Speech.

    atelier-agent/.venv/Scripts/python -m pip install google-cloud-texttospeech
    gcloud auth application-default login
    gcloud services enable texttospeech.googleapis.com --project atelier-hack
    python demo/video/make_voiceover.py

Writes `demo/video/audio/01-….mp3` … and `demo/video/subtitles.srt`, and prints each segment's
spoken length against the window its heading claims, so an overrun is visible before it is baked
into a video.

**One file per segment rather than one long take**, because that is what makes editing survivable:
if a screen recording runs three seconds long you nudge one clip instead of re-cutting a
three-minute waveform. It does not compromise the "unedited live execution" the rules reward —
that is about the screen capture, which stays continuous through segments 2 to 7.

**`narration.md` is the only copy of the words.** The headings there give the time windows, the
paragraphs give the caption breaks. Keeping the spoken text, the captions and the script's own
transcript in three places is a guarantee that the captions eventually say something the voice does
not, silently, and only visible to whoever watches with the sound off — which on a judging panel is
most of them.

**Subtitle timings come from the synthesised audio, not from an estimate.** Each segment is timed as
it is generated and its cues are laid out across that measured length in proportion to their word
counts.

**Lengths are measured by decoding the MP3's own frame headers**, which needs nothing installed and
cannot be wrong about the bitrate. `ffprobe` is used as a cross-check when it is on PATH, and a
disagreement over a tenth of a second is printed rather than swallowed. The older approach — bytes
divided by an assumed bitrate — was wrong by a factor of two in a sibling project and made a
narration look like it ran to four and a half minutes.

**Why Google's own speech API and not another.** Nothing in the rules restricts editing tools. But a
project whose whole claim is that the measurement is never guessed at has no reason to narrate
itself with a vendor it does not otherwise use. If a judge asks what the voice was, the answer
should add to the story rather than need explaining.

The voice is a Studio one: they read long-form prose with sentence rhythm instead of the
word-by-word cadence that makes a demo sound automated. Change VOICE below to audition others —
`en-GB-Studio-B`, `en-GB-Studio-C`, `en-US-Studio-O` and `en-US-Studio-Q` are the four that exist.
"""

import os
import re
import sys
from pathlib import Path

from _narration import (
    PAUSE_BETWEEN_SEGMENTS,
    SUBSTITUTION,
    ffprobe_duration,
    mp3_duration,
    parse_narration,
    shown,
    spoken,
    stamp,
)

try:
    from google.cloud import texttospeech
except ImportError:
    raise SystemExit("pip install google-cloud-texttospeech")

VOICE = "en-GB-Studio-B"
LANGUAGE = "en-GB"
SPEAKING_RATE = 0.95         # Under natural: this narration is dense with figures.

#: Longest caption before it is split. Two lines of roughly seventy characters is what fits a
#: 1080p frame without covering the thing being narrated.
CUE_CHARS = 150

#: Hard rule: four minutes, and only the first four are evaluated.
LIMIT_SECONDS = 240
#: Where to start complaining. Thinner than you would allow a live take, and deliberately so: this
#: narration is synthesised, so its length is a measured constant rather than a performance that
#: might run long. The video is cut to fit the audio, not the other way round. What the margin has
#: to absorb is a late edit to `narration.md`, not a slow reader.
COMFORT_SECONDS = 225

HERE = Path(__file__).parent
NARRATION = HERE / "narration.md"
OUT = HERE / "audio"
SRT = HERE / "subtitles.srt"

def cues(paragraphs):
    """
    Split paragraphs into caption-sized chunks, breaking at sentence ends.

    Cues come back with their `{{spoken|shown}}` markup intact, so the caller can render either
    side. The markup is masked before splitting for two reasons, both of which this got wrong
    first time round: `Gemini 3.5 Flash` inside a substitution looks like two sentences to a
    full-stop splitter and came out as "Gemini 3. 5 Flash", and a substitution that straddled a
    cue boundary put a raw `{{` in one caption and the matching `}}` in the next.
    """
    out = []
    for paragraph in paragraphs:
        spans = []

        def mask(match, spans=spans):
            spans.append(match.group(0))
            return f"@@{len(spans) - 1}@@"

        masked = SUBSTITUTION.sub(mask, paragraph)
        sentences = re.findall(r"[^.!?]+[.!?]+\s*|[^.!?]+$", masked)

        def restore(text, spans=spans):
            return re.sub(r"@@(\d+)@@", lambda m: spans[int(m.group(1))], text)

        buffer = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if buffer and len(buffer) + 1 + len(sentence) > CUE_CHARS:
                out.append(restore(buffer))
                buffer = sentence
            else:
                buffer = f"{buffer} {sentence}".strip()
        if buffer:
            out.append(restore(buffer))
    return out


def wrap(text: str, width: int = 72) -> str:
    """Two short lines read better on screen than one long one."""
    words, lines, line = text.split(), [], ""
    for word in words:
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    return "\n".join(lines)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        print("note: GOOGLE_CLOUD_PROJECT is unset; using whatever the default credentials point at.")

    segments = parse_narration(NARRATION)
    client = texttospeech.TextToSpeechClient()
    OUT.mkdir(exist_ok=True)

    # Rename a segment and its old mp3 stays behind, indistinguishable from a current one in a
    # file listing and one drag away from being cut into the video. Say what is being removed
    # rather than leaving it to be noticed.
    wanted = {f"{s['stem']}.mp3" for s in segments}
    for stale in sorted(p.name for p in OUT.glob("*.mp3") if p.name not in wanted):
        (OUT / stale).unlink()
        print(f"removed {stale}: no segment in narration.md claims it any more")

    voice = texttospeech.VoiceSelectionParams(language_code=LANGUAGE, name=VOICE)
    config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=SPEAKING_RATE)

    clock, blocks, overruns, disagreements = 0.0, [], [], []
    ffprobe_present = False
    print(f"voice {VOICE} at rate {SPEAKING_RATE}\n")
    print(f"{'segment':<34} {'words':>6} {'window':>8} {'spoken':>8}  {'lands at':>12}")
    print("-" * 74)

    for segment in segments:
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=spoken(segment["text"])),
            voice=voice, audio_config=config)
        path = OUT / f"{segment['stem']}.mp3"
        path.write_bytes(response.audio_content)

        length = mp3_duration(response.audio_content)
        probed = ffprobe_duration(path)
        ffprobe_present = ffprobe_present or probed is not None
        if probed is not None and abs(probed - length) > 0.1:
            disagreements.append((segment["stem"], length, probed))

        # Lay this segment's cues across its measured length, by share of words. Proportional
        # rather than equal: "Refused." is one word and should not hold the screen as long as a
        # twenty-word sentence.
        segment_cues = cues(segment["paragraphs"])
        # Timing follows the words the voice actually says; the caption shows the readable form.
        counts = [max(1, len(spoken(c).split())) for c in segment_cues]
        at = clock
        for cue, count in zip(segment_cues, counts):
            span = length * count / sum(counts)
            blocks.append((at, at + span, wrap(shown(cue))))
            at += span

        starts_at = clock
        clock += length + PAUSE_BETWEEN_SEGMENTS
        over = segment["budget"] > 0 and length > segment["budget"]
        if over:
            overruns.append(segment["title"])
        print(f"{segment['stem']:<34} {len(spoken(segment['text']).split()):>6} "
              f"{segment['budget']:>7}s {length:>7.1f}s  "
              f"{stamp(starts_at)[3:8]}–{stamp(starts_at + length)[3:8]}"
              f"{'  ← OVER' if over else ''}")

    SRT.write_text("".join(
        f"{i}\n{stamp(a)} --> {stamp(b)}\n{text}\n\n" for i, (a, b, text) in enumerate(blocks, 1)
    ), encoding="utf-8")

    clock -= PAUSE_BETWEEN_SEGMENTS      # no trailing pause after the last segment
    print("-" * 74)
    print(f"{'total, with pauses':<34} {'':>6} {LIMIT_SECONDS:>7}s {clock:>7.1f}s  "
          f"ends {stamp(clock)[3:8]}")
    print(f"\n{len(blocks)} cues written to {SRT.name}, timed against the audio above")
    print(f"and a {PAUSE_BETWEEN_SEGMENTS:.1f}-second gap between segments.")

    if probed is None:
        print("\nnote: ffprobe is not on PATH, so the lengths above are the MP3 frame count only.")
        print("      That is the exact figure, not an estimate — the cross-check is what is missing.")
    for stem, frames, probe in disagreements:
        print(f"\nDISAGREEMENT on {stem}: frames say {frames:.2f}s, ffprobe says {probe:.2f}s.")
        print("      Do not average them. Find out which is wrong before cutting to either.")

    if clock > LIMIT_SECONDS:
        print(f"\nOVER {LIMIT_SECONDS // 60} MINUTES. The rules evaluate only the first four.")
    elif clock > COMFORT_SECONDS:
        print(f"\nInside the limit but only by {LIMIT_SECONDS - clock:.0f}s. One long clip eats that.")
    if overruns:
        print("Trim in narration.md, not in the edit: " + ", ".join(overruns))
    unwritten = [s["title"] for s in segments if s["budget"] <= 0]
    if unwritten:
        print("\nHeadings still at 0:00 in narration.md. Paste the windows above into them, so the")
        print("next run can tell you what a new sentence broke: " + ", ".join(unwritten))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
