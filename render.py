"""Dark cinematic silhouette-stickman reels: reel JSON -> 1080x1920 MP4 with ambient music.

Each reel picks one visual-metaphor template (door, boulder, crowd, stairs, compare, carry, leap)
and fills in its labels. No voiceover, short uppercase caption on top, loop-friendly.
"""
import glob
import math
import os
import random
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 24
GROUND = 1420
SIL = (7, 8, 11)
RIM = (64, 72, 88)
WHITE = (232, 236, 242)
MUTED = (140, 148, 162)
RED = (214, 46, 38)
WARM = (255, 202, 112)
WARM2 = (255, 238, 196)
PHONE = (150, 192, 255)
STONE = (48, 52, 60)
HANDLE = os.environ.get("IG_HANDLE", "@dailyrise.reels")

TORSO, HEAD, UA, FA, TH, SH, LW = 190, 60, 112, 102, 122, 118, 30


# ---------------- basics ----------------
def find_font(names):
    for n in names:
        if os.path.isabs(n) and os.path.exists(n):
            return n
        hits = glob.glob(f"/usr/share/fonts/**/{n}", recursive=True)
        if hits:
            return hits[0]
    return None


MONO = find_font(["DejaVuSansMono-Bold.ttf", "C:/Windows/Fonts/consolab.ttf", "C:/Windows/Fonts/courbd.ttf"])
_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(MONO, size) if MONO else ImageFont.load_default(size)
    return _fonts[size]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def pt(p, ang, length):
    """0 deg = down, 90 = right, 180 = up."""
    a = math.radians(ang)
    return (p[0] + length * math.sin(a), p[1] + length * math.cos(a))


def seg(d, pts, w, c):
    d.line(pts, fill=c, width=w, joint="curve")
    for p in (pts[0], pts[-1]):
        d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=c)


def text_w(d, s, f, sp):
    return sum(d.textlength(c, font=f) for c in s) + sp * max(0, len(s) - 1)


def spaced(d, cx, y, s, f, fill, sp=5):
    x = cx - text_w(d, s, f, sp) / 2
    for c in s:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + sp


def caption(d, text, y=250, size=44, color=WHITE):
    f = font(size)
    words, lines, cur = text.upper().split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if cur and text_w(d, t, f, 5) > 940:
            lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    for i, ln in enumerate(lines):
        spaced(d, W / 2, y + i * (size + 20), ln, f, color)


def sign(d, cx, cy, text, size=36, color=WHITE, box=(14, 16, 21), outline=WHITE):
    f = font(size)
    tw = text_w(d, text, f, 3)
    pw, ph = 20, 12
    d.rectangle([cx - tw / 2 - pw, cy - size / 2 - ph, cx + tw / 2 + pw, cy + size / 2 + ph + 4],
                fill=box, outline=outline, width=4)
    spaced(d, cx, cy - size / 2 - 2, text, f, color, 3)


# ---------------- backgrounds ----------------
def sky(seed=1, mountains=True):
    g = Image.linear_gradient("L").resize((W, H))
    top, bot = (70, 82, 104), (10, 12, 17)
    img = Image.merge("RGB", [g.point(lambda v, i=i: int(top[i] + (bot[i] - top[i]) * v / 255)) for i in range(3)])
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([630, 280, 930, 580], fill=130)
    glow = glow.filter(ImageFilter.GaussianBlur(95))
    img = Image.composite(Image.new("RGB", (W, H), (205, 214, 232)), img, glow)
    d = ImageDraw.Draw(img)
    d.ellipse([736, 386, 824, 474], fill=(226, 230, 238))
    rnd = random.Random(seed)
    if mountains:
        for base, amp, col in [(1190, 190, (42, 50, 66)), (1300, 130, (27, 32, 43))]:
            pts, x = [(0, H)], -40
            while x <= W + 120:
                pts.append((x, base - rnd.uniform(0.25, 1.0) * amp))
                x += rnd.randint(80, 170)
            pts.append((W, H))
            d.polygon(pts, fill=col)
        fog = Image.new("L", (W, H), 0)
        ImageDraw.Draw(fog).rectangle([0, 1270, W, 1380], fill=70)
        fog = fog.filter(ImageFilter.GaussianBlur(45))
        img = Image.composite(Image.new("RGB", (W, H), (120, 132, 150)), img, fog)
    return img


