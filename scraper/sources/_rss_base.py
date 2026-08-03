"""
Shared helper for fetching and normalising RSS feeds.
Every source file (et_markets.py, moneycontrol.py, ...) calls fetch_rss()
with its own feed URL and source name — keeps each source file to ~10 lines.
"""
import feedparser
import requests
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; market-sentiment-monitor/1.0)",
}


def fetch_rss(url: str, source_name: str, keyword_filter=None) -> list[dict]:
    """
    Fetch an RSS feed and return a list of normalised items:
    {title, url, source, published_at (ISO8601 UTC), summary}

    keyword_filter: optional list of lowercase keywords — if given, an item
    is kept only if at least one keyword appears in its title.
    """
    results = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [{source_name}] fetch failed: {e}")
        return results

    parsed = feedparser.parse(resp.content)

    for entry in parsed.entries:
        title = entry.get("title", "").strip()
        if not title:
            continue

        if keyword_filter:
            lowered = title.lower()
            if not any(kw in lowered for kw in keyword_filter):
                continue

        published_at = _parse_date(entry)

        results.append({
            "title": title,
            "url": entry.get("link", ""),
            "source": source_name,
            "published_at": published_at,
            "summary": entry.get("summary", "")[:300],
        })

    return results


def _parse_date(entry) -> str:
    """Best-effort parse of an RSS entry's publish date to ISO8601 UTC."""
    raw = entry.get("published", "") or entry.get("updated", "")
    if raw:
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError):
            pass
    return datetime.now(timezone.utc).isoformat()
