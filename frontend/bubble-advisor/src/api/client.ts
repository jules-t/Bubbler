import {
  InitializeRequest,
  InitializeResponse,
  VoiceConversationRequest,
  ConversationResponse,
  BubbleState,
  HealthCheckResponse,
  ApiError,
  Category,
  AnalysisRequest,
  AnalysisResponse,
} from "@/types/api";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        detail: `HTTP error ${response.status}: ${response.statusText}`,
      }));
      throw new Error(error.detail);
    }
    return response.json();
  }

  async healthCheck(): Promise<HealthCheckResponse> {
    const response = await fetch(`${this.baseUrl}/api/health`);
    return this.handleResponse<HealthCheckResponse>(response);
  }

  async initializeBubble(
    bubbleId: string,
    metrics: InitializeRequest["metrics"]
  ): Promise<InitializeResponse> {
    const response = await fetch(`${this.baseUrl}/api/initialize`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        bubble_id: bubbleId,
        metrics,
      } as InitializeRequest),
    });
    return this.handleResponse<InitializeResponse>(response);
  }

  async getBubbleStatus(bubbleId: string): Promise<BubbleState> {
    const response = await fetch(
      `${this.baseUrl}/api/bubble-status/${bubbleId}`
    );
    return this.handleResponse<BubbleState>(response);
  }

  async getAnalysis(
    categories: Category[]
  ): Promise<AnalysisResponse> {
    const response = await fetch(`${this.baseUrl}/api/analysis`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        categories,
      } as AnalysisRequest),
    });
    return this.handleResponse<AnalysisResponse>(response);
  }

  async sendVoiceMessage(
    bubbleId: string,
    audioBase64: string,
    conversationId?: string
  ): Promise<ConversationResponse> {
    const response = await fetch(`${this.baseUrl}/api/chat/voice`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        bubble_id: bubbleId,
        audio_base64: audioBase64,
        conversation_id: conversationId,
      } as VoiceConversationRequest),
    });
    return this.handleResponse<ConversationResponse>(response);
  }
}

// Export a singleton instance
export const apiClient = new ApiClient(API_URL);

// Export the class for testing
export { ApiClient };