def vignette(img):
    m = Image.new("L", (W, H), 255)
    ImageDraw.Draw(m).ellipse([-200, 150, W + 200, H - 150], fill=0)
    m = m.filter(ImageFilter.GaussianBlur(220)).point(lambda v: int(v * 0.65))
    return Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, m)


def flat_ground(img, y=GROUND):
    d = ImageDraw.Draw(img)
    d.rectangle([0, y, W, H], fill=(11, 12, 16))
    d.line([0, y, W, y], fill=(78, 88, 106), width=3)


def watermark(img):
    d = ImageDraw.Draw(img)
    spaced(d, W / 2, H - 120, HANDLE, font(32), (96, 104, 118), 3)


_bg_cache = {}


def bg(key, builder):
    if key not in _bg_cache:
        im = builder()
        im = vignette(im)
        watermark(im)
        _bg_cache[key] = im
    return _bg_cache[key]


# ---------------- figure ----------------
BASE = dict(lean=0, head=0, la1=-14, la2=-6, ra1=14, ra2=6, ll1=-8, ll2=0, rl1=8, rl2=0)


def mirror(P):
    return {k: -v for k, v in P.items()}


def walk(t, f=7.0, amp=26, lean=4, bend=15):
    w = math.sin(t * f)
    P = dict(BASE, ll1=amp * w, ll2=-amp * 0.9 * max(0, -w), rl1=-amp * w, rl2=-amp * 0.9 * max(0, w),
             la1=-amp * 0.8 * w, la2=bend, ra1=amp * 0.8 * w, ra2=bend, lean=lean)
    return P, abs(w)


def stand_y(s=1.0):
    return GROUND - (TH + SH) * s


def figure(d, hip, P, s=1.0, look=0, eyes="open", col=SIL, rim=RIM):
    lean = P.get("lean", 0)
    neck = pt(hip, 180 - lean, TORSO * s)
    sh = pt(hip, 180 - lean, (TORSO - 28) * s)
    head = pt(neck, 180 - lean - P.get("head", 0), (HEAD + 4) * s)
    bones, hands, feet = [], {}, {}
    for k in "lr":
        a1, a2 = P[k + "l1"], P.get(k + "l2", 0)
        kn = pt(hip, a1, TH * s)
        ft = pt(kn, a1 + a2, SH * s)
        bones.append(([hip, kn, ft], 1.0))
        feet[k] = ft
    bones.append(([hip, neck], 1.2))
    for k in "lr":
        a1, a2 = P[k + "a1"], P.get(k + "a2", 0)
        el = pt(sh, a1, UA * s)
        hd = pt(el, a1 + a2, FA * s)
        bones.append(([sh, el, hd], 0.85))
        hands[k] = hd
    r = HEAD * s
    passes = [(rim, 7 * s), (col, 0)] if rim else [(col, 0)]
    for color, extra in passes:
        for pts, wm in bones:
            seg(d, pts, int(LW * s * wm + extra), color)
        rr = r + extra / 2
        d.ellipse([head[0] - rr, head[1] - rr, head[0] + rr, head[1] + rr], fill=color)
    ex, ox = 20 * s, look * 13 * s
    for sx in (-1, 1):
        x, y = head[0] + sx * ex + ox, head[1] - 4 * s
        if eyes == "closed":
            d.line([x - 8 * s, y + 2 * s, x + 8 * s, y + 2 * s], fill=WHITE, width=max(2, int(4 * s)))
            continue
        ew, eh = {"open": (5, 8), "wide": (7, 10), "squint": (6, 3.5), "down": (5, 5)}.get(eyes, (5, 8))
        if eyes == "down":
            y += 9 * s
        d.ellipse([x - ew * s, y - eh * s, x + ew * s, y + eh * s], fill=WHITE)
    return {"hands": hands, "head": head, "feet": feet, "neck": neck}


