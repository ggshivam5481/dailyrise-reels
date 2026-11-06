"""'lifeline' format in the cosy night-room style (ghstyle): two kids grow up in the same room.

AGE steps up every beat; the blue-head one keeps working at the desk while the other drifts
(ball -> games -> phone -> sleep). Props pile up on the worker's side. At the end the worker walks out
through a glowing door and the other is left in the dark room.
"""
import math

from PIL import Image, ImageDraw

import nv
import ghstyle as G

BT = 3.4      # seconds per age beat
EXIT = 3.6    # closing scene

AGES = [[6, 9, 13, 18, 25], [8, 12, 16, 20, 26], [10, 14, 17, 21, 28]]

# main: study / read / code / save / train ; vices per beat: ball / game / phone / sleep / snack
SCRIPTS = [
    dict(topic="habits", main="study", vices=["ball", "ball", "game", "phone", "phone"], bubbles={1: "LATER."},
         top="The gap starts small.", punch="It never stays small.", prize="FIRST JOB",
         cap="The gap between two people starts with one small evening.",
         ig="Aaj ka chhota farak, kal ka bada farak."),
    dict(topic="growth", main="read", vices=["game", "phone", "phone", "phone", "sleep"], bubbles={2: "JUST 5 MIN."},
         top="15 pages a night.", punch="That's 20 books a year.", prize="NEW MIND",
         cap="Fifteen pages a night quietly becomes a different mind.",
         ig="Roz 15 page. Saal mein naya dimaag."),
    dict(topic="money", main="save", vices=["snack", "game", "phone", "snack", "phone"], bubbles={3: "YOLO."},
         top="Save a little. Every month.", punch="Small savings. Big freedom.", prize="FREEDOM",
         cap="Small savings look boring until they buy your freedom.",
         ig="Thoda thoda bachao, aazaadi khareedo."),
    dict(topic="discipline", main="train", vices=["game", "snack", "game", "phone", "sleep"],
         bubbles={2: "TOMORROW."}, top="Same age. Same room.", punch="One built a body. One built excuses.",
         prize="STRONG BODY", cap="Same room, same age, different reps.",
         ig="Ek ne body banayi, ek ne bahane."),
    dict(topic="growth", main="code", vices=["ball", "game", "game", "phone", "phone"],
         bubbles={3: "ONE MORE GAME."}, top="One hour of skill a day.", punch="Skills pay for life.",
         prize="DREAM JOB", cap="One hour of skill a day pays you for the rest of your life.",
         ig="Roz ek ghanta skill. Zindagi bhar ki kamaai."),
    dict(topic="time", main="study", vices=["ball", "game", "phone", "sleep", "sleep"],
         bubbles={1: "LATER.", 3: "TOMORROW."}, top="Later is a habit too.", punch="Later became never.",
         prize="GOALS", cap="Later feels harmless. Do it enough and it becomes never.",
         ig="Baad mein... kabhi nahi ban jaata hai."),
    dict(topic="focus", main="read", vices=["ball", "game", "game", "game", "phone"], bubbles={2: "LAST ROUND."},
         top="Hobby or future?", punch="Play less. Build more.", prize="CAREER",
         cap="Fun is fine. Building is what pays later.", ig="Khelna kam, banana zyada."),
    dict(topic="money", main="code", vices=["game", "phone", "phone", "phone", "phone"], bubbles={3: "BORING."},
         top="They scrolled. He shipped.", punch="The side hustle paid off.", prize="OWN BUSINESS",
         cap="Scrolling costs you. Building pays you.", ig="Scroll karne wale dekhte reh gaye."),
    dict(topic="discipline", main="train", vices=["ball", "game", "sleep", "sleep", "snack"],
         bubbles={2: "SKIP TODAY."}, top="He skipped one day.", punch="Then he skipped a year.",
         prize="FITNESS", cap="One skipped day is small. A skipped habit is huge.",
         ig="Ek din chhoda, phir saal chhoot gaya."),
    dict(topic="discipline", main="study", vices=["ball", "phone", "phone", "game", "sleep"], bubbles={},
         top="Nobody saw the nights.", punch="Everyone saw the result.", prize="TOPPER",
         cap="Quiet nights of work become loud results.", ig="Raaton ki mehnat kisi ne nahi dekhi."),
    dict(topic="money", main="save", vices=["ball", "snack", "snack", "phone", "game"], bubbles={2: "BUY IT."},
         top="Rs 100 a week.", punch="It adds up quietly.", prize="FIRST INVESTMENT",
         cap="Rs 100 a week does not look like much. Give it years.", ig="Hafte ke 100, saalon mein lakhs."),
    dict(topic="mindset", main="read", vices=["snack", "game", "phone", "phone", "snack"], bubbles={3: "WHY READ?"},
         top="Feed your mind first.", punch="What you feed, grows.", prize="CLARITY",
         cap="Your mind becomes whatever you feed it every night.", ig="Dimaag ko jo khilaoge, wahi badhega."),
    dict(topic="mindset", main="study", vices=["ball", "ball", "game", "phone", "sleep"], bubbles={2: "CHILL."},
         top="Same childhood. Different choices.", punch="Choices become lives.", prize="COLLEGE",
         cap="Same start. Different daily choices. Different lives.", ig="Choice roz ki, zindagi bhar ki."),
    dict(topic="time", main="code", vices=["game", "sleep", "sleep", "phone", "sleep"], bubbles={1: "5 MORE MIN."},
         top="Dreams need work hours.", punch="He woke up to his dream.", prize="STARTUP",
         cap="Dreams don't need more sleep. They need work hours.", ig="Sapne neend mein nahi, kaam mein poore hote hain."),
    dict(topic="habits", main="train", vices=["ball", "phone", "phone", "snack", "phone"], bubbles={3: "MONDAY."},
         top="Your body keeps score.", punch="Habits show by 25.", prize="HEALTH",
         cap="Your habits at 15 show up in your body at 25.", ig="Aaj ki aadat, kal ki body."),
    dict(topic="focus", main="study", vices=["ball", "ball", "game", "game", "phone"], bubbles={1: "LET'S PLAY!"},
         top="Fun now or freedom later?", punch="He chose freedom later.", prize="FREEDOM",
         cap="Choosing focus now buys you freedom later.", ig="Abhi focus, baad mein aazaadi."),
    dict(topic="fear", main="read", vices=["game", "phone", "phone", "sleep", "phone"], bubbles={2: "TOO HARD."},
         top="Scared to start?", punch="Starting small still counts.", prize="CONFIDENCE",
         cap="You don't need courage to start big. Start small.", ig="Chhota shuru karo, par shuru karo."),
    dict(topic="money", main="save", vices=["snack", "snack", "phone", "game", "snack"], bubbles={3: "EMI IT."},
         top="Every small spend is a choice.", punch="Choices compound.", prize="NO DEBT",
         cap="Every small spend is a vote for your future.", ig="Har chhota kharcha ek faisla hai."),
    dict(topic="growth", main="code", vices=["ball", "game", "game", "game", "game"], bubbles={2: "GG."},
         top="Playing vs building.", punch="Builders get paid.", prize="OFFER LETTER",
         cap="Players spend hours. Builders invest them.", ig="Khelne wale ghante kharch karte hain, banane wale invest."),
    dict(topic="discipline", main="study", vices=["sleep", "sleep", "phone", "sleep", "sleep"],
         bubbles={1: "ZZZ."}, top="Wake up early. Once. Then again.", punch="Mornings made him.",
         prize="GOALS", cap="One early morning is easy. A thousand of them build a life.",
         ig="Subah jaldi uthna, roz."),
    dict(topic="discipline", main="train", vices=["snack", "snack", "game", "snack", "phone"],
         bubbles={2: "CHEAT DAY."}, top="Comfort food. Comfort life.", punch="Discipline pays later.",
         prize="FITNESS", cap="Comfort today is borrowed from tomorrow.", ig="Aaj ka aaram, kal ka udhaar."),
    dict(topic="time", main="read", vices=["ball", "game", "phone", "phone", "sleep"], bubbles={3: "NO TIME."},
         top="Minutes turn into years.", punch="So use the minutes.", prize="WISDOM",
         cap="Your years are made of the minutes you waste or use.", ig="Minute hi saal banate hain."),
    dict(topic="focus", main="study", vices=["game", "phone", "phone", "phone", "phone"],
         bubbles={2: "1 MORE REEL."}, top="Your phone or your future?", punch="The phone never studied for him.",
         prize="RANK 1", cap="Your phone won't write your exam. You will.", ig="Phone tumhara exam nahi dega."),
]


