from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, List, Set
from urllib.parse import urljoin

from playwright.sync_api import Browser, Error as PlaywrightError, Page, TimeoutError, sync_playwright

from .models import Artist

LINEUP_URL = "https://szigetfestival.com/en/programs-lineup-2026#/"
BASE_URL = "https://szigetfestival.com"
CACHE_FILE = Path("data/artists_cache.json")

DATE_RE = re.compile(r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)?\s*\d{1,2}\s+[A-Za-z]+\s+2026", re.IGNORECASE)


class ScrapeError(RuntimeError):
    """Raised when live scraping cannot be completed."""


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _safe_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "artist"


def _collect_artist_links(page: Page) -> List[str]:
    page.goto(LINEUP_URL, wait_until="domcontentloaded", timeout=120_000)
    page.wait_for_timeout(2_500)

    # Scroll to trigger lazy-loaded cards in the SPA.
    for _ in range(6):
        page.mouse.wheel(0, 3000)
        page.wait_for_timeout(350)

    selectors = [
        "a[href*='/programs/']",
        "a[href*='/en/programs/']",
        "a[href*='programs-lineup-2026']",
        "a[href*='#/programs/']",
    ]

    links: Set[str] = set()
    for selector in selectors:
        hrefs = page.eval_on_selector_all(selector, "els => els.map(el => el.getAttribute('href'))")
        for href in hrefs:
            if not href:
                continue
            normalized = href
            if normalized.startswith("#"):
                normalized = f"/en/programs-lineup-2026{normalized}"
            absolute = urljoin(BASE_URL, normalized)
            if "programs-lineup-2026" in absolute and "#/" in absolute:
                links.add(absolute)
            elif "/programs/" in absolute:
                links.add(absolute)

    return sorted(links)


def _extract_text(page: Page, selectors: Iterable[str]) -> str:
    for selector in selectors:
        locator = page.locator(selector).first
        if locator.count():
            text = _normalize_whitespace(locator.inner_text())
            if text:
                return text
    return ""


def _extract_date_from_text_fallback(page: Page) -> str:
    text = _normalize_whitespace(page.inner_text("body"))
    match = DATE_RE.search(text)
    return match.group(0) if match else ""


def _extract_artist(page: Page, url: str) -> Artist | None:
    page.goto(url, wait_until="domcontentloaded", timeout=120_000)
    page.wait_for_timeout(1_200)

    name = _extract_text(
        page,
        [
            "h1",
            "[data-testid='program-title']",
            ".program-detail h1",
            ".lineup-detail h1",
        ],
    )
    if not name:
        return None

    genre = _extract_text(
        page,
        [
            "[data-testid='program-genre']",
            ".program-detail .genre",
            ".lineup-detail .genre",
            "text=/genre/i",
        ],
    )

    biography = _extract_text(
        page,
        [
            "[data-testid='program-description']",
            ".program-detail .description",
            ".lineup-detail .description",
            "article p",
            "main p",
        ],
    )

    performance_date = _extract_text(
        page,
        [
            "[data-testid='program-date']",
            ".program-detail .date",
            ".lineup-detail .date",
            "text=/2026/",
        ],
    ) or _extract_date_from_text_fallback(page)

    return Artist(
        name=name,
        slug=_safe_slug(name),
        genre=genre,
        biography=biography,
        performance_date=performance_date,
        source_url=url,
    )


def scrape_sziget_lineup(limit: int | None = None) -> List[Artist]:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            artists = _scrape_with_browser(browser, limit=limit)
            browser.close()
            if not artists:
                raise ScrapeError("No artists were discovered on the lineup page.")
            return artists
    except (PlaywrightError, TimeoutError) as exc:
        raise ScrapeError(f"Live scrape failed: {exc}") from exc


def _scrape_with_browser(browser: Browser, limit: int | None = None) -> List[Artist]:
    page = browser.new_page()
    links = _collect_artist_links(page)
    if limit is not None:
        links = links[:limit]

    seen_names: Set[str] = set()
    artists: List[Artist] = []
    for link in links:
        try:
            artist = _extract_artist(page, link)
        except PlaywrightError:
            continue
        if not artist:
            continue
        key = artist.name.lower()
        if key in seen_names:
            continue
        seen_names.add(key)
        artists.append(artist)

    return sorted(artists, key=lambda a: a.name.lower())


def save_cache(artists: List[Artist], cache_file: Path = CACHE_FILE) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    payload = [artist.to_dict() for artist in artists]
    cache_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_cache(cache_file: Path = CACHE_FILE) -> List[Artist]:
    if not cache_file.exists():
        return []
    payload = json.loads(cache_file.read_text(encoding="utf-8"))
    return [Artist.from_dict(item) for item in payload]
