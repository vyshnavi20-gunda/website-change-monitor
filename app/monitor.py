import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

from app.database import (
    get_publication_by_key,
    initialize_database,
    mark_publications_seen,
    save_check,
    save_publication,
    update_publication,
    get_latest_publication_version,
    save_publication_version,
)
from app.scraper import fetch_page_text, fetch_publications


# Checking the newest 15 publications per company keeps the daily run bounded.
# Older pages are already in the historical baseline; new links are discovered
# from the curated listing sources on the next run.
MAX_PUBLICATIONS_PER_SITE = 15


def canonical_company(company: str) -> str:
    return (
        "Ma'aden"
        if company.lower().replace("'", "") == "maaden"
        else company
    )


def calculate_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_summary(
    item: dict,
    content: str,
    status: str,
    url_changed: bool = False,
    previous_content: str = "",
) -> str:
    """Create a compact, business-readable change explanation."""

    compact = re.sub(r"\s+", " ", content).strip()

    sentences = re.split(
        r"(?<=[.!?])\s+",
        compact,
    )

    excerpt = " ".join(
        sentence for sentence in sentences[:2] if sentence
    )[:420]

    if not excerpt:
        excerpt = (
            "The source page did not provide readable article text."
        )

    # NEW publication
    if status == "new":
        first_line = (
            f"New official publication: {item['title']}."
        )

        change_line = (
            "What changed: New publication discovered since "
            "the previous check."
        )

    # UPDATED because URL changed
    elif url_changed:
        first_line = (
            f"Updated: {item['title']} moved to a new "
            "official source address."
        )

        change_line = (
            "What changed: The official source URL changed."
        )

    # UPDATED because content changed
    else:
        first_line = (
            f"Updated: {item['title']} has changed "
            "since the prior check."
        )

        if previous_content:
            before = {
                re.sub(r"\s+", " ", value).strip()
                for value in re.split(
                    r"(?<=[.!?])\s+",
                    previous_content,
                )
                if value.strip()
            }

            added = next(
                (
                    value
                    for value in sentences
                    if value and value not in before
                ),
                "",
            )

            if added:
                change_line = (
                    f"What changed: {added[:300]}"
                )
            else:
                change_line = (
                    "What changed: The article wording or "
                    "structure changed."
                )
        else:
            change_line = (
                "What changed: The article content changed "
                "since the previous saved version."
            )

    return (
        f"{first_line}\n"
        f"{change_line}\n"
        f"Current page excerpt: {excerpt}"
    )


def check_website(
    company: str,
    url: str,
    sections: tuple[str, ...] = (),
    allowed_hosts: tuple[str, ...] = (),
) -> dict:

    initialize_database()

    stored_company = canonical_company(company)

    mark_publications_seen(stored_company)

    checked_at = datetime.now(timezone.utc).isoformat()

    try:
        candidates = {}
        section_errors = []
        successful_sections = 0

        # Check the curated publication sources before the homepage.  Do not
        # probe guessed paths: a 404 is not useful monitoring evidence.
        paths = tuple(
            dict.fromkeys(
                (*sections, url)
            )
        )

        for path in paths:

            section_url = urljoin(url, path)

            try:
                discovered = fetch_publications(
                    section_url,
                    stored_company, allowed_hosts,
                )

                successful_sections += 1

            except Exception as error:

                section_errors.append(
                    f"{section_url}: {error}"
                )

                save_check(
                    stored_company,
                    section_url,
                    checked_at,
                    "error",
                    str(error),
                )

                continue

            for item in discovered:

                key = re.sub(
                    r"[^a-z0-9]+",
                    " ",
                    item["title"].lower(),
                ).strip()

                # Ignore empty or meaningless titles
                if not key or len(key) < 5:
                    continue

                candidates[key] = item

                if len(candidates) >= MAX_PUBLICATIONS_PER_SITE:
                    break

        new_items = []
        updated_items = []

        for key, item in list(candidates.items())[:MAX_PUBLICATIONS_PER_SITE]:

            try:
                content = fetch_page_text(
                    item["url"]
                )
            except Exception as error:
                # Do not treat a failed article fetch
                # as an update.
                section_errors.append(
                    f"{item['url']}: {error}"
                )
                continue

            content = re.sub(
                r"\s+",
                " ",
                content,
            ).strip()

            # Skip pages where we could not obtain useful content.
            if not content:
                continue

            content_hash = calculate_hash(content)

            previous = get_publication_by_key(
                stored_company,
                key,
            )

            # ==================================================
            # NEW PUBLICATION
            # ==================================================

            if previous is None:

                summary = make_summary(
                    item,
                    content,
                    "new",
                )

                publication_id = save_publication(
                    stored_company,
                    item["type"],
                    item["title"],
                    item["url"],
                    item["date"],
                    checked_at,
                    content_hash,
                    summary,
                    "new",
                    key,
                    checked_at,
                )

                save_publication_version(
                    publication_id,
                    content,
                    checked_at,
                )

                new_items.append(item)

                continue

            # ==================================================
            # EXISTING PUBLICATION
            # ==================================================

            previous_url = previous[4]
            previous_hash = previous[7]

            url_changed = (
                previous_url != item["url"]
            )

            content_changed = (
                previous_hash != content_hash
            )

            changed = (
                content_changed
                or url_changed
            )

            # Get previous saved content only when
            # we actually need it.
            previous_content = ""

            if changed:
                previous_content = (
                    get_latest_publication_version(
                        previous[0]
                    )
                )

            # ==================================================
            # UPDATED PUBLICATION
            # ==================================================

            if changed:

                summary = make_summary(
                    item,
                    content,
                    "updated",
                    url_changed,
                    previous_content,
                )

                update_publication(
                    previous[0],
                    item["url"],
                    item["date"],
                    content_hash,
                    summary,
                    "updated",
                    checked_at,
                )

                updated_items.append(item)

            # ==================================================
            # NO CHANGE
            # ==================================================

            else:

                update_publication(
                    previous[0],
                    item["url"],
                    item["date"],
                    content_hash,
                    previous[8],
                    "seen",
                    checked_at,
                )

                save_publication_version(
                    previous[0],
                    content,
                    checked_at,
                )

        # If every section failed, this is a real failed check.
        if not successful_sections:
            raise RuntimeError(
                "No publication section could be checked. "
                + "; ".join(section_errors)
            )

        # Save successful website-level check.
        save_check(
            stored_company,
            url,
            checked_at,
            "ok",
            "; ".join(section_errors) or None,
        )

        return {
            "company": company,
            "url": url,
            "checked_at": checked_at,
            "status": "ok",
            "new": new_items,
            "updated": updated_items,
            "changed": bool(
                new_items or updated_items
            ),
            "error": (
                "; ".join(section_errors)
                or None
            ),
        }

    except Exception as error:

        save_check(
            stored_company,
            url,
            checked_at,
            "error",
            str(error),
        )

        return {
            "company": company,
            "url": url,
            "checked_at": checked_at,
            "status": "error",
            "new": [],
            "updated": [],
            "changed": False,
            "error": str(error),
        }
