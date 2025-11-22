"""Bubble burst probability scoring engine.

Implements the design in files_read/SCORING_ENGINE_DESIGN.md:
- Calculates 5 category scores (valuation, sentiment, positioning, liquidity, capex)
- Aggregates to an overall bubble risk score/state
- Returns a JSON-serializable dict for UI/TTS teammates

Usage:
    python scoring_engine.py               # loads backend/data/outputs/bubble_data.json
    from scoring_engine import calculate_bubble_score
    result = calculate_bubble_score("backend/data/outputs/bubble_data.json")
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

import duckdb
import numpy as np
import pandas as pd


DATA_PATH = Path(__file__).resolve().parent.parent / "outputs" / "bubble_data.json"
DEFAULT_DUCKDB = Path(__file__).resolve().parent / "db" / "redit_pipeline.duckdb"


@dataclass
class MetricScore:
    """Individual metric score result."""

    score: float  # 0-100
    state: str  # Text description
    indicators: Dict[str, Any]  # Raw indicator values
    weight: float  # Contribution to overall score


@dataclass
class BubbleAnalysis:
    """Complete bubble analysis output."""

    timestamp: str
    overall_bubble_score: float  # 0-100
    bubble_state: str  # LOW, MODERATE, HIGH_RISK, CRITICAL
    confidence: float  # 0-1
    metrics: Dict[str, MetricScore]
    warning_signals: List[str]
    historical_comparison: Dict[str, Any]


class BubbleScoringEngine:
    """Main scoring engine for AI bubble burst probability."""

    def __init__(self, raw_data: List[Dict[str, Any]], duckdb_path: Optional[Path] = DEFAULT_DUCKDB):
        self.raw_data = raw_data
        self.processed_data = self._process_data()
        self.duckdb_path = duckdb_path
        self.db = duckdb.connect(str(duckdb_path)) if duckdb_path and duckdb_path.exists() else None
        # Metric weights (must sum to 1.0)
        self.weights = {
            "valuation": 0.25,
            "sentiment": 0.20,
            "positioning": 0.15,
            "liquidity": 0.20,
            "capex": 0.20,
        }

    def _process_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Organize raw data by category."""

        categories = {
            "valuation": [],
            "sentiment": [],
            "positioning": [],
            "liquidity": [],
            "capex": [],
        }
        for item in self.raw_data:
            category = item.get("category", "sentiment")
            categories.setdefault(category, [])
            categories[category].append(item)
        return categories

    def calculate_bubble_score(self) -> Dict[str, Any]:
        """Calculate all scores and aggregate."""

        valuation_score = self._calculate_valuation_score()
        sentiment_score = self._calculate_sentiment_score()
        positioning_score = self._calculate_positioning_score()
        liquidity_score = self._calculate_liquidity_score()
        capex_score = self._calculate_capex_score()

        overall_score = (
            valuation_score.score * self.weights["valuation"]
            + sentiment_score.score * self.weights["sentiment"]
            + positioning_score.score * self.weights["positioning"]
            + liquidity_score.score * self.weights["liquidity"]
            + capex_score.score * self.weights["capex"]
        )

        bubble_state = self._determine_bubble_state(overall_score)
        warnings = self._generate_warnings(
            valuation_score, sentiment_score, positioning_score, liquidity_score, capex_score
        )
        historical = self._compare_to_historical_bubbles(overall_score)
        confidence = self._calculate_confidence()

        analysis = BubbleAnalysis(
            timestamp=datetime.utcnow().isoformat() + "Z",
            overall_bubble_score=round(overall_score, 1),
            bubble_state=bubble_state,
            confidence=round(confidence, 2),
            metrics={
                "valuation": valuation_score,
                "sentiment": sentiment_score,
                "positioning": positioning_score,
                "liquidity": liquidity_score,
                "capex": capex_score,
            },
            warning_signals=warnings,
            historical_comparison=historical,
        )
        return self._to_dict(analysis)

    # ==================== METRIC CALCULATORS ====================

    def _calculate_valuation_score(self) -> MetricScore:
        data = self.processed_data["valuation"]
        indicators = {}

        # Quantitative: Alpha Vantage forward PE / PE percentiles across tickers
        score_components: List[float] = []
        if self.db:
            try:
                # Use yfinance-derived equity history as proxy: price/PE percentiles
                df_prices = self.db.execute(
                    "select ticker, date, close from ai_bubble_data.ai_equity_history "
                    "where close is not null"
                ).df()
                if not df_prices.empty:
                    df_prices["close"] = pd.to_numeric(df_prices["close"], errors="coerce")
                    latest = df_prices.sort_values("date").groupby("ticker")["close"].last().dropna()
                    if len(latest) > 0:
                        pctl = (latest < latest.mean()).mean()
                        score_components.append((1 - pctl) * 100)
                        indicators["price_level_pct"] = float(pctl)
                # Alpha Vantage still used if present
                df = self.db.execute(
                    "select symbol, forward_pe, pe_ratio from ai_bubble_data.alpha_vantage_overview "
                    "where forward_pe is not null or pe_ratio is not null"
                ).df()
                if not df.empty:
                    for col in ["forward_pe", "pe_ratio"]:
                        series = df[col].dropna().astype(float)
                        if len(series) > 0:
                            latest_val = series.mean()
                            percentile = (series < latest_val).mean()
                            score_components.append(percentile * 100)
                            indicators[f"{col}_mean"] = float(latest_val)
                            indicators[f"{col}_pctl"] = float(percentile)
            except Exception:
                pass

        # Qualitative fallback
        indicators["high_valuations_count"] = sum(
            1 for d in data if "billion" in d.get("content", "").lower()
        )
        indicators["valuation_mentions"] = len(
            [d for d in data if "valuation" in d.get("content", "").lower()]
        )
        indicators["sentiment_skew"] = sum(1 for d in data if d.get("sentiment") == "peak_hype") / max(
            len(data), 1
        )

        if score_components:
            score = float(np.mean(score_components))
        else:
            base_score = 50.0
            base_score += indicators["high_valuations_count"] * 10
            base_score += indicators["sentiment_skew"] * 30
            score = min(base_score, 100.0)

        if score >= 80:
            state = "SEVERELY_OVERVALUED"
        elif score >= 60:
            state = "OVERVALUED"
        elif score >= 40:
            state = "FAIR_VALUE"
        else:
            state = "UNDERVALUED"

        return MetricScore(
            score=round(score, 1),
            state=state,
            indicators=indicators,
            weight=self.weights["valuation"],
        )

    def _calculate_sentiment_score(self) -> MetricScore:
        data = self.processed_data["sentiment"]
        indicators = {}

        # VADER compound sentiment from bubble_data entries (range -1..1)
        compounds = [
            d.get("sentiment_score")
            for d in data
            if isinstance(d.get("sentiment_score"), (int, float))
        ]
        compound_avg = float(np.mean(compounds)) if compounds else None
        compound_score = ((compound_avg + 1) / 2 * 100) if compound_avg is not None else None

        score_components: List[float] = []
        # Quantitative: Google Trends z-score; Reddit volume z-score
        if self.db:
            try:
                df_trends = self.db.execute(
                    "select * from ai_bubble_data.google_trends_interest"
                ).df()
                if not df_trends.empty:
                    num_cols = [c for c in df_trends.columns if c not in ("date", "is_partial", "_dlt_id", "_dlt_load_id")]
                    if num_cols:
                        df_trends["interest"] = df_trends[num_cols].apply(pd.to_numeric, errors="coerce").mean(axis=1)
                        series = df_trends["interest"].dropna()
                        if len(series) > 5:
                            z = (series.iloc[-1] - series.mean()) / (series.std() or 1)
                            score_components.append(self._z_to_score(z))
                            indicators["trends_latest"] = float(series.iloc[-1])
                            indicators["trends_z"] = float(z)
            except Exception:
                pass

            try:
                df_reddit = self.db.execute(
                    "select cast(left(created_utc,10) as date) as d, count(*) as c "
                    "from ai_bubble_data.reddit_posts group by d order by d"
                ).df()
                if not df_reddit.empty:
                    series = df_reddit["c"]
                    z = (series.iloc[-1] - series.mean()) / (series.std() or 1)
                    score_components.append(self._z_to_score(z))
                    indicators["reddit_posts_latest"] = int(series.iloc[-1])
                    indicators["reddit_posts_z"] = float(z)
            except Exception:
                pass

        indicators["peak_hype_ratio"] = sum(1 for d in data if d.get("sentiment") == "peak_hype") / max(
            len(data), 1
        )
        indicators["warning_ratio"] = sum(1 for d in data if d.get("sentiment") == "warning") / max(
            len(data), 1
        )
        indicators["total_articles"] = len(data)
        if compound_avg is not None:
            indicators["vader_compound_avg"] = compound_avg

        if compound_score is not None:
            score = compound_score
            # Adjust modestly with label ratios
            score += indicators["peak_hype_ratio"] * 20
            score -= indicators["warning_ratio"] * 10
            score = max(0.0, min(score, 100.0))
        elif score_components:
            score = float(np.mean(score_components))
        else:
            score = 50.0
            score += indicators["peak_hype_ratio"] * 40
            score -= indicators["warning_ratio"] * 20
            score = max(0.0, min(score, 100.0))

        if score >= 75:
            state = "PEAK_EUPHORIA"
        elif score >= 60:
            state = "HIGH_OPTIMISM"
        elif score >= 40:
            state = "BALANCED"
        else:
            state = "PESSIMISTIC"

        return MetricScore(
            score=round(score, 1),
            state=state,
            indicators=indicators,
            weight=self.weights["sentiment"],
        )

    def _calculate_positioning_score(self) -> MetricScore:
        data = self.processed_data.get("positioning", []) or self.processed_data["sentiment"]
        indicators = {}
        score_components: List[float] = []

        # Proxy: equity volatility z-score from ai_equity_history if available
        if self.db:
            try:
                df = self.db.execute(
                    "select ticker, date, close from ai_bubble_data.ai_equity_history "
                    "where close is not null"
                ).df()
                if not df.empty:
                    df["close"] = pd.to_numeric(df["close"], errors="coerce")
                    vols = []
                    for _, g in df.groupby("ticker"):
                        g = g.sort_values("date")
                        rets = g["close"].pct_change().dropna()
                        if len(rets) > 5:
                            vols.append(rets.std())
                    if vols:
                        series = pd.Series(vols)
                        z = (series.mean() - series.min()) / (series.std() or 1)
                        score_components.append(self._z_to_score(z))
                        indicators["avg_volatility"] = float(np.mean(vols))
            except Exception:
                pass

        indicators["crowding_level"] = "HIGH" if len(data) > 10 else "MODERATE"
        indicators["retail_interest"] = "ELEVATED"
        indicators["institutional_flows"] = "POSITIVE"

        if score_components:
            score = float(np.mean(score_components))
        else:
            score = 55.0
            if len(data) > 15:
                score += 20

        if score >= 70:
            state = "OVERCROWDED"
        elif score >= 50:
            state = "CROWDED"
        else:
            state = "BALANCED"

        return MetricScore(
            score=round(score, 1),
            state=state,
            indicators=indicators,
            weight=self.weights["positioning"],
        )

    def _calculate_liquidity_score(self) -> MetricScore:
        data = self.processed_data.get("liquidity", []) or self.raw_data
        indicators: Dict[str, Any] = {}
        score_components: List[float] = []

        # Quantitative: real yield, M2, HY OAS z-scores
        if self.db:
            try:
                df = self.db.execute(
                    "select metric, date, value from ai_bubble_data.fred_macro"
                ).df()
                if not df.empty:
                    for metric in ["real_yield_10y", "m2", "hy_oas"]:
                        series = df[df["metric"] == metric]["value"].astype(float)
                        if len(series) > 5:
                            z = (series.iloc[-1] - series.mean()) / (series.std() or 1)
                            score_components.append(self._z_to_score(z))
                            indicators[f"{metric}_latest"] = float(series.iloc[-1])
                            indicators[f"{metric}_z"] = float(z)
            except Exception:
                pass

        funding_decline = sum(
            1
            for d in data
            if "decline" in d.get("content", "").lower()
            or "down" in d.get("content", "").lower()
        )
        indicators["funding_trend"] = "DECLINING" if funding_decline > 2 else "STABLE"
        indicators["rate_environment"] = "RESTRICTIVE"
        indicators["funding_decline_mentions"] = funding_decline

        if score_components:
            score = float(np.mean(score_components))
        else:
            score = 40.0 + (funding_decline * 5)
            score = min(score, 100.0)

        if score >= 60:
            state = "TIGHT"
        elif score >= 40:
            state = "TIGHTENING"
        else:
            state = "ACCOMMODATIVE"

        return MetricScore(
            score=round(score, 1),
            state=state,
            indicators=indicators,
            weight=self.weights["liquidity"],
        )

    def _calculate_capex_score(self) -> MetricScore:
        data = self.processed_data.get("capex", []) or self.raw_data
        spending_mentions = sum(
            1
            for d in data
            if any(
                word in d.get("content", "").lower()
                for word in ["billion", "spending", "capex", "investment"]
            )
        )
        indicators = {
            "spending_mentions": spending_mentions,
            "spending_trend": "ACCELERATING",
            "roi_concern": "HIGH" if spending_mentions > 5 else "MODERATE",
        }

        score = 50.0 + (spending_mentions * 3)
        score = min(score, 100.0)

        if score >= 75:
            state = "UNSUSTAINABLE"
        elif score >= 60:
            state = "ELEVATED"
        else:
            state = "SUSTAINABLE"

        return MetricScore(
            score=round(score, 1),
            state=state,
            indicators=indicators,
            weight=self.weights["capex"],
        )

    # ==================== AGGREGATION & HELPERS ====================

    @staticmethod
    def _determine_bubble_state(overall_score: float) -> str:
        if overall_score >= 80:
            return "CRITICAL"
        if overall_score >= 65:
            return "HIGH_RISK"
        if overall_score >= 50:
            return "MODERATE"
        return "LOW"

    @staticmethod
    def _generate_warnings(*metrics: MetricScore) -> List[str]:
        warnings: List[str] = []
        for metric in metrics:
            if metric.score >= 75:
                if metric.state == "SEVERELY_OVERVALUED":
                    warnings.append("Valuations at extreme levels - dot-com bubble comparison")
                elif metric.state == "PEAK_EUPHORIA":
                    warnings.append("Sentiment at peak euphoria - contrarian indicator")
                elif metric.state == "UNSUSTAINABLE":
                    warnings.append("Capex spending outpacing revenue generation")
        if not warnings:
            warnings.append("No critical warnings at this time")
        return warnings[:5]

    @staticmethod
    def _compare_to_historical_bubbles(current_score: float) -> Dict[str, Any]:
        dotcom_peak = 85.0
        crypto_peak = 78.0
        housing_peak = 72.0
        return {
            "dotcom_2000": round(min(current_score / dotcom_peak, 1.0), 2),
            "crypto_2022": round(min(current_score / crypto_peak, 1.0), 2),
            "housing_2008": round(min(current_score / housing_peak, 1.0), 2),
            "comparison": "MORE_EXTREME" if current_score > dotcom_peak else "LESS_EXTREME",
        }

    def _calculate_confidence(self) -> float:
        total_datapoints = len(self.raw_data)
        numeric_sources = 0
        for table in [
            "ai_bubble_data.alpha_vantage_overview",
            "ai_bubble_data.fred_macro",
            "ai_bubble_data.google_trends_interest",
            "ai_bubble_data.ai_equity_history",
        ]:
            try:
                if self.db and self.db.execute(f"select count(*) from {table}").fetchone()[0] > 0:
                    numeric_sources += 1
            except Exception:
                continue

        base_conf = 0.65
        if total_datapoints >= 15:
            base_conf = 0.85
        elif total_datapoints >= 10:
            base_conf = 0.75

        # bump a bit for each numeric source available
        return min(0.95, base_conf + numeric_sources * 0.02)

    @staticmethod
    def _to_dict(analysis: BubbleAnalysis) -> Dict[str, Any]:
        result = asdict(analysis)
        # Convert MetricScore objects to plain dicts
        for key, metric in analysis.metrics.items():
            result["metrics"][key] = asdict(metric)
        return result

    @staticmethod
    def _z_to_score(z: float, scale: float = 15.0) -> float:
        """Map z-score to 0-100 with mean=50."""

        return max(0.0, min(100.0, 50.0 + z * scale))


