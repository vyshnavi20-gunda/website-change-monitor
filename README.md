# Website Change Monitor

A small daily monitor for official publications on five corporate websites:
Norsk Hydro, Constellium, Alcoa, Ma'aden, and Rio Tinto.

## Local dashboard

Start the dashboard server from PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe -m app.web
```

Then open [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in a browser. This address works only on this computer. Keep the PowerShell window open while using the dashboard; press `Ctrl+C` to stop the server.

## What it checks

`main.py` checks each homepage plus curated official News, Press Release, Investor Relations and report pages. It does not probe guessed paths, because a routine 404 is not useful monitoring evidence. Playwright renders JavaScript pages when a normal HTTP response is insufficient. Candidate links are opened and their meaningful visible text is hashed, so a changed article is reported even when its website publication date stays the same. PDF links are hashed as binary documents, but PDF internals are never printed as report text.

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

To retry only one company after a warning, run (for example):

```powershell
.venv\Scripts\python.exe main.py --company "Ma'aden"
```

Use `--database data/trial-monitor.db` for a fresh trial baseline without changing the daily history.

## Optional update notifications

Set `MONITOR_WEBHOOK_URL` to an incoming webhook for Teams, Slack, Discord, or an approved automation relay. The monitor posts one short alert only when it finds `NEW` or `UPDATED` publications; it does not notify on a no-change run. The webhook URL is not stored in this project.

```powershell
$env:MONITOR_WEBHOOK_URL = "https://your-approved-webhook.example/secret"
.venv\Scripts\python.exe main.py
```

For a one-off run, pass `--webhook-url` instead. Test the configured webhook with a known fresh trial database before putting it in Task Scheduler.

### Simple Windows notification

No external service is required. Add `--toast` to show a small Windows notification-center alert only when the monitor finds a new or changed publication:

```powershell
.venv\Scripts\python.exe main.py --toast
```

Preview the notification safely, without checking a site or changing saved monitoring data:

```powershell
.venv\Scripts\python.exe main.py --demo-toast
```

## Trainer demo

To demonstrate the notification feature during review, either double-click `Show Notification Demo.bat` or run:

```powershell
.venv\Scripts\python.exe main.py --demo-toast
```

This opens a sample Windows notification and does not check websites or change the SQLite monitoring history. For a live check, use `Run Monitor with Popup.bat`; it sends a notification only if a real new or updated publication is found.

For Task Scheduler, use the same argument and choose **Run only when user is logged on**. A notification cannot appear on a locked or signed-out Windows desktop; the monitor still records the result in its database.

For a silent manual check with no command window, double-click `Check for Updates.vbs`. It shows a Windows notification only when a real update is found. For automatic checks, double-click `Install Background Notifications.bat` and choose daily or hourly monitoring. The task runs while you are logged in and notifies you only when it finds a real update.

When the dashboard is open, click **Enable dashboard notifications** once. Later dashboard refreshes show a browser notification with the latest status, including “No new or changed publications” when there are no current updates. Click **Disable dashboard notifications** at any time to stop these dashboard-refresh alerts. This dashboard setting does not stop the separate `--toast` background monitor, which alerts you while the dashboard is closed.

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

Add one configuration object to `SITES` in `app/sites.py`, with a company name, root URL, and its official publication section URLs. The persistence code does not need redesigning. If the site uses an official publication subdomain, add it to `allowed_hosts`.

## Evidence and known limits

The database keeps the source URL, title, website date, first-found timestamp, current hash, and a short visible-text summary. Errors are stored as `error` checks and are never treated as no-change.

Some items may be missed when a site exposes them only behind login, a non-link interaction, an API call not rendered by the page, or a section path not in the generic list. A title change can appear as a new item, and two unrelated items with exactly the same normalized title at one company may be merged. Boilerplate that remains in an article body can cause a false update, although navigation and rotating homepage content are excluded from publication identity and are not themselves reported.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest -q
```
