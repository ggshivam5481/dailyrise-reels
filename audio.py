"""Cinematic background score + synced sound effects, synthesized with numpy only.

No samples, no downloads, nothing copyrighted: every sound is generated from sines and noise.

    build_audio(path, dur, seed, events)

writes a 48 kHz stereo 16-bit WAV. `events` is a list of (time_sec, kind) or (time_sec, kind, gain).
Kinds: whoosh impact snap step riser chime rumble flash heartbeat thud pop swell (unknown kinds are ignored).
"riser" and "swell" END at their event time; every other kind STARTS at its event time.
"""
import os
import wave

import numpy as np

SR = 48000

# ---------------------------------------------------------------- helpers


def _t(n):
    return np.arange(n) / SR


def _mtof(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def _filt(x, lo=None, hi=None):
    """Smooth band filter in the frequency domain (x: 1-D)."""
    n = len(x)
    if n < 4:
        return x
    f = np.fft.rfftfreq(n, 1 / SR)
    g = np.ones_like(f)
    if hi:
        g /= 1 + (f / hi) ** 4
    if lo:
        g /= 1 + (lo / np.maximum(f, 1e-3)) ** 4
    return np.fft.irfft(np.fft.rfft(x) * g, n)


def _pan(mono, p):
    a = (p + 1) * np.pi / 4
    return np.stack([mono * np.cos(a), mono * np.sin(a)], 1)


def _st(mono):
    return np.stack([mono, mono], 1)


def _norm(x, peak=1.0):
    m = np.abs(x).max()
    return x * (peak / m) if m > 0 else x


def _add(buf, start, sig):
    s = int(round(start * SR))
    a = max(0, -s)
    s = max(s, 0)
    m = min(len(sig) - a, len(buf) - s)
    if m > 0:
        buf[s:s + m] += sig[a:a + m]


def _sweep_sine(f_curve):
    return np.sin(2 * np.pi * np.cumsum(f_curve) / SR)


def _fade_edges(x, a=0.002, b=0.01):
    na, nb = min(len(x), int(a * SR)), min(len(x), int(b * SR))
    if na:
        x[:na] *= np.linspace(0, 1, na)[:, None] if x.ndim == 2 else np.linspace(0, 1, na)
    if nb:
        x[-nb:] *= np.linspace(1, 0, nb)[:, None] if x.ndim == 2 else np.linspace(1, 0, nb)
    return x


# ---------------------------------------------------------------- sound effects
# each returns a stereo array with peak ~1; LEVEL sets its place in the mix.


def sfx_whoosh(rng):
    n = int(0.6 * SR)
    t = _t(n)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    for i, fc in enumerate([250, 500, 1000, 2000, 4000, 7000]):
        band = _filt(noise, lo=fc * 0.7, hi=fc * 1.4)
        peak = 0.12 + i * 0.055
        out += band / (np.abs(band).max() + 1e-9) * np.exp(-((t - peak) / 0.09) ** 2) * (1 - 0.08 * i)
    env = np.sin(np.pi * np.clip(t / 0.6, 0, 1)) ** 1.5
    pan = np.linspace(-0.7, 0.7, n)
    a = (pan + 1) * np.pi / 4
    mono = out * env
    return _fade_edges(np.stack([mono * np.cos(a), mono * np.sin(a)], 1))


def sfx_impact(rng):
    n = int(1.5 * SR)
    t = _t(n)
    sub = _sweep_sine(34 + 50 * np.exp(-t / 0.22)) * np.exp(-t / 0.55)
    body = _sweep_sine(85 + 90 * np.exp(-t / 0.04)) * np.exp(-t / 0.16)
    hit = _filt(rng.standard_normal(n), hi=3500) * np.exp(-t / 0.025)
    thump = _filt(rng.standard_normal(n), lo=40, hi=500) * np.exp(-t / 0.22)
    mono = sub * 1.0 + body * 0.7 + _norm(hit) * 0.55 + _norm(thump) * 0.35
    mono = np.tanh(mono * 1.4)
    side = _filt(rng.standard_normal(n), lo=200, hi=2500) * np.exp(-t / 0.3)
    side = _norm(side) * 0.08
    return _fade_edges(np.stack([mono + side, mono - side], 1), 0.0005, 0.05)


def sfx_snap(rng):
    n = int(0.45 * SR)
    t = _t(n)
    crack = _filt(rng.standard_normal(n), lo=1800) * np.exp(-t / 0.010)
    whip = _filt(rng.standard_normal(n), lo=2000, hi=8000) * np.exp(-t / 0.05)
    twang = _sweep_sine(260 + 220 * np.exp(-t / 0.05)) * np.exp(-t / 0.09)
    click = np.zeros(n)
    click[:24] = np.hanning(48)[24:]
    mono = _norm(crack) + _norm(whip) * 0.35 + twang * 0.3 + click * 0.6
    return _fade_edges(_pan(mono, 0.1), 0.0002, 0.02)


def sfx_step(rng):
    n = int(0.14 * SR)
    t = _t(n)
    scuff = _filt(rng.standard_normal(n), lo=60, hi=600) * np.exp(-t / 0.022)
    body = _sweep_sine(70 + 30 * np.exp(-t / 0.02)) * np.exp(-t / 0.035)
    return _fade_edges(_st(_norm(scuff) * 0.7 + body), 0.0005, 0.01)


def sfx_riser(rng):
    d = 1.5
    n = int(d * SR)
    t = _t(n)
    u = t / d
    tone = _sweep_sine(170 * (1100 / 170) ** u) + 0.5 * _sweep_sine(255 * (1650 / 255) ** u)
    tone *= u ** 2.4
    nl = _filt(rng.standard_normal(n), lo=900, hi=7000)
    nr = _filt(rng.standard_normal(n), lo=900, hi=7000)
    env = u ** 3
    out = np.stack([tone * 0.5 + _norm(nl) * env * 0.6, tone * 0.5 + _norm(nr) * env * 0.6], 1)
    return _fade_edges(out, 0.01, 0.012)


def sfx_chime(rng):
    n = int(2.2 * SR)
    t = _t(n)

    def bell(f0, delay):
        s = np.zeros(n)
        k = int(delay * SR)
        tt = t[: n - k]
        for r, a, tau in ((1, 1.0, 1.5), (2.0, 0.35, 0.9), (2.76, 0.45, 0.6), (5.4, 0.18, 0.3), (8.93, 0.06, 0.15)):
            s[k:] += a * np.sin(2 * np.pi * f0 * r * tt) * np.exp(-tt / tau)
        s[k:k + 96] *= np.linspace(0, 1, 96)
        return s

    mono_a = bell(1046.5, 0.0)
    mono_b = bell(1568.0, 0.13) * 0.7
    out = _pan(mono_a, -0.25) + _pan(mono_b, 0.3)
    return _fade_edges(out, 0.0005, 0.05)


def sfx_rumble(rng):
    n = int(1.7 * SR)
    t = _t(n)
    low = _filt(rng.standard_normal(n), lo=25, hi=150)
    wob = np.abs(_filt(rng.standard_normal(n), hi=7))
    wob = 0.5 + wob / (wob.max() + 1e-9)
    grit = _filt(rng.standard_normal(n), lo=300, hi=1200) * (rng.random(n) < 0.004)
    env = np.minimum(1, t / 0.18) * np.exp(-np.maximum(0, t - 0.5) / 0.5)
    mono = (_norm(low) * wob + _norm(_filt(grit, hi=2000)) * 0.25) * env
    side = _norm(_filt(rng.standard_normal(n), lo=40, hi=200)) * env * 0.15
    return _fade_edges(np.stack([mono + side, mono - side], 1), 0.005, 0.05)


def sfx_flash(rng):
    n = int(1.3 * SR)
    t = _t(n)
    env = np.minimum(1, t / 0.1) ** 2 * np.exp(-np.maximum(0, t - 0.1) / 0.45)
    out = np.zeros((n, 2))
    for _ in range(14):
        f = rng.uniform(1800, 7500)
        trem = 0.6 + 0.4 * np.sin(2 * np.pi * rng.uniform(7, 15) * t + rng.uniform(0, 6.28))
        out += _pan(np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) * trem / (1 + f / 3000),
                    rng.uniform(-0.8, 0.8))
    air = _filt(rng.standard_normal(n), lo=5000)
    out = _norm(out) + _st(_norm(air) * 0.25)
    swell = _sweep_sine(np.full(n, 523.25)) * 0.25 + _sweep_sine(np.full(n, 784.0)) * 0.18
    out += _st(swell)
    return _fade_edges(out * env[:, None], 0.001, 0.05)


