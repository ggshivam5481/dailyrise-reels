"""Stickman reel renderer: script JSON -> 1080x1920 MP4 with Hindi voiceover."""
import asyncio
import glob
import math
import os
import random
import subprocess
import tempfile
import wave

from PIL import Image, ImageDraw, ImageFont
import edge_tts

W, H, FPS = 1080, 1920, 24
BG = (250, 247, 240)
INK = (24, 24, 30)
ACCENT = (255, 92, 56)
BLUE = (48, 118, 255)
GOLD = (255, 196, 40)
LIGHT = (196, 196, 204)
GRID = (237, 233, 223)

VOICE = os.environ.get("TTS_VOICE", "hi-IN-MadhurNeural")
RATE = os.environ.get("TTS_RATE", "+8%")
HANDLE = os.environ.get("IG_HANDLE", "@dailyrise.reels")

GROUND = 1440
S = 1.25  # stickman scale
TORSO, HEAD, UA, FA, TH, SH, LW = 190, 58, 115, 105, 125, 120, 16
CX = W // 2


def find_font(names):
    for n in names:
        if os.path.isabs(n) and os.path.exists(n):
            return n
        hits = glob.glob(f"/usr/share/fonts/**/{n}", recursive=True)
        if hits:
            return hits[0]
    return None


FONT_PATH = find_font([
    "ComicNeue-Bold.ttf", "ComicNeue-Bold.otf", "C:/Windows/Fonts/comicbd.ttf",
    "DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf",
])
_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT_PATH, size) if FONT_PATH else ImageFont.load_default(size)
    return _fonts[size]


# ---------- geometry ----------
def pt(p, ang, length):
    """Angle in degrees: 0 = down, 90 = right, 180 = up."""
    a = math.radians(ang)
    return (p[0] + length * math.sin(a), p[1] + length * math.cos(a))


def seg(d, pts, w, c):
    d.line(pts, fill=c, width=w, joint="curve")
    for p in (pts[0], pts[-1]):
        d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=c)


STAND = dict(lean=0, head=0, la1=-18, la2=-8, ra1=18, ra2=8, ll1=-10, ll2=0, rl1=10, rl2=0)


def draw_stick(d, hip, P, s=S, mood="neutral", blink=False, eyes_closed=False, look=0, color=INK):
    lw = int(LW * s)
    lean = P.get("lean", 0)
    neck = pt(hip, 180 - lean, TORSO * s)
    shoulder = pt(hip, 180 - lean, (TORSO - 25) * s)
    head_c = pt(neck, 180 - lean - P.get("head", 0), (HEAD + 6) * s)
    for k in ("l", "r"):
        a1, a2 = P[k + "l1"], P.get(k + "l2", 0)
        knee = pt(hip, a1, TH * s)
        seg(d, [hip, knee, pt(knee, a1 + a2, SH * s)], lw, color)
    seg(d, [hip, neck], lw, color)
    hands = {}
    for k in ("l", "r"):
        a1, a2 = P[k + "a1"], P.get(k + "a2", 0)
        el = pt(shoulder, a1, UA * s)
        hand = pt(el, a1 + a2, FA * s)
        seg(d, [shoulder, el, hand], lw, color)
        hands[k] = hand
    r = HEAD * s
    hx, hy = head_c
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=BG, outline=color, width=lw)
    ex = 19 * s
    ox = look * 10 * s
    for sx in (-1, 1):
        x, y = hx + sx * ex + ox, hy - 8 * s
        if blink or eyes_closed:
            d.line([x - 8 * s, y, x + 8 * s, y], fill=color, width=int(5 * s))
        else:
            d.ellipse([x - 6.5 * s, y - 6.5 * s, x + 6.5 * s, y + 6.5 * s], fill=color)
    mx, my = hx + ox, hy + 20 * s
    if mood == "happy":
        d.arc([mx - 22 * s, my - 16 * s, mx + 22 * s, my + 12 * s], 20, 160, fill=color, width=int(5 * s))
    elif mood == "sad":
        d.arc([mx - 18 * s, my, mx + 18 * s, my + 22 * s], 200, 340, fill=color, width=int(5 * s))
    elif mood == "wow":
        d.ellipse([mx - 9 * s, my - 6 * s, mx + 9 * s, my + 12 * s], outline=color, width=int(5 * s))
    else:
        d.line([mx - 14 * s, my + 2 * s, mx + 14 * s, my + 2 * s], fill=color, width=int(5 * s))
    return hands, head_c


