"""Minimal Instagram Graph API client: publish a reel (resumable upload) and reply to comments."""
import os
import time

import requests

VER = os.environ.get("GRAPH_VERSION", "v24.0")
GRAPH = f"https://graph.facebook.com/{VER}"


class IG:
    def __init__(self, user_id, token):
        self.uid = user_id
        self.token = token

    def _check(self, r):
        if r.status_code >= 400:
            raise RuntimeError(f"Graph API {r.status_code}: {r.text[:500]}")
        return r.json()

    def get(self, path, **params):
        params["access_token"] = self.token
        return self._check(requests.get(f"{GRAPH}/{path}", params=params, timeout=60))

    def post(self, path, **data):
        data["access_token"] = self.token
        return self._check(requests.post(f"{GRAPH}/{path}", data=data, timeout=60))

    def username(self):
        return self.get(self.uid, fields="username")["username"]

    def publish_reel(self, video_path, caption, thumb_offset=None):
        c = self.post(f"{self.uid}/media", media_type="REELS", upload_type="resumable",
                      caption=caption, share_to_feed="true",
                      **({"thumb_offset": str(thumb_offset)} if thumb_offset is not None else {}))
        cid = c["id"]
        size = os.path.getsize(video_path)
        with open(video_path, "rb") as f:
            r = requests.post(f"https://rupload.facebook.com/ig-api-upload/{VER}/{cid}",
                              headers={"Authorization": f"OAuth {self.token}", "offset": "0",
                                       "file_size": str(size)}, data=f, timeout=600)
        self._check(r)
        for _ in range(60):
            st = self.get(cid, fields="status_code,status")
            code = st.get("status_code")
            if code == "FINISHED":
                break
            if code in ("ERROR", "EXPIRED"):
                raise RuntimeError(f"Upload processing failed: {st}")
            time.sleep(10)
        else:
            raise RuntimeError("Upload processing timed out")
        return self.post(f"{self.uid}/media_publish", creation_id=cid)["id"]

    def reply_to_comments(self, replied, replies, max_replies=15):
        me = self.username()
        media = self.get(f"{self.uid}/media", fields="id", limit=6).get("data", [])
        done = 0
        for m in media:
            comments = self.get(f"{m['id']}/comments", fields="id,username,text,replies{username}",
                                limit=50).get("data", [])
            for c in comments:
                if done >= max_replies:
                    return done
                if c["id"] in replied or c.get("username") == me:
                    continue
                if any(r.get("username") == me for r in c.get("replies", {}).get("data", [])):
                    replied.append(c["id"])
                    continue
                msg = replies[len(replied) % len(replies)]
                self.post(f"{c['id']}/replies", message=msg)
                replied.append(c["id"])
                done += 1
        return done
