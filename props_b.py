"""Small coloured vector props for the minimal reels. Every prop: fn(c, x, y, s, t) draws centred at (x, y),
roughly `s` px tall, on canvas `c` (uses c.d / c.glow). Natural colours so they pop on the dark theme."""
import math
import random

from nv import GOLD, GOLD2, RED, WHITE, clamp

ORANGE = (240, 140, 50)
BLUE = (80, 170, 255)
GREEN = (90, 200, 110)
PINK = (240, 130, 170)
PURPLE = (160, 110, 230)
BROWN = (130, 85, 55)
STEEL = (150, 156, 168)
DARKS = (40, 42, 48)
BOOKS = [(220, 70, 70), (70, 140, 230), (90, 190, 110), (240, 190, 60), (160, 110, 230)]


def pop(t, t0, dur=0.28):
    """Pop-in scale: 0 before t0, overshoots to ~1.15 then settles at 1."""
    u = (t - t0) / dur
    if u <= 0:
        return 0.0
    if u >= 1:
        return 1.0
    return math.sin(u * math.pi * 0.5) * (1 + 0.25 * math.sin(u * math.pi))


def _r(cx, cy, w, h):
    return [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2]


def coin(c, x, y, s, t=0.0):
    w = s * abs(math.cos(t * 3)) * 0.9 + s * 0.1
    c.d.ellipse(_r(x, y, w, s), fill=(200, 150, 40))
    c.d.ellipse(_r(x, y, w * 0.8, s * 0.8), fill=GOLD)
    if w > s * 0.4:
        c.d.text((x - s * 0.12, y - s * 0.28), "$", fill=(160, 110, 20))


def phone(c, x, y, s, t=0.0):
    w = s * 0.52
    c.glow(x, y, int(s * 0.7), BLUE, 0.45 + 0.15 * math.sin(t * 6))
    c.d.rounded_rectangle(_r(x, y, w, s), int(s * 0.1), fill=(30, 32, 40))
    g = 160 + int(60 * (0.5 + 0.5 * math.sin(t * 7)))
    c.d.rounded_rectangle(_r(x, y, w * 0.8, s * 0.8), int(s * 0.06), fill=(60, g - 20, 255))


def book(c, x, y, s, t=0.0, col=None):
    col = col or BOOKS[int(x + y) % len(BOOKS)]
    c.d.rectangle(_r(x, y, s * 0.75, s), fill=col)
    c.d.rectangle([x - s * 0.375, y - s / 2, x - s * 0.26, y + s / 2], fill=tuple(int(v * 0.6) for v in col))
    c.d.line([(x - s * 0.15, y - s * 0.2), (x + s * 0.28, y - s * 0.2)], fill=WHITE, width=max(2, int(s * 0.05)))


def books(c, x, y, s, t=0.0):
    for i in range(3):
        c.d.rectangle(_r(x + (i - 1) * 4, y + s * 0.33 - i * s * 0.3, s, s * 0.26), fill=BOOKS[i])


def dumbbell(c, x, y, s, t=0.0):
    c.d.rectangle(_r(x, y, s * 1.2, s * 0.14), fill=STEEL)
    for sx in (-1, 1):
        c.d.rounded_rectangle(_r(x + sx * s * 0.5, y, s * 0.22, s * 0.7), 6, fill=(60, 64, 72))
        c.d.rounded_rectangle(_r(x + sx * s * 0.68, y, s * 0.16, s * 0.5), 5, fill=(80, 84, 92))


def trophy(c, x, y, s, t=0.0, glow=True):
    if s < 6:
        return
    if glow:
        c.glow(x, y, int(s * 0.9), GOLD, 0.5 + 0.2 * math.sin(t * 5))
    d = c.d
    d.pieslice([x - s * 0.4, y - s * 0.75, x + s * 0.4, y + s * 0.05], 0, 180, fill=GOLD)
    d.rectangle([x - s * 0.4, y - s * 0.5, x + s * 0.4, y - s * 0.34], fill=GOLD)
    for sx in (-1, 1):
        d.arc([x + sx * s * 0.42 - s * 0.16, y - s * 0.5, x + sx * s * 0.42 + s * 0.16, y - s * 0.16],
              -90 if sx > 0 else 90, 90 if sx > 0 else 270, fill=GOLD, width=max(3, int(s * 0.06)))
    d.rectangle([x - s * 0.07, y, x + s * 0.07, y + s * 0.25], fill=(210, 160, 50))
    d.rectangle([x - s * 0.3, y + s * 0.25, x + s * 0.3, y + s * 0.38], fill=(200, 150, 40))