# ---------- poses ----------
def hip_stand(s=S):
    return GROUND - (TH + SH) * s


def pose(name, t, dur):
    P = dict(STAND)
    sn = math.sin
    x, y = CX, hip_stand()
    o = dict(mood="neutral", look=0, closed=False, props=[])
    if name == "walk" or name == "run":
        fast = name == "run"
        f, amp = (12, 42) if fast else (7, 26)
        w = sn(t * f)
        P.update(ll1=amp * w, ll2=-(amp * 0.9) * max(0, -w), rl1=-amp * w, rl2=-(amp * 0.9) * max(0, w),
                 la1=-amp * 0.8 * w, la2=50 if fast else 15, ra1=amp * 0.8 * w, ra2=50 if fast else 15,
                 lean=12 if fast else 4)
        y -= abs(sn(t * f)) * (14 if fast else 6)
        o.update(mood="happy", look=1, props=[("ground", (t * (700 if fast else 320)))])
        if fast:
            o["props"].append(("speed", t))
    elif name == "think":
        P.update(ra1=30, ra2=170, la1=28, la2=75, head=-8)
        y += sn(t * 2) * 3
        o.update(look=-1, props=[("bubble", t)])
    elif name == "point":
        P.update(ra1=95 + 6 * sn(t * 5), ra2=-4, la1=-14)
        x -= 120
        o.update(mood="happy", look=1, props=[("arrow", t)])
    elif name == "sad":
        P.update(lean=10, head=-14, la1=-4, la2=0, ra1=4, ra2=0)
        y += 6 + sn(t * 1.5) * 3
        o.update(mood="sad", props=[("cloud", t)])
    elif name == "celebrate":
        wv = 16 * sn(t * 10)
        P.update(la1=-150 + wv, la2=-10, ra1=150 - wv, ra2=10, ll1=-22, rl1=22)
        y -= abs(sn(t * 6)) * 55
        o.update(mood="happy", props=[("confetti", t)])
    elif name == "lift":
        ph = (1 + sn(t * 4)) / 2
        P.update(la1=-(115 + 50 * ph), la2=-(70 * (1 - ph)), ra1=115 + 50 * ph, ra2=70 * (1 - ph), ll1=-18, rl1=18)
        o.update(mood="happy" if ph > 0.5 else "neutral", props=[("barbell", None)])
    elif name == "phone":
        P.update(ra1=28, ra2=118, la1=-12, head=-10)
        o.update(mood="neutral", look=1, props=[("phone", t)])
    elif name == "read":
        P.update(la1=38, la2=62, ra1=48, ra2=58, head=-10)
        o.update(mood="happy", look=1, props=[("book", t)])
    elif name == "meditate":
        P.update(ll1=-82, ll2=150, rl1=82, rl2=-150, la1=-42, la2=-25, ra1=42, ra2=25)
        y = GROUND - 30 * S + sn(t * 2) * 5
        o.update(mood="happy", closed=True, props=[("glow", t)])
    elif name == "climb":
        steps = min(dur * 1.4, 5.0)
        k = min(t * 1.4, steps)
        w = sn(t * 8)
        P.update(ll1=35 * max(0, w) - 5, ll2=-40 * max(0, w), rl1=35 * max(0, -w) - 5, rl2=-40 * max(0, -w),
                 la1=-25 * w, la2=20, ra1=25 * w, ra2=20, lean=6)
        x = 260 + k * 95
        y = hip_stand() - k * 72
        o.update(mood="happy", look=1, props=[("stairs", None), ("flag", t)])
    elif name == "sleep":
        o.update(mood="neutral", closed=True, props=[("zzz", t)], lying=True)
    else:  # idle
        P.update(la1=-18 + 4 * sn(t * 2), ra1=18 - 4 * sn(t * 2))
        y += sn(t * 3) * 4
        o.update(mood="happy")
    return P, (x, y), o


