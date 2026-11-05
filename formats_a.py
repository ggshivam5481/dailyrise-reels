"""Formats A: "duel" (two labelled people, opposite choices, one wins) and "split" (two stacked panels
with a shared ticking counter). Drawn through the nv.Canvas API."""
import math
import random

from PIL import Image, ImageDraw

import nv
import props_a as P
from nv import (BG, BLOCK, FLOOR, GOLD, GOLD2, GREY, H, RED, SUB, W, WHITE, Canvas, carry_up, celebrate, clamp,
                ease, lerp, mirror, sad, sit, stand, walk)

LABEL_Y = int(0.26 * H)  # 499


# ---------------- small helpers ----------------
def _pose(Q, flip):
    return mirror(Q) if flip else Q


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


# ---------------- round 2: new coloured duel scenes ----------------
DUEL2 = [
    ("SPENDER", "SAVER", "money", "SAME SALARY.", "ONE BUYS THINGS. ONE BUYS FREEDOM.",
     "Rich isn't what you earn. It's what you keep.", "Kamaana nahi, bachana amir banata hai.", "money", "RS", "RS"),
    ("SHOW OFF", "INVESTOR", "money", "LOOKING RICH VS BEING RICH.", "QUIET MONEY GROWS.",
     "Looking rich is expensive. Being rich is quiet.", "Dikhawa mehenga hai, asli ameeri chup rehti hai.",
     "money", "RS", "RS"),
    ("BROKE MINDSET", "WEALTH MINDSET", "money", "100 RUPEES A DAY.", "SMALL COINS. BIG FREEDOM.",
     "Small amounts saved daily become life-changing.", "Roz ke 100 rupaye zindagi badal dete hain.", "money",
     "RS", "RS"),
    ("IMPULSE BUYER", "PATIENT ONE", "money", "WANT IT NOW?", "PATIENCE PAYS INTEREST.",
     "Delayed gratification is a superpower.", "Abhi ka mazaa, baad ki saza.", "money", "RS", "RS"),
    ("COUCH", "GYM", "gym", "SAME EVENING. TWO CHOICES.", "YOUR BODY KEEPS THE SCORE.",
     "Your body is a diary of your daily choices.", "Body tumhari roz ki choices ki diary hai.", "discipline",
     "SLICE", "REP"),
    ("NETFLIX", "DISCIPLINE", "gym", "ONE MORE EPISODE?", "ONE MORE REP INSTEAD.",
     "Trade one episode for one workout.", "Ek episode kam, ek workout zyada.", "discipline", "EP", "REP"),
    ("TOMORROW", "TODAY", "gym", "I'LL START MONDAY.", "TODAY BUILT THE BODY.",
     "Monday never comes. Today does.", "Monday kabhi nahi aata, aaj aata hai.", "habits", "DAY", "REP"),
    ("COMFORT", "GROWTH", "gym", "COMFORT FEELS GOOD.", "GROWTH FEELS BETTER LATER.",
     "Comfort is a loan. Future you pays the interest.", "Aaj ka aaram, kal ka karz.", "growth", "SNACK", "REP"),
    ("SCROLLER", "READER", "read", "10 MINUTES BEFORE BED.", "WHAT YOU FEED, GROWS.",
     "Your mind becomes what you feed it.", "Dimaag wahi banta hai jo tum use khilate ho.", "focus", "REEL",
     "PAGE"),
    ("DISTRACTED", "FOCUSED", "read", "SAME PHONE. SAME HOUR.", "FOCUS IS THE NEW IQ.",
     "In a distracted world, focus is a superpower.", "Distraction ki duniya mein focus superpower hai.",
     "focus", "PING", "PAGE"),
    ("ENTERTAINED", "EDUCATED", "read", "ONE HOUR A DAY.", "ONE GETS SMARTER.",
     "Entertainment costs you. Education pays you.", "Entertainment kharcha hai, education kamai.", "growth",
     "VIDEO", "BOOK"),
    ("CONSUMER", "LEARNER", "read", "THE SAME 60 MINUTES.", "LIGHTS ON.",
     "Consume less, learn more.", "Kam dekho, zyada seekho.", "growth", "REEL", "IDEA"),
    ("IGNORER", "GARDENER", "plant", "TWO SEEDS. SAME SOIL.", "WHAT YOU WATER, GROWS.",
     "Whatever you water daily is what grows.", "Jise roz paani doge, wahi badhega.", "habits", "DAY", "DAY"),
    ("WAITER", "WORKER", "plant", "DREAMS NEED WATER.", "SMALL DAILY CARE.",
     "Dreams don't grow on wishes. They grow on daily work.", "Sapne roz ke kaam se badhte hain.", "discipline",
     "WISH", "DAY"),
    ("SOMEDAY", "DAILY", "plant", "GROWTH IS SLOW.", "THEN SUDDENLY IT ISN'T.",
     "Growth is invisible until it isn't.", "Growth dikhti nahi, phir achanak dikhti hai.", "growth", "DAY", "DAY"),
    ("NEGLECT", "PATIENCE", "plant", "NOTHING HAPPENS FOR WEEKS.", "THEN EVERYTHING DOES.",
     "Patience is just consistency you can't see yet.", "Sabr bhi consistency hai, bas dikhti nahi.",
     "mindset", "WEEK", "WEEK"),
]


def _acc():
    return P.T()["accent"]