def make_lifeline(rnd, used):
    order = list(range(len(SCRIPTS)))
    rnd.shuffle(order)
    combos = [(i, a) for i in order for a in rnd.sample(range(len(AGES)), len(AGES))]
    fresh = [(i, a) for i, a in combos if f"g1|lifeline|{i}|{a}" not in used]
    if not fresh:  # every script/age combo used: allow a repeat rather than stop the batch
        fresh = combos
    for i, a in fresh[:1]:
        key = f"g1|lifeline|{i}|{a}"
        if True:
            used.add(key)
            s = SCRIPTS[i]
            ages = AGES[a]
            n = len(ages)
            dur = n * BT + EXIT
            text = "|".join([s["top"], s["punch"], s["main"], ",".join(s["vices"]),
                             ",".join(f"{k}:{v}" for k, v in sorted(s["bubbles"].items())), s["prize"],
                             ",".join(map(str, ages))])
            return dict(format="lifeline", key=key, script_text=text, dur=dur, top=None, punch=None,
                        g_top=s["top"], g_punch=s["punch"], punch_at=(n * BT + 1.0) / dur,
                        caption_line=s["cap"], ig=s["ig"], topic=s["topic"], main=s["main"], vices=s["vices"],
                        bubbles=s["bubbles"], prize=s["prize"], ages=ages, gh=True)
    raise RuntimeError("lifeline scripts exhausted")


