"""Cosy night-room style: navy room, glossy blue-head stickman, line-art props, clean bold sans text.

Drawn onto an nv.Canvas (c.img / c.d), so it works with nv.render. Everything that must survive nv's floor pass
stays above nv.FLOOR (1240); nv paints its own floor + soft reflection below that line.
"""
import glob
import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

import nv

W, H = nv.W, nv.H
RF = 1110          # wall / floor line
FOOT = 1205        # where characters stand
WALL_TOP, WALL_BOT = (12, 18, 40), (26, 38, 78)
FLOOR_C = (14, 20, 44)
LINE = (150, 178, 235)      # line-art outline
LINE_DIM = (70, 92, 150)
NAVY = (20, 32, 70)
NAVY2 = (28, 44, 96)
BLUE = (47, 123, 255)
BLUE_D = (24, 70, 190)
BLUE_L = (130, 185, 255)
BODY = (10, 12, 20)
GREYH = (208, 213, 224)
GREYH_D = (140, 148, 165)
TXT = (232, 236, 246)
TXT_DIM = (170, 180, 205)
RED = (238, 52, 64)
NOTE_COLS = [(250, 214, 92), (120, 220, 230), (250, 160, 190), (150, 230, 150), (250, 180, 110)]


# ---------------- fonts / text ----------------
def _font_path():
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf",
              "C:/Windows/Fonts/segoeuib.ttf"):
        if glob.glob(p):
            return p
    return None


_FP = _font_path()
_fc = {}


def font(size):
    if size not in _fc:
        _fc[size] = ImageFont.truetype(_FP, size) if _FP else ImageFont.load_default()
    return _fc[size]


def text_w(d, s, f, sp=0):
    return sum(d.textlength(ch, font=f) for ch in s) + sp * max(0, len(s) - 1)


def spaced(d, cx, y, s, size, fill, sp=0, shadow=True):
    f = font(size)
    x = cx - text_w(d, s, f, sp) / 2
    for ch in s:
        if shadow:
            d.text((x + 2, y + 3), ch, font=f, fill=(4, 6, 14))
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + sp