def calculate_bubble_score(bubble_data: Union[str, Path, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Convenience wrapper for teammates: load data and compute scores."""

    if isinstance(bubble_data, (str, Path)):
        with open(bubble_data, "r") as f:
            data = json.load(f)
    else:
        data = bubble_data

    engine = BubbleScoringEngine(data)
    return engine.calculate_bubble_score()


def _main() -> None:
    data_path = DATA_PATH
    if not data_path.exists():
        raise FileNotFoundError(
            f"bubble_data.json not found at {data_path}. "
            "Place your curated dataset there or pass a path to calculate_bubble_score()."
        )
    result = calculate_bubble_score(data_path)
    print("=" * 60)
    print("🎈 AI BUBBLE BURST PROBABILITY ANALYSIS")
    print("=" * 60)
    print(f"\nOverall Bubble Score: {result['overall_bubble_score']}/100")
    print(f"State: {result['bubble_state']}")
    print(f"Confidence: {result['confidence']}")
    print("\nIndividual Metrics:")
    for name, metric in result["metrics"].items():
        print(f"  • {name.upper()}: {metric['score']}/100 ({metric['state']})")
    print("\nWarnings:")
    for warning in result["warning_signals"]:
        print(f"  - {warning}")
    output_path = Path(__file__).resolve().parent / "outputs" / "bubble_score_output.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2))
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    _main()