def _thump(n, f_hi, f_lo, tau, rng):
    t = _t(n)
    s = _sweep_sine(f_lo + (f_hi - f_lo) * np.exp(-t / 0.03)) * np.exp(-t / tau)
    s += _norm(_filt(rng.standard_normal(n), hi=400)) * np.exp(-t / 0.015) * 0.3
    return s


def sfx_heartbeat(rng):
    n = int(0.65 * SR)
    a = _thump(int(0.3 * SR), 75, 42, 0.09, rng)
    b = _thump(int(0.3 * SR), 70, 40, 0.08, rng) * 0.75
    mono = np.zeros(n)
    mono[: len(a)] += a
    k = int(0.27 * SR)
    mono[k:k + len(b)] += b[: n - k]
    return _fade_edges(_st(mono), 0.0005, 0.02)


def sfx_thud(rng):
    n = int(0.7 * SR)
    t = _t(n)
    main = _sweep_sine(38 + 40 * np.exp(-t / 0.04)) * np.exp(-t / 0.15)
    crunch = _norm(_filt(rng.standard_normal(n), hi=800)) * np.exp(-t / 0.04) * 0.6
    rattle = _norm(_filt(rng.standard_normal(n), lo=900, hi=3200)) * np.exp(-t / 0.03) * 0.2
    mono = main + crunch + rattle
    k = int(0.13 * SR)
    mono[k:] += (main[: n - k] * 0.25 + crunch[: n - k] * 0.15)
    return _fade_edges(_st(np.tanh(mono * 1.3)), 0.0005, 0.03)


