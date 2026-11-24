import subprocess
import tempfile
from pathlib import Path

from groq import Groq


def _get(w, key):
    return w[key] if isinstance(w, dict) else getattr(w, key)


def transcribe(source):
    with tempfile.TemporaryDirectory() as tmp:
        audio = Path(tmp) / "audio.mp3"
        cmd = [
            "ffmpeg", "-y", "-i", str(source),
            "-vn", "-ac", "1", "-ar", "16000", "-b:a", "32k", str(audio),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError("Could not read audio: " + result.stderr[-300:])

        client = Groq()  # reads GROQ_API_KEY
        with open(audio, "rb") as f:
            resp = client.audio.transcriptions.create(
                file=("audio.mp3", f.read()),
                model="whisper-large-v3-turbo",
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )

    raw = getattr(resp, "words", None) or []
    return [
        {
            "word": str(_get(w, "word")).strip(),
            "start": float(_get(w, "start")),
            "end": float(_get(w, "end")),
        }
        for w in raw
    ]


def stamp(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def build_srt(words, start, end, per_line=3):
    chosen = [w for w in words if w["start"] >= start and w["end"] <= end]
    blocks = []
    for i in range(0, len(chosen), per_line):
        group = chosen[i:i + per_line]
        t0 = group[0]["start"] - start
        t1 = group[-1]["end"] - start
        text = " ".join(w["word"] for w in group).upper()
        blocks.append(f"{len(blocks) + 1}\n{stamp(t0)} --> {stamp(t1)}\n{text}\n")
    return "\n".join(blocks)


STYLE = (
    "FontName=Arial,Bold=1,FontSize=11,"
    "PrimaryColour=&H00FFFFFF,OutlineColour=&H0024120A,"
    "BorderStyle=1,Outline=2,Alignment=2,MarginV=60"
)


def make_clip(source, words, pick, out_path):
    start, end = pick["start"], pick["end"]
    source = str(Path(source).resolve())
    out_path = str(Path(out_path).resolve())

    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "cap.srt").write_text(
            build_srt(words, start, end), encoding="utf-8"
        )
        vf = (
            "crop=min(iw\\,ih*9/16):ih,scale=1080:1920,"
            f"subtitles=cap.srt:force_style='{STYLE}'"
        )
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start), "-i", source,
            "-t", str(end - start),
            "-vf", vf,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-movflags", "+faststart",
            out_path,
        ]
        result = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError("ffmpeg failed: " + result.stderr[-400:])
