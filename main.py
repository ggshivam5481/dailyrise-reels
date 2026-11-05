"""Daily job: render the next stickman reel and post it, or reply to comments.

Usage:
  python main.py            render + post next reel
  python main.py --comments reply to new comments
  DRY_RUN=1 python main.py  render only, no posting
"""
import json
import os
import sys

STATE = "state.json"
HASHTAGS = ("#motivation #hindimotivation #selfimprovement #discipline #1percentbetter "
            "#dailyrise #successmindset #motivationalreels #stickman #reelsindia")
REPLIES = [
    "Thank you! Roz 1% better 💪",
    "🔥 Keep going, aaj ka 1% done?",
    "Bilkul sahi! Consistency is key 🙌",
    "Shukriya ❤️ Roz naya reel aata hai, follow karte raho",
    "💯 Chhote kadam, badi jeet!",
]


def load_state():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    return {"next": 0, "replied": [], "posted": []}


def save_state(s):
    s["replied"] = s["replied"][-2000:]
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)


def client():
    from instagram import IG
    return IG(os.environ["IG_USER_ID"], os.environ["IG_TOKEN"])


def caption_for(reel):
    lines = [reel["title"], ""]
    lines += [f"👉 {sc['text']}" for sc in reel["scenes"]]
    lines += ["", "Save karo, share karo, aur roz 1% better bano. Follow @dailyrise.reels", "", HASHTAGS]
    return "\n".join(lines)


def post_next():
    import render
    with open("scripts.json", encoding="utf-8") as f:
        reels = json.load(f)
    s = load_state()
    idx = s["next"] % len(reels)
    reel = reels[idx]
    os.makedirs("out", exist_ok=True)
    path = os.path.join("out", f"reel_{idx:02d}.mp4")
    dur = render.render(reel, path)
    print(f"Rendered reel {idx}: {reel['title']} ({dur:.1f}s)")
    if os.environ.get("DRY_RUN"):
        print("DRY_RUN set, not posting")
        return
    media_id = client().publish_reel(path, caption_for(reel))
    print(f"Posted reel {idx}, media id {media_id}")
    s["next"] = idx + 1
    s["posted"].append({"idx": idx, "media": media_id})
    save_state(s)


def comments():
    s = load_state()
    n = client().reply_to_comments(s["replied"], REPLIES)
    print(f"Replied to {n} comments")
    save_state(s)


if __name__ == "__main__":
    comments() if "--comments" in sys.argv else post_next()