def sfx_pop(rng):
    n = int(0.09 * SR)
    t = _t(n)
    mono = _sweep_sine(650 + 650 * np.exp(-t / 0.012)) * np.exp(-t / 0.025)
    mono[:48] += np.hanning(96)[48:] * 0.4
    return _fade_edges(_pan(mono, rng.uniform(-0.2, 0.2)), 0.0003, 0.01)


def sfx_swell(rng):
    d = 1.0
    n = int(d * SR)
    t = _t(n)
    u = t / d
    l = _filt(rng.standard_normal(n), lo=2500, hi=14000)
    r = _filt(rng.standard_normal(n), lo=2500, hi=14000)
    tone = _filt(rng.standard_normal(n), lo=600, hi=2400)
    env = u ** 3.2
    out = np.stack([_norm(l) + _norm(tone) * 0.3, _norm(r) + _norm(tone) * 0.3], 1) * env[:, None]
    return _fade_edges(out, 0.01, 0.008)


SFX = {
    # kind: (generator, level, start offset relative to event time, reverb send, ducks music)
    "whoosh": (sfx_whoosh, 0.42, 0.0, 0.15, False),
    "impact": (sfx_impact, 0.80, 0.0, 0.30, True),
    "snap": (sfx_snap, 0.60, 0.0, 0.20, True),
    "step": (sfx_step, 0.16, 0.0, 0.05, False),
    "riser": (sfx_riser, 0.38, -1.5, 0.20, False),
    "chime": (sfx_chime, 0.34, 0.0, 0.35, False),
    "rumble": (sfx_rumble, 0.55, 0.0, 0.10, False),
    "flash": (sfx_flash, 0.36, 0.0, 0.35, False),
    "heartbeat": (sfx_heartbeat, 0.60, 0.0, 0.08, False),
    "thud": (sfx_thud, 0.60, 0.0, 0.15, True),
    "pop": (sfx_pop, 0.24, 0.0, 0.10, False),
    "swell": (sfx_swell, 0.32, -1.0, 0.25, False),
}

