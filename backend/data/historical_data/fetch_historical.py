"""Fetch available historical metrics and store them as CSVs in historical_data/.

Sources used (free/public):
- FRED (requires FRED_API_KEY in .env): DFII10 (10Y real yield), M2SL (used to compute M2 YoY),
  BAMLH0A0HYM2 (HY credit spread).
- Yahoo Finance via yfinance: price history for AI-related equities/ETFs, plus a snapshot of PE ratios.
- Google Trends via pytrends: interest over time for AI keywords.

Not covered here (manual/premium): Fear & Greed, put/call, short interest, IV/RV, GPU shipments,
capex/OCF, AI revenue. These are emitted as TODO placeholders.

Run:
    python3 fetch_historical.py
Outputs (written to backend/data/historical_data/):
    fred_macro_history.csv
    m2_yoy_history.csv
    yfinance_prices.csv
    yfinance_pe_snapshot.csv
    google_trends_history.csv
    manual_todo.csv
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from fredapi import Fred
from pytrends.request import TrendReq


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")

FRED_API_KEY = os.getenv("FRED_API_KEY")
FRED_SERIES = {
    "real_yield_10y": os.getenv("FRED_SERIES_REAL_YIELD", "DFII10"),
    "m2": os.getenv("FRED_SERIES_M2", "M2SL"),
    "hy_oas": os.getenv("FRED_SERIES_HY_OAS", "BAMLH0A0HYM2"),
}

YF_TICKERS: List[str] = [
    t.strip()
    for t in os.getenv(
        "AI_TICKERS", "NVDA,MSFT,GOOGL,AMZN,META,SMCI,AMD,AVGO,QQQ,BOTZ,IRBO"
    ).split(",")
    if t.strip()
]

TRENDS_KEYWORDS = ["ChatGPT", "OpenAI", "AI stocks", "AI bubble"]
TRENDS_TIMEFRAME = os.getenv("TRENDS_TIMEFRAME", "2023-01-01 2024-11-22")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def fetch_fred_series() -> pd.DataFrame:
    if not FRED_API_KEY:
        print("FRED_API_KEY not set; skipping FRED fetch.")
        return pd.DataFrame()
    fred = Fred(api_key=FRED_API_KEY)
    frames: List[pd.DataFrame] = []
    for label, series_id in FRED_SERIES.items():
        try:
            series = fred.get_series(series_id)
        except Exception as exc:  # noqa: BLE001
            print(f"FRED fetch failed for {series_id}: {exc}")
            continue
        if series is None or len(series) == 0:
            continue
        df = series.reset_index()
        df.columns = ["date", "value"]
        df["metric"] = label
        df["series_id"] = series_id
        df["source"] = "fred"
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def compute_m2_yoy(macro_df: pd.DataFrame) -> pd.DataFrame:
    if macro_df.empty:
        return pd.DataFrame()
    m2 = macro_df[macro_df["metric"] == "m2"].copy()
    if m2.empty:
        return pd.DataFrame()
    m2 = m2.sort_values("date")
    m2["m2_yoy"] = m2["value"].pct_change(periods=12) * 100
    m2 = m2.dropna(subset=["m2_yoy"])
    m2["metric"] = "m2_yoy"
    m2["series_id"] = "M2SL_yoy"
    m2["value"] = m2["m2_yoy"]
    m2["source"] = "fred_derived"
    return m2[["date", "value", "metric", "series_id", "source"]]


def fetch_yfinance_prices(tickers: Iterable[str], period: str = "max") -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(period=period)
        except Exception as exc:  # noqa: BLE001
            print(f"yfinance fetch failed for {ticker}: {exc}")
            continue
        if hist.empty:
            continue
        hist = hist.reset_index()
        # Ensure Adj Close exists; fallback to Close
        if "Adj Close" not in hist.columns and "Close" in hist.columns:
            hist["Adj Close"] = hist["Close"]
        hist["ticker"] = ticker
        hist["source"] = "yfinance"
        frames.append(hist[["Date", "ticker", "Close", "Adj Close", "Volume", "source"]])
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df.rename(columns={"Date": "date", "Close": "close", "Adj Close": "adj_close", "Volume": "volume"}, inplace=True)
    return df


def fetch_yfinance_pe_snapshot(tickers: Iterable[str]) -> pd.DataFrame:
    rows: List[dict] = []
    today = datetime.utcnow().date().isoformat()
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
        except Exception as exc:  # noqa: BLE001
            print(f"yfinance info failed for {ticker}: {exc}")
            continue
        rows.append(
            {
                "ticker": ticker,
                "date": today,
                "forward_pe": info.get("forwardPE"),
                "trailing_pe": info.get("trailingPE"),
                "market_cap": info.get("marketCap"),
                "source": "yfinance_snapshot",
            }
        )
    return pd.DataFrame(rows)


def fetch_google_trends(keywords: List[str], timeframe: str) -> pd.DataFrame:
    try:
        pytrends = TrendReq()
        pytrends.build_payload(keywords, timeframe=timeframe)
        df = pytrends.interest_over_time()
    except Exception as exc:  # noqa: BLE001
        print(f"pytrends fetch failed: {exc}")
        return pd.DataFrame()
    if df.empty:
        return pd.DataFrame()
    df = df.reset_index()
    frames = []
    for kw in keywords:
        if kw not in df.columns:
            continue
        tmp = df[["date", kw]].rename(columns={kw: "value"})
        tmp["keyword"] = kw
        tmp["source"] = "google_trends"
        frames.append(tmp)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def write_csv(df: pd.DataFrame, filename: str) -> None:
    if df is None or df.empty:
        return
    ensure_dir(BASE_DIR)
    out_path = BASE_DIR / filename
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path}")


def write_manual_todo() -> None:
    todos = [
        {"metric": "fear_greed_index", "status": "manual/premium", "note": "No official free API; scrape CNN or enter manually."},
        {"metric": "put_call_ratio_nvda", "status": "manual/premium", "note": "Options data; CBOE/premium feeds."},
        {"metric": "short_interest_nvda", "status": "manual/premium", "note": "FINRA/Nasdaq short interest; manual entry."},
        {"metric": "iv_rv_ratio_nvda", "status": "manual/premium", "note": "Options vol data; premium."},
        {"metric": "gpu_shipment_growth", "status": "manual", "note": "Industry reports (e.g., JPR)"},
        {"metric": "ai_capex_to_ocf", "status": "manual", "note": "Compute from filings (MSFT/GOOGL/AMZN/META/AVGO/NVDA)"},
        {"metric": "ai_revenue_yoy", "status": "manual", "note": "Segment disclosures from earnings."},
    ]
    df = pd.DataFrame(todos)
    write_csv(df, "manual_todo.csv")


def main() -> None:
    # FRED
    fred_df = fetch_fred_series()
    write_csv(fred_df, "fred_macro_history.csv")
    m2_yoy = compute_m2_yoy(fred_df)
    write_csv(m2_yoy, "m2_yoy_history.csv")

    # yfinance prices and PE snapshot
    yf_prices = fetch_yfinance_prices(YF_TICKERS, period="max")
    write_csv(yf_prices, "yfinance_prices.csv")
    yf_pe = fetch_yfinance_pe_snapshot(YF_TICKERS)
    write_csv(yf_pe, "yfinance_pe_snapshot.csv")

    # Google Trends
    trends = fetch_google_trends(TRENDS_KEYWORDS, TRENDS_TIMEFRAME)
    write_csv(trends, "google_trends_history.csv")

    # Manual placeholders
    write_manual_todo()


if __name__ == "__main__":
    main()
