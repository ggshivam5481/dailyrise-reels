"""Formats B (round 2): tiers (95/4/1%), stack (crates / habit tower / savings jar), failstairs (stairs / rocket),
kills (KILLS / BUILDS / TRADE lists). Coloured props, a new beat every ~1 s, louder SFX.
Each format: make(rnd, used) -> spec, draw(c, t, spec), events(spec) -> [(t, kind, gain)].
Note: nv.render multiplies event gains by 1.8 (capped at 1.0), so gains here are 0.25-0.55."""
import math

import nv
import props_b as P
from nv import FLOOR, GOLD, GOLD2, GREY, RED, SUB, WHITE, W, clamp, ease, lerp, mix

GREEN = (110, 220, 130)
DARK = (20, 20, 20)
DEFAULT_T = dict(name="default", bg_top=(8, 8, 12), bg_bot=(5, 5, 5), spot=(255, 255, 255), accent=(255, 200, 80),
                 accent2=(120, 200, 255), particle=(200, 200, 255), floor=(30, 30, 33))


def th():
    T = getattr(nv, "T", None)
    return T if isinstance(T, dict) else DEFAULT_T


def _pick_key(rnd, used, build, tries=600):
    for _ in range(tries):
        key, spec = build()
        key = "b2|" + key
        if key not in used:
            used.add(key)
            spec["key"] = key
            return spec
    raise RuntimeError("script bank exhausted")


def _spot_at(c, x, floor_y, width=170, height=300, strength=0.8, color=None):
    m = nv._cone(width, height)
    if strength < 1:
        m = m.point(lambda v: int(v * strength))
    c.img.paste(color or th()["spot"], (int(x - width), int(floor_y - height)), m)


def _row_text(c, parts, cx, y, px, sp=22, icon=None, icon_s=44, t=0.0, k=1.0, positive=False):
    """One centred line made of (text, colour) parts with an optional prop icon on the left."""
    masks = [nv.text_mask(p.upper(), px) for p, _ in parts]
    total = sum(m.width for m in masks) + sp * (len(parts) - 1) + (icon_s + 24 if icon else 0)
    x = cx - total / 2 + (1 - k) * 90
    if icon:
        P.icon(c, icon, x + icon_s / 2, y + masks[0].height / 2, icon_s * max(0.01, k), t, positive)
        x += icon_s + 24
    for (p, col), m in zip(parts, masks):
        c.text(p, x, y, px, col, align="left")
        x += m.width + sp


# =====================================================================
# 1. TIERS
# =====================================================================
TIER_SETS = [("95%", "4%", "1%"), ("90%", "9%", "1%"), ("97%", "2%", "1%"), ("80%", "19%", "1%")]
TIER_TARGETS = ["hoop", "goal", "bullseye", "bell", "hurdle", "hurdle"]
TIER_GOALS = ["DREAM", "GOAL", "6 PACK", "FIRST 1 LAKH", "PROMOTION", "FLUENT ENGLISH", "OWN BUSINESS",
              "DREAM JOB", "100 FOLLOWERS", "FIRST CLIENT", "NEW HABIT", "TOP RANK", "MARATHON", "FREEDOM",
              "GOVT JOB", "SELECTION", "FIRST SALARY", "BOARD EXAM", "NEW SKILL", "OWN HOUSE"]
TIER_SCRIPTS = [
    ("WHERE ARE YOU?", "THE 1% JUST DIDN'T STOP.", "Most people quit at the first miss. The 1% keep missing until they don't.",
     "Miss hona normal hai. Rukna nahi."),
    ("WHICH ONE ARE YOU?", "MISSES ARE PART OF THE SHOT.", "Missing is not failing. Stopping is.",
     "Galti se mat daro, rukne se daro."),
    ("SAME GOAL. DIFFERENT PEOPLE.", "ONLY ONE KEPT GOING.", "Everyone wants the result. Few accept the misses before it.",
     "Sab ko result chahiye, misses koi nahi chahta."),
    ("MOST PEOPLE NEVER EVEN TRY.", "TRYING AGAIN IS THE SKILL.", "The real skill is the attempt after the failure.",
     "Asli talent hai dobara try karna."),
    ("TALENT IS NOT THE DIFFERENCE.", "ATTEMPTS ARE.", "Talent decides where you start. Attempts decide where you end.",
     "Talent start deta hai, attempts finish dete hain."),
    ("ONE MISS STOPS MOST PEOPLE.", "SEVEN MISSES MADE ONE WINNER.", "Your seventh try is someone else's first excuse.",
     "Jahan log rukte hain, wahin se jeet shuru hoti hai."),
    ("EVERYONE GETS THE SAME SHOT.", "NOT EVERYONE TAKES IT AGAIN.", "Opportunity is equal. Persistence is not.",
     "Mauka sabko milta hai, himmat sabme nahi."),
    ("BE HONEST. WHICH ROW?", "THE GOAL NEVER MOVED.", "The goal stays where it is. Only quitters move away from it.",
     "Goal wahi hai. Tum kahan ho?"),
    ("THIS IS WHY 1% WIN.", "THEY TREAT MISSES AS DATA.", "Every miss tells you how to aim the next one.",
     "Har miss agla shot better banata hai."),
    ("DON'T BE THE 95%.", "KEEP GOING.", "Comfort sits. Fear tries once. Discipline keeps going.",
     "Baithna aasaan hai, lagatar try karna rare hai."),
    ("THE DIFFERENCE IS SIMPLE.", "THEY DIDN'T QUIT.", "Success is mostly refusing to stop.", "Bas rukna mat."),
    ("SAME CHANCE. 3 OUTCOMES.", "YOUR NEXT TRY DECIDES.", "You are always one attempt away from a different row.",
     "Agla try tumhari row badal sakta hai."),
    ("FAILURE IS NOT THE END.", "QUITTING IS.", "Failure is a step. Quitting is a wall.", "Fail hona step hai, quit karna deewar."),
    ("WHO GETS THE GOAL?", "THE ONE WHO MISSED THE MOST.", "The winner usually has the most misses.",
     "Jeetne wale ke paas sabse zyada misses hote hain."),
    ("NOBODY SEES THE MISSES.", "THEY ONLY SEE THE WIN.", "People clap for the goal, never for the misses behind it.",
     "Log goal dekhte hain, uske peeche ke misses nahi."),
    ("ARE YOU STILL TRYING?", "THE 1% IS A DECISION.", "The 1% is not a talent group. It is a decision group.",
     "1% banna ek decision hai."),
    ("3 PEOPLE. 1 DREAM.", "ONLY ONE REFUSED TO STOP.", "Same dream, same chance. The difference was the next attempt.",
     "Sapna sabka same, rukna sabka alag."),
    ("THE PHONE GUY NEVER LOSES.", "BECAUSE HE NEVER PLAYS.", "You can't lose a game you never play. You can't win it either.",
     "Jo khelta hi nahi, wo jeetega kaise?"),
    ("ONE TRY IS NOT TRYING.", "IT'S TESTING.", "One attempt is a test. Real trying starts after the first failure.",
     "Ek try, try nahi hota."),
    ("YOUR ROW IS A CHOICE.", "CHOOSE AGAIN TODAY.", "You are not stuck in your row. You choose it every morning.",
     "Row tum roz khud chunte ho."),
    ("EXAM, GYM, BUSINESS.", "SAME RULE EVERYWHERE.", "In every field the winners are just the ones who kept attempting.",
     "Har field mein rule same hai, rukna mat."),
    ("WHAT DID YOU DO AFTER THE MISS?", "THAT'S YOUR ANSWER.", "The miss doesn't define you. Your next move does.",
     "Miss ke baad kya kiya, wahi tum ho."),
]
TIER_ROWS = [720, 980, FLOOR]
TIER_FIG_X, TIER_TX = 230, 860
TIER_ATT0, TIER_GAP, TIER_FLY, TIER_N = 0.7, 0.95, 0.6, 7
HURDLE_X = 560
BALL_COL = {"hoop": (240, 130, 50), "goal": (245, 245, 245), "bullseye": (230, 60, 60), "bell": GOLD}


