# Bubbler - AI Economic Bubble Agent

A voice-based conversational AI agent that personifies the AI economic bubble. The agent's personality and responses change based on real-time economic metrics, ranging from euphoric and inflated (low risk) to panicked and about to pop (high risk).

## Project Structure

```
Bubbler/
├── backend/              # FastAPI backend (Python)
│   ├── main.py          # FastAPI app and endpoints
│   ├── config.py        # Configuration and API keys
│   ├── requirements.txt # Python dependencies
│   ├── models/          # Pydantic schemas
│   ├── services/        # Core services (OpenAI, ElevenLabs, bubble logic)
│   ├── utils/           # Helper utilities (prompt builder)
│   └── data/            # Data storage
├── frontend/            # Frontend (handled by teammate)
└── .env                 # Environment variables (API keys)
```

## Backend Setup

### Prerequisites

- Python 3.9+
- OpenAI API key
- ElevenLabs API key

### Installation

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
Edit the `.env` file in the root directory and add your API keys:
```
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### Running the Server

From the backend directory:
```bash
python main.py
```

The server will start on `http://localhost:8000`

API documentation (Swagger UI) available at: `http://localhost:8000/docs`

## API Endpoints

### Health Check
```
GET /api/health
```
Returns server status and service availability.

### Initialize Agent
```
POST /api/initialize
```
Initialize the agent with economic metrics. Must be called before using the chat endpoint.

**Request body example:**
```json
{
  "metrics": {
    "category1_valuation": {
      "nasdaq_100_forward_pe": 25.5,
      "nasdaq_100_10y_avg_pe": 20.0,
      "ai_etf_avg_pe": 35.2
    },
    "category2_sentiment": {
      "cnn_fear_greed_index": 75,
      "social_bubble_mentions": 450
    },
    "category3_options_flow": {
      "nvda_put_call_ratio": 0.6,
      "ai_etf_weekly_flows": -500.0,
      "avg_short_interest": 8.5,
      "nvda_iv_rv_ratio": 1.3
    },
    "category4_macro": {
      "us_10y_real_yield": 2.1,
      "m2_yoy_growth": 3.5,
      "us_hy_credit_spread": 350
    },
    "category5_fundamentals": {
      "gpu_shipment_growth": 45.0,
      "ai_capex_burden": 0.8,
      "enterprise_ai_adoption": 35.0
    }
  }
}
```

### Get Bubble Status
```
GET /api/bubble-status
```
Returns current bubble risk level and personality state.

### Voice Chat
```
POST /api/chat/voice
```
Main conversation endpoint. Sends audio, receives audio response.

**Request body:**
```json
{
  "audio_base64": "base64_encoded_audio_data",
  "conversation_id": "optional_conversation_id"
}
```

**Response:**
```json
{
  "audio_base64": "base64_encoded_audio_response",
  "transcript_user": "What the user said",
  "transcript_agent": "What the agent responded",
  "bubble_state": {
    "risk_score": 65.5,
    "risk_level": "medium",
    "personality_description": "Anxious and uncertain...",
    "metrics_summary": "Current metrics summary..."
  },
  "conversation_id": "conversation_id"
}
```

## How It Works

### Bubble Risk Calculation

The agent calculates a risk score (0-100) based on 5 categories of metrics:

1. **Valuation Metrics (20%)**: P/E ratios
2. **Sentiment Metrics (15%)**: Fear/Greed Index, social mentions
3. **Options & Flow Metrics (25%)**: Put/call ratios, ETF flows, short interest
4. **Macro Metrics (20%)**: Real yields, M2 growth, credit spreads
5. **Fundamental Metrics (20%)**: GPU growth, AI capex, enterprise adoption

### Personality States

- **Low Risk (0-33)**: Confident, inflated, euphoric
- **Medium Risk (34-66)**: Anxious, wobbly, uncertain
- **High Risk (67-100)**: Panicked, fragile, about to pop

### Conversation Flow

1. User speaks → Audio sent to backend
2. ElevenLabs STT → Converts audio to text
3. OpenAI GPT-4 → Generates response with bubble personality
4. ElevenLabs TTS → Converts response to audio
5. Audio returned to frontend

## Development

### Testing Locally

You can test the API using the Swagger UI at `http://localhost:8000/docs` or use curl:

```bash
# Health check
curl http://localhost:8000/api/health

# Initialize with example metrics
curl -X POST http://localhost:8000/api/initialize \
  -H "Content-Type: application/json" \
  -d @example_metrics.json

# Get bubble status
curl http://localhost:8000/api/bubble-status
```

### For the Data Collection Teammate

Call the `/api/initialize` endpoint with the latest metrics whenever you have new data. The format is shown in the example above.

### For the Frontend Teammate

The main endpoint you'll use is `POST /api/chat/voice`. Send base64 encoded audio and receive base64 encoded audio back, along with transcripts and bubble state information.

## Team Division

- **Backend** (this repo): FastAPI server, OpenAI integration, ElevenLabs integration, bubble logic
- **Data Collection**: Gathering economic metrics and calling `/api/initialize`
- **Frontend**: User interface and voice recording/playback

## License

Hackathon Project