def wrap(d, s, size, max_w, sp=0):
    f = font(size)
    words, lines, cur = s.split(), [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if cur and text_w(d, cand, f, sp) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def block(d, s, cx, y, size, fill, sp=2, max_w=920, gap=1.3):
    """Wrapped centred uppercase text; returns y below the block."""
    for i, ln in enumerate(wrap(d, s.upper(), size, max_w, sp)):
        spaced(d, cx, y + i * size * gap, ln, size, fill, sp)
    return y + len(wrap(d, s.upper(), size, max_w, sp)) * size * gap


def bubble(d, s, x, y, size=30):
    """White rounded speech bubble, tail tip at (x, y)."""
    s = s.upper()
    f = font(size)
    tw = text_w(d, s, f, 1)
    bw, bh = tw + 44, size + 30
    bx, by = x - bw / 2, y - bh - 22
    d.rounded_rectangle([bx + 3, by + 4, bx + bw + 3, by + bh + 4], 20, fill=(4, 6, 14))
    d.rounded_rectangle([bx, by, bx + bw, by + bh], 20, fill=(246, 248, 252))
    d.polygon([(x - 12, by + bh - 1), (x + 12, by + bh - 1), (x + 2, y)], fill=(246, 248, 252))
    xx = bx + 22
    for ch in s:
        d.text((xx, by + 12), ch, font=f, fill=(10, 12, 20))
        xx += d.textlength(ch, font=f) + 1


def age_counter(d, age, t_since_change, y=330):
    """'AGE n' label; the number pops when it changes."""
    k = nv.clamp(t_since_change / 0.35)
    size = int(46 + 26 * (1 - nv.ease(k)))
    col = nv.mix(BLUE_L, TXT_DIM, nv.ease(k))
    f = font(46)
    lab = "AGE "
    lw = text_w(d, lab, f, 6)
    nw = text_w(d, str(age), font(size), 6)
    x0 = W / 2 - (lw + nw) / 2
    spaced(d, x0 + lw / 2, y, lab, 46, TXT_DIM, 6)
    spaced(d, x0 + lw + nw / 2, y - (size - 46) / 2, str(age), size, col, 6)


def time_counter(d, text, y):
    spaced(d, W / 2, y, text, 54, RED, 2)


# ---------------- glow helper ----------------
_gc = {}


def glow(img, x, y, rx, ry, color, strength=0.6):
    key = (int(rx), int(ry), int(strength * 100))
    if key not in _gc:
        m = Image.new("L", (int(rx * 4), int(ry * 4)), 0)
        ImageDraw.Draw(m).ellipse([rx, ry, rx * 3, ry * 3], fill=int(255 * strength))
        _gc[key] = m.filter(ImageFilter.GaussianBlur(max(rx, ry) * 0.5))
    m = _gc[key]
    img.paste(color, (int(x - rx * 2), int(y - ry * 2)), m)


# ---------------- room ----------------
_room_cache = {}


def room_base():
    """Static room (wall, floor, window frame, door frame, desk, wall clock face)."""
    if "base" in _room_cache:
        return _room_cache["base"]
    img = Image.new("RGB", (W, H), (6, 9, 20))
    g = Image.linear_gradient("L").resize((W, RF))
    wall = Image.merge("RGB", [g.point(lambda v, i=i: int(WALL_TOP[i] + (WALL_BOT[i] - WALL_TOP[i]) * v / 255))
                               for i in range(3)])
    img.paste(wall, (0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, RF, W, H], fill=FLOOR_C)
    # perspective floor lines
    for i in range(-6, 7):
        d.line([(W / 2 + i * 60, RF), (W / 2 + i * 260, H)], fill=(20, 28, 58), width=2)
    d.line([(0, RF), (W, RF)], fill=(110, 140, 210), width=3)
    glow(img, W / 2, RF, 560, 26, (70, 100, 190), 0.35)
    # window
    wx0, wy0, wx1, wy1 = 380, 640, 680, 900
    d.rectangle([wx0, wy0, wx1, wy1], fill=(8, 14, 36), outline=LINE, width=4)
    import random as _r
    rr = _r.Random(5)
    for _ in range(40):
        x, y = rr.uniform(wx0 + 8, wx1 - 8), rr.uniform(wy0 + 8, wy1 - 8)
        d.ellipse([x - 1.6, y - 1.6, x + 1.6, y + 1.6], fill=(200, 210, 240))
    d.line([((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], fill=LINE_DIM, width=3)
    mx, my = wx1 - 70, wy0 + 60
    d.ellipse([mx - 26, my - 26, mx + 26, my + 26], fill=(235, 238, 250))
    d.ellipse([mx - 14, my - 32, mx + 34, my + 18], fill=(8, 14, 36))
    d.rectangle([wx0 - 16, wy1, wx1 + 16, wy1 + 12], fill=NAVY2, outline=LINE_DIM, width=2)
    # door frame (door leaf drawn per frame)
    d.rectangle([780, 620, 990, RF], fill=(6, 10, 26), outline=LINE, width=4)
    # desk
    d.rectangle([0, 1000, 330, 1018], fill=NAVY2, outline=LINE, width=3)
    d.rectangle([20, 1018, 150, 1188], fill=NAVY, outline=LINE_DIM, width=3)
    d.line([(55, 1100), (115, 1100)], fill=LINE, width=4)
    d.line([(310, 1018), (310, 1192)], fill=LINE_DIM, width=6)
    _room_cache["base"] = img
    return img


def clock(d, cx, cy, r, t, speed=1.0):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(222, 228, 240), outline=(120, 130, 160), width=3)
    for i in range(12):
        a = i * math.pi / 6
        d.line([(cx + math.sin(a) * r * 0.78, cy - math.cos(a) * r * 0.78),
                (cx + math.sin(a) * r * 0.9, cy - math.cos(a) * r * 0.9)], fill=(40, 44, 60), width=3)
    am = t * speed * 2 * math.pi
    ah = am / 12
    d.line([(cx, cy), (cx + math.sin(ah) * r * 0.5, cy - math.cos(ah) * r * 0.5)], fill=(20, 24, 40), width=5)
    d.line([(cx, cy), (cx + math.sin(am) * r * 0.75, cy - math.cos(am) * r * 0.75)], fill=BLUE_D, width=3)


def door(img, d, k_open):
    """Door leaf; k_open 0..1 swings it open and spills light."""
    x0, y0, x1, y1 = 790, 630, 980, RF
    if k_open > 0:
        light = nv.mix((6, 10, 26), (235, 242, 255), k_open)
        d.rectangle([x0, y0, x1, y1], fill=light)
        glow(img, (x0 + x1) / 2, (y0 + y1) / 2, 160, 300, (190, 210, 255), 0.45 * k_open)
        # light spill on the floor
        d.polygon([(x0, RF), (x1, RF), (x1 + 140 * k_open, FOOT + 30), (x0 - 120 * k_open, FOOT + 30)],
                  fill=nv.mix(FLOOR_C, (120, 150, 230), 0.45 * k_open))
    wd = (x1 - x0) * (1 - 0.82 * k_open)
    d.rectangle([x0, y0, x0 + wd, y1], fill=NAVY, outline=LINE, width=3)
    if wd > 60:
        d.rectangle([x0 + 22, y0 + 30, x0 + wd - 22, y0 + 210], outline=LINE_DIM, width=2)
        d.rectangle([x0 + 22, y0 + 250, x0 + wd - 22, y1 - 40], outline=LINE_DIM, width=2)
        d.ellipse([x0 + wd - 34, 880, x0 + wd - 20, 894], fill=LINE)


def desk_props(img, d, t, lamp=True, laptop=True, notes=3, books=0, chart=1, trophies=0, coins=0):
    if lamp:
        glow(img, 60, 950, 170, 120, (170, 200, 255), 0.5)
        d.polygon([(40, 900), (90, 900), (210, 1000), (-40, 1000)], fill=(60, 80, 130))
        d.line([(50, 1000), (60, 900)], fill=LINE, width=4)
        d.polygon([(30, 880), (95, 880), (80, 905), (45, 905)], fill=(225, 232, 250))
    if laptop:
        d.polygon([(150, 996), (262, 996), (268, 1002), (146, 1002)], fill=(200, 210, 230))
        d.line([(170, 996), (205, 900)], fill=(200, 210, 230), width=5)
        glow(img, 190, 950, 45, 40, (150, 190, 255), 0.35 + 0.1 * math.sin(t * 6))
    for i in range(notes):
        col = NOTE_COLS[i % len(NOTE_COLS)]
        x = 30 + (i % 4) * 62 + (i // 4) * 18
        y = 760 + (i // 4) * 62 + (i % 2) * 12
        d.rectangle([x, y, x + 50, y + 46], fill=col)
        d.line([(x + 9, y + 16), (x + 41, y + 16)], fill=nv.mix(col, (0, 0, 0), 0.4), width=2)
        d.line([(x + 9, y + 28), (x + 34, y + 28)], fill=nv.mix(col, (0, 0, 0), 0.4), width=2)
    for i in range(books):
        cols = [(230, 90, 90), (90, 170, 240), (250, 200, 80), (130, 210, 130), (190, 130, 230)]
        y = 1000 - 14 * (i + 1)
        x = 268 - (i % 2) * 6
        d.rectangle([x, y, x + 56, y + 13], fill=cols[i % 5], outline=(10, 14, 30), width=1)
    # progress chart on the wall
    cx0, cy0 = 700, 700
    d.rectangle([cx0, cy0, cx0 + 70, cy0 + 80], fill=(10, 16, 40), outline=LINE_DIM, width=3)
    for i in range(min(chart, 4)):
        h = 14 + i * 14
        d.rectangle([cx0 + 10 + i * 14, cy0 + 70 - h, cx0 + 20 + i * 14, cy0 + 70], fill=BLUE)
    # trophies on a small shelf
    if trophies:
        d.rectangle([380, 935, 560, 945], fill=NAVY2, outline=LINE_DIM, width=2)
        for i in range(trophies):
            x = 405 + i * 48
            d.polygon([(x - 14, 905), (x + 14, 905), (x + 6, 922), (x - 6, 922)], fill=(250, 200, 70))
            d.rectangle([x - 3, 922, x + 3, 930], fill=(250, 200, 70))
            d.rectangle([x - 10, 930, x + 10, 935], fill=(200, 150, 50))
    if coins:
        x0 = 230
        d.rectangle([x0, 940, x0 + 36, 1000], outline=LINE, width=3)
        lvl = min(1.0, coins / 10)
        d.rectangle([x0 + 3, 1000 - 57 * lvl, x0 + 33, 997], fill=(250, 200, 70))


def rug(img, d):
    glow(img, 560, 1202, 430, 34, (40, 90, 220), 0.35)
    d.ellipse([140, 1170, 980, 1236], outline=(70, 130, 255), width=4)


# ---------------- characters ----------------
HEAD_R, TORSO, UA, FA, TH, SH, LIMB = 60, 138, 80, 76, 102, 98, 24


def chair(d, hip, s, facing=-1):
    """Office chair under a sitting character (facing -1 = towards the desk on the left)."""
    hx, hy = hip
    seat_y = hy + 16 * s
    d.rounded_rectangle([hx - 70 * s, seat_y, hx + 70 * s, seat_y + 18 * s], 8, fill=NAVY2, outline=LINE_DIM, width=2)
    bx = hx - facing * 70 * s
    d.rounded_rectangle([bx - 12 * s, seat_y - 170 * s, bx + 12 * s, seat_y + 10], 10, fill=NAVY2, outline=LINE_DIM,
                        width=2)
    d.line([(hx, seat_y + 18 * s), (hx, FOOT - 8)], fill=LINE_DIM, width=6)
    d.line([(hx - 55 * s, FOOT - 6), (hx + 55 * s, FOOT - 6)], fill=LINE_DIM, width=5)


def figure(img, d, x, P, s=1.0, foot_y=FOOT, head="blue", facing=1, dy=0.0, eyes="open"):
    """Black-body stickman with a big glossy head (blue = main character, grey = others)."""
    if facing < 0:
        P = nv.mirror(P)
    lean = P.get("lean", 0)
    hip = (0.0, 0.0)
    neck = nv.pt(hip, 180 - lean, TORSO * s)
    sh = nv.pt(hip, 180 - lean, (TORSO - 14) * s)
    head_c = nv.pt(neck, 180 - lean - P.get("head", 0), (HEAD_R + 4) * s)
    legs, arms = [], []
    hands, feet = {}, {}
    for k in "lr":
        a1, a2 = P[k + "l1"], P.get(k + "l2", 0)
        kn = nv.pt(hip, a1, TH * s)
        ft = nv.pt(kn, a1 + a2, SH * s)
        legs.append([hip, kn, ft])
        feet[k] = ft
    for k in "lr":
        a1, a2 = P[k + "a1"], P.get(k + "a2", 0)
        el = nv.pt(sh, a1, UA * s)
        hd = nv.pt(el, a1 + a2, FA * s)
        arms.append((k, [sh, el, hd]))
        hands[k] = hd
    low = max(p[1] for ch in legs + [a for _, a in arms] for p in ch)
    ox, oy = x, foot_y - low - dy

    def T(p):
        return (p[0] + ox, p[1] + oy)

    w = max(6, int(LIMB * s))
    rim = (175, 200, 250)
    # far arm (behind body) first
    far = arms[0] if facing > 0 else arms[1]
    near = arms[1] if facing > 0 else arms[0]

    def limb(chain, col, width, rim_col):
        pts = [T(p) for p in chain]
        d.line(pts, fill=rim_col, width=width + 5, joint="curve")
        for p in pts:
            d.ellipse([p[0] - (width + 5) / 2, p[1] - (width + 5) / 2, p[0] + (width + 5) / 2, p[1] + (width + 5) / 2],
                      fill=rim_col)
        d.line(pts, fill=col, width=width, joint="curve")
        for p in pts:
            d.ellipse([p[0] - width / 2, p[1] - width / 2, p[0] + width / 2, p[1] + width / 2], fill=col)

    limb(far[1], BODY, w, nv.mix(rim, BODY, 0.45))
    for ch in legs:
        limb(ch, BODY, w + 2, rim)
    limb([hip, neck], BODY, int(w * 1.5), rim)
    # blue shirt panel on the torso
    tb = [T(nv.pt(hip, 180 - lean, TORSO * s * 0.15)), T(nv.pt(hip, 180 - lean, TORSO * s * 0.85))]
    shirt = BLUE if head == "blue" else (120, 128, 150)
    d.line(tb, fill=shirt, width=int(w * 1.05))
    # near arm, blue-lit upper arm
    ch = near[1]
    limb([ch[1], ch[2]], BODY, w, rim)
    limb([ch[0], ch[1]], shirt, int(w * 1.15), rim)
    # head
    hx, hy = T(head_c)
    r = HEAD_R * s
    if head == "blue":
        base, dark, hl = BLUE, BLUE_D, (190, 220, 255)
    else:
        base, dark, hl = GREYH, GREYH_D, (255, 255, 255)
    d.ellipse([hx - r - 3, hy - r - 3, hx + r + 3, hy + r + 3], fill=(225, 235, 255))
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=dark)
    d.ellipse([hx - r * 0.96, hy - r * 0.98, hx + r * 0.88, hy + r * 0.86], fill=base)
    d.ellipse([hx - r * 0.62, hy - r * 0.78, hx - r * 0.08, hy - r * 0.42], fill=hl)
    ex = hx + facing * r * 0.32
    for sx in (-1, 1):
        cx, cy = ex + sx * r * 0.22, hy + r * 0.05
        if eyes == "closed":
            d.line([(cx - r * 0.1, cy), (cx + r * 0.1, cy)], fill=(10, 14, 30), width=max(2, int(3 * s)))
            continue
        d.ellipse([cx - r * 0.12, cy - r * 0.16, cx + r * 0.12, cy + r * 0.16], fill=(250, 250, 255))
        py = cy + (r * 0.05 if eyes == "down" else 0)
        d.ellipse([cx + facing * r * 0.02 - r * 0.06, py - r * 0.06, cx + facing * r * 0.02 + r * 0.06, py + r * 0.06],
                  fill=(10, 14, 30))
    return {"head": (hx, hy), "hip": T(hip), "neck": T(neck), "hands": {k: T(v) for k, v in hands.items()},
            "feet": {k: T(v) for k, v in feet.items()}, "r": r}


# poses (facing right; figure(facing=-1) mirrors them)
def sit_work(t):
    k = math.sin(t * 9)
    return dict(nv.BASE, lean=14, head=10, ll1=88, ll2=-88, rl1=82, rl2=-84,
                la1=62 + 4 * k, la2=40, ra1=70 - 4 * k, ra2=34)


def sit_read(t):
    return dict(nv.BASE, lean=8, head=18, ll1=88, ll2=-88, rl1=82, rl2=-84, la1=40, la2=80, ra1=46, ra2=76)


def sit_sleep(t):
    return dict(nv.BASE, lean=58, head=30, ll1=88, ll2=-88, rl1=82, rl2=-84, la1=80, la2=40, ra1=86, ra2=36)


def stand_phone(t):
    return dict(nv.BASE, head=-26, lean=4, ra1=34, ra2=118, la1=-8)


def kick(t):
    k = math.sin(t * 5)
    return dict(nv.BASE, ll1=-6, rl1=28 + 30 * max(0, k), rl2=-10, la1=-30, ra1=30, lean=-4)


def curls(t):
    k = 0.5 + 0.5 * math.sin(t * 5)
    return dict(nv.BASE, la1=-10, la2=-(30 + 110 * k), ra1=10, ra2=30 + 110 * k)


def lie_floor(t):
    return dict(nv.BASE, lean=-88, head=88, ll1=-92, rl1=-88, la1=-60, ra1=-100)


def game(t):
    k = math.sin(t * 12)
    return dict(nv.BASE, head=-14, ll1=-10, rl1=10, la1=40 + 3 * k, la2=70, ra1=46 - 3 * k, ra2=66)


# ---------------- extras for split / table layouts ----------------
def no_reflection(c):
    """Swap nv's glossy-floor pass for this canvas only (layouts that draw content below nv.FLOOR)."""
    def _finish(t=0.0, handle_xy=None):
        img = c.img
        for item in c.ui:
            if item[0] != "__bubble__":
                c._draw_text(*item)
        small = img.resize((W // 4, H // 4)).filter(ImageFilter.GaussianBlur(5))
        small = small.point(lambda v: int(max(0, v - 80) * 1.5))
        return ImageChops.screen(img, small.resize((W, H), Image.BILINEAR))
    c.finish = _finish


def navy_fill(img):
    g = Image.linear_gradient("L").resize((W, H))
    top, bot = (6, 9, 22), (14, 22, 50)
    img.paste(Image.merge("RGB", [g.point(lambda v, i=i: int(top[i] + (bot[i] - top[i]) * v / 255))
                                  for i in range(3)]), (0, 0))


def bed(img, d, x0=400, x1=760):
    """Bed on the floor; returns the y the sleeper lies on."""
    top = FOOT - 70
    d.rounded_rectangle([x0, top, x1, FOOT - 6], 14, fill=NAVY2, outline=LINE_DIM, width=3)
    d.rounded_rectangle([x0 + 6, top - 18, x1 - 6, top + 16], 12, fill=(40, 90, 210), outline=LINE, width=2)
    d.rounded_rectangle([x0 + 14, top - 34, x0 + 110, top - 6], 12, fill=(220, 228, 245))
    d.rectangle([x0, top - 120, x0 + 18, FOOT - 6], fill=NAVY2, outline=LINE_DIM, width=2)
    return top - 10


def mic(d, x, y, s=1.0):
    d.line([(x, y), (x + 8 * s, y + 46 * s)], fill=(60, 66, 84), width=max(3, int(7 * s)))
    d.ellipse([x - 13 * s, y - 16 * s, x + 13 * s, y + 10 * s], fill=(200, 205, 220), outline=(40, 44, 60), width=2)


def guitar(d, x, y, s=1.0):
    d.line([(x - 10 * s, y + 10 * s), (x + 120 * s, y - 70 * s)], fill=(90, 60, 30), width=max(4, int(10 * s)))
    d.ellipse([x - 70 * s, y - 20 * s, x + 10 * s, y + 52 * s], fill=(200, 120, 50), outline=(80, 40, 10), width=3)
    d.ellipse([x - 50 * s, y - 2 * s, x - 6 * s, y + 38 * s], fill=(160, 90, 30))
    d.ellipse([x - 38 * s, y + 6 * s, x - 18 * s, y + 26 * s], fill=(30, 20, 10))


def notebook(d, x, y, s=1.0):
    d.rectangle([x - 34 * s, y - 6 * s, x + 34 * s, y + 6 * s], fill=(245, 242, 230), outline=(40, 44, 70), width=2)
    d.line([(x, y - 6 * s), (x, y + 6 * s)], fill=(40, 44, 70), width=2)


def left_label(d, s, x, y, size=30, fill=TXT):
    f = font(size)
    xx = x
    for ch in s.upper():
        d.text((xx + 2, y + 3), ch, font=f, fill=(0, 0, 0))
        d.text((xx, y), ch, font=f, fill=fill)
        xx += d.textlength(ch, font=f) + 2
