from models.schemas import MetricsData, BubbleState, BubbleRiskLevel


class BubbleAgent:
    """Core bubble agent that calculates risk and determines personality"""

    def __init__(self):
        self.current_metrics: MetricsData | None = None
        self.current_state: BubbleState | None = None

    def initialize_with_metrics(self, metrics: MetricsData) -> BubbleState:
        """Initialize the agent with economic metrics and calculate bubble state"""
        self.current_metrics = metrics
        risk_score = self._calculate_risk_score(metrics)
        risk_level = self._determine_risk_level(risk_score)
        personality = self._generate_personality_description(risk_score, risk_level)
        summary = self._generate_metrics_summary(metrics)

        self.current_state = BubbleState(
            risk_score=risk_score,
            risk_level=risk_level,
            personality_description=personality,
            metrics_summary=summary
        )

        return self.current_state

    def _calculate_risk_score(self, metrics: MetricsData) -> float:
        """
        Calculate overall bubble risk score (0-100) based on all metrics.
        Higher score = higher risk of bubble bursting.
        """
        score = 0.0

        # Category 1: Valuation (20% weight)
        # High P/E ratios compared to historical average = higher risk
        cat1 = metrics.category1_valuation
        pe_deviation = (cat1.nasdaq_100_forward_pe / cat1.nasdaq_100_10y_avg_pe - 1) * 100
        valuation_risk = min(max((pe_deviation + cat1.ai_etf_avg_pe / 5), 0), 20)
        score += valuation_risk

        # Category 2: Sentiment (15% weight)
        # High greed and high social mentions = higher risk
        cat2 = metrics.category2_sentiment
        sentiment_risk = (cat2.cnn_fear_greed_index / 100 * 10) + min(cat2.social_bubble_mentions / 100, 5)
        score += min(sentiment_risk, 15)

        # Category 3: Options & Flow (25% weight)
        # Low put/call (complacency), high outflows, low short interest = higher risk
        cat3 = metrics.category3_options_flow
        put_call_signal = max(10 - cat3.nvda_put_call_ratio * 10, 0)  # Low put/call = higher risk
        flow_signal = max(-cat3.ai_etf_weekly_flows / 1000, 0)  # Outflows = risk
        short_signal = max(5 - cat3.avg_short_interest / 4, 0)  # Low short interest = complacency
        iv_signal = max((cat3.nvda_iv_rv_ratio - 1) * 5, 0)  # High IV/RV = nervousness
        options_risk = min(put_call_signal + flow_signal + short_signal + iv_signal, 25)
        score += options_risk

        # Category 4: Macro (20% weight)
        # High real yields, low M2 growth, high credit spreads = tighter conditions = higher risk
        cat4 = metrics.category4_macro
        yield_risk = max(cat4.us_10y_real_yield * 2, 0)
        m2_risk = max(5 - cat4.m2_yoy_growth / 2, 0)  # Low M2 growth = less liquidity
        credit_risk = max(cat4.us_hy_credit_spread / 50, 0)
        macro_risk = min(yield_risk + m2_risk + credit_risk, 20)
        score += macro_risk

        # Category 5: Fundamentals (20% weight)
        # Slowing GPU growth, high capex burden, low adoption = weaker fundamentals
        cat5 = metrics.category5_fundamentals
        gpu_risk = max(10 - cat5.gpu_shipment_growth / 10, 0)
        capex_risk = max(cat5.ai_capex_burden * 3, 0)
        adoption_risk = max((100 - cat5.enterprise_ai_adoption) / 10, 0)
        fundamental_risk = min(gpu_risk + capex_risk + adoption_risk, 20)
        score += fundamental_risk

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
        cat1 = metrics.category1_valuation
        cat2 = metrics.category2_sentiment
        cat5 = metrics.category5_fundamentals

        return (
            f"Valuation: NASDAQ-100 P/E {cat1.nasdaq_100_forward_pe:.1f} "
            f"(10Y avg: {cat1.nasdaq_100_10y_avg_pe:.1f}), AI ETF P/E {cat1.ai_etf_avg_pe:.1f}. "
            f"Sentiment: Fear/Greed {cat2.cnn_fear_greed_index:.0f}, "
            f"Social mentions {cat2.social_bubble_mentions}/day. "
            f"Fundamentals: GPU growth {cat5.gpu_shipment_growth:.1f}%, "
            f"Enterprise adoption {cat5.enterprise_ai_adoption:.1f}%."
        )

    def get_current_state(self) -> BubbleState | None:
        """Get the current bubble state"""
        return self.current_state

    def is_initialized(self) -> bool:
        """Check if agent has been initialized with metrics"""
        return self.current_state is not None


# Global agent instance
bubble_agent = BubbleAgent()