# ---------- props ----------
def draw_prop(d, kind, arg, hands, head, hip):
    if kind == "ground":
        off = arg % 120
        for gx in range(-120, W + 120, 120):
            d.line([gx - off, GROUND + 26, gx - off + 55, GROUND + 26], fill=LIGHT, width=8)
    elif kind == "speed":
        for i in range(4):
            yy = hip[1] - 220 + i * 70
            xx = hip[0] - 230 - (arg * 900 + i * 60) % 120
            d.line([xx, yy, xx - 110, yy], fill=LIGHT, width=9)
    elif kind == "bubble":
        bx, by = head[0] + 150, head[1] - 210
        for i, (dx, dy, r) in enumerate([(-95, 150, 12), (-60, 100, 20)]):
            d.ellipse([bx + dx - r, by + dy - r, bx + dx + r, by + dy + r], outline=INK, width=6, fill=(255, 255, 255))
        d.ellipse([bx - 95, by - 80, bx + 105, by + 60], outline=INK, width=7, fill=(255, 255, 255))
        q = "?" if int(arg * 2) % 2 == 0 else "?!"
        f = font(96)
        tw = d.textlength(q, font=f)
        d.text((bx + 5 - tw / 2, by - 70), q, font=f, fill=BLUE)
    elif kind == "arrow":
        hx, hy = hands["r"]
        sh = 20 * math.sin(arg * 6)
        x0 = hx + 40 + sh
        d.line([x0, hy, x0 + 150, hy], fill=ACCENT, width=14)
        d.polygon([(x0 + 190, hy), (x0 + 140, hy - 34), (x0 + 140, hy + 34)], fill=ACCENT)
    elif kind == "cloud":
        cx, cy = head[0], head[1] - 230
        for dx, dy, r in [(-70, 10, 55), (0, -20, 70), (70, 10, 55)]:
            d.ellipse([cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r], fill=(150, 156, 170))
        for i in range(5):
            ph = (arg * 1.6 + i * 0.37) % 1
            rx = cx - 90 + i * 45
            ry = cy + 60 + ph * 140
            d.line([rx, ry, rx - 6, ry + 26], fill=BLUE, width=7)
    elif kind == "confetti":
        rnd = random.Random(7)
        for i in range(40):
            px = rnd.uniform(60, W - 60)
            sp = rnd.uniform(220, 420)
            py = (rnd.uniform(0, 900) + arg * sp) % 1000 + 380
            c = rnd.choice([ACCENT, BLUE, GOLD, (60, 190, 120)])
            a = arg * rnd.uniform(3, 8)
            dx, dy = 14 * math.cos(a), 14 * math.sin(a)
            d.line([px - dx, py - dy, px + dx, py + dy], fill=c, width=10)
    elif kind == "barbell":
        (lx, ly), (rx, ry) = hands["l"], hands["r"]
        my = (ly + ry) / 2
        d.line([lx - 90, my, rx + 90, my], fill=INK, width=12)
        for px in (lx - 70, rx + 70):
            d.rounded_rectangle([px - 18, my - 60, px + 18, my + 60], 8, fill=ACCENT)
    elif kind == "phone":
        hx, hy = hands["r"]
        d.rounded_rectangle([hx - 34, hy - 62, hx + 34, hy + 62], 12, fill=INK)
        glow = 150 + int(80 * (0.5 + 0.5 * math.sin(arg * 8)))
        d.rounded_rectangle([hx - 26, hy - 50, hx + 26, hy + 48], 6, fill=(120, 170, glow))
    elif kind == "book":
        (lx, ly), (rx, ry) = hands["l"], hands["r"]
        mx, my = (lx + rx) / 2 + 20, min(ly, ry) - 10
        d.polygon([(mx, my + 10), (mx - 110, my - 20), (mx - 110, my + 90), (mx, my + 120)], fill=(255, 255, 255), outline=INK, width=6)
        d.polygon([(mx, my + 10), (mx + 110, my - 20), (mx + 110, my + 90), (mx, my + 120)], fill=(255, 255, 255), outline=INK, width=6)
        for i in range(3):
            yy = my + 15 + i * 25
            d.line([mx - 90, yy, mx - 20, yy + 10], fill=LIGHT, width=5)
            d.line([mx + 20, yy + 10, mx + 90, yy], fill=LIGHT, width=5)
    elif kind == "glow":
        r = 330 + 20 * math.sin(arg * 2)
        cx, cy = hip[0], hip[1] - 230
        for i, c in enumerate([(255, 236, 190), (255, 228, 160)]):
            rr = r - i * 70
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=c, width=14)
    elif kind == "stairs":
        for i in range(7):
            x0 = 200 + i * 95 + 60
            y0 = GROUND - i * 72
            d.rectangle([x0, y0, x0 + 95, y0 + 72 * (i + 1)], fill=(232, 226, 212), outline=INK, width=6)
    elif kind == "flag":
        fx, fy = 200 + 7 * 95 + 40, GROUND - 7 * 72
        d.line([fx, fy, fx, fy - 170], fill=INK, width=9)
        wv = 10 * math.sin(arg * 6)
        d.polygon([(fx, fy - 170), (fx + 100, fy - 140 + wv), (fx, fy - 110)], fill=ACCENT)
    elif kind == "zzz":
        for i in range(3):
            ph = (arg * 0.7 + i / 3) % 1
            f = font(int(50 + 30 * i))
            d.text((head[0] + 70 + ph * 120 + i * 30, head[1] - 80 - ph * 260), "Z", font=f, fill=BLUE)
    elif kind == "clock":
        cx, cy, r = 880, 640, 85
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255), outline=INK, width=9)
        a = arg * 140
        d.line([(cx, cy), pt((cx, cy), 180 - a, r * 0.75)], fill=ACCENT, width=9)
        d.line([(cx, cy), pt((cx, cy), 180 - a / 12, r * 0.5)], fill=INK, width=11)


