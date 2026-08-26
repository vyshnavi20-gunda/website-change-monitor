"""Run one monitoring cycle. Use --dashboard for browser output."""
import argparse
import webbrowser
from pathlib import Path

from app import database
from app.monitor import check_website
from app.notify import notify_webhook, notify_windows_popup, notify_windows_toast
from app.report import print_report
from app.sites import SITES


def run(
    company_filter: str | None = None,
    webhook_url: str | None = None,
    popup: bool = False,
    toast: bool = False,
) -> None:
    database.initialize_database()
    results = []
    for site in SITES:
        if company_filter and site["company"].casefold() != company_filter.casefold():
            continue
        result = check_website(
            site["company"], site["url"], site["sections"],
            site.get("allowed_hosts", ()),
        )
        results.append(result)
        print(f"{result['company']}: {result['status']} | "
              f"new={len(result['new'])}, updated={len(result['updated'])} | "
              f"{result['checked_at']}")
        if result["error"]:
            print(f"  Check warning: {result['error']}")
    print_report()
    notification = notify_webhook(results, webhook_url)
    if notification:
        print(f"\n{notification}")
    if popup:
        popup_result = notify_windows_popup(results)
        if popup_result:
            print(popup_result)
    if toast:
        toast_result = notify_windows_toast(results)
        if toast_result:
            print(toast_result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check official corporate publications.")
    parser.add_argument("--dashboard", action="store_true",
                        help="keep a local browser dashboard open after the check")
    parser.add_argument("--database", metavar="PATH",
                        help="use a separate SQLite database (useful for a fresh baseline)")
    parser.add_argument("--company", metavar="NAME",
                        help="check one configured company (for retrying a failed site)")
    parser.add_argument("--webhook-url", metavar="URL",
                        help="send updates to this incoming webhook; otherwise use MONITOR_WEBHOOK_URL")
    parser.add_argument("--popup", action="store_true",
                        help="show a Windows popup when new or changed publications are found")
    parser.add_argument("--demo-popup", action="store_true",
                        help="show a sample popup without checking websites or changing the database")
    parser.add_argument("--toast", action="store_true",
                        help="show a Windows notification-center alert when updates are found")
    parser.add_argument("--demo-toast", action="store_true",
                        help="show a sample Windows notification-center alert without checking websites")
    args = parser.parse_args()
    if args.database:
        database.DB_PATH = Path(args.database)
    if args.company and not any(site["company"].casefold() == args.company.casefold() for site in SITES):
        parser.error("--company must match a configured company name")
    if args.demo_popup:
        notify_windows_popup([{
            "company": "Example Metals",
            "new": [{
                "type": "Press Release",
                "title": "Example quarterly results published",
                "date": "26 August 2026",
                "url": "https://example.test/quarterly-results",
            }],
            "updated": [],
        }])
        raise SystemExit(0)
    if args.demo_toast:
        notify_windows_toast([{
            "company": "Example Metals",
            "new": [{
                "type": "Press Release",
                "title": "Example quarterly results published",
                "date": "26 August 2026",
                "url": "https://example.test/quarterly-results",
            }],
            "updated": [],
        }])
        raise SystemExit(0)
    run(args.company, args.webhook_url, args.popup, args.toast)
    if args.dashboard:
        webbrowser.open_new("http://127.0.0.1:5000/")
        from app.web import app
        app.run(host="127.0.0.1", port=5000, debug=False)
