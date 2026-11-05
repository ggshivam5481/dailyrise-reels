"""Small coloured vector props for the minimal reels (drawn with PIL on an nv.Canvas).

Every prop is placed by its BOTTOM-CENTRE (x, y) and a size factor s, so props sit on floors / hands easily.
`pop(t, t0)` gives a pop-in scale (0 before t0, overshoot then settle) for animated appearance.
"""
import math

import nv
from nv import GOLD, GOLD2, RED, clamp

GREEN = (60, 190, 110)
GREEN2 = (40, 140, 80)
BLUE = (80, 150, 255)
SCREEN = (150, 200, 255)
PINK = (240, 130, 170)
ORANGE = (255, 140, 40)
YELLOW = (255, 220, 90)
BROWN = (120, 80, 50)
STEEL = (180, 184, 192)
DARK = (40, 42, 48)
BOOKS = [(220, 70, 70), (70, 130, 230), (240, 190, 60), (90, 190, 120), (170, 100, 210), (240, 140, 60)]


def pop(t, t0, dur=0.28):
    """Pop-in scale: 0 before t0, overshoots to ~1.18, settles at 1."""
    if t < t0:
        return 0.0
    k = (t - t0) / dur
    if k >= 1:
        return 1.0
    return math.sin(k * math.pi * 0.5) * (1 + 0.18 * math.sin(k * math.pi))


def T():
    th = getattr(nv, "T", None)
    if isinstance(th, dict):
        return th
    return {"accent": (120, 200, 255), "accent2": (255, 120, 180), "spot": (255, 255, 255), "particle": (200, 200, 200)}


def _r(x, y, w, h):
    return [x - w / 2, y - h, x + w / 2, y]


# ---------------- money ----------------
def coin(c, x, y, s=1.0, spin=0.0):
    w = 46 * s * max(0.15, abs(math.cos(spin)))
    h = 46 * s
    c.d.ellipse([x - w / 2, y - h, x + w / 2, y], fill=(200, 150, 40))
    c.d.ellipse([x - w / 2 + 3 * s, y - h + 3 * s, x + w / 2 - 3 * s, y - 3 * s], fill=GOLD)
    if w > 20 * s:
        c.d.text((x - 5 * s, y - h * 0.75), "$", fill=(200, 150, 40), font=nv._font(max(8, int(22 * s))))


def coin_stack(c, x, y, n, s=1.0):
    for i in range(n):
        cy = y - i * 11 * s
        c.d.ellipse([x - 30 * s, cy - 14 * s, x + 30 * s, cy], fill=(190, 140, 36))
        c.d.ellipse([x - 30 * s, cy - 16 * s, x + 30 * s, cy - 3 * s], fill=GOLD if i % 2 else GOLD2)


def money_bag(c, x, y, s=1.0, fill=1.0):
    s = s * (0.6 + 0.4 * fill)
    c.d.ellipse([x - 55 * s, y - 100 * s, x + 55 * s, y], fill=(150, 110, 60))
    c.d.polygon([(x - 18 * s, y - 96 * s), (x + 18 * s, y - 96 * s), (x + 28 * s, y - 128 * s),
                 (x - 28 * s, y - 128 * s)], fill=(150, 110, 60))
    c.d.line([(x - 20 * s, y - 100 * s), (x + 20 * s, y - 100 * s)], fill=(90, 60, 30), width=max(2, int(5 * s)))
    c.d.text((x - 12 * s, y - 72 * s), "$", fill=GOLD, font=nv._font(max(8, int(44 * s))))


def cash(c, x, y, s=1.0, ang=0.0):
    w, h = 80 * s, 38 * s
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    ca, sa = math.cos(ang), math.sin(ang)
    P = [(x + px * ca - py * sa, y - h / 2 + px * sa + py * ca) for px, py in pts]
    c.d.polygon(P, fill=GREEN)
    c.d.ellipse([x - 9 * s, y - h / 2 - 9 * s, x + 9 * s, y - h / 2 + 9 * s], fill=GREEN2)


def shop_bag(c, x, y, s=1.0, col=None):
    col = col or T()["accent2"]
    c.d.rectangle(_r(x, y, 70 * s, 80 * s), fill=col)
    c.d.arc([x - 20 * s, y - 104 * s, x + 20 * s, y - 64 * s], 180, 360, fill=col, width=max(2, int(5 * s)))