def tiers_make(rnd, used):
    def build():
        si = rnd.randrange(len(TIER_SCRIPTS))
        top, punch, cap, ig = TIER_SCRIPTS[si]
        tset = rnd.choice(TIER_SETS)
        target = rnd.choice(TIER_TARGETS)
        goal = rnd.choice(TIER_GOALS)
        miss = [rnd.choice((-1, 1)) for _ in range(TIER_N)]
        key = f"tiers|{si}|{tset[0]}|{target}|{goal}"
        return key, dict(format="tiers", dur=9.0, top=top, punch=punch, punch_at=0.82, caption_line=cap, ig=ig,
                         topic="growth", tiers=tset, target=target, goal=goal, miss=miss)
    return _pick_key(rnd, used, build)


def _target_center(kind, floor_y):
    return {"hoop": (TIER_TX - 34, floor_y - 150), "goal": (TIER_TX, floor_y - 55),
            "bullseye": (TIER_TX, floor_y - 120), "bell": (TIER_TX, floor_y - 150),
            "hurdle": (TIER_TX, floor_y - 120)}[kind]


def _draw_target(c, kind, floor_y, lit, t):
    d = c.d
    if kind == "hoop":
        d.line([(TIER_TX + 34, floor_y), (TIER_TX + 34, floor_y - 205)], fill=(90, 94, 104), width=8)
        d.rectangle([TIER_TX + 4, floor_y - 230, TIER_TX + 40, floor_y - 130], fill=(240, 240, 244))
        d.rectangle([TIER_TX + 12, floor_y - 200, TIER_TX + 32, floor_y - 160], outline=RED, width=3)
        d.ellipse([TIER_TX - 72, floor_y - 160, TIER_TX + 4, floor_y - 140], outline=GOLD if lit else (240, 120, 40),
                  width=6)
        for i in range(5):
            x = TIER_TX - 66 + i * 16
            d.line([(x, floor_y - 150), (x + 6, floor_y - 108)], fill=(230, 230, 230), width=2)
    elif kind == "goal":
        col = GOLD if lit else (245, 245, 245)
        for i in range(8):
            d.line([(TIER_TX - 66 + i * 19, floor_y - 116), (TIER_TX - 66 + i * 19, floor_y)], fill=(90, 96, 110), width=2)
        for j in range(5):
            d.line([(TIER_TX - 66, floor_y - 116 + j * 24), (TIER_TX + 66, floor_y - 116 + j * 24)], fill=(90, 96, 110),
                   width=2)
        d.line([(TIER_TX - 70, floor_y), (TIER_TX - 70, floor_y - 120), (TIER_TX + 70, floor_y - 120),
                (TIER_TX + 70, floor_y)], fill=col, width=8)
    elif kind == "bullseye":
        d.line([(TIER_TX, floor_y), (TIER_TX, floor_y - 70)], fill=P.BROWN, width=10)
        P.target(c, TIER_TX, floor_y - 120, 108, t, lit)
    elif kind == "bell":
        d.line([(TIER_TX + 40, floor_y), (TIER_TX + 40, floor_y - 200), (TIER_TX, floor_y - 200)],
               fill=P.BROWN, width=9)
        sw = 0.15 * math.sin(t * 14) if lit else 0
        bx = TIER_TX + 30 * sw
        col = GOLD2 if lit else (215, 170, 60)
        d.polygon([(bx - 34, floor_y - 125), (bx - 22, floor_y - 182), (bx + 22, floor_y - 182),
                   (bx + 34, floor_y - 125)], fill=col)
        d.ellipse([bx - 9, floor_y - 132, bx + 9, floor_y - 114], fill=col)
    else:  # hurdle + finish flag
        for x in (HURDLE_X - 46, HURDLE_X + 46):
            d.line([(x, floor_y), (x, floor_y - 92)], fill=(220, 220, 224), width=6)
        for i in range(6):
            d.rectangle([HURDLE_X - 52 + i * 18, floor_y - 104, HURDLE_X - 34 + i * 18, floor_y - 86],
                        fill=RED if i % 2 == 0 else (245, 245, 245))
        P.flag(c, TIER_TX + 10, floor_y - 70, 140, t, GOLD if lit else th()["accent2"])


def _ball(c, t, t0, floor_y, end, miss_dir, col):
    u = (t - t0) / TIER_FLY
    if u < 0:
        return False
    sx, sy = TIER_FIG_X + 40, floor_y - 120
    if miss_dir:
        ex = end[0] - 140 if miss_dir < 0 else end[0] + 110
        ey = floor_y - 10
    else:
        ex, ey = end
    if u <= 1:
        x = lerp(sx, ex, u)
        y = lerp(sy, ey, u) - 190 * math.sin(math.pi * u)
    else:
        if not miss_dir:
            return True
        k = min(1.0, u - 1)
        x = ex + miss_dir * 50 * k
        y = floor_y - 10 - 30 * abs(math.sin(math.pi * k * 2)) * (1 - k)
    c.d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=col)
    c.d.arc([x - 14, y - 14, x + 14, y + 14], 200, 340, fill=mix(col, (0, 0, 0), 0.5), width=3)
    return u > 1


def _jumper(t, t0, fy, success):
    """Hurdle jumper position for an attempt starting at t0. Returns (x, dy, phase) or None."""
    u = (t - t0) / TIER_FLY
    if u < 0 or (not success and u > 1.6):
        return None
    if success:
        k = clamp(u)
        return lerp(TIER_FIG_X, TIER_TX - 120, ease(k)), 170 * math.sin(math.pi * k), "fly" if k < 1 else "land"
    if u <= 1:
        return lerp(TIER_FIG_X, HURDLE_X - 70, u), 60 * math.sin(math.pi * u), "fly"
    k = (u - 1) / 0.6
    return lerp(HURDLE_X - 70, TIER_FIG_X, ease(k)), 0, "fall"


def tiers_draw(c, t, spec):
    T = th()
    tset, kind = spec["tiers"], spec["target"]
    for ri, fy in enumerate(TIER_ROWS):
        if fy != FLOOR:
            c.d.line([(40, fy), (W - 40, fy)], fill=mix(T["floor"], (80, 80, 90), 0.5), width=2)
        _spot_at(c, TIER_FIG_X, fy, 150, 230, 0.75)
        c.text(f"{tset[ri]} OF PEOPLE", 60, fy - 236, 22, WHITE, align="left")
        tc = _target_center(kind, fy)
        lit = False
        if ri == 0:
            c.text("NEVER TRIED", 60, fy - 204, 16, SUB, align="left")
            P.couch(c, TIER_FIG_X + 10, fy - 30, 80, t, mix(T["accent2"], (60, 60, 70), 0.4))
            info = c.figure(TIER_FIG_X, nv.phone(t), s=0.6, col=GREY, foot_y=fy - 40)
            hx, hy = info["hands"]["r"]
            P.phone(c, hx, hy - 6, 28, t)
            if t > 3.2:  # cloud of regret rolls in
                k = P.pop(t, 3.2)
                P.cloud(c, TIER_FIG_X, fy - 250, 90 * k, t, rain=t > 3.6)
        elif ri == 1:
            t0 = TIER_ATT0 + 0.2
            if kind == "hurdle":
                st = _jumper(t, t0, fy, False)
                failed = t > t0 + TIER_FLY
            else:
                st = None
                failed = _ball(c, t, t0, fy, tc, spec["miss"][0], BALL_COL.get(kind, WHITE))
            c.text("TRIED ONCE", 60, fy - 204, 16, SUB, align="left")
            if failed:
                k = P.pop(t, t0 + TIER_FLY)
                c.text("X", 330, fy - 206, int(20 + 6 * (1 - min(1, k))), RED)
            sad = t > t0 + TIER_FLY + 0.6
            if st:
                x, dy, ph = st
                pose = nv.run(t) if ph == "fly" else nv.sad(t)
                c.figure(x, pose, s=0.6, foot_y=fy, dy=dy)
            else:
                pose = nv.sad(t) if sad else (dict(nv.BASE, ra1=150, ra2=10) if t0 - 0.25 < t < t0 + 0.2 else nv.stand(t))
                c.figure(TIER_FIG_X, pose, s=0.6, col=GREY if sad else WHITE, foot_y=fy)
            if sad:
                k = P.pop(t, t0 + TIER_FLY + 0.8)
                if k > 0:
                    P.cloud(c, TIER_FIG_X, fy - 230, 80 * k, t, rain=True)
        else:
            n_att, misses, throwing, jump = 0, 0, False, None
            for k in range(TIER_N):
                t0 = TIER_ATT0 + k * TIER_GAP
                last = k == TIER_N - 1
                if t >= t0 - 0.25:
                    n_att = k + 1
                if t0 - 0.25 < t < t0 + 0.2:
                    throwing = True
                if kind == "hurdle":
                    st = _jumper(t, t0, fy, last)
                    if st:
                        jump = st
                elif t0 <= t < t0 + TIER_FLY + 0.45:
                    md = spec["miss"][k] if not last else 0
                    if _ball(c, t, t0, fy, tc, md, BALL_COL.get(kind, WHITE)) and md == 0:
                        lit = True
                if not last and t >= t0 + TIER_FLY:
                    misses += 1
                if last and t >= t0 + TIER_FLY:
                    lit = True
            c.text(f"ATTEMPT {max(1, n_att)}", 60, fy - 204, 16, GOLD if lit else T["accent2"], align="left")
            for i in range(misses):
                t_m = TIER_ATT0 + i * TIER_GAP + TIER_FLY
                k = P.pop(t, t_m)
                c.text("X", 330 + i * 34, fy - 206 - (1 - min(1, k)) * 10, 20, RED)
            win_t = TIER_ATT0 + (TIER_N - 1) * TIER_GAP + TIER_FLY
            if kind == "hurdle":
                if lit:
                    c.figure(TIER_TX - 120, nv.celebrate(t), s=0.6, foot_y=fy)
                elif jump:
                    x, dy, ph = jump
                    c.figure(x, nv.run(t) if ph != "fall" else nv.sad(t), s=0.6, foot_y=fy, dy=dy)
                else:
                    c.figure(TIER_FIG_X, nv.stand(t), s=0.6, foot_y=fy)
            elif lit:
                c.figure(TIER_FIG_X, nv.celebrate(t), s=0.6, foot_y=fy)
            else:
                pose = dict(nv.BASE, ra1=150, ra2=10) if throwing else nv.stand(t)
                c.figure(TIER_FIG_X, pose, s=0.6, foot_y=fy)
            if lit:
                P.confetti(c, tc[0], tc[1] - 40, t, win_t, n=36, spread=260, seed=3)
                k = P.pop(t, win_t + 0.15)
                P.trophy(c, TIER_TX - 150 if kind != "hurdle" else TIER_TX + 120, fy - 300, 70 * k, t)
                P.sparks(c, tc[0], tc[1], t, win_t)
        if lit:
            c.glow(tc[0], tc[1], 70, GOLD, 0.75)
        _draw_target(c, kind, fy, lit, t)
        c.text(spec["goal"], TIER_TX, fy - 250, 18, GOLD if lit else T["accent"])


