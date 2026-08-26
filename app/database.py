import sqlite3
from pathlib import Path


DB_PATH = Path("data/monitor.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def initialize_database():
    with get_connection() as connection:

        # Existing website-level snapshot table
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS website_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                url TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                checked_at TEXT NOT NULL
            )
            """
        )

        # New publication-level monitoring table
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS publications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                item_type TEXT NOT NULL,
                title TEXT NOT NULL,
                source_url TEXT NOT NULL,
                website_date TEXT,
                first_found_at TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                summary TEXT,
                status TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS site_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                url TEXT NOT NULL,
                checked_at TEXT NOT NULL,
                status TEXT NOT NULL,
                error TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS publication_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                publication_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                captured_at TEXT NOT NULL
            )
            """
        )

        connection.execute("UPDATE publications SET company = 'Ma''aden' WHERE company = 'Maaden'")
        connection.execute("UPDATE site_checks SET company = 'Ma''aden' WHERE company = 'Maaden'")
        connection.execute("UPDATE website_snapshots SET company = 'Ma''aden' WHERE company = 'Maaden'")

        # Earlier generic discovery could mistake investor-section navigation
        # categories for publications. They are deliberately never reportable.
        connection.execute(
            "UPDATE publications SET status = 'seen' WHERE company = 'Ma''aden' "
            "AND lower(title) IN (?, ?, ?, ?, ?, ?, ?, ?)",
            ("corporate overview", "financial information", "share information",
             "analyst coverage", "tadawul announcement", "shareholder meeting",
             "email subscription", "maaden strategy 2040"),
        )

        columns = {row[1] for row in connection.execute("PRAGMA table_info(publications)")}
        if "canonical_key" not in columns:
            connection.execute("ALTER TABLE publications ADD COLUMN canonical_key TEXT")
        if "last_seen_at" not in columns:
            connection.execute("ALTER TABLE publications ADD COLUMN last_seen_at TEXT")

        rows = connection.execute(
            "SELECT id, title FROM publications WHERE canonical_key IS NULL"
        ).fetchall()
        for publication_id, title in rows:
            key = "".join(character.lower() if character.isalnum() else " " for character in title)
            key = " ".join(key.split())
            connection.execute(
                "UPDATE publications SET canonical_key = ? WHERE id = ?",
                (key, publication_id),
            )

        connection.commit()


# ---------------------------------------------------------
# Existing website snapshot functions
# ---------------------------------------------------------

def save_snapshot(company, url, content_hash, checked_at):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO website_snapshots
            (company, url, content_hash, checked_at)
            VALUES (?, ?, ?, ?)
            """,
            (company, url, content_hash, checked_at),
        )
        connection.commit()


def get_latest_snapshot(company):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT company, url, content_hash, checked_at
            FROM website_snapshots
            WHERE company = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (company,),
        )

        return cursor.fetchone()


def save_check(company, url, checked_at, status, error=None):
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO site_checks (company, url, checked_at, status, error) VALUES (?, ?, ?, ?, ?)",
            (company, url, checked_at, status, error),
        )
        connection.commit()


def get_latest_checks():
    with get_connection() as connection:
        return connection.execute(
            "SELECT company, url, checked_at, status, error FROM site_checks "
            "WHERE id IN (SELECT MAX(id) FROM site_checks GROUP BY company) ORDER BY company"
        ).fetchall()


# ---------------------------------------------------------
# Publication functions
# ---------------------------------------------------------

def save_publication(
    company,
    item_type,
    title,
    source_url,
    website_date,
    first_found_at,
    content_hash,
    summary,
    status,
    canonical_key=None,
    last_seen_at=None,
):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO publications
            (
                company,
                item_type,
                title,
                source_url,
                website_date,
                first_found_at,
                content_hash,
                summary,
                status,
                canonical_key,
                last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company,
                item_type,
                title,
                source_url,
                website_date,
                first_found_at,
                content_hash,
                summary,
                status,
                canonical_key,
                last_seen_at,
            ),
        )

        connection.commit()
        return cursor.lastrowid


def get_publication_by_title(company, title):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                id,
                company,
                item_type,
                title,
                source_url,
                website_date,
                first_found_at,
                content_hash,
                summary,
                status
            FROM publications
            WHERE company = ?
              AND title = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (company, title),
        )

        return cursor.fetchone()


def get_publication_by_key(company, canonical_key):
    with get_connection() as connection:
        return connection.execute(
            "SELECT id, company, item_type, title, source_url, website_date, first_found_at, "
            "content_hash, summary, status FROM publications WHERE company = ? AND canonical_key = ? LIMIT 1",
            (company, canonical_key),
        ).fetchone()


def mark_publications_seen(company):
    with get_connection() as connection:
        connection.execute(
            "UPDATE publications SET status = 'seen' "
            "WHERE company = ? AND status IN ('new', 'updated')",
            (company,),
        )
        connection.commit()


def get_publication_by_hash(company, content_hash):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                id,
                company,
                item_type,
                title,
                source_url,
                website_date,
                first_found_at,
                content_hash,
                summary,
                status
            FROM publications
            WHERE company = ?
              AND content_hash = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (company, content_hash),
        )

        return cursor.fetchone()


def get_all_publications():
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                id,
                company,
                item_type,
                title,
                source_url,
                website_date,
                first_found_at,
                content_hash,
                summary,
                status
            FROM publications
            ORDER BY first_found_at DESC
            """
        )

        return cursor.fetchall()


def update_publication(
    publication_id,
    source_url,
    website_date,
    content_hash,
    summary,
    status,
    last_seen_at=None,
):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE publications
            SET
                source_url = ?,
                website_date = ?,
                content_hash = ?,
                summary = ?,
                status = ?,
                last_seen_at = ?
            WHERE id = ?
            """,
            (
                source_url,
                website_date,
                content_hash,
                summary,
                status,
                last_seen_at,
                publication_id,
            ),
        )

        connection.commit()


def save_publication_version(publication_id, content, captured_at):
    """Keep content evidence so a later update can describe the real difference."""
    if publication_id is None:
        return
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO publication_versions (publication_id, content, captured_at) VALUES (?, ?, ?)",
            (publication_id, content[:12000], captured_at),
        )
        connection.commit()
        return cursor.lastrowid


def get_latest_publication_version(publication_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT content FROM publication_versions WHERE publication_id = ? ORDER BY id DESC LIMIT 1",
            (publication_id,),
        ).fetchone()
        return row[0] if row else ""


def publication_exists(company, title):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT 1
            FROM publications
            WHERE company = ?
              AND title = ?
            LIMIT 1
            """,
            (company, title),
        )

        return cursor.fetchone() is not None
