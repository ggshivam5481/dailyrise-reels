"""Formats B: tiers (95/4/1%), stack (LATER piles up / good habits tower), failstairs (FAIL -> SUCCESS),
kills (X KILLS Y list). Each format: make(rnd, used) -> spec, draw(c, t, spec), events(spec)."""
import math

import nv
from nv import FLOOR, GOLD, GOLD2, GREY, RED, SUB, WHITE, W, clamp, ease, lerp, mix

GREEN = (128, 214, 140)
DARK = (20, 20, 20)


def _pick_key(rnd, used, build, tries=400):
    for _ in range(tries):
        key, spec = build()
        if key not in used:
            used.add(key)
            spec["key"] = key
            return spec
    raise RuntimeError("script bank exhausted")


def _spot_at(c, x, floor_y, width=170, height=300, strength=0.8):
    m = nv._cone(width, height)
    if strength < 1:
        m = m.point(lambda v: int(v * strength))
    c.img.paste((255, 255, 255), (int(x - width), int(floor_y - height)), m)


# =====================================================================
# 1. TIERS
# =====================================================================
TIER_SETS = [("95%", "4%", "1%"), ("90%", "9%", "1%"), ("97%", "2%", "1%"), ("80%", "19%", "1%")]
TIER_TARGETS = ["hoop", "goal", "bullseye", "bell"]
TIER_GOALS = ["DREAM", "GOAL", "6 PACK", "FIRST 1 LAKH", "PROMOTION", "FLUENT ENGLISH", "OWN BUSINESS",
              "DREAM JOB", "100 FOLLOWERS", "FIRST CLIENT", "NEW HABIT", "TOP RANK", "MARATHON", "FREEDOM"]
TIER_SCRIPTS = [
    ("WHERE ARE YOU?", "THE 1% JUST DIDN'T STOP.", "Most people quit at the first miss. The 1% keep missing until they don't.",
     "Miss hona normal hai. Rukna nahi."),
    ("WHICH ONE ARE YOU?", "MISSES ARE PART OF THE SHOT.", "Missing is not failing. Stopping is.",
     "Galti se mat daro, rukne se daro."),
    ("SAME GOAL. DIFFERENT PEOPLE.", "ONLY ONE KEPT SHOOTING.", "Everyone wants the result. Few accept the misses before it.",
     "Sab ko result chahiye, misses koi nahi chahta."),
    ("MOST PEOPLE NEVER EVEN TRY.", "TRYING AGAIN IS THE SKILL.", "The real skill is the attempt after the failure.",
     "Asli talent hai dobara try karna."),
    ("TALENT IS NOT THE DIFFERENCE.", "ATTEMPTS ARE.", "Talent decides where you start. Attempts decide where you end.",
     "Talent start deta hai, attempts finish dete hain."),
    ("ONE MISS STOPS MOST PEOPLE.", "SEVEN MISSES MADE ONE WINNER.", "Your seventh try is someone else's first excuse.",
     "Jahan log rukte hain, wahin se jeet shuru hoti hai."),
    ("EVERYONE HAS THE SAME SHOT.", "NOT EVERYONE TAKES IT AGAIN.", "Opportunity is equal. Persistence is not.",
     "Mauka sabko milta hai, himmat sabme nahi."),
    ("BE HONEST. WHICH ROW?", "THE GOAL NEVER MOVED.", "The goal stays where it is. Only quitters move away from it.",
     "Goal wahi hai. Tum kahan ho?"),
    ("THIS IS WHY 1% WIN.", "THEY TREAT MISSES AS DATA.", "Every miss tells you how to aim the next one.",
     "Har miss agla shot better banata hai."),
    ("DON'T BE THE 95%.", "KEEP SHOOTING.", "Comfort sits. Fear tries once. Discipline keeps going.",
     "Baithna aasaan hai, lagatar try karna rare hai."),
    ("THE DIFFERENCE IS SIMPLE.", "THEY DIDN'T QUIT.", "Success is mostly refusing to stop.", "Bas rukna mat."),
    ("SAME CHANCE. 3 OUTCOMES.", "YOUR NEXT TRY DECIDES.", "You are always one attempt away from a different row.",
     "Agla try tumhari row badal sakta hai."),
    ("FAILURE IS NOT THE END.", "QUITTING IS.", "Failure is a step. Quitting is a wall.", "Fail hona step hai, quit karna deewar."),
    ("WHO GETS THE GOAL?", "THE ONE WHO MISSED THE MOST.", "The winner usually has the most misses.",
     "Jeetne wale ke paas sabse zyada misses hote hain."),
    ("NOBODY SEES THE MISSES.", "THEY ONLY SEE THE GOAL.", "People clap for the goal, never for the misses behind it.",
     "Log goal dekhte hain, uske peeche ke misses nahi."),
    ("ARE YOU STILL TRYING?", "THE 1% IS A DECISION.", "The 1% is not a talent group. It is a decision group.",
     "1% banna ek decision hai."),
]
TIER_ROWS = [720, 980, FLOOR]
TIER_FIG_X, TIER_TX = 230, 860
TIER_ATT0, TIER_GAP, TIER_FLY, TIER_N = 0.7, 0.95, 0.6, 7


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
            "bullseye": (TIER_TX, floor_y - 120), "bell": (TIER_TX, floor_y - 150)}[kind]


