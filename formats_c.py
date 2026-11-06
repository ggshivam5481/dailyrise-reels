"""Format C: "montage" — 5 quick visual metaphors on one theme (the 25M–37M-view pattern).

Each segment (~5 s) is its own little scene with two labels (or a time label), action from its first frame,
and a resolution at ~70% (winner glows gold, loser goes grey/red). Segments are separated by a short flash.
"""
import math
from PIL import Image

import nv
from nv import FLOOR, GOLD, GREY, RED, W, WHITE, clamp, ease, mix
from props_a import (BLUE, BROWN, GREEN, cash, chain, coin, coin_stack, fire, flag, money_bag, phone, plant,
                     pop, shop_bag, sparkle, trophy, watering_can, bulb)

SEGS = 5
SEG = 5.2
LX, RX = 300, 780
LAB_Y = 600
RES = 0.7  # resolution point inside a segment


def _acc():
    return nv.T.get("accent", GOLD)


def _labels(c, lab, u, win="R", y=LAB_Y, subs=None):
    """Two labels; after RES the winner turns accent and the loser grey (optional sub-labels)."""
    done = u >= RES
    lc = (GREY if win == "R" else _acc()) if done else WHITE
    rc = (_acc() if win == "R" else GREY) if done else WHITE
    ls = rs = None
    if subs and done:
        ls, rs = subs
    if pop(u * SEG, 0.15) > 0:
        c.label(lab[0], LX, y, ls, lc, 26)
    if pop(u * SEG, 0.35) > 0:
        c.label(lab[1], RX, y, rs, rc, 26)


def _win_fx(c, x, y, u, t):
    if u >= RES:
        k = ease((u - RES) / 0.15)
        c.glow(x, y, 120, GOLD, 0.45 * k)
        for i in range(3):
            sparkle(c, x - 90 + 90 * i, y - 60 - 30 * math.sin(t * 3 + i), 1.0, t + i, GOLD)


# ---------------- metaphors: f(c, u, t, lab) ----------------
def m_grind(c, u, t, lab):
    """A rough cube is pushed every day and slowly becomes a ball that rolls."""
    idx = 0 if u < 0.3 else (1 if u < 0.6 else 2)
    names = lab if len(lab) == 3 else ("TODAY", "IN A MONTH", "IN A YEAR")
    c.text(names[idx], W / 2, LAB_Y, 32, _acc() if idx == 2 else WHITE)
    k = ease(u / RES)
    size = 170
    r = int(size / 2 * k)
    roll = max(0.0, u - RES) * 900
    cx = 640 + roll
    y1 = FLOOR
    col = mix((150, 150, 158), _acc(), k)
    c.d.rounded_rectangle([cx - size / 2, y1 - size, cx + size / 2, y1], radius=max(2, r), fill=col)
    ang = roll / 85
    c.d.line([(cx, y1 - size / 2), (cx + 60 * math.cos(ang), y1 - size / 2 + 60 * math.sin(ang))],
             fill=mix(col, (0, 0, 0), 0.4), width=6)
    push = 0.5 + 0.5 * math.sin(t * 6)
    P = nv.walk(t, 5, 18, 28)
    c.figure(cx - size / 2 - 70 - 10 * push if u < RES else 380, P if u < RES else nv.celebrate(t))
    if u < RES and int(t * 2) % 2 == 0:
        sparkle(c, cx - size / 2, y1 - 60, 0.8, t, (255, 230, 160))
    _win_fx(c, cx, y1 - size / 2, u, t)


def _row_ground(c, pts, col):
    c.d.polygon(pts, fill=col)
    c.d.line(pts[:-2], fill=mix(col, _acc(), 0.6), width=4)


