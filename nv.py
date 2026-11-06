"""Minimal 'wisdom meets minimalism' reel engine.

Look: near-black void, one glossy floor with mirror reflection, faceless white capsule stickmen with soft
bloom, spotlights, pixel-font labels, one accent colour (red = loss, gold = reward), counters that tick.
Formats live in formats_*.py and draw through the Canvas API below.
"""
import glob
import math
import os
import subprocess

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 24
FLOOR = 1240
REF_H = 460  # how much of the scene above the floor gets mirrored
BG = (5, 5, 5)
WHITE = (244, 244, 244)
GREY = (140, 140, 140)   # passive / losing character
SUB = (154, 154, 154)    # sub-labels
CROWD = (96, 96, 96)
RED = (224, 40, 46)
GOLD = (242, 193, 78)
GOLD2 = (255, 214, 130)
BLOCK = (210, 210, 212)
HANDLE = "@DAILYRISE.REELS"

# Per-reel colour themes (background gradient, spotlight, accents, particles, floor tint)
THEMES = [
    dict(name="midnight", bg_top=(10, 14, 40), bg_bot=(2, 3, 10), spot=(130, 160, 255), accent=(255, 200, 80),
         accent2=(120, 200, 255), particle=(140, 170, 255), floor=(10, 14, 34)),
    dict(name="ember", bg_top=(42, 12, 6), bg_bot=(6, 2, 2), spot=(255, 150, 70), accent=(255, 110, 50),
         accent2=(255, 210, 120), particle=(255, 140, 60), floor=(36, 12, 6)),
    dict(name="royal", bg_top=(32, 10, 48), bg_bot=(5, 2, 10), spot=(200, 140, 255), accent=(255, 205, 95),
         accent2=(220, 150, 255), particle=(190, 130, 255), floor=(26, 8, 38)),
    dict(name="teal", bg_top=(4, 34, 40), bg_bot=(1, 6, 8), spot=(90, 235, 215), accent=(255, 210, 90),
         accent2=(90, 235, 215), particle=(110, 240, 220), floor=(4, 28, 32)),
    dict(name="crimson", bg_top=(44, 4, 14), bg_bot=(6, 1, 3), spot=(255, 90, 110), accent=(255, 70, 90),
         accent2=(255, 190, 120), particle=(255, 100, 120), floor=(36, 4, 12)),
    dict(name="forest", bg_top=(6, 32, 16), bg_bot=(1, 6, 3), spot=(140, 255, 160), accent=(140, 255, 120),
         accent2=(255, 220, 110), particle=(150, 255, 170), floor=(6, 26, 12)),
    dict(name="sunset", bg_top=(56, 18, 44), bg_bot=(8, 3, 10), spot=(255, 160, 130), accent=(255, 170, 70),
         accent2=(255, 120, 170), particle=(255, 170, 140), floor=(44, 14, 32)),
    dict(name="ice", bg_top=(14, 30, 50), bg_bot=(2, 5, 10), spot=(180, 225, 255), accent=(120, 210, 255),
         accent2=(255, 255, 255), particle=(190, 230, 255), floor=(12, 24, 40)),
]
T = dict(THEMES[0])


def set_theme(i):
    """Pick the colour theme for the next reel (int index/seed or theme name)."""
    global T
    if isinstance(i, str):
        T = dict(next(th for th in THEMES if th["name"] == i))
    else:
        T = dict(THEMES[int(i) % len(THEMES)])
    return T


_bgc = {}


def _background():
    key = T["name"]
    if key not in _bgc:
        g = Image.linear_gradient("L").resize((W, FLOOR))
        top = tuple(min(255, int(c * 2.1)) for c in T["bg_top"])
        bot = tuple(min(255, int(c * 1.6)) for c in T["bg_bot"])
        img = Image.merge("RGB", [g.point(lambda v, i=i: int(top[i] + (bot[i] - top[i]) * (v / 255) ** 0.8))
                                  for i in range(3)])
        full = Image.new("RGB", (W, H), BG)
        full.paste(img, (0, 0))
        glow = Image.new("L", (W, H), 0)
        ImageDraw.Draw(glow).ellipse([W * 0.1, 360, W * 0.9, 1240], fill=105)
        glow = glow.filter(ImageFilter.GaussianBlur(160))
        full.paste(T["spot"], (0, 0), glow)
        fl = Image.linear_gradient("L").resize((W, H - FLOOR))
        fc = T["floor"]
        floor = Image.merge("RGB", [fl.point(lambda v, i=i: min(255, int(fc[i] * 2.2 * (1 - v / 255) ** 1.3 + BG[i]))) for i in range(3)])
        _bgc[key] = (full, floor)
    return _bgc[key]

HEAD_R, TORSO, UA, FA, TH, SH, LIMB = 27, 92, 52, 48, 62, 60, 18
BASE = dict(lean=0, head=0, la1=-12, la2=-4, ra1=12, ra2=4, ll1=-6, ll2=0, rl1=6, rl2=0)


# ---------------- math ----------------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def lerp(a, b, k):
    return a + (b - a) * k


def mix(c1, c2, k):
    return tuple(int(lerp(a, b, clamp(k))) for a, b in zip(c1, c2))