def _draw_target(c, kind, floor_y, lit):
    d = c.d
    col = GOLD if lit else (190, 190, 194)
    if kind == "hoop":
        d.line([(TIER_TX + 30, floor_y), (TIER_TX + 30, floor_y - 200)], fill=(70, 70, 74), width=8)
        d.rectangle([TIER_TX + 8, floor_y - 215, TIER_TX + 34, floor_y - 140], fill=(60, 60, 64))
        d.ellipse([TIER_TX - 70, floor_y - 160, TIER_TX + 2, floor_y - 140], outline=col, width=6)
    elif kind == "goal":
        d.line([(TIER_TX - 70, floor_y), (TIER_TX - 70, floor_y - 120), (TIER_TX + 70, floor_y - 120),
                (TIER_TX + 70, floor_y)], fill=col, width=7)
    elif kind == "bullseye":
        d.line([(TIER_TX, floor_y), (TIER_TX, floor_y - 70)], fill=(70, 70, 74), width=8)
        for r, cc in ((52, col), (36, (30, 30, 32)), (20, col)):
            d.ellipse([TIER_TX - r, floor_y - 120 - r, TIER_TX + r, floor_y - 120 + r], fill=cc)
    else:  # bell on a post
        d.line([(TIER_TX + 40, floor_y), (TIER_TX + 40, floor_y - 200), (TIER_TX, floor_y - 200)],
               fill=(70, 70, 74), width=8)
        d.polygon([(TIER_TX - 30, floor_y - 125), (TIER_TX - 20, floor_y - 180), (TIER_TX + 20, floor_y - 180),
                   (TIER_TX + 30, floor_y - 125)], fill=col)
        d.ellipse([TIER_TX - 8, floor_y - 130, TIER_TX + 8, floor_y - 114], fill=col)


def _ball(c, t, t0, floor_y, end, miss_dir):
    """Ball thrown at t0. Returns landed state."""
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
    c.d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=WHITE)
    return u > 1


