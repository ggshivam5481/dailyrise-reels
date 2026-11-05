"""Thumbnail: a 1-second title card added at the end of each reel, used as the reel cover.

Instagram picks the cover with thumb_offset (ms into the video), so no public image URL is needed.
The title sits inside the centre 3:4 area so the profile grid crop shows all of it.
"""
import json
import os
import re
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageEnhance

import render as R

CARD = 1.0


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def title_from(caption):
    first = caption.split("\n", 1)[0]
    return re.sub(r"[^\w\s'%,!?-]", "", first).strip(" .")


def make_card(video, title, png):
    dur = duration(video)
    frame = png + ".src.png"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{dur * 0.55:.2f}", "-i", video,
                    "-frames:v", "1", frame], check=True)
    img = ImageEnhance.Brightness(Image.open(frame).convert("RGB")).enhance(0.35)
    os.remove(frame)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 238, R.W, 378], fill=img.getpixel((R.W // 2, 230)))  # hide the small in-video caption
    f = R.font(92)
    words, lines, cur = title.upper().split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if cur and R.text_w(d, t, f, 6) > 900:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    lh = 92 + 30
    y = R.H / 2 - len(lines) * lh / 2
    R.spaced(d, R.W / 2, y - 110, "1% BETTER", R.font(40), R.WARM, sp=10)
    for i, ln in enumerate(lines):
        R.spaced(d, R.W / 2, y + i * lh, ln, f, R.WHITE, sp=6)
    d.line([(R.W / 2 - 90, y + len(lines) * lh + 30), (R.W / 2 + 90, y + len(lines) * lh + 30)],
           fill=R.WARM, width=6)
    R.spaced(d, R.W / 2, y + len(lines) * lh + 70, "@DAILYRISE.REELS", R.font(36), (190, 196, 210), sp=6)
    img.save(png)
    return dur


def add_cover(video, caption, out):
    """Write `out` = video + title card. Returns thumb_offset in ms (middle of the card)."""
    png = os.path.join(tempfile.gettempdir(), "cover_card.png")
    dur = make_card(video, title_from(caption), png)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video,
                    "-loop", "1", "-framerate", str(R.FPS), "-t", str(CARD), "-i", png,
                    "-f", "lavfi", "-t", str(CARD), "-i", "anullsrc=r=48000:cl=stereo",
                    "-filter_complex",
                    "[0:v]fps=%d,format=yuv420p,setsar=1[v0];[1:v]fps=%d,format=yuv420p,setsar=1[v1];"
                    "[0:a]aresample=48000,aformat=channel_layouts=stereo[a0];"
                    "[v0][a0][v1][2:a]concat=n=2:v=1:a=1[v][a]" % (R.FPS, R.FPS),
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out], check=True)
    return int((dur + CARD / 2) * 1000)
