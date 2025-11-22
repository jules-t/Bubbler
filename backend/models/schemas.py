from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class BubbleRiskLevel(str, Enum):
    """Bubble risk level categories"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MetricsCategory1(BaseModel):
    """Valuation Metrics - accepts any numeric values 0-100"""
    pe_ratio: float = Field(..., ge=0, le=100, description="P/E ratio metric")
    revenue_multiple: float = Field(..., ge=0, le=100, description="Revenue multiple metric")
    market_cap_gdp: float = Field(..., ge=0, le=100, description="Market cap to GDP metric")
    growth_premium: float = Field(..., ge=0, le=100, description="Growth premium metric")


class MetricsCategory2(BaseModel):
    """Sentiment Metrics - accepts any numeric values 0-100"""
    media_mentions: float = Field(..., ge=0, le=100, description="Media mentions metric")
    social_sentiment: float = Field(..., ge=0, le=100, description="Social sentiment metric")
    search_trends: float = Field(..., ge=0, le=100, description="Search trends metric")
    analyst_ratings: float = Field(..., ge=0, le=100, description="Analyst ratings metric")


class MetricsCategory3(BaseModel):
    """Positioning & Flow Metrics - accepts any numeric values 0-100"""
    fund_flows: float = Field(..., ge=0, le=100, description="Fund flows metric")
    institutional_holdings: float = Field(..., ge=0, le=100, description="Institutional holdings metric")
    retail_interest: float = Field(..., ge=0, le=100, description="Retail interest metric")
    options_volume: float = Field(..., ge=0, le=100, description="Options volume metric")


class MetricsCategory4(BaseModel):
    """Macro & Liquidity Metrics - accepts any numeric values 0-100"""
    interest_rates: float = Field(..., ge=0, le=100, description="Interest rates metric")
    liquidity: float = Field(..., ge=0, le=100, description="Liquidity metric")
    vix: float = Field(..., ge=0, le=100, description="VIX fear index metric")
    put_call_ratio: float = Field(..., ge=0, le=100, description="Put/Call ratio metric")


class MetricsCategory5(BaseModel):
    """Fundamental AI Metrics - accepts any numeric values 0-100"""
    revenue_growth: float = Field(..., ge=0, le=100, description="Revenue growth metric")
    profit_margins: float = Field(..., ge=0, le=100, description="Profit margins metric")
    capex_cycle: float = Field(..., ge=0, le=100, description="CapEx cycle metric")
    adoption_rate: float = Field(..., ge=0, le=100, description="Adoption rate metric")


class MetricsData(BaseModel):
    """Complete set of metrics for bubble risk assessment"""
    category_1_valuation: MetricsCategory1
    category_2_sentiment: MetricsCategory2
    category_3_positioning: MetricsCategory3
    category_4_macro: MetricsCategory4
    category_5_fundamentals: MetricsCategory5


class BubbleState(BaseModel):
    """Current state of the bubble agent"""
    risk_score: float = Field(..., ge=0, le=100, description="Risk score from 0 (safe) to 100 (about to pop)")
    risk_level: BubbleRiskLevel
    personality: str = Field(..., description="Personality description")
    summary: str = Field(..., description="Metrics summary")


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
    conversation_id: str
    user_transcript: str = Field(..., description="Transcription of user's speech")
    bubble_response: str = Field(..., description="Agent's text response before TTS")
    audio_base64: str = Field(..., description="Base64 encoded audio response")
    bubble_state: BubbleState


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    agent_initialized: bool
    services_available: dict


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
