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
import time
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
SLOTS = [(6, 0), (18, 0)]
STORY_HOUR = 6
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "35"))
MAX_QUEUE = int(os.environ.get("MAX_QUEUE", "100000"))  # no practical limit
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


FORMAT_WEIGHTS = {"lifeline": 1}  # grindhallway-style night-room stories


def formats():
    import formats_a
    import formats_b
    import formats_c
    import formats_g
    return {**formats_a.FORMATS, **formats_b.FORMATS, **formats_c.FORMATS, **formats_g.FORMATS}


def _script_key(spec):
    return "script|" + (spec.get("script_text") or (str(spec.get("top")) + "|" + str(spec.get("punch"))))


def make_spec(F, used, rnd, last):
    """Weighted format choice; a format whose scripts are all used is skipped, so no script repeats."""
    import hooks
    import nv
    names = [n for n in FORMAT_WEIGHTS if n in F and n != last] or [n for n in FORMAT_WEIGHTS if n in F]
    spec = None
    while names:
        name = rnd.choices(names, weights=[FORMAT_WEIGHTS.get(n, 1) for n in names])[0]
        for _try in range(40):
            snap = set(used)
            cand = F[name]["make"](rnd, used)
            if _script_key(cand) not in used:
                spec = cand
                break
            used.clear()
            used.update(snap)
        if spec:
            break
        names.remove(name)
    if spec is None:  # every bank exhausted: allow repeats rather than stop posting
        name = rnd.choice(list(F))
        spec = F[name]["make"](rnd, used)
    used.add(_script_key(spec))
    spec["format"] = name
    spec["hook"], spec["hook_style"] = hooks.pick(rnd, used, spec.get("topic"))
    import growth_copy as G
    pool = G.OPENING_HOOKS.get(spec.get("topic"), G.OPENING_HOOKS["growth"])
    fresh = [h for h in pool if "open|" + h not in used] or pool
    spec["open_hook"] = rnd.choice(fresh)
    used.add("open|" + spec["open_hook"])
    spec["follow_cta"] = rnd.choice(G.FOLLOW_CTAS)
    last_theme = getattr(make_spec, "last_theme", None)
    spec["theme"] = rnd.choice([th["name"] for th in nv.THEMES if th["name"] != last_theme])
    make_spec.last_theme = spec["theme"]
    return spec


# 6 AM = start-the-day energy, 6 PM = end-of-day reflection
SERIES_START = datetime(2026, 11, 6, tzinfo=IST).date()  # "Day N of becoming 1% better"
MORNING_TOPICS = {"discipline", "habits", "focus", "growth"}


def topic_of(e):
    if e.get("topic"):
        return e["topic"]
    import seo
    for name, (kw, _) in seo.NV_TOPIC.items():
        if kw in e.get("caption", ""):
            return name
    return None


def reslot(q):
    """Keep the same time slots but give 6 AM slots to morning topics and 6 PM slots to evening topics."""
    if not q:
        return q
    slots = sorted(e["slot"] for e in q)
    am = [e for e in q if topic_of(e) in MORNING_TOPICS]
    pm = [e for e in q if topic_of(e) not in MORNING_TOPICS]
    for sl in slots:
        want_am = datetime.fromisoformat(sl).hour < 12
        src = am if (want_am and am) or not pm else pm
        src.pop(0)["slot"] = sl
    q.sort(key=lambda e: e["slot"])
    return q


