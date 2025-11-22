from models.schemas import MetricsData, BubbleState, BubbleRiskLevel
from typing import Dict


class BubbleAgent:
    """Core bubble agent that calculates risk and determines personality"""

    def __init__(self):
        # Store multiple bubbles by bubble_id
        self.bubbles: Dict[str, dict] = {}
        # Each bubble stores: {"metrics": MetricsData, "state": BubbleState}

    def initialize_with_metrics(self, bubble_id: str, metrics: MetricsData) -> BubbleState:
        """Initialize a specific bubble with economic metrics and calculate bubble state"""
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