def dust(d, t, n=34, seed=3):
    rnd = random.Random(seed)
    for _ in range(n):
        x0, y0, sp, r = rnd.uniform(0, W), rnd.uniform(400, 1700), rnd.uniform(8, 26), rnd.uniform(1.5, 3.5)
        x = (x0 + math.sin(t * 0.6 + y0) * 18) % W
        y = (y0 - t * sp) % 1400 + 350
        c = 95 + int(40 * (0.5 + 0.5 * math.sin(t * 2 + x0)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(c, c + 6, c + 18))


def scroll_ground(d, t, speed, y=GROUND, col=(52, 60, 74)):
    off = (t * speed) % 140
    for gx in range(-140, W + 140, 140):
        d.line([gx - off, y + 30, gx - off + 60, y + 30], fill=col, width=5)


def blink_eyes(t, base="open"):
    return "closed" if (t % 3.4) < 0.11 else base


# ---------------- props for the compare template ----------------
def pose_lib(name, t, s):
    """Returns P, dy, look, eyes, extra-draw callback."""
    if name == "walk":
        P, b = walk(t)
        return P, -b * 6 * s, 1, blink_eyes(t), None
    if name == "run":
        P, b = walk(t, 12, 42, 14, 55)

        def lines(d, info, hip):
            for i in range(3):
                yy = hip[1] - 200 * s + i * 60 * s
                xx = hip[0] - 170 * s - (t * 700 + i * 50) % 90
                d.line([xx, yy, xx - 90 * s, yy], fill=MUTED, width=6)
        return P, -b * 16 * s, 1, blink_eyes(t), lines
    if name == "phone":
        P = dict(BASE, ra1=28, ra2=118, la1=-10, head=-14)

        def ph(d, info, hip):
            hx, hy = info["hands"]["r"]
            g = 170 + int(60 * (0.5 + 0.5 * math.sin(t * 9)))
            d.rounded_rectangle([hx - 20 * s, hy - 36 * s, hx + 20 * s, hy + 36 * s], 8, fill=(g - 40, g, 255))
        return P, 0, 1, "down", ph
    if name == "read":
        P = dict(BASE, la1=40, la2=62, ra1=50, ra2=56, head=-12)

        def bk(d, info, hip):
            (lx, ly), (rx, ry) = info["hands"]["l"], info["hands"]["r"]
            mx, my = (lx + rx) / 2 + 15 * s, min(ly, ry) - 10 * s
            for sx in (-1, 1):
                d.polygon([(mx, my + 8 * s), (mx + sx * 85 * s, my - 14 * s), (mx + sx * 85 * s, my + 70 * s),
                           (mx, my + 92 * s)], fill=WARM2, outline=SIL)
        return P, 0, 1, "down", bk
    if name == "lift":
        ph_ = (1 + math.sin(t * 4)) / 2
        P = dict(BASE, la1=-(115 + 50 * ph_), la2=-(70 * (1 - ph_)), ra1=115 + 50 * ph_, ra2=70 * (1 - ph_),
                 ll1=-16, rl1=16)

        def bar(d, info, hip):
            (lx, ly), (rx, ry) = info["hands"]["l"], info["hands"]["r"]
            my = (ly + ry) / 2
            d.line([lx - 70 * s, my, rx + 70 * s, my], fill=(90, 96, 108), width=int(10 * s))
            for px in (lx - 55 * s, rx + 55 * s):
                d.rectangle([px - 14 * s, my - 48 * s, px + 14 * s, my + 48 * s], fill=SIL, outline=RIM, width=3)
        return P, 0, 0, "squint" if ph_ < 0.5 else "open", bar
    if name == "sleep":
        P = dict(BASE, head=24, lean=6, la1=-4, ra1=4)

        def z(d, info, hip):
            hx, hy = info["head"]
            for i in range(3):
                ph2 = (t * 0.6 + i / 3) % 1
                d.text((hx + 50 * s + ph2 * 90 * s, hy - 60 * s - ph2 * 200 * s), "z", font=font(int((34 + 14 * i) * s)),
                       fill=MUTED)
        return P, 0, 0, "closed", z
    if name == "sad":
        P = dict(BASE, lean=10, head=-18, la1=-3, la2=0, ra1=3, ra2=0)
        return P, 4 * s, 0, "down", None
    if name == "celebrate":
        wv = 16 * math.sin(t * 10)
        P = dict(BASE, la1=-150 + wv, la2=-10, ra1=150 - wv, ra2=10, ll1=-20, rl1=20)
        return P, -abs(math.sin(t * 6)) * 45 * s, 0, "wide", None
    P = dict(BASE, la1=-14 + 4 * math.sin(t * 2), ra1=14 - 4 * math.sin(t * 2))
    return P, math.sin(t * 3) * 3, 0, blink_eyes(t), None


# ---------------- templates ----------------
def t_door(img, d, t, dur, p):
    u = t / dur
    dx0, dx1, dtop = 770, 920, GROUND - 330
    snap = p.get("snap", True)
    sn_u = 0.6
    stake = (120, GROUND - 120)
    sign(d, 150, GROUND - 230, p["anchor"], 34)
    d.rectangle([110, GROUND - 200, 130, GROUND], fill=SIL, outline=RIM, width=3)
    flash = 0
    if not snap or u < sn_u:
        P, b = walk(t, 9, 32, 26, 20)
        x = 470 + 18 * math.sin(t * 1.4)
        hip = (x, stand_y() - b * 6)
        info = figure(d, hip, P, look=1, eyes=blink_eyes(t, "squint"))
        foot = info["feet"]["l"]
        d.line([foot, stake], fill=RED, width=7)
    else:
        k = (u - sn_u) / (0.88 - sn_u)
        d.line([stake, (250, GROUND - 6)], fill=RED, width=7)
        if k < 1:
            P, b = walk(t, 12, 42, 14, 55)
            x = 470 + (dx0 + 40 - 470) * ease(k)
            hip = (x, stand_y() - b * 14)
            info = figure(d, hip, P, look=1, eyes="wide")
            f = info["feet"]["l"]
            d.line([f, (f[0] - 60, f[1] + 6)], fill=RED, width=7)
        flash = clamp((u - 0.84) / 0.06) * (1 - clamp((u - 0.94) / 0.06))
    # door drawn last so the figure walks into the light
    d.rectangle([dx0 - 10, dtop - 10, dx1 + 10, GROUND], fill=SIL)
    d.rectangle([dx0, dtop, dx1, GROUND], fill=WARM)
    d.rectangle([dx0 + 14, dtop + 14, dx1 - 14, GROUND], fill=WARM2)
    spaced(d, (dx0 + dx1) / 2, dtop - 80, p["goal"], font(50), WARM, 6)
    if flash > 0:
        ov = Image.new("RGB", (W, H), WARM2)
        img.paste(Image.blend(img, ov, flash * 0.8))
    caption(ImageDraw.Draw(img), p["caption"])


def door_bg():
    im = sky(4, mountains=False)
    flat_ground(im)
    glow = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow)
    gd.rectangle([700, GROUND - 400, 990, GROUND], fill=200)
    gd.polygon([(770, GROUND), (920, GROUND), (1080, H), (300, H)], fill=140)
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    return Image.composite(Image.new("RGB", (W, H), (150, 120, 72)), im, glow)