def moneybag(c, x, y, s, t=0.0):
    d = c.d
    d.ellipse(_r(x, y + s * 0.12, s * 0.85, s * 0.75), fill=(80, 170, 90))
    d.polygon([(x - s * 0.18, y - s * 0.25), (x + s * 0.18, y - s * 0.25), (x + s * 0.25, y - s * 0.45),
               (x - s * 0.25, y - s * 0.45)], fill=(70, 150, 80))
    d.line([(x - s * 0.2, y - s * 0.24), (x + s * 0.2, y - s * 0.24)], fill=GOLD, width=max(3, int(s * 0.06)))
    d.text((x - s * 0.1, y), "$", fill=(230, 255, 230))


def clock(c, x, y, s, t=0.0, ring=False):
    d = c.d
    sh = 3 * math.sin(t * 60) if ring else 0
    x += sh
    for sx in (-1, 1):
        d.ellipse(_r(x + sx * s * 0.3, y - s * 0.42, s * 0.28, s * 0.22), fill=RED)
    d.ellipse(_r(x, y, s, s), fill=RED)
    d.ellipse(_r(x, y, s * 0.82, s * 0.82), fill=(245, 245, 240))
    a = t * 2
    d.line([(x, y), (x + s * 0.3 * math.sin(a), y - s * 0.3 * math.cos(a))], fill=(20, 20, 20), width=4)
    d.line([(x, y), (x + s * 0.2 * math.sin(a / 12), y - s * 0.2 * math.cos(a / 12))], fill=(20, 20, 20), width=5)


def hourglass(c, x, y, s, t=0.0, k=0.5):
    d = c.d
    w = s * 0.6
    d.rectangle(_r(x, y - s / 2, w + 10, 8), fill=BROWN)
    d.rectangle(_r(x, y + s / 2, w + 10, 8), fill=BROWN)
    d.polygon([(x - w / 2, y - s / 2 + 4), (x + w / 2, y - s / 2 + 4), (x, y), (x + w / 2, y + s / 2 - 4),
               (x - w / 2, y + s / 2 - 4), (x, y)], outline=(200, 220, 240), width=3)
    k = clamp(k)
    top = (1 - k) * s * 0.45
    d.polygon([(x - w / 2 * (top / (s * 0.45)), y - top), (x + w / 2 * (top / (s * 0.45)), y - top), (x, y)],
              fill=(240, 200, 110))
    d.polygon([(x - w / 2 * k, y + s / 2 - 4), (x + w / 2 * k, y + s / 2 - 4), (x, y + s / 2 - 4 - k * s * 0.4)],
              fill=(240, 200, 110))


def fire(c, x, y, s, t=0.0):
    c.glow(x, y, int(s * 0.8), ORANGE, 0.55)
    for i, (col, k) in enumerate(((RED, 1.0), (ORANGE, 0.75), ((255, 220, 90), 0.45))):
        f = 1 + 0.12 * math.sin(t * 17 + i * 2)
        h = s * k * f
        w = s * 0.55 * k
        c.d.polygon([(x - w / 2, y + s * 0.3), (x - w * 0.3, y + s * 0.3 - h * 0.6), (x + 0.1 * w * math.sin(t * 9),
                     y + s * 0.3 - h), (x + w * 0.3, y + s * 0.3 - h * 0.55), (x + w / 2, y + s * 0.3)], fill=col)


