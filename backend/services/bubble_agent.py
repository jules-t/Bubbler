from models.schemas import MetricsData, BubbleState, BubbleRiskLevel
from typing import Dict, Any
from pathlib import Path
import sys

# Add data folder to path for imports
data_models_path = Path(__file__).parent.parent / "data" / "models"
if str(data_models_path) not in sys.path:
    sys.path.insert(0, str(data_models_path))

try:
    from scoring_engine import calculate_bubble_score
    SCORING_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Advanced scoring engine not available: {e}")
    SCORING_ENGINE_AVAILABLE = False


class BubbleAgent:
    """Core bubble agent that calculates risk and determines personality"""

    def __init__(self):
        # Store multiple bubbles by bubble_id
        self.bubbles: Dict[str, dict] = {}
        # Each bubble stores: {"metrics": MetricsData, "state": BubbleState}

        # Paths for advanced scoring
        self.bubble_data_path = Path(__file__).parent.parent / "data" / "outputs" / "bubble_data.json"
        self.duckdb_path = Path(__file__).parent.parent / "data" / "db" / "redit_pipeline.duckdb"

    def initialize_with_metrics(self, bubble_id: str, metrics: MetricsData) -> BubbleState:
        """Initialize a specific bubble with economic metrics and calculate bubble state"""
        # Use advanced scoring for market bubble if available
        if bubble_id == "market" and SCORING_ENGINE_AVAILABLE:
            try:
                return self._initialize_market_bubble()
            except Exception as e:
                print(f"Advanced scoring failed for market bubble: {e}")
                print("Falling back to simple scoring...")
                # Fall through to simple scoring

        # Use simple scoring for personal bubbles or as fallback
        return self._initialize_simple_bubble(bubble_id, metrics)

    def _initialize_simple_bubble(self, bubble_id: str, metrics: MetricsData) -> BubbleState:
        """Initialize bubble using simple metric-based scoring (original logic)"""
        risk_score = self._calculate_risk_score(metrics)
        risk_level = self._determine_risk_level(risk_score)
        personality = self._generate_personality_description(risk_score, risk_level)
        summary = self._generate_metrics_summary(metrics)

        bubble_state = BubbleState(
            risk_score=risk_score,
            risk_level=risk_level,
            personality=personality,
            summary=summary
        )

        # Store this bubble's data
        self.bubbles[bubble_id] = {
            "metrics": metrics,
            "state": bubble_state
        }

        return bubble_state

    def _initialize_market_bubble(self) -> BubbleState:
        """Initialize market bubble using advanced scoring engine with real data"""
        if not self.bubble_data_path.exists():
            raise FileNotFoundError(f"bubble_data.json not found at {self.bubble_data_path}")

        # Calculate advanced score using real market data
        analysis = calculate_bubble_score(str(self.bubble_data_path))

        # Map analysis to BubbleState
        risk_score = analysis["overall_bubble_score"]
        risk_level = self._map_bubble_state_to_risk_level(analysis["bubble_state"])
        personality = self._generate_advanced_personality(analysis)
        summary = self._generate_advanced_summary(analysis)

        bubble_state = BubbleState(
            risk_score=risk_score,
            risk_level=risk_level,
            personality=personality,
            summary=summary,
            confidence=analysis.get("confidence"),
            warning_signals=analysis.get("warning_signals"),
            historical_comparison=analysis.get("historical_comparison")
        )

        # Store this bubble's data with full analysis
        self.bubbles["market"] = {
            "analysis": analysis,
            "state": bubble_state
        }

        return bubble_state

    def _calculate_risk_score(self, metrics: MetricsData) -> float:
        """
        Calculate overall bubble risk score (0-100) based on all metrics.
        Higher score = higher risk of bubble bursting.
        All input metrics are normalized 0-100 values.
        """
        # Category weights
        weights = {
            'valuation': 0.20,
            'sentiment': 0.15,
            'positioning': 0.25,
            'macro': 0.20,
            'fundamentals': 0.20
        }

        score = 0.0

        # Category 1: Valuation (20% weight)
        cat1 = metrics.category_1_valuation
        valuation_avg = (cat1.pe_ratio + cat1.revenue_multiple + cat1.market_cap_gdp + cat1.growth_premium) / 4
        score += valuation_avg * weights['valuation']

        # Category 2: Sentiment (15% weight)
        cat2 = metrics.category_2_sentiment
        sentiment_avg = (cat2.media_mentions + cat2.social_sentiment + cat2.search_trends + cat2.analyst_ratings) / 4
        score += sentiment_avg * weights['sentiment']

        # Category 3: Positioning & Flow (25% weight)
        cat3 = metrics.category_3_positioning
        positioning_avg = (cat3.fund_flows + cat3.institutional_holdings + cat3.retail_interest + cat3.options_volume) / 4
        score += positioning_avg * weights['positioning']

        # Category 4: Macro & Liquidity (20% weight)
        cat4 = metrics.category_4_macro
        macro_avg = (cat4.interest_rates + cat4.liquidity + cat4.vix + cat4.put_call_ratio) / 4
        score += macro_avg * weights['macro']

        # Category 5: Fundamentals (20% weight)
        cat5 = metrics.category_5_fundamentals
        fundamentals_avg = (cat5.revenue_growth + cat5.profit_margins + cat5.capex_cycle + cat5.adoption_rate) / 4
        score += fundamentals_avg * weights['fundamentals']

        # Normalize to 0-100 range
        return min(max(score, 0), 100)

    def _determine_risk_level(self, risk_score: float) -> BubbleRiskLevel:
        """Determine categorical risk level from score"""
        if risk_score < 33:
            return BubbleRiskLevel.LOW
        elif risk_score < 67:
            return BubbleRiskLevel.MEDIUM
        else:
            return BubbleRiskLevel.HIGH

    def _generate_personality_description(self, risk_score: float, risk_level: BubbleRiskLevel) -> str:
        """Generate personality description based on risk level"""
        if risk_level == BubbleRiskLevel.LOW:
            return (
                "Confident and inflated. Feeling euphoric and expansive. "
                "Full of optimism about AI's future. Dismissive of concerns."
            )
        elif risk_level == BubbleRiskLevel.MEDIUM:
            return (
                "Anxious and uncertain. Starting to feel wobbly and uncomfortable. "
                "Aware of growing pressures. Nervous about the future."
            )
        else:  # HIGH
            return (
                "Panicked and unwell. Feeling fragile and about to pop. "
                "Overwhelmed by warning signs. Desperate and unstable."
            )

    def _generate_metrics_summary(self, metrics: MetricsData) -> str:
        """Generate human-readable summary of key metrics"""
        cat1 = metrics.category_1_valuation
        cat2 = metrics.category_2_sentiment
        cat5 = metrics.category_5_fundamentals

        valuation_avg = (cat1.pe_ratio + cat1.revenue_multiple + cat1.market_cap_gdp + cat1.growth_premium) / 4
        sentiment_avg = (cat2.media_mentions + cat2.social_sentiment + cat2.search_trends + cat2.analyst_ratings) / 4
        fundamentals_avg = (cat5.revenue_growth + cat5.profit_margins + cat5.capex_cycle + cat5.adoption_rate) / 4

        return (
            f"Valuation indicators at {valuation_avg:.1f}/100. "
            f"Market sentiment at {sentiment_avg:.1f}/100. "
            f"Fundamental strength at {fundamentals_avg:.1f}/100."
        )

    def _map_bubble_state_to_risk_level(self, state: str) -> BubbleRiskLevel:
        """Map advanced scoring engine states to API risk levels"""
        mapping = {
            "LOW": BubbleRiskLevel.LOW,
            "MODERATE": BubbleRiskLevel.MEDIUM,
            "HIGH_RISK": BubbleRiskLevel.HIGH,
            "CRITICAL": BubbleRiskLevel.HIGH
        }
        return mapping.get(state, BubbleRiskLevel.MEDIUM)

    def _generate_advanced_personality(self, analysis: Dict[str, Any]) -> str:
        """Generate personality using real market analysis data"""
        state = analysis["bubble_state"]
        metrics = analysis["metrics"]
        warnings = analysis.get("warning_signals", [])

        # Extract key metric states
        valuation = metrics["valuation"]
        sentiment = metrics["sentiment"]
        capex = metrics["capex"]
        liquidity = metrics["liquidity"]

        # Build personality based on actual market conditions
        if state == "CRITICAL":
            personality = (
                f"I'm feeling extremely fragile and unstable. {warnings[0] if warnings else 'Multiple critical warning signs.'} "
                f"My valuations are {valuation['state'].lower().replace('_', ' ')} "
                f"while sentiment has reached {sentiment['state'].lower().replace('_', ' ')}. "
                f"I'm terrified - I feel like I could pop at any moment."
            )
        elif state == "HIGH_RISK":
            personality = (
                f"I'm feeling very anxious and wobbly. {warnings[0] if warnings else 'Several warning signs are flashing.'} "
                f"With {sentiment['state'].lower().replace('_', ' ')} in the market "
                f"and {capex['state'].lower()} spending levels, "
                f"I'm getting increasingly uncomfortable about my stability."
            )
        elif state == "MODERATE":
            personality = (
                f"I'm feeling cautiously optimistic but watchful. "
                f"Sentiment is at {sentiment['state'].lower().replace('_', ' ')} "
                f"while valuations show {valuation['state'].lower().replace('_', ' ')}. "
                f"There are some concerns, but I'm not panicking yet."
            )
        else:  # LOW
            personality = (
                f"I'm feeling confident and expansive! "
                f"Valuations are {valuation['state'].lower().replace('_', ' ')} "
                f"and fundamentals look solid. "
                f"This AI revolution has plenty of room to grow!"
            )

        return personality

    def _generate_advanced_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate summary using real market indicators"""
        metrics = analysis["metrics"]
        confidence = analysis.get("confidence", 0.0)
        historical = analysis.get("historical_comparison", {})

        # Extract scores
        val_score = metrics["valuation"]["score"]
        sent_score = metrics["sentiment"]["score"]
        pos_score = metrics["positioning"]["score"]
        liq_score = metrics["liquidity"]["score"]
        capex_score = metrics["capex"]["score"]

        # Build summary with real data
        summary = (
            f"Overall bubble risk: {analysis['overall_bubble_score']:.1f}/100 (confidence: {confidence:.0%}). "
            f"Valuation: {val_score:.1f}/100, "
            f"Sentiment: {sent_score:.1f}/100, "
            f"Positioning: {pos_score:.1f}/100, "
            f"Liquidity: {liq_score:.1f}/100, "
            f"CapEx: {capex_score:.1f}/100."
        )

        # Add historical context if available
        if historical:
            dotcom = historical.get("dotcom_2000", 0)
            summary += f" Currently at {dotcom:.0%} of dotcom-2000 peak levels."

        return summary

    def get_bubble_state(self, bubble_id: str) -> BubbleState | None:
        """Get the state of a specific bubble"""
        if bubble_id in self.bubbles:
            return self.bubbles[bubble_id]["state"]
        return None

    def is_bubble_initialized(self, bubble_id: str) -> bool:
        """Check if a specific bubble has been initialized with metrics"""
        return bubble_id in self.bubbles

    def get_all_bubble_ids(self) -> list[str]:
        """Get list of all initialized bubble IDs"""
        return list(self.bubbles.keys())


# Global agent instance
bubble_agent = BubbleAgent()