def _vice(img, d, kind, x, t, s, k_dark):
    """Draw the drifting character doing his thing."""
    if kind == "ball":
        info = G.figure(img, d, x, G.kick(t), s, head="grey", facing=-1)
        bx = x - 120 * s + 30 * math.sin(t * 5)
        by = G.FOOT - 22 * s - abs(math.sin(t * 5)) * 60 * s
        r = 22 * s
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=(245, 245, 250), outline=(20, 20, 30), width=2)
        d.ellipse([bx - r * 0.35, by - r * 0.35, bx + r * 0.35, by + r * 0.35], fill=(20, 20, 30))
    elif kind == "game":
        info = G.figure(img, d, x, G.game(t), s, head="grey", facing=-1)
        hx, hy = info["hands"]["l"]
        d.rounded_rectangle([hx - 34 * s, hy - 14 * s, hx + 34 * s, hy + 14 * s], 8, fill=(40, 44, 60))
        d.ellipse([hx - 24 * s, hy - 5 * s, hx - 14 * s, hy + 5 * s], fill=(240, 80, 90))
        d.ellipse([hx + 14 * s, hy - 5 * s, hx + 24 * s, hy + 5 * s], fill=(90, 200, 120))
        G.glow(img, info["head"][0], info["head"][1], 70 * s, 60 * s, (90, 140, 255), 0.25 + 0.1 * math.sin(t * 20))
    elif kind == "phone":
        info = G.figure(img, d, x, G.stand_phone(t), s, head="grey", facing=-1, eyes="down")
        hx, hy = info["hands"]["r"]
        d.rounded_rectangle([hx - 12 * s, hy - 24 * s, hx + 12 * s, hy + 24 * s], 5, fill=(150, 200, 255))
        G.glow(img, hx, hy - 10, 50 * s, 50 * s, (120, 170, 255), 0.35)
    elif kind == "sleep":
        d.rounded_rectangle([x - 190 * s, G.FOOT - 34 * s, x - 90 * s, G.FOOT - 4], 12, fill=(200, 210, 230))
        info = G.figure(img, d, x, G.lie_floor(t), s, head="grey", facing=-1, eyes="closed")
        hx, hy = info["head"]
        for i in range(3):
            ph = (t * 0.6 + i / 3) % 1
            G.spaced(d, hx + 40 + ph * 60, hy - 60 - ph * 120, "Z", int((26 + 10 * i) * s), G.TXT_DIM, 0)
    else:  # snack
        info = G.figure(img, d, x, G.stand_phone(t), s, head="grey", facing=-1)
        hx, hy = info["hands"]["r"]
        d.polygon([(hx - 20 * s, hy - 26 * s), (hx + 20 * s, hy - 26 * s), (hx + 16 * s, hy + 26 * s),
                   (hx - 16 * s, hy + 26 * s)], fill=(240, 90, 60))
        d.rectangle([hx - 12 * s, hy - 6 * s, hx + 12 * s, hy + 6 * s], fill=(250, 210, 70))
    return info