# ---------------- tech ----------------
def phone(c, x, y, s=1.0, t=0.0, glow=True, badge=0):
    w, h = 40 * s, 72 * s
    c.d.rounded_rectangle(_r(x, y, w, h), int(8 * s), fill=DARK)
    flick = 0.85 + 0.15 * math.sin(t * 13)
    scr = nv.mix((40, 60, 90), SCREEN, flick)
    c.d.rounded_rectangle([x - w / 2 + 4 * s, y - h + 6 * s, x + w / 2 - 4 * s, y - 6 * s], int(5 * s), fill=scr)
    if glow:
        c.glow(x, y - h / 2, int(60 * s), SCREEN, 0.4)
    if badge:
        c.d.ellipse([x + w / 2 - 12 * s, y - h - 10 * s, x + w / 2 + 12 * s, y - h + 14 * s], fill=RED)
        c.d.text((x + w / 2 - 6 * s, y - h - 7 * s), str(min(badge, 99)), fill=(255, 255, 255),
                 font=nv._font(max(8, int(16 * s))))


def notif(c, x, y, s=1.0, txt="NEW"):
    w, h = 120 * s, 40 * s
    c.d.rounded_rectangle(_r(x, y, w, h), int(10 * s), fill=(235, 238, 245))
    c.d.ellipse([x - w / 2 + 8 * s, y - h + 8 * s, x - w / 2 + 32 * s, y - 8 * s], fill=RED)
    c.img.paste((30, 30, 34), (int(x - w / 2 + 40 * s), int(y - h + 12 * s)), nv.text_mask(txt, max(10, int(16 * s))))


def laptop(c, x, y, s=1.0, t=0.0, code=True):
    c.d.polygon([(x - 80 * s, y), (x + 80 * s, y), (x + 66 * s, y - 12 * s), (x - 66 * s, y - 12 * s)], fill=STEEL)
    c.d.rectangle([x - 62 * s, y - 100 * s, x + 62 * s, y - 12 * s], fill=DARK)
    c.d.rectangle([x - 56 * s, y - 94 * s, x + 56 * s, y - 18 * s], fill=(25, 40, 60))
    if code:
        acc = T()["accent"]
        for i in range(5):
            ln = (0.3 + 0.6 * ((i * 37 + int(t * 6)) % 10) / 10) * 90 * s
            yy = y - 86 * s + i * 13 * s
            c.d.line([(x - 48 * s, yy), (x - 48 * s + ln, yy)], fill=acc if i % 2 else GREEN, width=max(2, int(4 * s)))
    c.glow(x, y - 56 * s, int(70 * s), SCREEN, 0.25)


def controller(c, x, y, s=1.0):
    c.d.rounded_rectangle(_r(x, y, 90 * s, 44 * s), int(20 * s), fill=(60, 60, 70))
    c.d.rectangle([x - 32 * s, y - 26 * s, x - 14 * s, y - 20 * s], fill=(200, 200, 210))
    c.d.rectangle([x - 26 * s, y - 32 * s, x - 20 * s, y - 14 * s], fill=(200, 200, 210))
    for dx, col in ((18, RED), (30, BLUE)):
        c.d.ellipse([x + (dx - 5) * s, y - 28 * s, x + (dx + 5) * s, y - 18 * s], fill=col)


def tv(c, x, y, s=1.0, t=0.0):
    c.d.rectangle(_r(x, y - 20 * s, 150 * s, 100 * s), fill=DARK)
    k = 0.5 + 0.5 * math.sin(t * 9)
    c.d.rectangle([x - 68 * s, y - 114 * s, x + 68 * s, y - 26 * s], fill=nv.mix((60, 40, 120), (60, 140, 200), k))
    c.d.line([(x - 20 * s, y), (x, y - 20 * s), (x + 20 * s, y)], fill=STEEL, width=max(2, int(4 * s)))
    c.glow(x, y - 70 * s, int(110 * s), (120, 120, 255), 0.25)


# ---------------- fitness / home ----------------
def dumbbell(c, x, y, s=1.0, col=None):
    col = col or T()["accent"]
    c.d.rectangle([x - 40 * s, y - 14 * s, x + 40 * s, y - 8 * s], fill=STEEL)
    for dx in (-40, 32):
        c.d.rounded_rectangle([x + dx * s, y - 26 * s, x + (dx + 10) * s, y + 4 * s], int(3 * s), fill=col)


