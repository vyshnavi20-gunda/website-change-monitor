"""Run one monitoring cycle. Use --dashboard for browser output."""
import argparse
import webbrowser

from app.database import initialize_database
from app.monitor import check_website
from app.report import print_report
from app.sites import SITES


def run() -> None:
    initialize_database()
    for site in SITES:
        result = check_website(site["company"], site["url"], site["sections"])
        print(f"{result['company']}: {result['status']} | "
              f"new={len(result['new'])}, updated={len(result['updated'])} | "
              f"{result['checked_at']}")
        if result["error"]:
            print(f"  Check warning: {result['error']}")
    print_report()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check official corporate publications.")
    parser.add_argument("--dashboard", action="store_true",
                        help="keep a local browser dashboard open after the check")
    args = parser.parse_args()
    run()
    if args.dashboard:
        webbrowser.open_new("http://127.0.0.1:5000/")
        from app.web import app
        app.run(host="127.0.0.1", port=5000, debug=False)
