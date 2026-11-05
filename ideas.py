"""Endless reel ideas: combines templates with label banks. No AI API needed.

new_reel(used) returns a reel dict whose key is not in `used` (a set of strings).
"""
import random

DOOR = {
    "goals": ["DREAM", "GYM", "SUCCESS", "FUTURE", "BETTER YOU", "FREEDOM", "CAREER", "GOALS", "PEACE", "BUSINESS",
              "SIX PACK", "TOPPER", "FIRST CRORE", "NEW LIFE", "PURPOSE"],
    "anchors": ["FEAR", "LAZINESS", "PHONE", "EXCUSES", "COMFORT", "DOUBT", "PAST", "EGO", "OVERTHINKING",
                "PROCRASTINATION", "BAD HABITS", "TOXIC FRIENDS", "INSTAGRAM", "NETFLIX", "SLEEP"],
    "captions": ["What's holding you back?", "The only thing stopping you", "Cut the rope.",
                 "It was never that far", "You know what to do", "Break free."],
    "ig": ["{a} ki rassi kaato, {g} ka darwaza khula hai.", "{g} door nahi hai. Bas {a} ne pakad rakha hai.",
           "Jis din {a} chhoda, us din {g} paas aa gaya."],
}
BOULDER = {
    "sets": [["MON", "WED", "FRI"], ["CH 1", "CH 7", "CH 15"], ["DAY 1", "DAY 30", "DAY 90"], ["IDEA", "WORK", "WORK"],
             ["JAN", "JUN", "DEC"], ["0", "100", "1K"], ["LEVEL 1", "LEVEL 5", "LEVEL 10"], ["5AM", "9AM", "6PM"],
             ["SEM 1", "SEM 4", "SEM 8"], ["1 KM", "5 KM", "10 KM"]],
    "captions": ["What a week feels like...", "Nobody sees this part", "Keep pushing.", "This is the real grind",
                 "Every single day", "It gets heavy. Don't stop."],
    "ig": ["Patthar bhaari hai, par tum usse zyada mazboot ho.", "Ye wala hissa koi nahi dekhta. Phir bhi dhakelte raho.",
           "Roz thoda aage. Bas itna hi kaafi hai."],
}
CROWD = {
    "pairs": [["EVERYONE", "YOU"], ["SCROLLING", "BUILDING"], ["EXCUSES", "DISCIPLINE"], ["AVERAGE", "1%"],
              ["COMPLAINING", "WORKING"], ["PARTYING", "LEARNING"], ["COPYING", "CREATING"], ["SLEEPING", "GRINDING"],
              ["WAITING", "STARTING"], ["WISHING", "DOING"]],
    "captions": ["The 1% walk the other way", "Don't follow the crowd", "Walking alone is not losing",
                 "2AM. Everyone is scrolling.", "Be the one who goes against it", "Different direction. Different life."],
    "ig": ["Sab {c} mein busy. Tum {y} pe focus karo.", "Bheed ke saath chaloge to bheed jaise hi banoge.",
           "Ulti disha mein chalna mushkil hai. Isliye kam log chalte hain."],
}
STAIRS = {
    "sets": [["1%", "1%", "1%", "1%", "37X"], ["FAIL", "TRY", "FAIL", "TRY", "WIN"],
             ["DAY 1", "DAY 90", "DAY 180", "DAY 270", "DAY 365"], ["READ", "MOVE", "LEARN", "BUILD", "WIN"],
             ["WAKE", "WORK", "REST", "REPEAT", "RESULT"], ["SAVE", "LEARN", "INVEST", "GROW", "FREE"],
             ["START", "STRUGGLE", "LEARN", "GROW", "TOP"], ["SMALL", "STEADY", "STRONG", "SURE", "WIN"]],
    "captions": ["1% better every day", "How success actually looks", "Small steps. Every day.",
                 "One step at a time", "Nobody skips the stairs", "The climb is the reward"],
    "ig": ["Roz ka chhota kadam hi badi seedhi banata hai.", "Seedhi koi skip nahi karta. Ek ek step.",
           "Roz 1% better = saal ke end mein 37 guna better."],
}
COMPARE = [
    ("Same 24 hours", "YOU AT 6AM", "sleep", "6:00", "HIM AT 6AM", "run", "6:00"),
    ("Free time", "MOST PEOPLE", "phone", None, "THE 1%", "read", None),
    ("After failing once", "QUITTER", "sad", None, "WINNER", "lift", None),
    ("Monday morning", "THEM", "sad", None, "YOU", "celebrate", None),
    ("11PM", "YOU", "phone", "11:00", "YOUR FUTURE SELF", "sleep", "11:00"),
    ("Sunday", "MOST PEOPLE", "sleep", None, "THE 1%", "lift", None),
    ("Exam season", "LAST NIGHT", "phone", "2:00", "EVERY NIGHT", "read", "9:00"),
    ("Bad day", "WEAK MIND", "sad", None, "STRONG MIND", "walk", None),
    ("Rainy morning", "EXCUSE", "sleep", "5:30", "DISCIPLINE", "run", "5:30"),
    ("Lunch break", "THEM", "phone", None, "YOU", "read", None),
]
CARRY = {
    "loads": ["OVERTHINKING", "PAST", "LOG KYA KAHENGE", "EGO", "REGRET", "STRESS", "GRUDGES", "COMPARISON",
              "FEAR", "FAILURE", "TOXIC PEOPLE", "SELF DOUBT"],
    "captions": ["Let it go.", "Stop carrying this", "Heavy? Drop it.", "You don't need this anymore",
                 "Lighter. Faster. Free."],
    "ig": ["{l} ka bojh utaaro, phir dekho kitna tez bhaagte ho.", "{l} uthake future tak nahi pahunch sakte.",
           "Kuch cheezein chhodne se hi aage badhte hain."],
}
LEAP = {
    "pairs": [["COMFORT", "GROWTH"], ["SAFE JOB", "DREAM"], ["FEAR", "FREEDOM"], ["DOUBT", "BELIEF"],
              ["TODAY", "TOMORROW"], ["STUDENT", "BUILDER"], ["9 TO 5", "OWN THING"], ["SHY", "CONFIDENT"],
              ["THINKING", "DOING"], ["OLD ME", "NEW ME"]],
    "captions": ["Growth starts where comfort ends", "One jump changes everything", "Scared? Jump anyway.",
                 "Bet on yourself", "The gap is smaller than it looks"],
    "ig": ["{f} se {t} tak, bas ek chhalaang ka fasla.", "Dar lagega. Chhalaang phir bhi lagao.",
           "Safe rehna bhi ek risk hai. Kab tak rukoge?"],
}


