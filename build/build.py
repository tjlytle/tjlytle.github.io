#!/usr/bin/env python3
"""Render index.html, talks.html and talks/<slug>.html from build/talks.json and build/templates/.

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


def talk_url(talk):
    return f'/talks/{talk["slug"]}.html'


def short_event(name):
    """'Longhorn PHP Conference 2023' -> 'Longhorn PHP 2023', and a few one-offs."""
    name = re.sub(r"\s+Conference\b", "", name)
    name = re.sub(r"\s+-\s+Online Edition", " (online)", name)
    name = re.sub(r"\s+\(Online\)", " (online)", name)
    name = name.replace("Nomad PHP US - June 2015", "Nomad PHP 2015").replace("Nomad PHP December 2016 US", "Nomad PHP 2016")
    name = name.replace("LVPHP - February 2013", "LVPHP 2013").replace("php|tek 2012 UnCons", "php[tek] 2012 uncon")
    return name


def pretty_date(iso):
    return date.fromisoformat(iso).strftime("%B %-d, %Y")


def highly_rated(talk):
    """Weighted joind.in average of 4.5+ across at least three ratings."""
    rated = [i for i in talk["instances"] if i.get("rating") and i.get("comments")]
    total = sum(i["comments"] for i in rated)
    if total < 3:
        return False
    return sum(i["rating"] * i["comments"] for i in rated) / total >= 4.5


def rating_tag(cls):
    return f'<span class="{cls}">highly rated</span>'


def newest_first(talk):
    return sorted(talk["instances"], key=lambda i: i["date"], reverse=True)


def slides_link(talk):
    return next((i["slides"] for i in newest_first(talk) if i.get("slides")), None)


def instances_line(talk):
    parts = [f'<a href="{esc(i["joindin"])}" rel="noopener">{esc(short_event(i["event"]))}</a>' for i in newest_first(talk)]
    return " &middot; ".join(parts)


def paragraphs(text):
    chunks = [c.strip() for c in re.split(r"\n\s*\n|\s{2,}(?=[A-Z])", text or "") if c.strip()]
    return "".join(f"<p>{esc(c)}</p>" for c in chunks)


WASHES = [1, 9, 4, 10, 5]  # red, pink, orange, green, purple: nothing blue, so the cards stand off the teal site


def slide_title(title):
    """Bold the last word the way the decks do: 'Let Go of <b>Ownership</b>'."""
    words = title.split()
    if len(words) < 2:
        return f"<b>{esc(title)}</b>"
    return esc(" ".join(words[:-1])) + f" <b>{esc(words[-1])}</b>"


def media(talk, cls="talk__thumb"):
    if talk.get("thumb"):
        return f'<img class="{cls}" src="/assets/img/decks/{esc(talk["thumb"])}" alt="" loading="lazy" width="800" height="450">'
    wash = WASHES[talk.get("_order", 0) % len(WASHES)]
    n = len(talk["title"])
    size = "slide--xl" if n <= 16 else "slide--lg" if n <= 30 else ""
    return (f'<div class="{cls} slide slide--wash-{wash} {size}" aria-hidden="true">'
            f'<span class="slide__title">{slide_title(talk["title"])}</span>'
            f'<span class="slide__sig hand">Tim Lytle &middot; @tjlytle</span></div>')


def card(talk, idx):
    color = STICKY_CYCLE[idx % len(STICKY_CYCLE)]
    url = talk_url(talk)
    foot = f'<div class="talk__foot"><a class="talk__more-link" href="{url}">About this talk &rarr;</a>{rating_tag("talk__rating") if highly_rated(talk) else ""}</div>'
    return f'''
      <article class="talk sticky sticky--tape {color}" id="{esc(talk["slug"])}">
        <a class="talk__media" href="{url}" tabindex="-1" aria-hidden="true">{media(talk)}</a>
        <h3 class="talk__title"><a href="{url}">{esc(talk["title"])}</a></h3>
        <p class="talk__blurb">{esc(talk["blurb"])}</p>
        <p class="talk__meta mono">{instances_line(talk)}</p>
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
        if slides_link(talk):
            side += f'<a class="row__link" href="{esc(slides_link(talk))}" rel="noopener">Slides</a>'
        if highly_rated(talk):
            side += rating_tag("row__rated")
        rows.append(f'''
        <li class="row">
          {label}
          <div class="row__main">
            <h3 class="row__title"><a href="{talk_url(talk)}">{esc(talk["title"])}</a></h3>
            <p class="row__events mono">{instances_line(talk)}</p>
            <p class="row__blurb">{esc(talk["blurb"])}</p>
          </div>
          <div class="row__side">{side}</div>
        </li>''')
    return "".join(rows)


def given_at(talk):
    items = []
    for i in newest_first(talk):
        where = f' &middot; {esc(i["location"])}' if i.get("location") and i["location"].lower() != "online" else ""
        items.append(f'''
          <li class="given__item">
            <span class="given__event">{esc(i["event"])}</span>
            <span class="given__meta mono">{esc(pretty_date(i["date"]))}{where} &middot; <a href="{esc(i["joindin"])}" rel="noopener">joind.in</a></span>
          </li>''')
    return "".join(items)


def upcoming_for(slug=None):
    today = date.today().isoformat()
    items = [u for u in DATA.get("upcoming", []) if u["date"] >= today and (slug is None or u.get("slug") == slug)]
    return items[0] if items else None


def upcoming_block():
    u = upcoming_for()
    if not u:
        return ""
    when = date.fromisoformat(u["date"]).strftime("%b %-d, %Y")
    href = talk_url({"slug": u["slug"]}) if u.get("slug") else "#"
    return f'''
      <a class="upcoming sticky sticky--tape sticky--yellow" href="{href}">
        <span class="hand hand--orange">Next up</span>
        <span class="upcoming__title">{esc(u["title"])}</span>
        <span class="upcoming__meta mono">{esc(u["event"])} &middot; {esc(when)}</span>
      </a>'''


def hero_note():
    u = upcoming_for()
    if not u:
        return ""
    when = date.fromisoformat(u["date"]).strftime("%b %-d")
    title = re.split(r"[:?]", u["title"])[0].strip() + ("?" if "?" in u["title"] else "")
    href = talk_url({"slug": u["slug"]}) if u.get("slug") else "/talks.html"
    return f'''
        <a class="hero__note sticky sticky--tape" href="{href}">
          <span class="hand hand--orange">Next up</span>
          <span class="title">{esc(title)}</span>
          <span class="mono">{esc(u["event"])} &middot; {esc(when)}</span>
        </a>'''


def talk_kicker(talk):
    u = upcoming_for(talk["slug"])
    if u:
        return f'next at {esc(u["event"])}, {date.fromisoformat(u["date"]).strftime("%b %-d")}'
    n = len(talk["instances"])
    first, last = talk["first"][:4], talk["last"][:4]
    if n == 1:
        return f"given once, in {last}"
    span = last if first == last else f"{first} to {last}"
    return f"given {n} times, {span}"


def quote_item(h, with_talk=None):
    text = h.get("pull") or h["text"]
    talk_line = f'<span class="quote__talk">on <a href="{talk_url(with_talk)}">{esc(with_talk["title"])}</a></span>' if with_talk else ""
    return f'''
        <li class="quote sticky sticky--tape">
          <blockquote class="quote__text">{esc(text)}</blockquote>
          <p class="quote__cite mono">{esc(h["author"])} &middot; {esc(h["event"])} &middot; <a href="{esc(h["url"])}" rel="noopener">on joind.in</a> {talk_line}</p>
        </li>'''


def quotes_block(talk):
    """Attendee comments for a talk page; more than three get shuffled client-side."""
    hs = talk.get("highlights") or []
    if not hs:
        return ""
    rand = ' data-random="3"' if len(hs) > 3 else ""
    return f'''

          <div class="quotes">
            <p class="hand hand--yellow quotes__kicker">What people said</p>
            <ul class="quotes__list"{rand}>{"".join(quote_item(h) for h in hs)}
            </ul>
          </div>'''


def speaker_quotes_block(talks):
    by_id = {h["id"]: (h, t) for t in talks for h in t.get("highlights", [])}
    hs = [by_id[i] for i in DATA.get("speaker_quotes", []) if i in by_id]
    if not hs:
        return ""
    rand = ' data-random="3"' if len(hs) > 3 else ""
    return f'''
      <ul class="quotes__list quotes__list--home"{rand}>{"".join(quote_item(h, t) for h, t in hs)}
      </ul>'''


def render(template_name, out_path, **slots):
    tpl = (BUILD / "templates" / template_name).read_text(encoding="utf-8")
    for key, val in slots.items():
        tpl = tpl.replace("{{" + key + "}}", val)
    leftover = re.findall(r"{{\w+}}", tpl)
    if leftover:
        raise SystemExit(f"unfilled slots in {template_name}: {leftover}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(tpl, encoding="utf-8")


talks = sorted(DATA["talks"], key=lambda t: t["last"], reverse=True)
for n, t in enumerate(t for t in talks if not t.get("thumb")):
    t["_order"] = n
by_slug = {t["slug"]: t for t in talks}
featured = [by_slug[s] for s in DATA.get("featured", [])] or talks[:3]
deliveries = sum(len(t["instances"]) for t in talks)
first_year = min(i["date"] for t in talks for i in t["instances"])[:4]

render(
    "talks.html", ROOT / "talks.html",
    FEATURED_CARDS="".join(card(t, i) for i, t in enumerate(featured)),
    TALK_LIST=list_rows(talks),
    UPCOMING=upcoming_block(),
    QUOTES=speaker_quotes_block(talks),
    TALK_COUNT=str(len(talks)), DELIVERY_COUNT=str(deliveries), FIRST_YEAR=first_year,
)
render(
    "index.html", ROOT / "index.html",
    RECENT_CARDS="".join(card(t, i) for i, t in enumerate(featured)),
    HERO_NOTE=hero_note(),
    QUOTES=speaker_quotes_block(talks),
    TALK_COUNT=str(len(talks)),
)
for talk in talks:
    slides = slides_link(talk)
    render(
        "talk.html", ROOT / "talks" / f'{talk["slug"]}.html',
        TITLE=esc(talk["title"]),
        BLURB=esc(talk["blurb"]),
        KICKER=talk_kicker(talk),
        MEDIA=media(talk, "detail__thumb"),
        DESCRIPTION=paragraphs(talk["description"]) or f'<p>{esc(talk["blurb"])}</p>',
        GIVEN_AT=given_at(talk),
        QUOTES=quotes_block(talk),
        SLIDES=f'<a class="btn-sticky btn-sticky--quiet" href="{esc(slides)}" rel="noopener">Open the slides</a>' if slides else "",
        RATED=rating_tag("detail__rated") if highly_rated(talk) else "",
        OG_IMAGE=f'/assets/img/decks/{talk["thumb"]}' if talk.get("thumb") else "/assets/img/og-talks.jpg",
        SLUG=talk["slug"],
    )
print(f"wrote index.html, talks.html and {len(talks)} talk pages")