def batch():
    import nv
    import seo
    F = formats()
    s, q = state(), reslot(load(QUEUE, []))
    today = datetime.now(IST).date().isoformat()
    automatic = os.environ.get("GITHUB_EVENT_NAME") == "schedule" or os.environ.get("AUTO") == "1"
    if automatic and s.get("last_batch") == today:
        print("today's batch is already done; this backup run has nothing to do")
        return
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
        slot = next_slot(after)
        morning = slot.hour < 12
        for _try in range(60):  # pick a script whose topic fits the time of day
            snapshot = set(used)
            spec = make_spec(F, used, rnd, last)
            if (spec.get("topic") in MORNING_TOPICS) == morning:
                break
            used.clear()
            used.update(snapshot)
        last = spec["format"]
        spec["day"] = (slot.date() - SERIES_START).days + 1
        spec["follow_cta"] = spec.get("follow_cta", "").replace("{next}", str(spec["day"] + 1))
        s["counter"] += 1
        name = f"reel_{s['counter']:05d}.mp4"
        path = os.path.join("out", name)
        fmt = F[spec["format"]]
        thumb = nv.render(spec, fmt["draw"], fmt["events"](spec), path, seed=s["counter"])
        if not os.environ.get("NO_UPLOAD"):
            gh("release", "upload", RELEASE, path, "--clobber")
        after = slot
        q.append({"file": name, "slot": after.isoformat(), "template": spec["format"], "key": spec["key"],
                  "topic": spec.get("topic"), "thumb": thumb, "caption": seo.caption_v2(spec)})
        s["used"] = sorted(used)
        save(QUEUE, q)
        save(STATE, s)
        print(f"{name}  {spec['format']:10s}  {after:%d %b %H:%M} IST  {spec.get('top')} / {spec.get('punch')}")
    s["last_batch"] = today
    save(STATE, s)


def post():
    from instagram import IG
    s, q = state(), reslot(load(QUEUE, []))
    now = datetime.now(IST)
    due = [e for e in q if datetime.fromisoformat(e["slot"]) <= now + timedelta(minutes=45)]
    if not due:
        print("nothing due now; queue size", len(q))
        return
    e = min(due, key=lambda x: x["slot"])
    os.makedirs("out", exist_ok=True)
    gh("release", "download", RELEASE, "-p", e["file"], "-D", "out", "--clobber")
    # The run starts early on purpose (GitHub cron is often late): wait for the exact slot time.
    wait = (datetime.fromisoformat(e["slot"]) - datetime.now(IST)).total_seconds() - 60  # upload takes ~1 min
    if wait > 0:
        print(f"waiting {int(wait)} s for the {e['slot']} slot")
        time.sleep(wait)
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


def stats():
    """Print views/reach/likes for the latest posted reels and the account."""
    from instagram import IG
    ig = IG(os.environ["IG_USER_ID"], os.environ["IG_TOKEN"])
    acc = ig.get(ig.uid, fields="username,followers_count,media_count")
    print(f"@{acc.get('username')}  followers={acc.get('followers_count')}  posts={acc.get('media_count')}")
    media = ig.get(f"{ig.uid}/media", fields="id,caption,timestamp,like_count,comments_count,media_product_type",
                   limit=10).get("data", [])
    for m in media:
        row = {"likes": m.get("like_count"), "comments": m.get("comments_count")}
        for metric in ("views", "reach", "saved", "shares"):
            try:
                d = ig.get(f"{m['id']}/insights", metric=metric).get("data", [])
                row[metric] = d[0]["values"][0]["value"] if d else None
            except Exception as ex:  # some metrics are not available for every media type
                row[metric] = "n/a"
        first = (m.get("caption") or "").splitlines()[0][:50] if m.get("caption") else ""
        print(m.get("timestamp", "")[:16], m.get("media_product_type"), row, "|", first)


def comments():
    from instagram import IG
    s = state()
    n = IG(os.environ["IG_USER_ID"], os.environ["IG_TOKEN"]).reply_to_comments(s["replied"], REPLIES)
    s["replied"] = s["replied"][-3000:]
    save(STATE, s)
    print(f"replied to {n} comments")


def preview(n):
    import nv
    import seo
    F, used, rnd, last = formats(), set(), random.Random(42), None
    os.makedirs("out", exist_ok=True)
    for i in range(n):
        spec = make_spec(F, used, rnd, last)
        last = spec["format"]
        fmt = F[spec["format"]]
        nv.render(spec, fmt["draw"], fmt["events"](spec), f"out/preview_{i}.mp4", seed=i)
        print(f"--- preview_{i}.mp4 [{spec['format']}]")
        print(seo.caption_nv(spec))
        print()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "post"
    if cmd == "batch":
        batch()
    elif cmd == "comments":
        comments()
    elif cmd == "stats":
        stats()
    elif cmd == "preview":
        preview(int(sys.argv[2]) if len(sys.argv) > 2 else 3)
    else:
        post()