def plant(c, x, y, s, t=0.0, grow=1.0):
    d = c.d
    d.polygon([(x - s * 0.28, y + s * 0.2), (x + s * 0.28, y + s * 0.2), (x + s * 0.2, y + s * 0.5),
               (x - s * 0.2, y + s * 0.5)], fill=(190, 100, 60))
    g = clamp(grow)
    top = y + s * 0.2 - s * 0.7 * g
    d.line([(x, y + s * 0.2), (x, top)], fill=GREEN, width=max(3, int(s * 0.06)))
    for i in range(int(1 + 3 * g)):
        ly = y + s * 0.1 - i * s * 0.18
        sx = -1 if i % 2 else 1
        d.ellipse([x + (sx > 0) * 2 - (sx < 0) * s * 0.3, ly - s * 0.08, x + (sx > 0) * s * 0.3, ly + s * 0.08],
                  fill=GREEN)


def heart(c, x, y, s, t=0.0, col=RED):
    k = 1 + 0.08 * math.sin(t * 8)
    s *= k
    d = c.d
    d.ellipse([x - s * 0.5, y - s * 0.4, x, y + s * 0.1], fill=col)
    d.ellipse([x, y - s * 0.4, x + s * 0.5, y + s * 0.1], fill=col)
    d.polygon([(x - s * 0.48, y - s * 0.05), (x + s * 0.48, y - s * 0.05), (x, y + s * 0.5)], fill=col)


def bulb(c, x, y, s, t=0.0, on=True):
    if on:
        c.glow(x, y - s * 0.1, int(s * 0.9), (255, 230, 120), 0.6 + 0.15 * math.sin(t * 6))
    c.d.ellipse(_r(x, y - s * 0.12, s * 0.7, s * 0.7), fill=(255, 235, 140) if on else (90, 90, 96))
    c.d.rectangle(_r(x, y + s * 0.3, s * 0.32, s * 0.22), fill=STEEL)


def brain(c, x, y, s, t=0.0):
    d = c.d
    for dx, dy, r in ((-0.22, -0.08, 0.3), (0.2, -0.1, 0.32), (-0.1, 0.12, 0.3), (0.16, 0.12, 0.28), (0, -0.22, 0.26)):
        d.ellipse(_r(x + dx * s, y + dy * s, r * 2 * s * 0.8, r * 2 * s * 0.7), fill=PINK)
    d.line([(x, y - s * 0.35), (x, y + s * 0.3)], fill=(200, 90, 130), width=3)


def rocket(c, x, y, s, t=0.0, flame=False):
    d = c.d
    if flame:
        fire(c, x, y + s * 0.7, s * 0.6, t)
    d.polygon([(x - s * 0.18, y + s * 0.35), (x - s * 0.4, y + s * 0.55), (x - s * 0.18, y + s * 0.05)], fill=RED)
    d.polygon([(x + s * 0.18, y + s * 0.35), (x + s * 0.4, y + s * 0.55), (x + s * 0.18, y + s * 0.05)], fill=RED)
    d.rounded_rectangle(_r(x, y + s * 0.05, s * 0.38, s * 0.8), int(s * 0.12), fill=(235, 235, 240))
    d.polygon([(x - s * 0.19, y - s * 0.3), (x + s * 0.19, y - s * 0.3), (x, y - s * 0.6)], fill=RED)
    d.ellipse(_r(x, y - s * 0.05, s * 0.18, s * 0.18), fill=BLUE)


def key(c, x, y, s, t=0.0):
    d = c.d
    d.ellipse(_r(x - s * 0.3, y, s * 0.4, s * 0.4), outline=GOLD, width=max(4, int(s * 0.1)))
    d.rectangle([x - s * 0.1, y - s * 0.05, x + s * 0.45, y + s * 0.05], fill=GOLD)
    d.rectangle([x + s * 0.3, y, x + s * 0.38, y + s * 0.18], fill=GOLD)


def lock(c, x, y, s, t=0.0, open_=False):
    d = c.d
    lift = s * 0.15 if open_ else 0
    d.arc([x - s * 0.25, y - s * 0.55 - lift, x + s * 0.25, y - s * 0.05 - lift], 180, 360, fill=STEEL,
          width=max(4, int(s * 0.1)))
    d.rounded_rectangle(_r(x, y + s * 0.12, s * 0.7, s * 0.55), 6, fill=GOLD if open_ else (200, 160, 60))
    d.ellipse(_r(x, y + s * 0.1, s * 0.1, s * 0.1), fill=(60, 40, 10))