def barbell(c, hand_l, hand_r, s=1.0, col=None):
    col = col or T()["accent"]
    (lx, ly), (rx, ry) = hand_l, hand_r
    my = (ly + ry) / 2
    c.d.line([lx - 55 * s, my, rx + 55 * s, my], fill=STEEL, width=max(3, int(7 * s)))
    for px_ in (lx - 45 * s, rx + 45 * s):
        c.d.rounded_rectangle([px_ - 11 * s, my - 36 * s, px_ + 11 * s, my + 36 * s], int(4 * s), fill=col)


def couch(c, x, y, s=1.0, col=(110, 60, 70)):
    dark = nv.mix(col, (0, 0, 0), 0.3)
    c.d.rounded_rectangle([x - 150 * s, y - 120 * s, x + 150 * s, y - 50 * s], int(16 * s), fill=dark)
    c.d.rounded_rectangle([x - 150 * s, y - 70 * s, x + 150 * s, y - 14 * s], int(12 * s), fill=col)
    for dx in (-160, 130):
        c.d.rounded_rectangle([x + dx * s, y - 95 * s, x + (dx + 30) * s, y - 14 * s], int(10 * s), fill=dark)
    c.d.rectangle([x - 140 * s, y - 14 * s, x - 128 * s, y], fill=(40, 30, 30))
    c.d.rectangle([x + 128 * s, y - 14 * s, x + 140 * s, y], fill=(40, 30, 30))


def bed(c, x, y, s=1.0):
    c.d.rectangle([x - 170 * s, y - 50 * s, x + 170 * s, y - 14 * s], fill=(70, 80, 120))
    c.d.rectangle([x - 170 * s, y - 90 * s, x - 150 * s, y], fill=(90, 70, 50))
    c.d.rectangle([x + 150 * s, y - 70 * s, x + 170 * s, y], fill=(90, 70, 50))
    c.d.rounded_rectangle([x - 145 * s, y - 70 * s, x - 90 * s, y - 48 * s], int(8 * s), fill=(230, 230, 240))


def pizza(c, x, y, s=1.0):
    c.d.polygon([(x - 40 * s, y - 50 * s), (x + 40 * s, y - 50 * s), (x, y)], fill=(240, 190, 80))
    c.d.polygon([(x - 40 * s, y - 50 * s), (x + 40 * s, y - 50 * s), (x + 36 * s, y - 60 * s),
                 (x - 36 * s, y - 60 * s)], fill=(190, 120, 60))
    for dx, dy in ((-14, -38), (10, -30), (-2, -16)):
        c.d.ellipse([x + (dx - 6) * s, y + (dy - 6) * s, x + (dx + 6) * s, y + (dy + 6) * s], fill=(200, 50, 40))


def soda(c, x, y, s=1.0):
    c.d.rounded_rectangle(_r(x, y, 34 * s, 64 * s), int(6 * s), fill=RED)
    c.d.rectangle([x - 17 * s, y - 44 * s, x + 17 * s, y - 34 * s], fill=(240, 240, 240))


def salad(c, x, y, s=1.0):
    c.d.chord([x - 46 * s, y - 50 * s, x + 46 * s, y + 10 * s], 0, 180, fill=(230, 230, 236))
    for dx, col in ((-24, GREEN), (0, (120, 210, 90)), (22, GREEN2), (-10, (230, 80, 70)), (12, ORANGE)):
        c.d.ellipse([x + (dx - 14) * s, y - 44 * s, x + (dx + 14) * s, y - 20 * s], fill=col)


def water_bottle(c, x, y, s=1.0):
    c.d.rounded_rectangle(_r(x, y, 30 * s, 80 * s), int(8 * s), fill=(110, 180, 255))
    c.d.rectangle([x - 8 * s, y - 92 * s, x + 8 * s, y - 78 * s], fill=(60, 120, 220))


# ---------------- learning / mind ----------------
def book(c, x, y, s=1.0, col=None, w=90, h=18):
    col = col or BOOKS[0]
    c.d.rectangle(_r(x, y, w * s, h * s), fill=col)
    c.d.rectangle([x + (w / 2 - 10) * s, y - h * s + 3 * s, x + (w / 2 - 3) * s, y - 3 * s], fill=(245, 240, 225))


