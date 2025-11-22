"""Free-source data gathering pipelines for the AI bubble dashboard.

This module uses only free/public sources and writes to DuckDB via dlt:
- Reddit hot posts from key AI subreddits (no auth required, respects rate limits).
- RSS feeds from TechCrunch and VentureBeat AI sections.
- Google Trends interest over time for AI keywords.
- Yahoo Finance price history for major AI-related tickers.

Set your environment variables in backend/data/.env before running.
Run: `python reddit_pipeline.py`
"""

from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime
from typing import Iterable, List, Optional

import dlt
import feedparser
import yfinance as yf
from dotenv import load_dotenv
from fredapi import Fred
from pytrends.request import TrendReq
from dlt.sources.helpers import requests
from dlt.destinations import duckdb as duckdb_destination

load_dotenv()

DEFAULT_SUBREDDITS: List[str] = ["artificial", "MachineLearning", "singularity", "OpenAI"]
DEFAULT_RSS_FEEDS: List[str] = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://hnrss.org/newest?q=artificial+intelligence",
]
DEFAULT_TRENDS_KEYWORDS: List[str] = ["ChatGPT", "OpenAI", "AI stocks", "AI bubble"]
DEFAULT_TRENDS_TIMEFRAME = os.getenv("TRENDS_TIMEFRAME", "2023-01-01 2024-11-22")
DEFAULT_REDDIT_LIMIT = int(os.getenv("REDDIT_LIMIT", "50"))
DEFAULT_TICKERS: List[str] = [
    ticker.strip()
    for ticker in os.getenv("AI_TICKERS", "NVDA,MSFT,GOOGL,AMZN,META").split(",")
    if ticker.strip()
]
ALPHAVANTAGE_TICKERS: List[str] = [
    t.strip()
    for t in os.getenv(
        "ALPHAVANTAGE_TICKERS", "QQQ,BOTZ,IRBO,NVDA,MSFT,GOOGL,AMZN,META,SMCI"
    ).split(",")
    if t.strip()
]

FRED_SERIES_REAL_YIELD = os.getenv("FRED_SERIES_REAL_YIELD", "DFII10")
FRED_SERIES_M2 = os.getenv("FRED_SERIES_M2", "M2SL")
FRED_SERIES_HY_OAS = os.getenv("FRED_SERIES_HY_OAS", "BAMLH0A0HYM2")
FRED_SERIES_MARGIN_DEBT = os.getenv("FRED_SERIES_MARGIN_DEBT", "BOGZ1FL663067003Q")


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
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:  # noqa: BLE001
            print(f"Skipping subreddit {subreddit} due to fetch error: {exc}")
            continue
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


