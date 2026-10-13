#!/usr/bin/env python3
"""Render index.html and talks.html from build/talks.json and build/templates/.

Usage: python3 build/build.py
Refresh the data first with: python3 build/fetch_joindin.py  (merges new joind.in entries into talks.json)
"""
import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
DATA = json.loads((BUILD / "talks.json").read_text(encoding="utf-8"))

STICKY_CYCLE = ["", "sticky--yellow", "sticky--blue", "", "sticky--green", "", "sticky--peach", "sticky--yellow", "", "sticky--blue"]


def esc(s):
    return html.escape(s or "", quote=True)


def short_event(name):
    """php[tek] 2023 -> php[tek] 2023; 'Longhorn PHP Conference 2023' -> 'Longhorn PHP 2023'."""
    name = re.sub(r"\s+Conference\b", "", name)
    name = re.sub(r"\s+-\s+Online Edition", " (online)", name)
    name = re.sub(r"\s+\(Online\)", " (online)", name)
    name = name.replace("Nomad PHP US - June 2015", "Nomad PHP 2015").replace("Nomad PHP December 2016 US", "Nomad PHP 2016")
    name = name.replace("LVPHP - February 2013", "LVPHP 2013").replace("php|tek 2012 UnCons", "php[tek] 2012 uncon")
    return name


def highly_rated(talk):
    """Weighted joind.in average of 4.5+ across at least three ratings."""
    rated = [i for i in talk["instances"] if i.get("rating") and i.get("comments")]
    total = sum(i["comments"] for i in rated)
    if total < 3:
        return False
    return sum(i["rating"] * i["comments"] for i in rated) / total >= 4.5


def rating_line(talk):
    return '<span class="talk__rating">highly rated</span>' if highly_rated(talk) else ""


def instances_line(talk):
    parts = []
    for inst in sorted(talk["instances"], key=lambda i: i["date"], reverse=True):
        label = esc(short_event(inst["event"]))
        parts.append(f'<a href="{esc(inst["joindin"])}" rel="noopener">{label}</a>')
    return " &middot; ".join(parts)


def links_line(talk):
    links = []
    slides = next((i["slides"] for i in sorted(talk["instances"], key=lambda i: i["date"], reverse=True) if i.get("slides")), None)
    if slides:
        links.append(f'<a href="{esc(slides)}" rel="noopener">Slides</a>')
    if talk.get("video"):
        links.append(f'<a href="{esc(talk["video"])}" rel="noopener">Video</a>')
    return "".join(links)


def paragraphs(text):
    chunks = [c.strip() for c in re.split(r"\n\s*\n|\s{2,}(?=[A-Z])", text or "") if c.strip()]
    return "".join(f"<p>{esc(c)}</p>" for c in chunks)


def card(talk, idx):
    color = STICKY_CYCLE[idx % len(STICKY_CYCLE)]
    if talk.get("thumb"):
        media = f'<img class="talk__thumb" src="assets/img/decks/{esc(talk["thumb"])}" alt="" loading="lazy" width="800" height="450">'
    else:
        media = f'<div class="talk__thumb--placeholder" aria-hidden="true">{esc(talk["title"])}</div>'
    newest = max(talk["instances"], key=lambda i: i["date"])
    foot = ""
    if links_line(talk) or rating_line(talk):
        foot = f'<div class="talk__foot"><div class="talk__links">{links_line(talk)}</div>{rating_line(talk)}</div>'
    more = ""
    if talk.get("description") and len(talk["description"]) > len(talk["blurb"]) + 40:
        more = f'<details class="talk__more"><summary>Full abstract</summary>{paragraphs(talk["description"])}</details>'
    return f'''
      <article class="talk sticky sticky--tape {color}" id="{esc(talk["slug"])}">
        {media}
        <h3 class="talk__title"><a href="{esc(newest["joindin"])}" rel="noopener">{esc(talk["title"])}</a></h3>
        <p class="talk__blurb">{esc(talk["blurb"])}</p>
        <p class="talk__meta mono">{instances_line(talk)}</p>
        {more}
        {foot}
      </article>'''


