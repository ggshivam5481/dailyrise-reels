"""Cinematic post effects for the stickman reels (Pillow only, cached, a few ms per frame each).

  camera(img, t, dur, shakes)   slow push-in + decaying screen shake
  grade(img, t)                 colour grade + vignette + animated film grain
  light_rays(img, t, origin)    soft god-rays from the moon / a light, slowly turning
  flash(img, amount)            warm white flash
  hook(img, t, text, dur)       slam-in hook title for the first seconds ("*word*" = warm accent)
  cta(img, k, title)            end card: FOLLOW + handle + like/comment/save row
  ornaments(img, t)             corner ticks, small label, ticking timecode
"""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import render as R

W, H, FPS = R.W, R.H, R.FPS
BLACK = (0, 0, 0)
_cache = {}


def _ease_out(x):
    x = R.clamp(x)
    return 1 - (1 - x) ** 3


def _solid(color):
    key = ("solid", color)
    if key not in _cache:
        _cache[key] = Image.new("RGB", (W, H), color)
    return _cache[key]


def _fade_mask(mask, a):
    """Scale an L mask by alpha a (0..1)."""
    if a >= 0.999:
        return mask
    return mask.point(lambda v: int(v * a))


# ---------------- camera ----------------
def camera(img, t, dur, shakes=()):
    z = 1.0 + 0.06 * R.ease(t / max(dur, 0.01))
    dx = dy = 0.0
    for st, strength in shakes:
        a = t - st
        if 0 <= a < 0.35:
            k = (1 - a / 0.35) ** 2 * strength
            dx += math.sin(a * 91.0 + st * 7) * 26 * k
            dy += math.cos(a * 77.0 + st * 3) * 20 * k
    cw, ch = W / z, H / z
    x0 = (W - cw) / 2 + dx
    y0 = (H - ch) / 2 + dy
    x0 = min(max(x0, 0), W - cw)
    y0 = min(max(y0, 0), H - ch)
    if z < 1.0005 and abs(dx) + abs(dy) < 0.5:
        return img
    return img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))


# ---------------- grade ----------------
def _grade_lut():
    if "lut" not in _cache:
        r, g, b = [], [], []
        for v in range(256):
            x = v / 255
            # cool lifted shadows, warm soft highlights, gentle S-curve
            s = 0.022 + 0.978 * (x * x * (3 - 2 * x) * 0.35 + x * 0.65)
            r.append(int(255 * R.clamp(s + 0.045 * max(0, x - 0.55))))
            g.append(int(255 * R.clamp(s + 0.012 * (1 - x))))
            b.append(int(255 * R.clamp(s + 0.05 * (1 - x) * (1 - x) - 0.03 * max(0, x - 0.6))))
        _cache["lut"] = r + g + b
    return _cache["lut"]


def _vignette_l():
    if "vig" not in _cache:
        sw, sh = W // 8, H // 8
        m = Image.new("L", (sw, sh))
        px = m.load()
        for y in range(sh):
            for x in range(sw):
                nx = (x - sw / 2) / (sw / 2)
                ny = (y - sh / 2) / (sh / 2)
                dd = math.sqrt(nx * nx + ny * ny * 0.75)
                px[x, y] = int(255 * (1 - 0.55 * R.clamp((dd - 0.45) / 0.85) ** 1.6))
        _cache["vig"] = m.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(4))
    return _cache["vig"]