def _acc2():
    return P.T()["accent2"]


def _beats(dur, start=0.5, step=1.2, end_frac=0.66):
    n = int((end_frac * dur - start) / step) + 1
    return [start + i * step for i in range(max(1, n))]


def _plus(c, t, x, y, beats, txt="+1", col=None):
    for b in beats:
        k = (t - b) / 0.8
        if 0 <= k < 1:
            c.text(txt, x, y - 70 * k, 28, nv.mix(BG, col or _acc(), 1 - k * k))


def _decor(c, t, spec, xa, xb, win, win_xy=None, cloud=True):
    """Shared colour beats: progress bars, +1 pops, rain over the loser, sparkles + trophy for the winner."""
    k = clamp(t / win)
    P.progress_bar(c, xb, LABEL_Y + 96, 190, k, _acc())
    P.progress_bar(c, xa, LABEL_Y + 96, 190, min(k, 0.15), RED if t >= win else (120, 120, 126))
    _plus(c, t, xb, LABEL_Y + 160, _beats(spec["dur"]), "+1")
    if t >= win:
        if cloud:
            s = 0.8 * P.pop(t, win + 0.4)
            if s > 0:
                P.rain_cloud(c, xa, FLOOR - 420, s, t)
        if win_xy:
            for i, (dx, dy) in enumerate(((-90, -40), (80, -90), (-60, -160), (100, 10), (0, -200))):
                if t > win + 0.2 + i * 0.12:
                    P.sparkle(c, win_xy[0] + dx, win_xy[1] + dy, 1.2, t, GOLD2 if i % 2 else _acc())


def _decor_events(spec, win):
    ev = [(b, "pop", 0.45) for b in _beats(spec["dur"])]
    ev += [(win, "riser", 0.6), (win, "impact", 0.7), (win + 0.02, "flash", 0.9), (win + 0.12, "chime", 1.0),
           (win + 0.35, "pop", 0.5), (win + 0.5, "pop", 0.45), (win + 0.45, "rumble", 0.45),
           (win + 0.6, "heartbeat", 0.5)]
    return ev