def draw_lifeline(c, t, spec):
    img = c.img
    img.paste(G.room_base(), (0, 0))
    d = ImageDraw.Draw(img)
    ages, main = spec["ages"], spec["main"]
    n = len(ages)
    story = n * BT
    b = min(int(t / BT), n - 1)
    tb = t - b * BT
    exiting = t >= story
    te = t - story
    age = ages[b]
    s = nv.lerp(0.74, 1.12, nv.clamp((age - 5) / 16))

    # wall clock spins during each time skip
    G.clock(d, 530, 560, 46, b + nv.ease(nv.clamp(tb / 0.6)) + t * 0.02)
    G.desk_props(img, d, t, notes=2 + b, books=(1 + 2 * b) if main in ("study", "read", "code") else b,
                 chart=1 + b, trophies=max(0, b - 2), coins=(2 * b + 2) if main == "save" else 0)
    k_open = nv.ease(nv.clamp((te - 0.6) / 0.8)) if exiting else 0.0
    G.door(img, d, 0.0)
    G.rug(img, d)

    # the drifting one
    vice = spec["vices"][min(b, len(spec["vices"]) - 1)]
    other = _vice(img, d, vice, 700, t, s, 0)
    if not exiting and b in spec["bubbles"] and 0.7 < tb < 3.0:
        hx, hy = other["head"]
        G.bubble(d, spec["bubbles"][b], hx - 20, hy - other["r"] - 8)

    # the worker
    walk_x = None
    if exiting and te > 1.0:
        walk_x = nv.lerp(420, 900, nv.ease(nv.clamp((te - 1.0) / 1.9)))
    if not exiting:
        if main == "train":
            info = G.figure(img, d, 420, G.curls(t), s, head="blue", facing=1)
            for hk in ("l", "r"):
                hx, hy = info["hands"][hk]
                d.rectangle([hx - 22 * s, hy - 6 * s, hx + 22 * s, hy + 6 * s], fill=(120, 130, 150))
                d.rectangle([hx - 26 * s, hy - 14 * s, hx - 18 * s, hy + 14 * s], fill=(60, 66, 84))
                d.rectangle([hx + 18 * s, hy - 14 * s, hx + 26 * s, hy + 14 * s], fill=(60, 66, 84))
        else:
            pose = G.sit_read(t) if main == "read" else G.sit_work(t)
            # sitting: hip height = shin length; draw the chair first
            hip_y = G.FOOT - G.SH * s
            G.chair(d, (420, hip_y), s, facing=-1)
            info = G.figure(img, d, 420, pose, s, head="blue", facing=-1)
            if main == "read":
                hx = (info["hands"]["l"][0] + info["hands"]["r"][0]) / 2
                hy = min(info["hands"]["l"][1], info["hands"]["r"][1])
                for sx in (-1, 1):
                    d.polygon([(hx, hy), (hx + sx * 50 * s, hy - 14 * s), (hx + sx * 50 * s, hy + 50 * s),
                               (hx, hy + 60 * s)], fill=(240, 236, 220), outline=(40, 44, 70))
            if main == "save" and 0.6 < tb < 1.4:
                cy = 900 + (tb - 0.6) * 90
                d.ellipse([240, cy, 266, cy + 26], fill=(250, 200, 70), outline=(180, 130, 40))

    # closing: lights fade on the room, the door opens, the worker walks into the light
    if exiting:
        k = nv.ease(nv.clamp(te / 1.2))
        dark = Image.new("RGB", img.size, (2, 3, 8))
        img.paste(Image.blend(img, dark, 0.55 * k))
        d = ImageDraw.Draw(img)
        G.door(img, d, k_open)
        if k_open > 0.3:
            G.spaced(d, 885, 560, spec["prize"], 34, nv.mix(G.FLOOR_C, G.BLUE_L, k_open), 3)
        if walk_x is not None and walk_x < 885:
            G.figure(img, d, walk_x, nv.walk(t, 7, 22), s, head="blue", facing=1)
        elif walk_x is None:  # stands up from the desk, still lit, before walking to the door
            G.figure(img, d, 420, nv.stand(t), s, head="blue", facing=1)

    # brief bright flash on every time skip
    if b > 0 and tb < 0.22:
        img.paste(Image.blend(img, Image.new("RGB", img.size, (200, 215, 255)), 0.18 * (1 - tb / 0.22)))
        d = ImageDraw.Draw(img)

    # text: statement line, AGE counter, punch
    if t >= 2.15:
        G.block(d, spec["g_top"], nv.W / 2, 210, 44, G.TXT, sp=2)
    G.age_counter(d, age, tb if b > 0 else 9, y=310)
    pt = spec["punch_at"] * spec["dur"]
    if t >= pt:
        kp = nv.clamp((t - pt) / 0.25)
        size = int(50 + 18 * (1 - nv.ease(kp)))
        G.block(d, spec["g_punch"], nv.W / 2, 400, size, G.BLUE_L, sp=2)
    c.d = ImageDraw.Draw(img)


