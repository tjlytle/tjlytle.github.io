#!/usr/bin/env python3
"""Merge new joind.in talk entries for user tjlytle into build/talks.json.

Existing talks keep their curated blurb/thumb; new deliveries of a known talk are added by
normalized title; genuinely new talks are appended with the joind.in description as blurb
(edit talks.json afterwards). Then run build/build.py.
"""
import json
import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / "talks.json"
API = "https://api.joind.in/v2.1"
UA = {"Accept": "application/json", "User-Agent": "timlytle.net build script"}


def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA)))


def norm(title):
    t = re.sub(r"[^a-z0-9 ]", " ", title.lower())
    t = re.sub(r"\b(the|a|of|and)\b", " ", t)
    return " ".join(t.split())


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    by_key = {}
    for talk in data["talks"]:
        for inst in talk["instances"]:
            by_key.setdefault(norm(talk["title"]), talk)
        for alias in talk.get("aliases", []):
            by_key[norm(alias)] = talk
    known_urls = {i["joindin"] for t in data["talks"] for i in t["instances"]}

    user = get(f"{API}/users?username=tjlytle")["users"][0]
    talks = get(user["talks_uri"] + "?verbose=yes&resultsperpage=200")["talks"]
    events = {}
    added = 0
    for t in talks:
        if t["website_uri"] in known_urls:
            continue
        ev = events.get(t["event_uri"]) or events.setdefault(t["event_uri"], get(t["event_uri"])["events"][0])
        inst = {
            "date": t["start_date"][:10],
            "event": ev["name"],
            "location": ev.get("location"),
            "event_url": ev.get("href"),
            "joindin": t["website_uri"],
            "rating": t.get("average_rating"),
            "comments": t.get("comment_count"),
            "slides": t.get("slides_link") or None,
        }
        key = norm(t["talk_title"])
        talk = by_key.get(key)
        if talk is None:
            talk = {
                "slug": re.sub(r"\s+", "-", key),
                "title": t["talk_title"],
                "description": (t.get("talk_description") or "").strip(),
                "blurb": (t.get("talk_description") or "").strip().split(".")[0] + ".",
                "thumb": None,
                "video": None,
                "instances": [],
            }
            data["talks"].append(talk)
            by_key[key] = talk
            print("NEW TALK (edit blurb/thumb):", t["talk_title"])
        talk["instances"].append(inst)
        added += 1
    for talk in data["talks"]:
        talk["instances"].sort(key=lambda i: i["date"], reverse=True)
        talk["first"] = talk["instances"][-1]["date"]
        talk["last"] = talk["instances"][0]["date"]
        talk["times"] = len(talk["instances"])
    DATA_PATH.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"added {added} deliveries")


if __name__ == "__main__":
    main()
