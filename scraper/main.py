"""
Daily Indian stock market sentiment monitor.
Run manually:  python -m scraper.main
Run on schedule via .github/workflows/daily-sentiment.yml
"""
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from scraper.sources import et_markets, et_economy, moneycontrol, business_standard
from storage.local_sync import save_day

SOURCES = [
    ("Economic Times - Markets", et_markets.fetch),
    ("Economic Times - Economy", et_economy.fetch),
    ("Moneycontrol", moneycontrol.fetch),
    ("Business Standard", business_standard.fetch),
]


def ai_enabled() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


def main():
    config = yaml.safe_load((Path(__file__).parent.parent / "config.yaml").read_text())
    tz_name = config.get("output", {}).get("timezone", "Asia/Kolkata")
    freshness_hours = config.get("freshness_hours", 20)

    all_items = []
    for name, fetch_fn in SOURCES:
        try:
            items = fetch_fn()
            print(f"[{name}] {len(items)} items")
            all_items.extend(items)
        except Exception as e:
            print(f"[{name}] FAILED: {e}")

    # Dedupe by URL
    seen, deduped = set(), []
    for item in all_items:
        url = item.get("url", "")
        if url and url not in seen:
            seen.add(url)
            deduped.append(item)
    print(f"Unique items: {len(deduped)}")

    # Keep only items published within the freshness window
    cutoff = datetime.now(timezone.utc) - timedelta(hours=freshness_hours)
    fresh = []
    for item in deduped:
        try:
            published = datetime.fromisoformat(item["published_at"])
        except (ValueError, KeyError):
            published = datetime.now(timezone.utc)
        if published >= cutoff:
            fresh.append(item)
    print(f"Fresh items (last {freshness_hours}h): {len(fresh)}")

    if not fresh:
        print("No fresh market-relevant headlines found — nothing to save.")
        sys.exit(0)

    if ai_enabled():
        from ai.pipeline import analyse_batch, generate_daily_summary
        fresh = analyse_batch(fresh)
        summary = generate_daily_summary(fresh)
    else:
        print("[AI] Skipped — GEMINI_API_KEY not set. Saving raw headlines only.")
        summary = {
            "overall_sentiment": "unknown",
            "summary": "AI enrichment skipped (no GEMINI_API_KEY set).",
            "bullish_count": 0, "bearish_count": 0, "neutral_count": 0,
        }

    today = datetime.now(ZoneInfo(tz_name)).strftime("%Y-%m-%d")
    path = save_day(today, fresh, summary)

    print(f"\nSaved: {path}")
    print(f"Overall sentiment: {summary['overall_sentiment']}")
    print(f"Summary: {summary['summary']}")


if __name__ == "__main__":
    main()
