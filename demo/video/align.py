"""
Takes the film you exported from Clipchamp and finds where each voice segment actually landed.

    atelier-agent/.venv/Scripts/python demo/video/align.py path/to/atelier-demo.mp4
    atelier-agent/.venv/Scripts/python demo/video/align.py path/to/atelier-demo.mp4 --write-srt

Prints, for every segment, where the subtitles expect its voice to start and where it really
starts. With `--write-srt` it rewrites `subtitles.srt` against the film instead of against the
plan, and keeps a copy of the old one.

Needs `ffmpeg` on PATH. `numpy` comes with the agent's virtualenv already.

---

**Why this exists.** In a sibling project the clips were joined in an editor by hand and the voice
files dropped on top by eye. That works, and it is off by a few tenths of a second in places — which
nobody notices watching, and everybody notices reading, because the captions were timed against the
plan rather than against the film. Hand-typed timings are only ever right for the take they were
written against.

**It measures rather than assumes.** Each segment's MP3 is cross-correlated against the film's own
audio track, normalised, so a difference in export level changes nothing. The search for segment
*n + 1* starts where segment *n* ended, which makes it both fast and impossible to match a segment
to the wrong repetition of a similar phrase.

**It refuses rather than guesses.** A segment whose best match is weak is reported as not found, and
`--write-srt` then declines to write anything at all. A subtitle file that is confidently wrong
about half the film is worse than one that is honestly stale — you can see a stale one.

**It does not touch your video.** The film is the artefact; the captions adapt to it. Re-cutting the
edit to match a plan is the wrong way round, and `assemble.py` is there if you would rather build
the film from the clips in the first place.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from _narration import (
    PAUSE_BETWEEN_SEGMENTS,
    mp3_duration,
    parse_narration,
    shown,
    spoken,
    stamp,
)
from make_voiceover import CUE_CHARS, cues, wrap  # noqa: F401  (CUE_CHARS via cues)

HERE = Path(__file__).parent
AUDIO = HERE / "audio"
SRT = HERE / "subtitles.srt"

#: Correlating at 8 kHz mono is plenty to locate speech to within a few milliseconds and keeps the
#: whole film comfortably in memory. Higher rates cost time and find the same peak.
RATE = 8000

#: Below this normalised correlation the match is not believed. Speech against the same speech at a
#: different level scores near 1.0; the wrong place in a film of the same voice scores well under
#: half that, so this leaves a wide margin either side.
MIN_SCORE = 0.45

#: How far past the previous segment's end to keep looking. Generous: an editor may have left a long
#: pause, and a false match cannot happen behind us because we never search backwards.
SEARCH_AHEAD = 90.0


def decode(path: Path, extra: list[str] | None = None) -> np.ndarray:
    """One channel of float32 PCM at RATE, straight out of ffmpeg."""
    args = ["ffmpeg", "-v", "error", "-i", str(path), *(extra or []),
            "-map", "0:a:0", "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"]
    out = subprocess.run(args, capture_output=True, check=False)
    if out.returncode != 0 or not out.stdout:
        sys.stderr.write(out.stderr.decode("utf-8", "replace")[-2000:] + "\n")
        raise SystemExit(f"ffmpeg could not decode an audio track from {path.name}")
    return np.frombuffer(out.stdout, dtype=np.float32).astype(np.float64)


def locate(film: np.ndarray, needle: np.ndarray, start: int, ahead: int) -> tuple[int, float]:
    """
    Where in `film` the `needle` sits, and how much to believe it.

    Normalised cross-correlation, computed through an FFT and divided by the sliding energy of the
    film window, so the score is comparable between segments and immune to export level. Returns
    the sample offset and that score.
    """
    end = min(len(film), start + ahead + len(needle))
    window = film[start:end]
    if len(window) < len(needle):
        return start, 0.0

    n = 1 << int(np.ceil(np.log2(len(window) + len(needle))))
    corr = np.fft.irfft(np.fft.rfft(window, n) * np.conj(np.fft.rfft(needle, n)), n)
    corr = corr[:len(window) - len(needle) + 1]

    # Sliding sum of squares of the film, so each lag is normalised by its own window's energy.
    squared = np.concatenate(([0.0], np.cumsum(window * window)))
    energy = squared[len(needle):] - squared[:len(window) - len(needle) + 1]
    denom = np.sqrt(np.maximum(energy, 1e-12) * float(needle @ needle))
    score = corr / denom

    best = int(np.argmax(score))
    return start + best, float(score[best])


def write_srt(segments, offsets, lengths) -> None:
    """The same cue layout make_voiceover.py writes, over the offsets measured from the film."""
    blocks = []
    for segment, offset, length in zip(segments, offsets, lengths):
        segment_cues = cues(segment["paragraphs"])
        counts = [max(1, len(spoken(c).split())) for c in segment_cues]
        at = offset
        for cue, count in zip(segment_cues, counts):
            span = length * count / sum(counts)
            blocks.append((at, at + span, wrap(shown(cue))))
            at += span

    if SRT.exists():
        backup = SRT.with_suffix(".srt.planned")
        backup.write_text(SRT.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"kept the previous file as {backup.name}")

    SRT.write_text("".join(
        f"{i}\n{stamp(a)} --> {stamp(b)}\n{text}\n\n" for i, (a, b, text) in enumerate(blocks, 1)
    ), encoding="utf-8")
    print(f"wrote {SRT.name}: {len(blocks)} cues, timed against the film")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("film", help="the exported video, or any file with the voice in its audio track")
    ap.add_argument("--write-srt", action="store_true",
                    help="rewrite subtitles.srt against the film")
    args = ap.parse_args()

    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is not on PATH.")
    film_path = Path(args.film)
    if not film_path.exists():
        raise SystemExit(f"{film_path} does not exist.")

    segments = parse_narration(HERE / "narration.md")
    needles, lengths = [], []
    for segment in segments:
        mp3 = AUDIO / f"{segment['stem']}.mp3"
        if not mp3.exists():
            raise SystemExit(f"missing {mp3.name}. Run make_voiceover.py first.")
        needles.append(decode(mp3))
        lengths.append(mp3_duration(mp3.read_bytes()))

    film = decode(film_path)
    print(f"film: {len(film) / RATE:.1f}s of audio, {len(segments)} segments to place\n")

    # What the shipped subtitles currently assume.
    planned, clock = [], 0.0
    for length in lengths:
        planned.append(clock)
        clock += length + PAUSE_BETWEEN_SEGMENTS

    print(f"{'segment':<34} {'planned':>9} {'measured':>9} {'drift':>8} {'score':>7}")
    print("-" * 72)

    measured, cursor, weak = [], 0, []
    for segment, needle, length, expected in zip(segments, needles, lengths, planned):
        at, score = locate(film, needle, cursor, int(SEARCH_AHEAD * RATE))
        seconds = at / RATE
        measured.append(seconds)
        drift = seconds - expected
        flag = "" if score >= MIN_SCORE else "  ← NOT FOUND"
        if score < MIN_SCORE:
            weak.append(segment["stem"])
        print(f"{segment['stem']:<34} {stamp(expected)[3:11]:>9} {stamp(seconds)[3:11]:>9} "
              f"{drift:>+7.2f}s {score:>7.2f}{flag}")
        cursor = at + len(needle)

    print("-" * 72)
    worst = max(abs(m - p) for m, p in zip(measured, planned))
    print(f"largest drift: {worst:.2f}s")

    if weak:
        print(f"\nNot found in the film: {', '.join(weak)}.")
        print("Either that segment is not in this export, or its audio was replaced. Nothing was")
        print("written — a subtitle file that is confidently wrong is worse than one that is stale.")
        return 1

    if worst < 0.15:
        print("Inside a frame and a half at 30 fps. The shipped subtitles already fit; nothing to do.")
        if not args.write_srt:
            return 0

    if not args.write_srt:
        print("\nRe-run with --write-srt to retime subtitles.srt against these measurements.")
        return 0

    write_srt(segments, measured, lengths)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