def pt(p, ang, length):
    """0 = straight down, 90 = right, 180 = up, -90 = left."""
    r = math.radians(ang)
    return (p[0] + length * math.sin(r), p[1] + length * math.cos(r))


# ---------------- poses ----------------
def stand(t=0.0):
    b = math.sin(t * 2.2)
    return dict(BASE, la1=-12 + 3 * b, ra1=12 - 3 * b)


def walk(t, f=7.0, amp=24, lean=3):
    w = math.sin(t * f)
    return dict(BASE, ll1=amp * w, ll2=-amp * 0.9 * max(0, -w), rl1=-amp * w, rl2=-amp * 0.9 * max(0, w),
                la1=-amp * 0.8 * w, la2=14, ra1=amp * 0.8 * w, ra2=14, lean=lean)


def run(t):
    return walk(t, 12, 40, 12)


def mirror(P):
    """Face left instead of right."""
    Q = dict(P)
    Q["lean"] = -P.get("lean", 0)
    Q["head"] = -P.get("head", 0)
    for k in ("la1", "la2", "ra1", "ra2", "ll1", "ll2", "rl1", "rl2"):
        Q[k] = -P.get(k, 0)
    return Q


def phone(t):
    return dict(BASE, head=-22, lean=4, ra1=30, ra2=128, la1=-8)


def sad(t=0.0):
    return dict(BASE, lean=8, head=-20, la1=-3, ra1=3, la2=0, ra2=0)


def celebrate(t):
    wv = 14 * math.sin(t * 10)
    return dict(BASE, la1=-150 + wv, la2=-10, ra1=150 - wv, ra2=10, ll1=-16, rl1=16)


def carry_up(t):
    """Both arms up holding something overhead."""
    return dict(BASE, la1=-165, la2=-10, ra1=165, ra2=10)


def bend(t, k):
    """Bend down to pick something up, k 0..1."""
    return dict(BASE, lean=55 * k, head=10 * k, la1=10 + 20 * k, ra1=25 + 20 * k, ll1=-6 - 20 * k, ll2=30 * k,
                rl1=6 - 10 * k, rl2=20 * k)


def sit(t=0.0):
    return dict(BASE, ll1=84, ll2=-10, rl1=80, rl2=-6, la1=40, la2=20, ra1=50, ra2=20, lean=-6)


def pushup(t, speed=5.0):
    k = 0.5 + 0.5 * math.sin(t * speed)
    return dict(BASE, lean=88, head=-80, ll1=-86, rl1=-87, la1=-4 + 20 * (1 - k), la2=35 * (1 - k),
                ra1=4 + 20 * (1 - k), ra2=35 * (1 - k))


def lie(t=0.0):
    return dict(BASE, lean=-90, head=90, ll1=88, rl1=90, la1=70, ra1=95)


# ---------------- pixel text ----------------
def _find_font():
    for pat in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", "C:/Windows/Fonts/consolab.ttf",
                "C:/Windows/Fonts/courbd.ttf"):
        hits = glob.glob(pat)
        if hits:
            return hits[0]
    return None


_FONT_PATH = _find_font()
_fcache, _tcache = {}, {}


def _font(size):
    if size not in _fcache:
        _fcache[size] = ImageFont.truetype(_FONT_PATH, size) if _FONT_PATH else ImageFont.load_default()
    return _fcache[size]


def text_mask(s, px):
    """Pixel-look text: drawn tiny without anti-aliasing, then scaled up with NEAREST. Returns an L mask."""
    key = (s, px)
    if key in _tcache:
        return _tcache[key]
    k = max(2, round(px / 10))
    f = _font(11)
    tmp = Image.new("L", (1, 1))
    dd = ImageDraw.Draw(tmp)
    sp = 2
    widths = [dd.textlength(c, font=f) for c in s]
    w = int(sum(widths) + sp * max(0, len(s) - 1)) + 2
    m = Image.new("L", (max(1, w), 15), 0)
    dm = ImageDraw.Draw(m)
    dm.fontmode = "1"
    x = 1
    for c, cw in zip(s, widths):
        dm.text((x, 0), c, font=f, fill=255)
        x += cw + sp
    m = m.resize((m.width * k, m.height * k), Image.NEAREST)
    _tcache[key] = m
    return m


def wrap(s, px, max_w=900):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        cand = (cur + " " + w_).strip()
        if cur and text_mask(cand, px).width > max_w:
            lines.append(cur)
            cur = w_
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


# ---------------- canvas ----------------
_cone_cache = {}


def _cone(width, height):
    key = (width, height)
    if key not in _cone_cache:
        m = Image.new("L", (width * 2, height + 80), 0)
        dm = ImageDraw.Draw(m)
        top = width * 0.18
        for i in range(height):
            k = i / height
            half = lerp(top, width * 0.5, k)
            v = int(26 * (0.35 + 0.65 * k))
            dm.line([(width - half, i), (width + half, i)], fill=v)
        dm.ellipse([width - width * 0.62, height - 30, width + width * 0.62, height + 38], fill=70)
        m = m.filter(ImageFilter.GaussianBlur(18))
        _cone_cache[key] = m
    return _cone_cache[key]


