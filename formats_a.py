"""Formats A: "duel" (two labelled people, opposite choices, one wins) and "split" (two stacked panels
with a shared ticking counter). Drawn through the nv.Canvas API."""
import math
import random

from PIL import Image, ImageDraw

import nv
from nv import (BG, BLOCK, FLOOR, GOLD, GOLD2, GREY, H, RED, SUB, W, WHITE, Canvas, carry_up, celebrate, clamp,
                ease, lerp, mirror, sad, sit, stand, walk)

LABEL_Y = int(0.26 * H)  # 499


# ---------------- small helpers ----------------
def _pose(P, flip):
    return mirror(P) if flip else P


def _X(spec, x):
    return W - x if spec.get("flip") else x


def _label(c, name, cx, y, sub=None, sub_color=SUB, color=WHITE, px=26):
    c.text(name, cx, y, px, color)
    if sub:
        c.text(sub, cx, y + px * 1.5, int(px * 0.72), sub_color)


def _spot_at(c, x, floor_y, height=520, width=260, strength=0.8, color=(255, 255, 255)):
    m = nv._cone(width, height)
    if strength < 1:
        m = m.point(lambda v: int(v * strength))
    c.img.paste(color, (int(x - width), int(floor_y - height)), m)


def _hammer(c, hand, ang, length=60, col=(200, 200, 204)):
    tip = nv.pt(hand, ang, length)
    c.d.line([hand, tip], fill=col, width=7)
    hx, hy = tip
    c.d.rectangle([hx - 16, hy - 8, hx + 16, hy + 8], fill=col)


def _sit_phone(t):
    return dict(sit(t), la1=120, la2=70, ra1=130, ra2=60, head=-25)


def _phone_glow(c, info, flip=False):
    hx, hy = info["hands"]["l"]
    c.d.rounded_rectangle([hx - 10, hy - 20, hx + 10, hy + 6], 4, fill=(200, 222, 255))
    c.glow(hx, hy - 8, 26, (170, 200, 255), 0.35)