def m_hills(c, u, t, lab):
    """Easy-now path turns into a wall later; hard-now climb turns into a flat road to the flag."""
    top_f, bot_f = 900, FLOOR
    dark = (26, 26, 32)
    # top row: flat then a cliff at x=700
    _row_ground(c, [(80, top_f), (700, top_f), (700, top_f - 230), (1000, top_f - 230), (1000, top_f + 40),
                    (80, top_f + 40)], dark)
    # bottom row: steep first, flat later
    _row_ground(c, [(80, bot_f), (430, bot_f - 220), (1000, bot_f - 220), (1000, bot_f), (80, bot_f)], dark)
    flag(c, 960, bot_f - 220, 0.9, t, _acc())
    # top walker: fast, then stuck at the wall
    xt = 120 + 560 * ease(clamp(u / 0.45))
    stuck = u > 0.45
    c.figure(xt, nv.sad(t) if stuck else nv.walk(t, 9, 26), 0.7, GREY if u >= RES else WHITE, top_f)
    # bottom climber: slow up the slope, then fast on the flat
    if u < 0.5:
        k = u / 0.5
        xb = 110 + 320 * k
        yb = bot_f - 220 * clamp((xb - 80) / 350)
        c.figure(xb, nv.walk(t, 4, 16, 18), 0.7, WHITE, yb)
    else:
        xb = 430 + 500 * ease(clamp((u - 0.5) / 0.25))
        c.figure(xb, nv.celebrate(t) if u >= RES else nv.run(t), 0.7, WHITE, bot_f - 220)
    c.label(lab[0], 230, 640, "HARD LATER" if u >= RES else None, GREY if u >= RES else WHITE, 24)
    c.label(lab[1], 230, 960, "EASY LATER" if u >= RES else None, _acc() if u >= RES else WHITE, 24)
    if u >= RES:
        _win_fx(c, 940, bot_f - 300, u, t)