def events_lifeline(spec):
    n = len(spec["ages"])
    story = n * BT
    ev = []
    for b in range(1, n):
        t0 = b * BT
        ev += [(t0, "whoosh", 0.4), (t0 + 0.05, "pop", 0.35), (t0 + 0.7, "pop", 0.3)]
        if b in spec["bubbles"]:
            ev += [(t0 + 0.75, "pop", 0.45)]
    if 0 in spec["bubbles"]:
        ev += [(0.75, "pop", 0.45)]
    for b, v in enumerate(spec["vices"]):
        if v == "ball":
            ev += [(b * BT + 0.3 + i * 1.26, "step", 0.22) for i in range(2)]
    if spec["main"] == "save":
        ev += [(b * BT + 1.3, "pop", 0.3) for b in range(n)]
    ev += [(story + 0.1, "heartbeat", 0.35), (story + 0.6, "swell", 0.45), (story + 1.3, "flash", 0.45),
           (story + 1.4, "chime", 0.5)]
    ev += [(story + 1.2 + i * 0.4, "step", 0.25) for i in range(4)]
    pt = spec["punch_at"] * spec["dur"]
    ev += [(pt, "impact", 0.45), (pt, "pop", 0.4)]
    return ev


FORMATS = {"lifeline": {"make": make_lifeline, "draw": draw_lifeline, "events": events_lifeline}}


if __name__ == "__main__":
    import random
    rnd, used = random.Random(1), set()
    spec = make_lifeline(rnd, used)
    nv.set_theme("midnight")
    frames = []
    for t in (0.5, 2.5, 4.0, 7.5, 11.0, 15.0, spec["dur"] - 2.5, spec["dur"] - 0.6):
        c = nv.Canvas()
        draw_lifeline(c, t, spec)
        frames.append(c.finish(t).resize((270, 480)))
    sheet = Image.new("RGB", (270 * 4, 480 * 2))
    for i, f in enumerate(frames):
        sheet.paste(f, ((i % 4) * 270, (i // 4) * 480))
    sheet.save("out/fg_lifeline.png")
    print(spec["key"], spec["g_top"])