# ---------------- DUEL scripts ----------------
# (label_a passive, label_b doer, variant, top, punch, caption_line, ig, topic, unit_a, unit_b)
DUEL = [
    ("PERFECTIONIST", "ACTION TAKER", "stack", "PERFECT IS A SLOW WAY TO START.", "DONE BEATS PERFECT.",
     "Perfect is the enemy of finished.", "Perfect ka wait mat karo, shuru karo.", "mindset", "BRICK", "BRICK"),
    ("OVERTHINKER", "DOER", "stack", "ONE THINKS. ONE BUILDS.", "ACTION KILLS DOUBT.",
     "You can't think your way out of something you acted your way into.",
     "Sochte raho ya banate raho, choice tumhari.", "mindset", "PLAN", "STEP"),
    ("DREAMER", "BUILDER", "stack", "SAME DREAM. DIFFERENT HABIT.", "DREAMS NEED BRICKS.",
     "A dream without daily bricks is just a wish.", "Sapne tab bante hain jab roz eent lagti hai.",
     "habits", "IDEA", "BRICK"),
    ("WAITER", "STARTER", "stack", "WAITING FOR THE RIGHT TIME?", "THE RIGHT TIME WAS DAY ONE.",
     "The perfect moment is a myth. Start ugly.", "Sahi waqt kabhi nahi aata, banana padta hai.", "time",
     "DAY", "DAY"),
    ("COMPLAINER", "LEARNER", "stack", "ONE BLAMES. ONE LEARNS.", "LESSONS STACK UP.",
     "Complaints don't compound. Lessons do.", "Shikayat se kuch nahi banta, seekhne se banta hai.",
     "growth", "EXCUSE", "LESSON"),
    ("SCROLLER", "CREATOR", "stack", "SAME PHONE. DIFFERENT USE.", "CREATE MORE THAN YOU CONSUME.",
     "Consume less. Create more. Watch your life change.", "Scroll kam, create zyada.", "focus",
     "REEL", "POST"),
    ("TALKER", "WALKER", "stack", "TALK IS CHEAP.", "WORK SPEAKS LOUDER.",
     "Stop announcing. Start building.", "Batein kam, kaam zyada.", "discipline", "TALK", "WORK"),
    ("PLANNER", "STARTER", "stack", "THE PLAN LOOKED PERFECT.", "THE STARTER GOT THERE.",
     "A messy start beats a perfect plan that never moves.", "Plan se zyada zaroori hai pehla kadam.",
     "mindset", "PLAN", "STEP"),
    ("SPENDER", "SAVER", "stack", "SMALL AMOUNTS. BIG GAP.", "SAVINGS BUILD FREEDOM.",
     "Every rupee saved is a brick of freedom.", "Chhoti bachat, badi azaadi.", "money", "SPENT", "SAVED"),
    ("MOTIVATED", "DISCIPLINED", "stack", "MOTIVATION FADES.", "DISCIPLINE STAYS.",
     "Motivation gets you started. Discipline keeps you going.",
     "Motivation chali jaati hai, discipline rehta hai.", "discipline", "MOOD", "DAY"),
    ("STARTER", "FINISHER", "stack", "EVERYONE STARTS.", "FEW FINISH.",
     "Starting is easy. Finishing is rare.", "Shuru sab karte hain, khatam kuch log.", "discipline",
     "DAY", "DAY"),
    ("QUITTER", "FINISHER", "dig", "IT WAS RIGHT THERE.", "ONE MORE SWING.",
     "Most people quit one step before the breakthrough.", "Haar maanne se pehle ek baar aur try karo.",
     "growth", "DEPTH", "DEPTH"),
    ("DOUBTER", "BELIEVER", "dig", "HE STOPPED AT 5 METERS.", "GOLD WAS AT 6.",
     "You never know how close you are.", "Tumhe nahi pata tum kitne kareeb ho.", "mindset",
     "DEPTH", "DEPTH"),
    ("TIRED", "CONSISTENT", "dig", "TIRED IS NOT A REASON.", "CONSISTENCY STRIKES GOLD.",
     "Consistency is boring until it pays.", "Consistency boring lagti hai, jab tak result na aaye.",
     "habits", "DAY", "DAY"),
    ("IMPATIENT", "PATIENT", "dig", "RESULTS TAKE TIME.", "PATIENCE PAYS IN GOLD.",
     "Patience is cheaper than regret.", "Sabr rakho, result zaroor aayega.", "growth", "WEEK", "WEEK"),
    ("SHORTCUT", "SLOW WORK", "dig", "LOOKING FOR A SHORTCUT?", "THERE ISN'T ONE.",
     "The shortcut is doing the long work.", "Shortcut nahi hai, mehnat hi rasta hai.", "discipline",
     "TRY", "TRY"),
    ("GAVE UP", "KEPT GOING", "dig", "ALMOST IS NOT ENOUGH.", "KEEP DIGGING.",
     "Almost doesn't count. Keep going.", "Lagbhag se kaam nahi chalta, lage raho.", "growth",
     "ATTEMPT", "ATTEMPT"),
    ("COMFORT", "GROWTH", "dig", "COMFORT STOPS EARLY.", "GROWTH DIGS DEEPER.",
     "Comfort is a loan. Future you pays the interest.", "Comfort aaj accha lagta hai, kal mehenga padta hai.",
     "growth", "DEPTH", "DEPTH"),
    ("EXCUSES", "EFFORT", "dig", "EXCUSES SOUND REASONABLE.", "EFFORT FINDS GOLD.",
     "Excuses are comfortable. Results are not.", "Bahane aasaan hain, result mehnat se aata hai.",
     "discipline", "DEPTH", "DEPTH"),
    ("SCROLLER", "CLIMBER", "climb", "THE LADDER WAS ALWAYS THERE.", "CLIMB IT DAILY.",
     "Your phone won't climb the ladder for you.", "Phone neeche rakho, seedhi chadho.", "focus",
     "SCROLL", "STEP"),
    ("WAITER", "CLIMBER", "climb", "WAITING FOR AN ELEVATOR?", "TAKE THE STAIRS.",
     "Nobody is coming to lift you. Climb.", "Koi utha ke nahi le jayega, khud chadho.", "mindset",
     "WAIT", "STEP"),
    ("BINGE", "BUILD", "climb", "SAME NIGHT. DIFFERENT CHOICE.", "NIGHTS BUILD FUTURES.",
     "Your evenings decide your future.", "Raat ka time hi future banata hai.", "time", "EPISODE", "STEP"),
    ("BUSY", "PRODUCTIVE", "climb", "BUSY IS NOT PRODUCTIVE.", "MOVE UP, NOT AROUND.",
     "Being busy is not the same as moving forward.", "Busy rehna aur aage badhna alag hai.", "focus",
     "TASK", "STEP"),
    ("SPECTATOR", "PLAYER", "climb", "WATCHING IS EASY.", "PLAYERS GO HIGHER.",
     "Stop watching other people live your dream.", "Doosron ko dekhna band, khud khelo.", "growth",
     "WATCH", "STEP"),
    ("CONSUMER", "LEARNER", "climb", "ONE WATCHES. ONE LEARNS.", "SKILLS ARE THE LADDER.",
     "Skills are the only ladder that never breaks.", "Skill hi asli seedhi hai.", "growth", "VIDEO", "SKILL"),
    ("PROCRASTINATOR", "EARLY RISER", "climb", "TOMORROW NEVER COMES.", "TODAY IS THE LADDER.",
     "Tomorrow is where dreams go to die.", "Kal kabhi nahi aata, aaj se shuru karo.", "time",
     "TOMORROW", "STEP"),
    ("COMPARER", "FOCUSED", "climb", "EYES ON OTHERS?", "EYES ON YOUR LADDER.",
     "Compare less. Climb more.", "Doosron se compare kam, apni seedhi pe dhyan.", "focus", "COMPARE", "STEP"),
    ("SCARED", "BRAVE", "climb", "FEAR SAYS STAY DOWN.", "BRAVE SAYS ONE MORE STEP.",
     "Courage is fear that kept climbing.", "Darr ke saath bhi chadhte raho.", "fear", "FEAR", "STEP"),
    ("LAZY", "CONSISTENT", "stack", "TALENT IS NOT ENOUGH.", "CONSISTENCY WINS.",
     "Consistency beats talent when talent sleeps.", "Talent se zyada consistency jeetti hai.", "habits",
     "DAY", "DAY"),
    ("FIXED MIND", "GROWTH MIND", "stack", "I CAN'T VS I CAN'T YET.", "YET CHANGES EVERYTHING.",
     "Add one word: yet.", "Abhi nahi aata, par seekh lunga.", "mindset", "TRY", "TRY"),
    ("EXCUSE MAKER", "RESULT MAKER", "climb", "REASONS OR RESULTS.", "YOU CAN'T HAVE BOTH.",
     "You can have reasons or results, not both.", "Bahane ya result, dono nahi milte.", "discipline",
     "REASON", "STEP"),
    ("BROKE MINDSET", "RICH MINDSET", "stack", "SPEND IT OR STACK IT.", "STACK IT.",
     "Rich is a habit before it's a number.", "Ameer banna pehle aadat hai.", "money", "SPENT", "INVEST"),
    ("NIGHT OWL", "EARLY BIRD", "climb", "5 AM FEELS IMPOSSIBLE.", "UNTIL IT DOESN'T.",
     "Win the morning, win the day.", "Subah jeeto, din jeeto.", "habits", "SNOOZE", "STEP"),
    ("NERVOUS", "READY", "dig", "PRACTICE FEELS USELESS.", "UNTIL THE DAY IT COUNTS.",
     "Practice when nobody watches. Win when everyone does.", "Akele practice karo, sabke saamne jeeto.",
     "discipline", "PRACTICE", "PRACTICE"),
    ("ALONE", "TOGETHER", "stack", "ONE BRICK AT A TIME.", "EVERY EMPIRE STARTED HERE.",
     "Every empire started with one brick.", "Har bada kaam ek eent se shuru hota hai.", "growth",
     "BRICK", "BRICK"),
    ("FOLLOWER", "LEADER", "climb", "EVERYONE WAITS FOR SOMEONE.", "BE THE ONE WHO STARTS.",
     "Leaders aren't born. They start first.", "Leader wahi jo pehle shuru kare.", "mindset", "WAIT", "STEP"),
    ("SAFE", "BOLD", "dig", "SAFE FEELS GOOD.", "BOLD FINDS GOLD.",
     "Safe never made anyone great.", "Safe khelne se koi bada nahi bana.", "fear", "DEPTH", "DEPTH"),
]


