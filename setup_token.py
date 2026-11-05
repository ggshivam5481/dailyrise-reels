"""One-time setup: save the never-expiring System User token as GitHub secrets.

Token comes from Business Settings > System users > reel-bot > Generate token (expiry: Never).
You paste it once; nothing is printed or written to disk.

Run:  py setup_token.py ggshivam5481/dailyrise-reels
"""
import getpass
import subprocess
import sys

import requests

REPO = sys.argv[1] if len(sys.argv) > 1 else "dailyrise-reels"
IG_USER_ID = "17841415761450869"
G = "https://graph.facebook.com/v24.0"


def die(msg):
    print("ERROR:", msg)
    input("Enter dabao band karne ke liye...")
    sys.exit(1)


token = getpass.getpass("System User token paste karo (dikhega nahi), phir Enter: ").strip()
if not token:
    die("token khaali hai")

r = requests.get(f"{G}/{IG_USER_ID}", params={"fields": "username", "access_token": token}, timeout=30)
if r.status_code != 200:
    die(f"token Instagram tak nahi pahunch raha: {r.text[:300]}")
username = r.json()["username"]

for name, val in (("IG_USER_ID", IG_USER_ID), ("IG_TOKEN", token)):
    p = subprocess.run(["gh", "secret", "set", name, "--repo", REPO], input=val, text=True, capture_output=True)
    if p.returncode != 0:
        die(f"gh secret set {name} fail: {p.stderr[:300]}")

print(f"Done. Instagram @{username} connected. GitHub secrets IG_USER_ID aur IG_TOKEN save ho gaye.")
input("Enter dabao band karne ke liye...")