def tiers_events(spec):
    hurdle = spec["target"] == "hurdle"
    t1 = TIER_ATT0 + 0.2
    ev = [(t1, "whoosh", 0.35), (t1 + TIER_FLY, "thud" if hurdle else "snap", 0.4),
          (t1 + TIER_FLY + 0.8, "rumble", 0.3), (3.2, "pop", 0.3), (3.6, "rumble", 0.25)]
    for k in range(TIER_N):
        t0 = TIER_ATT0 + k * TIER_GAP
        ev.append((t0, "whoosh", 0.3))
        if hurdle:
            ev.append((t0, "step", 0.4))
        if k < TIER_N - 1:
            ev.append((t0 + TIER_FLY, "snap" if not hurdle else "thud", 0.4))
            ev.append((t0 + TIER_FLY + 0.05, "pop", 0.3))
    win = TIER_ATT0 + (TIER_N - 1) * TIER_GAP + TIER_FLY
    ev += [(win - 1.2, "heartbeat", 0.4), (win, "riser", 0.4), (win, "impact", 0.5), (win, "chime", 0.55),
           (win + 0.05, "flash", 0.5), (win + 0.2, "pop", 0.4)]
    return ev


# =====================================================================
# 2. STACK  (crates of excuses / tower of habits / savings jar)
# =====================================================================
STACK_NEG_WORDS = ["LATER", "TOMORROW", "SNOOZE", "EXCUSE", "NEXT MONDAY", "JUST 5 MIN", "ONE MORE EPISODE",
                   "NOT TODAY", "MAYBE", "SKIP", "I'M TIRED", "AFTER THIS", "NEW YEAR", "SCROLL", "JUNK FOOD",
                   "ONE MORE GAME"]
STACK_NEG = [
    ("EVERY LATER HAS WEIGHT.", "ONE DAY YOU CAN'T MOVE.", "Every 'later' feels light. Together they bury you.",
     "Har 'baad mein' halka lagta hai, milke dabaa dete hain."),
    ("LATER DOESN'T DISAPPEAR.", "IT PILES UP.", "Postponed work does not vanish. It waits with interest.",
     "Taala hua kaam gayab nahi hota, jama hota hai."),
    ("YOU SAID IT ONCE.", "THEN YOU SAID IT DAILY.", "A habit is just a choice you repeated without noticing.",
     "Ek baar bola, phir roz bolne lage."),
    ("SMALL DELAYS LOOK HARMLESS.", "UNTIL THEY ARE A WALL.", "Small delays look harmless until they become a wall.",
     "Chhoti der, badi deewar ban jaati hai."),
    ("ONE MORE DAY, YOU SAID.", "THE DAYS SAID YES.", "Time always agrees with your excuses. That's the danger.",
     "Waqt tumhare bahano se kabhi bahas nahi karta."),
    ("WATCH WHAT YOU REPEAT.", "IT BECOMES YOUR LIFE.", "What you repeat daily is who you become.",
     "Jo roz karte ho, wahi ban jaate ho."),
    ("IT'S JUST ONE TIME.", "SAID EVERY TIME.", "'Just once' is how every bad habit introduces itself.",
     "'Bas ek baar' se hi har buri aadat shuru hoti hai."),
    ("THIS IS HOW YOU GET STUCK.", "ONE EXCUSE AT A TIME.", "Nobody gets stuck in one day. It's one excuse at a time.",
     "Koi ek din mein nahi phansta."),
    ("FUTURE YOU IS WATCHING.", "AND CARRYING ALL OF IT.", "Comfort is a loan. Future you pays the interest.",
     "Aaj ka aaram, kal ka karz."),
    ("NOTHING HAPPENED TODAY.", "THAT'S THE PROBLEM.", "Doing nothing is also a decision. It just compounds quietly.",
     "Kuch na karna bhi ek decision hai."),
    ("YOU'RE NOT LAZY.", "YOU'RE BURIED.", "It isn't laziness. It's a pile of small delays you never cleared.",
     "Tum lazy nahi ho, dabe hue ho."),
    ("IT STARTED WITH ONE.", "NOW LOOK AT IT.", "Every pile started with one 'it's fine'.",
     "Shuruaat ek se hi hui thi."),
    ("THE PILE NEVER ASKS.", "IT JUST GROWS.", "Unfinished things don't knock. They just stack up.",
     "Adhoora kaam awaaz nahi karta, bas badhta hai."),
    ("CLEAR ONE TODAY.", "OR CARRY ALL TOMORROW.", "Clear one thing today, or carry everything tomorrow.",
     "Aaj ek hatao, warna kal sab uthao."),
]
STACK_POS_WORDS = ["READ 10 PAGES", "WORKOUT", "NO SUGAR", "WAKE 5 AM", "DEEP WORK", "SAVE 100", "WALK 5K",
                   "NO PHONE HOUR", "JOURNAL", "LEARN 1 SKILL", "COLD SHOWER", "SLEEP ON TIME", "PRACTICE", "MEDITATE"]
