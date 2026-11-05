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
GENERAL = ["#motivation", "#hindimotivation", "#motivationinhindi", "#selfimprovement", "#stickmananimation",
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
    hook = rnd.choice(HOOKS).format(c=reel["caption"].rstrip("."))
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
        "👉 Follow @dailyrise.reels for daily 1% better.",
        "",
        " ".join(tags),
    ]
    return "\n".join(lines)