def chain(c, x, y, s, t=0.0, n=4):
    for i in range(n):
        cx = x + (i - (n - 1) / 2) * s * 0.42
        if i % 2:
            c.d.ellipse(_r(cx, y, s * 0.5, s * 0.22), outline=STEEL, width=max(3, int(s * 0.07)))
        else:
            c.d.ellipse(_r(cx, y, s * 0.5, s * 0.34), outline=(120, 124, 134), width=max(3, int(s * 0.07)))


def flag(c, x, y, s, t=0.0, col=RED):
    d = c.d
    d.line([(x, y + s / 2), (x, y - s / 2)], fill=(210, 210, 214), width=max(3, int(s * 0.05)))
    wv = s * 0.06 * math.sin(t * 6)
    d.polygon([(x, y - s / 2), (x + s * 0.55, y - s * 0.35 + wv), (x, y - s * 0.18)], fill=col)


def calendar(c, x, y, s, t=0.0, label="1"):
    d = c.d
    d.rounded_rectangle(_r(x, y, s * 0.9, s), 8, fill=(245, 245, 245))
    d.rectangle([x - s * 0.45, y - s * 0.5, x + s * 0.45, y - s * 0.25], fill=RED)
    d.text((x - 6 * len(label) / 2 * 1.2, y - 2), label, fill=(20, 20, 20))


def target(c, x, y, s, t=0.0, lit=False):
    cols = [(230, 60, 60), (245, 245, 245), (230, 60, 60), (245, 245, 245), GOLD if lit else (230, 60, 60)]
    for i, col in enumerate(cols):
        r = s / 2 * (1 - i * 0.19)
        c.d.ellipse(_r(x, y, r * 2, r * 2), fill=col)


def mountain(c, x, y, s, t=0.0):
    d = c.d
    d.polygon([(x - s * 0.8, y + s / 2), (x, y - s / 2), (x + s * 0.8, y + s / 2)], fill=(60, 70, 96))
    d.polygon([(x - s * 0.2, y - s * 0.25), (x, y - s / 2), (x + s * 0.2, y - s * 0.25)], fill=(235, 240, 250))


def cloud(c, x, y, s, t=0.0, rain=True, col=(110, 116, 132)):
    if s < 6:
        return
    d = c.d
    for dx, dy, r in ((-0.3, 0.05, 0.28), (0, -0.08, 0.36), (0.32, 0.05, 0.26)):
        d.ellipse(_r(x + dx * s, y + dy * s, r * 2 * s, r * 2 * s * 0.8), fill=col)
    d.rectangle([x - s * 0.55, y, x + s * 0.55, y + s * 0.2], fill=col)
    if rain:
        rnd = random.Random(int(x))
        for i in range(7):
            rx = x - s * 0.45 + i * s * 0.15
            ry = y + s * 0.3 + ((t * 600 + rnd.random() * 200) % (s * 0.9))
            d.line([(rx, ry), (rx - 4, ry + 16)], fill=BLUE, width=3)


def bed(c, x, y, s, t=0.0):
    d = c.d
    d.rectangle([x - s, y - s * 0.15, x + s, y + s * 0.15], fill=(90, 110, 170))
    d.rectangle([x - s, y - s * 0.45, x - s * 0.9, y + s * 0.4], fill=BROWN)
    d.rounded_rectangle([x - s * 0.88, y - s * 0.32, x - s * 0.55, y - s * 0.12], 6, fill=(240, 240, 240))
    d.rectangle([x + s * 0.9, y - s * 0.3, x + s, y + s * 0.4], fill=BROWN)


def couch(c, x, y, s, t=0.0, col=(170, 70, 80)):
    d = c.d
    dk = tuple(int(v * 0.7) for v in col)
    d.rounded_rectangle([x - s, y - s * 0.55, x + s, y], 12, fill=dk)
    d.rounded_rectangle([x - s * 0.85, y - s * 0.2, x + s * 0.85, y + s * 0.15], 10, fill=col)
    for sx in (-1, 1):
        d.rounded_rectangle([x + sx * s - s * 0.15, y - s * 0.35, x + sx * s + s * 0.15, y + s * 0.15], 10, fill=dk)
    for sx in (-1, 1):
        d.rectangle([x + sx * s * 0.8 - 4, y + s * 0.15, x + sx * s * 0.8 + 4, y + s * 0.3], fill=(40, 30, 25))