def book_stack(c, x, y, n, s=1.0, seed=0):
    for i in range(n):
        col = BOOKS[(i + seed) % len(BOOKS)]
        off = ((i * 7 + seed) % 5 - 2) * 4 * s
        book(c, x + off, y - i * 19 * s, s, col)


def open_book(c, x, y, s=1.0, t=0.0):
    c.d.polygon([(x, y - 6 * s), (x - 60 * s, y - 20 * s), (x - 60 * s, y - 64 * s), (x, y - 50 * s)],
                fill=(250, 245, 230))
    c.d.polygon([(x, y - 6 * s), (x + 60 * s, y - 20 * s), (x + 60 * s, y - 64 * s), (x, y - 50 * s)],
                fill=(235, 228, 210))
    flip = (t * 0.8) % 1
    if flip < 0.4:
        k = flip / 0.4
        px = x + 60 * s * math.cos(k * math.pi)
        c.d.polygon([(x, y - 6 * s), (px, y - 20 * s), (px, y - 64 * s), (x, y - 50 * s)], fill=(255, 252, 240))


def bulb(c, x, y, s=1.0, on=1.0):
    col = nv.mix((70, 70, 60), YELLOW, on)
    c.d.ellipse([x - 32 * s, y - 100 * s, x + 32 * s, y - 36 * s], fill=col)
    c.d.rectangle([x - 14 * s, y - 40 * s, x + 14 * s, y - 14 * s], fill=STEEL)
    c.d.rectangle([x - 10 * s, y - 14 * s, x + 10 * s, y], fill=(120, 120, 130))
    if on > 0:
        c.glow(x, y - 68 * s, int(90 * s), YELLOW, 0.55 * on)
        for i in range(8):
            a = i * math.pi / 4
            r0, r1 = 44 * s, (56 + 12 * on) * s
            cx, cy = x, y - 68 * s
            c.d.line([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r1 * math.cos(a), cy + r1 * math.sin(a))],
                     fill=YELLOW, width=max(2, int(4 * s)))


def brain(c, x, y, s=1.0, k=1.0):
    col = nv.mix((110, 90, 100), PINK, k)
    for dx, dy, r in ((-22, -50, 28), (16, -54, 30), (-4, -32, 30), (26, -28, 22), (-28, -24, 20)):
        c.d.ellipse([x + (dx - r) * s, y + (dy - r) * s, x + (dx + r) * s, y + (dy + r) * s], fill=col)
    c.d.line([(x, y - 80 * s), (x, y - 10 * s)], fill=nv.mix(col, (0, 0, 0), 0.3), width=max(2, int(3 * s)))
    if k > 0.5:
        c.glow(x, y - 45 * s, int(80 * s), PINK, 0.4 * (k - 0.5) * 2)


# ---------------- symbols ----------------
def trophy(c, x, y, s=1.0, shine=1.0):
    col = nv.mix((120, 100, 50), GOLD, shine)
    c.d.rectangle(_r(x, y, 70 * s, 14 * s), fill=(110, 80, 40))
    c.d.rectangle(_r(x, y - 14 * s, 16 * s, 30 * s), fill=col)
    c.d.chord([x - 44 * s, y - 120 * s, x + 44 * s, y - 30 * s], 0, 180, fill=col)
    c.d.rectangle([x - 44 * s, y - 120 * s, x + 44 * s, y - 76 * s], fill=col)
    for sx in (-1, 1):
        c.d.arc([x + sx * 44 * s - 18 * s, y - 112 * s, x + sx * 44 * s + 18 * s, y - 76 * s],
                270 if sx > 0 else 90, 90 if sx > 0 else 270, fill=col, width=max(2, int(6 * s)))
    if shine > 0:
        c.glow(x, y - 80 * s, int(100 * s), GOLD, 0.5 * shine)


def heart(c, x, y, s=1.0, beat=0.0, col=RED):
    s = s * (1 + 0.12 * beat)
    c.d.ellipse([x - 40 * s, y - 80 * s, x, y - 40 * s], fill=col)
    c.d.ellipse([x, y - 80 * s, x + 40 * s, y - 40 * s], fill=col)
    c.d.polygon([(x - 39 * s, y - 55 * s), (x + 39 * s, y - 55 * s), (x, y - 6 * s)], fill=col)