# ---------- duel: MONEY (saver vs spender) ----------
def _draw_money(c, t, spec):
    dur, flip = spec["dur"], spec["flip"]
    win = 0.7 * dur
    xa, xb = _X(spec, 270), _X(spec, 790)
    beats = _beats(dur)
    nb = sum(1 for b in beats if t >= b)
    c.spot(xa, 260, strength=0.7)
    c.spot(xb, 300, strength=0.9)
    sgn = -1 if flip else 1
    # saver: drops a coin each beat, stack + bag grow
    ph = 0.5 + 0.5 * math.sin(t * 6)
    c.figure(xb - sgn * 70, _pose(nv.bend(t, 0.25 + 0.3 * ph), flip))
    stack_x = xb + sgn * 70
    P.coin_stack(c, stack_x, FLOOR, 2 + nb * 2)
    if beats and nb < len(beats):
        nxt = beats[nb]
        fall = clamp(1 - (nxt - t) / 0.5)
        if fall > 0:
            P.coin(c, stack_x, FLOOR - (2 + nb * 2) * 11 - 160 * (1 - fall) - 10, 0.8, t * 9)
    bag_k = clamp(t / win)
    P.money_bag(c, xb + sgn * 190, FLOOR, 0.75, bag_k)
    lit = clamp((t - win) / 0.4)
    if lit > 0:
        c.glow(xb + sgn * 190, FLOOR - 70, 120, GOLD, 0.6 * lit)
        s = P.pop(t, win + 0.25)
        P.key(c, xb + sgn * 120, FLOOR - 330, 1.4 * s)
        P.lock(c, xb + sgn * 10, FLOOR - 300, 1.0 * max(0.01, s), open_=clamp((t - win - 0.6) / 0.4))
    # spender: shopping bags pile, cash flies away
    info = c.figure(xa, _pose(stand(t) if t < win else sad(t), flip), col=GREY if t >= win else (205, 205, 210))
    cols = [_acc2(), (90, 170, 255), (240, 120, 60), (170, 100, 220), (60, 190, 140), (240, 200, 60)]
    for i in range(min(nb, 6)):
        s = 0.7 * P.pop(t, beats[i])
        if s > 0:
            P.shop_bag(c, xa + sgn * (90 + (i % 3) * 55) * (1 if i < 3 else -1), FLOOR - (i // 3) * 0, s,
                       cols[i % len(cols)])
    for i in range(4):
        ph2 = (t * 0.7 + i * 0.25) % 1
        if t < win:
            P.cash(c, xa + 60 * math.sin(i * 2 + t), info["top"] - 30 - ph2 * 260, 0.7, ph2 * 3 + i)
    sa = f"RS {max(0, 900 - nb * 150)}" if t < win else "BROKE"
    sb = f"RS {100 * (1 + nb * 7)}" if t < win else "FREE"
    _label(c, spec["a"], xa, LABEL_Y, sa, sub_color=RED if t >= win else SUB)
    _label(c, spec["b"], xb, LABEL_Y, sb, sub_color=GOLD if t >= win else _acc())
    _decor(c, t, spec, xa, xb, win, (xb + sgn * 120, FLOOR - 300))


def _events_money(spec):
    dur = spec["dur"]
    win = 0.7 * dur
    ev = [(b, "thud", 0.5) for b in _beats(dur)] + [(b - 0.1, "whoosh", 0.4) for b in _beats(dur)]
    return ev + _decor_events(spec, win) + [(win + 0.6, "snap", 0.6)]


# ---------- duel: GYM (gym vs couch) ----------
def _draw_gym(c, t, spec):
    dur, flip = spec["dur"], spec["flip"]
    win = 0.7 * dur
    xa, xb = _X(spec, 280), _X(spec, 790)
    beats = _beats(dur)
    nb = sum(1 for b in beats if t >= b)
    sgn = -1 if flip else 1
    c.spot(xa, 280, strength=0.6)
    c.spot(xb, 300, strength=0.95)
    # couch side: TV flicker, pizza + soda pile up
    P.tv(c, xa - sgn * 0, FLOOR - 330, 0.75, t)
    P.couch(c, xa, FLOOR, 0.75)
    col_a = GREY if t >= win else (205, 205, 210)
    info = c.figure(xa, _pose(dict(sit(t), lean=-14, head=-6, la1=40, la2=60, ra1=50, ra2=50), flip), s=0.9,
                    col=col_a, foot_y=FLOOR - 36)
    P.controller(c, info["hands"]["r"][0], info["hands"]["r"][1] + 10, 0.6)
    for i in range(min(nb, 6)):
        s = 0.6 * P.pop(t, beats[i])
        if s > 0:
            fx = xa + sgn * (150 + (i % 3) * 40)
            (P.pizza if i % 2 == 0 else P.soda)(c, fx, FLOOR - (i // 3) * 40, s)
    # gym side: barbell lift, dumbbell rack grows
    k = 0.5 + 0.5 * math.sin(t * 4.5)
    Pz = dict(nv.BASE, la1=-(110 + 55 * k), la2=-(60 * (1 - k)), ra1=110 + 55 * k, ra2=60 * (1 - k), ll1=-14, rl1=14)
    if t >= win:
        Pz = celebrate(t)
    info_b = c.figure(xb, Pz)
    if t < win:
        P.barbell(c, info_b["hands"]["l"], info_b["hands"]["r"], 1.0, _acc())
    for i in range(min(nb, 6)):
        s = 0.8 * P.pop(t, beats[i])
        if s > 0:
            P.dumbbell(c, xb + sgn * (150 + (i % 3) * 75), FLOOR - (i // 3) * 34, s,
                       [_acc(), _acc2(), (255, 140, 40)][i % 3])
    if t >= win:
        s = P.pop(t, win + 0.2)
        P.trophy(c, xb, info_b["top"] - 40, 1.2 * max(0.01, s), s)
    sa = f"{spec['ua']} {1 + nb}" if t < win else "TIRED"
    sb = f"{spec['ub']} {10 * (1 + nb * 3)}" if t < win else "STRONG"
    _label(c, spec["a"], xa, LABEL_Y, sa, sub_color=RED if t >= win else SUB)
    _label(c, spec["b"], xb, LABEL_Y, sb, sub_color=GOLD if t >= win else _acc())
    _decor(c, t, spec, xa, xb, win, (xb, FLOOR - 380))


def _events_gym(spec):
    dur = spec["dur"]
    win = 0.7 * dur
    ev = [(b + 0.05, "thud", 0.6) for b in _beats(dur)]
    ev += [(0.3 + i * (2 * math.pi / 4.5), "step", 0.4) for i in range(int(win / (2 * math.pi / 4.5)))]
    return ev + _decor_events(spec, win)


# ---------- duel: READ (reader vs scroller) ----------
def _draw_read(c, t, spec):
    dur, flip = spec["dur"], spec["flip"]
    win = 0.7 * dur
    xa, xb = _X(spec, 280), _X(spec, 780)
    beats = _beats(dur)
    nb = sum(1 for b in beats if t >= b)
    sgn = -1 if flip else 1
    c.spot(xa, 260, strength=0.6, color=(120, 160, 255))
    c.spot(xb, 300, strength=0.95)
    # scroller: phone glow, notifications pop
    col_a = GREY if t >= win else (205, 205, 210)
    info = c.figure(xa, _pose(_sit_phone(t) if t < win else sad(t), flip), col=col_a)
    if t < win:
        hx, hy = info["hands"]["l"]
        P.phone(c, hx, hy + 20, 0.7, t, True, badge=3 + nb * 9)
    words = ["LIKE", "REEL", "NEW", "PING", "SALE", "LIVE"]
    for i in range(min(nb, 5)):
        s = 0.9 * P.pop(t, beats[i])
        if s > 0 and t < win:
            P.notif(c, xa + sgn * (40 if i % 2 else -40), info["top"] - 60 - i * 52, s, words[i % len(words)])
    # reader: open book, colourful stack grows, bulb brightens
    info_b = c.figure(xb, _pose(dict(sit(t), la1=60, la2=50, ra1=70, ra2=45, head=-18), flip) if t < win
                      else celebrate(t))
    if t < win:
        hx, hy = info_b["hands"]["r"]
        P.open_book(c, hx, hy + 30, 0.8, t)
    P.book_stack(c, xb + sgn * 170, FLOOR, 1 + nb, 1.0, seed=3)
    on = clamp(t / win) * 0.6 + (0.4 if t >= win else 0)
    P.bulb(c, xb, info_b["top"] - 30, 0.9 + 0.3 * (t >= win), on)
    if t >= win:
        s = P.pop(t, win + 0.3)
        P.brain(c, xb + sgn * 170, FLOOR - (1 + nb) * 19 - 10, 0.9 * max(0.01, s), s)
    sa = f"{spec['ua']} {1 + nb * 23}" if t < win else "0% BATTERY"
    sb = f"{spec['ub']} {1 + nb * 4}" if t < win else "LEVEL UP"
    _label(c, spec["a"], xa, LABEL_Y, sa, sub_color=RED if t >= win else SUB)
    _label(c, spec["b"], xb, LABEL_Y, sb, sub_color=GOLD if t >= win else _acc())
    _decor(c, t, spec, xa, xb, win, (xb, info_b["top"] - 60))


def _events_read(spec):
    dur = spec["dur"]
    win = 0.7 * dur
    ev = [(b + 0.03, "pop", 0.55) for b in _beats(dur)] + [(b + 0.4, "step", 0.35) for b in _beats(dur)]
    return ev + _decor_events(spec, win) + [(win + 0.3, "swell", 0.6)]


# ---------- duel: PLANT (gardener vs ignorer) ----------
def _draw_plant(c, t, spec):
    dur, flip = spec["dur"], spec["flip"]
    win = 0.7 * dur
    xa, xb = _X(spec, 280), _X(spec, 790)
    beats = _beats(dur)
    nb = sum(1 for b in beats if t >= b)
    sgn = -1 if flip else 1
    c.spot(xa, 250, strength=0.55)
    c.spot(xb, 300, strength=0.95, color=(170, 255, 190))
    grow = clamp(t / win)
    # ignorer: on the phone, plant wilts
    col_a = GREY if t >= win else (205, 205, 210)
    info = c.figure(xa - sgn * 50, _pose(_sit_phone(t) if t < win else sad(t), flip), col=col_a)
    if t < win:
        hx, hy = info["hands"]["l"]
        P.phone(c, hx, hy + 20, 0.6, t, True)
    P.plant(c, xa + sgn * 110, FLOOR, 0.9, 0.35, wilt=clamp(t / win), t=t)
    # gardener: waters each beat, plant grows to fruit
    pour = 1.0 if any(0 <= t - b < 0.8 for b in beats) and t < win else 0.0
    Pz = dict(nv.BASE, ra1=70 + 20 * pour, ra2=20, la1=-10, lean=6) if t < win else celebrate(t)
    info_b = c.figure(xb - sgn * 110, _pose(Pz, flip))
    if t < win:
        hx, hy = info_b["hands"]["r"]
        P.watering_can(c, hx + sgn * 20, hy + 30, 0.8, pour, t)
    P.plant(c, xb + sgn * 60, FLOOR, 1.1, 0.15 + 0.85 * grow, 0.0, t)
    if t >= win:
        c.glow(xb + sgn * 60, FLOOR - 250, 140, (120, 255, 150), 0.4 * clamp((t - win) / 0.4))
    sa = f"{spec['ua']} {1 + nb * 9}" if t < win else "DEAD"
    sb = f"{spec['ub']} {1 + nb * 9}" if t < win else "HARVEST"
    _label(c, spec["a"], xa, LABEL_Y, sa, sub_color=RED if t >= win else SUB)
    _label(c, spec["b"], xb, LABEL_Y, sb, sub_color=GOLD if t >= win else _acc())
    _decor(c, t, spec, xa, xb, win, (xb + sgn * 60, FLOOR - 300), cloud=False)


def _events_plant(spec):
    dur = spec["dur"]
    win = 0.7 * dur
    ev = [(b, "whoosh", 0.45) for b in _beats(dur)] + [(b + 0.3, "pop", 0.5) for b in _beats(dur)]
    return ev + _decor_events(spec, win) + [(win + 0.4, "swell", 0.5)]


def make_duel(rnd, used):
    bank = DUEL + DUEL2
    order = list(range(len(bank)))
    rnd.shuffle(order)
    for _ in range(4):
        for i in order:
            v = rnd.randrange(10)
            key = f"a2|duel|{i}|{v}"
            if key in used:
                continue
            used.add(key)
            a, b, var, top, punch, cap, ig, topic, ua, ub = bank[i]
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
        c.block(X0, FLOOR - hgt, X1, FLOOR, color=nv.mix(BLOCK, _acc() if i % 2 else _acc2(), 0.45))
        if 0 <= t - tb - 0.3 < 0.45:
            P.sparkle(c, (X0 + X1) / 2, FLOOR - hgt - 20, 1.2, t, _acc())
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
            Pq = carry_up(t)
            info = c.figure(fx, _pose(Pq, flip))
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
    _label(c, spec["b"], bx, LABEL_Y, sub_b, sub_color=GOLD if t >= win else _acc())
    P.flag(c, dx + (40 if not flip else -40), dtop, 0.7, t, _acc())
    _decor(c, t, spec, xa, bx, win, (dx, dtop - 120))


def _events_stack(spec):
    dur, n = spec["dur"], spec["n"]
    beat = (0.5 * dur - 0.4) / n
    ev = [(0.4 + i * beat + 0.28, "thud", 0.7) for i in range(n)]
    ev += [(0.4 + i * beat + 0.3, "pop", 0.45) for i in range(n)]
    k0, k1 = 0.5 * dur, 0.68 * dur
    ev += [(k0 + (k1 - k0) * j / n, "step", 0.55) for j in range(n)]
    return ev + _decor_events(spec, 0.7 * dur)


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
        for i in range(6):
            k = clamp((t - win - i * 0.08) / 0.7)
            if k > 0:
                P.coin(c, xb + (i - 2.5) * 40, vein_y - 260 * math.sin(k * math.pi * 0.8) - 10, 0.8, t * 8 + i)
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
            Pq = dict(nv.BASE, lean=10 + 25 * hit, ra1=150 - 120 * hit, ra2=-20, la1=-20)
            info = c.figure(x, _pose(Pq, spec["flip"]), foot_y=foot, col=col)
            hand = info["hands"]["r"]
            ang = (150 - 120 * hit) * (-1 if spec["flip"] else 1)
            _hammer(c, hand, ang, 56)
    sa = f"{spec['ua']} {da + spec['start'] - 1}" if t <= 0.5 * dur else f"QUIT AT {da + spec['start'] - 1}"
    sb = f"{spec['ub']} {min(db, ROWS) + spec['start'] - 1}" if t < win else "GOLD"
    _label(c, spec["a"], xa, LABEL_Y, sa, sub_color=RED if t > 0.5 * dur else SUB)
    _label(c, spec["b"], xb, LABEL_Y, sb, sub_color=GOLD if t >= win else _acc())
    P.torch(c, _X(spec, 60), TOPG, 0.8, t)
    P.torch(c, _X(spec, 1020), TOPG, 0.8, t + 1)
    _decor(c, t, spec, xa, xb, win, (xb, vein_y - 200))


def _events_dig(spec):
    dur = spec["dur"]
    pace = 0.5 * dur / (ROWS - 1)
    ev = [(i * pace, "thud", 0.7) for i in range(1, ROWS)]
    ev += [(i * pace + 0.02, "snap", 0.35) for i in range(1, ROWS)]
    ev += [(0.5 * dur + 0.1, "heartbeat", 0.7), (0.68 * dur, "rumble", 0.7)]
    return ev + _decor_events(spec, 0.7 * dur)


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
        c.d.line([(lx + sx_, FLOOR), (lx + sx_, LTOP - 20)], fill=nv.mix((200, 200, 204), _acc(), 0.5), width=8)
    for r in range(1, rungs + 1):
        y = FLOOR - r * RUNG
        c.d.line([(lx - 34, y), (lx + 34, y)], fill=(200, 200, 204), width=6)
    # B climbs
    k = clamp((t - 0.3) / (0.66 * dur - 0.3))
    r = int(k * rungs)
    if t < 0.66 * dur:
        ph = math.sin(t * 8)
        Pq = dict(nv.BASE, la1=-165 + 15 * ph, la2=-5, ra1=165 + 15 * ph, ra2=5, ll1=-25 + 20 * ph, ll2=40,
                 rl1=25 + 20 * ph, rl2=-40)
        c.figure(lx, Pq, foot_y=FLOOR - r * RUNG)
        sb = f"{spec['ub']} {r + spec['start'] - 1}" if r else f"{spec['ub']} 0"
    else:
        wx = lerp(lx, dx - 40 * (1 if not flip else -1), ease((t - 0.66 * dur) / 0.25))
        c.figure(wx, celebrate(t) if t >= win else _pose(walk(t), flip), foot_y=LTOP - 20)
        sb = "TOP" if t >= win else f"{spec['ub']} {rungs + spec['start'] - 1}"
    # A on the floor with the phone
    info = c.figure(xa, _pose(_sit_phone(t) if t < win else sad(t), flip), col=GREY)
    if t < win:
        hx, hy = info["hands"]["l"]
        P.phone(c, hx, hy + 20, 0.6, t, True, badge=1 + int(t * 7))
    hours = 1 + int(t / (dur / 8))
    sa = f"{spec['ua']} {hours}H"
    _label(c, spec["a"], xa, LABEL_Y, sa, sub_color=RED if t >= win else SUB)
    _label(c, spec["b"], lx, LABEL_Y, sb, sub_color=GOLD if t >= win else _acc())
    P.flag(c, _X(spec, 1010), LTOP - 20, 0.6, t, _acc())
    _decor(c, t, spec, xa, lx, win, (dx, LTOP - 150))


def _events_climb(spec):
    dur = spec["dur"]
    rungs = (FLOOR - LTOP) // RUNG
    t0, t1 = 0.3, 0.66 * dur
    ev = [(t0 + (t1 - t0) * (i + 1) / rungs, "step", 0.6) for i in range(rungs)]
    ev += [(dur / 8 * i, "pop", 0.3) for i in range(1, 8)]
    return ev + _decor_events(spec, 0.7 * dur)


_DUEL_DRAW = {"stack": _draw_stack, "dig": _draw_dig, "climb": _draw_climb, "money": _draw_money,
              "gym": _draw_gym, "read": _draw_read, "plant": _draw_plant}
_DUEL_EV = {"stack": _events_stack, "dig": _events_dig, "climb": _events_climb, "money": _events_money,
            "gym": _events_gym, "read": _events_read, "plant": _events_plant}


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


SPLIT2 = [
    ("CODE 1 HOUR", "laptop", "GAME 1 HOUR", "game", "days", "HIRED", "SAME", "ONE HOUR CHANGES CAREERS.",
     "One focused hour a day can change your career.", "Roz ka ek ghanta career badal deta hai.", "growth"),
    ("BUILD AN APP", "laptop", "BINGE A SHOW", "game", "weeks", "LAUNCHED", "BORED", "CREATE MORE. CONSUME LESS.",
     "Creators build the world consumers scroll through.", "Banao zyada, dekho kam.", "growth"),
    ("LEARN TO CODE", "laptop", "DOOMSCROLL", "scroll", "days", "SKILLED", "DRAINED", "SKILLS ARE THE NEW SALARY.",
     "Your skills are your real salary.", "Skill hi asli salary hai.", "growth"),
    ("EAT CLEAN", "salad", "EAT JUNK", "junk", "days", "ENERGY", "TIRED", "YOU ARE WHAT YOU EAT.",
     "Every meal is a vote for the body you want.", "Har khana us body ka vote hai jo tum chahte ho.", "habits"),
    ("COOK AT HOME", "salad", "ORDER DAILY", "junk", "weeks", "HEALTHY", "RS GONE", "HOME FOOD. RICH BODY.",
     "Cooking at home saves money and health.", "Ghar ka khana, paisa aur sehat dono bachata hai.", "money"),
    ("FRUIT SNACK", "salad", "SUGAR SNACK", "junk", "days", "LIGHT", "HEAVY", "SMALL SWAPS. BIG BODY.",
     "Swap one snack and change your year.", "Ek snack badlo, saal badal jayega.", "habits"),
    ("WATER IT", "plant", "FORGET IT", "neglect", "weeks", "GROWN", "DEAD", "WHAT YOU WATER, GROWS.",
     "Anything you water daily will grow.", "Jise roz paani doge, wahi badhega.", "habits"),
    ("NURTURE A SKILL", "plant", "IGNORE IT", "neglect", "days", "BLOOMED", "WITHERED", "CARE DAILY. GROW SLOWLY.",
     "Skills are plants. Neglect kills them quietly.", "Skill bhi paudha hai, chhod doge to sookh jayega.",
     "growth"),
    ("GOAL ON PAPER", "laptop", "GOAL IN HEAD", "couch", "weeks", "DONE", "FORGOTTEN", "WRITE IT. DO IT.",
     "Written goals get done. Imagined ones get forgotten.", "Likha hua goal poora hota hai.", "mindset"),
]


def make_split(rnd, used):
    bank = SPLIT + SPLIT2
    order = list(range(len(bank)))
    rnd.shuffle(order)
    for _ in range(4):
        for i in order:
            v = rnd.randrange(6)
            key = f"a2|split|{i}|{v}"
            if key in used:
                continue
            used.add(key)
            tl, ta, bl, ba, ck, rt, rb, punch, cap, ig, topic = bank[i]
            return dict(format="split", key=key, dur=11.5 + (v % 3) * 0.5, top=None, punch=punch, punch_at=0.7,
                        caption_line=cap, ig=ig, topic=topic, tl=tl, ta=ta, bl=bl, ba=ba, ck=ck, rt=rt, rb=rb,
                        flip=v % 2 == 1)
    raise RuntimeError("split scripts exhausted")


def _act(c, kind, x, foot, t, s, col, prog, beats=()):
    """Draw one panel's action with coloured props. prog 0..1 grows the panel's progress prop."""
    nb = sum(1 for b in beats if t >= b)
    acc = _acc()
    if kind == "pushup":
        c.figure(x, nv.pushup(t), s=s, col=col, foot_y=foot)
        P.calendar(c, x - 230, foot, 0.7, f"x{5 + nb * 5}", acc)
    elif kind == "lift":
        k = 0.5 + 0.5 * math.sin(t * 4)
        Pz = dict(nv.BASE, la1=-(110 + 55 * k), la2=-(60 * (1 - k)), ra1=110 + 55 * k, ra2=60 * (1 - k),
                  ll1=-14, rl1=14)
        info = c.figure(x, Pz, s=s, col=col, foot_y=foot)
        P.barbell(c, info["hands"]["l"], info["hands"]["r"], s, acc)
        for i in range(min(nb, 5)):
            P.dumbbell(c, x - 220, foot - i * 22, 0.7 * P.pop(t, beats[i]) + 0.01, [acc, _acc2()][i % 2])
    elif kind == "read":
        info = c.figure(x, dict(sit(t), la1=60, la2=50, ra1=70, ra2=45, head=-18), s=s, col=col, foot_y=foot)
        hx, hy = info["hands"]["r"]
        P.open_book(c, hx, hy + 26, 0.7, t)
        P.book_stack(c, x - 190, foot, 1 + nb, 0.8, seed=1)
        P.bulb(c, x + 170, foot - 120, 0.6, prog)
    elif kind in ("run", "walk"):
        c.figure(x, walk(t, 12, 40, 12) if kind == "run" else walk(t), s=s, col=col, foot_y=foot)
        sp = 420 if kind == "run" else 200
        for i in range(5):
            xx = (W - (t * sp + i * 230) % (W + 200))
            c.d.line([(xx, foot + 6), (xx + 60, foot + 6)], fill=acc, width=3)
        P.flag(c, x + 300, foot, 0.6, t, acc)
        P.water_bottle(c, x - 260, foot, 0.7)
    elif kind == "save":
        k = 0.5 + 0.5 * math.sin(t * 5)
        c.figure(x, nv.bend(t, 0.3 + 0.3 * k), s=s, col=col, foot_y=foot)
        P.coin_stack(c, x + 110, foot, 2 + int(prog * 12), 0.9)
        P.money_bag(c, x + 230, foot, 0.55, prog)
        if prog >= 1:
            c.glow(x + 230, foot - 60, 90, GOLD, 0.5)
    elif kind == "meditate":
        k = 0.5 + 0.5 * math.sin(t * 2)
        c.glow(x, foot - 120, 120, _acc2(), 0.25 + 0.25 * k)
        c.figure(x, dict(sit(t), ll1=70, ll2=-140, rl1=75, rl2=-140, la1=40, la2=-30, ra1=50, ra2=-30),
                 s=s, col=col, foot_y=foot)
        P.heart(c, x + 200, foot - 60, 0.5, k, (240, 120, 160))
    elif kind == "snooze":
        P.bed(c, x, foot, 0.85)
        c.figure(x, nv.lie(t), s=s, col=col, foot_y=foot - 44)
        P.alarm(c, x + 210, foot, 0.7, t, ring=(t * 1.2) % 1 < 0.5)
        for i in range(3):
            ph = (t * 0.5 + i / 3) % 1
            c.text("Z", x + 110 + ph * 60, foot - 150 - ph * 110, 22, (150, 160, 200), world=True)
    elif kind == "scroll":
        info = c.figure(x, _sit_phone(t), s=s, col=col, foot_y=foot)
        hx, hy = info["hands"]["l"]
        P.phone(c, hx, hy + 18, 0.6, t, True, badge=2 + nb * 11)
        for i in range(min(nb, 3)):
            sc = 0.7 * P.pop(t, beats[i])
            if sc > 0:
                P.notif(c, x + 190, foot - 40 - i * 40, sc, ["LIKE", "REEL", "PING"][i])
    elif kind == "spend":
        c.figure(x, stand(t), s=s, col=col, foot_y=foot)
        cols = [_acc2(), (90, 170, 255), (240, 120, 60), (170, 100, 220)]
        for i in range(min(nb, 4)):
            sc = 0.6 * P.pop(t, beats[i])
            if sc > 0:
                P.shop_bag(c, x + 110 + i * 50, foot, sc, cols[i % 4])
        P.coin_stack(c, x - 160, foot, max(0, 12 - int(prog * 12)), 0.9)
        fall = (t * 1.3) % 1
        P.cash(c, x - 230, foot - 140 + fall * 60, 0.6, fall * 4)
    elif kind == "laptop":
        info = c.figure(x, dict(sit(t), la1=75, la2=-20, ra1=85, ra2=-25, head=-12), s=s, col=col, foot_y=foot)
        P.laptop(c, x + 120 * s, foot, 0.8, t)
        P.progress_bar(c, x, foot - 260 * s, 200, prog, acc)
        P.rocket(c, x - 230, foot, 0.5 + 0.2 * prog, t, flame=prog >= 1)
    elif kind == "game":
        P.tv(c, x + 230, foot, 0.6, t)
        P.couch(c, x - 20, foot, 0.6)
        info = c.figure(x - 20, dict(sit(t), lean=-14, head=-6, la1=40, la2=60, ra1=50, ra2=50), s=s, col=col,
                        foot_y=foot - 30)
        P.controller(c, info["hands"]["r"][0], info["hands"]["r"][1] + 10, 0.5)
    elif kind == "salad":
        info = c.figure(x, dict(stand(t), ra1=70, ra2=70), s=s, col=col, foot_y=foot)
        hx, hy = info["hands"]["r"]
        P.salad(c, hx + 10, hy + 20, 0.6)
        P.heart(c, x - 200, foot - 40, 0.5 + 0.3 * prog, 0.5 + 0.5 * math.sin(t * 6), (90, 210, 130))
        P.water_bottle(c, x + 190, foot, 0.7)
    elif kind == "junk":
        P.couch(c, x, foot, 0.6, (90, 70, 60))
        c.figure(x, dict(sit(t), lean=-14, head=-6), s=s, col=col, foot_y=foot - 30)
        for i in range(min(nb, 6)):
            sc = 0.55 * P.pop(t, beats[i])
            if sc > 0:
                (P.pizza if i % 2 == 0 else P.soda)(c, x + 170 + (i % 3) * 40, foot - (i // 3) * 36, sc)
    elif kind == "plant":
        c.figure(x - 80, dict(nv.BASE, ra1=80, ra2=20, la1=-10), s=s, col=col, foot_y=foot)
        pour = 1.0 if any(0 <= t - b < 0.7 for b in beats) else 0.0
        P.watering_can(c, x - 20, foot - 120, 0.6, pour, t)
        P.plant(c, x + 110, foot, 0.8, 0.15 + 0.85 * prog, 0.0, t)
    elif kind == "neglect":
        info = c.figure(x - 60, _sit_phone(t), s=s, col=col, foot_y=foot)
        hx, hy = info["hands"]["l"]
        P.phone(c, hx, hy + 18, 0.5, t, True)
        P.plant(c, x + 120, foot, 0.8, 0.4, wilt=prog, t=t)
    else:  # couch
        P.couch(c, x - 10, foot, 0.65)
        P.tv(c, x + 240, foot, 0.55, t)
        c.figure(x - 20, dict(sit(t), lean=-14, head=-6), s=s, col=col, foot_y=foot - 32)
        P.pizza(c, x - 230, foot, 0.6)


def _top_reflection(c):
    hgt = 150
    band = c.img.crop((0, TF - hgt, W, TF)).transpose(Image.FLIP_TOP_BOTTOM)
    band = band.resize((W // 3, hgt // 3)).resize((W, hgt))
    g = Image.linear_gradient("L").resize((W, hgt)).point(lambda v: int(80 * (1 - v / 255) ** 1.6))
    c.img.paste(band, (0, TF), g)
    c.d.line([(60, TF), (W - 60, TF)], fill=nv.mix(_acc(), (0, 0, 0), 0.5), width=2)


def draw_split(c, t, spec):
    dur = spec["dur"]
    res = 0.7 * dur
    k = clamp(t / res)
    lit = clamp((t - res) / 0.4)
    s = 0.8
    xt = _X(spec, 520)
    beats = _beats(dur, 0.6, 1.1, 0.68)
    # top panel (the good choice)
    _spot_at(c, xt, TF, 380, 280, 0.85, nv.mix(_acc(), GOLD, lit))
    if lit > 0:
        c.glow(xt, TF - 120, 190, GOLD, 0.4 * lit)
    _act(c, spec["ta"], xt, TF, t, s, WHITE, k, beats)
    _top_reflection(c)
    # bottom panel on the main floor (the easy choice)
    c.spot(xt, 260, strength=0.55)
    _act(c, spec["ba"], xt, FLOOR, t, s, GREY if t >= res else (190, 190, 196), k, beats)
    if t >= res:
        sc = 0.8 * P.pop(t, res + 0.4)
        if sc > 0:
            P.rain_cloud(c, xt + (-250 if spec.get("flip") else 250), FLOOR - 190, 0.75 * sc, t)
        for i, (dx, dy) in enumerate(((-200, -200), (210, -260), (-120, -330), (180, -120))):
            if t > res + 0.15 + i * 0.12:
                P.sparkle(c, xt + dx, TF + dy, 1.1, t, GOLD2 if i % 2 else _acc())
    # labels + counter (accent coloured, pulses on each tick)
    _label(c, spec["tl"], W / 2, 370, spec["rt"] if t >= res else None, sub_color=GOLD, color=_acc(), px=30)
    tick = any(0 <= t - b < 0.15 for b in beats)
    c.text(_counter(spec["ck"], k, 0), W / 2, 830 - (6 if tick else 0), 60 if tick else 56,
           GOLD if t >= res else WHITE)
    _label(c, spec["bl"], W / 2, 950, spec["rb"] if t >= res else None, sub_color=RED, color=_acc2(), px=26)


def events_split(spec):
    dur = spec["dur"]
    res = 0.7 * dur
    beats = _beats(dur, 0.6, 1.1, 0.68)
    ev = [(b, "pop", 0.55) for b in beats] + [(b + 0.05, "thud", 0.35) for b in beats]
    ev += [(res, "riser", 0.6), (res, "impact", 0.6), (res + 0.02, "flash", 0.9), (res + 0.12, "chime", 1.0),
           (res + 0.45, "rumble", 0.45), (res + 0.6, "heartbeat", 0.45), (res + 0.3, "pop", 0.5)]
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
    bank = DUEL + DUEL2
    variants = sys.argv[1:] or ["stack", "dig", "climb", "money", "gym", "read", "plant"]
    ts = [0.08, 0.3, 0.5, 0.66, 0.78, 0.95]
    rows = []
    for vi, var in enumerate(v for v in variants if v != "split"):
        i = next(j for j, row in enumerate(bank) if row[2] == var)
        sp = make_duel(rnd, used)
        a, b, vr, top, punch, cap, ig, topic, ua, ub = bank[i]
        sp.update(a=a, b=b, variant=vr, top=top, punch=punch, ua=ua, ub=ub, flip=vi % 2 == 1)
        rows.append(sp)
    if rows:
        sheet = Image.new("RGB", (270 * len(ts), 480 * len(rows)))
        for r, sp in enumerate(rows):
            if hasattr(nv, "set_theme"):
                nv.set_theme(r)
            for ci, f in enumerate(ts):
                sheet.paste(_frame(sp, f * sp["dur"]).resize((270, 480)), (ci * 270, r * 480))
        sheet.save("out/fa_duel.png")
        print("duel", [r_["variant"] for r_ in rows])
    srows = []
    for ta in ("pushup", "read", "save", "laptop", "salad", "plant"):
        i = next(j for j, row in enumerate(SPLIT + SPLIT2) if row[1] == ta)
        sp = make_split(rnd, used)
        tl, ta_, bl, ba, ck, rt, rb, punch, cap, ig, topic = (SPLIT + SPLIT2)[i]
        sp.update(tl=tl, ta=ta_, bl=bl, ba=ba, ck=ck, rt=rt, rb=rb, punch=punch)
        srows.append(sp)
    sheet = Image.new("RGB", (270 * len(ts), 480 * len(srows)))
    for r, sp in enumerate(srows):
        if hasattr(nv, "set_theme"):
            nv.set_theme(r + 3)
        for ci, f in enumerate(ts):
            sheet.paste(_frame(sp, f * sp["dur"]).resize((270, 480)), (ci * 270, r * 480))
    sheet.save("out/fa_split.png")
    print("split", [(r_["ta"], r_["ba"]) for r_ in srows])