class Canvas:
    def __init__(self):
        self.img = _background()[0].copy()
        self.d = ImageDraw.Draw(self.img)
        self.ui = []

    def particles(self, t, n=40):
        """Soft coloured bokeh drifting upward (theme colour)."""
        col = T["particle"]
        for i in range(n):
            ph = (i * 0.6180339) % 1
            x = (ph * W + math.sin(t * 0.4 + i) * 30) % W
            y = FLOOR - ((t * (14 + 9 * (i % 5)) + i * 97) % (FLOOR - 120))
            r = 2 + (i % 4)
            a = 0.45 + 0.5 * (0.5 + 0.5 * math.sin(t * 1.7 + i * 2.3))
            c = mix(T["bg_bot"], col, a)
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=c)

    # lights & props (world: reflected in the floor)
    def spot(self, x, width=320, color=None, strength=1.0, top=FLOOR - 760):
        color = color or mix(T["spot"], (255, 255, 255), 0.35)
        m = _cone(width, FLOOR - top)
        if strength < 1:
            m = m.point(lambda v: int(v * strength))
        self.img.paste(color, (int(x - width), int(top)), m)

    def glow(self, x, y, r, color=GOLD, strength=0.6):
        m = Image.new("L", (r * 4, r * 4), 0)
        ImageDraw.Draw(m).ellipse([r, r, r * 3, r * 3], fill=int(255 * strength))
        m = m.filter(ImageFilter.GaussianBlur(r * 0.6))
        self.img.paste(color, (int(x - 2 * r), int(y - 2 * r)), m)

    def block(self, x0, y0, x1, y1, color=BLOCK, label=None, label_px=20, label_color=(20, 20, 20)):
        shade = mix(color, (0, 0, 0), 0.35)
        self.d.rectangle([x0, y0, x1, y1], fill=shade)
        self.d.rectangle([x0, y0, max(x0, x1 - 4), max(y0, y1 - 4)], fill=color)
        if label:
            self.text(label, (x0 + x1) / 2, (y0 + y1) / 2 - text_mask(label, label_px).height / 2, label_px,
                      label_color, world=True)

    def figure(self, x, P, s=1.0, col=WHITE, foot_y=FLOOR, dy=0.0):
        """Faceless capsule stickman. Feet (lowest point) rest on foot_y unless dy lifts him."""
        lean = P.get("lean", 0)
        hip = (0.0, 0.0)
        neck = pt(hip, 180 - lean, TORSO * s)
        sh = pt(hip, 180 - lean, (TORSO - 10) * s)
        head = pt(neck, 180 - lean - P.get("head", 0), (HEAD_R + 6) * s)
        legs, arms, feet, hands = [], [], {}, {}
        for k in "lr":
            a1, a2 = P[k + "l1"], P.get(k + "l2", 0)
            kn = pt(hip, a1, TH * s)
            ft = pt(kn, a1 + a2, SH * s)
            legs.append([hip, kn, ft])
            feet[k] = ft
        for k in "lr":
            a1, a2 = P[k + "a1"], P.get(k + "a2", 0)
            el = pt(sh, a1, UA * s)
            hd = pt(el, a1 + a2, FA * s)
            arms.append([sh, el, hd])
            hands[k] = hd
        low = max(p[1] for chain in legs + arms for p in chain)
        low = max(low, head[1] + HEAD_R * s)
        ox, oy = x, foot_y - low - dy

        def T(p):
            return (p[0] + ox, p[1] + oy)

        w = max(4, int(LIMB * s))
        dark = mix(col, (0, 0, 0), 0.28)
        for color, extra, off in ((dark, 3, 2), (col, 0, 0)):
            for chain in legs + [[hip, neck]] + arms:
                pts = [(T(p)[0] + off, T(p)[1] + off) for p in chain]
                self.d.line(pts, fill=color, width=w + extra, joint="curve")
                for p in (pts[0], pts[-1]):
                    r = (w + extra) / 2
                    self.d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=color)
            hx, hy = T(head)
            r = HEAD_R * s + extra / 2
            self.d.ellipse([hx - r + off, hy - r + off, hx + r + off, hy + r + off], fill=color)
        hx, hy = T(head)
        hl = mix(col, (255, 255, 255), 0.6)
        self.d.ellipse([hx - HEAD_R * s * 0.55, hy - HEAD_R * s * 0.7, hx - HEAD_R * s * 0.05, hy - HEAD_R * s * 0.2],
                       fill=hl)
        return {"head": T(head), "neck": T(neck), "hip": T(hip), "hands": {k: T(v) for k, v in hands.items()},
                "feet": {k: T(v) for k, v in feet.items()}, "top": T(head)[1] - HEAD_R * s}

    def text(self, s, cx, y, px=26, color=WHITE, world=False, align="center"):
        """Pixel text. world=True draws now (gets reflected); otherwise it is drawn on top after the floor pass."""
        s = s.upper()
        if not world:
            self.ui.append((s, cx, y, px, color, align))
            return
        self._draw_text(s, cx, y, px, color, align)

    def _draw_text(self, s, cx, y, px, color, align):
        m = text_mask(s, px)
        x = cx - m.width / 2 if align == "center" else cx
        self.img.paste(color, (int(x), int(y)), m)

    def lines(self, s, cx, y, px=28, color=WHITE, gap=1.55, max_w=900):
        """Wrapped multi-line UI text. Returns the y below the block."""
        for i, ln in enumerate(wrap(s.upper(), px, max_w)):
            self.text(ln, cx, y + i * px * gap, px, color)
        return y + len(wrap(s.upper(), px, max_w)) * px * gap

    def label(self, s, cx, y, sub=None, color=WHITE, px=26):
        self.text(s, cx, y, px, color)
        if sub:
            self.text(sub, cx, y + px * 1.5, int(px * 0.72), SUB)

    def bubble(self, s, x, y, px=22, tail="down"):
        """Speech bubble anchored at its tail tip (x, y)."""
        m = text_mask(s.upper(), px)
        bw, bh = m.width + 44, m.height + 30
        bx, by = x - bw / 2, y - bh - 26
        self.ui.append(("__bubble__", bx, by, bw, bh, x, y, s.upper(), px))

    def finish(self, t=0.0, handle_xy=None):
        img = self.img
        # glossy floor: mirrored scene, faded and soft
        band = img.crop((0, FLOOR - REF_H, W, FLOOR)).transpose(Image.FLIP_TOP_BOTTOM)
        small = band.resize((W // 3, REF_H // 3)).filter(ImageFilter.GaussianBlur(1.2))
        band = small.resize((W, REF_H))
        img.paste(_background()[1], (0, FLOOR))
        img.paste(band, (0, FLOOR), _fade_mask())
        d = ImageDraw.Draw(img)
        d.line([(0, FLOOR), (W, FLOOR)], fill=mix(T["floor"], (255, 255, 255), 0.12), width=2)
        for item in self.ui:
            if item[0] != "__bubble__":
                self._draw_text(*item)
        # bloom
        small = img.resize((W // 4, H // 4)).filter(ImageFilter.GaussianBlur(5))
        small = small.point(lambda v: int(max(0, v - 80) * 1.5))
        img = ImageChops.screen(img, small.resize((W, H), Image.BILINEAR))
        d = ImageDraw.Draw(img)
        for item in self.ui:  # bubbles stay crisp (no bloom)
            if item[0] == "__bubble__":
                _, bx, by, bw, bh, x, y, s, px = item
                d.rounded_rectangle([bx, by, bx + bw, by + bh], 16, fill=(236, 236, 236))
                d.polygon([(x - 14, by + bh - 1), (x + 14, by + bh - 1), (x, y)], fill=(236, 236, 236))
                img.paste((12, 12, 12), (int(bx + 22), int(by + 15)), text_mask(s, px))
        return img


_fm = None


def _fade_mask():
    global _fm
    if _fm is None:
        g = Image.linear_gradient("L").resize((W, REF_H))
        _fm = g.point(lambda v: int(95 * (1 - v / 255) ** 1.6))
    return _fm


# ---------------- watermark ----------------
def watermark(img, t):
    """Small handle drifting slowly over the whole frame, semi-transparent."""
    m = text_mask(HANDLE, 18).point(lambda v: int(v * 0.33))
    w, h = m.size
    x = (W - w) / 2 + (W - w - 120) / 2 * math.sin(t * 0.37 + 0.6)
    y = (H - h) / 2 + (H - h - 260) / 2 * math.sin(t * 0.23 + 2.1)
    img.paste((230, 230, 230), (int(x), int(y)), m)
    return img


# ---------------- render ----------------
TOP_Y = 270          # statement line
PUNCH_GAP = 18


HOOK_DUR = 1.8
HOOK_STYLES = ["pop", "type", "slide", "shake", "flash", "zoom", "glitch", "drop"]
KICKERS = ["WAIT...", "READ THIS.", "STOP.", "LISTEN.", "TRUTH:", "1% ONLY", "BE HONEST.", "REAL TALK."]


def _hook_tokens(text):
    """Words with accent flag; *several words* marks a whole span."""
    out, inside = [], False
    for w_ in text.split():
        starts = w_.startswith("*")
        core = w_.rstrip(".,!?")
        ends = core.endswith("*") and (len(core) > 1 or not starts)
        acc = inside or starts
        out.append((w_.replace("*", "").upper(), acc))
        if starts and not ends:
            inside = True
        if ends:
            inside = False
    return out


def _scaled_mask(s, px, scale):
    m = text_mask(s, px)
    if abs(scale - 1) < 0.02:
        return m
    return m.resize((max(1, int(m.width * scale)), max(1, int(m.height * scale))), Image.NEAREST)


def draw_hook(img, t, text, style, kicker=None):
    """End card that is also the reel cover: glowing scene, big title, accent words on colour pills."""
    if t >= HOOK_DUR:
        return img
    img = Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), 0.32)
    toks = _hook_tokens(text)
    n = len(" ".join(w for w, _ in toks))
    px = 74 if n < 18 else (64 if n < 30 else 54)
    lines, cur, curw = [], [], 0
    for w_, acc in toks:
        ww = text_mask(w_, px).width + px * 0.7
        if cur and curw + ww > 900:
            lines.append(cur)
            cur, curw = [], 0
        cur.append((w_, acc))
        curw += ww
    if cur:
        lines.append(cur)
    lh = px * 1.9
    y0 = 900 - len(lines) * lh / 2
    scale = 1.0
    if style == "slide":
        y0 += 180 * (1 - ease(t / 0.35))
    if style == "drop":
        y0 -= 500 * (1 - ease(t / 0.3)) - 25 * math.sin(clamp((t - 0.3) / 0.25) * math.pi)
    if style == "zoom":
        scale = 1 + 0.45 * (1 - ease(t / 0.25))
    shake = 0
    if style in ("shake", "glitch") and t < 0.4:
        shake = math.sin(t * 90) * 20 * (1 - t / 0.4)
    # soft dark panel behind the title for contrast
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rounded_rectangle([60, y0 - 150, W - 60, y0 + len(lines) * lh + 90], 40, fill=(0, 0, 0, 120))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(img)
    # top badge
    badge = (kicker or "DAILY 1% BETTER").upper()
    bm = text_mask(badge, 24)
    bx, by = W / 2 - bm.width / 2, y0 - 110
    d.rounded_rectangle([bx - 22, by - 14, bx + bm.width + 22, by + bm.height + 14], 22, fill=T["accent"])
    img.paste((14, 14, 18), (int(bx), int(by)), bm)
    nwords = sum(len(l) for l in lines)
    total_chars = sum(len(w_) for l in lines for w_, _ in l)
    shown_words = nwords if style != "pop" else int(clamp(t / 0.6) * nwords) + 1
    shown_chars = total_chars if style != "type" else int(clamp(t / 0.7) * total_chars) + 1
    k = chars = 0
    for li, line in enumerate(lines):
        masks = [_scaled_mask(w_, px, scale) for w_, _ in line]
        gap = px * 0.7 * scale
        x = W / 2 - (sum(m.width for m in masks) + gap * (len(line) - 1)) / 2 + shake
        yy = y0 + li * lh - (masks[0].height - text_mask(line[0][0], px).height) / 2
        for (w_, acc), m in zip(line, masks):
            k += 1
            if k > shown_words:
                break
            if style == "type":
                left = shown_chars - chars
                if left <= 0:
                    break
                m = text_mask(w_[:left], px)
            chars += len(w_)
            if acc:  # accent word: dark text on a bright pill
                d.rounded_rectangle([x - 14, yy - 12, x + m.width + 14, yy + m.height + 12], 14, fill=T["accent"])
                img.paste((12, 12, 16), (int(x), int(yy)), m)
            else:
                img.paste((0, 0, 0), (int(x + 4), int(yy + 5)), m)
                if style == "glitch" and t < 0.5:
                    img.paste((255, 40, 80), (int(x - 8), int(yy)), m)
                    img.paste((40, 220, 255), (int(x + 8), int(yy)), m)
                img.paste(WHITE, (int(x), int(yy)), m)
            x += m.width + gap
    hm = text_mask(HANDLE, 22)
    img.paste(mix(SUB, T["accent2"], 0.4), (int(W / 2 - hm.width / 2), int(y0 + len(lines) * lh + 30)), hm)
    if style in ("flash", "zoom", "drop") and t < 0.15:
        img = Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), 0.6 * (1 - t / 0.15))
    return img


