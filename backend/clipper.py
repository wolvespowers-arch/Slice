import json
import re

import anthropic


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
- be 20 to 60 seconds long
- start on a strong hook and end on a complete thought
- make sense without the rest of the video

Reply with ONLY a JSON list, no other text. Each item:
{{"start": number, "end": number, "title": "short title", "score": 1-100, "reason": "one short sentence on why it works"}}

Transcript:
{transcript_lines(words)}"""

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    msg = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    text = msg.content[0].text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    raw = json.loads(text)

    picks = []
    for p in raw:
        start = max(0.0, float(p["start"]))
        end = min(total, float(p["end"]))
        if end - start < 10:
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