# ---------------------------------------------------------------- music

KEYS = [57, 55, 53, 52, 50, 54]  # tonic (minor) around octave 3: A G F E D F#
PROGS = [
    [(0, "m"), (8, "M"), (3, "M"), (10, "M")],   # i  VI  III VII
    [(0, "m"), (5, "m"), (8, "M"), (7, "M")],    # i  iv  VI  V
    [(8, "M"), (10, "M"), (0, "m"), (0, "m")],   # VI VII i   i
    [(0, "m"), (10, "M"), (8, "M"), (10, "M")],  # i  VII VI  VII
    [(0, "m"), (3, "M"), (10, "M"), (5, "m")],   # i  III VII iv
    [(8, "M"), (3, "M"), (10, "M"), (0, "m")],   # VI III VII i
]
BPMS = [70, 72, 74, 76, 78, 80]
TIMBRES = [(0.50, 2.4), (0.62, 3.0), (0.42, 2.0), (0.56, 3.4), (0.47, 2.7)]  # (brightness, decay s)
ARPS = [[0, 1, 2, 3, 4, 3, 2, 1], [0, 2, 3, 4, 5, 4, 3, 2], [0, 2, 1, 3, 2, 4, 3, 5],
        [0, 1, 2, 1, 3, 2, 4, 2], [0, 3, 2, 4, 3, 5, 4, 2]]


def _piano_note(freq, bright, decay):
    length = min(3.0, decay * 1.4)
    n = int(length * SR)
    t = _t(n).astype(np.float32)
    out = np.zeros(n, np.float32)
    for k in range(1, 8):
        fk = freq * k * np.sqrt(1 + 0.0004 * k * k)
        if fk > 15000:
            break
        tau = decay / (1 + 0.9 * (k - 1))
        m = min(n, int(4.6 * tau * SR))  # stop each partial once it is ~40 dB down
        tk = t[:m]
        out[:m] += (bright ** (k - 1) / k) * np.sin(np.float32(2 * np.pi * fk) * tk + np.float32(0.4 * k))             * np.exp(-tk / np.float32(tau))
    out *= 0.55 * np.exp(-t / np.float32(0.3)) + 0.45  # fast initial drop, slower sustain
    a = int(0.005 * SR)
    out[:a] *= np.linspace(0, 1, a, dtype=np.float32)
    r = int(0.08 * SR)
    out[-r:] *= np.linspace(1, 0, r, dtype=np.float32)
    return out.astype(np.float64)


_TABLE_N = 4096
_PAD_TABLE = (lambda ph: np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.18 * np.sin(3 * ph) + 0.08 * np.sin(4 * ph))(
    2 * np.pi * np.arange(_TABLE_N) / _TABLE_N).astype(np.float32)


def _pad_voice(f, m, phase0):
    idx = (np.arange(m, dtype=np.float64) * (f * _TABLE_N / SR) + phase0 * _TABLE_N).astype(np.int64)
    return _PAD_TABLE[idx & (_TABLE_N - 1)]