STACK_POS = [
    ("NOBODY SEES THE BLOCKS.", "THEY SEE THE TOWER.", "People see results. They never see the boring blocks under them.",
     "Log tower dekhte hain, eentein nahi."),
    ("ONE BLOCK A DAY.", "THAT'S THE WHOLE SECRET.", "Consistency is boring until it is impressive.",
     "Roz ek eent. Bas itna hi secret hai."),
    ("SMALL DAILY WINS.", "STACK INTO A NEW LIFE.", "Small wins don't look like much. Stacked, they look like a new life.",
     "Chhoti jeet roz, badi life ek din."),
    ("IT FEELS LIKE NOTHING.", "UNTIL IT'S EVERYTHING.", "Day 1 feels useless. Day 100 feels unfair to everyone else.",
     "Pehla din bekaar lagta hai, sauva din kamaal."),
    ("DON'T BUILD IT IN A DAY.", "BUILD IT EVERY DAY.", "You don't need a big day. You need many normal ones.",
     "Ek din mein nahi, har din banao."),
    ("YOUR HABITS ARE BRICKS.", "CHOOSE WHAT YOU BUILD.", "Every habit is a brick. You are building something either way.",
     "Har aadat ek eent hai, kya bana rahe ho?"),
    ("BORING WORK. DAILY.", "THAT'S HOW TOWERS RISE.", "The work is boring. The result is not.",
     "Kaam boring hai, result nahi."),
    ("START SMALL.", "STAY LONG.", "Start small, stay long. Time does the rest.", "Chhota shuru karo, lamba tiko."),
    ("BUILD QUIETLY.", "LET THE TOWER TALK.", "Don't announce it. Stack it.", "Chup chaap banao, tower bolega."),
    ("YOU DON'T RISE TO GOALS.", "YOU RISE TO HABITS.", "You don't rise to your goals. You rise to your daily habits.",
     "Goal nahi, aadatein upar le jaati hain."),
]
JAR_SCRIPTS = [  # (top, punch, caption, ig, unit label, step, final)
    ("₹100 A DAY.", "1 YEAR = ₹36,500.", "Small money, saved daily, becomes real money.", "Roz ₹100, saal ke ₹36,500.",
     "₹", 100, "₹36,500"),
    ("1 PAGE A DAY.", "1 YEAR = 365 PAGES.", "One page a day is a dozen books a year.", "Roz ek page, saal mein kitaabein.",
     "PAGE", 1, "12 BOOKS"),
    ("10 PUSHUPS A DAY.", "1 YEAR = 3,650.", "Ten a day looks small. A year of it looks strong.",
     "Roz 10, saal ke 3,650.", "PUSHUPS", 10, "3,650"),
    ("1% BETTER A DAY.", "1 YEAR = 37X BETTER.", "One percent better every day compounds to 37 times in a year.",
     "Roz 1%, saal mein 37 guna.", "DAY", 1, "37X"),
    ("5 NEW WORDS A DAY.", "1 YEAR = 1,825 WORDS.", "Five words a day is a new language in a year.",
     "Roz 5 words, saal mein nayi language.", "WORDS", 5, "1,825"),
    ("30 MIN A DAY.", "1 YEAR = 182 HOURS.", "Thirty minutes daily is 182 hours a year. That's a new skill.",
     "Roz 30 minute, saal ke 182 ghante.", "MIN", 30, "182 HRS"),
    ("₹50 LESS ON JUNK.", "1 YEAR = ₹18,250 SAVED.", "Skip one small waste a day and watch the jar fill.",
     "Roz ₹50 bachao, saal ke ₹18,250.", "₹", 50, "₹18,250"),
    ("1 GOOD DEED A DAY.", "1 YEAR = 365 LIVES TOUCHED.", "One kind act a day changes more lives than you think.",
     "Roz ek achha kaam.", "DEED", 1, "365"),
]
STACK_COUNTERS = ["clock", "day", "age"]
STACK_N = 8
STACK_T0, STACK_GAP, STACK_FALL = 0.6, 0.85, 0.32
BOX_W, BOX_H = 300, 74
POS_COLS = [(70, 140, 230), (90, 190, 110), (240, 150, 60), (160, 110, 230), (230, 90, 140), (40, 170, 190),
            (220, 70, 70), (200, 170, 60)]
JAR_X, JAR_W, JAR_H = 690, 300, 420


def stack_make(rnd, used):
    def build():
        r = rnd.random()
        variant = "jar" if r < 0.28 else ("pos" if r < 0.6 else "neg")
        if variant == "jar":
            si = rnd.randrange(len(JAR_SCRIPTS))
            top, punch, cap, ig, unit, step, final = JAR_SCRIPTS[si]
            topic = "money" if unit == "₹" else "habits"
            key = f"stack|jar|{si}|{rnd.randrange(6)}"
            return key, dict(format="stack", dur=10.0, top=top.replace("₹", "RS "), punch=punch.replace("₹", "RS "),
                             punch_at=0.74, caption_line=cap, ig=ig, topic=topic, variant="jar",
                             unit=unit.replace("₹", "RS"), step=step, final=final.replace("₹", "RS "),
                             positive=True, labels=[], counter="day", start=1)
        pos = variant == "pos"
        bank, words = (STACK_POS, STACK_POS_WORDS) if pos else (STACK_NEG, STACK_NEG_WORDS)
        si = rnd.randrange(len(bank))
        top, punch, cap, ig = bank[si]
        counter = "day" if pos else rnd.choice(STACK_COUNTERS)
        if pos:
            labels = rnd.sample(words, STACK_N)
            word = "/".join(labels[:3])
        else:
            word = rnd.choice(words)
            labels = [word] * STACK_N
        key = f"stack|{variant}|{si}|{word}|{counter}"
        return key, dict(format="stack", dur=10.0, top=top, punch=punch, punch_at=0.72, caption_line=cap, ig=ig,
                         topic="habits" if pos else "discipline", variant=variant, positive=pos, labels=labels,
                         counter=counter, start=rnd.choice((7, 8, 9)) if counter == "clock" else rnd.choice((18, 20, 22)))
    return _pick_key(rnd, used, build)