def draw_sleeper(img, t):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([170, GROUND - 120, 910, GROUND - 40], 20, fill=(140, 170, 230), outline=INK, width=7)
    d.rectangle([170, GROUND - 40, 190, GROUND + 20], fill=INK)
    d.rectangle([890, GROUND - 40, 910, GROUND + 20], fill=INK)
    d.rounded_rectangle([200, GROUND - 175, 330, GROUND - 120], 20, fill=(255, 255, 255), outline=INK, width=6)
    layer = Image.new("RGBA", (900, 900), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    breath = math.sin(t * 2) * 4
    P = dict(STAND, la1=-6, ra1=6, ll1=-3, rl1=3)
    _, head = draw_stick(ld, (450, 520 + breath), P, s=1.05, eyes_closed=True, mood="happy")
    rot = layer.rotate(-90, resample=Image.BICUBIC, center=(450, 520))
    img.paste(rot, (165, GROUND - 650), rot)
    draw_prop(d, "zzz", t, {}, (300, GROUND - 230), None)


# ---------- text ----------
def wrap_words(words, f, d, maxw):
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if cur and d.textlength(test, font=f) > maxw:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(cur)
    return lines


def draw_title(d, title):
    f = font(78)
    lines = wrap_words(title.split(), f, d, 900)
    lh = 92
    top = 150
    box_h = lh * len(lines) + 50
    d.rounded_rectangle([60, top - 25, W - 60, top - 25 + box_h], 36, fill=INK)
    for i, ln in enumerate(lines):
        s = " ".join(ln)
        tw = d.textlength(s, font=f)
        d.text(((W - tw) / 2, top + i * lh), s, font=f, fill=(255, 255, 255))
    d.rounded_rectangle([W / 2 - 70, top - 25 + box_h - 8, W / 2 + 70, top - 25 + box_h + 4], 6, fill=ACCENT)


def draw_subtitle(d, text, progress):
    f = font(70)
    words = text.split()
    lines = wrap_words(words, f, d, 940)
    n = len(words)
    spoken = progress * n
    lh = 88
    top = 1530
    idx = 0
    space = d.textlength(" ", font=f)
    for li, ln in enumerate(lines):
        total = d.textlength(" ".join(ln), font=f)
        x = (W - total) / 2
        y = top + li * lh
        for w in ln:
            if idx < int(spoken):
                c = INK
            elif idx == int(spoken):
                c = ACCENT
            else:
                c = LIGHT
            d.text((x, y), w, font=f, fill=c)
            x += d.textlength(w, font=f) + space
            idx += 1


def make_background():
    bg = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(bg)
    for yy in range(80, H, 80):
        d.line([0, yy, W, yy], fill=GRID, width=2)
    d.line([0, GROUND + 6, W, GROUND + 6], fill=INK, width=8)
    f = font(40)
    tw = d.textlength(HANDLE, font=f)
    d.text(((W - tw) / 2, H - 110), HANDLE, font=f, fill=(170, 170, 178))
    return bg


# ---------- audio ----------
async def _tts(text, path):
    await edge_tts.Communicate(text, VOICE, rate=RATE).save(path)


def synth(scenes, tmp):
    durs, wavs = [], []
    for i, sc in enumerate(scenes):
        mp3 = os.path.join(tmp, f"s{i}.mp3")
        wav = os.path.join(tmp, f"s{i}.wav")
        for attempt in range(3):
            try:
                asyncio.run(_tts(sc["say"], mp3))
                break
            except Exception:
                if attempt == 2:
                    raise
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-af", "apad=pad_dur=0.35",
                        "-ar", "44100", "-ac", "1", wav], check=True)
        with wave.open(wav) as wf:
            durs.append(wf.getnframes() / wf.getframerate())
        wavs.append(wav)
    full = os.path.join(tmp, "full.wav")
    with wave.open(wavs[0]) as w0:
        params = w0.getparams()
    with wave.open(full, "wb") as out:
        out.setparams(params)
        for wv in wavs:
            with wave.open(wv) as wf:
                out.writeframes(wf.readframes(wf.getnframes()))
    return durs, full


