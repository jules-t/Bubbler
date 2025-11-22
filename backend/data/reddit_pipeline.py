"""Free-source data gathering pipelines for the AI bubble dashboard.

This module uses only free/public sources and writes to DuckDB via dlt:
- Reddit hot posts from key AI subreddits (no auth required, respects rate limits).
- RSS feeds from TechCrunch and VentureBeat AI sections.
- Google Trends interest over time for AI keywords.
- FRED Federal Funds Rate (requires free API key).
- Yahoo Finance price history for major AI-related tickers.

Set your environment variables in backend/data/.env before running.
Run: `python reddit_pipeline.py`
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Iterable, List, Optional

import dlt
import feedparser
import yfinance as yf
from dotenv import load_dotenv
from fredapi import Fred
from pytrends.request import TrendReq
from dlt.sources.helpers import requests

load_dotenv()

DEFAULT_SUBREDDITS: List[str] = ["artificial", "MachineLearning", "singularity", "OpenAI"]
DEFAULT_RSS_FEEDS: List[str] = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
]
DEFAULT_TRENDS_KEYWORDS: List[str] = ["ChatGPT", "OpenAI", "AI stocks", "AI bubble"]
DEFAULT_TRENDS_TIMEFRAME = os.getenv("TRENDS_TIMEFRAME", "2023-01-01 2024-11-22")
DEFAULT_REDDIT_LIMIT = int(os.getenv("REDDIT_LIMIT", "50"))
DEFAULT_TICKERS: List[str] = [
    ticker.strip()
    for ticker in os.getenv("AI_TICKERS", "NVDA,MSFT,GOOGL,AMZN,META").split(",")
    if ticker.strip()
]


def _utc_to_iso(timestamp: Optional[float]) -> Optional[str]:
    if timestamp is None:
        return None
    return datetime.utcfromtimestamp(timestamp).isoformat()


@dlt.resource(name="reddit_posts", write_disposition="replace")
def reddit_posts(subreddits: Iterable[str] = DEFAULT_SUBREDDITS, limit: int = DEFAULT_REDDIT_LIMIT):
    """Fetch hot posts from AI-related subreddits."""

    headers = {"User-Agent": os.getenv("REDDIT_USER_AGENT", "ai-bubble-tracker/0.1")}
    params = {"limit": limit}
    for subreddit in subreddits:
        url = f"https://www.reddit.com/r/{subreddit}/hot.json"
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        for child in payload.get("data", {}).get("children", []):
            data = child.get("data", {}) or {}
            yield {
                "id": data.get("id"),
                "subreddit": data.get("subreddit"),
                "title": data.get("title"),
                "score": data.get("score"),
                "num_comments": data.get("num_comments"),
                "created_utc": _utc_to_iso(data.get("created_utc")),
                "url": data.get("url"),
                "permalink": data.get("permalink"),
                "selftext": data.get("selftext"),
                "upvote_ratio": data.get("upvote_ratio"),
            }


@dlt.resource(name="rss_ai_news", write_disposition="replace")
def rss_ai_news(feeds: Iterable[str] = DEFAULT_RSS_FEEDS, max_items: int = 50):
    """Parse AI news from free RSS feeds."""

    for feed_url in feeds:
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries[:max_items]:
            yield {
                "feed": feed_url,
                "title": getattr(entry, "title", None),
                "link": getattr(entry, "link", None),
                "published": getattr(entry, "published", None),
                "summary": getattr(entry, "summary", None),
            }


@dlt.resource(name="google_trends_interest", write_disposition="replace")
def google_trends_interest(
    keywords: Iterable[str] = DEFAULT_TRENDS_KEYWORDS,
    timeframe: str = DEFAULT_TRENDS_TIMEFRAME,
    geo: str = "",
):
    """Collect Google Trends interest over time for AI queries."""

    pytrends = TrendReq()
    pytrends.build_payload(list(keywords), timeframe=timeframe, geo=geo)
    df = pytrends.interest_over_time()
    if df.empty:
        return
    df = df.reset_index()
    for row in df.to_dict(orient="records"):
        date_value = row.pop("date", None) or row.pop("index", None)
        if hasattr(date_value, "isoformat"):
            date_value = date_value.isoformat()
        is_partial = row.pop("isPartial", None)
        yield {"date": date_value, "is_partial": bool(is_partial), **row}


@dlt.resource(name="fred_fed_funds_rate", write_disposition="replace")
def fred_fed_funds_rate(series_id: str = os.getenv("FRED_SERIES_ID", "DFF"), max_points: int = 180):
    """Fetch Federal Funds Rate (DFF) from FRED; requires free API key."""

    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        print("FRED_API_KEY not set; skipping FRED fetch.")
        return
    fred = Fred(api_key=api_key)
    series = fred.get_series(series_id)
    if series is None:
        return
    series = series.tail(max_points)
    for date, value in series.items():
        yield {"series_id": series_id, "date": date.isoformat(), "value": float(value)}


@dlt.resource(name="ai_equity_history", write_disposition="replace")
def ai_equity_history(tickers: Iterable[str] = DEFAULT_TICKERS, period: str = "1y"):
    """Get daily OHLCV history for key AI-related equities."""

    for ticker in tickers:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            continue
        hist = hist.reset_index()
        for row in hist.to_dict(orient="records"):
            date_value = row.pop("Date", None)
            if hasattr(date_value, "isoformat"):
                date_value = date_value.isoformat()
            yield {"ticker": ticker, "date": date_value, **row}


def run_all() -> None:
    """Run all resources into a single DuckDB-backed dlt pipeline."""

    pipeline = dlt.pipeline(
        pipeline_name="ai_bubble_pipeline", destination="duckdb", dataset_name="ai_bubble_data"
    )
    load_steps = [
        ("reddit_posts", reddit_posts()),
        ("rss_ai_news", rss_ai_news()),
        ("google_trends_interest", google_trends_interest()),
        ("fred_fed_funds_rate", fred_fed_funds_rate()),
        ("ai_equity_history", ai_equity_history()),
    ]
    for name, resource in load_steps:
        info = pipeline.run(resource)
        print(f"{name} -> {info}")  # noqa: T201


if __name__ == "__main__":
    run_all()
