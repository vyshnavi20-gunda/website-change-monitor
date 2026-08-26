from app import monitor
from app.scraper import looks_like_publication_link, publications_from_html
from app.notify import make_notification, notify_webhook, notify_windows_popup, notify_windows_toast

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_check_website_detects_new_then_unchanged(monkeypatch):
    stored = {}
    monkeypatch.setattr(monitor, "initialize_database", lambda: None)
    monkeypatch.setattr(monitor, "mark_publications_seen", lambda company: None)
    monkeypatch.setattr(monitor, "save_check", lambda *args: None)
    monkeypatch.setattr(monitor, "get_publication_by_key", lambda company, key: stored.get(key))

    def save(company, item_type, title, source_url, website_date, first_found_at,
             content_hash, summary, status, key, last_seen_at):
        stored[key] = (1, company, item_type, title, source_url, website_date,
                       first_found_at, content_hash, summary, status)

    monkeypatch.setattr(monitor, "save_publication", save)
    monkeypatch.setattr(monitor, "update_publication", lambda *args: None)
    item = {"title": "Quarterly results", "url": "https://example.test/results",
            "date": "26 August 2026", "type": "Investor Update"}
    monkeypatch.setattr(monitor, "fetch_publications", lambda *args: [item])
    monkeypatch.setattr(monitor, "fetch_page_text", lambda url: "Meaningful official article text")

    result = monitor.check_website("Maaden", "https://example.test/", ())

    assert result["company"] == "Maaden"
    assert result["url"] == "https://example.test/"
    assert "changed" in result
    assert "checked_at" in result
    assert len(result["new"]) == 1

    later = monitor.check_website("Maaden", "https://example.test/", ())
    assert later["new"] == []
    assert later["updated"] == []


def test_excludes_investor_navigation_but_keeps_a_dated_release():
    assert not looks_like_publication_link(
        "Stock quote", "https://investors.example.test/stock-information/stock-quote"
    )
    assert looks_like_publication_link(
        "2026 Annual Report", "https://investors.example.test/reports/annual-report.pdf"
    )

    publications = publications_from_html(
        """
        <article><time datetime='2026-08-26'>26 August 2026</time>
        <a href='/news/new-results'>New results announcement</a></article>
        """,
        "https://example.test/news",
        "Example",
    )

    assert publications[0]["date"] == "2026-08-26"


def test_notification_only_posts_when_a_publication_changed(monkeypatch):
    results = [{
        "company": "Example Metals",
        "new": [{"type": "Press Release", "title": "New results", "date": "26 August 2026",
                 "url": "https://example.test/new-results"}],
        "updated": [],
    }]
    payload = make_notification(results)
    assert "NEW | Example Metals" in payload["text"]
    assert make_notification([{"company": "Example", "new": [], "updated": []}]) is None

    posted = {}

    class Response:
        def raise_for_status(self):
            return None

    def post(url, json, timeout):
        posted.update(url=url, payload=json, timeout=timeout)
        return Response()

    monkeypatch.setattr("app.notify.requests.post", post)
    assert notify_webhook(results, "https://hooks.example.test/monitor") == "Notification sent for 1 publication(s)."
    assert posted["payload"] == payload


def test_popup_is_skipped_when_there_are_no_changes():
    assert notify_windows_popup([{"company": "Example", "new": [], "updated": []}]) is None
    assert notify_windows_toast([{"company": "Example", "new": [], "updated": []}]) is None