def _music(n, dur, seed):
    rng = np.random.default_rng(seed)
    key = KEYS[seed % len(KEYS)]
    prog = PROGS[(seed // len(KEYS) + seed) % len(PROGS)]
    bpm = BPMS[int(rng.integers(len(BPMS)))]
    bright, decay = TIMBRES[(seed + 2) % len(TIMBRES)]
    arp = ARPS[int(rng.integers(len(ARPS)))]
    beat = 60.0 / bpm
    bar = 4 * beat

    piano, pad, bass, kick = (np.zeros((n, 2)) for _ in range(4))
    cache = {}

    def note(m, at, vel):
        if at >= dur:
            return
        if m not in cache:
            cache[m] = _piano_note(_mtof(m), bright, decay)
        _add(piano, at, _pan(cache[m] * vel, float(np.clip((m - 69) / 28, -0.5, 0.5))))

    k_n = int(0.35 * SR)
    kt = _t(k_n)
    kick_sig = _st(_sweep_sine(45 + 75 * np.exp(-kt / 0.025)) * np.exp(-kt / 0.16))

    nbars = int(np.ceil(dur / bar)) + 1
    for b in range(nbars):
        t0 = b * bar
        if t0 >= dur:
            break
        off, q = prog[b % len(prog)]
        if off > 6:
            off -= 12
        third = 3 if q == "m" else 4
        tones = [0, third, 7, 12, 12 + third, 19]
        root = key + off

        # piano: block chord intro, then flowing arpeggio, melody on top from bar 3
        if b == 0:
            for i, tn in enumerate([0, third, 7, 12]):
                note(root + tn, t0 + 0.05 + i * 0.02, 0.42)
            for j in range(4, 8):
                note(root + tones[arp[j]], t0 + j * beat / 2, 0.20 + 0.04 * (j - 4))
        else:
            grow = min(1.0, 0.8 + 0.1 * b)
            for j in range(8):
                v = (0.50 if j % 4 == 0 else 0.36) * (1 + rng.uniform(-0.1, 0.1)) * grow
                note(root + tones[arp[j]], t0 + j * beat / 2 + rng.uniform(-0.006, 0.006), v)
        if b >= 2:
            for j in (0, 4):
                note(root + 24 + int(rng.choice([0, third, 7])), t0 + j * beat / 2 + 0.01, 0.30)

        # pad: open voicing, detuned voices split left/right
        plen = bar + 1.0
        m = int(plen * SR)
        t = _t(m)
        env = np.sin(np.pi / 2 * np.minimum(1, t / 0.9)) ** 2 * np.minimum(1, (plen - t) / 0.9)
        base = root - 12 if root - 12 >= 43 else root
        L = np.zeros(m, np.float32)
        R = np.zeros(m, np.float32)
        for mm in (base, base + 7, base + 12 + third):
            f = _mtof(mm)
            for cents, side in ((-8, L), (3, L), (-3, R), (8, R)):
                side += _pad_voice(f * 2 ** (cents / 1200), m, rng.uniform(0, 1))
        gain = 0.55 + 0.11 * min(b, 4)
        _add(pad, t0 - 0.3, np.stack([L, R], 1) * (env * gain)[:, None])

        # sub bass on the chord root, from bar 2
        if b >= 1:
            bm = root - 24
            if bm < 28:
                bm += 12
            ln = int((bar + 0.05) * SR)
            bt = _t(ln)
            benv = np.minimum(1, bt / 0.03) * np.exp(-bt / 3.0) * np.minimum(1, (bar + 0.05 - bt) / 0.12)
            ph = 2 * np.pi * _mtof(bm) * bt
            _add(bass, t0, _st(np.tanh((np.sin(ph) + 0.3 * np.sin(2 * ph)) * 1.2) * benv))

        # soft pulse on beats 1 and 3, from bar 3
        if b >= 2:
            for j in (0, 2):
                _add(kick, t0 + j * beat, kick_sig)

    pad = np.stack([_filt(pad[:, 0], lo=60, hi=1500), _filt(pad[:, 1], lo=60, hi=1500)], 1)

    def rms(x):
        return float(np.sqrt((x ** 2).mean())) or 1.0

    dry = (piano / rms(piano) + pad / rms(pad) * 0.6 + (bass / rms(bass) * 0.5 if bass.any() else 0)
           + (_norm(kick) * 1.6 if kick.any() else 0))
    return _norm(dry, 0.45)


# ---------------------------------------------------------------- reverb + mix


def _ir(seed, decay=2.3, length=2.6):
    rng = np.random.default_rng(seed + 7919)
    n = int(length * SR)
    t = _t(n)
    ir = rng.standard_normal((n, 2)) * np.exp(-t * 6.9 / decay)[:, None]
    ir = np.stack([_filt(ir[:, 0], lo=120, hi=5500), _filt(ir[:, 1], lo=120, hi=5500)], 1)
    ir[: int(0.004 * SR)] = 0
    pre = np.zeros((int(0.025 * SR), 2))
    ir = np.concatenate([pre, ir])
    return ir / np.sqrt((ir ** 2).sum(0))


def _convolve(x, ir):
    size = len(x) + len(ir) - 1
    nfft = 1 << (size - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, nfft, axis=0) * np.fft.rfft(ir, nfft, axis=0), nfft, axis=0)
    return y[: len(x)]


def _limit(x, th=0.7):
    a = np.abs(x)
    over = a > th
    y = x.copy()
    y[over] = np.sign(x[over]) * (th + (1 - th) * np.tanh((a[over] - th) / (1 - th)))
    return y


def build_audio(path, dur, seed, events):
    """Write a 48 kHz stereo 16-bit WAV of length `dur` seconds to `path`.
    events: list of (time_sec: float, kind: str[, gain: float]) — SFX to place at those times.
    seed: int, picks music variation (key/progression/tempo) deterministically."""
    n = int(round(dur * SR))
    seed = int(seed)
    music = _music(n, dur, seed)

    # fades on the music bed
    t = _t(n)
    fade = np.minimum(1, t / 0.6) * np.clip((dur - t) / 1.2, 0, 1)
    duck = np.ones(n)
    sfx_dry = np.zeros((n, 2))
    sfx_send = np.zeros((n, 2))
    for i, ev in enumerate(events or []):
        at, kind = float(ev[0]), str(ev[1])
        gain = float(ev[2]) if len(ev) > 2 else 1.0
        if kind not in SFX:
            continue
        gen, level, offset, send, ducks = SFX[kind]
        sig = gen(np.random.default_rng(seed * 1009 + i * 31 + 17)) * (level * gain)
        _add(sfx_dry, at + offset, sig)
        _add(sfx_send, at + offset, sig * send)
        if ducks:
            depth = 1 - 10 ** (-4 / 20)
            s = int(at * SR)
            if s < n:
                tt = _t(n - max(s, 0))
                g = 1 - depth * np.exp(-tt / 0.45)
                duck[max(s, 0):] = np.minimum(duck[max(s, 0):], g)
                a0 = max(0, s - int(0.01 * SR))
                if a0 < max(s, 0):
                    duck[a0:s] = np.minimum(duck[a0:s], np.linspace(1, 1 - depth, s - a0))

    music *= (fade * duck)[:, None]
    wet = _convolve(music + sfx_send, _ir(seed))
    mix = music * 0.85 + wet * 0.42 + sfx_dry
    mix = np.nan_to_num(mix)
    tail = min(n, int(0.04 * SR))
    if tail:
        mix[-tail:] *= np.linspace(1, 0, tail)[:, None]
    mix = _norm(_limit(mix), 10 ** (-1 / 20))

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


if __name__ == "__main__":
    import time

    demo = [(0.3, "whoosh"), (0.5, "pop"), (1.0, "step"), (1.45, "step"), (1.9, "step"), (2.4, "heartbeat"),
            (3.4, "riser"), (3.4, "impact"), (4.2, "rumble"), (5.6, "thud"), (6.5, "swell"), (6.5, "snap"),
            (7.4, "whoosh"), (8.6, "flash"), (10.0, "impact", 0.8), (11.2, "pop"), (12.6, "chime")]
    for sd in (0, 1, 2, 3, 4):
        t0 = time.perf_counter()
        out = build_audio(f"out/audio_demo{'' if sd == 0 else sd}.wav", 15.0, sd, demo)
        el = time.perf_counter() - t0
        with wave.open(out) as w:
            data = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float) / 32767
            frames = w.getnframes()
        print(f"seed {sd}: {el:.2f}s build, {frames / SR:.2f}s audio, peak {np.abs(data).max():.3f}, "
              f"rms {np.sqrt((data ** 2).mean()):.3f}, nan {np.isnan(data).any()}, "
              f"full-scale samples {(np.abs(data) >= 0.999).sum()}")