def burger(c, x, y, s, t=0.0):
    d = c.d
    d.pieslice([x - s / 2, y - s * 0.5, x + s / 2, y + s * 0.1], 180, 360, fill=(220, 150, 60))
    d.rectangle([x - s * 0.5, y - s * 0.22, x + s * 0.5, y - s * 0.12], fill=GREEN)
    d.rectangle([x - s * 0.48, y - s * 0.12, x + s * 0.48, y + s * 0.06], fill=(110, 60, 40))
    d.rectangle([x - s * 0.5, y + s * 0.06, x + s * 0.5, y + s * 0.12], fill=(250, 210, 60))
    d.rounded_rectangle([x - s * 0.5, y + s * 0.12, x + s * 0.5, y + s * 0.3], 8, fill=(220, 150, 60))


def controller(c, x, y, s, t=0.0):
    d = c.d
    d.rounded_rectangle(_r(x, y, s, s * 0.5), int(s * 0.22), fill=(60, 64, 80))
    d.rectangle(_r(x - s * 0.25, y, s * 0.2, s * 0.06), fill=WHITE)
    d.rectangle(_r(x - s * 0.25, y, s * 0.06, s * 0.2), fill=WHITE)
    for i, col in enumerate((RED, GREEN, BLUE, GOLD)):
        a = i * math.pi / 2
        d.ellipse(_r(x + s * 0.25 + s * 0.08 * math.cos(a), y + s * 0.08 * math.sin(a), s * 0.08, s * 0.08), fill=col)