def _grade_tiles(n=8):
    """Vignette x film grain, baked: one multiply per frame does both."""
    if "gtiles" not in _cache:
        vig = _vignette_l()
        tiles = []
        for _ in range(n):
            g = Image.effect_noise((W // 2, H // 2), 40).resize((W, H), Image.NEAREST)
            g = g.point(lambda v: min(255, int(255 * (0.93 + 0.07 * v / 128))))
            m = ImageChops.multiply(vig, g)
            tiles.append(Image.merge("RGB", (m, m, m)))
        _cache["gtiles"] = tiles
    return _cache["gtiles"]


def grade(img, t):
    tiles = _grade_tiles()
    return ImageChops.multiply(img.point(_grade_lut()), tiles[int(t * FPS) % len(tiles)])


# ---------------- light rays ----------------
PHASES = 24


def _rays(origin, strength):
    key = ("rays", origin, round(strength, 3))
    if key in _cache:
        return _cache[key]
    sc = 2  # half resolution
    sw, sh = W // sc, H // sc
    ox, oy = origin[0] / sc, origin[1] / sc
    rnd = random.Random(7)
    beams = [(rnd.uniform(20, 160), rnd.uniform(1.5, 5), rnd.uniform(0.45, 1.0)) for _ in range(11)]
    rad = Image.radial_gradient("L").resize((sw * 2, sw * 2))
    fall = rad.crop((int(sw - ox), int(sw - oy), int(sw - ox) + sw, int(sw - oy) + sh))
    fall = fall.point(lambda v: max(0, 255 - int(v * 1.35)))
    # no rays on the ground: fade out over the 60 px above GROUND
    gy = R.GROUND // sc
    cut = Image.new("L", (sw, sh), 255)
    cd = ImageDraw.Draw(cut)
    for i in range(30):
        cd.line([(0, gy - 30 + i), (sw, gy - 30 + i)], fill=int(255 * (1 - i / 30)))
    cd.rectangle([0, gy, sw, sh], fill=0)
    fall = ImageChops.multiply(fall, cut)
    frames = []
    warm = (255, 216, 160)
    box = None
    for ph in range(PHASES):
        rot = 14 * math.sin(2 * math.pi * ph / PHASES)  # gentle sway, loops cleanly
        m = Image.new("L", (sw, sh))
        d = ImageDraw.Draw(m)
        for ang, width, a in beams:
            a0, a1 = math.radians(ang + rot), math.radians(ang + rot + width)
            L = 1400
            pts = [(ox, oy), (ox + math.cos(a0) * L, oy + math.sin(a0) * L),
                   (ox + math.cos(a1) * L, oy + math.sin(a1) * L)]
            flick = 0.7 + 0.3 * math.sin(2 * math.pi * ph / PHASES * 3 + ang)
            d.polygon(pts, fill=int(255 * a * flick))
        m = ImageChops.multiply(m, fall).filter(ImageFilter.GaussianBlur(5))
        m = m.point(lambda v: int(v * strength))
        frames.append(m)
        bb = m.getbbox()
        if bb:
            box = bb if box is None else (min(box[0], bb[0]), min(box[1], bb[1]), max(box[2], bb[2]), max(box[3], bb[3]))
    box = box or (0, 0, 1, 1)
    full = (box[0] * sc, box[1] * sc, box[2] * sc, box[3] * sc)
    out = []
    for m in frames:
        c = m.crop(box).resize((full[2] - full[0], full[3] - full[1]), Image.BILINEAR)
        out.append(Image.merge("RGB", [c.point(lambda v, k=k: v * k // 255) for k in warm]))
    _cache[key] = (out, full)
    return _cache[key]


def light_rays(img, t, origin=(780, 430), strength=0.22):
    frames, box = _rays(tuple(origin), strength)
    f = frames[int(t * FPS / 3) % PHASES]
    img = img.copy() if img.readonly else img
    region = img.crop(box)
    img.paste(ImageChops.add(region, f), box[:2])
    return img


# ---------------- flash ----------------
def flash(img, amount):
    if amount <= 0.002:
        return img
    return Image.blend(img, _solid(R.WARM2), R.clamp(amount) * 0.85)


# ---------------- text blocks ----------------
def _parse(text):
    words = []
    for w in text.split():
        core = w.rstrip(".,!?")
        acc = core.startswith("*") or core.endswith("*")
        words.append((w.replace("*", "").upper(), acc))
    return words


def _text_block(text, size, max_w=900, sp=6, lh_extra=26, color=None):
    """Render (rgb_crop, alpha_mask) for wrapped text; '*word*' words in WARM."""
    key = ("tb", text, size, max_w, sp, color)
    if key in _cache:
        return _cache[key]
    f = R.font(size)
    probe = ImageDraw.Draw(Image.new("L", (8, 8)))
    space = probe.textlength(" ", font=f) + sp
    lines, cur = [], []
    for w, acc in _parse(text):
        trial = " ".join(x[0] for x in cur + [(w, acc)])
        if cur and R.text_w(probe, trial, f, sp) > max_w:
            lines.append(cur)
            cur = [(w, acc)]
        else:
            cur.append((w, acc))
    if cur:
        lines.append(cur)
    lh = size + lh_extra
    bw, bh = max_w + 120, len(lines) * lh + 60
    rgb = Image.new("RGB", (bw, bh), BLACK)
    mask = Image.new("L", (bw, bh))
    dr, dm = ImageDraw.Draw(rgb), ImageDraw.Draw(mask)
    for i, ln in enumerate(lines):
        widths = [R.text_w(probe, w, f, sp) for w, _ in ln]
        total = sum(widths) + space * (len(ln) - 1)
        x = bw / 2 - total / 2
        y = 30 + i * lh
        for (w, acc), ww in zip(ln, widths):
            col = R.WARM if acc else (color or R.WHITE)
            for c in w:
                dr.text((x, y), c, font=f, fill=col)
                dm.text((x, y), c, font=f, fill=255)
                x += probe.textlength(c, font=f) + sp
            x += space
    _cache[key] = (rgb, mask)
    return rgb, mask


def _paste_block(img, block, cx, cy, scale=1.0, alpha=1.0, blur=0.0, ca=0.0):
    rgb, mask = block
    if scale != 1.0:
        sz = (max(1, int(rgb.width * scale)), max(1, int(rgb.height * scale)))
        rgb, mask = rgb.resize(sz, Image.BILINEAR), mask.resize(sz, Image.BILINEAR)
    if blur > 0.3:
        rgb = rgb.filter(ImageFilter.GaussianBlur(blur))
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    m = _fade_mask(mask, alpha)
    x, y = int(cx - rgb.width / 2), int(cy - rgb.height / 2)
    if ca > 0.5:
        cm = _fade_mask(mask, alpha * 0.55)
        img.paste((255, 40, 70), (x + int(ca), y), cm)
        img.paste((40, 210, 255), (x - int(ca), y), cm)
    img.paste(rgb, (x, y), m)


# ---------------- hook ----------------
def hook(img, t, text, dur=1.8):
    if t >= dur or not text:
        return img
    out_t = dur - 0.35
    dark = 0.55 if t < out_t else 0.55 * (1 - (t - out_t) / 0.35)
    img = Image.blend(img, _solid(BLACK), dark)
    nwords = len(text.split())
    size = 104 if nwords <= 6 else 92
    block = _text_block(text, size)
    land = 0.18
    if t < land:
        k = _ease_out(t / land)
        scale, alpha, blur = 1.35 - 0.35 * k, k, 8 * (1 - k)
        ca = 14 * (1 - k) + 4
    elif t < out_t:
        a = t - land
        scale, alpha, blur = 1.0, 1.0, 0
        ca = 6 * math.exp(-a * 18) * abs(math.sin(a * 60))  # small glitch settle
    else:
        k = R.ease((t - out_t) / 0.35)
        scale, alpha, blur, ca = 1.0 - 0.08 * k, 1 - k, 0, 0
    _paste_block(img, block, W / 2, 880, scale, alpha, blur, ca)
    # warm tick under the hook
    if t >= land * 0.6:
        d = ImageDraw.Draw(img)
        k = _ease_out((t - land * 0.6) / 0.3) * (alpha if t >= out_t else 1)
        half = 70 * k
        yb = 880 + block[0].height / 2 * scale + 6
        d.line([(W / 2 - half, yb), (W / 2 + half, yb)], fill=R.WARM, width=5)
    return img


# ---------------- CTA ----------------
def _icon(kind, size=74, filled=False):
    key = ("icon", kind, size, filled)
    if key in _cache:
        return _cache[key]
    s = size
    m = Image.new("L", (s + 8, s + 8))
    d = ImageDraw.Draw(m)
    lw = 5
    o = 4
    if kind == "heart":
        pts = []
        for i in range(64):
            a = 2 * math.pi * i / 64
            x = 16 * math.sin(a) ** 3
            y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
            pts.append((o + s / 2 + x * s / 36, o + s / 2 - y * s / 36 - 2))
        if filled:
            d.polygon(pts, fill=255)
        else:
            d.line(pts + [pts[0]], fill=255, width=lw, joint="curve")
    elif kind == "comment":
        d.ellipse([o + 4, o + 6, o + s - 4, o + s - 14], outline=255, width=lw)
        d.polygon([(o + 16, o + s - 24), (o + 10, o + s), (o + 32, o + s - 16)], fill=255)
    else:  # bookmark
        x0, x1, y0, y1 = o + s * 0.24, o + s * 0.76, o + 4, o + s - 2
        pts = [(x0, y0), (x1, y0), (x1, y1), ((x0 + x1) / 2, y1 - s * 0.24), (x0, y1), (x0, y0)]
        if filled:
            d.polygon(pts, fill=255)
        else:
            d.line(pts, fill=255, width=lw, joint="curve")
    _cache[key] = m
    return m


def _appear(k, k0, span=0.16):
    a = _ease_out((k - k0) / span)
    return a, (1 - a) * 34


def cta(img, k, title=None):
    k = R.clamp(k)
    img = Image.blend(img, _solid(BLACK), 0.7 * R.ease(k / 0.18))
    d = ImageDraw.Draw(img)
    if title:
        a, dy = _appear(k, 0.06)
        if a > 0:
            _paste_block(img, _text_block(title, 34, max_w=860, sp=5, color=R.MUTED), W / 2, 610 + dy, alpha=a)
    a, dy = _appear(k, 0.12)
    if a > 0:
        _paste_block(img, _text_block("FOLLOW", 132, sp=18), W / 2, 760 + dy, alpha=a)
    # warm underline grows
    u = _ease_out((k - 0.22) / 0.3)
    if u > 0:
        d.line([(W / 2 - 230 * u, 852), (W / 2 + 230 * u, 852)], fill=R.WARM, width=5)
        d.ellipse([W / 2 + 230 * u - 6, 846, W / 2 + 230 * u + 6, 858], fill=R.WARM)
    a, dy = _appear(k, 0.24)
    if a > 0:
        _paste_block(img, _text_block(R.HANDLE.upper(), 50, sp=8, color=R.WARM), W / 2, 930 + dy, alpha=a)
    a, dy = _appear(k, 0.34)
    if a > 0:
        _paste_block(img, _text_block("FOR DAILY 1% BETTER", 34, sp=8, color=R.MUTED), W / 2, 1005 + dy, alpha=a)
    labels = [("heart", "LIKE"), ("comment", "COMMENT"), ("bookmark", "SAVE")]
    f = R.font(26)
    for i, (kind, lab) in enumerate(labels):
        a, dy = _appear(k, 0.46 + i * 0.07, 0.14)
        if a <= 0:
            continue
        cx = W / 2 + (i - 1) * 250
        filled = kind in ("heart", "bookmark") and k > 0.78 + 0.06 * (kind == "bookmark")
        pop = 1.0
        if filled:
            pk = (k - (0.78 + 0.06 * (kind == "bookmark"))) / 0.08
            pop = 1 + 0.22 * math.sin(math.pi * R.clamp(pk))
        m = _icon(kind, int(74 * pop), filled)
        col = R.WARM if filled else R.WHITE
        img.paste(col, (int(cx - m.width / 2), int(1150 + dy - m.height / 2)), _fade_mask(m, a))
        R.spaced(d, cx, 1205 + dy, lab, f, tuple(int(c * a) for c in R.MUTED), 5)
    # thin progress ornament
    p = _ease_out((k - 0.1) / 0.85)
    if p > 0:
        d.line([(W / 2 - 300, 1320), (W / 2 + 300, 1320)], fill=(44, 48, 58), width=2)
        d.line([(W / 2 - 300, 1320), (W / 2 - 300 + 600 * p, 1320)], fill=R.WARM, width=2)
    return img


# ---------------- ornaments ----------------
def _orn_layer():
    if "orn" not in _cache:
        m = Image.new("L", (W, H))
        d = ImageDraw.Draw(m)
        mg, L = 54, 46
        for (x, y, sx, sy) in [(mg, mg, 1, 1), (W - mg, mg, -1, 1), (mg, H - mg, 1, -1), (W - mg, H - mg, -1, -1)]:
            d.line([(x, y), (x + sx * L, y)], fill=150, width=3)
            d.line([(x, y), (x, y + sy * L)], fill=150, width=3)
        R.spaced(d, 250, 92, "DAILY  1%  BETTER", R.font(22), 160, 4)
        pieces = []
        for box in [(0, 0, W // 2, 160), (W // 2, 0, W, 160), (0, H - 120, 160, H), (W - 160, H - 120, W, H)]:
            c = m.crop(box)
            bb = c.getbbox()
            if bb:
                pieces.append((c.crop(bb), (box[0] + bb[0], box[1] + bb[1])))
        _cache["orn"] = pieces
    return _cache["orn"]


def ornaments(img, t):
    for m, xy in _orn_layer():
        img.paste((150, 158, 172), xy, m)
    d = ImageDraw.Draw(img)
    # tiny ticking timecode, top right
    s = int(t)
    fr = int((t - s) * FPS)
    tc = f"00:{s:02d}:{fr:02d}"
    f = R.font(22)
    R.spaced(d, W - 210, 92, tc, f, (120, 128, 142), 3)
    if int(t * 2) % 2 == 0:  # blinking rec dot
        d.ellipse([W - 330, 96, W - 316, 110], fill=(200, 60, 52))
    return img


# ---------------- demo ----------------
if __name__ == "__main__":
    import os
    import time

    os.makedirs("out", exist_ok=True)
    reel = {"template": "stairs", "labels": ["1%", "1%", "1%", "1%", "37X"],
            "caption": "Nobody skips the stairs", "dur": 11}
    fn, bgf = R.TEMPLATES[reel["template"]]
    key, builder = bgf(reel)
    base = R.bg(key, builder)

    def scene(t):
        img = base.copy()
        d = ImageDraw.Draw(img)
        R.dust(d, t)
        fn(img, d, t, reel["dur"], reel)
        return img

    hook_txt = "Nobody skips *the stairs*"

    def full(t, cta_k=None):
        img = scene(t)
        img = light_rays(img, t)
        img = camera(img, t, 11, shakes=[(0.18, 1.0)])
        img = hook(img, t, hook_txt)
        if cta_k is not None:
            img = cta(img, cta_k, title="Nobody skips the stairs")
        img = ornaments(img, t)
        return grade(img, t)

    full(0.25).save("out/fx_hook.png")
    full(0.08).save("out/fx_hook_early.png")
    full(5.5).save("out/fx_mid.png")
    full(10.9, cta_k=0.95).save("out/fx_cta.png")
    full(10.5, cta_k=0.4).save("out/fx_cta_mid.png")

    img0 = scene(3.0)
    tests = {
        "camera": lambda t: camera(img0, t, 11, [(t - 0.1, 1.0)]),
        "grade": lambda t: grade(img0, t),
        "light_rays": lambda t: light_rays(img0, t),
        "flash": lambda t: flash(img0, 0.5),
        "hook": lambda t: hook(img0.copy(), 0.1 + (t % 1.0), hook_txt),
        "cta": lambda t: cta(img0.copy(), (t % 1.0)),
        "ornaments": lambda t: ornaments(img0.copy(), t),
        "copy(baseline)": lambda t: img0.copy(),
    }
    for name, f in tests.items():
        f(0.0)  # warm caches
        n = 30
        t0 = time.perf_counter()
        for i in range(n):
            f(i / FPS)
        print(f"{name:16s} {1000 * (time.perf_counter() - t0) / n:6.1f} ms/frame")
