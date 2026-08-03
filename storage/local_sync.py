"""Local-file storage: no external service. Writes into the data/ folder,
which the GitHub Action commits back to the repo after each run."""
import csv
import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data"
HISTORY_CSV = DATA_DIR / "history.csv"
LATEST_JSON = DATA_DIR / "latest.json"


def save_day(date_str: str, items: list[dict], summary: dict) -> Path:
    """Writes data/YYYY-MM-DD.json, refreshes data/latest.json, and appends
    a row to data/history.csv for trend tracking over time."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    day_record = {
        "date": date_str,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "overall_sentiment": summary.get("overall_sentiment", "neutral"),
        "summary": summary.get("summary", ""),
        "bullish_count": summary.get("bullish_count", 0),
        "bearish_count": summary.get("bearish_count", 0),
        "neutral_count": summary.get("neutral_count", 0),
        "headline_count": len(items),
        "headlines": items,
    }

    day_path = DATA_DIR / f"{date_str}.json"
    day_path.write_text(json.dumps(day_record, indent=2, ensure_ascii=False))

    LATEST_JSON.write_text(json.dumps(day_record, indent=2, ensure_ascii=False))

    _append_history_row(day_record)

    return day_path


def _append_history_row(day_record: dict):
    is_new_file = not HISTORY_CSV.exists()

    # Avoid duplicate rows if the workflow is re-run manually same day
    if HISTORY_CSV.exists():
        existing = HISTORY_CSV.read_text()
        if f"\n{day_record['date']}," in existing or existing.startswith(day_record["date"] + ","):
            _rewrite_history_row(day_record)
            return

    with open(HISTORY_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        if is_new_file:
            writer.writerow([
                "date", "overall_sentiment", "bullish_count",
                "bearish_count", "neutral_count", "headline_count", "summary",
            ])
        writer.writerow([
            day_record["date"],
            day_record["overall_sentiment"],
            day_record["bullish_count"],
            day_record["bearish_count"],
            day_record["neutral_count"],
            day_record["headline_count"],
            day_record["summary"].replace("\n", " "),
        ])


def _rewrite_history_row(day_record: dict):
    """Replace an existing row for the same date (manual re-run same day)."""
    rows = list(csv.reader(HISTORY_CSV.read_text().splitlines()))
    header, body = rows[0], rows[1:]
    body = [r for r in body if r and r[0] != day_record["date"]]
    body.append([
        day_record["date"],
        day_record["overall_sentiment"],
        day_record["bullish_count"],
        day_record["bearish_count"],
        day_record["neutral_count"],
        day_record["headline_count"],
        day_record["summary"].replace("\n", " "),
    ])
    with open(HISTORY_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(body)