def fire(c, x, y, s=1.0, t=0.0):
    for i, (col, k) in enumerate(((ORANGE, 1.0), (YELLOW, 0.62), ((255, 250, 220), 0.3))):
        f = 1 + 0.12 * math.sin(t * 17 + i * 2)
        w, h = 46 * s * k, 96 * s * k * f
        c.d.polygon([(x - w, y), (x + w, y), (x + w * 0.4, y - h * 0.55), (x + 4 * math.sin(t * 9) * s, y - h),
                     (x - w * 0.4, y - h * 0.55)], fill=col)
    c.glow(x, y - 40 * s, int(90 * s), ORANGE, 0.5)


def torch(c, x, y, s=1.0, t=0.0):
    c.d.polygon([(x - 10 * s, y), (x + 10 * s, y), (x + 16 * s, y - 70 * s), (x - 16 * s, y - 70 * s)],
                fill=(120, 80, 50))
    fire(c, x, y - 70 * s, 0.6 * s, t)


def hourglass(c, x, y, s=1.0, k=0.0):
    c.d.rectangle(_r(x, y, 70 * s, 10 * s), fill=BROWN)
    c.d.rectangle(_r(x, y - 110 * s, 70 * s, 10 * s), fill=BROWN)
    c.d.polygon([(x - 28 * s, y - 110 * s), (x + 28 * s, y - 110 * s), (x, y - 60 * s)], fill=(200, 220, 240))
    c.d.polygon([(x - 28 * s, y - 10 * s), (x + 28 * s, y - 10 * s), (x, y - 60 * s)], fill=(200, 220, 240))
    top = 1 - k
    if top > 0:
        c.d.polygon([(x - 26 * s * top, y - 60 * s - 46 * s * top), (x + 26 * s * top, y - 60 * s - 46 * s * top),
                     (x, y - 62 * s)], fill=YELLOW)
    c.d.polygon([(x - 26 * s * k, y - 12 * s), (x + 26 * s * k, y - 12 * s), (x, y - 12 * s - 44 * s * k)],
                fill=YELLOW)
    c.d.line([(x, y - 60 * s), (x, y - 14 * s)], fill=YELLOW, width=max(1, int(2 * s)))


def alarm(c, x, y, s=1.0, t=0.0, ring=False):
    sh = 6 * s * math.sin(t * 60) if ring else 0
    x = x + sh
    c.d.ellipse([x - 40 * s, y - 86 * s, x + 40 * s, y - 6 * s], fill=RED)
    c.d.ellipse([x - 32 * s, y - 78 * s, x + 32 * s, y - 14 * s], fill=(245, 245, 245))
    c.d.line([(x, y - 46 * s), (x, y - 70 * s)], fill=(20, 20, 20), width=max(2, int(4 * s)))
    c.d.line([(x, y - 46 * s), (x + 16 * s, y - 40 * s)], fill=(20, 20, 20), width=max(2, int(4 * s)))
    for sx in (-1, 1):
        c.d.ellipse([x + sx * 34 * s - 14 * s, y - 100 * s, x + sx * 34 * s + 14 * s, y - 76 * s], fill=STEEL)


def calendar(c, x, y, s=1.0, txt="DAY 1", col=None):
    col = col or RED
    c.d.rectangle(_r(x, y, 110 * s, 120 * s), fill=(240, 240, 244))
    c.d.rectangle([x - 55 * s, y - 120 * s, x + 55 * s, y - 92 * s], fill=col)
    m = nv.text_mask(txt, max(10, int(22 * s)))
    c.img.paste((30, 30, 34), (int(x - m.width / 2), int(y - 70 * s)), m)


def flag(c, x, y, s=1.0, t=0.0, col=None):
    col = col or T()["accent"]
    c.d.line([(x, y), (x, y - 180 * s)], fill=STEEL, width=max(3, int(7 * s)))
    wv = 10 * s * math.sin(t * 6)
    c.d.polygon([(x, y - 180 * s), (x + 100 * s, y - 155 * s + wv), (x, y - 125 * s)], fill=col)


