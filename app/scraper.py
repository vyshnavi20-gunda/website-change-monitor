from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
import requests
import hashlib

REQUEST_HEADERS = {"User-Agent": "WebsiteChangeMonitor/1.0"}


def extract_meaningful_text(html: str) -> str:
    """Prefer article/main content so menus and widgets do not drive changes."""
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(
        ["script", "style", "noscript", "nav", "footer", "header", "aside", "form"]
    ):
        element.decompose()

    primary = soup.select_one(
        "article, main, [role='main'], .article-body, .news-detail"
    )

    return (primary or soup).get_text(" ", strip=True)


def fetch_page_text(url: str) -> str:
    """Open a webpage and return its visible text."""

    try:
        response = requests.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=15,
        )
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()

        if (
            "application/pdf" in content_type
            or url.lower().split("?")[0].endswith(".pdf")
        ):
            digest = hashlib.sha256(response.content).hexdigest()
            return f"PDF document | size: {len(response.content)} bytes | hash: {digest}"

        text = extract_meaningful_text(response.text)

        if "performing security verification" in text.lower():
            raise RuntimeError("anti-bot verification page returned instead of the publication")

        if len(text) >= 120:
            return text

    except requests.RequestException:
        pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=15000,
        )

        try:
            if url.lower().split("?")[0].endswith(".pdf"):
                return "PDF document (browser text extraction unavailable)"

            text = page.locator("body").inner_text()
            if "performing security verification" in text.lower():
                raise RuntimeError("anti-bot verification page returned instead of the publication")
            return text

        finally:
            browser.close()


PUBLICATION_KEYWORDS = [
    "news",
    "press",
    "press release",
    "media",
    "investor",
    "investors",
    "reports",
    "report",
    "financial",
    "results",
    "announcement",
    "publications",
    "release",
    "updates",
    "notices",
]


NAVIGATION_TITLES = {
    "news",
    "media",
    "investors",
    "investor relations",
    "reports",
    "publications",
    "press releases",
    "announcements",
    "updates",
    "search",
    "contact us",
    "investor contacts",
    "financial calendar",
    "stock information",
    "corporate governance",
    "corporate overview",
    "financial information",
    "share information",
    "analyst coverage",
    "tadawul announcement",
    "shareholder meeting",
    "email subscription",
    "maaden strategy 2040",
    "unsubscribe",
    "subscribe",
    "subscribe to news",
    "news subscription",
    "learn more",
    "read more",
    "continue reading",
    "more",
    "see all",
    "see all events",
    "next event",
    "skip to main content",
}


GENERIC_NAVIGATION_PREFIXES = (
    "go to:",
    "go to ",
    "visit ",
    "view ",
    "see ",
    "open ",
    "back to ",
    "skip to ",
)


GENERIC_NAVIGATION_WORDS = {
    "unsubscribe",
    "subscribe",
    "subscription",
    "login",
    "log in",
    "sign in",
    "sign up",
    "menu",
    "home",
    "next event",
    "previous event",
    "all news",
    "all reports",
    "all publications",
    "all announcements",
    "contact",
    "contact us",
}


def normalize_url(url: str) -> str:
    """Remove fragments and normalize a URL."""

    parsed = urlparse(url)

    return parsed._replace(
        fragment=""
    ).geturl().rstrip("/")


def looks_like_publication_link(text: str, url: str) -> bool:
    """Return True when a link looks like an official publication."""

    normalized_text = re.sub(r"\s+", " ", text.lower()).strip()
    lowered_url = url.lower()

    # ---------------------------------------------------------
    # 1. Reject obvious navigation and utility links.
    # ---------------------------------------------------------

    if normalized_text in NAVIGATION_TITLES:
        return False

    if normalized_text in GENERIC_NAVIGATION_WORDS:
        return False

    if normalized_text.startswith(GENERIC_NAVIGATION_PREFIXES):
        return False

    # Links containing these labels are normally navigation,
    # subscription, accessibility or account controls rather
    # than actual corporate publications.
    if any(
        phrase in normalized_text
        for phrase in [
            "skip to",
            "go to:",
            "unsubscribe",
            "subscribe",
            "sign in",
            "log in",
            "cookie",
            "accept cookies",
            "privacy settings",
            "manage preferences",
        ]
    ):
        return False

    # ---------------------------------------------------------
    # 2. Reject generic section URLs.
    # ---------------------------------------------------------

    path = urlparse(url).path.lower().rstrip("/")

    if path in {
        "/news",
        "/media",
        "/reports",
        "/publications",
        "/investors",
        "/investor-relations",
        "/announcements",
        "/updates",
        "/search",
        "/contact",
        "/subscribe",
        "/unsubscribe",
    }:
        return False

    # ---------------------------------------------------------
    # 3. Reject obvious utility URL patterns.
    # ---------------------------------------------------------

    if any(
        pattern in lowered_url
        for pattern in [
            "/subscribe",
            "/unsubscribe",
            "/search?",
            "category=",
            "tag=",
            "filter=",
            "login",
            "signin",
            "signup",
        ]
    ):
        return False

    # ---------------------------------------------------------
    # 4. A keyword in an investor-section URL alone is not enough: it
    # would turn every share-price or governance navigation page into an
    # update.  Accept a meaningful label, a document, or a news-style URL.
    # ---------------------------------------------------------

    if lowered_url.split("?")[0].endswith((".pdf", ".xlsx", ".xls")):
        return True

    if any(keyword in normalized_text for keyword in PUBLICATION_KEYWORDS):
        return True

    return any(
        marker in urlparse(lowered_url).path
        for marker in ("/news/", "/press-releases/", "/releases/", "/announcements/")
    ) and len(normalized_text) >= 12