def list_rows(talks):
    rows = []
    last_year = None
    for talk in talks:
        year = talk["last"][:4]
        label = f'<span class="row__year mono">{year}</span>' if year != last_year else '<span class="row__year mono" aria-hidden="true"></span>'
        last_year = year
        side = ""
        slides = next((i["slides"] for i in sorted(talk["instances"], key=lambda i: i["date"], reverse=True) if i.get("slides")), None)
        if slides:
            side += f'<a class="row__link" href="{esc(slides)}" rel="noopener">Slides</a>'
        if highly_rated(talk):
            side += '<span class="row__rated">highly rated</span>'
        anchor = f'#{esc(talk["slug"])}' if talk["slug"] in FEATURED_SLUGS else None
        title = f'<a href="{anchor}">{esc(talk["title"])}</a>' if anchor else esc(talk["title"])
        rows.append(f'''
        <li class="row">
          {label}
          <div class="row__main">
            <h3 class="row__title">{title}</h3>
            <p class="row__events mono">{instances_line(talk)}</p>
            <p class="row__blurb">{esc(talk["blurb"])}</p>
          </div>
          <div class="row__side">{side}</div>
        </li>''')
    return "".join(rows)


def upcoming_block():
    today = date.today().isoformat()
    items = [u for u in DATA.get("upcoming", []) if u["date"] >= today]
    if not items:
        return ""
    u = items[0]
    when = date.fromisoformat(u["date"]).strftime("%b %-d, %Y")
    anchor = f'#{esc(u["slug"])}' if u.get("slug") else ""
    return f'''
      <a class="upcoming sticky sticky--tape sticky--yellow" href="{anchor}">
        <span class="hand hand--orange">Next up</span>
        <span class="upcoming__title">{esc(u["title"])}</span>
        <span class="upcoming__meta mono">{esc(u["event"])} &middot; {esc(when)}</span>
      </a>'''


def hero_note():
    today = date.today().isoformat()
    items = [u for u in DATA.get("upcoming", []) if u["date"] >= today]
    if not items:
        return ""
    u = items[0]
    when = date.fromisoformat(u["date"]).strftime("%b %-d")
    title = re.split(r"[:?]", u["title"])[0].strip()
    if "?" in u["title"]:
        title += "?"
    href = f'talks.html#{esc(u["slug"])}' if u.get("slug") else "talks.html"
    return f'''
        <a class="hero__note sticky sticky--tape" href="{href}">
          <span class="hand hand--orange">Next up</span>
          <span class="title">{esc(title)}</span>
          <span class="mono">{esc(u["event"])} &middot; {esc(when)}</span>
        </a>'''


def render(template_name, out_name, **slots):
    tpl = (BUILD / "templates" / template_name).read_text(encoding="utf-8")
    for key, val in slots.items():
        tpl = tpl.replace("{{" + key + "}}", val)
    leftover = re.findall(r"{{\w+}}", tpl)
    if leftover:
        raise SystemExit(f"unfilled slots in {template_name}: {leftover}")
    (ROOT / out_name).write_text(tpl, encoding="utf-8")
    print(f"wrote {out_name}")


talks = sorted(DATA["talks"], key=lambda t: t["last"], reverse=True)
by_slug = {t["slug"]: t for t in talks}
FEATURED_SLUGS = DATA.get("featured", [])
featured = [by_slug[s] for s in FEATURED_SLUGS] or talks[:3]
deliveries = sum(len(t["instances"]) for t in talks)
first_year = min(i["date"] for t in talks for i in t["instances"])[:4]

render(
    "talks.html",
    "talks.html",
    FEATURED_CARDS="".join(card(t, i) for i, t in enumerate(featured)),
    TALK_LIST=list_rows(talks),
    UPCOMING=upcoming_block(),
    TALK_COUNT=str(len(talks)),
    DELIVERY_COUNT=str(deliveries),
    FIRST_YEAR=first_year,
)
render(
    "index.html",
    "index.html",
    RECENT_CARDS="".join(card(t, i) for i, t in enumerate(featured)),
    HERO_NOTE=hero_note(),
    TALK_COUNT=str(len(talks)),
)
