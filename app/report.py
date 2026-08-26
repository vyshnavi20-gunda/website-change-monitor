from app.database import get_all_publications, get_latest_checks
def get_report():
    return get_all_publications()


def print_report():
    records = get_report()

    print("\nWEBSITE CHANGE MONITOR REPORT")
    print("=" * 60)

    reported = False
    for record in records:
        _, company, item_type, title, source_url, website_date, first_found_at, _, summary, status = record
        if status not in {"new", "updated"}:
            continue
        reported = True
        print(f"{company} | {item_type} | {status.upper()}")
        print(f"Title: {title}")
        print(f"Source: {source_url}")
        print(f"Website date: {website_date or 'Not shown'}")
        print(f"First found: {first_found_at}")
        print(f"Summary: {summary or 'No summary available'}")
        print("-" * 60)
    if not reported:
        print("No new or meaningfully changed publications.")
    print("Latest checks:")
    for company, url, checked_at, status, error in get_latest_checks():
        message = f"{company}: {status} at {checked_at}"
        if error:
            message += f" | {error}"
        print(message)