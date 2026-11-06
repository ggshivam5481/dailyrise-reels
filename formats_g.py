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

AGES = [[6, 9, 13, 18, 25], [8, 12, 16, 20, 26], [10, 14, 17, 21, 28], [7, 10, 14, 19, 24],
        [9, 12, 15, 19, 23], [11, 14, 17, 20, 27]]

# main: study / read / code / save / train / guitar / journal / run / speak ; vices: ball / game / phone / sleep / snack
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
         top="Your body keeps score.", punch="Habits show up later.", prize="HEALTH",
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
    # ---- round 2 ----
    dict(topic="growth", main="guitar", vices=["ball", "game", "game", "phone", "phone"], bubbles={2: "BORING."},
         top="Ten minutes of practice a day.", punch="Ten years later, he plays stages.", prize="FIRST STAGE",
         cap="Ten minutes a day of practice is a skill in ten years.", ig="Roz 10 minute riyaaz, saalon mein kala."),
    dict(topic="habits", main="guitar", vices=["game", "game", "phone", "phone", "sleep"], bubbles={3: "LATER."},
         top="Same guitar. Two owners.", punch="One played. One posted about it.", prize="OWN SONG",
         cap="Owning the tool is easy. Practising with it is the habit.", ig="Guitar dono ke paas thi, riyaaz ek ne kiya."),
    dict(topic="discipline", main="run", vices=["snack", "snack", "game", "snack", "phone"], bubbles={2: "TOO TIRED."},
         top="One ran. One snacked.", punch="Bodies remember every choice.", prize="MARATHON",
         cap="Your body remembers every run and every skipped one.", ig="Body har choice yaad rakhti hai."),
    dict(topic="habits", main="run", vices=["sleep", "sleep", "phone", "sleep", "snack"], bubbles={1: "5 MORE MIN."},
         top="Morning runs feel useless.", punch="Until the years add up.", prize="HEALTH",
         cap="One morning run feels useless. A thousand of them change your life.",
         ig="Ek run bekaar lagta hai, hazaar zindagi badal dete hain."),
    dict(topic="money", main="save", vices=["phone", "snack", "phone", "snack", "phone"], bubbles={2: "ADD TO CART."},
         top="Saving vs shopping.", punch="One owns things. One owns time.", prize="TIME FREEDOM",
         cap="Shopping buys things. Saving buys time.", ig="Shopping cheezein deti hai, saving waqt."),
    dict(topic="money", main="save", vices=["game", "snack", "phone", "phone", "snack"], bubbles={3: "SALE!"},
         top="He skipped one treat a week.", punch="It became a safety net.", prize="SAFETY NET",
         cap="One skipped treat a week quietly becomes a safety net.", ig="Hafte ki ek treat chhodi, safety net bana."),
    dict(topic="focus", main="read", vices=["phone", "phone", "phone", "phone", "phone"], bubbles={2: "ONE MORE REEL."},
         top="Reels or reading?", punch="Reels entertain. Books upgrade.", prize="SHARP MIND",
         cap="Reels entertain you for a minute. Books upgrade you for life.", ig="Reels time pass, kitaabein upgrade."),
    dict(topic="focus", main="code", vices=["game", "game", "phone", "game", "phone"], bubbles={3: "NEXT EPISODE."},
         top="Coding vs binge-watching.", punch="He built what they watch.", prize="OWN APP",
         cap="Some people binge content. Some people build it.", ig="Kuch log dekhte hain, kuch banate hain."),
    dict(topic="time", main="study", vices=["phone", "phone", "game", "phone", "sleep"], bubbles={2: "2 AM SCROLL."},
         top="Early sleep. Early start.", punch="Mornings belonged to him.", prize="HEAD START",
         cap="Whoever owns the night scroll loses the morning.", ig="Raat ka scroll, subah ki haar."),
    dict(topic="fear", main="speak", vices=["phone", "game", "phone", "sleep", "phone"], bubbles={2: "TOO SCARY."},
         top="He was scared to speak.", punch="He practised anyway.", prize="THE STAGE",
         cap="Confidence is just fear that kept practising.", ig="Darr ke saath practice, wahi confidence hai."),
    dict(topic="fear", main="speak", vices=["ball", "phone", "phone", "phone", "game"], bubbles={3: "WHAT IF THEY LAUGH?"},
         top="Practise in an empty room.", punch="Then own a full one.", prize="FULL ROOM",
         cap="Practise where nobody watches so you shine where everyone does.",
         ig="Khaali kamre mein practice, bhare hall mein jeet."),
    dict(topic="mindset", main="journal", vices=["phone", "phone", "game", "phone", "sleep"], bubbles={2: "OVERTHINKING."},
         top="One wrote it down.", punch="One kept it in his head.", prize="CLEAR MIND",
         cap="Thoughts in your head spin. Thoughts on paper turn into plans.",
         ig="Dimaag mein ghoomta hai, kaagaz pe plan banta hai."),
    dict(topic="mindset", main="journal", vices=["game", "phone", "sleep", "phone", "phone"], bubbles={3: "WHATEVER."},
         top="Five lines every night.", punch="He knew himself better.", prize="SELF-AWARE",
         cap="Five honest lines a night teach you more than a year of noise.", ig="Roz 5 line, khud se mulaqaat."),
    dict(topic="growth", main="code", vices=["ball", "game", "phone", "phone", "game"], bubbles={1: "NERD."},
         top="They called him a nerd.", punch="Now they call him boss.", prize="OWN COMPANY",
         cap="The names change when the results show up.", ig="Pehle nerd bola, ab boss bolte hain."),
    dict(topic="discipline", main="train", vices=["phone", "phone", "game", "phone", "snack"], bubbles={1: "GYM IS BORING."},
         top="Two kids. One habit apart.", punch="Years make it visible.", prize="STRONG BODY",
         cap="One habit apart today. Worlds apart in ten years.", ig="Aaj ek aadat ka farak, kal duniya ka."),
    dict(topic="habits", main="read", vices=["ball", "ball", "phone", "game", "phone"], bubbles={2: "BOOKS ARE OLD."},
         top="One book a month.", punch="Hundreds of minds borrowed.", prize="WISDOM",
         cap="Every book lends you a lifetime of someone else's lessons.", ig="Har kitaab ek zindagi ka sabak."),
    dict(topic="time", main="study", vices=["game", "game", "game", "phone", "sleep"], bubbles={3: "I HAVE TIME."},
         top="I have time, he said.", punch="Time had other plans.", prize="ON TRACK",
         cap="'I have time' is the most expensive sentence.", ig="'Abhi time hai' sabse mehnga jumla hai."),
    dict(topic="growth", main="guitar", vices=["phone", "phone", "game", "phone", "phone"], bubbles={1: "TOO HARD."},
         top="Every expert sounded bad first.", punch="He kept going. Then he got good.", prize="ALBUM",
         cap="Every expert sounded terrible at the start. They just did not stop.",
         ig="Har expert pehle bura tha, bas ruka nahi."),
    dict(topic="discipline", main="run", vices=["phone", "game", "sleep", "snack", "sleep"], bubbles={2: "IT'S COLD."},
         top="Rain or not, he ran.", punch="Excuses never got fitter.", prize="FINISH LINE",
         cap="Weather is an excuse. Habits do not check the forecast.", ig="Mausam bahana hai, aadat nahi."),
    dict(topic="money", main="code", vices=["snack", "phone", "game", "phone", "phone"], bubbles={3: "GET RICH QUICK."},
         top="Skills or shortcuts?", punch="Skills kept paying.", prize="HIGH INCOME",
         cap="Shortcuts pay once. Skills pay every month.", ig="Shortcut ek baar, skill har mahine."),
    dict(topic="focus", main="study", vices=["phone", "game", "phone", "game", "phone"], bubbles={2: "MULTITASKING."},
         top="One thing at a time.", punch="Focus beat talent.", prize="TOP RANK",
         cap="One focused hour beats five distracted ones.", ig="Ek focused ghanta, paanch bhatke ghanton se behtar."),
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
    G.desk_props(img, d, t, notes=2 + b, books=(1 + 2 * b) if main in ("study", "read", "code", "journal") else b,
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
        if main == "run":
            info = G.figure(img, d, 440, nv.run(t), s, head="blue", facing=1)
            for i in range(3):
                yy = G.FOOT - 120 * s - i * 50 * s
                xx = 300 - (t * 500 + i * 60) % 120
                d.line([(xx, yy), (xx - 70 * s, yy)], fill=G.LINE_DIM, width=4)
        elif main == "speak":
            P = dict(nv.BASE, ra1=150, ra2=60, la1=-40, la2=-20, head=-6)
            info = G.figure(img, d, 440, P, s, head="blue", facing=1)
            hx, hy = info["hands"]["r"]
            G.mic(d, hx, hy - 8, s)
            if 0.5 < tb < 2.8:
                for i in range(3):
                    ph = (tb * 1.4 + i / 3) % 1
                    r = 20 + 50 * ph
                    d.arc([hx + 30 - r, hy - 30 - r, hx + 30 + r, hy - 30 + r], -40, 40,
                          fill=nv.mix(G.BLUE_L, G.WALL_BOT, ph), width=3)
        elif main == "train":
            info = G.figure(img, d, 420, G.curls(t), s, head="blue", facing=1)
            for hk in ("l", "r"):
                hx, hy = info["hands"][hk]
                d.rectangle([hx - 22 * s, hy - 6 * s, hx + 22 * s, hy + 6 * s], fill=(120, 130, 150))
                d.rectangle([hx - 26 * s, hy - 14 * s, hx - 18 * s, hy + 14 * s], fill=(60, 66, 84))
                d.rectangle([hx + 18 * s, hy - 14 * s, hx + 26 * s, hy + 14 * s], fill=(60, 66, 84))
        else:
            pose = G.sit_read(t) if main in ("read", "guitar") else G.sit_work(t)
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
            if main == "guitar":
                hx = (info["hands"]["l"][0] + info["hands"]["r"][0]) / 2
                hy = max(info["hands"]["l"][1], info["hands"]["r"][1])
                G.guitar(d, hx + 10 * s, hy, s * 0.9)
                for i in range(2):
                    ph = (t * 0.7 + i / 2) % 1
                    G.spaced(d, hx + 60 + ph * 80, hy - 80 - ph * 160, "~", int(34 * s), G.BLUE_L, 0)
            if main == "journal":
                G.notebook(d, 250, 994, 1.0)
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


# =====================================================================================
# "tworooms": the same room twice (top / bottom), a red clock between them, one night.
# =====================================================================================
TR_BT = 4.2                                   # seconds per time beat
TR_TIMES = [["9:30 PM", "11:59 PM", "2:10 AM", "6:00 AM"], ["10:00 PM", "12:30 AM", "3:00 AM", "6:30 AM"],
            ["8:45 PM", "11:15 PM", "1:40 AM", "5:50 AM"]]
PANEL_CROP = (0, 520, nv.W, 1220)             # window of the full room shown in each panel
PANEL_Y = (240, 1010)                         # top-left y of the two panels
CLOCK_Y = 944

# good / bad actions per beat; the last beat is the morning
TR_SCRIPTS = [
    dict(topic="focus", labels=("SCROLLER", "BUILDER"), bad=["phone", "phone", "bed_phone", "alarm"],
         good=["code", "code", "sleep", "door"], bubbles={("bad", 1): "ONE MORE REEL.", ("bad", 3): "5 MORE MIN."},
         top="Same night. Two choices.", punch="Mornings belong to builders.", prize="READY",
         cap="Two people, one night, two very different mornings.", ig="Raat ek, subah do alag."),
    dict(topic="money", labels=("BROKE HABITS", "RICH HABITS"), bad=["phone", "snack", "bed_phone", "alarm"],
         good=["save", "read", "sleep", "door"], bubbles={("bad", 0): "ADD TO CART.", ("good", 1): "BUDGET DONE."},
         top="Your night shows your wallet.", punch="Habits decide your bank balance.", prize="ON BUDGET",
         cap="What you do at 10 PM shows up in your bank account.", ig="Raat ki aadat, bank ka balance."),
    dict(topic="mindset", labels=("OVERTHINKER", "DOER"), bad=["bed_think", "bed_think", "bed_phone", "alarm"],
         good=["journal", "study", "sleep", "door"], bubbles={("bad", 0): "WHAT IF IT FAILS?", ("good", 0): "STEP 1."},
         top="Same idea. Same night.", punch="One thought. One did.", prize="STARTED",
         cap="Overthinking feels like work. Only doing is work.", ig="Sochna kaam jaisa lagta hai, karna hi kaam hai."),
    dict(topic="discipline", labels=("SNOOZER", "EARLY RISER"), bad=["game", "phone", "bed_phone", "alarm"],
         good=["read", "sleep", "sleep", "door"], bubbles={("bad", 3): "SNOOZE.", ("good", 1): "LIGHTS OFF."},
         top="The morning starts the night before.", punch="Sleep early. Win early.", prize="6 AM CLUB",
         cap="Your morning is decided by what you do the night before.", ig="Subah ki jeet raat se shuru hoti hai."),
    dict(topic="habits", labels=("GAMER", "LEARNER"), bad=["game", "game", "game", "alarm"],
         good=["study", "read", "sleep", "door"], bubbles={("bad", 1): "ONE MORE MATCH.", ("good", 0): "CHAPTER 3."},
         top="Two screens. Two futures.", punch="What you repeat, you become.", prize="EXAM READY",
         cap="Two screens, two habits, two very different futures.", ig="Screen ek jaisi, future alag."),
    dict(topic="time", labels=("LATER", "NOW"), bad=["phone", "game", "bed_phone", "alarm"],
         good=["study", "code", "sleep", "door"], bubbles={("bad", 0): "I'LL DO IT LATER.", ("good", 0): "DOING IT NOW."},
         top="Later or now?", punch="Later never shows up.", prize="DONE",
         cap="Later never comes. Now is the only time you own.", ig="Baad mein kabhi nahi aata."),
    dict(topic="growth", labels=("CONSUMER", "CREATOR"), bad=["phone", "phone", "phone", "alarm"],
         good=["code", "journal", "sleep", "door"], bubbles={("bad", 1): "SO INSPIRING.", ("good", 1): "POSTED."},
         top="Watching vs making.", punch="Creators get paid for your scroll.", prize="LAUNCHED",
         cap="One person watched content all night. The other one made it.", ig="Ek ne dekha, ek ne banaya."),
    dict(topic="discipline", labels=("SKIPPER", "SHOWS UP"), bad=["snack", "phone", "bed_phone", "alarm"],
         good=["train", "read", "sleep", "door"], bubbles={("bad", 0): "SKIP TODAY.", ("good", 0): "REP 50."},
         top="Tired is not a reason.", punch="Show up tired. Still counts.", prize="STRONGER",
         cap="Showing up tired still counts. Skipping never does.", ig="Thak ke bhi aao, ginti hoti hai."),
    dict(topic="focus", labels=("MULTITASKER", "FOCUSED"), bad=["phone", "game", "phone", "alarm"],
         good=["study", "study", "sleep", "door"], bubbles={("bad", 0): "10 TABS OPEN.", ("good", 0): "ONE TASK."},
         top="Busy vs productive.", punch="One task done beats ten started.", prize="FINISHED",
         cap="Busy feels productive. Finished is productive.", ig="Busy hona aur kaam karna alag hai."),
    dict(topic="fear", labels=("WAITER", "STARTER"), bad=["bed_think", "phone", "bed_phone", "alarm"],
         good=["code", "journal", "sleep", "door"], bubbles={("bad", 0): "NOT READY YET.", ("good", 0): "SHIP IT."},
         top="Waiting to feel ready?", punch="Ready comes after starting.", prize="IT'S LIVE",
         cap="Nobody feels ready. Starters start anyway.", ig="Ready koi nahi hota, shuru karo."),
    dict(topic="money", labels=("SPENDER", "INVESTOR"), bad=["snack", "phone", "game", "alarm"],
         good=["save", "study", "sleep", "door"], bubbles={("bad", 1): "TREAT YOURSELF.", ("good", 1): "SIP DONE."},
         top="Same salary. Different nights.", punch="Small savings. Big future.", prize="WEALTH",
         cap="Same salary, different nightly choices, different futures.", ig="Salary same, aadat alag, future alag."),
    dict(topic="habits", labels=("NIGHT SCROLL", "NIGHT ROUTINE"), bad=["phone", "bed_phone", "bed_phone", "alarm"],
         good=["read", "journal", "sleep", "door"], bubbles={("bad", 2): "IT'S 2 AM?", ("good", 1): "3 WINS TODAY."},
         top="Your last hour decides tomorrow.", punch="Fix your nights. Fix your life.", prize="FRESH START",
         cap="The last hour of your night decides the first hour of your morning.",
         ig="Raat ka aakhri ghanta, subah ka pehla ghanta."),
    dict(topic="growth", labels=("COMFORT", "GROWTH"), bad=["game", "snack", "bed_phone", "alarm"],
         good=["guitar", "read", "sleep", "door"], bubbles={("bad", 0): "TOO TIRED.", ("good", 0): "PRACTICE."},
         top="Comfort or growth?", punch="Growth feels hard. Comfort costs more.", prize="LEVEL UP",
         cap="Comfort feels free tonight. It sends the bill later.", ig="Aaram aaj free lagta hai, bill baad mein aata hai."),
    dict(topic="mindset", labels=("COMPLAINER", "PLANNER"), bad=["phone", "bed_think", "bed_phone", "alarm"],
         good=["journal", "study", "sleep", "door"], bubbles={("bad", 0): "LIFE IS UNFAIR.", ("good", 0): "PLAN B."},
         top="Complain or plan?", punch="Plans change lives. Complaints don't.", prize="ON PLAN",
         cap="Complaining feels good for a minute. Planning changes your year.", ig="Shikayat ek minute, plan saal bhar."),
    dict(topic="time", labels=("ALL-NIGHTER", "SLEEPER"), bad=["study", "study", "study", "alarm"],
         good=["study", "sleep", "sleep", "door"], bubbles={("bad", 2): "JUST ONE MORE HOUR.", ("good", 1): "ENOUGH TODAY."},
         top="Grinding all night?", punch="Rest is part of the work.", prize="SHARP",
         cap="All-nighters feel brave. Sleep is what makes you sharp.", ig="Neend bhi mehnat ka hissa hai."),
    dict(topic="focus", labels=("DISTRACTED", "DEEP WORK"), bad=["phone", "game", "phone", "alarm"],
         good=["code", "code", "sleep", "door"], bubbles={("bad", 1): "QUICK CHECK.", ("good", 0): "PHONE AWAY."},
         top="Phone away. Mind on.", punch="Deep work builds careers.", prize="PROMOTED",
         cap="Two hours of deep work beat a day of distracted effort.", ig="Do ghante focus, poore din se zyada."),
    dict(topic="discipline", labels=("MOOD", "SYSTEM"), bad=["bed_phone", "phone", "game", "alarm"],
         good=["train", "study", "sleep", "door"], bubbles={("bad", 0): "NOT FEELING IT.", ("good", 0): "IT'S 9:30. GO."},
         top="Mood or system?", punch="Systems don't need moods.", prize="CONSISTENT",
         cap="Moods change daily. Systems show up anyway.", ig="Mood roz badalta hai, system nahi."),
    dict(topic="fear", labels=("WHAT IF", "WHY NOT"), bad=["bed_think", "bed_think", "bed_phone", "alarm"],
         good=["speak", "journal", "sleep", "door"], bubbles={("bad", 1): "THEY'LL LAUGH.", ("good", 0): "PRACTICE TALK."},
         top="Scared of judgement?", punch="Nobody remembers. Do it.", prize="BRAVE",
         cap="People forget your mistakes fast. They remember your courage.", ig="Log bhool jaate hain, himmat yaad rehti hai."),
    dict(topic="habits", labels=("JUNK NIGHTS", "CLEAN NIGHTS"), bad=["snack", "snack", "bed_phone", "alarm"],
         good=["train", "read", "sleep", "door"], bubbles={("bad", 1): "MIDNIGHT SNACK.", ("good", 1): "WATER. BED."},
         top="Night habits show in the mirror.", punch="Your body keeps the receipts.", prize="ENERGY",
         cap="What you eat at midnight shows up in the mirror.", ig="Raat ka khaana, subah ka sheesha."),
    dict(topic="growth", labels=("SAME DAY", "DAY ONE"), bad=["phone", "game", "bed_phone", "alarm"],
         good=["read", "code", "sleep", "door"], bubbles={("bad", 3): "SAME AS YESTERDAY.", ("good", 0): "DAY 1."},
         top="Every night is a choice.", punch="Day one beats one day.", prize="DAY 2",
         cap="Day one or one day. You choose it every night.", ig="Day 1 ya one day, roz ka faisla."),
    dict(topic="money", labels=("SHOW OFF", "SAVER"), bad=["phone", "snack", "phone", "alarm"],
         good=["save", "save", "sleep", "door"], bubbles={("bad", 0): "NEW SHOES?", ("good", 1): "+500 SAVED."},
         top="Looking rich vs being rich.", punch="Quiet money grows.", prize="SAVINGS",
         cap="Looking rich costs money. Being rich saves it.", ig="Dikhawa kharcha hai, bachat daulat."),
    dict(topic="mindset", labels=("EXCUSES", "RESULTS"), bad=["game", "bed_think", "bed_phone", "alarm"],
         good=["study", "train", "sleep", "door"], bubbles={("bad", 1): "NO TIME.", ("good", 1): "MADE TIME."},
         top="Excuses or results?", punch="You can't have both.", prize="RESULTS",
         cap="Excuses and results never live in the same room.", ig="Bahane aur result ek saath nahi rehte."),
    dict(topic="time", labels=("TOMORROW", "TONIGHT"), bad=["phone", "phone", "game", "alarm"],
         good=["journal", "study", "sleep", "door"], bubbles={("bad", 0): "TOMORROW, FOR SURE.", ("good", 0): "TONIGHT."},
         top="Tomorrow is a trap.", punch="Tonight is all you have.", prize="AHEAD",
         cap="Tomorrow is where plans go to wait forever.", ig="Kal ek jaal hai."),
    dict(topic="focus", labels=("NOTIFICATIONS ON", "NOTIFICATIONS OFF"), bad=["phone", "phone", "bed_phone", "alarm"],
         good=["read", "study", "sleep", "door"], bubbles={("bad", 1): "PING!", ("good", 0): "DO NOT DISTURB."},
         top="Who controls your night?", punch="Silence the phone. Hear your goals.", prize="CALM",
         cap="Your notifications are someone else's priorities.", ig="Notification doosron ki priority hai."),
    dict(topic="discipline", labels=("WISHER", "WORKER"), bad=["bed_think", "phone", "bed_phone", "alarm"],
         good=["code", "train", "sleep", "door"], bubbles={("bad", 0): "ONE DAY...", ("good", 0): "DAY 47."},
         top="Wishing vs working.", punch="Wishes don't pay bills.", prize="PAID",
         cap="Wishing is free. That is why it gives nothing back.", ig="Sapne free hain, isliye kuch nahi dete."),
]


def make_tworooms(rnd, used):
    combos = [(i, ti, o) for i in range(len(TR_SCRIPTS)) for ti in range(len(TR_TIMES)) for o in (0, 1)]
    rnd.shuffle(combos)
    fresh = [c for c in combos if f"g2|tworooms|{c[0]}|{c[1]}|{c[2]}" not in used] or combos
    i, ti, o = fresh[0]
    key = f"g2|tworooms|{i}|{ti}|{o}"
    used.add(key)
    s = TR_SCRIPTS[i]
    times = TR_TIMES[ti]
    n = len(times)
    dur = n * TR_BT + 1.4
    order = ("bad", "good") if o == 0 else ("good", "bad")       # which story is in the top panel
    labels = {"bad": s["labels"][0], "good": s["labels"][1]}
    text = "|".join([s["top"], s["punch"], labels[order[0]], labels[order[1]], ",".join(s["bad"]),
                     ",".join(s["good"]), ",".join(f"{k[0]}{k[1]}:{v}" for k, v in sorted(s["bubbles"].items())),
                     s["prize"], ",".join(times)])
    return dict(format="tworooms", key=key, script_text=text, dur=dur, top=None, punch=None,
                g_top=s["top"], g_punch=s["punch"], punch_at=((n - 1) * TR_BT + 1.6) / dur,
                caption_line=s["cap"], ig=s["ig"], topic=s["topic"], times=times, order=order, labels=labels,
                acts={"bad": s["bad"], "good": s["good"]}, bubbles=s["bubbles"], prize=s["prize"], gh=True)


def _actor(img, d, kind, t, tb, s, head, prize):
    """One person's action in a room panel (full-size room coordinates). Returns head pos or None."""
    eyes = "open"
    if kind in ("study", "code", "journal", "read", "save", "guitar"):
        hip_y = G.FOOT - G.SH * s
        G.chair(d, (420, hip_y), s, facing=-1)
        pose = G.sit_read(t) if kind in ("read", "guitar") else G.sit_work(t)
        info = G.figure(img, d, 420, pose, s, head=head, facing=-1)
        hx = (info["hands"]["l"][0] + info["hands"]["r"][0]) / 2
        hy = min(info["hands"]["l"][1], info["hands"]["r"][1])
        if kind == "read":
            for sx in (-1, 1):
                d.polygon([(hx, hy), (hx + sx * 50 * s, hy - 14 * s), (hx + sx * 50 * s, hy + 50 * s),
                           (hx, hy + 60 * s)], fill=(240, 236, 220), outline=(40, 44, 70))
        if kind == "guitar":
            G.guitar(d, hx + 10 * s, max(info["hands"]["l"][1], info["hands"]["r"][1]), s * 0.9)
        if kind == "journal":
            G.notebook(d, 250, 994, 1.0)
        if kind == "save" and 0.6 < tb < 1.4:
            cy = 900 + (tb - 0.6) * 90
            d.ellipse([240, cy, 266, cy + 26], fill=(250, 200, 70), outline=(180, 130, 40))
        return info
    if kind == "train":
        info = G.figure(img, d, 520, G.curls(t), s, head=head, facing=1)
        for hk in ("l", "r"):
            hx, hy = info["hands"][hk]
            d.rectangle([hx - 22 * s, hy - 6 * s, hx + 22 * s, hy + 6 * s], fill=(120, 130, 150))
        return info
    if kind == "speak":
        info = G.figure(img, d, 520, dict(nv.BASE, ra1=150, ra2=60, la1=-40, la2=-20, head=-6), s, head=head)
        hx, hy = info["hands"]["r"]
        G.mic(d, hx, hy - 8, s)
        return info
    if kind in ("sleep", "alarm", "bed_phone", "bed_think"):
        top = G.bed(img, d)
        eyes = "closed" if kind in ("sleep", "alarm") else ("down" if kind == "bed_phone" else "open")
        info = G.figure(img, d, 600, G.lie_floor(t), s * 0.85, foot_y=top, head=head, facing=-1, eyes=eyes)
        hx, hy = info["head"]
        if kind == "bed_phone":
            d.rounded_rectangle([hx + 40, hy - 50, hx + 64, hy - 6], 5, fill=(150, 200, 255))
            G.glow(img, hx + 52, hy - 28, 60, 60, (120, 170, 255), 0.4)
        if kind == "sleep" or kind == "alarm":
            for i in range(3):
                ph = (t * 0.6 + i / 3) % 1
                G.spaced(d, hx + 50 + ph * 60, hy - 50 - ph * 110, "Z", int((24 + 10 * i) * s), G.TXT_DIM, 0)
        if kind == "bed_think":
            for i in range(3):
                G.spaced(d, hx - 30 + i * 34, hy - 90 - 10 * math.sin(t * 4 + i), "?", 36, G.BLUE_L, 0)
        if kind == "alarm":  # ringing clock on the floor
            jx = 6 * math.sin(t * 60)
            d.ellipse([820 + jx, G.FOOT - 60, 880 + jx, G.FOOT], fill=(238, 52, 64), outline=(255, 220, 220), width=3)
            for sx in (-1, 1):
                d.line([(850 + jx + sx * 40, G.FOOT - 70), (850 + jx + sx * 55, G.FOOT - 90)], fill=(255, 120, 120),
                       width=4)
        return info
    if kind == "door":  # morning: walks into the open, glowing door
        x = nv.lerp(500, 880, nv.ease(nv.clamp((tb - 0.6) / 2.6)))
        if x < 880:
            return G.figure(img, d, x, nv.walk(t, 7, 22), s, head=head, facing=1)
        return None
    return _vice(img, d, kind, 650, t, s, 0) if head == "grey" else G.figure(img, d, 650, G.stand_phone(t), s, head=head)


def _panel(spec, who, t, b, tb, dark):
    room = G.room_base().copy()
    d = ImageDraw.Draw(room)
    acts = spec["acts"][who]
    kind = acts[min(b, len(acts) - 1)]
    morning = b == len(spec["times"]) - 1
    G.clock(d, 530, 560, 46, b + nv.ease(nv.clamp(tb / 0.6)))
    G.desk_props(room, d, t, lamp=not morning, notes=3, books=2 + b if who == "good" else 1,
                 chart=1 + (b if who == "good" else 0))
    k_open = nv.ease(nv.clamp((tb - 0.3) / 0.8)) if (morning and kind == "door") else 0.0
    G.door(room, d, k_open)
    if k_open > 0.4:
        G.spaced(d, 885, 660, spec["prize"], 30, nv.mix(G.FLOOR_C, G.BLUE_L, k_open), 3)
    G.rug(room, d)
    head = "blue" if who == "good" else "grey"
    info = _actor(room, d, kind, t, tb, 0.92, head, spec["prize"])
    bub = spec["bubbles"].get((who, b))
    if bub and info is not None and 0.6 < tb < 3.6:
        hx, hy = info["head"]
        G.bubble(d, bub, hx + 10, hy - info["r"] - 6, size=28)
    if dark > 0:
        room = Image.blend(room, Image.new("RGB", room.size, (2, 3, 10)), dark)
    return room.crop(PANEL_CROP)


def draw_tworooms(c, t, spec):
    G.no_reflection(c)
    img = c.img
    G.navy_fill(img)
    times = spec["times"]
    n = len(times)
    b = min(int(t / TR_BT), n - 1)
    tb = t - b * TR_BT
    for pi, who in enumerate(spec["order"]):
        night_dark = 0.0 if b == n - 1 else 0.18
        if b == n - 1 and spec["acts"][who][-1] == "alarm":
            night_dark = 0.35   # the late one wakes into a dull room
        panel = _panel(spec, who, t, b, tb, night_dark)
        y0 = PANEL_Y[pi]
        img.paste(panel, (0, y0))
        d = ImageDraw.Draw(img)
        d.rectangle([0, y0, nv.W - 1, y0 + panel.height - 1], outline=G.LINE_DIM, width=3)
        G.left_label(d, spec["labels"][who], 36, y0 + 22, 30, G.BLUE_L if who == "good" else G.TXT)
    d = ImageDraw.Draw(img)
    # red clock between the panels; pops on every change
    k = nv.clamp(tb / 0.3)
    size = int(54 + 16 * (1 - nv.ease(k)))
    G.spaced(d, nv.W / 2, CLOCK_Y - (size - 54) / 2, times[b], size, G.RED, 2)
    if b > 0 and tb < 0.2:
        img.paste(Image.blend(img, Image.new("RGB", img.size, (200, 215, 255)), 0.15 * (1 - tb / 0.2)))
        d = ImageDraw.Draw(img)
    if t >= 2.15:
        G.block(d, spec["g_top"], nv.W / 2, 150, 40, G.TXT, sp=2)
    pt = spec["punch_at"] * spec["dur"]
    if t >= pt:
        kp = nv.clamp((t - pt) / 0.25)
        G.block(d, spec["g_punch"], nv.W / 2, 1745, int(44 + 16 * (1 - nv.ease(kp))), G.BLUE_L, sp=2)
    c.d = ImageDraw.Draw(img)


def events_tworooms(spec):
    n = len(spec["times"])
    ev = []
    for b in range(1, n):
        t0 = b * TR_BT
        ev += [(t0, "whoosh", 0.4), (t0 + 0.05, "pop", 0.4)]
    for (who, b), _ in spec["bubbles"].items():
        ev += [(b * TR_BT + 0.65, "pop", 0.45)]
    last = (n - 1) * TR_BT
    if "alarm" in (spec["acts"]["bad"][-1], spec["acts"]["good"][-1]):
        ev += [(last + 0.1 + i * 0.5, "snap", 0.25) for i in range(4)]
    ev += [(last + 0.4, "swell", 0.45), (last + 1.1, "flash", 0.4), (last + 1.2, "chime", 0.5)]
    ev += [(last + 0.8 + i * 0.4, "step", 0.25) for i in range(5)]
    pt = spec["punch_at"] * spec["dur"]
    ev += [(pt, "impact", 0.45)]
    return ev


# =====================================================================================
# "table": a long dinner table; as AGE climbs the seats change and show a life truth.
# =====================================================================================
TB_BT = 3.2
TB_AGES = [[18, 21, 24, 27, 30], [16, 20, 24, 28, 32], [20, 23, 26, 29, 35]]
FAR_Y, NEAR_Y, FAR_HW, NEAR_HW, TCX = 660, 1520, 110, 330, nv.W / 2
SEATS = 5   # per side

# variant: leave (people drift away), plates (they leave once the food is gone),
#          refill (empties, then fills again once he starts building), family (two seats never empty)
TB_SCRIPTS = [
    dict(variant="leave", topic="mindset", top="At 18 every seat is taken.", punch="Real ones don't need reminders.",
         bubbles={4: "STILL HERE."}, cap="Your circle gets smaller as you grow. That's not a loss.",
         ig="Circle chhota hota hai, sachcha hota hai."),
    dict(variant="leave", topic="growth", top="Crowds come with free time.", punch="Few stay for the hard years.",
         bubbles={2: "BUSY, BRO."}, cap="Plenty of people sit with you when life is easy.",
         ig="Aasan waqt mein sab saath, mushkil mein kuch."),
    dict(variant="leave", topic="mindset", top="Count who stays, not who came.", punch="Two seats. Full heart.",
         bubbles={3: "SEE YOU AROUND."}, cap="Count the people who stay, not the ones who showed up.",
         ig="Kaun aaya nahi, kaun ruka ginna."),
    dict(variant="leave", topic="fear", top="Afraid of being left alone?", punch="The right ones never left.",
         bubbles={2: "I'M OUT."}, cap="Losing people who leave makes room for people who stay.",
         ig="Jaane wale jagah khaali karte hain sahi logon ke liye."),
    dict(variant="leave", topic="time", top="Time is the best filter.", punch="It keeps the real ones.",
         bubbles={1: "LATER, MAN."}, cap="Time quietly filters your friendships for you.",
         ig="Waqt khud dosti filter kar deta hai."),
    dict(variant="plates", topic="money", top="Some came for the food.", punch="Notice who stays when it's gone.",
         bubbles={3: "ANY MORE FOOD?"}, cap="When the treats stop, you see who came for you.",
         ig="Treat band, asli dost samne."),
    dict(variant="plates", topic="money", top="Paying for everyone?", punch="Empty plates show true friends.",
         bubbles={2: "YOUR TREAT, RIGHT?"}, cap="If they only show up when you pay, they are customers, not friends.",
         ig="Sirf treat pe aaye toh dost nahi."),
    dict(variant="plates", topic="mindset", top="Full plates. Full table.", punch="Empty plates. Real table.",
         bubbles={4: "I'M NOT HERE FOR FOOD."}, cap="A full plate fills a table. Loyalty keeps it full.",
         ig="Khaana table bharta hai, wafaadari rokti hai."),
    dict(variant="plates", topic="growth", top="When you have, they come.", punch="When you don't, you learn.",
         bubbles={3: "CALL YOU LATER."}, cap="Hard times are the best teachers about people.",
         ig="Bura waqt logon ko pehchanna sikhata hai."),
    dict(variant="refill", topic="growth", top="Everyone left when he started.", punch="Build. The right people come.",
         bubbles={1: "YOU'VE CHANGED."}, cap="When you start building, some leave. Better people arrive.",
         ig="Badloge toh kuch jaayenge, behtar aayenge."),
    dict(variant="refill", topic="discipline", top="He chose the grind over parties.",
         punch="The table filled with builders.", bubbles={1: "BORING NOW."},
         cap="Choose growth and your table slowly fills with growers.", ig="Mehnat chuno, mehnati log aayenge."),
    dict(variant="refill", topic="habits", top="New habits. Empty table.", punch="Then a better table.",
         bubbles={2: "WE MISS THE OLD YOU."}, cap="New habits empty old tables and build better ones.",
         ig="Nayi aadat, nayi company."),
    dict(variant="refill", topic="focus", top="Lonely while building?", punch="That's the price of the next level.",
         bubbles={1: "COME OUT TONIGHT?"}, cap="The quiet building years feel lonely. They don't stay lonely.",
         ig="Banane ke saal akele lagte hain, hamesha nahi."),
    dict(variant="refill", topic="money", top="He stopped spending on show.",
         punch="People who stayed were worth it.", bubbles={2: "CHEAPSKATE."},
         cap="Stop spending to impress and you meet people who value you.", ig="Dikhawa band, asli log shuru."),
    dict(variant="family", topic="mindset", top="Friends come and go.", punch="Two seats never emptied.",
         bubbles={4: "EAT SOMETHING, BETA."}, cap="Some seats at your table never go empty. Call them today.",
         ig="Kuch kursiyan kabhi khaali nahi hoti. Aaj call karo."),
    dict(variant="family", topic="time", top="You'll be busy at 25.", punch="They'll still save your seat.",
         bubbles={3: "COME HOME SOON."}, cap="You will get busy. Some people will always wait for you.",
         ig="Tum busy ho jaoge, woh intezaar karenge."),
    dict(variant="family", topic="growth", top="Chasing new friends?", punch="Don't forget the first table.",
         bubbles={4: "PROUD OF YOU."}, cap="While you chase new circles, do not forget your first table.",
         ig="Naye circle ke chakkar mein pehli table mat bhoolo."),
    dict(variant="family", topic="habits", top="Missed dinners add up.", punch="Show up for the ones who stayed.",
         bubbles={3: "YOU MISSED DINNER."}, cap="Missed dinners add up like missed workouts.",
         ig="Chhoote dinner bhi jud jaate hain."),
    dict(variant="leave", topic="discipline", top="Grow and some will leave.", punch="Grow anyway.",
         bubbles={2: "YOU NEVER CHILL."}, cap="Growth makes some people uncomfortable. Grow anyway.",
         ig="Badhoge toh kuch log naraaz honge, phir bhi badho."),
    dict(variant="plates", topic="fear", top="Afraid to say no?", punch="Those who leave over a no weren't yours.",
         bubbles={2: "LEND ME AGAIN?"}, cap="If one no ends the friendship, it was never one.",
         ig="Ek 'na' pe jaaye toh dost nahi tha."),
    dict(variant="refill", topic="time", top="Ten quiet years.", punch="A table full of winners.",
         bubbles={1: "YOU'RE NO FUN."}, cap="Ten quiet years of work can fill your table with the right people.",
         ig="Das saal ki chup mehnat, sahi log."),
    dict(variant="leave", topic="focus", top="Protect your time.", punch="Your table, your rules.",
         bubbles={3: "WHY SO SERIOUS?"}, cap="You do not owe every seat at your table to everyone.",
         ig="Har kursi har kisi ke liye nahi."),
]


def _table_plan(variant, rnd_seed):
    """Per-seat (side, idx) leave beat (None = stays) and arrive beat (0 = present from the start)."""
    import random as _r
    rr = _r.Random(rnd_seed)
    seats = [(sd, i) for sd in (-1, 1) for i in range(SEATS)]
    leave, arrive, fam = {}, {}, set()
    if variant == "family":
        fam = {(-1, 0), (1, 0)}
    stay = list(fam) if fam else rr.sample(seats, 2)
    others = [s_ for s_ in seats if s_ not in stay]
    rr.shuffle(others)
    for j, s_ in enumerate(others):
        arrive[s_] = 0
        if variant == "refill":
            leave[s_] = 1 + j % 2          # everyone gone by beat 2
        else:
            leave[s_] = 1 + j * 3 // len(others)   # spread over beats 1..3
    for s_ in stay:
        arrive[s_] = 0
        leave[s_] = None
    if variant == "refill":
        for s_ in stay:
            leave[s_] = 2
        for j, s_ in enumerate(seats):     # new people arrive in beats 3 and 4
            arrive[("new",) + s_] = 3 + (j % 2)
    return leave, arrive, fam


def make_table(rnd, used):
    combos = [(i, a) for i in range(len(TB_SCRIPTS)) for a in range(len(TB_AGES))]
    rnd.shuffle(combos)
    fresh = [c for c in combos if f"g2|table|{c[0]}|{c[1]}" not in used] or combos
    i, a = fresh[0]
    key = f"g2|table|{i}|{a}"
    used.add(key)
    s = TB_SCRIPTS[i]
    ages = TB_AGES[a]
    n = len(ages)
    dur = n * TB_BT + 1.6
    text = "|".join([s["top"], s["punch"], s["variant"],
                     ",".join(f"{k}:{v}" for k, v in sorted(s["bubbles"].items())), ",".join(map(str, ages))])
    return dict(format="table", key=key, script_text=text, dur=dur, top=None, punch=None, g_top=s["top"],
                g_punch=s["punch"], punch_at=((n - 1) * TB_BT + 0.8) / dur, caption_line=s["cap"], ig=s["ig"],
                topic=s["topic"], ages=ages, variant=s["variant"], bubbles=s["bubbles"], seed=i * 7 + a, gh=True)


def _depth(k):
    y = nv.lerp(FAR_Y, NEAR_Y, k)
    hw = nv.lerp(FAR_HW, NEAR_HW, k)
    sc = nv.lerp(0.36, 0.74, k)
    return y, hw, sc


def draw_table(c, t, spec):
    G.no_reflection(c)
    img = c.img
    G.navy_fill(img)
    d = ImageDraw.Draw(img)
    # back wall, floor and a soft ceiling light
    d.rectangle([0, 0, nv.W, 600], fill=(10, 16, 36))
    d.line([(0, 600), (nv.W, 600)], fill=G.LINE_DIM, width=3)
    for i in range(-6, 7):
        d.line([(nv.W / 2 + i * 50, 600), (nv.W / 2 + i * 300, nv.H)], fill=(18, 26, 56), width=2)
    G.glow(img, nv.W / 2, 700, 420, 300, (60, 90, 200), 0.3)
    ages, n = spec["ages"], len(spec["ages"])
    b = min(int(t / TB_BT), n - 1)
    tb = t - b * TB_BT
    leave, arrive, fam = _table_plan(spec["variant"], spec["seed"])

    # head of the table: the main character
    G.figure(img, d, TCX, nv.stand(t), 0.42, foot_y=FAR_Y - 6, head="blue")
    # wall clock
    G.clock(d, nv.W - 130, 470, 44, b + nv.ease(nv.clamp(tb / 0.6)))
    # table top
    d.polygon([(TCX - FAR_HW, FAR_Y), (TCX + FAR_HW, FAR_Y), (TCX + NEAR_HW, NEAR_Y), (TCX - NEAR_HW, NEAR_Y)],
              fill=(8, 12, 28), outline=G.LINE, width=4)
    d.polygon([(TCX - FAR_HW * 0.3, FAR_Y), (TCX + FAR_HW * 0.3, FAR_Y), (TCX + NEAR_HW * 0.3, NEAR_Y),
               (TCX - NEAR_HW * 0.3, NEAR_Y)], fill=(26, 60, 160))
    d.rectangle([TCX - NEAR_HW, NEAR_Y, TCX + NEAR_HW, NEAR_Y + 26], fill=(14, 20, 44), outline=G.LINE_DIM, width=2)
    for sx in (-1, 1):
        d.line([(TCX + sx * (NEAR_HW - 30), NEAR_Y + 26), (TCX + sx * (NEAR_HW - 30), NEAR_Y + 200)],
               fill=G.LINE_DIM, width=8)
    # candles
    for k in (0.3, 0.65):
        y, hw, sc = _depth(k)
        d.rectangle([TCX - 5 * sc * 2, y - 46 * sc * 2, TCX + 5 * sc * 2, y], fill=(235, 235, 245))
        fl = 1 + 0.15 * math.sin(t * 13 + k * 9)
        G.glow(img, TCX, y - 52 * sc * 2, 40 * sc * 2, 50 * sc * 2, (255, 200, 120), 0.5)
        d.ellipse([TCX - 6 * sc * 2, y - (62 * fl) * sc * 2, TCX + 6 * sc * 2, y - 44 * sc * 2], fill=(255, 220, 140))

    # seats far -> near so nearer people overlap farther ones
    def seat_pos(sd, i):
        k = (i + 0.6) / (SEATS + 0.2)
        y, hw, sc = _depth(k)
        return TCX + sd * (hw + 100 * sc * 1.6), y, sc, k

    order = sorted([(sd, i) for sd in (-1, 1) for i in range(SEATS)], key=lambda s_: s_[1])
    for sd, i in order:
        x, y, sc, k = seat_pos(sd, i)
        # plate on the table edge
        px = TCX + sd * (nv.lerp(FAR_HW, NEAR_HW, k) - 50 * sc * 1.6)
        d.ellipse([px - 40 * sc, y - 12 * sc, px + 40 * sc, y + 12 * sc], fill=(225, 230, 242), outline=G.LINE_DIM)
        food = 1.0
        if spec["variant"] == "plates":
            food = max(0.0, 1 - (b + tb / TB_BT) / 2.4)
        # chair back (always visible, empty chairs show the loss)
        cx = x + sd * 40 * sc
        d.rounded_rectangle([cx - 20 * sc, y - 190 * sc, cx + 20 * sc, y + 10], 8, fill=(20, 30, 66),
                            outline=G.LINE_DIM, width=2)
        for who in ((sd, i), ("new", sd, i)):
            if who not in arrive:
                continue
            a_b, l_b = arrive[who], leave.get(who)
            if b < a_b:
                continue
            gone = l_b is not None and (b > l_b or (b == l_b and tb > 1.5))
            if gone:
                continue
            leaving = l_b is not None and b == l_b and tb > 0.4
            arriving = who[0] == "new" and b == a_b and tb < 1.2
            head = "grey"
            if who in fam or (who[0] == "new") or (l_b is None and spec["variant"] != "refill"):
                head = "blue" if who[0] == "new" else "grey"
            if leaving:
                kk = nv.clamp((tb - 0.4) / 1.1)
                G.figure(img, d, x + sd * 260 * sc * kk * 2, nv.walk(t, 7, 22), sc * 1.6, foot_y=y + 40 * sc,
                         head=head, facing=sd)
            elif arriving:
                kk = 1 - nv.clamp(tb / 1.2)
                G.figure(img, d, x + sd * 260 * sc * kk * 2, nv.walk(t, 7, 22), sc * 1.6, foot_y=y + 40 * sc,
                         head=head, facing=-sd)
            else:
                info = G.figure(img, d, x, G.sit_work(t * 0.3), sc * 1.6, foot_y=y + 40 * sc, head=head, facing=-sd)
                if who in fam:
                    G.glow(img, info["head"][0], info["head"][1], 50 * sc * 2, 50 * sc * 2, (255, 200, 120), 0.25)
        if food > 0.02 and spec["variant"] in ("plates", "leave", "family"):
            r = 26 * sc * food
            d.ellipse([px - r, y - 8 * sc * food - 6 * sc, px + r, y + 2 * sc], fill=(230, 140, 60))

    # bubble from a staying / leaving guest
    bub = spec["bubbles"].get(b)
    if bub and 0.5 < tb < 2.9:
        x, y, sc, k = seat_pos(1, 3)
        G.bubble(d, bub, x - 40, y - 230 * sc, size=28)
    if b > 0 and tb < 0.2:
        img.paste(Image.blend(img, Image.new("RGB", img.size, (200, 215, 255)), 0.15 * (1 - tb / 0.2)))
        d = ImageDraw.Draw(img)
    if t >= 2.15:
        G.block(d, spec["g_top"], nv.W / 2, 200, 42, G.TXT, sp=2)
    G.age_counter(d, ages[b], tb if b > 0 else 9, y=300)
    pt = spec["punch_at"] * spec["dur"]
    if t >= pt:
        kp = nv.clamp((t - pt) / 0.25)
        G.block(d, spec["g_punch"], nv.W / 2, 1640, int(46 + 16 * (1 - nv.ease(kp))), G.BLUE_L, sp=2)
    c.d = ImageDraw.Draw(img)


def events_table(spec):
    n = len(spec["ages"])
    ev = []
    for b in range(1, n):
        t0 = b * TB_BT
        ev += [(t0, "whoosh", 0.4), (t0 + 0.05, "pop", 0.4), (t0 + 0.6, "step", 0.3), (t0 + 1.0, "step", 0.25)]
    for b in spec["bubbles"]:
        ev += [(b * TB_BT + 0.55, "pop", 0.45)]
    if spec["variant"] == "refill":
        ev += [(3 * TB_BT + 0.2, "riser", 0.4), (3 * TB_BT + 1.0, "chime", 0.45)]
    else:
        ev += [((n - 1) * TB_BT + 0.2, "heartbeat", 0.4)]
    pt = spec["punch_at"] * spec["dur"]
    ev += [(pt, "impact", 0.45), (pt + 0.1, "flash", 0.35)]
    return ev


FORMATS = {
    "lifeline": {"make": make_lifeline, "draw": draw_lifeline, "events": events_lifeline},
    "tworooms": {"make": make_tworooms, "draw": draw_tworooms, "events": events_tworooms},
    "table": {"make": make_table, "draw": draw_table, "events": events_table},
}



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
