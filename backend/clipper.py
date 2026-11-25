import json
import re

from groq import Groq


def transcript_lines(words, per_line=14):
    lines = []
    for i in range(0, len(words), per_line):
        group = words[i:i + per_line]
        text = " ".join(w["word"] for w in group)
        lines.append(f"[{int(group[0]['start'])}s] {text}")
    return "\n".join(lines)


def pick_clips(words, max_clips=5):
    if not words:
        raise RuntimeError("No speech found in this video")

    total = words[-1]["end"]
    prompt = f"""You are picking the best short clips from a video transcript for TikTok.
Timestamps in brackets are seconds from the start. The video is {int(total)} seconds long.

Pick up to {max_clips} clips. Each clip must:
- be 20 to 60 seconds long (if the whole video is shorter than 20 seconds, use the best part of it)
- start on a strong hook and end on a complete thought
- make sense without the rest of the video

Reply with ONLY a JSON list, no other text. Each item:
{{"start": number, "end": number, "title": "short title", "score": 1-100, "reason": "one short sentence on why it works"}}

Transcript:
{transcript_lines(words)}"""

    client = Groq()  # reads GROQ_API_KEY
    resp = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=4000,
        extra_body={"reasoning_effort": "low"},
    )
    text = resp.choices[0].message.content or ""
    found = re.search(r"\[.*\]", text, re.S)
    if not found:
        raise RuntimeError("The AI did not return clips. Try again.")
    raw = json.loads(found.group(0))

    picks = []
    for p in raw:
        start = max(0.0, float(p["start"]))
        end = min(total, float(p["end"]))
        if end - start < 5:
            continue
        picks.append({
            "start": start,
            "end": end,
            "title": str(p.get("title", "Clip")),
            "score": int(p.get("score", 50)),
            "reason": str(p.get("reason", "")),
        })

    picks.sort(key=lambda p: p["score"], reverse=True)
    return picks[:max_clips]