# ---------- main render ----------
CTA = {"pose": "celebrate", "say": "रोज़ एक प्रतिशत बेहतर बनने के लिए, अभी फॉलो करो।",
       "text": "Roz 1% better ke liye FOLLOW karo"}


def render(reel, out_path):
    scenes = list(reel["scenes"]) + [CTA]
    with tempfile.TemporaryDirectory() as tmp:
        durs, audio = synth(scenes, tmp)
        total = sum(durs)
        bg = make_background()
        draw_title(ImageDraw.Draw(bg), reel["title"])
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-i", audio, "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-shortest",
               "-movflags", "+faststart", out_path]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        elapsed = 0.0
        for sc, dur in zip(scenes, durs):
            nfr = max(1, round(dur * FPS))
            for fi in range(nfr):
                t = fi / FPS
                gt = elapsed + t
                img = bg.copy()
                d = ImageDraw.Draw(img)
                d.rectangle([0, 0, W * gt / total, 14], fill=ACCENT)
                name = sc.get("pose", "idle")
                if name == "sleep":
                    draw_sleeper(img, t)
                    d = ImageDraw.Draw(img)
                else:
                    P, hip, o = pose(name, t, dur)
                    pre = [p for p in o["props"] if p[0] in ("glow", "stairs", "ground", "speed")]
                    post = [p for p in o["props"] if p not in pre]
                    for kind, arg in pre:
                        draw_prop(d, kind, arg, {}, None, hip)
                    pop = min(1.0, 0.85 + t * 1.2)
                    blink = (gt % 3.2) < 0.12
                    hands, head = draw_stick(d, hip, P, s=S * pop, mood=o["mood"], blink=blink,
                                             eyes_closed=o["closed"], look=o["look"])
                    for kind, arg in post:
                        draw_prop(d, kind, arg, hands, head, hip)
                if sc.get("prop") == "clock":
                    draw_prop(d, "clock", t, {}, None, None)
                draw_subtitle(d, sc["text"], min(1.0, t / max(0.1, dur - 0.35)))
                proc.stdin.write(img.tobytes())
            elapsed += dur
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError("ffmpeg failed")
    return total
