import shutil
import uuid
from pathlib import Path

import yt_dlp
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from captions import make_clip, transcribe
from clipper import pick_clips

WORK = Path("work")
OUT = Path("clips")
WORK.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)

app = FastAPI()

# Personal app: open for now. We tighten this once the front end has a real address.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/clips", StaticFiles(directory=OUT), name="clips")


def download_video(url: str, folder: Path) -> Path:
    opts = {
        "outtmpl": str(folder / "source.%(ext)s"),
        "format": "mp4/best",
        "noplaylist": True,
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    files = list(folder.glob("source.*"))
    if not files:
        raise RuntimeError("Download failed")
    return files[0]


@app.get("/")
def health():
    return {"app": "slice", "ok": True}


@app.post("/slice")
def slice_video(
    file: UploadFile | None = File(None),
    url: str | None = Form(None),
):
    if not file and not url:
        raise HTTPException(400, "Send a file or a url")

    job = uuid.uuid4().hex[:8]
    folder = WORK / job
    folder.mkdir()

    try:
        if file:
            source = folder / "source.mp4"
            with open(source, "wb") as f:
                shutil.copyfileobj(file.file, f)
        else:
            source = download_video(url, folder)

        words = transcribe(source)
        picks = pick_clips(words)

        clips = []
        for i, pick in enumerate(picks):
            clip_id = f"{job}-{i}"
            make_clip(source, words, pick, OUT / f"{clip_id}.mp4")
            clips.append({
                "id": clip_id,
                "title": pick["title"],
                "score": pick["score"],
                "reason": pick["reason"],
                "download_url": f"/clips/{clip_id}.mp4",
            })

        return {"clips": clips}

    except Exception as err:
        raise HTTPException(400, str(err))

    finally:
        shutil.rmtree(folder, ignore_errors=True)
