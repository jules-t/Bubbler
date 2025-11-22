# Multi-Bubble Support Guide

The backend now supports multiple bubble instances running simultaneously. Users can interact with both the market bubble and their personalized bubbles.

## How It Works

Each bubble is identified by a unique `bubble_id`:
- **Market bubble**: `"market"`
- **Personal bubbles**: `"personal_{session_id}"` (e.g., `"personal_user123"`)

## API Changes

### 1. Initialize a Bubble
**Endpoint**: `POST /api/initialize`

**Request**:
```json
{
  "bubble_id": "market",
  "metrics": {
    "category1_valuation": { ... },
    "category2_sentiment": { ... },
    "category3_options_flow": { ... },
    "category4_macro": { ... },
    "category5_fundamentals": { ... }
  }
}
```

**When to call**:
- **Market bubble**: Data collection teammate calls with `bubble_id="market"` and real metrics
- **Personal bubble**: Frontend calls when user adjusts sliders with `bubble_id="personal_{session_id}"` and slider values

### 2. Get Bubble Status
**Endpoint**: `GET /api/bubble-status/{bubble_id}`

**Examples**:
- `GET /api/bubble-status/market`
- `GET /api/bubble-status/personal_user123`

### 3. Chat with a Bubble
**Endpoint**: `POST /api/chat/voice`

**Request**:
```json
{
  "bubble_id": "market",
  "audio_base64": "base64_encoded_audio...",
  "conversation_id": "optional_conversation_id"
}
```

**Response**:
```json
{
  "bubble_id": "market",
  "audio_base64": "base64_encoded_response...",
  "transcript_user": "What the user said",
  "transcript_agent": "What the agent responded",
  "bubble_state": {
    "risk_score": 68.5,
    "risk_level": "high",
    "personality": "...",
    "summary": "..."
  },
  "conversation_id": "conversation_id"
}
```

## Frontend Integration

### User Flow 1: Talk to Market Bubble
1. User clicks "Market Bubble" on landing page
2. Frontend navigates to chat page
3. **Initialize** (if needed):
   ```javascript
   // Only if data teammate hasn't already initialized
   POST /api/initialize with { bubble_id: "market", metrics: {...} }
   ```
4. **Chat**:
   ```javascript
   POST /api/chat/voice with { bubble_id: "market", audio_base64: "..." }
   ```

### User Flow 2: Create and Talk to Personal Bubble
1. User adjusts sliders on landing page
2. User clicks "Personal Bubble"
3. **Initialize with slider values**:
   ```javascript
   const sessionId = getUserSessionId(); // Generate or get from cookie
   POST /api/initialize with {
     bubble_id: `personal_${sessionId}`,
     metrics: getMetricsFromSliders()
   }
   ```
4. Frontend navigates to chat page
5. **Chat**:
   ```javascript
   POST /api/chat/voice with {
     bubble_id: `personal_${sessionId}`,
     audio_base64: "..."
   }
   ```

### User Flow 3: Switch Between Bubbles
1. User talks to market bubble (creates conversation history)
2. User goes back, adjusts sliders, talks to personal bubble (creates separate conversation)
3. User goes back, clicks market bubble again
4. **Chat continues previous conversation**:
   - Same `bubble_id="market"` = same bubble state + conversation history
   - Each bubble maintains its own conversation context

## Key Points

- **Separate states**: Market and personal bubbles have completely independent metrics, risk scores, and personalities
- **Separate conversations**: Each bubble maintains its own conversation history
- **Session-based**: Personal bubbles use session IDs to allow users to return to their custom bubble
- **No conflicts**: Multiple bubbles can exist simultaneously without interfering

## Example Usage

### Initialize Market Bubble (Data Teammate)
```bash
curl -X POST http://localhost:8000/api/initialize \
  -H "Content-Type: application/json" \
  -d @example_metrics.json
```

### Initialize Personal Bubble (Frontend)
```bash
curl -X POST http://localhost:8000/api/initialize \
  -H "Content-Type: application/json" \
  -d '{
    "bubble_id": "personal_user123",
    "metrics": {
      "category1_valuation": {
        "nasdaq_100_forward_pe": 15.0,
        "nasdaq_100_10y_avg_pe": 22.0,
        "ai_etf_avg_pe": 20.0
      },
      ...
    }
  }'
```

### Check Bubble Status
```bash
# Market bubble
curl http://localhost:8000/api/bubble-status/market

# Personal bubble
curl http://localhost:8000/api/bubble-status/personal_user123
```

## Error Handling

If you try to chat with a bubble that doesn't exist:
```json
{
  "error": "Bubble 'personal_user123' not found. Please initialize it first with POST /api/initialize"
}
```

Solution: Call `/api/initialize` first with the bubble_id and metrics.