def tv(c, x, y, s, t=0.0):
    d = c.d
    d.rounded_rectangle(_r(x, y, s * 1.3, s * 0.85), 8, fill=(30, 32, 38))
    g = int(120 + 80 * (0.5 + 0.5 * math.sin(t * 9)))
    d.rectangle(_r(x, y, s * 1.15, s * 0.7), fill=(g // 2, g // 3, g))
    d.line([(x - s * 0.2, y + s * 0.6), (x, y + s * 0.42), (x + s * 0.2, y + s * 0.6)], fill=STEEL, width=3)


def star(c, x, y, s, t=0.0, col=GOLD):
    pts = []
    for i in range(10):
        r = s / 2 if i % 2 == 0 else s / 5
        a = i * math.pi / 5 - math.pi / 2 + t * 0.8
        pts.append((x + r * math.cos(a), y + r * math.sin(a)))
    c.d.polygon(pts, fill=col)


def confetti(c, x, y, t, t0, n=40, spread=320, seed=1):
    """Burst of coloured confetti from (x, y) starting at t0."""
    u = t - t0
    if u < 0 or u > 2.5:
        return
    rnd = random.Random(seed)
    cols = [GOLD, RED, BLUE, GREEN, PINK, PURPLE, (255, 255, 255)]
    for i in range(n):
        a = rnd.uniform(-math.pi, 0)
        sp = rnd.uniform(0.4, 1.0) * spread
        px = x + math.cos(a) * sp * min(1, u * 2.5) + rnd.uniform(-20, 20) * u
        py = y + math.sin(a) * sp * min(1, u * 2.5) + 260 * u * u
        w = 8 + 6 * abs(math.sin(u * 8 + i))
        c.d.rectangle([px - w / 2, py - 4, px + w / 2, py + 4], fill=cols[i % len(cols)])


def puff(c, x, y, t, t0, col=(150, 150, 150), n=6, size=26):
    """Dust/smoke puff at t0."""
    u = (t - t0) / 0.6
    if u < 0 or u > 1:
        return
    for i in range(n):
        a = math.pi * (i / (n - 1))
        r = size * (0.5 + u) * (1 - u) * 1.6
        px = x + math.cos(a) * 60 * u * (1 if i % 2 else -1)
        py = y - math.sin(a) * 30 * u
        c.d.ellipse([px - r / 2, py - r / 2, px + r / 2, py + r / 2], fill=col)


def sparks(c, x, y, t, t0, col=GOLD, n=10):
    u = (t - t0) / 0.5
    if u < 0 or u > 1:
        return
    for i in range(n):
        a = i * 2 * math.pi / n
        r1, r2 = 30 + 80 * u, 50 + 110 * u
        c.d.line([(x + r1 * math.cos(a), y + r1 * math.sin(a)), (x + r2 * math.cos(a), y + r2 * math.sin(a))],
                 fill=tuple(int(cc * (1 - u * 0.7)) for cc in col), width=4)


PROPS = {
    "coin": coin, "phone": phone, "book": book, "books": books, "dumbbell": dumbbell, "trophy": trophy,
    "moneybag": moneybag, "clock": clock, "hourglass": hourglass, "fire": fire, "plant": plant, "heart": heart,
    "bulb": bulb, "brain": brain, "rocket": rocket, "key": key, "lock": lock, "chain": chain, "flag": flag,
    "calendar": calendar, "target": target, "mountain": mountain, "cloud": cloud, "bed": bed, "couch": couch,
    "burger": burger, "controller": controller, "tv": tv, "star": star,
}

# icon for a word (used by stack crates and kills lines)
WORD_ICON = {
    "LATER": "clock", "TOMORROW": "calendar", "SNOOZE": "clock", "EXCUSE": "cloud", "NEXT MONDAY": "calendar",
    "JUST 5 MIN": "hourglass", "ONE MORE EPISODE": "tv", "NOT TODAY": "bed", "MAYBE": "cloud", "SKIP": "couch",
    "I'M TIRED": "bed", "AFTER THIS": "phone", "NEW YEAR": "calendar", "SCROLL": "phone", "JUNK FOOD": "burger",
    "ONE MORE GAME": "controller",
    "READ 10 PAGES": "book", "WORKOUT": "dumbbell", "NO SUGAR": "heart", "WAKE 5 AM": "clock", "DEEP WORK": "brain",
    "SAVE 100": "coin", "WALK 5K": "flag", "NO PHONE HOUR": "lock", "JOURNAL": "book", "LEARN 1 SKILL": "bulb",
    "COLD SHOWER": "cloud", "SLEEP ON TIME": "bed", "PRACTICE": "target", "MEDITATE": "brain",
    "LAZINESS": "couch", "PHONE": "phone", "FEAR": "cloud", "COMFORT": "couch", "DOUBT": "cloud", "EGO": "trophy",
    "EXCUSES": "cloud", "OVERTHINKING": "brain", "COMPARISON": "phone", "SUGAR": "burger", "SCROLLING": "phone",
    "ANGER": "fire", "WAITING": "hourglass", "GOSSIP": "phone", "DEBT": "moneybag", "PERFECTION": "target",
    "BLAME": "cloud", "ENVY": "fire", "NOISE": "tv", "REGRET": "hourglass", "LATE NIGHTS": "bed",
    "SHORTCUTS": "key", "COMPLAINING": "cloud", "GAMING": "controller", "JUNK": "burger",
    "DISCIPLINE": "dumbbell", "READING": "book", "SILENCE": "brain", "SAVING": "coin", "SLEEP": "bed",
    "PATIENCE": "plant", "GRATITUDE": "heart", "WALKING": "flag", "FOCUS": "target", "HONESTY": "heart",
    "ROUTINE": "clock", "LISTENING": "brain", "CONSISTENCY": "plant", "EFFORT": "dumbbell", "CALM": "brain",
    "LEARNING": "bulb", "INVESTING": "moneybag", "EXERCISE": "dumbbell", "JOURNALING": "book", "PLANNING": "calendar",
    "WAKING EARLY": "clock", "NO PHONE": "lock",
}


def icon(c, word, x, y, s, t=0.0, positive=False):
    if s < 6:
        return
    fn = PROPS.get(WORD_ICON.get(word.upper(), ""), None)
    if fn is None:
        fn = star if positive else cloud
    if fn is cloud:
        cloud(c, x, y, s * 1.1, t, rain=False)
    else:
        fn(c, x, y, s, t)
