import re
from urllib.parse import urlparse

from flask import Flask, render_template, jsonify

from app.database import (
    get_all_publications,
    get_latest_checks,
    initialize_database,
)
from app.sites import SITES


app = Flask(__name__)


def get_database_data():
    initialize_database()

    fields = [
        "id",
        "company",
        "item_type",
        "title",
        "source_url",
        "website_date",
        "first_found_at",
        "content_hash",
        "summary",
        "status",
    ]

    rows = get_all_publications()

    publications = [
        dict(zip(fields, row))
        for row in rows
    ]

    return publications


def dashboard_data():

    all_publications = get_database_data()

    # ---------------------------------------------------------
    # Navigation/menu text that should NOT be treated as news
    # ---------------------------------------------------------
    navigation_titles = {
        "corporate overview",
        "financial information",
        "share information",
        "analyst coverage",
        "tadawul announcement",
        "shareholder meeting",
        "email subscription",
        "maaden strategy 2040",
        "the hydro share",
        "reports and presentations",
        "analyst information",
        "information for shareholders",
        "debt investors",
        "topics",
        "brand center",
        "ir policy",
        "why invest in hydro",
        "news subscription",
        "media contacts",
        "hydro at a glance",
        "media gallery",
        "hydro alertline",
        "policies & reports",
        "all news",
        "subscribe to news",
        "see all share data",
        "investor relations",
        "news",
        "releases",
        "stories",
        "reports",
        "search",
        "learn more",
    }

    # ---------------------------------------------------------
    # Remove generic navigation pages and keep useful
    # corporate publications.
    # ---------------------------------------------------------
    def is_useful_publication(item):

        title = (item.get("title") or "").strip()
        normalized = title.lower()

        source_url = item.get("source_url") or ""
        path = urlparse(source_url).path.lower().rstrip("/")

        if normalized in navigation_titles:
            return False

        if normalized.startswith(
            (
                "go to:",
                "visit ",
                "next event",
            )
        ):
            return False

        if "category=" in source_url.lower():
            return False

        if path.endswith(
            (
                "/news",
                "/media",
                "/investors",
                "/investor-relations",
                "/reports",
                "/publications",
            )
        ):
            return False

        company_name = (
            item.get("company") or ""
        ).lower().replace("'", "")

        title_name = normalized.replace("'", "")

        # Keep publications that contain the company name,
        # or contain a year, which is common for official
        # reports and announcements.
        return (
            company_name in title_name
            or bool(re.search(r"\b20\d{2}\b", title))
        )

    # ---------------------------------------------------------
    # Generate a cleaner business-friendly summary.
    # ---------------------------------------------------------
    def clean_summary(item):

        raw = re.sub(
            r"\s+",
            " ",
            item.get("summary") or "",
        ).strip(" |")

        title = item.get("title") or ""
        company = item.get("company") or ""
        item_type = item.get("item_type") or "Publication"

        if raw:

            raw = re.sub(
                re.escape(title),
                "",
                raw,
                flags=re.IGNORECASE,
            ).strip(" |.-")

            content_start = re.search(
                r"\b(?:today )?(?:announced|reports|has announced|will|is pleased)\b",
                raw,
                re.IGNORECASE,
            )

            if content_start:
                raw = raw[content_start.start():]

            sentences = re.split(
                r"(?<=[.!?])\s+",
                raw,
            )

            meaningful = [
                sentence.strip()
                for sentence in sentences
                if len(sentence.strip()) > 35
            ]

            if meaningful:
                return " ".join(
                    meaningful[:3]
                )[:620]

        date = (
            item.get("website_date")
            or "an undated official page"
        )

        return (
            f"{title} is listed by {company} as an official "
            f"{item_type.lower()}. "
            f"The website shows {date}. "
            f"Open the official source to read the complete publication."
        )

    # ---------------------------------------------------------
    # Clean publications
    # ---------------------------------------------------------
    useful_publications = [
        item
        for item in all_publications
        if is_useful_publication(item)
    ]

    for item in useful_publications:
        item["display_summary"] = clean_summary(item)

    # ---------------------------------------------------------
    # Latest database publications
    # ---------------------------------------------------------
    useful_publications.sort(
        key=lambda item: (
            item.get("first_found_at") or "",
            item.get("id") or 0,
        ),
        reverse=True,
    )

    # Only NEW and UPDATED items are considered current updates.
    current_updates = [
        item
        for item in useful_publications
        if item.get("status") in {"new", "updated"}
    ]

    # ---------------------------------------------------------
    # Latest check status for every company
    # ---------------------------------------------------------
    checks = [
        dict(
            zip(
                (
                    "company",
                    "url",
                    "checked_at",
                    "status",
                    "error",
                ),
                row,
            )
        )
        for row in get_latest_checks()
    ]

    checks_by_company = {
        check["company"]: check
        for check in checks
    }

    # ---------------------------------------------------------
    # Build company dashboard cards
    # ---------------------------------------------------------
    companies = []

    for site in SITES:

        company = site["company"]

        company_updates = [
            item
            for item in current_updates
            if item.get("company") == company
        ]

        company_publications = [
            item
            for item in useful_publications
            if item.get("company") == company
        ]

        # Show the latest 8 known publications for the company.
        latest_publications = company_publications[:8]

        check = checks_by_company.get(company)

        if check and check.get("status") == "error":
            state = "error"
        elif company_updates:
            state = "updates"
        else:
            state = "clear"

        companies.append(
            {
                "company": company,
                "url": site["url"],
                "update_count": len(company_updates),
                "state": state,
                "check": check,
                "updates": company_updates,
                "latest": latest_publications,
            }
        )

    return current_updates, checks, companies


# =============================================================
# MAIN DASHBOARD
# =============================================================

@app.route("/")
def home():

    publications, checks, companies = dashboard_data()

    successful_checks = len(
        [
            check
            for check in checks
            if check.get("status") == "ok"
        ]
    )

    failed_checks = len(
        [
            check
            for check in checks
            if check.get("status") == "error"
        ]
    )

    return render_template(
        "index.html",
        publications=publications,
        companies=companies,
        total_websites=len(SITES),
        websites_checked=successful_checks,
        failed_checks=failed_checks,
        checks=checks,
    )


# =============================================================
# JSON REPORT API
# =============================================================

@app.route("/api/report")
def api_report():

    publications, checks, companies = dashboard_data()

    return jsonify(
        {
            "total_websites": len(SITES),
            "websites_checked": len(
                [
                    check
                    for check in checks
                    if check.get("status") == "ok"
                ]
            ),
            "failed_checks": len(
                [
                    check
                    for check in checks
                    if check.get("status") == "error"
                ]
            ),
            "publications": publications,
            "checks": checks,
            "companies": companies,
        }
    )


# =============================================================
# RUN APPLICATION
# =============================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Run the local website change monitor dashboard."
    )

    parser.add_argument(
        "--port",
        type=int,
        default=5000,
    )

    args = parser.parse_args()

    app.run(
        host="127.0.0.1",
        port=args.port,
        debug=False,
    )