def m_scale(c, u, t, lab):
    """Words (light bubbles) vs actions (heavy blocks) on a balance scale."""
    piv = (W / 2, 960)
    nl = min(8, int(u * SEG / 0.45))
    nr = min(5, int(max(0, u * SEG - 0.3) / 0.75))
    ang = math.radians(clamp(nr * 3.4 - nl * 0.6, -6, 16))
    half = 330
    lx, ly = piv[0] - half * math.cos(ang), piv[1] - half * math.sin(ang)
    rx, ry = piv[0] + half * math.cos(ang), piv[1] + half * math.sin(ang)
    c.d.polygon([(piv[0], piv[1]), (piv[0] - 70, FLOOR), (piv[0] + 70, FLOOR)], fill=(90, 92, 104))
    c.d.line([(lx, ly), (rx, ry)], fill=(200, 200, 210), width=10)
    for (px, py), items, heavy in (((lx, ly), nl, False), ((rx, ry), nr, True)):
        c.d.line([(px, py), (px - 70, py + 150)], fill=(150, 150, 160), width=3)
        c.d.line([(px, py), (px + 70, py + 150)], fill=(150, 150, 160), width=3)
        c.d.rectangle([px - 95, py + 150, px + 95, py + 162], fill=(200, 200, 210))
        for i in range(items):
            if heavy:
                bx = px - 60 + (i % 3) * 60
                by = py + 150 - 46 * (i // 3 + 1)
                c.block(bx - 26, by, bx + 26, by + 44, mix((210, 210, 214), _acc(), 0.5))
            else:
                bx = px - 70 + (i % 4) * 46
                by = py + 120 - 40 * (i // 4)
                c.d.ellipse([bx - 22, by - 16, bx + 22, by + 16], fill=(235, 235, 240))
                c.d.polygon([(bx - 6, by + 12), (bx + 6, by + 12), (bx - 10, by + 24)], fill=(235, 235, 240))
    _labels(c, lab, u, "R", 640)
    if u >= RES:
        _win_fx(c, rx, ry + 60, u, t)


def m_holes(c, u, t, lab):
    """Many shallow holes (multitasking) vs one deep hole that hits gold (focus)."""
    gy, vein = 900, 1185
    c.d.rectangle([60, gy, 1020, FLOOR], fill=(74, 50, 34))
    for i in range(4):
        c.d.line([(60, gy + 60 + i * 70), (1020, gy + 60 + i * 70)], fill=(62, 42, 28), width=3)
    c.d.rectangle([60, vein, 1020, vein + 26], fill=GOLD)
    n = min(5, 1 + int(u * SEG / 0.8))
    for i in range(n):
        hx = 110 + i * 75
        c.d.rectangle([hx - 26, gy, hx + 26, gy + 46], fill=(20, 14, 10))
    depth = (vein - gy) * clamp(u / RES)
    c.d.rectangle([RX - 40, gy, RX + 40, gy + depth], fill=(20, 14, 10))
    lxp = 110 + (n - 1) * 75
    c.figure(lxp + 40, nv.bend(t, 0.6 + 0.3 * math.sin(t * 6)), 0.75, GREY if u >= RES else WHITE, gy)
    c.figure(RX + 80 if u < RES else RX, nv.bend(t, 0.6 + 0.3 * math.sin(t * 6)) if u < RES else nv.celebrate(t),
             0.75, WHITE, gy)
    _labels(c, lab, u, "R", 640)
    if u >= RES:
        for i in range(5):
            coin(c, RX - 60 + i * 30, gy - 20 - 70 * ease((u - RES) / 0.2) * (0.6 + 0.4 * math.sin(i)), 0.7, t * 6 + i)
        _win_fx(c, RX, vein, u, t)


def m_graph(c, u, t, lab):
    """Motivation spikes and drops; discipline climbs steadily and overtakes."""
    x0, x1, base, topy = 130, 950, 1180, 700
    c.d.line([(x0, base), (x1, base)], fill=(90, 90, 100), width=3)
    c.d.line([(x0, base), (x0, topy - 20)], fill=(90, 90, 100), width=3)
    xs = int(x0 + (x1 - x0) * clamp(u / 0.85))

    def mot(x):
        k = (x - x0) / (x1 - x0)
        return base - 420 * math.exp(-((k - 0.18) / 0.09) ** 2) - 40

    def dis(x):
        k = (x - x0) / (x1 - x0)
        return base - 40 - 440 * (math.floor(k * 10) / 10 * 0.6 + k * 0.4)
    for f, col in ((mot, mix(RED, WHITE, 0.2)), (dis, _acc())):
        pts = [(x, f(x)) for x in range(x0, max(x0 + 2, xs), 8)]
        if len(pts) > 1:
            c.d.line(pts, fill=col, width=7, joint="curve")
        bx = pts[-1][0]
        by = f(bx)
        c.d.ellipse([bx - 16, by - 16, bx + 16, by + 16], fill=col)
    c.text(lab[0], x0 + 170, mot(x0 + 150) - 70, 22, mix(RED, WHITE, 0.3))
    c.text(lab[1], min(xs, 820), dis(min(xs, 820)) - 60, 22, _acc())
    if u >= RES:
        _win_fx(c, xs, dis(xs), u, t)


def _bucket(c, x, level, leak, t, col):
    w0, w1, h = 120, 160, 200
    y1 = FLOOR
    poly = [(x - w0 / 2, y1), (x + w0 / 2, y1), (x + w1 / 2, y1 - h), (x - w1 / 2, y1 - h)]
    wl = y1 - h * level
    wk = level
    c.d.polygon([(x - w0 / 2, y1), (x + w0 / 2, y1), (x + (w0 + (w1 - w0) * wk) / 2, wl),
                 (x - (w0 + (w1 - w0) * wk) / 2, wl)], fill=col)
    c.d.line(poly + [poly[0]], fill=(200, 200, 210), width=6)
    if leak:
        for i, hy in enumerate((y1 - 40, y1 - 90, y1 - 140)):
            for j in range(3):
                ph = (t * 1.5 + j / 3 + i * 0.2) % 1
                dx = (w0 / 2 + 10) + 120 * ph
                c.d.ellipse([x - dx - 6, hy + 160 * ph * ph - 8, x - dx + 6, hy + 160 * ph * ph + 8], fill=BLUE)


def m_bucket(c, u, t, lab):
    """Same water poured into a leaking bucket and a sealed one."""
    for x in (LX, RX):
        for j in range(4):
            ph = (t * 1.8 + j / 4) % 1
            c.d.ellipse([x - 7, 700 + 330 * ph - 9, x + 7, 700 + 330 * ph + 9], fill=BLUE)
        c.d.rectangle([x - 40, 680, x + 40, 700], fill=(160, 160, 170))
    _bucket(c, LX, 0.18 + 0.04 * math.sin(t * 3), True, t, BLUE)
    _bucket(c, RX, clamp(0.12 + 0.88 * u / RES), False, t, mix(BLUE, GOLD, ease((u - RES) / 0.2)))
    _labels(c, lab, u, "R", 560)
    if u >= RES:
        _win_fx(c, RX, FLOOR - 230, u, t)


def m_wall(c, u, t, lab):
    """One keeps jumping at the wall; the other adds one step a day and walks over."""
    top_f, bot_f = 900, FLOOR
    for f in (top_f, bot_f):
        c.d.line([(80, f), (1000, f)], fill=mix((40, 40, 48), _acc(), 0.4), width=4)
        c.block(640, f - 260, 700, f, (150, 150, 160))
    jump = abs(math.sin(t * 4)) * 150 * (1 if u < RES else 0)
    c.figure(560, nv.sad(t) if u >= RES else nv.celebrate(t), 0.75, GREY if u >= RES else WHITE, top_f, dy=jump)
    n = min(5, int(u * SEG / 0.7))
    for i in range(n):
        h = 52 * (i + 1)
        c.block(430 + i * 42, bot_f - h, 472 + i * 42, bot_f, mix((210, 210, 214), _acc(), 0.5))
    if u < RES:
        c.figure(380 + n * 30, nv.bend(t, 0.5 + 0.3 * math.sin(t * 5)), 0.75, WHITE, bot_f)
    else:
        k = ease((u - RES) / 0.2)
        c.figure(700 + 180 * k, nv.celebrate(t), 0.75, WHITE, bot_f - 260 * (1 - k))
        flag(c, 940, bot_f, 0.9, t, _acc())
        _win_fx(c, 880, bot_f - 200, u, t)
    c.label(lab[0], 220, 640, None, GREY if u >= RES else WHITE, 24)
    c.label(lab[1], 220, 960, None, _acc() if u >= RES else WHITE, 24)


def m_seed(c, u, t, lab):
    """Seed to tree time-lapse while someone keeps watering."""
    names = lab if len(lab) == 3 else ("DAY 1", "DAY 90", "DAY 365")
    idx = 0 if u < 0.3 else (1 if u < 0.6 else 2)
    c.text(names[idx], W / 2, LAB_Y, 32, _acc() if idx == 2 else WHITE)
    k = ease(clamp(u / RES))
    plant(c, 620, FLOOR, 1.6 + 0.8 * k, k, 0.0, t)
    pour = 0.5 + 0.5 * math.sin(t * 3)
    c.figure(380, nv.stand(t), 1.0)
    watering_can(c, 470, FLOOR - 170, 0.9, pour, t)
    if u >= RES:
        _win_fx(c, 620, FLOOR - 420, u, t)


def m_coins(c, u, t, lab):
    """Saving a little every day vs spending it all."""
    n = min(14, int(u * SEG / 0.3))
    coin_stack(c, LX + 60, FLOOR, n, 1.0)
    if n and n < 14:
        coin(c, LX + 60, FLOOR - 26 * n - 80 * ((t * 3) % 1), 1.0, t * 8)
    c.figure(LX - 60, nv.stand(t), 0.9, WHITE)
    for i in range(min(4, 1 + int(u * SEG / 0.9))):
        shop_bag(c, RX + 40 + (i % 2) * 70, FLOOR - (i // 2) * 0, 0.9)
    c.figure(RX - 70, nv.walk(t, 6, 18), 0.9, GREY if u >= RES else WHITE)
    for i in range(3):
        ph = (t * 0.8 + i / 3) % 1
        cash(c, RX + 20 + 40 * i, 900 - 280 * ph, 0.8, ph * 6)
    c.text("SAVED  " + str(n * 100), LX, 1000, 24, _acc() if u >= RES else WHITE)
    _labels(c, lab, u, "L", LAB_Y)
    if u >= RES:
        money_bag(c, LX + 60, FLOOR - 26 * n - 10, pop(u * SEG, RES * SEG) * 1.2, 1.0)
        _win_fx(c, LX + 60, FLOOR - 26 * n - 60, u, t)


def m_chain(c, u, t, lab):
    """Chained to the phone vs free hands that reach the flag."""
    c.figure(LX - 20, nv.phone(t), 1.0, GREY if u >= RES else WHITE)
    phone(c, LX + 80, FLOOR, 1.2, t, True, int(3 + u * 40))
    chain(c, LX - 20, FLOOR - 20, LX + 80, FLOOR - 40, 1.0)
    k = ease(clamp(u / RES))
    c.figure(560 + 340 * k, nv.celebrate(t) if u >= RES else nv.run(t), 1.0, WHITE)
    flag(c, 960, FLOOR, 1.1, t, _acc())
    _labels(c, lab, u, "R", LAB_Y)
    if u >= RES:
        _win_fx(c, 920, FLOOR - 200, u, t)


def m_candle(c, u, t, lab):
    """Burning the candle at both ends vs a steady lamp."""
    k = clamp(u / RES)
    full = 360
    left = full * (1 - k)
    cy = 980
    if left > 6:
        c.d.rectangle([LX - left / 2, cy - 22, LX + left / 2, cy + 22], fill=(240, 230, 210))
        fire(c, LX - left / 2 - 10, cy + 20, 0.8, t)
        fire(c, LX + left / 2 + 10, cy + 20, 0.8, t + 1)
    else:
        for i in range(4):
            ph = (t * 0.7 + i / 4) % 1
            c.d.ellipse([LX - 20 + 10 * i, cy - 150 * ph - 10, LX + 20 + 10 * i, cy - 150 * ph + 10],
                        fill=mix((70, 70, 80), (20, 20, 24), ph))
    c.d.line([(LX, cy + 22), (LX, FLOOR)], fill=(90, 90, 100), width=8)
    bulb(c, RX, FLOOR - 200, 1.4, 0.6 + 0.4 * ease(clamp(u / RES)))
    c.d.line([(RX, FLOOR - 200), (RX, FLOOR)], fill=(90, 90, 100), width=8)
    _labels(c, lab, u, "R", LAB_Y)
    if u >= RES:
        _win_fx(c, RX, FLOOR - 300, u, t)


def m_stairs(c, u, t, lab):
    """Staring at someone else's huge staircase vs climbing your own."""
    for i in range(8):
        c.block(60 + i * 40, FLOOR - 70 * (i + 1), 100 + i * 40, FLOOR, (70, 70, 78))
    c.text("THEIR DAY 1000", 220, FLOOR - 640, 18, GREY)
    c.figure(LX + 130, nv.sad(t), 0.85, GREY if u >= RES else WHITE)
    n = min(6, 1 + int(u * SEG / 0.6))
    for i in range(n):
        c.block(600 + i * 60, FLOOR - 45 * (i + 1), 660 + i * 60, FLOOR, mix((210, 210, 214), _acc(), 0.5))
    step = min(n - 1, int(u * SEG / 0.6))
    c.figure(630 + step * 60, nv.celebrate(t) if u >= RES else nv.walk(t, 6, 18), 0.85, WHITE,
             FLOOR - 45 * (step + 1))
    c.text("MY DAY " + str(1 + int(u * 120)), 780, LAB_Y + 120, 22, _acc() if u >= RES else WHITE)
    _labels(c, lab, u, "R", LAB_Y)
    if u >= RES:
        _win_fx(c, 630 + step * 60, FLOOR - 45 * (step + 1) - 120, u, t)


METAPHORS = {
    "grind": (m_grind, [("TODAY", "IN A MONTH", "IN A YEAR"), ("DAY 1", "DAY 30", "DAY 365"),
                        ("WEEK 1", "MONTH 6", "YEAR 2")]),
    "hills": (m_hills, [("EASY NOW", "HARD NOW"), ("COMFORT NOW", "EFFORT NOW"), ("SKIP IT", "DO IT")]),
    "scale": (m_scale, [("WORDS", "ACTIONS"), ("PLANS", "WORK"), ("PROMISES", "PROOF")]),
    "holes": (m_holes, [("MULTITASKING", "FOCUS"), ("10 IDEAS", "1 IDEA"), ("EVERYTHING", "ONE THING")]),
    "graph": (m_graph, [("MOTIVATION", "DISCIPLINE"), ("HYPE", "HABIT"), ("FEELINGS", "SYSTEMS")]),
    "bucket": (m_bucket, [("LEAKING", "SEALED"), ("DISTRACTED", "FOCUSED"), ("SPENDER", "SAVER")]),
    "wall": (m_wall, [("ONE BIG JUMP", "ONE STEP A DAY"), ("SHORTCUT", "STEPS"), ("ALL AT ONCE", "LITTLE DAILY")]),
    "seed": (m_seed, [("DAY 1", "DAY 90", "DAY 365"), ("SEED", "SPROUT", "TREE"), ("YEAR 1", "YEAR 3", "YEAR 5")]),
    "coins": (m_coins, [("SAVER", "SPENDER"), ("INVESTOR", "SHOW OFF"), ("100 A DAY", "ALL TODAY")]),
    "chain": (m_chain, [("CHAINED", "FREE"), ("SCROLLING", "BUILDING"), ("PHONE FIRST", "GOAL FIRST")]),
    "candle": (m_candle, [("BURNOUT", "BALANCE"), ("ALL NIGHTERS", "SLEEP ON TIME"), ("100% FOR A WEEK", "50% FOREVER")]),
    "stairs": (m_stairs, [("COMPARING", "CLIMBING"), ("WATCHING", "DOING"), ("THEIR PATH", "MY PATH")]),
}

# theme scripts: (top, punch, caption_line, ig, topic, [5 metaphors])
SCRIPTS = [
    ("WORK SMART OVER HARD.", "SMART EFFORT. EVERY DAY.", "Effort only counts when it points somewhere.",
     "Mehnat sahi disha mein ho, tabhi result aata hai.", "discipline", ["grind", "holes", "scale", "graph", "wall"]),
    ("BRICK BY BRICK.", "SLOW IS STILL FORWARD.", "Nobody builds anything great in one day.",
     "Roz ek eent, ek din mehal.", "habits", ["wall", "grind", "seed", "stairs", "coins"]),
    ("MAKE IT HAPPEN.", "PROVE IT TO YOURSELF.", "Stop announcing it. Start proving it.",
     "Bolna kam, karna zyada.", "discipline", ["scale", "chain", "hills", "holes", "grind"]),
    ("DON'T QUIT ON A BAD DAY.", "BAD DAYS ARE PART OF IT.", "One bad day is not a bad life.",
     "Ek bura din poori zindagi nahi hota.", "mindset", ["graph", "seed", "wall", "grind", "stairs"]),
    ("EASY NOW. HARD LATER.", "PICK YOUR HARD.", "Every path is hard. Choose the hard that pays you back.",
     "Mushkil sab mein hai, sahi mushkil chuno.", "discipline", ["hills", "candle", "coins", "chain", "wall"]),
    ("ONE THING AT A TIME.", "FOCUS WINS.", "Ten half things will never beat one finished thing.",
     "Ek kaam, poora dhyaan.", "focus", ["holes", "bucket", "chain", "graph", "scale"]),
    ("SMALL MONEY. BIG FUTURE.", "STACK QUIETLY.", "Wealth is built in small amounts nobody sees.",
     "Chhoti bachat, bada future.", "money", ["coins", "bucket", "seed", "grind", "hills"]),
    ("WHERE DID YOUR TIME GO?", "PLUG THE LEAKS.", "Your day doesn't disappear. It leaks.",
     "Time gayab nahi hota, leak hota hai.", "time", ["bucket", "chain", "candle", "holes", "graph"]),
    ("STOP COMPARING.", "CLIMB YOUR OWN STAIRS.", "Their chapter 20 is not your chapter 1.",
     "Doosron ki seedhi mat dekho, apni chadho.", "mindset", ["stairs", "seed", "wall", "graph", "grind"]),
    ("PATIENCE PAYS.", "GIVE IT A YEAR.", "Most things that matter look like nothing at first.",
     "Sabr rakho, ek saal do.", "growth", ["seed", "grind", "coins", "stairs", "graph"]),
    ("BURNOUT IS NOT A FLEX.", "STEADY BEATS INTENSE.", "The goal is to still be going next year.",
     "Thak ke girna jeet nahi hai.", "mindset", ["candle", "graph", "hills", "wall", "bucket"]),
    ("MOTIVATION FADES.", "SYSTEMS STAY.", "Feelings come and go. Routines keep showing up.",
     "Motivation jaata hai, routine rehta hai.", "habits", ["graph", "candle", "grind", "seed", "scale"]),
    ("PUT THE PHONE DOWN.", "YOUR LIFE IS OFF SCREEN.", "The phone gives you a feed. It takes your future.",
     "Phone neeche, zindagi upar.", "focus", ["chain", "bucket", "holes", "stairs", "hills"]),
    ("SAY LESS. DO MORE.", "LET RESULTS TALK.", "Quiet work makes the loudest results.",
     "Kam bolo, zyada karo.", "discipline", ["scale", "grind", "wall", "coins", "seed"]),
    ("SHORTCUTS COST MORE.", "TAKE THE STAIRS.", "The long way is the only way that lasts.",
     "Shortcut ka bill baad mein aata hai.", "growth", ["wall", "hills", "stairs", "candle", "holes"]),
    ("DAY 1 LOOKS LIKE NOTHING.", "DAY 365 LOOKS LIKE MAGIC.", "Nothing changes until it suddenly does.",
     "Pehla din kuch nahi lagta, saal ke baad sab dikhta hai.", "habits", ["seed", "grind", "stairs", "coins", "graph"]),
    ("STOP LEAKING ENERGY.", "GUARD YOUR FOCUS.", "Energy you spend on noise is energy you steal from goals.",
     "Apni energy bekaar cheezon pe mat bahao.", "focus", ["bucket", "holes", "candle", "chain", "scale"]),
    ("FEAR SAYS WAIT.", "ACTION SAYS NOW.", "Waiting feels safe. It is the riskiest move.",
     "Darr rokta hai, kadam chalaata hai.", "fear", ["hills", "wall", "scale", "stairs", "chain"]),
    ("RICH VS LOOKING RICH.", "QUIET MONEY GROWS.", "Looking rich is expensive. Being rich is boring.",
     "Dikhawa mehenga hai, bachat sasti.", "money", ["coins", "scale", "bucket", "hills", "seed"]),
    ("YOU'RE NOT BEHIND.", "YOU'RE ON YOUR STEP.", "Your timeline is yours. Keep stepping.",
     "Tum peeche nahi ho, apni seedhi pe ho.", "mindset", ["stairs", "graph", "seed", "wall", "grind"]),
    ("CONSISTENCY IS THE KEY.", "SHOW UP. AGAIN.", "Showing up beats showing off.",
     "Roz aana hi asli talent hai.", "discipline", ["grind", "graph", "wall", "seed", "coins"]),
    ("TOO MUCH AT ONCE?", "SLOW DOWN. GO DEEP.", "Depth beats speed when it matters.",
     "Sab ek saath mat karo, ek cheez gehra karo.", "focus", ["holes", "candle", "bucket", "graph", "hills"]),
    ("YOUR HABITS DECIDE.", "CHOOSE THEM DAILY.", "You don't rise to goals. You fall to habits.",
     "Goal nahi, aadatein future banati hain.", "habits", ["scale", "seed", "chain", "grind", "stairs"]),
    ("TIME IS THE REAL MONEY.", "SPEND IT ON YOU.", "You can earn money back. Not hours.",
     "Paisa wapas aata hai, waqt nahi.", "time", ["coins", "candle", "bucket", "chain", "hills"]),
    ("THE HARD ROAD IS SHORTER.", "START CLIMBING.", "The easy road ends at a wall. The hard one ends at a flag.",
     "Mushkil raasta hi chhota nikalta hai.", "growth", ["hills", "holes", "wall", "grind", "stairs"]),
    ("NOBODY SEES THE ROOTS.", "KEEP WATERING.", "Growth happens underground first.",
     "Jadein dikhti nahi, par sab wahi se hai.", "growth", ["seed", "holes", "stairs", "graph", "bucket"]),
    ("WHAT ARE YOU FEEDING?", "FEED YOUR FUTURE.", "Your attention is food. Feed the right thing.",
     "Dhyaan jahan, zindagi wahan.", "focus", ["chain", "scale", "seed", "bucket", "candle"]),
    ("STOP OVERTHINKING.", "START DOING.", "Thinking about it is not doing it.",
     "Sochna band, karna shuru.", "fear", ["scale", "hills", "wall", "chain", "graph"]),
]


def make_montage(rnd, used):
    for _ in range(400):
        si = rnd.randrange(len(SCRIPTS))
        top, punch, cap, ig, topic, mets = SCRIPTS[si]
        order = list(mets)
        if rnd.random() < 0.5:
            rnd.shuffle(order)
        labs = [rnd.randrange(len(METAPHORS[m][1])) for m in order]
        key = f"c1|montage|{si}|" + ",".join(f"{m}{li}" for m, li in zip(order, labs))
        if key in used:
            continue
        used.add(key)
        labels = [list(METAPHORS[m][1][li]) for m, li in zip(order, labs)]
        text = "|".join([top, punch] + [m + ":" + "/".join(l) for m, l in zip(order, labels)])
        dur = SEGS * SEG
        return dict(format="montage", key=key, script_text=text, dur=dur, top=top, punch=punch,
                    punch_at=0.9, caption_line=cap, ig=ig, topic=topic, segs=order, labels=labels)
    raise RuntimeError("montage bank exhausted")


def draw_montage(c, t, spec):
    i = min(SEGS - 1, int(t / SEG))
    lt = t - i * SEG
    u = lt / SEG
    fn = METAPHORS[spec["segs"][i]][0]
    c.spot(LX, strength=0.6)
    c.spot(RX, strength=0.6)
    fn(c, u, t, spec["labels"][i])
    c.text(f"{i + 1}/{SEGS}", W - 90, 400, 18, mix(WHITE, _acc(), 0.5))
    if lt < 0.14 and i > 0:  # cut flash
        a = int(150 * (1 - lt / 0.14))
        c.img.paste((255, 255, 255), (0, 0, W, nv.H), Image.new("L", (W, nv.H), a))


def events_montage(spec):
    ev = []
    for i in range(SEGS):
        s0 = i * SEG
        if i:
            ev += [(s0, "whoosh", 0.5), (s0 + 0.02, "flash", 0.3)]
        ev += [(s0 + 0.15, "pop", 0.35), (s0 + 0.35, "pop", 0.35)]
        for k in range(1, 4):
            ev.append((s0 + k * 1.1, "step" if k % 2 else "pop", 0.25))
        ev += [(s0 + RES * SEG - 0.6, "riser", 0.35), (s0 + RES * SEG, "chime", 0.45),
               (s0 + RES * SEG + 0.02, "impact", 0.3)]
    return ev


FORMATS = {"montage": {"make": make_montage, "draw": draw_montage, "events": events_montage}}


if __name__ == "__main__":
    import random
    rnd = random.Random(4)
    used = set()
    spec = make_montage(rnd, used)
    nv.set_theme("royal")
    tiles = []
    for i in range(SEGS):
        for f in (0.35, 0.85):
            t = (i + f) * SEG
            c = nv.Canvas()
            c.particles(t)
            draw_montage(c, t, spec)
            c.lines(spec["top"], W / 2, nv.TOP_Y, 30)
            tiles.append(c.finish(t).resize((216, 384)))
    sheet = Image.new("RGB", (216 * 5, 384 * 2))
    for k, im in enumerate(tiles):
        i, j = divmod(k, 2)
        sheet.paste(im, (i * 216, j * 384))
    sheet.save("out/fc_montage.png")
    print(spec["top"], spec["segs"], spec["labels"])