SLOPE = ((-60, 1700), (1140, 1000))


def slope_y(x):
    (x0, y0), (x1, y1) = SLOPE
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)


def boulder_bg():
    im = sky(7)
    d = ImageDraw.Draw(im)
    (x0, y0), (x1, y1) = SLOPE
    d.polygon([(x0, y0), (x1, y1), (x1, H), (x0, H)], fill=(11, 12, 16))
    d.line([(x0, y0), (x1, y1)], fill=(80, 90, 108), width=3)
    return im


def t_boulder(img, d, t, dur, p):
    u = t / dur
    labels = p["labels"]
    for i, lab in enumerate(labels):
        x = 470 + i * (560 / max(1, len(labels) - 1)) if len(labels) > 1 else 700
        y = slope_y(x)
        d.line([(x, y), (x, y - 190)], fill=(30, 34, 42), width=8)
        sign(d, x, y - 210, lab, 32)
    xb = 400 + 170 * u + 14 * math.sin(t * 2.4) - (40 * ease((u - 0.8) / 0.2) if p.get("slip") else 0)
    rb = 125
    cy = slope_y(xb) - rb * 1.08
    d.ellipse([xb - rb - 5, cy - rb - 5, xb + rb + 5, cy + rb + 5], fill=RIM)
    d.ellipse([xb - rb, cy - rb, xb + rb, cy + rb], fill=STONE)
    ang = xb / rb
    for k in range(3):
        a = ang + k * 2.1
        d.line([(xb + 30 * math.cos(a), cy + 30 * math.sin(a)), (xb + 95 * math.cos(a + 0.4), cy + 95 * math.sin(a + 0.4))],
               fill=(36, 39, 46), width=6)
    w = math.sin(t * 3.2)
    P = dict(BASE, lean=40, head=-14, la1=104, la2=-8, ra1=98, ra2=-4,
             ll1=-42 + 14 * w, ll2=8, rl1=12 - 14 * w, rl2=-22)
    hx = xb - rb - 150
    figure(d, (hx, slope_y(hx) - (TH + SH) * 0.86), P, look=1, eyes=blink_eyes(t, "squint"))
    caption(d, p["caption"])


