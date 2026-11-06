"""SEO captions for Instagram reels.

Instagram search reads the caption text, so the first line and body carry the keywords people
search for (motivation in hindi, discipline, self improvement...). Hashtags are kept to 5,
which is what Instagram currently recommends, mixed from a topic pool and a general pool.
"""
import random

TOPIC = {
    "door": {"kw": "fear, self doubt aur procrastination se bahar nikalne ki motivation",
             "tags": ["#overcomefear", "#procrastination", "#selfdoubt", "#dreambig", "#breakfree"]},
    "boulder": {"kw": "hard work, consistency aur grind ki real story",
                "tags": ["#hardwork", "#grindmode", "#consistency", "#neverquit", "#struggle"]},
    "crowd": {"kw": "bheed se alag sochne wale 1% logon ka mindset",
              "tags": ["#mindset", "#be different", "#focus", "#1percent", "#successhabits"]},
    "stairs": {"kw": "1% better every day, chhote kadam aur daily habits",
               "tags": ["#1percentbetter", "#dailyhabits", "#atomichabits", "#growthmindset", "#selfgrowth"]},
    "compare": {"kw": "discipline vs excuses, morning routine aur time management",
                "tags": ["#discipline", "#morningroutine", "#timemanagement", "#productivity", "#routine"]},
    "carry": {"kw": "overthinking, stress aur past ko chhodne ki motivation",
              "tags": ["#overthinking", "#letitgo", "#mentalhealth", "#mentalpeace", "#healing"]},
    "leap": {"kw": "comfort zone se bahar nikal kar risk lene ki motivation",
             "tags": ["#comfortzone", "#takerisks", "#believeinyourself", "#growth", "#courage"]},
}
GENERAL = ["#motivation", "#dailymotivation", "#motivationalquotes", "#selfimprovement", "#stickmananimation",
           "#motivationalreels", "#successmindset", "#reelsindia"]
HOOKS = ["{c}", "{c} 🔥", "{c}... 💭", "{c} 👀"]
CTAS = [
    "💾 Save karo, jab motivation kam ho tab dekhna.",
    "📤 Us dost ko bhejo jise aaj ye sunna chahiye.",
    "💬 Comment mein likho: aaj ka 1% kya hai?",
]


def caption(reel, rnd=None):
    rnd = rnd or random.Random(reel.get("key", ""))
    topic = TOPIC.get(reel["template"], TOPIC["stairs"])
    first = (reel.get("hook") or reel["caption"]).replace("*", "").rstrip(".")
    hook = rnd.choice(HOOKS).format(c=first)
    tags = [t.replace(" ", "") for t in rnd.sample(topic["tags"], 2)]
    tags += rnd.sample(GENERAL[:5], 2) + [rnd.choice(GENERAL[5:])]
    lines = [
        hook,
        "",
        reel["ig"],
        "",
        f"Daily motivation in Hindi: {topic['kw']}. Self improvement, discipline aur success mindset "
        f"ke liye roz ek naya stickman reel.",
        "",
        rnd.choice(CTAS),
        "🔁 Share karo us dost ko jise ye sunna chahiye.",
        "👉 Follow @dailyrise.reels — roz 1% better.",
        "",
        " ".join(tags),
    ]
    return "\n".join(lines)


# ---------------- captions for the minimal (nv) formats ----------------
NV_TOPIC = {
    "discipline": ("discipline, self control and showing up every day",
                   ["#discipline", "#selfdiscipline", "#consistency", "#nevergiveup"]),
    "habits": ("daily habits, small steps and getting 1% better every day",
               ["#dailyhabits", "#atomichabits", "#1percentbetter", "#habits"]),
    "mindset": ("success mindset: change your thoughts, change your life",
                ["#mindset", "#growthmindset", "#mindsetshift", "#successmindset"]),
    "money": ("money, time and the real value of life",
              ["#moneymindset", "#financialfreedom", "#wealthmindset", "#lifelessons"]),
    "focus": ("focus, phone addiction and beating distraction",
              ["#focus", "#deepwork", "#productivity", "#digitaldetox"]),
    "time": ("the value of time and beating procrastination",
             ["#timemanagement", "#procrastination", "#timeiseverything", "#productivity"]),
    "fear": ("fear, overthinking and leaving your comfort zone",
             ["#overthinking", "#comfortzone", "#courage", "#takeaction"]),
    "growth": ("self improvement and becoming a little better every day",
               ["#selfimprovement", "#personalgrowth", "#selfgrowth", "#levelup"]),
}
NV_GENERAL = ["#motivation", "#dailymotivation", "#motivationalquotes", "#stickmananimation", "#reelsindia",
              "#motivationalreels", "#wisdom"]


def caption_nv(spec, rnd=None):
    rnd = rnd or random.Random(spec.get("key", ""))
    kw, tags = NV_TOPIC.get(spec.get("topic"), NV_TOPIC["growth"])
    tags = rnd.sample(tags, 2) + rnd.sample(NV_GENERAL[:3], 1) + rnd.sample(NV_GENERAL[3:], 2)
    lines = [
        spec.get("caption_line") or (spec.get("punch") or spec.get("top") or "").capitalize(),
        "",
        spec.get("ig", ""),
        "",
        f"Daily motivation in Hindi: {kw}. Roz ek naya stickman reel, 1% better banne ke liye.",
        "",
        rnd.choice(CTAS),
        "👉 Follow @dailyrise.reels — roz 1% better.",
        "",
        " ".join(tags),
    ]
    out = [l for i, l in enumerate(lines) if l or (i and lines[i - 1])]
    return chr(10).join(out)


def caption_v2(spec, rnd=None):
    """SEO caption: keyword-rich first line, Hinglish line, comment-bait question, series follow CTA, 5 tags."""
    import growth_copy as G
    rnd = rnd or random.Random(spec.get("key", ""))
    topic = spec.get("topic") if spec.get("topic") in G.HASHTAGS else "growth"
    kw = NV_TOPIC.get(topic, NV_TOPIC["growth"])[0]
    kw = "Daily motivation: " + kw if rnd.random() < 0.5 else kw[0].upper() + kw[1:]
    tags = G.HASHTAGS[topic]
    tags = rnd.sample(tags[:2], 1) + rnd.sample(tags[2:6], 2) + rnd.sample(tags[6:], 2)
    title = (spec.get("caption_line") or spec.get("punch") or spec.get("top") or "").strip()
    return rnd.choice(G.CAPTION_TEMPLATES).format(
        kw=kw, title=title, ig=spec.get("ig_en") or spec.get("metaphor") or "", question=rnd.choice(G.QUESTIONS[topic]),
        day=spec.get("day", 1), tags=" ".join(tags))
