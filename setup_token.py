"""One-time setup: turn the short Graph Explorer token into a never-expiring Page token
and save it as GitHub secrets. You paste two things; nothing is printed or written to disk.

Run:  py setup_token.py
"""
import getpass
import subprocess
import sys

import requests

APP_ID = "1762325914839059"
REPO = sys.argv[1] if len(sys.argv) > 1 else "dailyrise-reels"
G = "https://graph.facebook.com/v24.0"


def die(msg):
    print("ERROR:", msg)
    sys.exit(1)


short = getpass.getpass("1) Graph Explorer token paste karo (dikhega nahi), Enter: ").strip()
secret = getpass.getpass("2) App Secret paste karo (App settings > Basic), Enter: ").strip()
if not short or not secret:
    die("dono cheezein chahiye")

r = requests.get(f"{G}/oauth/access_token", params={
    "grant_type": "fb_exchange_token", "client_id": APP_ID, "client_secret": secret,
    "fb_exchange_token": short}, timeout=30)
if r.status_code != 200:
    die(f"token exchange fail: {r.text[:300]}")
long_user = r.json()["access_token"]

r = requests.get(f"{G}/me/accounts", params={
    "fields": "name,access_token,instagram_business_account{id,username}",
    "access_token": long_user}, timeout=30)
if r.status_code != 200:
    die(f"pages fetch fail: {r.text[:300]}")
pages = [p for p in r.json().get("data", []) if p.get("instagram_business_account")]
if not pages:
    die("koi Facebook Page Instagram se linked nahi mila")
page = pages[0]
ig = page["instagram_business_account"]

r = requests.get(f"{G}/debug_token", params={"input_token": page["access_token"],
                                              "access_token": f"{APP_ID}|{secret}"}, timeout=30)
exp = r.json().get("data", {}).get("expires_at", "?") if r.ok else "?"

for name, val in (("IG_USER_ID", ig["id"]), ("IG_TOKEN", page["access_token"])):
    p = subprocess.run(["gh", "secret", "set", name, "--repo", REPO], input=val, text=True,
                       capture_output=True)
    if p.returncode != 0:
        die(f"gh secret set {name} fail: {p.stderr[:300]}")

print(f"Done. Instagram: @{ig['username']} | Page: {page['name']} | token expiry: "
      f"{'never' if exp == 0 else exp}")
print("GitHub secrets IG_USER_ID aur IG_TOKEN save ho gaye.")
