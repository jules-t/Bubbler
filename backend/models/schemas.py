from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class BubbleRiskLevel(str, Enum):
    """Bubble risk level categories"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MetricsCategory1(BaseModel):
    """Valuation Metrics"""
    nasdaq_100_forward_pe: float = Field(..., description="NASDAQ-100 forward P/E ratio")
    nasdaq_100_10y_avg_pe: float = Field(..., description="NASDAQ-100 10-year average P/E")
    ai_etf_avg_pe: float = Field(..., description="AI ETF (e.g. BOTZ) average P/E")


class MetricsCategory2(BaseModel):
    """Sentiment Metrics"""
    cnn_fear_greed_index: float = Field(..., ge=0, le=100, description="CNN Fear & Greed Index (0-100)")
    social_bubble_mentions: int = Field(..., description="Reddit/Discord AI-ticker + Bubble mentions per day")


class MetricsCategory3(BaseModel):
    """Options & Flow Metrics"""
    nvda_put_call_ratio: float = Field(..., description="Put/Call ratio for NVDA")
    ai_etf_weekly_flows: float = Field(..., description="Weekly net flows into AI/thematic ETFs (millions)")
    avg_short_interest: float = Field(..., ge=0, le=100, description="Average short interest % of float (NVDA/SMCI)")
    nvda_iv_rv_ratio: float = Field(..., description="Implied volatility / Realized volatility ratio for NVDA")


class MetricsCategory4(BaseModel):
    """Macro & Liquidity Metrics"""
    us_10y_real_yield: float = Field(..., description="US 10Y real yield (TIPS) in %")
    m2_yoy_growth: float = Field(..., description="Global/US M2 YoY growth %")
    us_hy_credit_spread: float = Field(..., description="US HY credit spread (OAS) in basis points")


class MetricsCategory5(BaseModel):
    """Fundamental AI Metrics"""
    gpu_shipment_growth: float = Field(..., description="GPU Shipment Growth YoY %")
    ai_capex_burden: float = Field(..., description="AI Capex / OCF ratio")
    enterprise_ai_adoption: float = Field(..., ge=0, le=100, description="Enterprise AI Adoption Rate %")


class MetricsData(BaseModel):
    """Complete set of metrics for bubble risk assessment"""
    category1_valuation: MetricsCategory1
    category2_sentiment: MetricsCategory2
    category3_options_flow: MetricsCategory3
    category4_macro: MetricsCategory4
    category5_fundamentals: MetricsCategory5


class BubbleState(BaseModel):
    """Current state of the bubble agent"""
    risk_score: float = Field(..., ge=0, le=100, description="Risk score from 0 (safe) to 100 (about to pop)")
    risk_level: BubbleRiskLevel
    personality_description: str
    metrics_summary: str


class InitializeRequest(BaseModel):
    """Request to initialize the agent with metrics"""
    bubble_id: str = Field(..., description="Unique identifier for this bubble (e.g., 'market', 'personal_user123')")
    metrics: MetricsData


class VoiceConversationRequest(BaseModel):
    """Request for voice-based conversation"""
    bubble_id: str = Field(..., description="Which bubble to talk to (e.g., 'market', 'personal_user123')")
    audio_base64: str = Field(..., description="Base64 encoded audio data")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context")


class ConversationResponse(BaseModel):
    """Response from the bubble agent"""
    bubble_id: str = Field(..., description="Which bubble responded")
    audio_base64: str = Field(..., description="Base64 encoded audio response")
    transcript_user: str = Field(..., description="Transcription of user's speech")
    transcript_agent: str = Field(..., description="Agent's text response before TTS")
    bubble_state: BubbleState
    conversation_id: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    agent_initialized: bool
    services_available: dict


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
