"""
Shared reading and measuring for the video rig: the narration format, and how long an MP3 is.

Both `make_voiceover.py` and `assemble.py` need these, and neither should own them. The MP3 frame
walker in particular is the kind of thing that gets copied once and then fixed in only one of the
copies — which is how a sibling project spent a week believing a two-minute narration ran to four
and a half.

Nothing here talks to a network, so `assemble.py` does not need the Text-to-Speech SDK installed
just to add up some durations.
"""

import re
import subprocess
from pathlib import Path

#: Silence between segments, in seconds. `make_voiceover.py` lays the subtitle timeline out with
#: it and `assemble.py` builds the voice track with it, so the two must be the same number or the
#: captions drift against the film. One definition rather than two that agree today.
PAUSE_BETWEEN_SEGMENTS = 2.5


#: `{{spoken|shown}}` — the first half is what the voice reads, the second is what the caption
#: says. One source, two outputs. Without this the subtitles read "Gen A. I. S. D. K.", which is
#: the spelling that makes the voice say it correctly and the last thing a viewer wants to read.
SUBSTITUTION = re.compile(r"\{\{([^|}]*)\|([^}]*)\}\}")


def spoken(text: str) -> str:
    """The words as the voice should say them."""
    return SUBSTITUTION.sub(lambda m: m.group(1).strip(), text)


def shown(text: str) -> str:
    """The same words as a reader should see them."""
    return SUBSTITUTION.sub(lambda m: m.group(2).strip(), text)


_SAMPLE_RATES = {
    3: (44100, 48000, 32000),   # MPEG-1
    2: (22050, 24000, 16000),   # MPEG-2
    0: (11025, 12000, 8000),    # MPEG-2.5
}
_BITRATES_V1_L3 = (None, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, None)
_BITRATES_V2_L3 = (None, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, None)


def mp3_duration(data: bytes) -> float:
    """
    Sum the durations of the file's own MPEG audio frames.

    Layer III carries 1152 samples per frame on MPEG-1 and 576 on MPEG-2 and 2.5, so a frame's
    length in seconds is that count over its sample rate. Walking the frames costs nothing and is
    exact, which is the point: the alternative was dividing the file size by a bitrate somebody
    had assumed.
    """
    i, total = 0, 0.0
    n = len(data)
    # Skip an ID3v2 tag if the encoder wrote one.
    if data[:3] == b"ID3" and n > 10:
        # Syncsafe integer: seven bits per byte, high bit always clear.
        size = ((data[6] & 0x7F) << 21 | (data[7] & 0x7F) << 14
                | (data[8] & 0x7F) << 7 | (data[9] & 0x7F))
        i = 10 + size

    while i + 4 <= n:
        if data[i] != 0xFF or (data[i + 1] & 0xE0) != 0xE0:
            i += 1
            continue
        version_bits = (data[i + 1] >> 3) & 0x03      # 3 = MPEG-1, 2 = MPEG-2, 0 = MPEG-2.5
        layer_bits = (data[i + 1] >> 1) & 0x03        # 1 = Layer III
        rate_index = (data[i + 2] >> 2) & 0x03
        bitrate_index = (data[i + 2] >> 4) & 0x0F
        padding = (data[i + 2] >> 1) & 0x01
        if layer_bits != 1 or version_bits == 1 or rate_index == 3:
            i += 1
            continue
        table = _BITRATES_V1_L3 if version_bits == 3 else _BITRATES_V2_L3
        kbps = table[bitrate_index]
        sample_rate = _SAMPLE_RATES[version_bits][rate_index]
        if not kbps or not sample_rate:
            i += 1
            continue
        samples = 1152 if version_bits == 3 else 576
        frame_bytes = int(samples / 8 * kbps * 1000 / sample_rate) + padding
        if frame_bytes <= 4:
            i += 1
            continue
        total += samples / sample_rate
        i += frame_bytes
    if total == 0.0:
        raise SystemExit("Could not find a single MPEG frame in the synthesised audio.")
    return total


def ffprobe_duration(path: Path) -> float | None:
    """The same length according to ffprobe, when it happens to be on PATH. Cross-check only."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
             str(path)], capture_output=True, text=True, timeout=30, check=False)
        if out.returncode == 0 and out.stdout.strip():
            return float(out.stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return None


def parse_narration(path: Path):
    """
    Read `narration.md` into segments: stem, budgeted seconds, paragraphs.

    A heading gives the window and the title; the blockquote under it gives the words, and a blank
    quote line starts a new paragraph. Paragraphs survive into the subtitles as cue boundaries,
    because whoever wrote the sentence knows better than a character count where a caption breaks.
    """
    heading = re.compile(r"^##\s+(\d+):(\d\d)\s*[–-]\s*(\d+):(\d\d)\s*·\s*(.+?)\s*$")
    segments, current = [], None

    for line in path.read_text(encoding="utf-8").splitlines():
        match = heading.match(line)
        if match:
            m1, s1, m2, s2, title = match.groups()
            start = int(m1) * 60 + int(s1)
            stem = f"{len(segments) + 1:02d}-" + re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            current = {"stem": stem, "title": title,
                       "budget": int(m2) * 60 + int(s2) - start, "paragraphs": [[]]}
            segments.append(current)
        elif current is not None and line.startswith(">"):
            text = line[1:].strip()
            if text:
                current["paragraphs"][-1].append(text)
            elif current["paragraphs"][-1]:
                current["paragraphs"].append([])

    if not segments:
        raise SystemExit(f"No segments found in {path}. Headings read '## 0:00 – 0:22 · Title'.")

    for segment in segments:
        segment["paragraphs"] = [" ".join(p) for p in segment["paragraphs"] if p]
        segment["text"] = " ".join(segment["paragraphs"])
    return segments


def stamp(seconds: float) -> str:
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