@dlt.resource(name="newsapi_ai_news", write_disposition="replace")
def newsapi_ai_news(
    query: str = os.getenv("NEWSAPI_QUERY", "AI OR artificial intelligence OR AI bubble"),
    from_date: Optional[str] = os.getenv("NEWSAPI_FROM", None),
    language: str = os.getenv("NEWSAPI_LANG", "en"),
    page_size: int = int(os.getenv("NEWSAPI_PAGE_SIZE", "50")),
):
    """Optional: NewsAPI (requires free key). Skips if NEWSAPI_KEY missing."""

    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        print("NEWSAPI_KEY not set; skipping NewsAPI fetch.")
        return

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": language,
        "sortBy": "relevancy",
        "pageSize": page_size,
    }
    if from_date:
        params["from"] = from_date

    headers = {"X-Api-Key": api_key}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        # 401s or rate limits: skip without failing pipeline
        print(f"NewsAPI fetch failed ({exc}); skipping NewsAPI.")
        return
    for article in data.get("articles", []):
        yield {
            "source": article.get("source", {}).get("name"),
            "author": article.get("author"),
            "title": article.get("title"),
            "description": article.get("description"),
            "url": article.get("url"),
            "publishedAt": article.get("publishedAt"),
            "content": article.get("content"),
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


@dlt.resource(name="ai_equity_history", write_disposition="replace")
def ai_equity_history(tickers: Iterable[str] = DEFAULT_TICKERS, period: str = "1y"):
    """Get daily OHLCV history for key AI-related equities and ETFs via yfinance."""

    for ticker in tickers:
        stock = yf.Ticker(ticker)
        try:
            hist = stock.history(period=period)
        except Exception as exc:  # noqa: BLE001
            print(f"Skipping {ticker} due to fetch error: {exc}")
            continue
        if hist.empty:
            print(f"No price data returned for {ticker}; skipping.")
            continue
        hist = hist.reset_index()
        for row in hist.to_dict(orient="records"):
            date_value = row.pop("Date", None)
            if hasattr(date_value, "isoformat"):
                date_value = date_value.isoformat()
            yield {"ticker": ticker, "date": date_value, **row}


@dlt.resource(name="fred_macro", write_disposition="replace")
def fred_macro(max_points: int = 365):
    """Fetch key macro series from FRED: real yield, M2, HY OAS."""

    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        print("FRED_API_KEY not set; skipping FRED fetch.")
        return
    fred = Fred(api_key=api_key)
    series_map = {
        "real_yield_10y": FRED_SERIES_REAL_YIELD,
        "m2": FRED_SERIES_M2,
        "hy_oas": FRED_SERIES_HY_OAS,
        "margin_debt": FRED_SERIES_MARGIN_DEBT,
    }
    for label, series_id in series_map.items():
        try:
            series = fred.get_series(series_id)
        except Exception as exc:  # noqa: BLE001
            print(f"FRED fetch failed for {series_id} ({exc}); skipping.")
            continue
        if series is None:
            continue
        series = series.tail(max_points)
        for date, value in series.items():
            yield {"metric": label, "series_id": series_id, "date": date.isoformat(), "value": float(value)}


@dlt.resource(name="alpha_vantage_overview", write_disposition="replace")
def alpha_vantage_overview(tickers: Iterable[str] = ALPHAVANTAGE_TICKERS):
    """Fetch fundamentals/PE ratios via Alpha Vantage OVERVIEW endpoint."""

    api_key = os.getenv("ALPHA_VANTAGE_API_KEY") or os.getenv("ALPHAVANTAGE_API_KEY")
    if not api_key:
        print("ALPHA_VANTAGE_API_KEY not set; skipping Alpha Vantage.")
        return
    base_url = "https://www.alphavantage.co/query"
    for ticker in tickers:
        params = {"function": "OVERVIEW", "symbol": ticker, "apikey": api_key}
        try:
            resp = requests.get(base_url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            print(f"Alpha Vantage fetch failed for {ticker}: {exc}")
            continue
        if not data or "Symbol" not in data:
            print(f"Alpha Vantage returned no data for {ticker}")
            continue
        yield {
            "symbol": data.get("Symbol"),
            "name": data.get("Name"),
            "exchange": data.get("Exchange"),
            "currency": data.get("Currency"),
            "pe_ratio": _safe_float(data.get("PERatio")),
            "forward_pe": _safe_float(data.get("ForwardPE")),
            "peg_ratio": _safe_float(data.get("PEGRatio")),
            "market_cap": _safe_float(data.get("MarketCapitalization")),
            "dividend_yield": _safe_float(data.get("DividendYield")),
            "profit_margin": _safe_float(data.get("ProfitMargin")),
            "operating_margin": _safe_float(data.get("OperatingMarginTTM")),
            "return_on_equity": _safe_float(data.get("ReturnOnEquityTTM")),
            "quarterly_revenue_growth": _safe_float(data.get("QuarterlyRevenueGrowthYOY")),
            "quarterly_earnings_growth": _safe_float(data.get("QuarterlyEarningsGrowthYOY")),
            "sector": data.get("Sector"),
            "industry": data.get("Industry"),
            "fiscal_year_end": data.get("FiscalYearEnd"),
            "latest_quarter": data.get("LatestQuarter"),
            "source": "alpha_vantage",
        }


def _safe_float(val):
    try:
        return float(val)
    except Exception:
        return None


def run_all() -> None:
    """Run all resources into a single DuckDB-backed dlt pipeline."""

    db_dir = Path(__file__).resolve().parent / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "redit_pipeline.duckdb"

    pipeline = dlt.pipeline(
        pipeline_name="ai_bubble_pipeline",
        destination=duckdb_destination(credentials=str(db_path)),
        dataset_name="ai_bubble_data",
    )
    load_steps = [
        ("reddit_posts", reddit_posts()),
        ("rss_ai_news", rss_ai_news()),
        ("google_trends_interest", google_trends_interest()),
        ("newsapi_ai_news", newsapi_ai_news()),
        ("ai_equity_history", ai_equity_history()),
        ("fred_macro", fred_macro()),
        ("alpha_vantage_overview", alpha_vantage_overview()),
    ]
    for name, resource in load_steps:
        try:
            info = pipeline.run(resource)
            print(f"{name} -> {info}")  # noqa: T201
        except Exception as exc:  # noqa: BLE001
            print(f"{name} failed: {exc}. Continuing to next resource.")


if __name__ == "__main__":
    run_all()