def crowd_bg():
    im = sky(11)
    flat_ground(im)
    return im


def t_crowd(img, d, t, dur, p):
    s = 0.72
    for i in range(7):
        x = (900 + i * 170 - t * 110) % (W + 340) - 170
        P, b = walk(t + i * 0.4, 6, 20, 8, 10)
        P = mirror(dict(P, ra1=28, ra2=118, head=-14))
        hip = (x, stand_y(s) - 70 - b * 4)
        info = figure(d, hip, P, s=s, look=-1, eyes="down", col=(26, 29, 36), rim=(44, 50, 62))
        hx, hy = info["hands"]["l"]
        d.rounded_rectangle([hx - 13, hy - 24, hx + 13, hy + 24], 6, fill=PHONE)
    sign(d, 230, 720, p["crowd"], 32, color=MUTED, outline=MUTED)
    scroll_ground(d, t, 60)
    P, b = walk(t, 7, 28, 2, 14)
    info = figure(d, (640, stand_y() - b * 6), P, look=1, eyes=blink_eyes(t))
    hx, hy = info["head"]
    sign(d, hx, hy - 150, p["you"], 36, color=WARM, outline=WARM)
    d.polygon([(hx - 14, hy - 112), (hx + 14, hy - 112), (hx, hy - 90)], fill=WARM)
    caption(d, p["caption"])


STEP_W, STEP_H, STEP_X = 160, 112, 120


def stairs_bg(n):
    def build():
        im = sky(5)
        flat_ground(im)
        d = ImageDraw.Draw(im)
        top_x = STEP_X + n * STEP_W
        glow = Image.new("L", (W, H), 0)
        ImageDraw.Draw(glow).ellipse([top_x - 260, GROUND - n * STEP_H - 420, top_x + 140, GROUND - n * STEP_H - 20], fill=150)
        glow = glow.filter(ImageFilter.GaussianBlur(70))
        im = Image.composite(Image.new("RGB", (W, H), (190, 160, 100)), im, glow)
        d = ImageDraw.Draw(im)
        for i in range(n):
            x0 = STEP_X + i * STEP_W
            y0 = GROUND - (i + 1) * STEP_H
            d.rectangle([x0, y0, x0 + STEP_W, GROUND], fill=(20, 23, 30), outline=(70, 80, 98), width=3)
        return im
    return build


def t_stairs(img, d, t, dur, p):
    labs = p["labels"]
    n = len(labs)
    for i, lab in enumerate(labs):
        x0 = STEP_X + i * STEP_W
        y0 = GROUND - (i + 1) * STEP_H
        f = font(30)
        spaced(d, x0 + STEP_W / 2, y0 + 36, lab, f, WHITE if i < n - 1 else WARM, 2)
    fx, fy = STEP_X + n * STEP_W - 40, GROUND - n * STEP_H
    d.line([(fx, fy), (fx, fy - 190)], fill=SIL, width=9)
    wv = 10 * math.sin(t * 6)
    d.polygon([(fx, fy - 190), (fx + 110, fy - 160 + wv), (fx, fy - 128)], fill=WARM)
    climb_t = dur * 0.82
    k = clamp(t / climb_t) * (n - 0.5)
    step = int(k)
    frac = k - step
    x = STEP_X + 60 + k * STEP_W
    floor = GROUND - step * STEP_H - (STEP_H * ease((frac - 0.5) * 2) if frac > 0.5 else 0)
    if t < climb_t:
        P, b = walk(t, 8, 30, 8, 18)
        figure(d, (x, floor - (TH + SH) - b * 10), P, look=1, eyes=blink_eyes(t))
    else:
        P, dy, look, eyes, _ = pose_lib("celebrate", t, 1.0)
        figure(d, (x, GROUND - n * STEP_H - (TH + SH) + dy + 12), P, look=0, eyes=eyes)
    caption(d, p["caption"])


