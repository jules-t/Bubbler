"""Transform current signals into the required 20-field bubble metrics JSON.

Outputs `backend/data/outputs/bubble_metrics.json` with schema:
{
  "bubble_id": "market",
  "metrics": { ... }
}

Uses available signals; missing data defaults to 50.0. Network-dependent
fetches will skip if access is restricted.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import duckdb
import feedparser
import numpy as np
import pandas as pd
import yfinance as yf
from dateutil import parser as dateparser


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "redit_pipeline.duckdb"
BUBBLE_JSON = BASE_DIR / "outputs" / "bubble_data.json"
OUTPUT_PATH = BASE_DIR / "outputs" / "bubble_metrics.json"


# ---------- Normalization helpers ----------
def norm_percentile(value: float, series: Iterable[float], higher_is_riskier: bool = True) -> float:
    series = [v for v in series if v is not None]
    if not series:
        return 50.0
    arr = np.array(series, dtype=float)
    pct = (arr < value).mean() * 100
    return float(pct if higher_is_riskier else (100 - pct))


def norm_z(value: float, mean: float, std: float, higher_is_riskier: bool = True, scale: float = 15.0) -> float:
    if value is None or std == 0:
        return 50.0
    z = (value - mean) / std
    score = 50 + (z * scale)
    score = max(0.0, min(100.0, score))
    return float(score if higher_is_riskier else (100.0 - score))


def norm_minmax(value: float, vmin: float, vmax: float, higher_is_riskier: bool = True) -> float:
    if vmax == vmin:
        return 50.0
    pct = (value - vmin) / (vmax - vmin)
    pct = max(0.0, min(1.0, pct))
    return float(pct * 100 if higher_is_riskier else (1 - pct) * 100)


def normalize_vader(compound: Optional[float]) -> float:
    if compound is None:
        return 50.0
    base = (compound + 1) / 2 * 100  # -1..1 -> 0..100
    if compound > 0.5:
        base = 70 + (compound - 0.5) * 60
    return float(max(0.0, min(100.0, base)))


# ---------- Data fetchers ----------
def load_bubble_entries() -> list[Dict[str, Any]]:
    if not BUBBLE_JSON.exists():
        return []
    try:
        return json.loads(BUBBLE_JSON.read_text())
    except Exception:
        return []


def get_vader_average(entries: list[Dict[str, Any]]) -> Optional[float]:
    compounds = [
        d.get("sentiment_score")
        for d in entries
        if isinstance(d.get("sentiment_score"), (int, float))
    ]
    if not compounds:
        return None
    return float(np.mean(compounds))


def get_capex_intensity(entries: list[Dict[str, Any]]) -> Optional[float]:
    intensities = [
        d.get("sentiment_score")
        for d in entries
        if d.get("category") == "capex" and isinstance(d.get("sentiment_score"), (int, float))
    ]
    if not intensities:
        return None
    return float(np.mean(intensities))


def fetch_alpha_pe(conn: duckdb.DuckDBPyConnection) -> Optional[float]:
    try:
        df = conn.execute(
            "select forward_pe, pe_ratio from ai_bubble_data.alpha_vantage_overview "
            "where forward_pe is not null or pe_ratio is not null"
        ).df()
    except Exception:
        return None
    if df.empty:
        return None
    df = df.apply(pd.to_numeric, errors="coerce")
    vals = []
    for col in ["forward_pe", "pe_ratio"]:
        series = df[col].dropna()
        if not series.empty:
            vals.append(series.mean())
    return float(np.mean(vals)) if vals else None


def fetch_trends_mean(conn: duckdb.DuckDBPyConnection) -> Optional[float]:
    try:
        df = conn.execute("select * from ai_bubble_data.google_trends_interest").df()
    except Exception:
        return None
    if df.empty:
        return None
    num_cols = [c for c in df.columns if c not in ("date", "is_partial", "_dlt_id", "_dlt_load_id")]
    if not num_cols:
        return None
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    df["interest"] = df[num_cols].mean(axis=1)
    latest = df.sort_values("date").tail(7)
    if latest.empty:
        return None
    return float(latest["interest"].mean())


def fetch_fred_latest(conn: duckdb.DuckDBPyConnection) -> Dict[str, float]:
    metrics: Dict[str, float] = {}
    try:
        df = conn.execute("select metric, date, value from ai_bubble_data.fred_macro").df()
    except Exception:
        return metrics
    if df.empty:
        return metrics
    for metric in ["real_yield_10y", "m2", "hy_oas", "margin_debt"]:
        sub = df[df["metric"] == metric].sort_values("date")
        if sub.empty:
            continue
        latest_val = float(sub["value"].iloc[-1])
        if metric == "m2":
            sub = sub.sort_values("date")
            sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
            if len(sub) > 12:
                latest = sub["value"].iloc[-1]
                year_ago = sub["value"].iloc[-13]
                if pd.notna(latest) and pd.notna(year_ago) and year_ago != 0:
                    metrics["m2_yoy"] = ((latest / year_ago) - 1) * 100
        elif metric == "real_yield_10y":
            metrics["real_yield"] = latest_val
        elif metric == "hy_oas":
            metrics["hy_oas"] = latest_val
        elif metric == "margin_debt":
            metrics["margin_debt"] = latest_val
    return metrics


def fetch_reddit_volume(conn: duckdb.DuckDBPyConnection) -> Optional[int]:
    try:
        df = conn.execute("select created_utc from ai_bubble_data.reddit_posts").df()
    except Exception:
        return None
    if df.empty:
        return None
    df["created_utc"] = pd.to_datetime(df["created_utc"], errors="coerce")
    recent = df[df["created_utc"] >= (pd.Timestamp.utcnow() - pd.Timedelta(days=1))]
    return int(len(recent))


def get_vix_percentile() -> Optional[float]:
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="1y")["Close"]
    except Exception:
        return None
    if hist.empty:
        return None
    current = hist.iloc[-1]
    pct = (hist < current).mean() * 100
    return float(pct)


def get_valuation_ps_peg() -> Dict[str, Optional[float]]:
    tickers = ["NVDA", "MSFT", "GOOGL", "META", "AMZN"]
    ps_vals = []
    peg_vals = []
    for t in tickers:
        try:
            info = yf.Ticker(t).info
        except Exception:
            continue
        ps = info.get("priceToSalesTrailing12Months")
        if ps:
            ps_vals.append(ps)
        peg = info.get("pegRatio")
        if peg:
            peg_vals.append(peg)
    return {
        "revenue_multiple": float(np.mean(ps_vals)) if ps_vals else None,
        "growth_premium": float(np.mean(peg_vals)) if peg_vals else None,
    }


def get_fundamentals_growth_margins() -> Dict[str, Optional[float]]:
    tickers = ["NVDA", "MSFT", "GOOGL"]
    rev_growth = []
    margins = []
    for t in tickers:
        try:
            info = yf.Ticker(t).info
        except Exception:
            continue
        rg = info.get("revenueGrowth")
        if rg:
            rev_growth.append(rg * 100)
        pm = info.get("profitMargins")
        if pm:
            margins.append(pm * 100)
    return {
        "revenue_growth": float(np.mean(rev_growth)) if rev_growth else None,
        "profit_margins": float(np.mean(margins)) if margins else None,
    }


def get_put_call_ratio() -> Optional[float]:
    try:
        spy = yf.Ticker("SPY")
        expirations = spy.options
        if not expirations:
            return None
        chain = spy.option_chain(expirations[0])
        put_vol = chain.puts["volume"].sum()
        call_vol = chain.calls["volume"].sum()
        if call_vol <= 0:
            return None
        return float(put_vol / call_vol)
    except Exception:
        return None


def get_analyst_ratings() -> Optional[float]:
    tickers = ["NVDA", "MSFT", "GOOGL"]
    bullish = []
    for t in tickers:
        try:
            info = yf.Ticker(t).info
        except Exception:
            continue
        rec = info.get("recommendationMean")
        if rec:
            bullish_pct = (5 - rec) / 4 * 100  # 1=strong buy ->100, 5=strong sell ->0
            bullish.append(bullish_pct)
    return float(np.mean(bullish)) if bullish else None


def get_media_mentions() -> Optional[float]:
    feeds = [
        "https://news.google.com/rss/search?q=AI+bubble",
        "https://news.google.com/rss/search?q=artificial+intelligence+stocks",
    ]
    count = 0
    cutoff = datetime.utcnow() - timedelta(days=1)
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for e in feed.entries:
                if hasattr(e, "published"):
                    try:
                        pub_dt = dateparser.parse(e.published)
                        if pub_dt >= cutoff:
                            count += 1
                    except Exception:
                        continue
        except Exception:
            continue
    if count == 0:
        return None
    return float(min(100, (count / 30) * 100))


def get_fund_flows_proxy() -> Optional[float]:
    ai_etfs = ["ROBO", "BOTZ", "IRBO", "ARKQ"]
    changes = []
    for etf in ai_etfs:
        try:
            hist = yf.Ticker(etf).history(period="1mo")["Volume"]
        except Exception:
            continue
        if hist.empty or len(hist) < 20:
            continue
        recent = hist.tail(5).mean()
        older = hist.tail(20).head(15).mean()
        if older > 0:
            change = (recent / older - 1) * 100
            changes.append(change)
    if not changes:
        return None
    avg_change = float(np.mean(changes))
    return norm_z(avg_change, mean=0, std=30, higher_is_riskier=True)


def get_retail_interest(reddit_count: Optional[int], trends_retail: Optional[float]) -> float:
    reddit_score = norm_minmax(reddit_count or 0, 0, 500, higher_is_riskier=True)
    trends_score = norm_z(trends_retail, mean=50, std=20, higher_is_riskier=True) if trends_retail is not None else 50.0
    return float((reddit_score * 0.5) + (trends_score * 0.5))


# ---------- Transformer ----------
def transform_to_spec() -> Dict[str, Any]:
    conn = duckdb.connect(str(DB_PATH)) if DB_PATH.exists() else None
    entries = load_bubble_entries()

    # Fetch signals
    pe_avg = fetch_alpha_pe(conn) if conn else None
    trends_mean = fetch_trends_mean(conn) if conn else None
    fred_metrics = fetch_fred_latest(conn) if conn else {}
    vader_comp = get_vader_average(entries)
    capex_intensity = get_capex_intensity(entries)
    reddit_vol = fetch_reddit_volume(conn) if conn else None
    vix_pct = get_vix_percentile()
    ps_peg = get_valuation_ps_peg()
    growth_margins = get_fundamentals_growth_margins()
    pc_ratio = get_put_call_ratio()
    analyst_bullish = get_analyst_ratings()
    media_mentions = get_media_mentions()
    fund_flows = get_fund_flows_proxy()
    retail = get_retail_interest(reddit_vol, trends_mean)

    # Normalized metrics (0-100)
    valuation = {
        "pe_ratio": norm_z(pe_avg, mean=25, std=5, higher_is_riskier=True) if pe_avg else 50.0,
        "revenue_multiple": norm_z(ps_peg.get("revenue_multiple"), mean=6, std=2.5, higher_is_riskier=True)
        if ps_peg.get("revenue_multiple") is not None
        else 50.0,
        "market_cap_gdp": 50.0,
        "growth_premium": norm_z(ps_peg.get("growth_premium"), mean=1.5, std=0.7, higher_is_riskier=True)
        if ps_peg.get("growth_premium") is not None
        else 50.0,
    }

    sentiment = {
        "media_mentions": media_mentions if media_mentions is not None else 50.0,
        "social_sentiment": normalize_vader(vader_comp),
        "search_trends": norm_z(trends_mean, mean=60, std=20, higher_is_riskier=True) if trends_mean else 50.0,
        "analyst_ratings": analyst_bullish if analyst_bullish is not None else 50.0,
    }

    positioning = {
        "fund_flows": fund_flows if fund_flows is not None else 50.0,
        "institutional_holdings": 50.0,
        "retail_interest": retail,
        "options_volume": 50.0,
    }

    macro = {
        "interest_rates": norm_z(fred_metrics.get("real_yield"), mean=0.5, std=0.8, higher_is_riskier=True)
        if "real_yield" in fred_metrics
        else 50.0,
        "liquidity": norm_z(fred_metrics.get("m2_yoy"), mean=6.5, std=4.2, higher_is_riskier=False)
        if "m2_yoy" in fred_metrics
        else 50.0,
        "vix": vix_pct if vix_pct is not None else 50.0,
        "put_call_ratio": norm_z(pc_ratio, mean=0.8, std=0.3, higher_is_riskier=False)
        if pc_ratio is not None
        else 50.0,
    }

    fundamentals = {
        "revenue_growth": norm_z(growth_margins.get("revenue_growth"), mean=15, std=10, higher_is_riskier=True)
        if growth_margins.get("revenue_growth") is not None
        else 50.0,
        "profit_margins": norm_z(growth_margins.get("profit_margins"), mean=15, std=8, higher_is_riskier=True)
        if growth_margins.get("profit_margins") is not None
        else 50.0,
        "capex_cycle": norm_z(capex_intensity, mean=10, std=10, higher_is_riskier=True)
        if capex_intensity is not None
        else 50.0,
        "adoption_rate": 50.0,
    }

    if conn:
        conn.close()

    return {
        "bubble_id": "market",
        "metrics": {
            "category_1_valuation": valuation,
            "category_2_sentiment": sentiment,
            "category_3_positioning": positioning,
            "category_4_macro": macro,
            "category_5_fundamentals": fundamentals,
        },
    }


def _main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    spec = transform_to_spec()
    OUTPUT_PATH.write_text(json.dumps(spec, indent=2))
    print(f"Wrote spec JSON to {OUTPUT_PATH}")


if __name__ == "__main__":
    _main()