def hook_sfx(style, n_words):
    ev = [(0.0, "impact", 1.0), (0.0, "whoosh", 0.8), (0.05, "riser", 0.0), (HOOK_DUR - 0.12, "whoosh", 0.8)]
    if style == "pop":
        ev += [(i * 0.6 / max(1, n_words), "pop", 0.8) for i in range(n_words)]
    elif style == "type":
        ev += [(i * 0.1, "pop", 0.4) for i in range(7)]
    elif style in ("shake", "glitch"):
        ev += [(0.02, "snap", 1.0), (0.45, "heartbeat", 0.9)]
    elif style == "slide":
        ev += [(0.05, "swell", 0.7)]
    elif style in ("flash", "zoom"):
        ev += [(0.0, "flash", 1.0)]
    elif style == "drop":
        ev += [(0.3, "thud", 1.0)]
    return ev


# ---------------- global animation layers (applied to every reel) ----------------
BEAT_KINDS = {"pop", "thud", "step", "impact", "snap", "chime", "flash"}


def _beat_times(ev):
    return sorted({round(e[0], 2) for e in ev if e[1] in BEAT_KINDS})


def camera(img, t, dur, shakes, punch_t):
    """Slow push-in (starts zoomed during the hook), beat bumps, and shake on impacts."""
    z = 1.0 + 0.05 * ease(t / dur)
    if t < 0.5:
        z += 0.06 * (1 - ease(t / 0.5))  # quick punch-in on frame 0
    if 0 <= t - punch_t < 0.3:
        z += 0.05 * (1 - (t - punch_t) / 0.3)
    dx = dy = 0.0
    for st, strength in shakes:
        a = t - st
        if 0 <= a < 0.3:
            k = (1 - a / 0.3) ** 2 * strength
            dx += math.sin(a * 91.0 + st * 7) * 22 * k
            dy += math.cos(a * 77.0 + st * 3) * 16 * k
    dx += 6 * math.sin(t * 0.7)
    cw, ch = W / z, H / z
    x0 = min(max((W - cw) / 2 + dx, 0), W - cw)
    y0 = min(max((H - ch) / 2 + dy, 0), H - ch)
    return img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))


