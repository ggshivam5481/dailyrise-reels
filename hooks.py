"""Opening hooks: a different one for every reel. *word* marks the accent-coloured word."""
import random

# curiosity hooks that work for any topic
ANY = [
    "Nobody talks about *this*.", "You've been doing it *wrong*.", "This took me years to *learn*.",
    "Don't skip *this* one.", "Watch till the *last* second.", "This will change how you *think*.",
    "Most people *fail* right here.", "Save this before you *forget*.", "I wish I knew this at *18*.",
    "The *1%* won't tell you this.", "This is your *sign*.", "You need to hear *this* today.",
    "Pause. *Read* this.", "Be honest with *yourself*.", "This is *uncomfortable*. Watch.",
    "Why nobody *changes*.", "The *hard* truth.", "Your future self is *watching*.",
    "Screenshot *this*.", "Rich minds do *this*.",
]

HAND = {
    "discipline": [
        "Motivation is *lying* to you.", "You don't need *motivation*.", "Discipline is just *this*.",
        "Nobody is coming to *save* you.", "Do it *tired*.", "Your excuses have *excuses*.",
        "This is what discipline *looks* like.", "Stop waiting to *feel* ready.", "Soft life, *hard* future.",
        "The alarm is a *test*.",
    ],
    "habits": [
        "*1%* a day. Watch this.", "Small things. *Huge* results.", "This habit changes *everything*.",
        "Your habits are *voting*.", "Boring days build *big* lives.", "What you repeat, you *become*.",
        "Day 1 or *one day*?", "Tiny steps *win*.", "Nobody sees day *100*.", "This is how habits *compound*.",
    ],
    "mindset": [
        "Read this *twice*.", "This will hit *different*.", "Most people *never* get this.",
        "Your mind is the *cage*.", "The *1%* think like this.", "Change this *one* thought.",
        "Losers and winners *both* see this.", "You are *closer* than you think.", "Stop thinking *small*.",
        "This is why you're *stuck*.",
    ],
    "money": [
        "Rich people know *this*.", "Where does your money *go*?", "Money can't buy *this*.",
        "Spend it or *stack* it?", "Broke habits *cost* more.", "Pay *yourself* first.",
        "Your wallet is *watching*.", "This is how wealth *starts*.", "Time or *money*?", "Saving is *boring*. Good.",
    ],
    "focus": [
        "Your phone is *winning*.", "Put the phone *down*.", "Scrolling is *stealing* this.",
        "Focus is the new *IQ*.", "One hour of *this* beats ten.", "Distraction is *expensive*.",
        "Where did your *day* go?", "Deep work *wins*.", "Notifications *own* you.", "Look up. *Now*.",
    ],
    "time": [
        "You have *less* time than you think.", "Later is a *lie*.", "Tomorrow never *comes*.",
        "How much of *2026* is left?", "Your clock is *ticking*.", "Time is the *real* money.",
        "Stop saying *later*.", "One year from *today*...", "This minute is *gone*.", "Waste time? *Watch this*.",
    ],
    "fear": [
        "Fear is a *liar*.", "Scared? *Good*.", "What if it *works*?", "Overthinking *kills* this.",
        "The comfort zone is a *trap*.", "Jump. *Now*.", "They will *laugh*. Do it anyway.",
        "Failure is *not* the end.", "Fear says *stay*.", "Brave is *not* fearless.",
    ],
    "growth": [
        "Become *unrecognisable*.", "Who are you *becoming*?", "Level up *quietly*.",
        "Grow in *silence*.", "This is *growth*.", "The old you won't *like* this.", "Outgrow *everyone*.",
        "Glow up starts *here*.", "Be *better* than yesterday.", "Watch till the *end*.",
    ],
}

FRAMES = [
    "Stop scrolling if you *{p}*.", "Watch this if you *{p}*.", "This is for you if you *{p}*.",
    "Still {p}? *Watch*.", "If you {p}, *see this*.", "Why do you *{p}*?",
    "You {p}? This is *why*.", "POV: you *{p}*.", "Admit it. You *{p}*.",
    "Do you {p}? *Be honest*.", "The truth if you *{p}*.", "Yes, you. You *{p}*.",
]
PAINS = {
    "discipline": ["skip workouts", "keep snoozing", "quit easily", "start Mondays", "need motivation",
                   "break promises to yourself"],
    "habits": ["break streaks", "start over every week", "can't stay consistent", "plan but never start",
               "give up after day 3"],
    "mindset": ["doubt yourself", "feel stuck", "compare yourself", "think you're too late", "feel average"],
    "money": ["spend on everything", "are always broke", "never save", "buy to impress", "hate budgeting"],
    "focus": ["scroll for hours", "can't focus", "waste your nights", "check your phone first",
              "can't finish anything"],
    "time": ["say later", "waste weekends", "keep delaying", "think you have time", "sleep through mornings"],
    "fear": ["overthink", "fear failure", "wait for the right time", "fear judgement", "never take risks"],
    "growth": ["feel behind", "want to change", "feel lost", "want a glow up", "feel stuck in life"],
}
STYLES = ["pop", "type", "slide", "shake", "flash", "zoom", "glitch", "drop"]


def all_hooks(topic):
    """Topic hooks + universal curiosity hooks + topic pain hooks first, then other topics' hooks."""
    own = list(HAND.get(topic, [])) + ANY + [f.format(p=p) for p in PAINS.get(topic, []) for f in FRAMES]
    rest = [h for t_, hs in HAND.items() if t_ != topic for h in hs]
    return own + rest, len(own)


def pick(rnd, used, topic):
    """Unique hook (never repeats until the whole bank is used), plus an animation style."""
    pool, own = all_hooks(topic or "growth")
    fresh = [h for h in pool if "hook|" + h not in used]
    if not fresh:
        for h in pool:
            used.discard("hook|" + h)
        fresh = pool
    topical = [h for h in fresh if pool.index(h) < own] or fresh
    h = rnd.choice(topical)
    used.add("hook|" + h)
    return h, rnd.choice(STYLES)