def compare_bg():
    im = sky(9, mountains=False)
    d = ImageDraw.Draw(im)
    for top in (430, 1170):
        d.rectangle([40, top, W - 40, top + 690], fill=(16, 18, 24), outline=(60, 68, 84), width=3)
        d.rectangle([60, top + 600, W - 60, top + 690], fill=(10, 11, 15))
        d.line([60, top + 600, W - 60, top + 600], fill=(74, 84, 100), width=3)
    return im


def t_compare(img, d, t, dur, p):
    s = 0.78
    for top, lab, pose_name, tm in ((430, p["a"], p["a_pose"], p.get("a_time")), (1170, p["b"], p["b_pose"], p.get("b_time"))):
        spaced(d, W / 2, top + 30, lab, font(40), WHITE, 5)
        d.line([W / 2 - 160, top + 90, W / 2 + 160, top + 90], fill=MUTED, width=3)
        if tm:
            spaced(d, W - 190, top + 120, tm, font(38), RED, 3)
        P, dy, look, eyes, extra = pose_lib(pose_name, t, s)
        hip = (W / 2, top + 600 - (TH + SH) * s + dy)
        info = figure(d, hip, P, s=s, look=look, eyes=eyes)
        if extra:
            extra(d, info, hip)
    caption(d, p["caption"], y=260)


def t_carry(img, d, t, dur, p):
    u = t / dur
    drop_u = 0.55
    if u < drop_u:
        scroll_ground(d, t, 50)
        P, b = walk(t, 3.2, 16, 34, 40)
        P.update(la1=-150, la2=-35, ra1=-138, ra2=-40, head=-6)
        hip = (560, stand_y() + 25 - b * 3)
        nx, ny = pt(hip, 180 - P["lean"], TORSO)
        cx, cy = nx - 175, ny - 95
        d.ellipse([cx - 175, cy - 145, cx + 175, cy + 145], fill=RIM)
        d.ellipse([cx - 168, cy - 138, cx + 168, cy + 138], fill=STONE)
        info = figure(d, hip, P, look=1, eyes=blink_eyes(t, "squint"))
        d.ellipse([cx - 175, cy - 145, cx + 175, cy + 145], fill=RIM)
        d.ellipse([cx - 168, cy - 138, cx + 168, cy + 138], fill=STONE)
        spaced(d, cx, cy - 20, p["load"], font(34 if len(p["load"]) < 12 else 28), WHITE, 3)
    else:
        k = (u - drop_u) / (1 - drop_u)
        sx, sy = 330, GROUND - 120
        fall = ease(k * 4)
        cy = (stand_y() - 260) + (sy - (stand_y() - 260)) * fall
        d.ellipse([sx - 175, cy - 125, sx + 175, cy + 125], fill=RIM)
        d.ellipse([sx - 168, cy - 118, sx + 168, cy + 118], fill=STONE)
        spaced(d, sx, cy - 20, p["load"], font(34 if len(p["load"]) < 12 else 28), WHITE, 3)
        scroll_ground(d, t, 50 + 600 * ease(k * 2))
        P, b = walk(t, 12, 42, 14, 55)
        x = 560 + 700 * ease((k - 0.25) / 0.75)
        figure(d, (x, stand_y() - b * 14), P, look=1, eyes="wide")
    caption(d, p["caption"])


GAP0, GAP1 = 420, 700


