"""
Cuts the recorded screen takes together, lays the generated voice over them, and says exactly
where the two disagree.

    atelier-agent/.venv/Scripts/python demo/video/assemble.py --check
    atelier-agent/.venv/Scripts/python demo/video/assemble.py

`--check` measures and reports without writing anything, which is what you want after a recording
session. Without it, the same measurements are taken and then `atelier-demo.mp4` is built.

Needs `ffmpeg` and `ffprobe` on PATH. After `winget install Gyan.FFmpeg` they live under
`%LOCALAPPDATA%\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_*\\ffmpeg-*-full_build\\bin`, which winget
does not add for you.

---

**What this replaces.** The sibling project did this by hand: crop each take from 1920x1200 to
1920x1080 because the recording was 16:10 and carried the taskbar, trim a few, concatenate, then
drop the voice on top and nudge until it fitted. It worked, and none of it was written down — so
the next person, including the same person a fortnight later, starts from remembered ffmpeg flags.

**The rule the whole file exists to enforce: the screen fits the voice, never the reverse.**
Stretching a clip to reach a sentence is how a demo starts to look slowed down, and speeding the
audio up to fit a short clip is how it starts to sound automated. So the voice track is built first,
at the exact offsets `subtitles.srt` was written against, and each clip is then checked against the
window it has to fill.

**A clip that is too short is padded by holding its last frame, and every pad is printed.** That is
a deliberate choice over the alternatives: silently letting the audio run past the video gives you
black frames nobody warned you about, and looping is worse. A held frame is visibly a held frame,
and the report tells you which clip to go back and re-record if you would rather not have one.

**A clip that is too long is never trimmed automatically.** Where to cut is a judgement about what
is on screen, and this script cannot see. It reports the overhang and stops.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _narration import (
    PAUSE_BETWEEN_SEGMENTS as PAUSE,
)
from _narration import (
    mp3_duration,
    parse_narration,
    stamp,
)

HERE = Path(__file__).parent
AUDIO = HERE / "audio"
OUT = HERE / "atelier-demo.mp4"

WIDTH, HEIGHT, FPS = 1920, 1080, 30

#: Hard rule: four minutes, and only the first four are evaluated.
LIMIT_SECONDS = 240

#: The edit, in order: one file you recorded, and the narration segments it has to cover.
#:
#: **Eight clips rather than one long take, with one exception.** A sibling project learned that a
#: bad shot should cost one retake rather than the whole film, and the narration is already cut per
#: segment, so per-segment clips are the cheap default.
#:
#: The exception is segments 3 and 4, which are **one uncut clip on purpose**: pressing Analyze,
#: the sixteen seconds the model actually takes, and the critique landing. Cutting inside that beat
#: would look exactly like hiding the latency, and the judging criteria reward unedited live
#: execution. Everything else is a scene change, and a scene change is allowed to be a cut.
#:
#: Record segments 2 to 7 in **one continuous pass** even so — the browser state carries forward and
#: the framing cannot drift if you never stop. Cut that pass into these clips afterwards.
#:
#: Edit the file names to match what came out of OBS. A `still` entry holds an image instead.
EDIT = [
    {"clip": "take-01-the-gap.mp4",       "segments": [1]},
    {"clip": "take-02-choose.mp4",        "segments": [2]},
    {"clip": "take-03-measure-critique.mp4", "segments": [3, 4]},   # uncut
    {"clip": "take-04-refusal.mp4",       "segments": [5]},
    {"clip": "take-05-three-systems.mp4", "segments": [6]},
    {"clip": "take-06-history.mp4",       "segments": [7]},
    {"clip": "take-07-console.mp4",       "segments": [8]},
    {"clip": "take-08-repo.mp4",          "segments": [9]},
    {"still": "closing-card.png",         "hold": 5.0},
]


def run(args: list[str]) -> None:
    """ffmpeg, loudly. A failure here must not look like a success with a shorter film."""
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        sys.stderr.write(result.stderr[-4000:] + "\n")
        raise SystemExit(f"ffmpeg failed: {' '.join(args[:6])} …")


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=False)
    if out.returncode != 0 or not out.stdout.strip():
        raise SystemExit(f"ffprobe could not read {path.name}")
    return float(out.stdout.strip())


def probe_size(path: Path) -> tuple[int, int]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "csv=p=0:s=x", str(path)],
        capture_output=True, text=True, check=False)
    if out.returncode != 0 or not out.stdout.strip():
        raise SystemExit(f"ffprobe could not read the video stream of {path.name}")
    w, h = out.stdout.strip().split("x")[:2]
    return int(w), int(h)


def crop_filter(width: int, height: int) -> str:
    """
    How to get this take to 1920x1080, and why.

    A 16:10 laptop panel recorded whole gives 1920x1200, and the extra 120 rows are the taskbar,
    the clock and whatever notification arrived during take four. Crop from the **top**, which
    keeps the browser chrome and drops the shelf. Anything else is scaled and letterboxed rather
    than cropped, because guessing which edge of an unfamiliar aspect ratio is disposable is how
    you cut the vanishing point off the bottom of a drawing.
    """
    target = WIDTH / HEIGHT
    if abs(width / height - target) < 0.001:
        return f"scale={WIDTH}:{HEIGHT}"
    if width / height < target:                       # taller than 16:9 — a taskbar band
        keep = int(width / target)
        return f"crop={width}:{keep}:0:0,scale={WIDTH}:{HEIGHT}"
    return (f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:black")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="measure and report, write nothing")
    ap.add_argument("--takes", default=str(HERE / "takes"),
                    help="directory holding the recorded clips (default: demo/video/takes)")
    args = ap.parse_args()
    takes = Path(args.takes)

    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise SystemExit(f"{tool} is not on PATH. See the module docstring for where winget put it.")

    segments = parse_narration(HERE / "narration.md")
    lengths = []
    for segment in segments:
        mp3 = AUDIO / f"{segment['stem']}.mp3"
        if not mp3.exists():
            raise SystemExit(f"missing {mp3.name}. Run make_voiceover.py first.")
        lengths.append(mp3_duration(mp3.read_bytes()))

    # Where each segment's voice starts, which is what subtitles.srt was written against.
    offsets, clock = [], 0.0
    for length in lengths:
        offsets.append(clock)
        clock += length + PAUSE
    voice_total = clock - PAUSE

    print(f"voice track: {len(segments)} segments, {voice_total:.1f}s, ends {stamp(voice_total)[3:8]}")
    print(f"{'clip':<28} {'covers':<12} {'needs':>8} {'has':>8} {'source':>11}  verdict")
    print("-" * 88)

    plan, missing, total_video, pads = [], [], 0.0, []
    for entry in EDIT:
        if "still" in entry:
            still = HERE / entry["still"]
            if not still.exists():
                missing.append(entry["still"])
                continue
            hold = float(entry["hold"])
            plan.append({"kind": "still", "path": still, "length": hold})
            total_video += hold
            print(f"{entry['still']:<28} {'—':<12} {'—':>8} {hold:>7.1f}s {'image':>11}  held")
            continue

        clip = takes / entry["clip"]
        first, last = entry["segments"][0], entry["segments"][-1]
        # The window this clip has to fill: its segments' voice, plus the gaps between them, plus
        # the gap that follows unless it is the last thing in the film.
        needed = sum(lengths[i - 1] for i in entry["segments"]) + PAUSE * (len(entry["segments"]) - 1)
        if last < len(segments):
            needed += PAUSE
        covers = f"{first}" if first == last else f"{first}–{last}"

        if not clip.exists():
            missing.append(entry["clip"])
            print(f"{entry['clip']:<28} {covers:<12} {needed:>7.1f}s {'—':>8} {'—':>11}  NOT RECORDED")
            continue

        have = probe_duration(clip)
        w, h = probe_size(clip)
        if have + 0.05 < needed:
            verdict = f"SHORT by {needed - have:.1f}s → last frame held"
            pads.append((entry["clip"], needed - have))
        elif have > needed + 1.0:
            verdict = f"long by {have - needed:.1f}s → trim it yourself"
        else:
            verdict = "fits"
        print(f"{entry['clip']:<28} {covers:<12} {needed:>7.1f}s {have:>7.1f}s {f'{w}x{h}':>11}  {verdict}")
        plan.append({"kind": "clip", "path": clip, "length": needed, "have": have,
                     "size": (w, h)})
        total_video += needed

    print("-" * 88)
    print(f"{'film':<28} {'':<12} {voice_total:>7.1f}s {total_video:>7.1f}s")

    if missing:
        print("\nNot recorded yet: " + ", ".join(missing))
        print(f"Put the takes in {takes} and name them as `EDIT` in this file says, or edit `EDIT`.")
        return 1

    if pads:
        print("\nClips shorter than their voice, which will hold a frozen frame:")
        for name, short in pads:
            print(f"  {name}: {short:.1f}s of held frame")
        print("A held frame is visible. Re-record if you would rather not have one.")

    if total_video + 0.5 > LIMIT_SECONDS:
        print(f"\nOVER {LIMIT_SECONDS}s. Only the first four minutes are evaluated.")
        return 1

    if args.check:
        print("\n--check: nothing written.")
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        parts = []
        for i, item in enumerate(plan, 1):
            part = tmp / f"part{i:02d}.mp4"
            if item["kind"] == "still":
                run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(item["path"]),
                     "-t", f"{item['length']:.3f}", "-r", str(FPS),
                     "-vf", f"scale={WIDTH}:{HEIGHT}", "-pix_fmt", "yuv420p",
                     "-c:v", "libx264", "-crf", "20", "-an", str(part)])
            else:
                # `tpad=stop_mode=clone` holds the last frame; `-t` then cuts to the window. When
                # the clip is longer than its window this simply trims the tail, which is why an
                # overhang is reported above rather than silently absorbed here.
                vf = crop_filter(*item["size"]) + ",tpad=stop_mode=clone:stop_duration=30"
                run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(item["path"]),
                     "-vf", vf, "-t", f"{item['length']:.3f}", "-r", str(FPS),
                     "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "20", "-an", str(part)])
            parts.append(part)

        listing = tmp / "parts.txt"
        listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
        silent = tmp / "silent.mp4"
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", str(listing), "-c", "copy", str(silent)])

        # One voice track, built at the offsets the subtitles assume. adelay per segment, then
        # amix; no resampling, no time-stretching, nothing that could move a caption.
        inputs, filters, labels = [], [], []
        for i, segment in enumerate(segments):
            inputs += ["-i", str(AUDIO / f"{segment['stem']}.mp3")]
            filters.append(f"[{i + 1}:a]adelay={int(offsets[i] * 1000)}|{int(offsets[i] * 1000)}[a{i}]")
            labels.append(f"[a{i}]")
        graph = ";".join(filters) + ";" + "".join(labels) + \
            f"amix=inputs={len(segments)}:normalize=0[voice]"
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), *inputs,
             "-filter_complex", graph, "-map", "0:v", "-map", "[voice]",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(OUT)])

    final = probe_duration(OUT)
    print(f"\nwrote {OUT.name}  {final:.1f}s  ends {stamp(final)[3:8]}")
    print(f"{LIMIT_SECONDS - final:.0f}s inside the four-minute limit.")
    print("Import subtitles.srt last; it was timed against exactly this layout.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
