# Two-run results

## Run 1 — baseline

The recorded baseline ran on 26 August 2026 (UTC) and checked all five companies. It stored 173 publication records: 59 for Norsk Hydro, 18 for Constellium, 38 for Alcoa, 27 for Ma'aden, and 31 for Rio Tinto. Every accepted publication is saved with its normalized title key, source URL, website date (when shown), first-found UTC timestamp, content hash, and a retained content version. Baseline items are deliberately marked `NEW`: there is no earlier comparison at that point. The matching console-style evidence is in `first-run.txt`.

## Run 2 — comparison

The second run uses the same database and sources. The recorded comparison result was:

| Company | Check status | New | Updated |
|---|---|---:|---:|
| Norsk Hydro | OK | 0 | 0 |
| Constellium | OK | 0 | 0 |
| Alcoa | OK | 0 | 0 |
| Ma'aden | OK | 0 | 0 |
| Rio Tinto | OK | 0 | 0 |

The business report read: “No new or meaningfully changed publications.” The latest recorded comparison completed between 09:46 and 09:51 UTC on 26 August 2026. Alcoa completed with a warning because its investor pages returned anti-bot verification pages; this was displayed as a warning, not interpreted as a no-change result. Each site’s latest timestamp and warning are available in the console report, dashboard, and SQLite `site_checks` table.

## How the comparison works

1. The scraper starts with curated publication pages, then checks the homepage for newly exposed official links.
2. It excludes navigation, stock/utility pages, rotating homepage content, cookie controls, and anti-bot verification pages.
3. It uses a normalized title key to merge the same item found in multiple sections and recognizes a move when that key has a different source URL.
4. It hashes cleaned article/report content. A missing key is `NEW`; a changed hash or source URL is `UPDATED`; an identical item becomes `SEEN` and is omitted from the next report.
5. A source or item failure is stored and shown as a warning/error; it can never produce a “no change” conclusion.

The retained content versions provide the evidence for the short “what changed” explanation in the daily report.
