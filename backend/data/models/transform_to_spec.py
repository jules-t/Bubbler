"""Transform current signals into the required 20-field bubble metrics JSON.

Outputs `backend/data/outputs/bubble_metrics.json` with schema:
{
  "bubble_id": "market",
  "metrics": {
    "category_1_valuation": {...},
    "category_2_sentiment": {...},
    "category_3_positioning": {...},
    "category_4_macro": {...},
    "category_5_fundamentals": {...}
  }
}

Notes:
- Uses available signals from DuckDB (alpha_vantage_overview, fred_macro, google_trends_interest)
  and bubble_data.json (VADER sentiment, capex entries). Everything else is stubbed at 50.0.
- Normalizes via z/percentile or min-max with basic baselines; missing data defaults to 50.0.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import duckdb
import numpy as np
import pandas as pd

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
    if std == 0:
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

    # Normalized metrics (0-100)
    valuation = {
        "pe_ratio": norm_z(pe_avg, mean=25, std=5, higher_is_riskier=True) if pe_avg else 50.0,
        "revenue_multiple": norm_z(None, mean=6, std=2.5, higher_is_riskier=True) if False else 50.0,
        "market_cap_gdp": 50.0,
        "growth_premium": norm_z(None, mean=1.5, std=0.7, higher_is_riskier=True) if False else 50.0,
    }

    sentiment = {
        "media_mentions": 50.0,
        "social_sentiment": normalize_vader(vader_comp),
        "search_trends": norm_z(trends_mean, mean=60, std=20, higher_is_riskier=True) if trends_mean else 50.0,
        "analyst_ratings": 50.0,
    }

    positioning = {
        "fund_flows": 50.0,
        "institutional_holdings": 50.0,
        "retail_interest": 50.0,
        "options_volume": 50.0,
    }

    macro = {
        "interest_rates": norm_z(fred_metrics.get("real_yield"), mean=0.5, std=0.8, higher_is_riskier=True)
        if "real_yield" in fred_metrics
        else 50.0,
        "liquidity": norm_z(fred_metrics.get("m2_yoy"), mean=6.5, std=4.2, higher_is_riskier=False)
        if "m2_yoy" in fred_metrics
        else 50.0,
        "vix": 50.0,  # could be added via yfinance percentile
        "put_call_ratio": 50.0,
    }

    fundamentals = {
        "revenue_growth": 50.0,
        "profit_margins": 50.0,
        "capex_cycle": norm_z(capex_intensity, mean=10, std=10, higher_is_riskier=True)
        if capex_intensity is not None
        else 50.0,
        "adoption_rate": 50.0,
    }

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
