# Daily Indian Stock Market Sentiment Monitor

Runs every weekday morning (8:00 AM IST, before market open), pulls fresh
headlines from four Indian financial news sources, tags each one
bullish/bearish/neutral with Gemini (free tier), and writes a short daily
sentiment summary — all committed straight into this repo. No external
database, no server, no cost.

**Sources:** Economic Times Markets, Economic Times Economy, Moneycontrol, Business Standard.

## Setup (5 minutes)

1. **Push this folder to a new GitHub repo** (public repo = free GitHub Actions minutes).

2. **Get a free Gemini API key:** https://aistudio.google.com/app/apikey
   (no credit card needed — 1,500+ requests/day on the free tier)

3. **Add it as a repo secret:**
   Repo → Settings → Secrets and variables → Actions → New repository secret
   - Name: `GEMINI_API_KEY`
   - Value: (paste your key)

4. **Enable the workflow:**
   The workflow file is already at `.github/workflows/daily-sentiment.yml`.
   Go to the Actions tab and confirm workflows are enabled for the repo.

5. **Test it manually:** Actions tab → "Daily Market Sentiment Monitor" → "Run workflow".
   Check the `data/` folder afterward for a new `YYYY-MM-DD.json` file.

That's it — it will now run automatically every weekday morning and commit
results to `data/`.

## Where to look

- `data/latest.json` — most recent day's full report (headlines + sentiment + summary)
- `data/YYYY-MM-DD.json` — archive of every past day
- `data/history.csv` — one row per day (sentiment, bullish/bearish/neutral counts) — open in Excel/Sheets to chart the trend over time

## Running locally

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in your GEMINI_API_KEY
python -m scraper.main
```

## Customizing

- **Change run time:** edit the `cron` line in `.github/workflows/daily-sentiment.yml`
  (times are UTC — IST is UTC+5:30)
- **Add a news source:** drop a new file in `scraper/sources/` following the
  pattern in `et_markets.py`, then add it to the `SOURCES` list in `scraper/main.py`
- **Tune keyword filters:** edit `filters.required_keywords` in `config.yaml`
  (only used for general-news feeds like Business Standard — market-specific
  feeds skip this)
- **Swap the AI model:** edit `ai.model` in `config.yaml`

## How sentiment is scored

Each headline gets sent to Gemini in batches of 8 with a prompt asking it to
classify the likely short-term implication for Indian equities as
`bullish`, `bearish`, or `neutral`. Once every headline is tagged, a final
call summarizes the day's overall mood in plain English. This is a sentiment
signal from news volume/tone — not investment advice, and not a substitute
for checking actual index levels, FII/DII flows, or a financial advisor.