def make_duel(rnd, used):
    order = list(range(len(DUEL)))
    rnd.shuffle(order)
    for _ in range(4):
        for i in order:
            v = rnd.randrange(10)
            key = f"duel|{i}|{v}"
            if key in used:
                continue
            used.add(key)
            a, b, var, top, punch, cap, ig, topic, ua, ub = DUEL[i]
            dur = 12.0 + (v % 3) * 0.6
            return dict(format="duel", key=key, dur=dur, top=top, punch=punch, punch_at=0.7, caption_line=cap,
                        ig=ig, topic=topic, a=a, b=b, variant=var, ua=ua, ub=ub, flip=v % 2 == 1,
                        n=5 + (v // 2) % 2, start=1 + (v // 4))
    raise RuntimeError("duel scripts exhausted")


# ---------- duel: STACK ----------
BW, BHT = 70, 50


def _draw_stack(c, t, spec):
    dur, n, flip = spec["dur"], spec["n"], spec["flip"]
    win = 0.7 * dur
    build_end, climb_end = 0.5 * dur, 0.68 * dur
    beat = (build_end - 0.4) / n
    sx = 560
    xa = _X(spec, 270)
    bx = _X(spec, sx + n * BW / 2)
    c.spot(xa, 250, strength=0.7)
    c.spot(bx, 330, strength=0.9)
    # B: staircase
    built = 0
    for i in range(n):
        tb = 0.4 + i * beat
        k = ease((t - tb) / 0.3)
        if k <= 0:
            continue
        built = i + 1
        hgt = max(8, (i + 1) * BHT * k)
        x0 = sx + i * BW
        X0, X1 = sorted((_X(spec, x0), _X(spec, x0 + BW - 2)))
        c.block(X0, FLOOR - hgt, X1, FLOOR)
        for j in range(1, i + 1):
            yy = FLOOR - j * BHT
            if FLOOR - hgt < yy:
                c.d.line([(X0, yy), (X1, yy)], fill=(150, 150, 152), width=2)
    # golden door on top of the last column
    dx = _X(spec, sx + (n - 1) * BW + BW / 2)
    dtop = FLOOR - n * BHT
    lit = clamp((t - win) / 0.4)
    if built == n:
        door_col = nv.mix((70, 56, 22), GOLD2, lit)
        c.d.rectangle([dx - 32, dtop - 116, dx + 32, dtop], fill=nv.mix((30, 26, 14), GOLD, lit))
        c.d.rectangle([dx - 26, dtop - 110, dx + 26, dtop], fill=door_col)
        if lit > 0:
            c.glow(dx, dtop - 60, 120, GOLD, 0.55 * lit)
    # B figure
    if t < build_end:
        i = min(n - 1, int((t - 0.4) / beat)) if t > 0.4 else 0
        ph = ((t - 0.4) / beat) % 1 if t > 0.4 else 0
        fx = _X(spec, sx - 70)
        if ph < 0.5:
            P = carry_up(t)
            info = c.figure(fx, _pose(P, flip))
            hx = (info["hands"]["l"][0] + info["hands"]["r"][0]) / 2
            hy = min(info["hands"]["l"][1], info["hands"]["r"][1])
            c.block(hx - 34, hy - 46, hx + 34, hy - 2)
        else:
            c.figure(fx, _pose(nv.bend(t, 0.7), flip))
        sub_b = f"{spec['ub']} {spec['start'] + built * (built + 1) // 2 - 1 + 1}"
    elif t < climb_end:
        k = (t - build_end) / (climb_end - build_end)
        j = min(n - 1, int(k * n))
        fx = _X(spec, sx + j * BW + BW / 2)
        c.figure(fx, _pose(walk(t, 9), flip), foot_y=FLOOR - (j + 1) * BHT)
        sub_b = f"{spec['ub']} {spec['start'] + n * (n + 1) // 2}"
    else:
        c.figure(dx, celebrate(t) if t >= win else stand(t), foot_y=dtop)
        sub_b = "DONE"
    # A: polishing one block forever
    blk = _X(spec, 345)
    B0, B1 = sorted((blk - 36, blk + 36))
    c.block(B0, FLOOR - 46, B1, FLOOR)
    if t < win:
        k = 0.5 + 0.5 * math.sin(t * 5)
        info = c.figure(xa, _pose(nv.bend(t, 0.35 + 0.35 * k), flip), col=GREY)
    else:
        c.figure(xa, _pose(sad(t), flip), col=GREY)
    _label(c, spec["a"], xa, LABEL_Y, f"{spec['ua']} {spec['start']}", color=GREY if t >= win else WHITE)
    _label(c, spec["b"], bx, LABEL_Y, sub_b, sub_color=GOLD if t >= win else SUB)


def _events_stack(spec):
    dur, n = spec["dur"], spec["n"]
    beat = (0.5 * dur - 0.4) / n
    ev = [(0.4 + i * beat + 0.28, "thud", 0.35) for i in range(n)]
    ev += [(0.4 + i * beat + 0.3, "pop", 0.12) for i in range(n)]
    k0, k1 = 0.5 * dur, 0.68 * dur
    ev += [(k0 + (k1 - k0) * j / n, "step", 0.25) for j in range(n)]
    ev += [(0.7 * dur, "flash", 0.5), (0.7 * dur + 0.1, "chime", 0.45)]
    return ev


# ---------- duel: DIG ----------
TOPG, ROW, ROWS = 800, 66, 6


def _dig_depths(t, dur):
    """Rows dug by A (quits at ROWS-1) and B (breaks through at win)."""
    pace = 0.5 * dur / (ROWS - 1)
    a = min(ROWS - 1, int(t / pace))
    b = min(ROWS - 1, int(t / pace))
    if t >= 0.68 * dur:
        b = ROWS
    return a, b


def _draw_dig(c, t, spec):
    dur = spec["dur"]
    win = 0.7 * dur
    xa, xb = _X(spec, 300), _X(spec, 780)
    c.spot(xa, 240, strength=0.6)
    c.spot(xb, 240, strength=0.8)
    da, db = _dig_depths(t, dur)
    # earth
    earth = (34, 34, 37)
    for r in range(ROWS):
        y0 = TOPG + r * ROW
        c.d.rectangle([0, y0, W, y0 + ROW - 3], fill=earth)
    vein_y = TOPG + ROWS * ROW
    c.d.rectangle([0, vein_y, W, FLOOR], fill=(64, 50, 18))
    rnd = random.Random(7)
    for _ in range(40):
        gx, gy = rnd.uniform(0, W), rnd.uniform(vein_y + 4, FLOOR - 6)
        c.d.ellipse([gx - 5, gy - 3, gx + 5, gy + 3], fill=(150, 116, 40))
    # shafts
    for x, d_ in ((xa, da), (xb, db)):
        if d_ > 0:
            bottom = TOPG + min(d_, ROWS) * ROW
            c.d.rectangle([x - 62, TOPG, x + 62, bottom - (3 if d_ < ROWS else 0)], fill=BG)
    lit = clamp((t - win) / 0.4)
    if db >= ROWS:
        c.d.rectangle([xb - 62, vein_y, xb + 62, FLOOR], fill=nv.mix((120, 92, 30), GOLD2, lit))
        c.glow(xb, vein_y + 10, 110, GOLD, 0.6 * lit)
    # figures
    hit = 0.5 + 0.5 * math.sin(t * 9)
    for who, x, d_ in (("a", xa, da), ("b", xb, db)):
        foot = TOPG + min(d_, ROWS) * ROW if d_ < ROWS else vein_y
        quit_ = who == "a" and t > 0.5 * dur
        col = GREY if who == "a" else WHITE
        if who == "b" and t >= win:
            c.figure(x, celebrate(t), foot_y=foot, col=col)
        elif quit_:
            c.figure(x, _pose(sad(t), spec["flip"]), foot_y=foot, col=col)
        else:
            P = dict(nv.BASE, lean=10 + 25 * hit, ra1=150 - 120 * hit, ra2=-20, la1=-20)
            info = c.figure(x, _pose(P, spec["flip"]), foot_y=foot, col=col)
            hand = info["hands"]["r"]
            ang = (150 - 120 * hit) * (-1 if spec["flip"] else 1)
            _hammer(c, hand, ang, 56)
    sa = f"{spec['ua']} {da + spec['start'] - 1}" if t <= 0.5 * dur else f"QUIT AT {da + spec['start'] - 1}"
    sb = f"{spec['ub']} {min(db, ROWS) + spec['start'] - 1}" if t < win else "GOLD"
    _label(c, spec["a"], xa, LABEL_Y, sa, sub_color=RED if t > 0.5 * dur else SUB)
    _label(c, spec["b"], xb, LABEL_Y, sb, sub_color=GOLD if t >= win else SUB)


def _events_dig(spec):
    dur = spec["dur"]
    pace = 0.5 * dur / (ROWS - 1)
    ev = [(i * pace, "thud", 0.3) for i in range(1, ROWS)]
    ev += [(i * pace + 0.02, "pop", 0.12) for i in range(1, ROWS)]
    ev += [(0.5 * dur + 0.1, "heartbeat", 0.35), (0.68 * dur, "thud", 0.45), (0.7 * dur, "flash", 0.5),
           (0.7 * dur + 0.1, "chime", 0.45)]
    return ev


# ---------- duel: CLIMB ----------
LTOP, RUNG = 740, 50


def _draw_climb(c, t, spec):
    dur, flip = spec["dur"], spec["flip"]
    win = 0.7 * dur
    xa, lx = _X(spec, 290), _X(spec, 760)
    rungs = (FLOOR - LTOP) // RUNG
    c.spot(xa, 240, strength=0.55)
    c.spot(lx, 260, strength=0.8)
    # ledge + door at the top
    L0, L1 = sorted((_X(spec, 700), _X(spec, 1040)))
    c.block(L0, LTOP - 20, L1, LTOP, color=(180, 180, 184))
    dx = _X(spec, 940)
    lit = clamp((t - win) / 0.4)
    c.d.rectangle([dx - 32, LTOP - 136, dx + 32, LTOP - 20], fill=nv.mix((30, 26, 14), GOLD, lit))
    c.d.rectangle([dx - 26, LTOP - 130, dx + 26, LTOP - 20], fill=nv.mix((70, 56, 22), GOLD2, lit))
    if lit > 0:
        c.glow(dx, LTOP - 80, 130, GOLD, 0.55 * lit)
    # ladder
    for sx_ in (-34, 34):
        c.d.line([(lx + sx_, FLOOR), (lx + sx_, LTOP - 20)], fill=(200, 200, 204), width=8)
    for r in range(1, rungs + 1):
        y = FLOOR - r * RUNG
        c.d.line([(lx - 34, y), (lx + 34, y)], fill=(200, 200, 204), width=6)
    # B climbs
    k = clamp((t - 0.3) / (0.66 * dur - 0.3))
    r = int(k * rungs)
    if t < 0.66 * dur:
        ph = math.sin(t * 8)
        P = dict(nv.BASE, la1=-165 + 15 * ph, la2=-5, ra1=165 + 15 * ph, ra2=5, ll1=-25 + 20 * ph, ll2=40,
                 rl1=25 + 20 * ph, rl2=-40)
        c.figure(lx, P, foot_y=FLOOR - r * RUNG)
        sb = f"{spec['ub']} {r + spec['start'] - 1}" if r else f"{spec['ub']} 0"
    else:
        wx = lerp(lx, dx - 40 * (1 if not flip else -1), ease((t - 0.66 * dur) / 0.25))
        c.figure(wx, celebrate(t) if t >= win else _pose(walk(t), flip), foot_y=LTOP - 20)
        sb = "TOP" if t >= win else f"{spec['ub']} {rungs + spec['start'] - 1}"
    # A on the floor with the phone
    info = c.figure(xa, _pose(_sit_phone(t) if t < win else sad(t), flip), col=GREY)
    if t < win:
        _phone_glow(c, info)
    hours = 1 + int(t / (dur / 8))
    sa = f"{spec['ua']} {hours}H"
    _label(c, spec["a"], xa, LABEL_Y, sa, sub_color=RED if t >= win else SUB)
    _label(c, spec["b"], lx, LABEL_Y, sb, sub_color=GOLD if t >= win else SUB)


def _events_climb(spec):
    dur = spec["dur"]
    rungs = (FLOOR - LTOP) // RUNG
    t0, t1 = 0.3, 0.66 * dur
    ev = [(t0 + (t1 - t0) * (i + 1) / rungs, "step", 0.2) for i in range(rungs)]
    ev += [(dur / 8 * i, "pop", 0.1) for i in range(1, 8)]
    ev += [(0.7 * dur, "flash", 0.5), (0.7 * dur + 0.1, "chime", 0.45)]
    return ev


_DUEL_DRAW = {"stack": _draw_stack, "dig": _draw_dig, "climb": _draw_climb}
_DUEL_EV = {"stack": _events_stack, "dig": _events_dig, "climb": _events_climb}


def draw_duel(c, t, spec):
    _DUEL_DRAW[spec["variant"]](c, t, spec)


def events_duel(spec):
    return _DUEL_EV[spec["variant"]](spec)


# ---------------- SPLIT ----------------
# (top_label, top_act, bottom_label, bottom_act, counter, res_top, res_bot, punch, caption_line, ig, topic)
SPLIT = [
    ("5 MINUTES", "pushup", "NO TIME", "snooze", "min", "STRONGER", "SAME", "SAME 5 MINUTES. DIFFERENT DAY.",
     "You don't need more time. You need to use five minutes.", "5 minute bhi kaafi hain, bas use karo.",
     "habits"),
    ("10 PAGES", "read", "10 REELS", "scroll", "days", "SMARTER", "SAME", "WHAT YOU FEED, GROWS.",
     "Ten pages a day is a book a month.", "Roz 10 page padho, saal mein 12 kitaabein.", "growth"),
    ("SAVE 100", "save", "SPEND 100", "spend", "days", "RS 36500", "RS 0", "SMALL SAVINGS. BIG FREEDOM.",
     "Small money, saved daily, becomes freedom.", "Roz ke 100 bachao, saal ke 36500.", "money"),
    ("WAKE AT 5", "pushup", "SNOOZE x3", "snooze", "clock", "AHEAD", "LATE", "WIN THE MORNING.",
     "Win the morning, win the day.", "Subah jeeto, poora din jeeto.", "habits"),
    ("RUN 1 KM", "run", "SKIP TODAY", "couch", "days", "FIT", "TIRED", "1 KM A DAY ADDS UP.",
     "A little movement daily beats a big plan someday.", "Roz thoda chalo, kabhi bahut nahi.",
     "discipline"),
    ("LEARN 1 SKILL", "read", "WATCH 1 SHOW", "scroll", "weeks", "HIRED", "STUCK", "SKILLS PAY. SHOWS DON'T.",
     "Learn while others are entertained.", "Doosre entertain ho rahe hain, tum seekho.", "growth"),
    ("WALK", "walk", "SIT", "couch", "days", "HEALTHY", "SAME", "MOVE A LITTLE EVERY DAY.",
     "Your body keeps the score of your habits.", "Body tumhari aadaton ka hisaab rakhti hai.", "habits"),
    ("FOCUS 1 HOUR", "read", "CHECK PHONE", "scroll", "min", "DONE", "NOT STARTED", "ONE HOUR OF FOCUS WINS.",
     "One hour of deep focus beats a day of distraction.", "Ek ghanta focus, poore din ke distraction se behtar.",
     "focus"),
    ("INVEST", "save", "SHOP", "spend", "years", "GROWING", "BROKE", "MONEY WORKS OR MONEY GOES.",
     "Make your money work, or it will walk away.", "Paisa kaam pe lagao, warna chala jayega.", "money"),
    ("TRAIN", "lift", "TALK ABOUT IT", "couch", "weeks", "STRONG", "SAME", "TALK LESS. TRAIN MORE.",
     "Results don't care about plans you talk about.", "Batane se nahi, karne se result aata hai.",
     "discipline"),
    ("PRACTICE", "pushup", "WAIT FOR LUCK", "couch", "days", "READY", "WAITING", "LUCK LOVES PRACTICE.",
     "The more you practice, the luckier you get.", "Jitni practice, utni kismat.", "growth"),
    ("READ AT NIGHT", "read", "SCROLL AT NIGHT", "scroll", "clocknight", "CALM", "TIRED",
     "YOUR NIGHT SHAPES YOUR MORNING.", "Your last hour decides your next morning.",
     "Raat ka aakhri ghanta kal ki subah banata hai.", "habits"),
    ("MEDITATE", "meditate", "OVERTHINK", "couch", "min", "CALM", "STRESSED", "5 MINUTES OF SILENCE.",
     "Five quiet minutes can save a loud day.", "5 minute shaanti, poora din behtar.", "mindset"),
    ("WRITE GOALS", "read", "JUST HOPE", "couch", "weeks", "CLEAR", "LOST", "WRITTEN GOALS GET DONE.",
     "A goal not written is just a wish.", "Goal likho, warna wo sirf wish hai.", "mindset"),
    ("NO SUGAR", "walk", "DAILY SWEETS", "couch", "days", "LIGHT", "HEAVY", "SMALL CHOICES. BIG BODY.",
     "Your plate today is your body tomorrow.", "Aaj ki plate kal ki body hai.", "habits"),
    ("SAVE FIRST", "save", "SAVE LATER", "spend", "years", "SECURE", "WORRIED", "PAY YOURSELF FIRST.",
     "Pay yourself first. Spend what's left.", "Pehle bachao, phir kharcho.", "money"),
    ("BUILD A SIDE", "read", "COMPLAIN", "couch", "weeks", "INCOME", "SAME", "BUILD WHILE THEY COMPLAIN.",
     "Build quietly while others complain loudly.", "Doosre shikayat karein, tum chupchap banao.", "growth"),
    ("STRETCH", "pushup", "SCROLL IN BED", "scroll", "min", "FRESH", "STIFF", "START THE DAY MOVING.",
     "Move first thing, and the day moves with you.", "Subah body chalao, din chalega.", "habits"),
    ("SPEAK UP", "walk", "STAY SILENT", "couch", "weeks", "NOTICED", "IGNORED", "SILENCE COSTS CHANCES.",
     "Opportunities go to people who raise their hand.", "Mauka unhe milta hai jo haath uthate hain.",
     "fear"),
    ("ONE MORE REP", "lift", "STOP AT TIRED", "couch", "weeks", "STRONGER", "SAME", "GROWTH STARTS AT TIRED.",
     "The rep you don't want to do is the one that counts.", "Jo rep mann nahi karta, wahi asli hai.",
     "discipline"),
    ("PLAN THE DAY", "read", "WING IT", "scroll", "clock", "ON TRACK", "BEHIND", "5 MINUTES OF PLANNING.",
     "Five minutes of planning saves hours of chaos.", "5 minute planning, ghanton ki bachat.", "time"),
    ("DRINK WATER", "walk", "DRINK SODA", "couch", "days", "ENERGY", "CRASH", "TINY SWAPS. BIG CHANGE.",
     "Tiny swaps make big lives.", "Chhote badlaav, bada farak.", "habits"),
    ("LEARN ENGLISH", "read", "SKIP CLASS", "scroll", "days", "FLUENT", "SAME", "10 WORDS A DAY.",
     "Ten new words a day is a new language a year.", "Roz 10 naye words, saal mein nayi bhasha.", "growth"),
    ("GYM AT 6", "lift", "SLEEP TILL 9", "snooze", "weeks", "FIT", "SAME", "SAME 24 HOURS.",
     "Same 24 hours. Different choices. Different life.", "24 ghante sabke paas same hain.", "time"),
    ("NO PHONE AM", "meditate", "PHONE FIRST", "scroll", "min", "FOCUSED", "SCATTERED",
     "DON'T START YOUR DAY WITH NOISE.", "The first hour belongs to you, not your phone.",
     "Subah ka pehla ghanta tumhara hai, phone ka nahi.", "focus"),
    ("SAY NO", "walk", "SAY YES TO ALL", "couch", "weeks", "FREE", "DRAINED", "PROTECT YOUR TIME.",
     "Every yes to others is a no to your goals.", "Har kisi ko haan, apne goal ko na.", "time"),
]

TF = 760  # top panel floor


def _counter(kind, k, v):
    if kind == "min":
        return f"MINUTE {1 + int(k * 4)}"
    if kind == "days":
        return f"DAY {int(lerp(1, 365, k ** 1.6))}"
    if kind == "weeks":
        return f"WEEK {int(lerp(1, 52, k))}"
    if kind == "years":
        return f"YEAR {1 + int(k * 9)}"
    if kind == "clock":
        m = int(lerp(5 * 60, 9 * 60, k)) // 5 * 5
        return f"{m // 60:02d}:{m % 60:02d}"
    if kind == "clocknight":
        m = int(lerp(22 * 60, 25 * 60, k)) // 5 * 5
        return f"{(m // 60) % 24:02d}:{m % 60:02d}"
    return str(int(k * 100))


def make_split(rnd, used):
    order = list(range(len(SPLIT)))
    rnd.shuffle(order)
    for _ in range(4):
        for i in order:
            v = rnd.randrange(6)
            key = f"split|{i}|{v}"
            if key in used:
                continue
            used.add(key)
            tl, ta, bl, ba, ck, rt, rb, punch, cap, ig, topic = SPLIT[i]
            return dict(format="split", key=key, dur=11.5 + (v % 3) * 0.5, top=None, punch=punch, punch_at=0.7,
                        caption_line=cap, ig=ig, topic=topic, tl=tl, ta=ta, bl=bl, ba=ba, ck=ck, rt=rt, rb=rb,
                        flip=v % 2 == 1)
    raise RuntimeError("split scripts exhausted")


def _act(c, kind, x, foot, t, s, col, prog):
    """Draw one panel's action. prog 0..1 grows the panel's progress prop."""
    if kind == "pushup":
        c.figure(x, nv.pushup(t), s=s, col=col, foot_y=foot)
    elif kind == "lift":
        k = 0.5 + 0.5 * math.sin(t * 4)
        P = dict(nv.BASE, la1=-(110 + 55 * k), la2=-(60 * (1 - k)), ra1=110 + 55 * k, ra2=60 * (1 - k),
                 ll1=-14, rl1=14)
        info = c.figure(x, P, s=s, col=col, foot_y=foot)
        (lx, ly), (rx, ry) = info["hands"]["l"], info["hands"]["r"]
        my = (ly + ry) / 2
        c.d.line([lx - 50, my, rx + 50, my], fill=(170, 170, 174), width=7)
        for px_ in (lx - 40, rx + 40):
            c.d.rectangle([px_ - 10, my - 34, px_ + 10, my + 34], fill=(200, 200, 204))
    elif kind == "read":
        info = c.figure(x, dict(sit(t), la1=60, la2=50, ra1=70, ra2=45, head=-18), s=s, col=col, foot_y=foot)
        hx, hy = info["hands"]["r"]
        c.d.polygon([(hx - 30, hy - 30), (hx + 4, hy - 20), (hx + 4, hy + 16), (hx - 30, hy + 6)], fill=GOLD2)
        c.d.polygon([(hx + 4, hy - 20), (hx + 38, hy - 30), (hx + 38, hy + 6), (hx + 4, hy + 16)], fill=GOLD)
        n = int(prog * 6)
        for i in range(n):  # pile of finished books
            c.block(x - 170, foot - (i + 1) * 16, x - 90, foot - i * 16 - 2, color=(200, 200, 204))
    elif kind == "run":
        c.figure(x, walk(t, 12, 40, 12), s=s, col=col, foot_y=foot)
        for i in range(5):
            xx = (W - (t * 420 + i * 230) % (W + 200))
            c.d.line([(xx, foot + 6), (xx + 60, foot + 6)], fill=(70, 70, 74), width=3)
    elif kind == "walk":
        c.figure(x, walk(t), s=s, col=col, foot_y=foot)
        for i in range(5):
            xx = (W - (t * 200 + i * 230) % (W + 200))
            c.d.line([(xx, foot + 6), (xx + 60, foot + 6)], fill=(70, 70, 74), width=3)
    elif kind == "save":
        k = 0.5 + 0.5 * math.sin(t * 5)
        c.figure(x, nv.bend(t, 0.3 + 0.3 * k), s=s, col=col, foot_y=foot)
        n = 1 + int(prog * 11)
        for i in range(n):
            cy = foot - 10 - i * 13
            c.d.ellipse([x + 70, cy - 8, x + 130, cy + 8], fill=GOLD if i % 2 else GOLD2)
    elif kind == "meditate":
        c.figure(x, dict(sit(t), ll1=70, ll2=-140, rl1=75, rl2=-140, la1=40, la2=-30, ra1=50, ra2=-30),
                 s=s, col=col, foot_y=foot)
    elif kind == "snooze":
        c.d.rectangle([x - 150, foot - 40, x + 150, foot], fill=(60, 60, 64))
        c.figure(x, nv.lie(t), s=s, col=col, foot_y=foot - 40)
        for i in range(3):
            ph = (t * 0.5 + i / 3) % 1
            c.text("Z", x + 110 + ph * 60, foot - 150 - ph * 110, 22, (110, 110, 114), world=True)
    elif kind == "scroll":
        info = c.figure(x, _sit_phone(t), s=s, col=col, foot_y=foot)
        _phone_glow(c, info)
    elif kind == "spend":
        c.figure(x, stand(t), s=s, col=col, foot_y=foot)
        n = max(0, 11 - int(prog * 12))
        for i in range(n):
            cy = foot - 10 - i * 13
            c.d.ellipse([x + 70, cy - 8, x + 130, cy + 8], fill=(110, 92, 40))
        fall = (t * 1.3) % 1
        c.d.ellipse([x + 160, foot - 120 + fall * 110, x + 190, foot - 110 + fall * 110], fill=GOLD)
    else:  # couch
        c.d.rectangle([x - 140, foot - 70, x + 120, foot], fill=(52, 52, 56))
        c.d.rectangle([x - 140, foot - 150, x - 100, foot], fill=(52, 52, 56))
        c.figure(x - 20, dict(sit(t), lean=-14, head=-6), s=s, col=col, foot_y=foot - 40)


def _top_reflection(c):
    hgt = 150
    band = c.img.crop((0, TF - hgt, W, TF)).transpose(Image.FLIP_TOP_BOTTOM)
    band = band.resize((W // 3, hgt // 3)).resize((W, hgt))
    g = Image.linear_gradient("L").resize((W, hgt)).point(lambda v: int(80 * (1 - v / 255) ** 1.6))
    c.img.paste(band, (0, TF), g)
    c.d.line([(60, TF), (W - 60, TF)], fill=(30, 30, 33), width=2)


def draw_split(c, t, spec):
    dur = spec["dur"]
    res = 0.7 * dur
    k = clamp(t / res)
    lit = clamp((t - res) / 0.4)
    s = 0.8
    xt = _X(spec, 500)
    # top panel
    _spot_at(c, xt, TF, 380, 280, 0.8, nv.mix((255, 255, 255), GOLD, lit))
    if lit > 0:
        c.glow(xt, TF - 120, 170, GOLD, 0.35 * lit)
    _act(c, spec["ta"], xt, TF, t, s, WHITE, k)
    _top_reflection(c)
    # bottom panel on the main floor
    c.spot(xt, 260, strength=0.55)
    _act(c, spec["ba"], xt, FLOOR, t, s, GREY, k)
    # labels + counter
    _label(c, spec["tl"], W / 2, 370, spec["rt"] if t >= res else None, sub_color=GOLD, px=30)
    c.text(_counter(spec["ck"], k, 0), W / 2, 830, 56, GOLD if t >= res else WHITE)
    _label(c, spec["bl"], W / 2, 950, spec["rb"] if t >= res else None, sub_color=RED, color=WHITE, px=26)


def events_split(spec):
    dur = spec["dur"]
    res = 0.7 * dur
    ev = [(i * 0.6, "pop", 0.12) for i in range(1, int(res / 0.6) + 1)]
    ev += [(res, "flash", 0.5), (res + 0.1, "chime", 0.45)]
    return ev


FORMATS = {
    "duel": {"make": make_duel, "draw": draw_duel, "events": events_duel},
    "split": {"make": make_split, "draw": draw_split, "events": events_split},
}


# ---------------- test ----------------
def _frame(spec, t):
    c = Canvas()
    FORMATS[spec["format"]]["draw"](c, t, spec)
    y = nv.TOP_Y
    if spec.get("top"):
        y = c.lines(spec["top"], W / 2, y, 30)
    if spec.get("punch") and t >= spec.get("punch_at", 0.66) * spec["dur"]:
        c.lines(spec["punch"], W / 2, y + nv.PUNCH_GAP, 30, GOLD)
    return nv.watermark(c.finish(t), t)


if __name__ == "__main__":
    import os
    import sys
    os.makedirs("out", exist_ok=True)
    rnd = random.Random(5)
    used = set()
    for fmt in ("duel", "split"):
        specs = [FORMATS[fmt]["make"](rnd, used) for _ in range(3 if fmt == "duel" else 2)]
        if fmt == "duel":  # make sure each variant appears
            for var in ("stack", "dig", "climb"):
                if not any(s_["variant"] == var for s_ in specs):
                    i = next(j for j, row in enumerate(DUEL) if row[2] == var)
                    s_ = dict(specs[0])
                    a, b, vr, top, punch, cap, ig, topic, ua, ub = DUEL[i]
                    s_.update(a=a, b=b, variant=vr, top=top, punch=punch, ua=ua, ub=ub)
                    specs.append(s_)
            specs = specs[-3:]
        ts = [0.3, 0.25, 0.45, 0.6, 0.72, 0.95]
        sheet = Image.new("RGB", (270 * len(ts), 480 * len(specs)))
        for r, sp in enumerate(specs):
            for ci, f in enumerate(ts):
                img = _frame(sp, f * sp["dur"] if f > 0.29 else 0.3)
                sheet.paste(img.resize((270, 480)), (ci * 270, r * 480))
        sheet.save(f"out/fa_{fmt}.png")
        print(fmt, [s_.get("variant", s_.get("ta")) for s_ in specs])
    if "video" in sys.argv:
        sp = make_duel(random.Random(1), set())
        print(sp["key"], sp["variant"])
        nv.render(sp, draw_duel, events_duel(sp), "out/fa_duel.mp4", seed=2)
        print("video ok")
