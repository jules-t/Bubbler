// TypeScript types mirroring backend Pydantic schemas

export enum BubbleRiskLevel {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
}

// Metrics Categories (matching backend schemas.py exactly)
export interface MetricsCategory1 {
  pe_ratio: number;
  revenue_multiple: number;
  market_cap_gdp: number;
  growth_premium: number;
}

export interface MetricsCategory2 {
  media_mentions: number;
  social_sentiment: number;
  search_trends: number;
  analyst_ratings: number;
}

export interface MetricsCategory3 {
  fund_flows: number;
  institutional_holdings: number;
  retail_interest: number;
  options_volume: number;
}

export interface MetricsCategory4 {
  interest_rates: number;
  liquidity: number;
  vix: number;
  put_call_ratio: number;
}

export interface MetricsCategory5 {
  revenue_growth: number;
  profit_margins: number;
  capex_cycle: number;
  adoption_rate: number;
}

export interface MetricsData {
  category_1_valuation: MetricsCategory1;
  category_2_sentiment: MetricsCategory2;
  category_3_positioning: MetricsCategory3;
  category_4_macro: MetricsCategory4;
  category_5_fundamentals: MetricsCategory5;
}

// Bubble State
export interface BubbleState {
  risk_score: number;
  risk_level: BubbleRiskLevel;
  personality: string;
  summary: string;
}

// API Request/Response Types
export interface InitializeRequest {
  bubble_id: string;
  metrics: MetricsData;
}

export interface InitializeResponse {
  risk_score: number;
  risk_level: BubbleRiskLevel;
  personality: string;
  summary: string;
}

export interface VoiceConversationRequest {
  bubble_id: string;
  audio_base64: string;
  conversation_id?: string;
}

export interface ConversationResponse {
  conversation_id: string;
  user_transcript: string;
  bubble_response: string;
  audio_base64: string;
  bubble_state: BubbleState;
}

export interface HealthCheckResponse {
  status: string;
  message: string;
  services: {
    openai: boolean;
    elevenlabs: boolean;
  };
  bubbles_initialized: number;
}

// Error Response
export interface ApiError {
  detail: string;
}

// Analysis types
export interface Index {
  id: string;
  name: string;
  description: string;
  value: number;
  marketWeight: number;
  userValue?: number;
  explanation: string;
}

export interface Category {
  id:string;
  name: string;
  description: string;
  indexes: Index[];
  userWeight: number;
  marketWeight: number;
  explanation: string;
}

export interface AnalysisRequest {
  categories: Category[];
}

export interface AnalysisResponse {
  user_snapshot: string;
  market_snapshot: string;
}

