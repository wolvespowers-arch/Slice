const API = "https://slice-6.onrender.com";

const go = document.getElementById("go");
const statusEl = document.getElementById("status");
const clipsEl = document.getElementById("clips");

go.addEventListener("click", async () => {
  const raw = document.getElementById("url").value.trim();
  const found = raw.match(/https?:\/\/\S+/);
  const url = found ? found[0] : raw;
  const file = document.getElementById("file").files[0];

  if (!url && !file) {
    statusEl.textContent = "Paste a link or choose a video first.";
    return;
  }

  const form = new FormData();
  if (file) form.append("file", file);
  else form.append("url", url);

  go.disabled = true;
  clipsEl.innerHTML = "";
  statusEl.textContent = "Slicing... this can take a few minutes.";

  try {
    const res = await fetch(API + "/slice", { method: "POST", body: form });
    if (!res.ok) {
      let msg = "Server error " + res.status;
      try {
        const j = await res.json();
        if (j.detail) msg = j.detail;
      } catch (e) {}
      throw new Error(msg);
    }
    const data = await res.json();
    showClips(data.clips);
    statusEl.textContent = data.clips.length + " clips ready.";
  } catch (err) {
    statusEl.textContent = "Something went wrong: " + err.message;
  } finally {
    go.disabled = false;
  }
});

function showClips(clips) {
  clips.forEach((c) => {
    const box = document.createElement("div");
    box.className = "clip";

    const title = document.createElement("div");
    title.textContent = c.title;

    const score = document.createElement("div");
    score.className = "score";
    score.textContent = "Score " + c.score;

    const reason = document.createElement("div");
    reason.className = "reason";
    reason.textContent = c.reason;

    const video = document.createElement("video");
    video.src = API + c.download_url;
    video.controls = true;
    video.style.width = "100%";
    video.style.marginBottom = "12px";

    const link = document.createElement("a");
    link.href = API + c.download_url;
    link.download = "slice-" + c.id + ".mp4";
    const btn = document.createElement("button");
    btn.textContent = "Download";
    link.appendChild(btn);

    box.append(title, score, reason, video, link);
    clipsEl.appendChild(box);
  });
      }
