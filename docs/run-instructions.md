# Run instructions

## One-time setup

Use PowerShell in the project folder:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
```

Run the automated checks before changing the monitor:

```powershell
.venv\Scripts\python.exe -m pytest -q
```

## First check and daily check

Run the following command once to create the baseline, then once per day:

```powershell
.venv\Scripts\python.exe main.py
```

Do not delete `data/monitor.db`: it is the comparison history and evidence store. The first run reports the baseline items as `NEW`. Later runs report only new or meaningfully changed items. A no-change run still prints the latest status for every company.

For a safe trial that does not change the production history, choose another database file:

```powershell
.venv\Scripts\python.exe main.py --database data/trial-monitor.db
```

## Errors and retries

Any failed section or publication fetch is printed as a check warning and saved in `site_checks`; it is never interpreted as “no change”. Retry one configured company without changing the rest of the daily result:

```powershell
.venv\Scripts\python.exe main.py --company "Ma'aden"
```

Use `--dashboard` to open the local review page after a run. Alternatively start it with:

```powershell
.venv\Scripts\python.exe -m app.web
```

Then open `http://127.0.0.1:5000/`.

## Schedule daily on Windows

Create a Windows Task Scheduler task with a daily trigger. Use:

- Program/script: the absolute path to `.venv\Scripts\python.exe`
- Add arguments: the absolute path to `main.py`
- Start in: this project folder

Keep the database and task output as review evidence.

## Optional notifications

The monitor can send one alert when a run finds new or updated publications. Configure an approved incoming webhook as the user-level Windows environment variable `MONITOR_WEBHOOK_URL`; do not put a secret webhook URL in source control. The alert includes company, item type, title, website date when present, and the official source link. No alert is sent when there are no changes.

For a one-off test, use `--webhook-url URL`. A failed notification is printed clearly after the monitoring report and does not change the monitoring result.

### Windows notification without any service

Run `main.py --toast` to show a small Windows notification-center alert whenever new or changed publications are found. There is no account, credential, or webhook to configure. When scheduling this mode, select **Run only when user is logged on**—Windows cannot show a notification from a non-interactive signed-out session. The dashboard does not need to be open.

## Trainer demonstration

Show the notification without changing monitoring results by double-clicking `Show Notification Demo.bat`, or use this command:

```powershell
.venv\Scripts\python.exe main.py --demo-toast
```

It displays an example notification only. Explain that the normal scheduled task runs `main.py --toast`, which uses the same notification style only when a real update is detected.

## Maintain or extend

Edit `app/sites.py` to add one configuration object with the company name, homepage, and curated official publication pages. Use absolute URLs for special official subdomains and `allowed_hosts` only when links must legitimately cross to one. No scraper or database redesign is needed.

Prefer pages that list press releases, news, results, reports, or exchange announcements. Verify a new page manually once, then run the test suite. If a company blocks automated access, retain the warning and add an approved alternative official page; do not silently mark it clear.