def _one(rnd):
    kind = rnd.choice(["door", "boulder", "crowd", "stairs", "compare", "carry", "leap"])
    if kind == "door":
        g, a = rnd.choice(DOOR["goals"]), rnd.choice(DOOR["anchors"])
        return f"door|{g}|{a}", dict(template="door", goal=g, anchor=a, dur=11,
                                      caption=rnd.choice(DOOR["captions"]),
                                      ig=rnd.choice(DOOR["ig"]).format(a=a.title(), g=g.title()))
    if kind == "boulder":
        labels = rnd.choice(BOULDER["sets"])
        cap = rnd.choice(BOULDER["captions"])
        return f"boulder|{'/'.join(labels)}|{cap}", dict(template="boulder", labels=labels, caption=cap, dur=10,
                                                          ig=rnd.choice(BOULDER["ig"]))
    if kind == "crowd":
        c, y = rnd.choice(CROWD["pairs"])
        cap = rnd.choice(CROWD["captions"])
        return f"crowd|{c}|{cap}", dict(template="crowd", crowd=c, you=y, caption=cap, dur=10,
                                        ig=rnd.choice(CROWD["ig"]).format(c=c.lower(), y=y.lower()))
    if kind == "stairs":
        labels = rnd.choice(STAIRS["sets"])
        cap = rnd.choice(STAIRS["captions"])
        return f"stairs|{'/'.join(labels)}|{cap}", dict(template="stairs", labels=labels, caption=cap, dur=11,
                                                         ig=rnd.choice(STAIRS["ig"]))
    if kind == "compare":
        cap, a, ap, at, b, bp, bt = rnd.choice(COMPARE)
        return f"compare|{a}|{b}|{cap}", dict(template="compare", caption=cap, a=a, a_pose=ap, a_time=at, b=b,
                                              b_pose=bp, b_time=bt, dur=9,
                                              ig="Same din, same ghante. Farak sirf choice ka hai.")
    if kind == "carry":
        load = rnd.choice(CARRY["loads"])
        cap = rnd.choice(CARRY["captions"])
        return f"carry|{load}|{cap}", dict(template="carry", load=load, caption=cap, dur=11,
                                           ig=rnd.choice(CARRY["ig"]).format(l=load.title()))
    f, t = rnd.choice(LEAP["pairs"])
    cap = rnd.choice(LEAP["captions"])
    return f"leap|{f}|{t}|{cap}", dict(template="leap", **{"from": f, "to": t}, caption=cap, dur=10,
                                       ig=rnd.choice(LEAP["ig"]).format(f=f.title(), t=t.title()))


def new_reel(used, rnd=None, last_template=None):
    rnd = rnd or random.Random()
    for _ in range(500):
        key, reel = _one(rnd)
        if key not in used and reel["template"] != last_template:
            used.add(key)
            reel["key"] = key
            return reel
    raise RuntimeError("idea bank exhausted, add more labels in ideas.py")