def extract_date(text: str) -> str | None:
    """Try to find a publication date in visible text."""

    patterns = [
        r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{1,2}/\d{1,2}/\d{4}\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(0)

    return None


def title_for_link(text: str, url: str) -> str:
    """Use the URL slug when a site labels every article link generically."""

    if text.lower().strip() not in {
        "learn more",
        "continue reading",
        "read more",
        "more",
    }:
        cleaned = re.sub(r"\s+", " ", text).strip()
        # Some corporate sites wrap an entire card in one link.  In that
        # case the ellipsis separates its headline from teaser copy.
        if "..." in cleaned:
            cleaned = cleaned.split("...", 1)[0].strip()
        return cleaned[:250]

    slug = urlparse(url).path.rstrip("/").split("/")[-1]

    return (
        re.sub(r"[-_]+", " ", slug).strip().title()[:500]
        or text[:500]
    )


def date_near_link(link) -> str | None:
    """Find a website date near a listing link, rather than only in its label."""
    if link.find("time"):
        value = link.find("time").get("datetime") or link.find("time").get_text(" ", strip=True)
        if value:
            return value.strip()

    container = link
    for _ in range(3):
        container = container.parent
        if container is None:
            break
        time_tag = container.find("time")
        if time_tag:
            value = time_tag.get("datetime") or time_tag.get_text(" ", strip=True)
            if value:
                return value.strip()
        date = extract_date(container.get_text(" ", strip=True))
        if date:
            return date
    return None


def publications_from_html(
    html: str,
    url: str,
    company: str,
    allowed_hosts: tuple[str, ...] = (),
) -> list[dict]:
    """Extract candidates from either a fast HTTP response or rendered HTML."""

    publications = []
    seen_urls = set()

    soup = BeautifulSoup(html, "html.parser")

    for link in soup.find_all("a", href=True):

        absolute_url = normalize_url(
            urljoin(url, link["href"])
        )

        text = link.get_text(" ", strip=True)

        if not text:
            continue

        if absolute_url in seen_urls:
            continue

        if not looks_like_publication_link(
            text,
            absolute_url,
        ):
            continue

        hosts = set(allowed_hosts) or {urlparse(url).netloc}
        if urlparse(absolute_url).netloc not in hosts:
            continue

        seen_urls.add(absolute_url)

        publications.append(
            {
                "company": company,
                "title": title_for_link(
                    text,
                    absolute_url,
                ),
                "url": absolute_url,
                "date": date_near_link(link),
                "type": classify_publication(
                    text,
                    absolute_url,
                ),
            }
        )

    return publications


def fetch_publications(
    url: str,
    company: str,
    allowed_hosts: tuple[str, ...] = (),
) -> list[dict]:
    """
    Open a company website and discover likely publication links.

    JavaScript-rendered pages are supported through Playwright.
    """

    try:
        response = requests.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=20,
        )

        response.raise_for_status()

        publications = publications_from_html(
            response.text,
            url,
            company, allowed_hosts,
        )

        if publications:
            return publications

    except requests.RequestException:
        pass

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=15000,
        )

        page.wait_for_timeout(1000)

        html = page.content()

        browser.close()

    return publications_from_html(
        html,
        url,
        company, allowed_hosts,
    )


def classify_publication(
    title: str,
    url: str,
) -> str:
    """Classify a discovered publication."""

    value = f"{title} {url}".lower()

    if "investor" in value or "financial" in value:
        return "Investor Update"

    if "report" in value:
        return "Report"

    if "press" in value or "release" in value:
        return "Press Release"

    if "notice" in value:
        return "Exchange Notice"

    if "news" in value or "media" in value:
        return "News"

    return "Official Publication"
