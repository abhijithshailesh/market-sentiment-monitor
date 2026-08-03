"""Batched AI enrichment: per-headline sentiment + one overall daily summary."""
import yaml
from pathlib import Path
from ai.client import generate

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def _load_config():
    return yaml.safe_load(CONFIG_PATH.read_text())


def analyse_batch(items: list[dict]) -> list[dict]:
    """Adds 'sentiment' (bullish/bearish/neutral) and 'reason' to each item."""
    config = _load_config()
    ai_cfg = config.get("ai", {})
    model = ai_cfg.get("model", "gemini-2.5-flash")
    rate_limit = ai_cfg.get("rate_limit_seconds", 7.0)
    batch_size = ai_cfg.get("batch_size", 8)
    max_tokens = ai_cfg.get("max_output_tokens", 2048)

    batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    print(f"  [AI] {len(items)} headlines -> {len(batches)} API calls")

    enriched = []
    for i, batch in enumerate(batches):
        print(f"  [AI] Sentiment batch {i + 1}/{len(batches)}...")
        prompt = _build_sentiment_prompt(batch)
        result = generate(prompt, model=model, rate_limit=rate_limit, max_output_tokens=max_tokens)
        analyses = result.get("analyses", [])

        for j, item in enumerate(batch):
            a = analyses[j] if j < len(analyses) else {}
            item["sentiment"] = a.get("sentiment", "neutral")
            item["reason"] = a.get("reason", "")
            enriched.append(item)

    return enriched


def _build_sentiment_prompt(batch: list[dict]) -> str:
    headlines = "\n".join(f"{idx}. {it['title']}" for idx, it in enumerate(batch))
    return f"""You are a financial news analyst covering the Indian stock market (Sensex, Nifty, NSE, BSE).
For each headline below, classify its likely short-term implication for Indian equity market sentiment.

Headlines:
{headlines}

Return ONLY valid JSON, no markdown, no preamble, in this exact shape:
{{"analyses": [{{"sentiment": "bullish|bearish|neutral", "reason": "under 12 words"}}, ...]}}

The analyses array must have exactly {len(batch)} entries, in the same order as the headlines.
"sentiment" must be one of: bullish, bearish, neutral.
"neutral" means the headline is market-relevant but doesn't clearly push price direction either way."""


def generate_daily_summary(items: list[dict]) -> dict:
    """One final AI call: takes all sentiment-tagged headlines and produces
    an overall verdict + short paragraph summary."""
    config = _load_config()
    ai_cfg = config.get("ai", {})
    model = ai_cfg.get("model", "gemini-2.5-flash")
    rate_limit = ai_cfg.get("rate_limit_seconds", 7.0)
    max_tokens = ai_cfg.get("max_output_tokens", 2048)

    if not items:
        return {
            "overall_sentiment": "neutral",
            "summary": "No market-relevant headlines were collected today.",
        }

    bullish = sum(1 for it in items if it.get("sentiment") == "bullish")
    bearish = sum(1 for it in items if it.get("sentiment") == "bearish")
    neutral = sum(1 for it in items if it.get("sentiment") == "neutral")

    headlines_block = "\n".join(
        f"- [{it.get('sentiment', 'neutral').upper()}] {it['title']} ({it.get('reason', '')})"
        for it in items
    )

    prompt = f"""You are a financial news analyst producing a short daily brief on Indian
stock market sentiment (Sensex, Nifty) based on today's news headlines.

Sentiment tally from {len(items)} headlines: {bullish} bullish, {bearish} bearish, {neutral} neutral.

Headlines with their tagged sentiment:
{headlines_block}

Return ONLY valid JSON, no markdown, no preamble, in this exact shape:
{{"overall_sentiment": "bullish|bearish|neutral|mixed", "summary": "3-4 sentence plain-English summary of what's driving sentiment today and the likely market mood, written for a retail investor"}}"""

    result = generate(prompt, model=model, rate_limit=rate_limit, max_output_tokens=max_tokens)

    return {
        "overall_sentiment": result.get("overall_sentiment", "neutral"),
        "summary": result.get("summary", "AI summary unavailable — see raw headlines below."),
        "bullish_count": bullish,
        "bearish_count": bearish,
        "neutral_count": neutral,
    }
