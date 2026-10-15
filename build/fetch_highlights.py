#!/usr/bin/env python3
"""Fill in highlighted joind.in comments listed in build/talks.json.

Each talk may carry a "highlights" list. An entry only needs {"id": <joind.in comment id>};
this script fetches the author, date, text, event, and a direct link to the comment on joind.in
for any entry that is missing them. Existing text is left alone, so quotes can be trimmed by hand.
Then run build/build.py.
"""
import hashlib
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / "talks.json"
API = "https://api.joind.in/v2.1"
UA = {"Accept": "application/json", "User-Agent": "timlytle.net build script"}
# joind.in's web frontend anchors each comment with the first six hex chars of the md5 of the
# comment URI as it sees it, which is served from this internal hostname rather than api.joind.in.
INTERNAL_API = "https://api.direct.joind.in/v2.1"


def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA)))


def anchor(comment_id):
    return hashlib.md5(f"{INTERNAL_API}/talk_comments/{comment_id}".encode()).hexdigest()[:6]


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    talk_stub = {}
    filled = 0
    for talk in data["talks"]:
        by_stub = {i["joindin"].rsplit("/", 1)[1]: i for i in talk["instances"] if i.get("joindin")}
        for h in talk.get("highlights", []):
            if h.get("text"):
                continue
            cid = str(h["id"])
            c = get(f"{API}/talk_comments/{cid}?verbose=yes")["comments"][0]
            if c["talk_uri"] not in talk_stub:
                talk_stub[c["talk_uri"]] = get(c["talk_uri"])["talks"][0]["website_uri"].rsplit("/", 1)[1]
            stub = talk_stub[c["talk_uri"]]
            inst = by_stub.get(stub)
            if inst is None:
                raise SystemExit(f'comment {cid} belongs to joind.in talk {stub}, which is not an instance of "{talk["title"]}"')
            h.update({
                "author": c.get("user_display_name") or "Anonymous",
                "date": c["created_date"][:10],
                "event": inst["event"],
                "rating": c.get("rating"),
                "text": " ".join(c["comment"].split()),
                "url": f"https://joind.in/talk/{stub}#comment-{anchor(cid)}",
            })
            filled += 1
    DATA_PATH.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"filled {filled} highlights")


if __name__ == "__main__":
    main()