def tiers_draw(c, t, spec):
    d = c.d
    tset, kind = spec["tiers"], spec["target"]
    for ri, fy in enumerate(TIER_ROWS):
        if fy != FLOOR:
            d.line([(40, fy), (W - 40, fy)], fill=(34, 34, 37), width=2)
        _spot_at(c, TIER_FIG_X, fy, 150, 230, 0.7)
        c.text(f"{tset[ri]} OF PEOPLE", 60, fy - 236, 22, WHITE, align="left")
        tc = _target_center(kind, fy)
        lit = False
        if ri == 0:
            c.text("NEVER TRIED", 60, fy - 204, 16, SUB, align="left")
            c.figure(TIER_FIG_X, nv.phone(t), s=0.6, col=GREY, foot_y=fy)
        elif ri == 1:
            t0 = TIER_ATT0 + 0.2
            landed = _ball(c, t, t0, fy, tc, spec["miss"][0])
            c.text("TRIED ONCE", 60, fy - 204, 16, SUB, align="left")
            if landed:
                c.text("X", 330, fy - 206, 20, RED)
            pose = nv.sad(t) if t > t0 + TIER_FLY + 0.6 else (
                dict(nv.BASE, ra1=150, ra2=10) if t0 - 0.25 < t < t0 + 0.2 else nv.stand(t))
            c.figure(TIER_FIG_X, pose, s=0.6, col=GREY if t > t0 + TIER_FLY + 0.6 else WHITE, foot_y=fy)
        else:
            n_att = 0
            misses = 0
            throwing = False
            for k in range(TIER_N):
                t0 = TIER_ATT0 + k * TIER_GAP
                if t >= t0 - 0.25:
                    n_att = k + 1
                if t0 - 0.25 < t < t0 + 0.2:
                    throwing = True
                if t0 <= t < t0 + TIER_FLY + 0.45:
                    md = spec["miss"][k] if k < TIER_N - 1 else 0
                    landed = _ball(c, t, t0, fy, tc, md)
                    if landed and md == 0:
                        lit = True
                if k < TIER_N - 1 and t >= t0 + TIER_FLY:
                    misses += 1
                if k == TIER_N - 1 and t >= t0 + TIER_FLY:
                    lit = True
            c.text(f"ATTEMPT {max(1, n_att)}", 60, fy - 204, 16, GOLD if lit else SUB, align="left")
            for i in range(misses):
                c.text("X", 330 + i * 34, fy - 206, 20, RED)
            if lit:
                c.figure(TIER_FIG_X, nv.celebrate(t), s=0.6, foot_y=fy)
            else:
                pose = dict(nv.BASE, ra1=150, ra2=10) if throwing else nv.stand(t)
                c.figure(TIER_FIG_X, pose, s=0.6, foot_y=fy)
        if lit:
            c.glow(tc[0], tc[1], 60, GOLD, 0.7)
        _draw_target(c, kind, fy, lit)
        c.text(spec["goal"], TIER_TX, fy - 236, 18, GOLD if lit else SUB)


def tiers_events(spec):
    ev = [(TIER_ATT0 + 0.2, "whoosh", 0.2), (TIER_ATT0 + 0.2 + TIER_FLY, "thud", 0.25)]
    for k in range(TIER_N):
        t0 = TIER_ATT0 + k * TIER_GAP
        ev.append((t0, "whoosh", 0.18))
        if k < TIER_N - 1:
            ev.append((t0 + TIER_FLY, "thud", 0.22))
    win = TIER_ATT0 + (TIER_N - 1) * TIER_GAP + TIER_FLY
    ev += [(win, "chime", 0.5), (win, "flash", 0.35)]
    return ev


# =====================================================================
# 2. STACK
# =====================================================================
STACK_NEG_WORDS = ["LATER", "TOMORROW", "SNOOZE", "EXCUSE", "NEXT MONDAY", "JUST 5 MIN", "ONE MORE EPISODE",
                   "NOT TODAY", "MAYBE", "SKIP", "I'M TIRED", "AFTER THIS", "NEW YEAR", "SCROLL"]
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
]
STACK_COUNTERS = ["clock", "day", "age"]
STACK_N = 8
STACK_T0, STACK_GAP, STACK_FALL = 0.6, 0.85, 0.32
BOX_W, BOX_H = 300, 74