def ripples(img, t, beats, seed):
    """Light rings spreading on the floor at every beat."""
    d = ImageDraw.Draw(img)
    for i, bt in enumerate(beats):
        a = t - bt
        if 0 <= a < 0.7:
            k = a / 0.7
            x = W * (0.3 + 0.4 * ((i * 0.618 + seed * 0.13) % 1))
            rx, ry = 40 + 260 * k, 8 + 40 * k
            col = mix(T["bg_bot"], T["accent2"], 0.9 * (1 - k))
            d.ellipse([x - rx, FLOOR - ry + 10, x + rx, FLOOR + ry + 10], outline=col, width=3)
    return img


_sweep_m = None


def light_sweep(img, t):
    """A soft diagonal light band crossing the frame every 5 s."""
    global _sweep_m
    ph = (t % 5.0) / 1.2
    if ph > 1:
        return img
    if _sweep_m is None:
        m = Image.new("L", (W // 4, H // 4), 0)
        ImageDraw.Draw(m).polygon([(0, 0), (60, 0), (W // 4 - 200, H // 4), (W // 4 - 260, H // 4)], fill=46)
        _sweep_m = m.filter(ImageFilter.GaussianBlur(14)).resize((W, H))
    x = int(-W + 2 * W * ease(ph))
    m = Image.new("L", (W, H), 0)
    m.paste(_sweep_m, (x, 0))
    img.paste(mix(T["spot"], (255, 255, 255), 0.5), (0, 0), m)
    return img


def shooting_stars(img, t, seed):
    d = ImageDraw.Draw(img)
    for i in range(2):
        period = 3.3 + i * 1.7
        a = ((t + i * 1.1 + seed * 0.37) % period) / 0.6
        if a > 1:
            continue
        x0 = W * ((0.2 + 0.5 * ((seed + i) * 0.618 % 1)))
        y0 = 120 + 160 * i
        x, y = x0 + 520 * a, y0 + 200 * a
        for j in range(10):
            f = j / 10
            d.line([(x - 26 * j, y - 10 * j), (x - 26 * (j + 1), y - 10 * (j + 1))],
                   fill=mix(T["bg_top"], (255, 255, 255), 1 - f), width=3)
    return img


def vignette_pulse(img, t, beats):
    """Edges breathe darker, and briefly brighten on beats."""
    k = 0.0
    for bt in beats:
        if 0 <= t - bt < 0.25:
            k = max(k, 1 - (t - bt) / 0.25)
    if k > 0:
        img = Image.blend(img, Image.new("RGB", (W, H), T["accent2"]), 0.06 * k)
    return img


def progress_bar(img, t, dur):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 7], fill=(20, 20, 24))
    d.rectangle([0, 0, int(W * t / dur), 7], fill=T["accent"])
    return img


def confetti_burst(img, t, at, seed):
    """Coloured confetti falling after the punchline."""
    a = t - at
    if a < 0 or a > 2.5:
        return img
    d = ImageDraw.Draw(img)
    cols = [T["accent"], T["accent2"], GOLD, (255, 255, 255), T["spot"]]
    for i in range(46):
        r = (i * 0.618 + seed * 0.1) % 1
        x = W * r + math.sin(a * 3 + i) * 40
        y = 160 + a * (420 + 260 * ((i * 0.37) % 1)) - 120 * math.sin(i)
        if y > FLOOR:
            continue
        w_ = 8 + (i % 3) * 4
        ang = a * 8 + i
        dx, dy = math.cos(ang) * w_, math.sin(ang) * w_ / 2
        d.polygon([(x - dx, y - dy), (x + dy, y - dx), (x + dx, y + dy), (x - dy, y + dx)], fill=cols[i % len(cols)])
    return img


OPEN_DUR = 2.2


def _layout_words(toks, px, max_w=900):
    lines, cur, curw = [], [], 0
    for w_, acc in toks:
        ww = text_mask(w_, px).width + px * 0.7
        if cur and curw + ww > max_w:
            lines.append(cur)
            cur, curw = [], 0
        cur.append((w_, acc))
        curw += ww
    if cur:
        lines.append(cur)
    return lines


def draw_open_hook(img, t, text):
    """Big hook over the running animation for the first OPEN_DUR seconds (no dimming, no delay)."""
    if t >= OPEN_DUR:
        return img
    toks = _hook_tokens(text)
    n = len(" ".join(w for w, _ in toks))
    px = 72 if n < 18 else (64 if n < 30 else 56)
    lines = _layout_words(toks, px)
    lh = px * 1.9
    exit_k = ease(clamp((t - 1.75) / 0.35))
    scale = 1 - 0.35 * exit_k
    alpha = 1 - clamp(exit_k * 1.4)
    if alpha <= 0:
        return img
    y_center = 700 - 220 * exit_k
    block_h = len(lines) * lh
    y0 = y_center - block_h / 2
    nwords = sum(len(l) for l in lines)
    shown = int(clamp(t / 0.45) * nwords) + 1
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    pad_x = 470 * scale + 40
    od.rounded_rectangle([W / 2 - pad_x, y0 - 40 * scale, W / 2 + pad_x, y0 + block_h * scale + 20],
                         int(36 * scale) + 4, fill=(0, 0, 0, int(130 * alpha)))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(img)
    k = 0
    for li, line in enumerate(lines):
        masks = []
        for w_, _ in line:
            m = text_mask(w_, px)
            if scale < 0.99:
                m = m.resize((max(1, int(m.width * scale)), max(1, int(m.height * scale))), Image.NEAREST)
            masks.append(m)
        gap = px * 0.7 * scale
        x = W / 2 - (sum(m.width for m in masks) + gap * (len(line) - 1)) / 2
        yy = y0 + li * lh * scale
        for (w_, acc), m in zip(line, masks):
            k += 1
            if k > shown:
                break
            pop = 1.0
            wt = t - (k - 1) * 0.45 / max(1, nwords)
            if 0 <= wt < 0.12:
                pop = 1 + 0.25 * (1 - wt / 0.12)
            mm = m if pop == 1.0 else m.resize((max(1, int(m.width * pop)), max(1, int(m.height * pop))), Image.NEAREST)
            ox, oy = (mm.width - m.width) / 2, (mm.height - m.height) / 2
            if acc:
                d.rounded_rectangle([x - 14 - ox, yy - 12 - oy, x + m.width + 14 + ox, yy + m.height + 12 + oy],
                                    14, fill=mix((0, 0, 0), T["accent"], alpha))
                img.paste(mix((0, 0, 0), (12, 12, 16), alpha), (int(x - ox), int(yy - oy)), mm)
            else:
                img.paste((0, 0, 0), (int(x - ox + 4), int(yy - oy + 5)), mm)
                img.paste(mix((0, 0, 0), WHITE, alpha), (int(x - ox), int(yy - oy)), mm)
            x += m.width + gap
    return img


def day_badge(img, day):
    if not day:
        return img
    s_ = f"DAY {int(day)} / 365"
    m = text_mask(s_, 20)
    d = ImageDraw.Draw(img)
    x, y = 60, 120
    d.rounded_rectangle([x - 16, y - 12, x + m.width + 16, y + m.height + 12], 18, fill=T["accent"])
    img.paste((14, 14, 18), (x, y), m)
    return img


def follow_cta(img, a, text):
    """Animated follow button; a = seconds since the CTA started (lasts ~2.2 s)."""
    slide = ease(clamp(a / 0.35))
    y = 1480 + 260 * (1 - slide)
    d = ImageDraw.Draw(img)
    if text:
        toks = _hook_tokens(text)
        widths = [text_mask(w_, 30).width for w_, _ in toks]
        gap = 20
        x = W / 2 - (sum(widths) + gap * (len(toks) - 1)) / 2
        ty = y - 92
        for (w_, acc), ww in zip(toks, widths):
            m = text_mask(w_, 30)
            if acc:
                d.rounded_rectangle([x - 10, ty - 8, x + ww + 10, ty + m.height + 8], 10, fill=T["accent"])
                img.paste((12, 12, 16), (int(x), int(ty)), m)
            else:
                img.paste((0, 0, 0), (int(x + 3), int(ty + 4)), m)
                img.paste(WHITE, (int(x), int(ty)), m)
            x += ww + gap
    tapped = a >= 0.95
    pulse = 1.0
    if 0.8 <= a < 1.1:
        pulse = 1 - 0.12 * math.sin((a - 0.8) / 0.3 * math.pi)
    label = "FOLLOWING" if tapped else "FOLLOW"
    m = text_mask(label, 30)
    bw, bh = (m.width + 130) * pulse, 84 * pulse
    bx, by = W / 2 - bw / 2, y - bh / 2 + 20
    fill = mix(T["accent"], (255, 255, 255), 0.15) if tapped else (245, 245, 248)
    d.rounded_rectangle([bx, by, bx + bw, by + bh], int(bh / 2), fill=fill)
    ix, iy = bx + 42 * pulse, by + bh / 2
    if tapped:
        d.line([(ix - 12, iy), (ix - 3, iy + 10), (ix + 14, iy - 10)], fill=(14, 14, 18), width=6)
    else:
        d.line([(ix - 13, iy), (ix + 13, iy)], fill=(14, 14, 18), width=6)
        d.line([(ix, iy - 13), (ix, iy + 13)], fill=(14, 14, 18), width=6)
    img.paste((14, 14, 18), (int(ix + 30 * pulse), int(iy - m.height / 2)), m)
    if 0.75 <= a < 1.25:  # finger tap ring
        r = 20 + 60 * (a - 0.75) / 0.5
        d.ellipse([W / 2 + bw / 2 - 60 - r, iy - r, W / 2 + bw / 2 - 60 + r, iy + r],
                  outline=mix((0, 0, 0), WHITE, 1 - (a - 0.75) / 0.5), width=4)
    return img


def render(spec, draw, events, out_path, seed=0):
    """spec: dict with dur, top, punch, punch_at, hook, hook_style, theme.
    draw(c, t, spec): draws the scene. events: (t, kind[, gain]) for audio.
    Returns thumb_offset (ms) = a frame showing the hook."""
    import audio
    set_theme(spec.get("theme", seed))
    story = float(spec["dur"])
    punch_t = spec.get("punch_at", 0.66) * story
    hook, style = spec.get("hook"), spec.get("hook_style", "pop")
    end_t = story  # the hook card plays after the story, as the closing card
    dur = story + (HOOK_DUR if hook else 0)
    if style not in HOOK_STYLES:
        style = "pop"
    kicker = KICKERS[seed % len(KICKERS)] if hook else None
    ev = []
    for e in events:
        g = e[2] if len(e) > 2 else 0.5
        ev.append((e[0], e[1], min(1.0, g * 1.8)))
    if hook:
        ev += [(end_t + e[0], e[1], e[2]) for e in hook_sfx(style, len(hook.split())) if e[2] > 0]
    ev += [(0.0, "impact", 0.8), (0.0, "whoosh", 0.7), (0.05, "pop", 0.5)]  # start straight into the action
    open_hook = spec.get("open_hook")
    if open_hook:
        nw = len(open_hook.split())
        ev += [(i * 0.45 / max(1, nw), "pop", 0.6) for i in range(nw)] + [(1.85, "whoosh", 0.6)]
    follow_text = spec.get("follow_cta")
    cta_t = story - 2.2
    ev += [(cta_t, "whoosh", 0.5), (cta_t + 0.95, "pop", 0.8), (cta_t + 0.97, "chime", 0.7)]
    if spec.get("punch"):
        ev += [(punch_t - 1.0, "riser", 0.7), (punch_t, "impact", 0.9), (punch_t, "flash", 0.7),
               (punch_t + 0.1, "chime", 0.6)]
    beats = _beat_times(ev)
    shakes = [(e[0], 0.25 + 0.6 * e[2]) for e in ev if e[1] in ("impact", "thud", "snap") and e[0] > 0.1]
    wav = out_path + ".wav"
    audio.build_audio(wav, dur, seed, ev)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-shortest",
           "-movflags", "+faststart", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    top_from = 2.15 if open_hook else 0
    for fi in range(int(dur * FPS)):
        t = fi / FPS
        st = min(t, story - 1 / FPS)  # story time; frozen on the last story frame under the end card
        c = Canvas()
        if not spec.get("gh"):
            c.particles(t)
        draw(c, st, spec)
        y = TOP_Y
        top = spec.get("top")
        if top and t >= top_from:
            n = int(clamp((t - top_from) / 0.5) * len(top)) + 1  # typewriter
            c.lines(top[:n], W / 2, y, 30, spec.get("top_color", WHITE))
            y = TOP_Y + 30 * 1.55 * len(wrap(top.upper(), 30))
        if spec.get("punch") and t >= punch_t:
            k = clamp((t - punch_t) / 0.22)
            px = int(30 + 14 * (1 - ease(k)))  # slam in big, settle
            c.lines(spec["punch"], W / 2, y + PUNCH_GAP, px, spec.get("punch_color", T["accent"]))
        img = c.finish(t)
        if not spec.get("gh"):  # the room style keeps a clean, calm look
            img = ripples(img, t, beats, seed)
            img = light_sweep(img, t)
            img = shooting_stars(img, t, seed)
        if spec.get("punch"):
            img = confetti_burst(img, t, punch_t, seed)
        img = camera(img, st, story, shakes, punch_t)
        img = vignette_pulse(img, t, beats)
        if open_hook:
            img = draw_open_hook(img, t, open_hook)
        if cta_t <= t < story:
            img = follow_cta(img, t - cta_t, follow_text or "FOLLOW FOR *DAILY* 1% BETTER")
        if hook and t >= end_t:
            img = draw_hook(img, t - end_t, hook, style, kicker)
        img = day_badge(img, spec.get("day"))
        img = progress_bar(img, t, dur)
        img = watermark(img, t)
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed")
    os.remove(wav)
    return int((end_t + 1.0) * 1000) if hook else int(min(dur - 0.5, punch_t + 1.0) * 1000)


if __name__ == "__main__":
    def demo(c, t, spec):
        c.spot(330)
        c.spot(750, strength=0.6)
        c.label("PERFECTIONIST", 330, 600, "BRICK 1")
        c.label("ACTION TAKER", 750, 600, "BRICK 7", color=WHITE)
        c.figure(300, stand(t), col=GREY)
        c.block(345, FLOOR - 40, 425, FLOOR, label=None)
        for i in range(4):
            c.block(620 + i * 70, FLOOR - 40 * (i + 1), 690 + i * 70, FLOOR - 40 * i)
        c.figure(760, walk(t))
        c.bubble("LATER.", 300, 820)
    spec = {"dur": 1.0, "top": "Start before you're ready.", "punch": "Done beats perfect.", "punch_at": 0.0}
    c = Canvas()
    demo(c, 0.4, spec)
    y = c.lines(spec["top"], W / 2, TOP_Y, 30)
    c.lines(spec["punch"], W / 2, y + PUNCH_GAP, 30, GOLD)
    os.makedirs("out", exist_ok=True)
    watermark(c.finish(0.4), 0.4).save("out/nv_demo.png")
    print("ok")
