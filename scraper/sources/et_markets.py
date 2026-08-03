"""Economic Times — Markets section. Already market-specific, no filter needed."""
from scraper.sources._rss_base import fetch_rss

FEED_URL = "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"


def fetch() -> list[dict]:
    return fetch_rss(FEED_URL, source_name="Economic Times - Markets")
