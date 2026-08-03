"""Economic Times — Economy section (RBI policy, GDP, inflation, trade etc)."""
from scraper.sources._rss_base import fetch_rss

FEED_URL = "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms"


def fetch() -> list[dict]:
    return fetch_rss(FEED_URL, source_name="Economic Times - Economy")
