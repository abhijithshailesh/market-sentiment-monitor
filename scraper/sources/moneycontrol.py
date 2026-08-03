"""Moneycontrol — latest news. Mixed topics, so we apply the keyword filter."""
import yaml
from pathlib import Path
from scraper.sources._rss_base import fetch_rss

FEED_URL = "https://www.moneycontrol.com/rss/latestnews.xml"


def fetch() -> list[dict]:
    config = yaml.safe_load(
        (Path(__file__).parent.parent.parent / "config.yaml").read_text()
    )
    keywords = [k.lower() for k in config.get("filters", {}).get("required_keywords", [])]
    return fetch_rss(FEED_URL, source_name="Moneycontrol", keyword_filter=keywords)
