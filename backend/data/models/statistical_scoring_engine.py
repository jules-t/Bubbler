"""Statistical bubble scoring engine using historical baselines.

Data sources (from DuckDB populated by pipelines):
- fred_macro (FRED: DFII10, M2SL, BAMLH0A0HYM2)
- google_trends_interest (pytrends)
- reddit_posts (Reddit JSON)
- ai_equity_history (yfinance OHLCV)
- alpha_vantage_overview (Alpha Vantage OVERVIEW)

Baselines:
- backend/data/historical_data/historical_baselines.json (hackathon estimates)

Output:
- backend/data/bubble_score_statistical.json
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import duckdb
import numpy as np
import pandas as pd
from scipy import stats


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB = BASE_DIR / "db" / "redit_pipeline.duckdb"
BASELINES_PATH = BASE_DIR / "historical_data" / "historical_baselines.json"
OUTPUT_PATH = BASE_DIR / "outputs" / "bubble_score_statistical.json"


@dataclass
class MetricResult:
    value: Optional[float]
    z_score: float
    percentile: float
    risk_score: float
    interpretation: str
    available: bool
    baseline_mean: Optional[float] = None
    baseline_std: Optional[float] = None


class StatisticalScoringEngine:
    def __init__(self, duckdb_path: Path = DEFAULT_DB, baselines_path: Path = BASELINES_PATH):
        self.duckdb_path = duckdb_path
        self.conn = duckdb.connect(str(duckdb_path)) if duckdb_path.exists() else None
        self.baselines = json.loads(baselines_path.read_text()) if baselines_path.exists() else {}
        self.weights = {
            "valuation": 0.25,
            "sentiment": 0.20,
            "positioning": 0.15,
            "liquidity": 0.20,
            "capex": 0.20,
        }
        # Load bubble_data.json for VADER sentiment aggregation
        self.bubble_data_path = BASE_DIR / "outputs" / "bubble_data.json"
        self.bubble_data = []
        if self.bubble_data_path.exists():
            try:
                self.bubble_data = json.loads(self.bubble_data_path.read_text())
            except Exception:
                self.bubble_data = []

    # ------------ Fetch current metrics -------------
    def _latest_fred_metrics(self) -> Dict[str, float]:
        if not self.conn:
            return {}
        metrics: Dict[str, float] = {}
        try:
            df = self.conn.execute(
                "select metric, date, value from ai_bubble_data.fred_macro"
            ).df()
        except Exception:
            return {}
        if df.empty:
            return {}
        for metric in ["real_yield_10y", "m2", "hy_oas"]:
            sub = df[df["metric"] == metric].sort_values("date")
            if sub.empty:
                continue
            metrics_map = {
                "real_yield_10y": "US_10Y_real_yield",
                "hy_oas": "US_HY_credit_spread",
            }
            if metric == "m2":
                sub = sub.sort_values("date")
                sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
                if len(sub) > 12:
                    latest = sub["value"].iloc[-1]
                    year_ago = sub["value"].iloc[-13]
                    if pd.notna(latest) and pd.notna(year_ago) and year_ago != 0:
                        metrics["US_M2_YoY_growth"] = ((latest / year_ago) - 1) * 100
            else:
                mapped = metrics_map.get(metric, metric)
                metrics[mapped] = float(sub["value"].iloc[-1])
        return metrics

    def _latest_valuation_metric(self) -> Dict[str, float]:
        metrics: Dict[str, float] = {}
        if not self.conn:
            return metrics
        # PE from Alpha Vantage snapshot
        try:
            df = self.conn.execute(
                "select forward_pe, pe_ratio from ai_bubble_data.alpha_vantage_overview "
                "where forward_pe is not null or pe_ratio is not null"
            ).df()
            if not df.empty:
                df = df.apply(pd.to_numeric, errors="coerce")
                vals = []
                for col in ["forward_pe", "pe_ratio"]:
                    series = df[col].dropna()
                    if not series.empty:
                        vals.append(series.mean())
                if vals:
                    metrics["forward_pe_mean"] = float(np.mean(vals))
        except Exception:
            pass

        # Equity volatility as positioning proxy
        try:
            eq = self.conn.execute(
                "select ticker, date, close from ai_bubble_data.ai_equity_history where close is not null"
            ).df()
            if not eq.empty:
                eq["close"] = pd.to_numeric(eq["close"], errors="coerce")
                vols = []
                for _, g in eq.groupby("ticker"):
                    g = g.sort_values("date")
                    rets = g["close"].pct_change().dropna()
                    if len(rets) > 5:
                        vols.append(rets.std())
                if vols:
                    metrics["equity_volatility_proxy"] = float(np.mean(vols))
        except Exception:
            pass
        return metrics

    def _fetch_current_metrics(self) -> Dict[str, float]:
        metrics: Dict[str, float] = {}
        metrics.update(self._latest_fred_metrics())
        metrics.update(self._latest_valuation_metric())
        # Sentiment from VADER compound in bubble_data.json
        if self.bubble_data:
            compounds = [
                d.get("sentiment_score")
                for d in self.bubble_data
                if isinstance(d.get("sentiment_score"), (int, float))
            ]
            if compounds:
                metrics["vader_compound_avg"] = float(np.mean(compounds))
        return metrics

    # ------------ Scoring helpers -------------
    @staticmethod
    def _z_score(value: float, mean: float, std: float) -> float:
        if std == 0:
            return 0.0
        return (value - mean) / std

    @staticmethod
    def _z_to_percentile(z: float) -> float:
        return float(stats.norm.cdf(z) * 100)

    @staticmethod
    def _percentile_to_risk(percentile: float, direction: str) -> float:
        if direction == "higher_is_riskier":
            normalized = (percentile - 50) / 50
            risk = 50 + (50 * np.tanh(normalized * 1.5))
        else:
            normalized = (50 - percentile) / 50
            risk = 50 + (50 * np.tanh(normalized * 1.5))
        return float(max(0.0, min(risk, 100.0)))

    @staticmethod
    def _interpret_percentile(percentile: float) -> str:
        if percentile >= 95:
            return "EXTREME (top 5%)"
        if percentile >= 90:
            return "VERY HIGH (top 10%)"
        if percentile >= 75:
            return "HIGH (top 25%)"
        if percentile >= 50:
            return "ABOVE AVERAGE"
        if percentile >= 25:
            return "BELOW AVERAGE"
        if percentile >= 10:
            return "LOW (bottom 10%)"
        return "VERY LOW (bottom 5%)"

    def _score_metric(self, category: str, metric_name: str, value: Optional[float]) -> Optional[MetricResult]:
        baseline = self.baselines.get(category, {}).get(metric_name)
        if not baseline:
            return None
        available = baseline.get("available", True)
        mean = baseline.get("mean")
        std = baseline.get("std", 0) or 0
        direction = baseline.get("direction", "higher_is_riskier")

        if (value is None) or (available is False):
            return MetricResult(
                value=value,
                z_score=0.0,
                percentile=50.0,
                risk_score=50.0,
                interpretation="DATA NOT AVAILABLE",
                available=False,
                baseline_mean=mean,
                baseline_std=std,
            )

        z = self._z_score(value, mean, std)
        percentile = self._z_to_percentile(z)
        risk = self._percentile_to_risk(percentile, direction)
        interpretation = self._interpret_percentile(percentile)
        return MetricResult(
            value=value,
            z_score=round(z, 2),
            percentile=round(percentile, 1),
            risk_score=round(risk, 1),
            interpretation=interpretation,
            available=True,
            baseline_mean=mean,
            baseline_std=std,
        )

    def _score_category(self, category: str, current_metrics: Dict[str, float]) -> Dict[str, Any]:
        baselines = self.baselines.get(category, {})
        scored: Dict[str, Any] = {}
        available_scores: List[float] = []
        for metric_name in baselines.keys():
            result = self._score_metric(category, metric_name, current_metrics.get(metric_name))
            if not result:
                continue
            scored[metric_name] = asdict(result)
            if result.available:
                available_scores.append(result.risk_score)
        if available_scores:
            score = float(np.mean(available_scores))
        else:
            score = 50.0
        if score >= 80:
            state = "CRITICAL"
        elif score >= 65:
            state = "HIGH_RISK"
        elif score >= 50:
            state = "ELEVATED"
        elif score >= 35:
            state = "MODERATE"
        else:
            state = "NORMAL"
        return {
            "score": round(score, 1),
            "state": state,
            "metrics": scored,
            "n_available": len(available_scores),
            "n_total": len(scored),
        }

    def calculate_overall_score(self) -> Dict[str, Any]:
        current_metrics = self._fetch_current_metrics()
        categories: Dict[str, Any] = {}
        for cat in ["valuation", "sentiment", "positioning", "liquidity", "capex"]:
            categories[cat] = self._score_category(cat, current_metrics)
        overall_score = sum(
            categories[cat]["score"] * self.weights.get(cat, 0) for cat in categories
        )
        if overall_score >= 80:
            state = "CRITICAL_BUBBLE_RISK"
        elif overall_score >= 65:
            state = "HIGH_BUBBLE_RISK"
        elif overall_score >= 50:
            state = "MODERATE_BUBBLE_RISK"
        elif overall_score >= 35:
            state = "ELEVATED_RISK"
        else:
            state = "NORMAL_MARKET"

        total_available = sum(cat["n_available"] for cat in categories.values())
        total_possible = sum(cat["n_total"] for cat in categories.values())
        confidence = total_available / total_possible if total_possible else 0

        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "overall_score": round(overall_score, 1),
            "state": state,
            "confidence": round(confidence, 2),
            "categories": categories,
            "methodology": "statistical_z_score_percentile",
            "data_coverage": f"{total_available}/{total_possible} metrics",
        }
        return result


def _main() -> None:
    engine = StatisticalScoringEngine()
    result = engine.calculate_overall_score()
    print(f"\n🎈 AI Bubble Score (statistical): {result['overall_score']}/100")
    print(f"📊 State: {result['state']}")
    print(f"💯 Confidence: {result['confidence']:.0%}")
    print(f"📈 Data Coverage: {result['data_coverage']}")
    print("\n📋 Category Breakdown:")
    for cat, data in result["categories"].items():
        print(f"  {cat.upper()}: {data['score']}/100 ({data['state']}) - {data['n_available']}/{data['n_total']} metrics")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2))
    print(f"\n✅ Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    _main()
