"""Reel autopilot.

  python main.py batch     render up to BATCH_SIZE new reels, upload to the "queue" release,
                           and give each the next free slot (06:00 / 18:00 IST)
  python main.py post      post the queued reel whose slot has arrived
  python main.py comments  reply to new comments
  python main.py preview N render N reels into out/ without uploading (local check)
"""
import json
import os
import random
import subprocess
import sys
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
SLOTS = [(6, 0), (18, 0)]
STORY_HOUR = 6
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "20"))
MAX_QUEUE = int(os.environ.get("MAX_QUEUE", "60"))
RELEASE = "queue"
STATE, QUEUE = "state.json", "queue.json"
REPLIES = [
    "Thank you! Roz 1% better 💪",
    "🔥 Keep going, aaj ka 1% done?",
    "Bilkul sahi! Consistency is key 🙌",
    "Shukriya ❤️ Roz naya reel aata hai, follow karte raho",
    "💯 Chhote kadam, badi jeet!",
]


def load(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def save(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def state():
    s = load(STATE, {})
    s.setdefault("used", [])
    s.setdefault("replied", [])
    s.setdefault("posted", [])
    s.setdefault("counter", 0)
    return s


def next_slot(after):
    day = after.date()
    for _ in range(400):
        for hh, mm in SLOTS:
            cand = datetime(day.year, day.month, day.day, hh, mm, tzinfo=IST)
            if cand > after:
                return cand
        day += timedelta(days=1)
    raise RuntimeError("no slot")


def gh(*args):
    subprocess.run(["gh", *args], check=True)


def batch():
    import ideas
    import render
    import seo
    s, q = state(), load(QUEUE, [])
    room = max(0, MAX_QUEUE - len(q))
    n = min(BATCH_SIZE, room)
    print(f"queue has {len(q)}, making {n} new reels (cap {MAX_QUEUE})")
    if n == 0:
        return
    used = set(s["used"])
    rnd = random.Random()
    last = q[-1]["template"] if q else None
    after = max([datetime.fromisoformat(e["slot"]) for e in q] + [datetime.now(IST)])
    os.makedirs("out", exist_ok=True)
    for _ in range(n):
        reel = ideas.new_reel(used, rnd, last)
        last = reel["template"]
        s["counter"] += 1
        name = f"reel_{s['counter']:05d}.mp4"
        path = os.path.join("out", name)
        thumb = render.render(reel, path, seed=s["counter"])
        if not os.environ.get("NO_UPLOAD"):
            gh("release", "upload", RELEASE, path, "--clobber")
        after = next_slot(after)
        q.append({"file": name, "slot": after.isoformat(), "template": reel["template"], "key": reel["key"],
                  "thumb": thumb, "caption": seo.caption(reel)})
        s["used"] = sorted(used)
        save(QUEUE, q)
        save(STATE, s)
        print(f"{name}  {reel['template']:8s}  {after:%d %b %H:%M} IST  {reel['caption']}")


def post():
    from instagram import IG
    s, q = state(), load(QUEUE, [])
    now = datetime.now(IST)
    due = [e for e in q if datetime.fromisoformat(e["slot"]) <= now + timedelta(minutes=45)]
    if not due:
        print("nothing due now; queue size", len(q))
        return
    e = min(due, key=lambda x: x["slot"])
    os.makedirs("out", exist_ok=True)
    gh("release", "download", RELEASE, "-p", e["file"], "-D", "out", "--clobber")
    final = os.path.join("out", e["file"])
    thumb = e.get("thumb")
    if thumb is None:  # older queue entries without a built-in hook cover
        import cover
        final = os.path.join("out", "final_" + e["file"])
        thumb = cover.add_cover(os.path.join("out", e["file"]), e["caption"], final)
    ig = IG(os.environ["IG_USER_ID"], os.environ["IG_TOKEN"])
    media_id = ig.publish_reel(final, e["caption"], thumb_offset=thumb)
    print(f"posted {e['file']} ({e['key']}) -> {media_id}")
    if datetime.fromisoformat(e["slot"]).hour == STORY_HOUR:  # morning reel also goes to the story
        try:
            print("story ->", ig.publish_story(final))
        except Exception as ex:  # a failed story must not undo the reel post
            print("story failed:", ex)
    q.remove(e)
    s["posted"].append({"file": e["file"], "key": e["key"], "media": media_id, "at": now.isoformat()})
    save(QUEUE, q)
    save(STATE, s)
    subprocess.run(["gh", "release", "delete-asset", RELEASE, e["file"], "-y"], check=False)


def comments():
    from instagram import IG
    s = state()
    n = IG(os.environ["IG_USER_ID"], os.environ["IG_TOKEN"]).reply_to_comments(s["replied"], REPLIES)
    s["replied"] = s["replied"][-3000:]
    save(STATE, s)
    print(f"replied to {n} comments")


def preview(n):
    import ideas
    import render
    import seo
    used, rnd, last = set(), random.Random(42), None
    os.makedirs("out", exist_ok=True)
    for i in range(n):
        reel = ideas.new_reel(used, rnd, last)
        last = reel["template"]
        render.render(reel, f"out/preview_{i}.mp4", seed=i)
        print(f"--- preview_{i}.mp4 [{reel['template']}]\n{seo.caption(reel)}\n")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "post"
    if cmd == "batch":
        batch()
    elif cmd == "comments":
        comments()
    elif cmd == "preview":
        preview(int(sys.argv[2]) if len(sys.argv) > 2 else 3)
    else:
        post()
