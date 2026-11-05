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
        self.img = Image.new("RGB", (W, H), BG)
        self.d = ImageDraw.Draw(self.img)
        self.ui = []

    # lights & props (world: reflected in the floor)
    def spot(self, x, width=320, color=(255, 255, 255), strength=1.0, top=FLOOR - 760):
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
        img.paste(Image.new("RGB", (W, H - FLOOR), BG), (0, FLOOR))
        img.paste(band, (0, FLOOR), _fade_mask())
        d = ImageDraw.Draw(img)
        d.line([(0, FLOOR), (W, FLOOR)], fill=(30, 30, 33), width=2)
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


def render(spec, draw, events, out_path, seed=0):
    """spec: dict with dur, top (statement line, optional), punch (optional), punch_at (0..1, default 0.66).
    draw(c, t, spec): draws the scene. events: list of (t, kind[, gain]) for audio.
    Returns thumb_offset (ms)."""
    import audio
    dur = float(spec["dur"])
    wav = out_path + ".wav"
    audio.build_audio(wav, dur, seed, events)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-shortest",
           "-movflags", "+faststart", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    punch_t = spec.get("punch_at", 0.66) * dur
    for fi in range(int(dur * FPS)):
        t = fi / FPS
        c = Canvas()
        draw(c, t, spec)
        y = TOP_Y
        if spec.get("top"):
            y = c.lines(spec["top"], W / 2, y, 30, spec.get("top_color", WHITE))
        if spec.get("punch") and t >= punch_t:
            c.lines(spec["punch"], W / 2, y + PUNCH_GAP, 30, spec.get("punch_color", GOLD))
        if t > dur - 1.4:
            c.text("FOLLOW FOR DAILY 1% BETTER", W / 2, 1560, 20, SUB)
        img = watermark(c.finish(t), t)
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed")
    os.remove(wav)
    return int(min(dur - 0.5, punch_t + 1.0) * 1000)


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