def _stack_slots(pos):
    slots = []
    if pos:
        for i in range(STACK_N):
            slots.append((640 + (8 if i % 2 else -8), FLOOR - (i + 1) * BOX_H))
    else:
        xs = [540 - BOX_W - 6, 546, 540 - BOX_W / 2]
        layer_h = [0, 0, 0]
        for i in range(STACK_N):
            col = i % 3
            if col == 2:
                lh = max(layer_h)
                y = FLOOR - lh - BOX_H
                layer_h = [lh + BOX_H] * 3
            else:
                y = FLOOR - layer_h[col] - BOX_H
                layer_h[col] += BOX_H
            slots.append((xs[col] + (i // 3) * 4, y))
    return slots


def _counter_text(spec, n):
    if spec["counter"] == "clock":
        h = spec["start"] + n
        ampm = "AM" if h % 24 < 12 else "PM"
        return f"{h % 12 or 12}:00 {ampm}"
    if spec["counter"] == "age":
        return f"AGE {spec['start'] + n * 3}"
    days = [1, 3, 7, 14, 30, 60, 100, 180, 365]
    return f"DAY {days[min(n, len(days) - 1)]}"


def _crate(c, x0, y, w, h, col, label, t, positive):
    c.block(x0, y, x0 + w, y + h, col)
    c.d.rectangle([x0, y, x0 + w - 4, y + 8], fill=mix(col, (255, 255, 255), 0.35))
    P.icon(c, label, x0 + 36, y + h / 2, 40, t, positive)
    px = 18 if len(label) <= 11 else 15
    m = nv.text_mask(label, px)
    c.text(label, x0 + 64 + (w - 70) / 2 - m.width / 2 + 2, y + h / 2 - m.height / 2, px, WHITE, world=True)


def _jar_draw(c, t, spec):
    T = th()
    dur = spec["dur"]
    n_total = 9
    gap = (dur * 0.68 - 0.6) / n_total
    drops = sum(1 for i in range(n_total) if t >= 0.6 + i * gap + 0.35)
    done = t >= dur * 0.7
    c.spot(330, 280, strength=0.9)
    c.spot(JAR_X, 320, color=GOLD2 if done else None, strength=0.9 if done else 0.6)
    # counter
    days = [1, 7, 30, 60, 100, 150, 200, 250, 300, 365]
    d_i = days[min(drops, len(days) - 1)]
    c.text(f"DAY {d_i}", W / 2, 430, 60, GOLD if done else T["accent"])
    amt = spec["final"] if done else f"{spec['unit']} {d_i * spec['step']:,}" if spec["unit"] == "RS" else \
        f"{d_i * spec['step']:,} {spec['unit']}"
    c.text(amt, JAR_X, FLOOR - JAR_H - 120, 30, GOLD if done else WHITE)
    # figure dropping coins/items
    dropping = any(0.6 + i * gap - 0.25 <= t < 0.6 + i * gap for i in range(n_total))
    pose = nv.celebrate(t) if done else (dict(nv.BASE, ra1=140, ra2=-30) if dropping else nv.stand(t))
    c.figure(330, pose)
    # jar fill
    fill = min(1.0, drops / n_total)
    jx0, jx1, jy1 = JAR_X - JAR_W / 2, JAR_X + JAR_W / 2, FLOOR
    jy0 = FLOOR - JAR_H
    fh = (JAR_H - 40) * fill
    coin_cols = [GOLD, (220, 170, 50), GOLD2] if spec["unit"] == "RS" else [th()["accent"], th()["accent2"], GOLD]
    rows = int(fh / 22)
    for r in range(rows):
        y = jy1 - 18 - r * 22
        for k in range(6):
            x = jx0 + 34 + k * 44 + (11 if r % 2 else 0)
            if x < jx1 - 26:
                c.d.ellipse([x - 20, y - 9, x + 20, y + 9], fill=coin_cols[(r + k) % 3])
    # falling item
    for i in range(n_total):
        t0 = 0.6 + i * gap
        if t0 <= t < t0 + 0.35:
            u = (t - t0) / 0.35
            y = lerp(jy0 - 160, jy1 - 30 - fh, u * u)
            P.coin(c, JAR_X, y, 40, t) if spec["unit"] == "RS" else P.star(c, JAR_X, y, 40, t, T["accent"])
    # jar glass
    c.d.rounded_rectangle([jx0, jy0, jx1, jy1], 30, outline=(200, 225, 240), width=6)
    c.d.rectangle([jx0 + 30, jy0 - 34, jx1 - 30, jy0 + 4], fill=P.BROWN)
    c.d.line([(jx0 + 26, jy0 + 40), (jx0 + 26, jy1 - 40)], fill=(240, 250, 255), width=5)
    if done:
        c.glow(JAR_X, jy0 + JAR_H / 2, 170, GOLD, 0.6)
        P.confetti(c, JAR_X, jy0, t, dur * 0.7, n=44, seed=7)
        P.sparks(c, JAR_X, jy0 - 40, t, dur * 0.7)


def stack_draw(c, t, spec):
    T = th()
    if spec.get("variant") == "jar":
        return _jar_draw(c, t, spec)
    pos = spec["positive"]
    slots = _stack_slots(pos)
    landed = sum(1 for i in range(STACK_N) if t >= STACK_T0 + i * STACK_GAP + STACK_FALL)
    done = landed >= STACK_N
    fig_x = 400 if pos else 540
    c.spot(fig_x, 300, strength=0.9)
    if pos:
        c.spot(790, 260, strength=0.6)
    warn = (not pos) and landed >= STACK_N - 2
    ctr = _counter_text(spec, landed)
    pulse = 1 + (0.08 * math.sin(t * 12) if warn else 0)
    c.text(ctr, W / 2, 440, int(64 * pulse), RED if warn else (GOLD if pos and done else T["accent"]))
    if pos:
        held = None
        for i in range(STACK_N):
            t0 = STACK_T0 + i * STACK_GAP
            if t0 - 0.5 * STACK_GAP <= t < t0:
                held = i
        pose = nv.celebrate(t) if done else (nv.carry_up(t) if held is not None else nv.stand(t))
        info = c.figure(fig_x, pose)
        if held is not None and not done:
            hx = (info["hands"]["l"][0] + info["hands"]["r"][0]) / 2
            hy = min(info["hands"]["l"][1], info["hands"]["r"][1])
            _crate(c, hx - 110, hy - 52, 220, 52, POS_COLS[held % len(POS_COLS)], spec["labels"][held], t, True)
    else:
        k = landed / STACK_N
        pose = nv.sad(t) if k > 0.4 else nv.stand(t)
        c.figure(fig_x, pose, col=mix(WHITE, GREY, k))
    neg_cols = [mix(T["accent2"], (70, 70, 80), 0.55), mix(RED, (70, 70, 80), 0.55), mix(T["accent"], (70, 70, 80), 0.6)]
    for i in range(STACK_N):
        t0 = STACK_T0 + i * STACK_GAP
        if t < t0:
            continue
        x0, y1 = slots[i]
        u = clamp((t - t0) / STACK_FALL)
        y = lerp(y1 - (420 if pos else 700), y1, u * u)
        if pos:
            col = GOLD if done and i == STACK_N - 1 else POS_COLS[i % len(POS_COLS)]
        else:
            col = neg_cols[i % 3]
        _crate(c, x0, y, BOX_W, BOX_H, col, spec["labels"][i], t, pos)
        tl = t0 + STACK_FALL
        P.puff(c, x0 + BOX_W / 2, y1 + BOX_H, t, tl, col=T["particle"])
        if pos:
            P.sparks(c, x0 + BOX_W / 2, y1 + BOX_H / 2, t, tl, col=POS_COLS[i % len(POS_COLS)], n=8)
    end = STACK_T0 + (STACK_N - 1) * STACK_GAP + STACK_FALL
    if pos and done:
        tx = slots[-1][0] + BOX_W / 2
        c.glow(tx, slots[-1][1] - 20, 130, GOLD, 0.75)
        c.spot(tx, 260, color=GOLD2, strength=0.8)
        k = P.pop(t, end + 0.1)
        P.trophy(c, tx, slots[-1][1] - 70, 90 * k, t)
        P.confetti(c, tx, slots[-1][1] - 60, t, end, n=44, seed=5)
    elif not pos and landed >= STACK_N - 3:
        k = P.pop(t, STACK_T0 + (STACK_N - 3) * STACK_GAP + STACK_FALL)
        P.cloud(c, 540, 600, 200 * k, t, rain=True, col=(80, 86, 100))
        if done:
            c.glow(540, 760, 160, RED, 0.25 + 0.1 * math.sin(t * 8))


def stack_events(spec):
    dur = spec["dur"]
    if spec.get("variant") == "jar":
        n_total = 9
        gap = (dur * 0.68 - 0.6) / n_total
        ev = []
        for i in range(n_total):
            t0 = 0.6 + i * gap
            ev += [(t0, "whoosh", 0.25), (t0 + 0.35, "pop", 0.45), (t0 + 0.35, "chime", 0.18)]
        ev += [(dur * 0.7 - 1.0, "riser", 0.45), (dur * 0.7, "impact", 0.5), (dur * 0.7, "chime", 0.55),
               (dur * 0.7 + 0.05, "flash", 0.5)]
        return ev
    ev = []
    for i in range(STACK_N):
        t0 = STACK_T0 + i * STACK_GAP
        tl = t0 + STACK_FALL
        ev += [(t0, "whoosh", 0.25), (tl, "thud", 0.35 + 0.02 * i), (tl, "pop", 0.3)]
    end = STACK_T0 + (STACK_N - 1) * STACK_GAP + STACK_FALL
    if spec["positive"]:
        ev += [(end - 1.0, "riser", 0.45), (end, "impact", 0.45), (end, "chime", 0.55), (end + 0.05, "flash", 0.5)]
    else:
        ev += [(end - 2.0, "heartbeat", 0.45), (end - 1.3, "rumble", 0.45), (end, "impact", 0.55),
               (end + 0.3, "heartbeat", 0.5)]
    return ev


# =====================================================================
# 3. FAILSTAIRS  (stairs of failures / rocket that keeps failing to launch)
# =====================================================================
FAIL_SETS = [
    ["FAIL"] * 6,
    ["NO", "NO", "REJECTED", "NO", "REJECTED", "NO"],
    ["FAIL", "TRY AGAIN", "FAIL", "TRY AGAIN", "FAIL", "TRY AGAIN"],
    ["LOST", "LOST", "LOST", "LOST", "LOST", "LOST"],
    ["0 SALES", "1 SALE", "0 SALES", "3 SALES", "2 SALES", "9 SALES"],
    ["REJECTED", "IGNORED", "REJECTED", "LAUGHED AT", "IGNORED", "DOUBTED"],
    ["FALL", "FALL", "FALL", "FALL", "FALL", "FALL"],
    ["MISTAKE", "MISTAKE", "LESSON", "MISTAKE", "LESSON", "LESSON"],
    ["0 VIEWS", "12 VIEWS", "3 VIEWS", "40 VIEWS", "9 VIEWS", "200 VIEWS"],
    ["FAILED", "FAILED", "BACKLOG", "FAILED", "BACKLOG", "PASSED?"],
]
FAIL_TOPS = ["SUCCESS", "WIN", "DREAM", "GOAL", "FREEDOM", "RESULT", "SELECTED", "1M"]
FAIL_SCRIPTS = [
    ("EVERY FAIL IS A STEP.", "KEEP CLIMBING.", "Every failure is a step, if you keep climbing.",
     "Har fail ek seedhi hai, chadhte raho."),
    ("THEY ALL SAID NO.", "THE NOS BUILT THE STAIRS.", "Every no you survive becomes a step under your feet.",
     "Har 'no' tumhe upar le jaata hai."),
    ("SUCCESS HAS A STAIRCASE.", "IT'S MADE OF FAILURES.", "Success is not a lift. It's a staircase of failures.",
     "Success lift nahi, seedhi hai."),
    ("YOU'RE NOT FAILING.", "YOU'RE CLIMBING.", "Failure feels like falling. It is actually climbing.",
     "Tum gir nahi rahe, chadh rahe ho."),
    ("FAILURE IS NOT THE OPPOSITE.", "IT'S THE PATH.", "Failure is not the opposite of success. It is part of it.",
     "Fail hona success ka hissa hai."),
    ("DON'T FEAR THE FALL.", "STAND ON IT.", "Use every fall as a step, not as a stop.",
     "Girne se mat daro, us par khade ho jao."),
    ("COUNT YOUR FAILS.", "THAT'S HOW HIGH YOU ARE.", "Your failures measure how far you have climbed.",
     "Jitne fail, utni unchai."),
    ("NOBODY SKIPS THESE STEPS.", "NOT EVEN THE GREATS.", "Every legend climbed the same ugly stairs.",
     "Koi bhi ye steps skip nahi karta."),
    ("ONE MORE TRY.", "THAT'S ALL IT EVER TAKES.", "The top step is always one more try away.",
     "Bas ek try aur."),
    ("THEY SAW YOU FAIL.", "NOW THEY SEE YOU WIN.", "Let them watch the failures. They'll stay for the win.",
     "Fail dekhne wale jeet bhi dekhenge."),
    ("MISTAKES ARE STAIRS.", "NOT WALLS.", "Treat mistakes as stairs, not walls.", "Galti seedhi hai, deewar nahi."),
    ("ATTEMPT 1 FEELS USELESS.", "ATTEMPT 7 CHANGES LIFE.", "The early attempts are paying for the last one.",
     "Pehle attempts aakhri ki keemat chukate hain."),
    ("STILL FAILING?", "GOOD. YOU'RE STILL GOING.", "If you're still failing, you're still in the game.",
     "Fail ho rahe ho matlab game mein ho."),
    ("REJECTION IS REDIRECTION.", "UP.", "Rejection only redirects you. Usually upward.", "Rejection raasta badalta hai, upar."),
    ("SUCCESS LOOKS SUDDEN.", "IT NEVER IS.", "Overnight success usually takes years of stairs.",
     "Raaton-raat success saalon lagta hai."),
    ("EVERY TOPPER HAS THIS STAIRCASE.", "THEY JUST DON'T SHOW IT.", "Every topper climbed a staircase you never saw.",
     "Har topper ki seedhi chhupi hoti hai."),
    ("THE VIEWS WERE ZERO.", "HE POSTED ANYWAY.", "Zero views is just step one of the staircase.",
     "Zero views bhi ek step hai."),
]
ROCKET_SCRIPTS = [
    ("IT FAILED 6 TIMES.", "LAUNCH 7 CHANGED EVERYTHING.", "The launch that worked was built on six that didn't.",
     "6 baar fail, 7th baar udaan."),
    ("EVERYONE LAUGHED AT LAUNCH 1.", "NOBODY LAUGHS NOW.", "They laugh at the smoke. Later they watch the flight.",
     "Pehle hasenge, phir dekhte reh jayenge."),
    ("SMOKE IS NOT FAILURE.", "IT'S WARM UP.", "Every failed start is your engine warming up.",
     "Dhuaan failure nahi, warm up hai."),
    ("FAIL. FIX. TRY AGAIN.", "THEN FLY.", "Fail, fix, try again. That's the whole method.",
     "Fail, fix, phir try. Phir udaan."),
    ("YOUR IDEA WON'T FLY?", "NOT YET.", "Most things that fly failed on the ground first.",
     "Abhi nahi udi, matlab kabhi nahi, aisa nahi."),
    ("ONE MORE IGNITION.", "THAT'S THE DIFFERENCE.", "The difference between grounded and flying is one more try.",
     "Ek aur try, bas itna farak."),
    ("THEY STOPPED AT SMOKE.", "YOU KEEP PRESSING.", "Most people quit when they see smoke. Keep pressing the button.",
     "Log dhuaan dekh ke ruk jaate hain."),
    ("EVERY STARTUP LOOKS LIKE THIS.", "UNTIL IT DOESN'T.", "Every success looked like a failure for a while.",
     "Har success pehle failure jaisi dikhti hai."),
]
FS_N = 7
FS_SW, FS_SH, FS_X0 = 128, 70, 110
RK_X, RK_N = 720, 7


def failstairs_make(rnd, used):
    def build():
        if rnd.random() < 0.35:
            si = rnd.randrange(len(ROCKET_SCRIPTS))
            top, punch, cap, ig = ROCKET_SCRIPTS[si]
            key = f"failstairs|rocket|{si}|{rnd.randrange(5)}"
            return key, dict(format="failstairs", dur=10.0, top=top, punch=punch, punch_at=0.74, caption_line=cap,
                             ig=ig, topic="growth", variant="rocket", labels=[], goal="LIFT OFF")
        si = rnd.randrange(len(FAIL_SCRIPTS))
        top, punch, cap, ig = FAIL_SCRIPTS[si]
        li = rnd.randrange(len(FAIL_SETS))
        goal = rnd.choice(FAIL_TOPS)
        key = f"failstairs|{si}|{li}|{goal}"
        return key, dict(format="failstairs", dur=10.0, top=top, punch=punch, punch_at=0.76, caption_line=cap,
                         ig=ig, topic="growth", variant="stairs", labels=FAIL_SETS[li] + [goal], goal=goal)
    return _pick_key(rnd, used, build)


def _rocket_draw(c, t, spec):
    T = th()
    dur = spec["dur"]
    win_t = dur * 0.62
    gap = (win_t - 0.6) / (RK_N - 1)
    att = sum(1 for i in range(RK_N) if t >= 0.6 + i * gap)
    won = t >= win_t
    c.spot(300, 280, strength=0.85)
    c.spot(RK_X, 360, color=GOLD2 if won else None, strength=0.95 if won else 0.7)
    # launch pad + button
    c.block(RK_X - 120, FLOOR - 40, RK_X + 120, FLOOR, (90, 96, 110))
    c.block(430, FLOOR - 80, 480, FLOOR, (70, 74, 86))
    pressed = any(0.6 + i * gap - 0.1 <= t < 0.6 + i * gap + 0.15 for i in range(RK_N))
    c.d.ellipse([437, FLOOR - 100 + (6 if pressed else 0), 473, FLOOR - 72], fill=RED)
    pose = nv.celebrate(t) if won else (dict(nv.BASE, ra1=70, ra2=20) if pressed else
                                        (nv.sad(t) if att >= 3 and not pressed else nv.stand(t)))
    c.figure(370, pose)
    # rocket
    if won:
        u = clamp((t - win_t) / 1.6)
        ry = lerp(FLOOR - 140, 640, ease(u))
        for k in range(6):  # smoke trail
            ty = ry + 160 + k * 70
            if ty < FLOOR:
                r = 30 + k * 10
                c.d.ellipse([RK_X - r, ty - r / 2, RK_X + r, ty + r / 2], fill=(200, 200, 206))
        P.rocket(c, RK_X, ry, 220, t, flame=True)
        c.glow(RK_X, ry + 120, 120, (255, 160, 60), 0.6)
        P.confetti(c, RK_X, 700, t, win_t + 1.2, n=44, seed=9)
        P.sparks(c, RK_X, FLOOR - 60, t, win_t)
    else:
        shake = 0
        for i in range(att):
            t0 = 0.6 + i * gap
            if 0 <= t - t0 < 0.5:
                shake = 8 * math.sin((t - t0) * 70) * (1 - (t - t0) / 0.5)
        P.rocket(c, RK_X + shake, FLOOR - 140, 220, t, flame=shake != 0 and abs(shake) > 4)
        for i in range(att):
            P.puff(c, RK_X, FLOOR - 40, t, 0.6 + i * gap + 0.1, col=(170, 170, 176), n=8, size=60)
    # fail log
    for i in range(min(att, RK_N - 1)):
        t0 = 0.6 + i * gap + 0.25
        if t >= t0:
            k = P.pop(t, t0)
            c.text(f"LAUNCH {i + 1}: FAIL", 70, 600 + i * 40, 18, (255, 150, 150) if k >= 1 else WHITE, align="left")
    c.text(f"ATTEMPT {max(1, att)}", 300, 540, 30, GOLD if won else T["accent2"])
    if won:
        c.text("LAUNCH 7: SUCCESS", 70, 600 + (RK_N - 1) * 40, 18, GOLD, align="left")


def failstairs_draw(c, t, spec):
    T = th()
    if spec.get("variant") == "rocket":
        return _rocket_draw(c, t, spec)
    dur = spec["dur"]
    climb = dur * 0.72
    k = clamp(t / climb) * (FS_N - 0.5)
    step = int(k)
    frac = k - step
    won = t >= climb
    gx = FS_X0 + (FS_N - 1) * FS_SW + FS_SW / 2
    P.mountain(c, 760, FLOOR - 560, 260)
    c.spot(gx, 300, color=GOLD2 if won else None, strength=0.9 if won else 0.45)
    c.spot(FS_X0 + 60 + k * FS_SW, 260, strength=0.7)
    for i, lab in enumerate(spec["labels"]):
        x0 = FS_X0 + i * FS_SW
        y0 = FLOOR - (i + 1) * FS_SH
        last = i == FS_N - 1
        edge = mix(T["accent2"], T["accent"], i / (FS_N - 1))
        col = GOLD if (last and won) else mix(edge, (40, 40, 46), 0.72)
        c.block(x0, y0, x0 + FS_SW - 6, FLOOR, col)
        c.d.line([(x0, y0), (x0 + FS_SW - 8, y0)], fill=GOLD2 if (last and won) else edge, width=5)
        reached = i < step or (i == step and frac > 0.5)
        px = 16 if len(lab) <= 7 else 13
        txt_col = (40, 30, 0) if (last and won) else (RED if (reached and not last) else (215, 215, 220))
        c.text(lab, x0 + (FS_SW - 6) / 2, y0 + 18, px, txt_col, world=True)
        if not last:
            t_step = (i + 0.5) / (FS_N - 0.5) * climb
            P.sparks(c, x0 + FS_SW / 2, y0, t, t_step, col=edge, n=8)
    top_y = FLOOR - FS_N * FS_SH
    P.flag(c, gx + 40, top_y - 70, 140, t, GOLD if won else T["accent2"])
    if won:
        c.glow(gx, top_y - 40, 150, GOLD, 0.8)
        P.confetti(c, gx, top_y - 120, t, climb, n=50, seed=11)
        k2 = P.pop(t, climb + 0.2)
        P.trophy(c, gx - 10, top_y - 330, 90 * k2, t)
    else:
        P.cloud(c, FS_X0 + 60 + k * FS_SW, FLOOR - step * FS_SH - 420, 110, t, rain=True, col=(90, 96, 112))
    x = FS_X0 + 56 + k * FS_SW
    floor = FLOOR - step * FS_SH - (FS_SH * ease((frac - 0.5) * 2) if frac > 0.5 else 0)
    if won:
        c.figure(FS_X0 + (FS_N - 1) * FS_SW + 58, nv.celebrate(t), s=0.85, foot_y=top_y)
    else:
        c.figure(x, nv.walk(t, 8, 26), s=0.85, foot_y=floor)
    att = min(FS_N, step + 1)
    c.text(f"ATTEMPT {att}", 300, 620, 34, GOLD if won else T["accent"])


def failstairs_events(spec):
    dur = spec["dur"]
    if spec.get("variant") == "rocket":
        win_t = dur * 0.62
        gap = (win_t - 0.6) / (RK_N - 1)
        ev = []
        for i in range(RK_N - 1):
            t0 = 0.6 + i * gap
            ev += [(t0, "pop", 0.35), (t0 + 0.05, "rumble", 0.4), (t0 + 0.25, "snap", 0.4), (t0 + 0.3, "thud", 0.3)]
        ev += [(win_t - 1.0, "heartbeat", 0.45), (win_t, "pop", 0.4), (win_t, "riser", 0.5), (win_t, "rumble", 0.55),
               (win_t + 0.1, "whoosh", 0.55), (win_t + 0.3, "impact", 0.5), (win_t + 1.2, "chime", 0.55),
               (win_t + 1.2, "flash", 0.5)]
        return ev
    climb = dur * 0.72
    ev = []
    for i in range(FS_N):
        ts = (i + 0.5) / (FS_N - 0.5) * climb
        ev += [(ts, "step", 0.45), (ts + 0.02, "pop", 0.3)]
        if i < FS_N - 1:
            ev.append((ts + 0.1, "snap", 0.2))
    ev += [(climb - 1.0, "riser", 0.45), (climb, "impact", 0.5), (climb, "chime", 0.55), (climb, "flash", 0.5),
           (climb + 0.2, "pop", 0.4)]
    return ev


# =====================================================================
# 4. KILLS  (X KILLS Y / X BUILDS Y / TRADE X FOR Y)
# =====================================================================
KILL_PAIRS = [("LAZINESS", "AMBITION"), ("PHONE", "FOCUS"), ("FEAR", "DREAMS"), ("COMFORT", "GROWTH"),
              ("DOUBT", "ACTION"), ("EGO", "LEARNING"), ("EXCUSES", "RESULTS"), ("OVERTHINKING", "PEACE"),
              ("COMPARISON", "JOY"), ("SUGAR", "ENERGY"), ("SCROLLING", "TIME"), ("ANGER", "WISDOM"),
              ("WAITING", "CHANCES"), ("GOSSIP", "TRUST"), ("DEBT", "FREEDOM"), ("GAMING", "HOURS"),
              ("PERFECTION", "PROGRESS"), ("BLAME", "GROWTH"), ("ENVY", "PEACE"), ("NOISE", "CLARITY"),
              ("REGRET", "TODAY"), ("LATE NIGHTS", "MORNINGS"), ("SHORTCUTS", "SKILL"), ("COMPLAINING", "ENERGY"),
              ("JUNK", "HEALTH")]
BUILD_PAIRS = [("DISCIPLINE", "FREEDOM"), ("READING", "WISDOM"), ("SILENCE", "CLARITY"), ("SAVING", "SECURITY"),
               ("SLEEP", "ENERGY"), ("PATIENCE", "WEALTH"), ("GRATITUDE", "PEACE"), ("INVESTING", "WEALTH"),
               ("WALKING", "HEALTH"), ("FOCUS", "RESULTS"), ("HONESTY", "TRUST"), ("ROUTINE", "MOMENTUM"),
               ("LISTENING", "RESPECT"), ("CONSISTENCY", "CONFIDENCE"), ("EFFORT", "LUCK"), ("CALM", "DECISIONS"),
               ("LEARNING", "OPTIONS"), ("EXERCISE", "MOOD"), ("PLANNING", "TIME")]
TRADE_PAIRS = [("SCROLLING", "READING"), ("JUNK", "FRUITS"), ("LATE NIGHTS", "WAKING EARLY"), ("GOSSIP", "SILENCE"),
               ("COMPLAINING", "PLANNING"), ("GAMING", "LEARNING"), ("EXCUSES", "EFFORT"), ("COMFORT", "EXERCISE"),
               ("ENVY", "GRATITUDE"), ("DEBT", "SAVING"), ("PHONE", "JOURNALING"), ("WAITING", "ROUTINE"),
               ("OVERTHINKING", "WALKING"), ("SUGAR", "WATER"), ("NOISE", "SILENCE"), ("BLAME", "FOCUS")]
KILL_SCRIPTS = [
    ("WHAT IS KILLING YOUR DREAMS?", None, "Most dreams don't die in one blow. They die of small daily habits.",
     "Sapne ek din mein nahi marte."),
    ("READ THIS TWICE.", None, "Read the list again. Circle the one you need to fix today.", "Is list ko do baar padho."),
    ("SILENT KILLERS.", None, "The most dangerous habits are the quiet ones.", "Sabse khatarnak aadatein chupchaap hoti hain."),
    ("CHOOSE WHAT YOU FEED.", None, "Whatever you feed daily is what grows.", "Jo roz khilaoge, wahi badhega."),
    ("WHICH ONE IS YOURS?", None, "Be honest. Which one is stealing from you?", "Sach bolo, tumhara kaun sa hai?"),
    ("SAVE THIS LIST.", None, "Save it. Read it when you feel stuck.", "Save karo, atko to padhna."),
    ("YOUR LIFE IS LEAKING.", None, "You don't lose life in big moments. It leaks through small habits.",
     "Zindagi chhoti aadaton se leak hoti hai."),
    ("THE ENEMY IS IN YOUR ROUTINE.", None, "Your biggest enemy is hidden in your daily routine.",
     "Dushman tumhari routine mein chhupa hai."),
    ("STOP FEEDING THESE.", None, "Starve the habits that are starving you.", "Inhe khilana band karo."),
]
BUILD_SCRIPTS = [
    ("WHAT BUILDS A STRONG LIFE?", None, "A strong life is built from boring, repeated choices.",
     "Strong life boring choices se banti hai."),
    ("THE QUIET BUILDERS.", None, "The habits that build you rarely feel exciting.", "Jo aadatein banati hain, wo shor nahi karti."),
    ("BUILD THESE. DAILY.", None, "Pick one. Do it today. Repeat tomorrow.", "Ek chuno, aaj karo, kal phir."),
    ("SAVE THIS. BUILD THIS.", None, "Small habits, built daily, become who you are.", "Chhoti aadatein, roz, tum ban jaati hain."),
    ("THE 1% DO THESE.", None, "None of these are exciting. All of them are powerful.", "1% log yahi karte hain."),
    ("PICK ONE FOR TODAY.", None, "You don't need all six. Start with one today.", "Aaj sirf ek chuno."),
]
TRADE_SCRIPTS = [
    ("SMALL TRADES. BIG LIFE.", None, "Your life changes one small trade at a time.", "Chhote trade, badi life."),
    ("UPGRADE YOUR DAY.", None, "Swap one habit today. Swap another next week.", "Ek aadat badlo, din badlega."),
    ("SWAP THIS FOR THAT.", None, "You don't need to quit everything. Just trade better.", "Sab chhodna nahi, bas swap karo."),
    ("THE 30-DAY SWAP.", None, "Pick one swap. Do it for 30 days. Watch yourself change.", "30 din, ek swap."),
    ("WHAT ARE YOU TRADING TODAY?", None, "Every day you trade something. Make it a good trade.", "Har din kuch trade karte ho."),
]
KILL_ACTIONS = ["walk", "run"]
KILL_T0, KILL_GAP = 0.5, 0.8


def kills_make(rnd, used):
    def build():
        r = rnd.random()
        kind = "trade" if r < 0.3 else ("build" if r < 0.55 else "kill")
        pairs = rnd.sample({"trade": TRADE_PAIRS, "build": BUILD_PAIRS, "kill": KILL_PAIRS}[kind], 6)
        bank = {"trade": TRADE_SCRIPTS, "build": BUILD_SCRIPTS, "kill": KILL_SCRIPTS}[kind]
        si = rnd.randrange(len(bank))
        top, punch, cap, ig = bank[si]
        key = f"kills|{kind}|{'/'.join(a for a, _ in pairs)}"
        return key, dict(format="kills", dur=7.5, top=top, punch=punch, punch_at=0.9, caption_line=cap, ig=ig,
                         topic="mindset" if kind == "kill" else "habits", positive=kind != "kill", kind=kind,
                         pairs=pairs, action=rnd.choice(KILL_ACTIONS),
                         verb={"trade": "FOR", "build": "BUILDS", "kill": "KILLS"}[kind])
    return _pick_key(rnd, used, build)


def kills_draw(c, t, spec):
    T = th()
    kind = spec.get("kind", "build" if spec["positive"] else "kill")
    px, gap = (26 if kind == "trade" else 30), 66
    y0 = 560
    a_col = {"kill": RED, "build": GREEN, "trade": RED}[kind]
    b_col = {"kill": GREEN, "build": GOLD, "trade": GREEN}[kind]
    for i, (a, b) in enumerate(spec["pairs"]):
        ti = KILL_T0 + i * KILL_GAP
        if t < ti:
            break
        k = min(1.0, P.pop(t, ti))
        y = y0 + i * gap
        if kind == "trade":
            parts = [("TRADE", T["accent2"]), (a, a_col), ("FOR", WHITE), (b, b_col)]
        else:
            parts = [(a, a_col), (spec["verb"], WHITE), (b, b_col)]
        _row_text(c, parts, W / 2, y, px, icon=a if kind != "trade" else b, icon_s=46, t=t, k=k,
                  positive=kind != "kill")
        if kind == "kill" and k >= 1 and t > ti + 0.4:  # strike the victim word in red once it lands
            pass
    # floor: the habits' objects pile around the walking figure
    c.spot(540, 320, strength=0.85)
    for i, (a, b) in enumerate(spec["pairs"]):
        ti = KILL_T0 + i * KILL_GAP + 0.15
        if t < ti:
            break
        word = b if kind == "trade" else a
        x = [190, 890, 300, 780, 120, 960][i]
        k = P.pop(t, ti)
        if kind == "kill":
            c.glow(x, FLOOR - 50, 50, RED, 0.25)
        else:
            c.glow(x, FLOOR - 50, 50, GOLD, 0.35)
        P.icon(c, word, x, FLOOR - 50, 74 * max(0.01, k), t, kind != "kill")
    act = spec["action"]
    done = t > KILL_T0 + 5 * KILL_GAP + 0.6
    if kind != "kill" and done:
        c.figure(540, nv.celebrate(t), s=0.85)
        P.confetti(c, 540, FLOOR - 400, t, KILL_T0 + 5 * KILL_GAP + 0.6, n=36, seed=4)
    elif kind == "kill" and done:
        c.figure(540, nv.sad(t), s=0.85, col=GREY)
        P.cloud(c, 540, FLOOR - 360, 140, t, rain=True)
    elif act == "walk":
        c.figure(540, nv.walk(t, 7, 22), s=0.85)
    else:
        c.figure(540, nv.run(t), s=0.85)


def kills_events(spec):
    ev = []
    for i in range(6):
        ti = KILL_T0 + i * KILL_GAP
        ev += [(ti, "pop", 0.4), (ti, "whoosh", 0.2), (ti + 0.15, "thud", 0.3)]
    end = KILL_T0 + 5 * KILL_GAP + 0.6
    if spec.get("positive"):
        ev += [(end - 0.6, "riser", 0.4), (end, "chime", 0.55), (end, "flash", 0.45)]
    else:
        ev += [(end - 0.6, "heartbeat", 0.45), (end, "impact", 0.5), (end + 0.1, "rumble", 0.4)]
    return ev


FORMATS = {
    "tiers": {"make": tiers_make, "draw": tiers_draw, "events": tiers_events},
    "stack": {"make": stack_make, "draw": stack_draw, "events": stack_events},
    "failstairs": {"make": failstairs_make, "draw": failstairs_draw, "events": failstairs_events},
    "kills": {"make": kills_make, "draw": kills_draw, "events": kills_events},
}


def _frame(spec, t):
    fmt = FORMATS[spec["format"]]
    c = nv.Canvas()
    if hasattr(c, "particles"):
        c.particles(t)
    fmt["draw"](c, t, spec)
    y = nv.TOP_Y
    if spec.get("top"):
        y = c.lines(spec["top"], W / 2, y, 30)
    if spec.get("punch") and t >= spec.get("punch_at", 0.66) * spec["dur"]:
        c.lines(spec["punch"], W / 2, y + nv.PUNCH_GAP, 30, th()["accent"])
    return nv.watermark(c.finish(t), t)


if __name__ == "__main__":
    import os
    import random
    import sys

    from PIL import Image
    os.makedirs("out", exist_ok=True)
    rnd = random.Random(int(os.environ.get("SEED", "5")))
    used = set()
    only = [a for a in sys.argv[1:] if not a.startswith("-")] or list(FORMATS)
    for fi, name in enumerate(only):
        specs = []
        for _ in range(60):
            s = FORMATS[name]["make"](rnd, used)
            v = s.get("variant") or s.get("kind") or s.get("target")
            if not specs or v != (specs[0].get("variant") or specs[0].get("kind") or specs[0].get("target")):
                specs.append(s)
            if len(specs) == 2:
                break
        times = [0.3, 0.3 + 0.22 * specs[0]["dur"], 0.5 * specs[0]["dur"], 0.72 * specs[0]["dur"],
                 0.86 * specs[0]["dur"], specs[0]["dur"] - 0.2]
        sheet = Image.new("RGB", (270 * len(times), 480 * len(specs)))
        for r, sp in enumerate(specs):
            if hasattr(nv, "set_theme"):
                nv.set_theme(fi * 2 + r)
            for i, tt in enumerate(times):
                sheet.paste(_frame(sp, tt).resize((270, 480)), (i * 270, r * 480))
        sheet.save(f"out/fb_{name}.png")
        print(name, [s["key"] for s in specs])
