"""Build a bubble_data.json file from the latest DuckDB pipeline output.

Inputs:
- DuckDB file written by dlt (`backend/data/db/redit_pipeline.duckdb` by default)
  Tables expected: reddit_posts, rss_ai_news, google_trends_interest, ai_equity_history.

Outputs:
- backend/data/outputs/bubble_data.json with entries shaped for the scoring engine:
  {title, date, sentiment, category, content}

Run:
    python backend/data/build_bubble_dataset.py
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import requests
import feedparser
import duckdb
import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB = Path(os.getenv("DUCKDB_PATH", BASE_DIR.parent / "db" / "redit_pipeline.duckdb"))
OUTPUT_JSON = BASE_DIR.parent / "outputs" / "bubble_data.json"
analyzer = SentimentIntensityAnalyzer()


def table_exists(con: duckdb.DuckDBPyConnection, name: str, schema: str | None = None) -> bool:
    if schema:
        return (
            con.execute(
                "select count(*) from information_schema.tables "
                "where table_schema = ? and table_name = ?",
                [schema.lower(), name.lower()],
            ).fetchone()[0]
            > 0
        )
    return (
        con.execute(
            "select count(*) from information_schema.tables where table_name = ?", [name.lower()]
        ).fetchone()[0]
        > 0
    )


def resolve_table(con: duckdb.DuckDBPyConnection, name: str) -> str | None:
    """Return a fully-qualified table name if present in ai_bubble_data or main."""

    if table_exists(con, name, "ai_bubble_data"):
        return f"ai_bubble_data.{name}"
    if table_exists(con, name, "main"):
        return name
    return None


def sentiment_from_scores(score: int, upvote_ratio: float | None) -> str:
    if score >= 500 or (upvote_ratio and upvote_ratio >= 0.9):
        return "peak_hype"
    if score <= 5:
        return "warning"
    return "correction"


def sentiment_from_text(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in ["record", "surge", "boom", "mania", "bubble"]):
        return "peak_hype"
    if any(k in lower for k in ["slow", "decline", "risk", "concern", "selloff", "downturn"]):
        return "warning"
    return "correction"


def vader_label(text: str) -> tuple[str, float]:
    """Return (label, compound) from VADER sentiment."""

    if not text:
        return "correction", 0.0
    scores = analyzer.polarity_scores(text)
    comp = scores.get("compound", 0.0)
    if comp >= 0.3:
        label = "peak_hype"
    elif comp <= -0.2:
        label = "warning"
    else:
        label = "correction"
    return label, comp


def categorize(text: str, default: str = "sentiment") -> str:
    lower = text.lower()
    if any(k in lower for k in ["valuation", "funding", "round", "market cap", "raise", "unicorn"]):
        return "valuation"
    if any(k in lower for k in ["rate", "fed", "liquidity", "inflation", "macro"]):
        return "liquidity"
    if any(k in lower for k in ["capex", "spending", "investment", "datacenter", "infrastructure"]):
        return "capex"
    if any(k in lower for k in ["flow", "positioning", "overweight", "underweight", "crowded"]):
        return "positioning"
    return default


def build_entries() -> List[Dict[str, Any]]:
    con = duckdb.connect(DEFAULT_DB)
    entries: List[Dict[str, Any]] = []

    # Reddit posts -> sentiment
    reddit_table = resolve_table(con, "reddit_posts")

    if reddit_table:
        rows = con.execute(
            f"select title, created_utc, score, upvote_ratio, permalink, url, selftext "
            f"from {reddit_table} order by created_utc desc limit 200"
        ).fetchall()
        for title, created, score, ratio, permalink, url, selftext in rows:
            if isinstance(created, datetime):
                date_iso = created.isoformat()
            elif created:
                date_iso = str(created)
            else:
                date_iso = datetime.utcnow().isoformat()
            content_parts = [p for p in [selftext, url, f"https://reddit.com{permalink}"] if p]
            content = " ".join(content_parts)
            vader_sent, vader_comp = vader_label(f"{title or ''} {selftext or ''}")
            entries.append(
                {
                    "title": title,
                    "date": date_iso[:10],
                    "sentiment": vader_sent,
                    "sentiment_score": vader_comp,
                    "category": "sentiment",
                    "content": content,
                }
            )

    # RSS feeds -> valuation/capex/liquidity depending on keywords
    rss_table = resolve_table(con, "rss_ai_news")
    newsapi_table = resolve_table(con, "newsapi_ai_news")

    if rss_table:
        rows = con.execute(
            f"select title, published, summary, link from {rss_table} order by published desc limit 200"
        ).fetchall()
        for title, published, summary, link in rows:
            text = f"{title or ''} {summary or ''}"
            vader_sent, vader_comp = vader_label(text)
            entries.append(
                {
                    "title": title or "AI news",
                    "date": (published or "")[:10],
                    "sentiment": vader_sent,
                    "sentiment_score": vader_comp,
                    "category": categorize(text, default="valuation"),
                    "content": f"{summary or ''} {link or ''}".strip(),
                }
            )

    if newsapi_table:
        rows = con.execute(
            f"select title, published_at, description, url, source from {newsapi_table} "
            f"order by published_at desc limit 200"
        ).fetchall()
        for title, published_at, description, url, source in rows:
            pub = published_at
            text = f"{title or ''} {description or ''}"
            vader_sent, vader_comp = vader_label(text)
            entries.append(
                {
                    "title": title or f"{source or 'news'}",
                    "date": (str(pub) if pub else "")[:10],
                    "sentiment": vader_sent,
                    "sentiment_score": vader_comp,
                    "category": categorize(text, default="valuation"),
                    "content": f"{description or ''} {url or ''}".strip(),
                }
            )

    # Google Trends -> sentiment entries per date (averaged interest)
    trends_table = resolve_table(con, "google_trends_interest")

    if trends_table:
        # Grab numeric columns dynamically (ignore date/is_partial)
        cols = [
            c[1]
            for c in con.execute(f"pragma table_info('{trends_table}')").fetchall()
            if c[1] not in ("date", "is_partial") and not c[1].startswith("_dlt_")
        ]
        if cols:
            select_cols = " + ".join([f"coalesce(cast({c} as double),0)" for c in cols])
            rows = con.execute(
                f"select date, ({select_cols})/{len(cols)} as interest from {trends_table}"
            ).fetchall()
            for date_val, interest in rows:
                entries.append(
                    {
                        "title": "Google Trends interest for AI terms",
                        "date": (str(date_val) if date_val else "")[:10],
                        "sentiment": "peak_hype" if interest >= 75 else "correction",
                        "category": "sentiment",
                        "content": f"Average interest score {interest}",
                    }
                )

    # FRED macro series
    fred_table = resolve_table(con, "fred_macro")
    if fred_table:
        rows = con.execute(
            f"select metric, series_id, date, value from {fred_table} order by date desc limit 300"
        ).fetchall()
        for metric, series_id, date_val, value in rows:
            entries.append(
                {
                    "title": f"FRED {metric}",
                    "date": (str(date_val) if date_val else "")[:10],
                    "sentiment": "warning" if metric in ["hy_oas"] and value and value > 4 else "correction",
                    "category": "liquidity",
                    "content": f"{series_id} at {value}",
                }
            )

    # Alpha Vantage fundamentals (P/E etc.)
    av_table = resolve_table(con, "alpha_vantage_overview")
    if av_table:
        rows = con.execute(
            f"select symbol, name, forward_pe, pe_ratio, market_cap, sector, industry "
            f"from {av_table} order by symbol"
        ).fetchall()
        for symbol, name, fpe, pe, mcap, sector, industry in rows:
            entries.append(
                {
                    "title": f"{symbol} valuation",
                    "date": datetime.utcnow().date().isoformat(),
                    "sentiment": "peak_hype" if (fpe or 0) > 50 or (pe or 0) > 50 else "correction",
                    "category": "valuation",
                    "content": f"{name or symbol}: PE={pe}, FwdPE={fpe}, MCAP={mcap}, Sector={sector}, Industry={industry}",
                }
            )

    # Equity history -> valuation (simple price change summary)
    equity_table = resolve_table(con, "ai_equity_history")

    if equity_table:
        rows = con.execute(
            f"""
            with stats as (
                select ticker,
                       first(close) as first_close,
                       last(close) as last_close,
                       first(date) as start_date,
                       last(date) as end_date
                from {equity_table}
                group by ticker
            )
            select ticker, first_close, last_close, start_date, end_date,
                   ((last_close - first_close)/nullif(first_close,0))*100 as pct_change
            from stats
            """
        ).fetchall()
        for ticker, first_close, last_close, start_date, end_date, pct_change in rows:
            pct_change_val = pct_change if pct_change is not None else 0.0
            first_close_val = first_close if first_close is not None else 0.0
            last_close_val = last_close if last_close is not None else 0.0
            entries.append(
                {
                    "title": f"{ticker} price trend",
                    "date": (str(end_date) if end_date else "")[:10],
                    "sentiment": "peak_hype" if pct_change_val > 50 else "correction",
                    "category": "valuation",
                    "content": f"{ticker} moved {pct_change_val:.2f}% from {start_date} to {end_date} "
                    f"(from {first_close_val} to {last_close_val})",
                }
            )

    return entries


def add_vix_and_fear_greed(entries: List[Dict[str, Any]]) -> None:
    """Append VIX and Alternative.me Fear & Greed as sentiment entries."""

    # VIX
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="1y")
        if not hist.empty:
            latest = float(hist["Close"].iloc[-1])
            pct = (hist["Close"] < latest).mean() * 100
            sentiment = "warning" if latest > 30 else "peak_hype" if latest < 12 else "correction"
            entries.append(
                {
                    "title": "VIX fear index",
                    "date": datetime.utcnow().date().isoformat(),
                    "sentiment": sentiment,
                    "sentiment_score": pct,
                    "category": "sentiment",
                    "content": f"VIX {latest:.2f} (percentile {pct:.1f}%)",
                }
            )
    except Exception as exc:  # noqa: BLE001
        print(f"VIX fetch failed: {exc}")

    # Fear & Greed (Alternative.me)
    try:
        resp = requests.get("https://api.alternative.me/fng/", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("data"):
            fg_val = float(data["data"][0].get("value", 50))
            sentiment = "warning" if fg_val < 25 else "peak_hype" if fg_val > 75 else "correction"
            entries.append(
                {
                    "title": "Fear & Greed Index (alt)",
                    "date": datetime.utcnow().date().isoformat(),
                    "sentiment": sentiment,
                    "sentiment_score": fg_val,
                    "category": "sentiment",
                    "content": f"Alternative.me FNG {fg_val}",
                }
            )
    except Exception as exc:  # noqa: BLE001
        print(f"Fear & Greed fetch failed: {exc}")


def add_insider_selling(entries: List[Dict[str, Any]]) -> None:
    """Add insider selling signal from OpenInsider RSS."""

    try:
        feed = feedparser.parse("http://openinsider.com/rss.aspx?rows=200&insider=true&ticker=&tdtype=s")
        ai_tickers = ["NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD", "AVGO", "SMCI"]
        sells = [e for e in feed.entries if any(t in e.title for t in ai_tickers)]
        intensity = len(sells) / max(len(ai_tickers), 1)
        sentiment = "warning" if intensity > 0.5 else "correction"
        entries.append(
            {
                "title": "Insider selling intensity",
                "date": datetime.utcnow().date().isoformat(),
                "sentiment": sentiment,
                "sentiment_score": intensity,
                "category": "sentiment",
                "content": f"AI tickers insider sells: {len(sells)}",
            }
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Insider selling fetch failed: {exc}")


def add_yf_valuation(entries: List[Dict[str, Any]], tickers: Iterable[str]) -> None:
    """Add yfinance-based valuation metrics (PE, PEG, EV ratios)."""

    today = datetime.utcnow().date().isoformat()
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
        except Exception as exc:  # noqa: BLE001
            print(f"yfinance info failed for {ticker}: {exc}")
            continue
        content_parts = []
        for field in ["trailingPE", "forwardPE", "pegRatio", "priceToBook", "enterpriseToRevenue", "enterpriseToEbitda", "priceToSalesTrailing12Months"]:
            val = info.get(field)
            if val is not None:
                content_parts.append(f"{field}={val}")
        if not content_parts:
            continue
        entries.append(
            {
                "title": f"{ticker} valuation snapshot",
                "date": today,
                "sentiment": "peak_hype" if (info.get("forwardPE") or 0) > 50 else "correction",
                "sentiment_score": info.get("forwardPE"),
                "category": "valuation",
                "content": ", ".join(content_parts),
            }
        )


def add_capex_metrics(entries: List[Dict[str, Any]], tickers: Iterable[str]) -> None:
    """Add capex signals from yfinance cash flow/revenue."""

    today = datetime.utcnow().date().isoformat()
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            cf = stock.quarterly_cashflow
            fin = stock.quarterly_financials
        except Exception as exc:  # noqa: BLE001
            print(f"Capex fetch failed for {ticker}: {exc}")
            continue
        if cf is None or cf.empty or fin is None or fin.empty:
            continue
        capex_series = cf.loc["Capital Expenditure"] if "Capital Expenditure" in cf.index else None
        revenue_series = fin.loc["Total Revenue"] if "Total Revenue" in fin.index else None
        if capex_series is None or revenue_series is None or len(capex_series) < 2 or len(revenue_series) < 1:
            continue
        capex_now = -float(capex_series.iloc[0])
        capex_prev = -float(capex_series.iloc[1]) if len(capex_series) > 1 else capex_now
        revenue_now = float(revenue_series.iloc[0])
        capex_yoy = ((capex_now / capex_prev) - 1) * 100 if capex_prev else None
        capex_intensity = (capex_now / revenue_now) * 100 if revenue_now else None
        entries.append(
            {
                "title": f"{ticker} capex signal",
                "date": today,
                "sentiment": "warning" if capex_intensity and capex_intensity > 50 else "correction",
                "sentiment_score": capex_intensity,
                "category": "capex",
                "content": f"capex_yoy={capex_yoy:.2f}% capex_intensity={capex_intensity:.2f}%",
            }
        )


def main() -> None:
    entries = build_entries()
    add_vix_and_fear_greed(entries)
    add_insider_selling(entries)
    # Enhanced valuation and capex signals via yfinance snapshots
    tickers = [t.strip() for t in os.getenv("AI_TICKERS", "").split(",") if t.strip()]
    if tickers:
        add_yf_valuation(entries, tickers)
        add_capex_metrics(entries, tickers)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(entries, indent=2))
    print(f"Wrote {len(entries)} entries to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