def stack_make(rnd, used):
    def build():
        pos = rnd.random() < 0.45
        bank, words = (STACK_POS, STACK_POS_WORDS) if pos else (STACK_NEG, STACK_NEG_WORDS)
        si = rnd.randrange(len(bank))
        top, punch, cap, ig = bank[si]
        counter = "day" if pos else rnd.choice(STACK_COUNTERS)
        if pos:
            labels = rnd.sample(words, STACK_N)
            word = "mix"
        else:
            word = rnd.choice(words)
            labels = [word] * STACK_N
        key = f"stack|{'pos' if pos else 'neg'}|{si}|{word if not pos else '/'.join(labels[:3])}|{counter}"
        return key, dict(format="stack", dur=10.0, top=top, punch=punch, punch_at=0.72, caption_line=cap, ig=ig,
                         topic="habits" if pos else "discipline", positive=pos, labels=labels, counter=counter,
                         start=rnd.choice((7, 8, 9)) if counter == "clock" else rnd.choice((18, 20, 22)))
    return _pick_key(rnd, used, build)


def _stack_slots(pos):
    """Resting rectangle (x0, y0) for each box."""
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
            slots.append((xs[col] - (0 if col != 2 else 0) + (i // 3) * 4, y))
    return slots


def _counter_text(spec, n):
    if spec["counter"] == "clock":
        h = spec["start"] + n * 1
        ampm = "AM" if h % 24 < 12 else "PM"
        hh = h % 12 or 12
        return f"{hh}:00 {ampm}"
    if spec["counter"] == "age":
        return f"AGE {spec['start'] + n * 3}"
    days = [1, 3, 7, 14, 30, 60, 100, 180, 365]
    return f"DAY {days[min(n, len(days) - 1)]}"


def stack_draw(c, t, spec):
    pos = spec["positive"]
    slots = _stack_slots(pos)
    landed = sum(1 for i in range(STACK_N) if t >= STACK_T0 + i * STACK_GAP + STACK_FALL)
    done = landed >= STACK_N
    fig_x = 400 if pos else 540
    c.spot(fig_x, 300, strength=0.9)
    if pos:
        c.spot(790, 260, strength=0.6)
    # counter
    ctr = _counter_text(spec, landed)
    warn = (not pos) and landed >= STACK_N - 2
    c.text(ctr, W / 2, 440, 64, RED if warn else (GOLD if pos and done else WHITE))
    # figure (drawn first so boxes can bury him)
    if pos:
        held = None
        for i in range(STACK_N):
            t0 = STACK_T0 + i * STACK_GAP
            if t0 - 0.5 * STACK_GAP <= t < t0:
                held = spec["labels"][i]
        if done:
            pose = nv.celebrate(t)
        elif held:
            pose = nv.carry_up(t)
        else:
            pose = nv.stand(t)
        info = c.figure(fig_x, pose)
        if held and not done:
            hx = (info["hands"]["l"][0] + info["hands"]["r"][0]) / 2
            hy = min(info["hands"]["l"][1], info["hands"]["r"][1])
            c.block(hx - 90, hy - 46, hx + 90, hy, (182, 182, 188), held, 14, (8, 8, 8))
    else:
        k = landed / STACK_N
        pose = nv.sad(t) if k > 0.4 else nv.stand(t)
        c.figure(fig_x, pose, col=mix(WHITE, GREY, k))
    # boxes
    for i in range(STACK_N):
        t0 = STACK_T0 + i * STACK_GAP
        if t < t0:
            continue
        x0, y1 = slots[i]
        u = clamp((t - t0) / STACK_FALL)
        y = lerp(y1 - (420 if pos else 700), y1, u * u)
        if pos:
            col = GOLD if done and i == STACK_N - 1 else (182, 182, 188)
        else:
            col = (176, 176, 182)
        label = spec["labels"][i]
        px = 18 if len(label) <= 12 else 16
        c.block(x0, y, x0 + BOX_W, y + BOX_H, col, label, px, (8, 8, 8))
    if pos and done:
        tx = slots[-1][0] + BOX_W / 2
        c.glow(tx, slots[-1][1] - 20, 120, GOLD, 0.75)
        c.spot(tx, 260, color=GOLD2, strength=0.8)


def stack_events(spec):
    ev = []
    for i in range(STACK_N):
        tl = STACK_T0 + i * STACK_GAP + STACK_FALL
        ev.append((tl, "thud", 0.28 + 0.03 * i))
        ev.append((tl, "pop", 0.1))
    end = STACK_T0 + (STACK_N - 1) * STACK_GAP + STACK_FALL
    if spec["positive"]:
        ev += [(end, "chime", 0.45), (end + 0.05, "flash", 0.35)]
    else:
        ev += [(end, "heartbeat", 0.4), (end - 1.2, "rumble", 0.25)]
    return ev


# =====================================================================
# 3. FAILSTAIRS
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
]
FAIL_TOPS = ["SUCCESS", "WIN", "DREAM", "GOAL", "FREEDOM", "RESULT"]
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
]
FS_N = 7
FS_SW, FS_SH, FS_X0 = 128, 70, 110


def failstairs_make(rnd, used):
    def build():
        si = rnd.randrange(len(FAIL_SCRIPTS))
        top, punch, cap, ig = FAIL_SCRIPTS[si]
        li = rnd.randrange(len(FAIL_SETS))
        goal = rnd.choice(FAIL_TOPS)
        key = f"failstairs|{si}|{li}|{goal}"
        return key, dict(format="failstairs", dur=10.0, top=top, punch=punch, punch_at=0.76, caption_line=cap,
                         ig=ig, topic="growth", labels=FAIL_SETS[li] + [goal], goal=goal)
    return _pick_key(rnd, used, build)


def failstairs_draw(c, t, spec):
    dur = spec["dur"]
    climb = dur * 0.72
    k = clamp(t / climb) * (FS_N - 0.5)
    step = int(k)
    frac = k - step
    won = t >= climb
    c.spot(FS_X0 + (FS_N - 1) * FS_SW + FS_SW / 2, 300, color=GOLD2 if won else (255, 255, 255),
           strength=0.9 if won else 0.45)
    c.spot(FS_X0 + 60 + k * FS_SW, 260, strength=0.7)
    for i, lab in enumerate(spec["labels"]):
        x0 = FS_X0 + i * FS_SW
        y0 = FLOOR - (i + 1) * FS_SH
        last = i == FS_N - 1
        col = GOLD if (last and won) else ((92, 92, 98) if last else (58, 58, 64))
        c.block(x0, y0, x0 + FS_SW - 6, FLOOR, col)
        c.d.line([(x0, y0), (x0 + FS_SW - 8, y0)], fill=(150, 150, 156) if not (last and won) else GOLD2, width=3)
        px = 16 if len(lab) <= 7 else 14
        c.text(lab, x0 + (FS_SW - 6) / 2, y0 + 18, px, (40, 30, 0) if (last and won) else (200, 200, 204),
               world=True)
    if won:
        gx = FS_X0 + (FS_N - 1) * FS_SW + FS_SW / 2
        c.glow(gx, FLOOR - FS_N * FS_SH - 40, 140, GOLD, 0.8)
    x = FS_X0 + 56 + k * FS_SW
    floor = FLOOR - step * FS_SH - (FS_SH * ease((frac - 0.5) * 2) if frac > 0.5 else 0)
    if won:
        c.figure(FS_X0 + (FS_N - 1) * FS_SW + 58, nv.celebrate(t), s=0.85, foot_y=FLOOR - FS_N * FS_SH)
    else:
        c.figure(x, nv.walk(t, 8, 26), s=0.85, foot_y=floor)
    att = min(FS_N, step + 1)
    c.text(f"ATTEMPT {att}", 300, 620, 34, GOLD if won else SUB)


def failstairs_events(spec):
    climb = spec["dur"] * 0.72
    ev = [((i + 0.5) / (FS_N - 0.5) * climb, "step", 0.3) for i in range(FS_N)]
    ev += [((i + 0.5) / (FS_N - 0.5) * climb, "pop", 0.12) for i in range(FS_N)]
    ev += [(climb - 0.6, "swell", 0.3), (climb, "chime", 0.5), (climb, "flash", 0.4)]
    return ev


# =====================================================================
# 4. KILLS
# =====================================================================
KILL_PAIRS = [("LAZINESS", "AMBITION"), ("PHONE", "FOCUS"), ("FEAR", "DREAMS"), ("COMFORT", "GROWTH"),
              ("DOUBT", "ACTION"), ("EGO", "LEARNING"), ("EXCUSES", "RESULTS"), ("OVERTHINKING", "PEACE"),
              ("COMPARISON", "JOY"), ("SUGAR", "ENERGY"), ("SCROLLING", "TIME"), ("ANGER", "WISDOM"),
              ("WAITING", "CHANCES"), ("GOSSIP", "TRUST"), ("SNOOZE", "MORNINGS"), ("DEBT", "FREEDOM"),
              ("PERFECTION", "PROGRESS"), ("BLAME", "GROWTH"), ("ENVY", "PEACE"), ("NOISE", "CLARITY"),
              ("REGRET", "TODAY"), ("LATE NIGHTS", "MORNINGS"), ("SHORTCUTS", "SKILL"), ("COMPLAINING", "ENERGY")]
BUILD_PAIRS = [("DISCIPLINE", "FREEDOM"), ("READING", "WISDOM"), ("SILENCE", "CLARITY"), ("SAVING", "SECURITY"),
               ("SLEEP", "ENERGY"), ("PRACTICE", "SKILL"), ("PATIENCE", "WEALTH"), ("GRATITUDE", "PEACE"),
               ("WALKING", "HEALTH"), ("FOCUS", "RESULTS"), ("HONESTY", "TRUST"), ("ROUTINE", "MOMENTUM"),
               ("LISTENING", "RESPECT"), ("CONSISTENCY", "CONFIDENCE"), ("EFFORT", "LUCK"), ("CALM", "DECISIONS")]
KILL_SCRIPTS = [
    ("WHAT IS KILLING YOUR DREAMS?", None, "Most dreams don't die in one blow. They die of small daily habits.",
     "Sapne ek din mein nahi marte."),
    ("READ THIS TWICE.", None, "Read the list again. Circle the one you need to fix today.",
     "Is list ko do baar padho."),
    ("SILENT KILLERS.", None, "The most dangerous habits are the quiet ones.", "Sabse khatarnak aadatein chupchaap hoti hain."),
    ("CHOOSE WHAT YOU FEED.", None, "Whatever you feed daily is what grows.", "Jo roz khilaoge, wahi badhega."),
    ("WHICH ONE IS YOURS?", None, "Be honest. Which one is stealing from you?", "Sach bolo, tumhara kaun sa hai?"),
    ("SAVE THIS LIST.", None, "Save it. Read it when you feel stuck.", "Save karo, atko to padhna."),
]
BUILD_SCRIPTS = [
    ("WHAT BUILDS A STRONG LIFE?", None, "A strong life is built from boring, repeated choices.",
     "Strong life boring choices se banti hai."),
    ("THE QUIET BUILDERS.", None, "The habits that build you rarely feel exciting.", "Jo aadatein banati hain, wo shor nahi karti."),
    ("BUILD THESE. DAILY.", None, "Pick one. Do it today. Repeat tomorrow.", "Ek chuno, aaj karo, kal phir."),
    ("SAVE THIS. BUILD THIS.", None, "Small habits, built daily, become who you are.", "Chhoti aadatein, roz, tum ban jaati hain."),
]
KILL_ACTIONS = ["walk", "run"]  # pushup/sit poses read poorly at this scale
KILL_T0, KILL_GAP = 0.5, 0.8


def kills_make(rnd, used):
    def build():
        pos = rnd.random() < 0.35
        pairs = rnd.sample(BUILD_PAIRS if pos else KILL_PAIRS, 6)
        si = rnd.randrange(len(BUILD_SCRIPTS if pos else KILL_SCRIPTS))
        top, punch, cap, ig = (BUILD_SCRIPTS if pos else KILL_SCRIPTS)[si]
        action = rnd.choice(KILL_ACTIONS)
        key = f"kills|{'b' if pos else 'k'}|{'/'.join(a for a, _ in pairs)}"
        return key, dict(format="kills", dur=7.5, top=top, punch=punch, punch_at=0.9, caption_line=cap, ig=ig,
                         topic="habits" if pos else "mindset", positive=pos, pairs=pairs, action=action,
                         verb="BUILDS" if pos else "KILLS")
    return _pick_key(rnd, used, build)


def kills_draw(c, t, spec):
    px, gap = 30, 64
    y0 = 560
    a_col = GREEN if spec["positive"] else RED
    b_col = GOLD if spec["positive"] else GREEN
    verb = spec["verb"]
    for i, (a, b) in enumerate(spec["pairs"]):
        ti = KILL_T0 + i * KILL_GAP
        if t < ti:
            break
        parts = [(a, a_col), (verb, WHITE), (b, b_col)]
        masks = [nv.text_mask(p, px) for p, _ in parts]
        sp = 26
        total = sum(m.width for m in masks) + sp * 2
        x = W / 2 - total / 2
        y = y0 + i * gap
        for (p, col), m in zip(parts, masks):
            c.text(p, x, y, px, col, align="left")
            x += m.width + sp
    c.spot(540, 300, strength=0.8)
    act = spec["action"]
    if act == "pushup":
        c.figure(560, nv.pushup(t, 6.0), s=0.85)
    elif act == "walk":
        c.figure(540, nv.walk(t, 7, 22), s=0.85)
    elif act == "run":
        c.figure(540, nv.run(t), s=0.85)
    else:
        c.figure(500, nv.sit(t), s=0.85)
        c.block(560, FLOOR - 190, 650, FLOOR - 120, (230, 230, 232))


def kills_events(spec):
    ev = [(KILL_T0 + i * KILL_GAP, "pop", 0.18) for i in range(6)]
    ev.append((KILL_T0 + 5 * KILL_GAP + 0.3, "swell", 0.25))
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
    fmt["draw"](c, t, spec)
    y = nv.TOP_Y
    if spec.get("top"):
        y = c.lines(spec["top"], W / 2, y, 30)
    if spec.get("punch") and t >= spec.get("punch_at", 0.66) * spec["dur"]:
        c.lines(spec["punch"], W / 2, y + nv.PUNCH_GAP, 30, GOLD)
    return nv.watermark(c.finish(t), t)


if __name__ == "__main__":
    import os
    import random
    import sys

    from PIL import Image
    os.makedirs("out", exist_ok=True)
    rnd = random.Random(5)
    used = set()
    only = sys.argv[1:] or list(FORMATS)
    for name in only:
        specs = [FORMATS[name]["make"](rnd, used) for _ in range(2)]
        times = [0.3, 0.3 + 0.22 * specs[0]["dur"], 0.5 * specs[0]["dur"], 0.72 * specs[0]["dur"],
                 0.86 * specs[0]["dur"], specs[0]["dur"] - 0.2]
        sheet = Image.new("RGB", (270 * len(times), 480 * 2))
        for r, sp in enumerate(specs):
            for i, tt in enumerate(times):
                sheet.paste(_frame(sp, tt).resize((270, 480)), (i * 270, r * 480))
        sheet.save(f"out/fb_{name}.png")
        print(name, [s["key"] for s in specs])
    if "--video" in sys.argv or not sys.argv[1:]:
        sp = stack_make(rnd, used)
        nv.render(sp, stack_draw, stack_events(sp), "out/fb_stack.mp4", seed=4)
        print("video ok", sp["key"])
