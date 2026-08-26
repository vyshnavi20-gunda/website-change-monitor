# Website Change Monitor

A small daily monitor for official publications on five corporate websites:
Norsk Hydro, Constellium, Alcoa, Ma'aden, and Rio Tinto.

## What it checks

`main.py` checks each starting domain and likely publication sections such as News, Media, Press Releases, Investor Relations, Reports, Publications, Announcements, and Updates. Playwright renders JavaScript pages. Candidate links are opened and their meaningful visible text is hashed, so a changed article is reported even when its website publication date stays the same. PDF links are hashed as binary documents, but PDF internals are never printed as report text.

SQLite stores:

- the website date separately from `first_found_at`
- a stable normalized title key for duplicates and moved URLs
- the latest article content hash and summary
- the latest check status and error for every company

Homepage-only visual changes are not reported unless they expose a publication link. RSS and sitemaps are not required.

## Run it

From the project directory in PowerShell:

```powershell
.venv\Scripts\Activate.ps1
.venv\Scripts\python.exe main.py
```

For the same check plus a local report in a separate browser window, run:

```powershell
.venv\Scripts\python.exe main.py --dashboard
```

Leave that terminal open while using the dashboard; press `Ctrl+C` to stop it.

The first run stores the discovered baseline and reports those publications as `NEW`. Run it again later; it reports only new or meaningfully changed publications. Previous `NEW` and `UPDATED` rows are closed at the start of the next check, so they are not repeated forever. A later unchanged run prints `No new or meaningfully changed publications.` and still lists the latest status for all sites.

The first Playwright setup may require:

```powershell
.venv\Scripts\python.exe -m playwright install chromium
```

## Browser output

Start the local dashboard in a second terminal:

```powershell
.venv\Scripts\python.exe -m app.web
```

Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in another browser window. The dashboard shows publication type, title/source link, website date, first-found time, summary, and the latest check status/error.

The JSON report is at [http://127.0.0.1:5000/api/report](http://127.0.0.1:5000/api/report).

## Schedule it daily on Windows

Create a Windows Task Scheduler task that runs daily with:

- Program: the absolute path to `.venv\Scripts\python.exe`
- Argument: the absolute path to `main.py`
- Start in: the project directory

Keep `data/monitor.db` and the console output as evidence for review. Do not delete the database between runs.

## Add another website

Add one configuration object to `SITES` in `app/sites.py`, with a company name, root URL, and its official publication section paths. The generic section discovery and persistence code does not need redesigning. If a site uses unusual section paths, add them to that site's `sections` list; `DISCOVERY_PATHS` remains the fallback.

## Evidence and known limits

The database keeps the source URL, title, website date, first-found timestamp, current hash, and a short visible-text summary. Errors are stored as `error` checks and are never treated as no-change.

Some items may be missed when a site exposes them only behind login, a non-link interaction, an API call not rendered by the page, or a section path not in the generic list. A title change can appear as a new item, and two unrelated items with exactly the same normalized title at one company may be merged. Boilerplate that remains in an article body can cause a false update, although navigation and rotating homepage content are excluded from publication identity and are not themselves reported.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest -q
```