def leap_bg():
    im = sky(13)
    d = ImageDraw.Draw(im)
    d.polygon([(0, GROUND), (GAP0, GROUND), (GAP0 - 40, H), (0, H)], fill=(11, 12, 16))
    d.polygon([(GAP1, GROUND - 40), (W, GROUND - 40), (W, H), (GAP1 + 30, H)], fill=(11, 12, 16))
    d.line([0, GROUND, GAP0, GROUND], fill=(78, 88, 106), width=3)
    d.line([GAP1, GROUND - 40, W, GROUND - 40], fill=(78, 88, 106), width=3)
    return im


def t_leap(img, d, t, dur, p):
    u = t / dur
    sign(d, 190, GROUND - 260, p["from"], 30)
    d.line([(190, GROUND), (190, GROUND - 230)], fill=SIL, width=8)
    sign(d, 900, GROUND - 300, p["to"], 30, color=WARM, outline=WARM)
    d.line([(900, GROUND - 40), (900, GROUND - 270)], fill=SIL, width=8)
    if u < 0.3:
        P = dict(BASE, head=-16, la1=-10 + 3 * math.sin(t * 20), ra1=10)
        figure(d, (300 + 2 * math.sin(t * 25), stand_y()), P, look=1, eyes="down")
    elif u < 0.5:
        k = (u - 0.3) / 0.2
        P, b = walk(t, 12, 42, 14, 55)
        figure(d, (150 + 250 * k, stand_y() - b * 14), P, look=1, eyes="wide")
    elif u < 0.72:
        k = (u - 0.5) / 0.22
        x = 400 + 420 * k
        y = stand_y() - 300 * math.sin(math.pi * k) - 40 * k
        P = dict(BASE, la1=-150, ra1=150, ll1=-40, ll2=70, rl1=30, rl2=-60, lean=10)
        figure(d, (x, y), P, look=1, eyes="wide")
    else:
        P, dy, look, eyes, _ = pose_lib("celebrate", t, 1.0)
        figure(d, (820, stand_y() - 40 + dy), P, eyes=eyes)
    caption(d, p["caption"])


TEMPLATES = {
    "door": (t_door, lambda p: ("door", door_bg)),
    "boulder": (t_boulder, lambda p: ("boulder", boulder_bg)),
    "crowd": (t_crowd, lambda p: ("crowd", crowd_bg)),
    "stairs": (t_stairs, lambda p: (f"stairs{len(p['labels'])}", stairs_bg(len(p["labels"])))),
    "compare": (t_compare, lambda p: ("compare", compare_bg)),
    "carry": (t_carry, lambda p: ("crowd", crowd_bg)),
    "leap": (t_leap, lambda p: ("leap", leap_bg)),
}

# ---------------- audio ----------------
CHORDS = [(110, 220, 261.63, 329.63), (98, 196, 246.94, 293.66), (87.31, 174.61, 220, 261.63),
          (116.54, 233.08, 277.18, 349.23), (103.83, 207.65, 246.94, 311.13)]


def music_filter(dur, seed):
    a, b, c, e = CHORDS[seed % len(CHORDS)]
    expr = (f"0.10*sin(2*PI*{a}*t)*(0.7+0.3*sin(2*PI*0.2*t))"
            f"+0.05*sin(2*PI*{b}*t)"
            f"+0.045*sin(2*PI*{c}*t)*(0.5+0.5*sin(2*PI*0.33*t))"
            f"+0.04*sin(2*PI*{e}*t)*(0.5+0.5*sin(2*PI*0.5*t+1))")
    return (f"aevalsrc='{expr}':s=44100:d={dur:.2f},aecho=0.8:0.8:300|620:0.35|0.25,lowpass=f=2400,"
            f"afade=t=in:d=1.2,afade=t=out:st={max(0.0, dur - 1.5):.2f}:d=1.5")


# ---------------- render ----------------
def render(reel, out_path, seed=0):
    fn, bgf = TEMPLATES[reel["template"]]
    key, builder = bgf(reel)
    base = bg(key, builder)
    dur = float(reel.get("dur", 10))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", music_filter(dur, seed),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fi in range(int(dur * FPS)):
        t = fi / FPS
        img = base.copy()
        d = ImageDraw.Draw(img)
        dust(d, t)
        fn(img, d, t, dur, reel)
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed")
    return dur