def target(c, x, y, s=1.0):
    for i, col in enumerate(((240, 240, 240), RED, (240, 240, 240), RED)):
        r = (50 - i * 12) * s
        c.d.ellipse([x - r, y - 50 * s - r, x + r, y - 50 * s + r], fill=col)


def mountain(c, x, y, s=1.0, col=(90, 100, 120)):
    c.d.polygon([(x - 160 * s, y), (x, y - 260 * s), (x + 160 * s, y)], fill=col)
    c.d.polygon([(x - 46 * s, y - 185 * s), (x, y - 260 * s), (x + 46 * s, y - 185 * s), (x + 14 * s, y - 196 * s),
                 (x - 12 * s, y - 180 * s)], fill=(240, 244, 250))


def rain_cloud(c, x, y, s=1.0, t=0.0):
    """y = the cloud's bottom."""
    col = (90, 96, 110)
    for dx, dy, r in ((-40, -30, 34), (0, -46, 44), (42, -28, 32)):
        c.d.ellipse([x + (dx - r) * s, y + (dy - r) * s, x + (dx + r) * s, y + (dy + r) * s], fill=col)
    c.d.rectangle([x - 70 * s, y - 34 * s, x + 70 * s, y], fill=col)
    for i in range(7):
        ph = (t * 1.8 + i * 0.37) % 1
        rx = x - 60 * s + i * 20 * s
        ry = y + 10 * s + ph * 140 * s
        c.d.line([(rx, ry), (rx - 4 * s, ry + 18 * s)], fill=(120, 170, 255), width=max(2, int(3 * s)))


def plant(c, x, y, s=1.0, k=1.0, wilt=0.0, t=0.0):
    """k 0..1 growth; wilt 0..1 makes it droop and brown."""
    c.d.polygon([(x - 34 * s, y), (x + 34 * s, y), (x + 44 * s, y - 50 * s), (x - 44 * s, y - 50 * s)],
                fill=(170, 90, 60))
    if k <= 0:
        return
    stem_h = (40 + 200 * k) * s
    leaf = nv.mix(GREEN, (130, 100, 50), wilt)
    sway = 6 * s * math.sin(t * 2)
    top = (x + sway + wilt * 40 * s, y - 50 * s - stem_h * (1 - 0.4 * wilt))
    c.d.line([(x, y - 50 * s), top], fill=nv.mix(GREEN2, (110, 80, 40), wilt), width=max(3, int(8 * s)))
    n = 1 + int(k * 5)
    for i in range(n):
        f = (i + 1) / (n + 1)
        px = x + (top[0] - x) * f
        py = y - 50 * s + (top[1] - (y - 50 * s)) * f
        side = -1 if i % 2 else 1
        droop = 30 * s * wilt
        c.d.ellipse([px + side * 6 * s - (24 if side < 0 else 0) * s - 10 * s, py - 14 * s + droop,
                     px + side * 6 * s + (24 if side > 0 else 0) * s + 10 * s, py + 6 * s + droop], fill=leaf)
    if k > 0.85 and wilt < 0.2:
        for dx, dy in ((-24, 20), (22, 40), (-6, 60)):
            c.d.ellipse([top[0] + (dx - 9) * s, top[1] + (dy - 9) * s, top[0] + (dx + 9) * s, top[1] + (dy + 9) * s],
                        fill=(230, 60, 60))
        c.glow(top[0], top[1] + 30 * s, int(80 * s), GREEN, 0.3)


def watering_can(c, x, y, s=1.0, pour=0.0, t=0.0):
    col = T()["accent"]
    c.d.rounded_rectangle(_r(x, y, 60 * s, 46 * s), int(6 * s), fill=col)
    c.d.line([(x + 30 * s, y - 30 * s), (x + 62 * s, y - 50 * s)], fill=col, width=max(3, int(8 * s)))
    if pour > 0:
        for i in range(5):
            ph = (t * 2.5 + i * 0.2) % 1
            c.d.ellipse([x + 62 * s + i * 3 * s, y - 50 * s + ph * 90 * s, x + 68 * s + i * 3 * s,
                         y - 42 * s + ph * 90 * s], fill=(120, 180, 255))


