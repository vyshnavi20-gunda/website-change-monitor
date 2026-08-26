from app import monitor


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
    monkeypatch.setattr(monitor, "fetch_publications", lambda url, company: [item])
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
