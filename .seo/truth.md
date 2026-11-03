# Source of truth

Derived from the repo, 2026-11-02. Numbers on the site are generated from `build/talks.json` by `build/build.py`, so the data file is the source; never hand-edit a count into a template.

| Claim | Value | Source | Read |
|---|---|---|---|
| Talks | 26 distinct talks | build/talks.json (`talks`) | 2026-11-02 |
| Deliveries | 51 | build/talks.json (sum of `instances`) | 2026-11-02 |
| Speaking since | 2012 | build/talks.json (earliest instance date) | 2026-11-02 |
| "Highly rated" | weighted joind.in average >= 4.5 over >= 3 rated comments | build/build.py `highly_rated()` | 2026-11-02 |
| Experience | 20+ years building API-first systems | build/templates/index.html (hero) | 2026-11-02 |
| Availability | consulting, advisory, the right longer-term role | build/templates/index.html (contact) | 2026-11-02 |
| TEDx talk | yes, on creativity; not in talks.json | build/templates/index.html (about) | 2026-11-02 |
| Contact | tim@timlytle.net; Google Calendar booking link | build/templates/index.html | 2026-11-02 |
| Profiles | linkedin.com/in/timlytle, github.com/tjlytle, joind.in/user/tjlytle, sessionize.com/tjlytle, x.com/tjlytle | build/build.py `PERSON.sameAs` | 2026-11-02 |

## HIGH-RISK

None. No pricing, compliance or medical/legal claims. The only thing to protect is the ratings: never emit `AggregateRating` schema built from joind.in scores (self-authored rating markup).

## Code vs site disagreements

None found. The counts on the site match `talks.json`.