def rocket(c, x, y, s=1.0, t=0.0, flame=True):
    c.d.polygon([(x - 22 * s, y - 20 * s), (x + 22 * s, y - 20 * s), (x + 22 * s, y - 110 * s), (x, y - 150 * s),
                 (x - 22 * s, y - 110 * s)], fill=(235, 235, 240))
    c.d.ellipse([x - 11 * s, y - 100 * s, x + 11 * s, y - 78 * s], fill=BLUE)
    for sx in (-1, 1):
        c.d.polygon([(x + sx * 22 * s, y - 20 * s), (x + sx * 40 * s, y), (x + sx * 22 * s, y - 56 * s)], fill=RED)
    if flame:
        fire(c, x, y + 50 * s, 0.5 * s, t)


def key(c, x, y, s=1.0, col=None):
    col = col or GOLD
    c.d.ellipse([x - 24 * s, y - 50 * s, x + 4 * s, y - 22 * s], outline=col, width=max(3, int(7 * s)))
    c.d.line([(x + 2 * s, y - 36 * s), (x + 56 * s, y - 36 * s)], fill=col, width=max(3, int(7 * s)))
    c.d.line([(x + 44 * s, y - 36 * s), (x + 44 * s, y - 22 * s)], fill=col, width=max(3, int(6 * s)))


def lock(c, x, y, s=1.0, open_=0.0, col=None):
    col = col or STEEL
    lift = 24 * s * open_
    c.d.arc([x - 24 * s, y - 100 * s - lift, x + 24 * s, y - 50 * s - lift], 180, 360, fill=col, width=max(3, int(8 * s)))
    c.d.line([(x - 24 * s, y - 75 * s - lift), (x - 24 * s, y - 58 * s - lift * (1 - open_))], fill=col,
             width=max(3, int(8 * s)))
    c.d.line([(x + 24 * s, y - 75 * s - lift), (x + 24 * s, y - 58 * s)], fill=col, width=max(3, int(8 * s)))
    c.d.rounded_rectangle(_r(x, y, 70 * s, 62 * s), int(8 * s), fill=GOLD if open_ > 0.5 else (150, 120, 60))


def chain(c, x0, y0, x1, y1, s=1.0, col=(150, 150, 158)):
    n = max(2, int(math.hypot(x1 - x0, y1 - y0) / (24 * s)))
    for i in range(n):
        f = i / n
        cx, cy = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
        if i % 2:
            c.d.ellipse([cx - 12 * s, cy - 7 * s, cx + 12 * s, cy + 7 * s], outline=col, width=max(2, int(4 * s)))
        else:
            c.d.ellipse([cx - 7 * s, cy - 12 * s, cx + 7 * s, cy + 12 * s], outline=col, width=max(2, int(4 * s)))


def sparkle(c, x, y, s=1.0, t=0.0, col=None):
    col = col or GOLD2
    k = 0.6 + 0.4 * math.sin(t * 8 + x * 0.01)
    r = 16 * s * k
    c.d.polygon([(x, y - r), (x + r * 0.25, y - r * 0.25), (x + r, y), (x + r * 0.25, y + r * 0.25), (x, y + r),
                 (x - r * 0.25, y + r * 0.25), (x - r, y), (x - r * 0.25, y - r * 0.25)], fill=col)


def progress_bar(c, x, y, w, k, col=None, s=1.0):
    col = col or T()["accent"]
    c.d.rounded_rectangle([x - w / 2, y - 14 * s, x + w / 2, y], int(7 * s), fill=(40, 40, 46))
    if k > 0:
        c.d.rounded_rectangle([x - w / 2, y - 14 * s, x - w / 2 + w * clamp(k), y], int(7 * s), fill=col)


PROPS = {
    "coin": coin, "money_bag": money_bag, "cash": cash, "phone": phone, "laptop": laptop, "controller": controller,
    "dumbbell": dumbbell, "couch": couch, "bed": bed, "pizza": pizza, "soda": soda, "salad": salad,
    "book": book, "bulb": bulb, "brain": brain, "trophy": trophy, "heart": heart, "fire": fire, "torch": torch,
    "hourglass": hourglass, "alarm": alarm, "calendar": calendar, "flag": flag, "target": target,
    "mountain": mountain, "rain_cloud": rain_cloud, "plant": plant, "rocket": rocket, "key": key, "lock": lock,
    "tv": tv, "water_bottle": water_bottle, "shop_bag": shop_bag,
}
