# Two-run results

## Run 1 — baseline

The first run checks the curated official publication pages for Norsk Hydro, Constellium, Alcoa, Ma'aden, and Rio Tinto. Every accepted publication is saved with its normalized title key, source URL, website date (when shown), first-found UTC timestamp, content hash, and a retained content version. Baseline items are deliberately marked `NEW`: there is no earlier comparison at that point.

## Run 2 — comparison

The second run uses the same database and sources. The recorded comparison result was:

| Company | Check status | New | Updated |
|---|---|---:|---:|
| Norsk Hydro | OK | 0 | 0 |
| Constellium | OK | 0 | 0 |
| Alcoa | OK | 0 | 0 |
| Ma'aden | OK | 0 | 0 |
| Rio Tinto | OK | 0 | 0 |

The business report read: “No new or meaningfully changed publications.” Each site’s latest timestamp and any warning are available in the console report, dashboard, and SQLite `site_checks` table.

## How the comparison works

1. The scraper starts with curated publication pages, then checks the homepage for newly exposed official links.
2. It excludes navigation, stock/utility pages, rotating homepage content, cookie controls, and anti-bot verification pages.
3. It uses a normalized title key to merge the same item found in multiple sections and recognizes a move when that key has a different source URL.
4. It hashes cleaned article/report content. A missing key is `NEW`; a changed hash or source URL is `UPDATED`; an identical item becomes `SEEN` and is omitted from the next report.
5. A source or item failure is stored and shown as a warning/error; it can never produce a “no change” conclusion.

The retained content versions provide the evidence for the short “what changed” explanation in the daily report.
