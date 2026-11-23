# Slice

Personal app. Paste a link or upload a video, get the best clips with captions,
download them, post from your phone.

## Structure
- `frontend/` the screen (HTML, CSS, JS)
- `backend/` the server (Python, FFmpeg, Whisper, Claude)

## Backend needs
- Environment variable `ANTHROPIC_API_KEY` (set on the host, never in this repo)

## Front end
In `frontend/app.js`, set `API` to the server address.
