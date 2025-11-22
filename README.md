# Bubbler - AI Economic Bubble Advisor

<div align="center">

**A conversational AI agent that personifies and analyzes economic bubble dynamics in real-time**

[Features](#features) • [Architecture](#architecture) • [Setup](#setup) • [API Documentation](#api-documentation) • [Technical Details](#technical-details)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Setup & Installation](#setup--installation)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Technical Details](#technical-details)
- [Data Model](#data-model)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

**Bubbler** is an intelligent economic bubble analysis platform that combines real-time market metrics with conversational AI. The system features:

- **Dual-Bubble Analysis**: Compare market consensus against personalized risk assessments
- **Voice-Powered AI Agent**: Interactive conversations with a personality-driven bubble entity
- **Dynamic Risk Calculation**: Real-time scoring based on 25+ economic indicators across 5 categories
- **Adaptive Personality**: AI responses change from euphoric to panicked based on bubble risk levels
- **Interactive Visualization**: 3D bubble rendering with size and color reflecting risk metrics

The application enables users to understand economic bubble dynamics through both analytical tools and natural conversation with an AI that embodies the bubble's emotional state.

---

## Features

### Core Capabilities

#### 1. **Market Consensus Analysis**
- Pre-configured with current AI sector market metrics
- Real-time bubble risk scoring (0-100 scale)
- 5 category breakdown: Valuation, Sentiment, Positioning, Macro, Fundamentals
- 25+ individual factor indexes with explanations

#### 2. **Personalized User Analysis**
- Fully customizable category weights (importance)
- Granular control over individual factor values
- Advanced controls for all 25 economic indicators
- Real-time recalculation of bubble risk
- Local persistence of user preferences

#### 3. **Voice-Powered Conversational AI**
- Natural speech-to-text conversation
- Context-aware responses maintaining conversation history
- Personality that shifts based on bubble risk level:
  - **Low Risk (0-33)**: Confident, euphoric, inflated
  - **Medium Risk (34-66)**: Anxious, wobbly, uncertain
  - **High Risk (67-100)**: Panicked, fragile, about to pop
- Text-to-speech audio responses
- Real-time audio playback

#### 4. **Interactive Data Visualization**
- 3D animated bubble representation
- Size proportional to risk score
- Color gradient (green → yellow → red) based on risk
- Smooth transitions and animations
- Historical trend chart showing score evolution

#### 5. **Educational Insights**
- Detailed explanations for each economic category
- Factor-specific tooltips explaining market implications
- Contribution analysis showing impact of each category
- Market comparison (user values vs market consensus)

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  React 18 + TypeScript + Vite (Port 8080)                   │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Landing    │  │   Market     │  │     User     │      │
│  │     Page     │  │  Consensus   │  │   Analysis   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌─────────────────────────────────────────────────┐        │
│  │  Components: BubbleVisualization, Voice Agent,  │        │
│  │  Category Controls, Trend Charts                │        │
│  └─────────────────────────────────────────────────┘        │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API (HTTPS)
                         │
┌────────────────────────▼────────────────────────────────────┐
│                         Backend                              │
│         FastAPI + Python 3.9+ (Port 8000)                   │
│                                                               │
│  ┌──────────────────────────────────────────────────┐       │
│  │              API Endpoints                        │       │
│  │  /api/initialize - Initialize bubble state       │       │
│  │  /api/bubble-status/{id} - Get current state     │       │
│  │  /api/chat/voice - Voice conversation             │       │
│  └──────────────────────────────────────────────────┘       │
│                                                               │
│  ┌──────────────────────────────────────────────────┐       │
│  │              Services Layer                       │       │
│  │  • BubbleAgent - Risk calculation & personality  │       │
│  │  • OpenAI Service - GPT-4 conversations          │       │
│  │  • ElevenLabs Service - Voice STT/TTS            │       │
│  └──────────────────────────────────────────────────┘       │
└───────────────────────┬──────────────────┬──────────────────┘
                        │                  │
                   ┌────▼─────┐      ┌────▼──────┐
                   │  OpenAI  │      │ ElevenLabs│
                   │  GPT-4   │      │  Voice AI │
                   └──────────┘      └───────────┘
```

### Data Flow

#### Initialization Flow
```
User loads page → Frontend calculates local score
                ↓
        initializeBubble() API call
                ↓
    Backend receives categories/metrics
                ↓
        Risk calculation (weighted average)
                ↓
    Personality state determination (Low/Med/High)
                ↓
        BubbleState returned to frontend
                ↓
    Display backend score + personality description
```

#### Voice Conversation Flow
```
User speaks → MediaRecorder captures audio
                ↓
        Convert to base64 encoding
                ↓
    POST /api/chat/voice with audio_base64
                ↓
    Backend: ElevenLabs STT (speech-to-text)
                ↓
    Construct prompt with bubble personality + context
                ↓
        OpenAI GPT-4 generates response
                ↓
    ElevenLabs TTS (text-to-speech) → audio
                ↓
    Return: transcript + audio_base64 + bubble_state
                ↓
        Frontend plays audio automatically
```

---

## Technology Stack

### Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.3.1 | UI framework |
| **TypeScript** | 5.8.3 | Type safety |
| **Vite** | 5.4.19 | Build tool & dev server |
| **TanStack Query** | 5.83.0 | Server state management |
| **React Router** | 6.30.1 | Client-side routing |
| **Framer Motion** | 12.23.24 | Animations & transitions |
| **Radix UI** | Various | Accessible component primitives |
| **Tailwind CSS** | 3.4.17 | Utility-first styling |
| **shadcn/ui** | Latest | Pre-built component library |
| **Recharts** | 2.15.4 | Data visualization charts |
| **Lucide React** | 0.462.0 | Icon library |
| **Zod** | 3.25.76 | Schema validation |

### Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | 0.115.5 | Modern Python web framework |
| **Uvicorn** | 0.32.1 | ASGI server |
| **Python** | 3.9+ | Programming language |
| **Pydantic** | 2.10.3 | Data validation |
| **OpenAI SDK** | 1.55.3 | GPT-4 integration |
| **ElevenLabs SDK** | 1.11.0 | Voice AI (STT/TTS) |
| **python-dotenv** | 1.0.1 | Environment management |
| **httpx** | 0.27.2 | Async HTTP client |

### External APIs & Services

| Service | Purpose | Documentation |
|---------|---------|---------------|
| **OpenAI GPT-4** | Conversational AI responses | [OpenAI Docs](https://platform.openai.com/docs) |
| **ElevenLabs** | Speech-to-text & text-to-speech | [ElevenLabs Docs](https://elevenlabs.io/docs) |

---

## Setup & Installation

### Prerequisites

Before setting up the project, ensure you have:

- **Python 3.9 or higher** - [Download](https://www.python.org/downloads/)
- **Node.js 18+ and npm** - [Download](https://nodejs.org/)
- **OpenAI API Key** - [Get Key](https://platform.openai.com/api-keys)
  - Requires GPT-4 access on your account
  - Minimum credit balance recommended: $5
- **ElevenLabs API Key** - [Get Key](https://elevenlabs.io/)
  - Free tier available (10,000 characters/month)
- **Git** - For cloning the repository

### Backend Setup

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd Bubbler
```

#### 2. Create Python Virtual Environment

**macOS/Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

#### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- OpenAI SDK
- ElevenLabs SDK
- Pydantic (data validation)
- python-dotenv (environment variables)
- httpx (async HTTP)

#### 4. Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
# From backend directory
cat > .env << EOF
OPENAI_API_KEY=sk-your-openai-key-here
ELEVENLABS_API_KEY=your-elevenlabs-key-here
EOF
```

Or manually create `.env`:

```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
ELEVENLABS_API_KEY=xxxxxxxxxxxxxxxxxxxxx
```

**Important Security Notes:**
- Never commit `.env` to version control
- Keep API keys confidential
- Rotate keys if accidentally exposed

#### 5. Verify Backend Installation

```bash
# Should show installed packages
pip list | grep -E "fastapi|openai|elevenlabs"

# Test import
python -c "import fastapi, openai, elevenlabs; print('✓ All imports successful')"
```

### Frontend Setup

#### 1. Navigate to Frontend Directory

```bash
cd ../frontend/bubble-advisor
```

#### 2. Install Node Dependencies

```bash
npm install
```

This installs:
- React & React DOM
- TypeScript
- Vite
- TanStack Query
- Radix UI components
- Tailwind CSS
- Framer Motion
- All other dependencies from `package.json`

**Note:** Installation may take 2-5 minutes depending on your internet connection.

#### 3. Configure Frontend Environment

Create `.env` file in `frontend/bubble-advisor`:

```bash
# From frontend/bubble-advisor directory
cat > .env << EOF
VITE_API_URL=http://localhost:8000
EOF
```

Or manually create `.env`:

```env
VITE_API_URL=http://localhost:8000
```

**For Production Deployment:**
Update `VITE_API_URL` to your production backend URL.

#### 4. Verify Frontend Installation

```bash
# Check if node_modules exists
ls node_modules | wc -l  # Should show 1000+ packages

# Test Vite
npx vite --version
```

### Running the Application

#### Start Backend Server (Terminal 1)

```bash
# From backend directory
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py
```

Expected output:
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Backend will be available at:** `http://localhost:8000`

**API Documentation (Swagger):** `http://localhost:8000/docs`

#### Start Frontend Server (Terminal 2)

```bash
# From frontend/bubble-advisor directory
npm run dev
```

Expected output:
```
  VITE v5.4.19  ready in 500 ms

  ➜  Local:   http://localhost:8080/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**Frontend will be available at:** `http://localhost:8080`

#### Verify Integration

1. **Health Check**: Visit `http://localhost:8000/api/health`
   - Should return: `{"status": "healthy", "openai": "connected", "elevenlabs": "connected"}`

2. **Frontend**: Open `http://localhost:8080`
   - Should see landing page with two bubbles

3. **Test Market Consensus**:
   - Click "Market Consensus" bubble
   - Should see risk score and bubble visualization
   - Check that backend personality description appears

4. **Test User Analysis**:
   - Click "Your Analysis" bubble
   - Adjust sliders → bubble should update
   - Expand categories → see individual factors

5. **Test Voice Agent**:
   - Click microphone icon
   - Allow microphone permissions
   - Speak a question (e.g., "What's your current state?")
   - Wait for processing
   - Should receive audio response with transcript

---

## API Documentation

### Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

All endpoints are prefixed with `/api`.

### Authentication

Currently, no authentication is required. For production deployment, implement:
- API key authentication
- JWT tokens
- Rate limiting

### Endpoints

#### 1. Health Check

**GET** `/api/health`

Check server status and service availability.

**Response:**
```json
{
  "status": "healthy",
  "openai": "connected",
  "elevenlabs": "connected"
}
```

**Status Codes:**
- `200 OK` - All services operational
- `500 Internal Server Error` - Service unavailable

---

#### 2. Initialize Bubble

**POST** `/api/initialize`

Initialize or update a bubble's state with economic metrics.

**Request Body:**
```json
{
  "bubble_id": "personal_user",
  "categories": [
    {
      "id": "valuation",
      "name": "Market Valuation",
      "userWeight": 50,
      "marketWeight": 50,
      "indexes": [
        {
          "id": "pe-ratio",
          "name": "AI Stock P/E Ratio",
          "value": 85,
          "userValue": 90,
          "marketWeight": 12.5
        }
      ]
    }
  ]
}
```

**Parameters:**
- `bubble_id` (string, required): Unique identifier ("market" or "personal_user")
- `categories` (array, required): Economic categories with metrics

**Response:**
```json
{
  "bubble_id": "personal_user",
  "risk_score": 72.5,
  "risk_level": "high",
  "personality_description": "I'm feeling shaky and fragile right now...",
  "metrics_summary": "Current risk factors indicate elevated bubble conditions",
  "categories": [...]
}
```

**Status Codes:**
- `200 OK` - Successfully initialized
- `400 Bad Request` - Invalid metrics format
- `500 Internal Server Error` - Processing error

---

#### 3. Get Bubble Status

**GET** `/api/bubble-status/{bubble_id}`

Retrieve current bubble state.

**Path Parameters:**
- `bubble_id` (string): "market" or "personal_user"

**Response:**
```json
{
  "bubble_id": "market",
  "risk_score": 65.3,
  "risk_level": "medium",
  "personality_description": "I'm feeling uncertain and anxious...",
  "metrics_summary": "Mixed signals across categories",
  "categories": [...]
}
```

**Status Codes:**
- `200 OK` - Bubble found
- `404 Not Found` - Bubble not initialized
- `500 Internal Server Error` - Server error

---

#### 4. Voice Chat

**POST** `/api/chat/voice`

Conversational endpoint with voice input/output.

**Request Body:**
```json
{
  "audio_base64": "base64_encoded_audio_data_here",
  "bubble_id": "personal_user",
  "conversation_id": "optional_uuid"
}
```

**Parameters:**
- `audio_base64` (string, required): Base64-encoded audio (WAV/MP3)
- `bubble_id` (string, required): Which bubble to converse with
- `conversation_id` (string, optional): For maintaining context

**Response:**
```json
{
  "audio_base64": "base64_encoded_response_audio",
  "transcript_user": "What's your current risk level?",
  "transcript_agent": "I'm feeling quite nervous right now. My risk score is at 68...",
  "bubble_state": {
    "risk_score": 68.2,
    "risk_level": "high",
    "personality_description": "Panicked and fragile",
    "metrics_summary": "Warning: High bubble risk detected"
  },
  "conversation_id": "uuid-for-this-conversation"
}
```

**Audio Format:**
- **Input**: WAV, MP3, or WEBM (browser MediaRecorder output)
- **Output**: MP3 (base64-encoded)
- **Max Size**: 25MB per request

**Status Codes:**
- `200 OK` - Successful conversation
- `400 Bad Request` - Invalid audio or missing bubble
- `404 Not Found` - Bubble not initialized
- `500 Internal Server Error` - OpenAI/ElevenLabs error

**Error Response:**
```json
{
  "detail": "Bubble 'personal_user' not initialized. Call /api/initialize first."
}
```

---

### Rate Limiting

**Recommended Limits** (implement in production):
- `/api/health`: 60 requests/minute
- `/api/initialize`: 10 requests/minute
- `/api/bubble-status`: 30 requests/minute
- `/api/chat/voice`: 5 requests/minute (due to API costs)

---

## Project Structure

```
Bubbler/
├── backend/                          # FastAPI Backend
│   ├── main.py                      # FastAPI app & endpoint definitions
│   ├── config.py                    # Configuration (CORS, API settings)
│   ├── requirements.txt             # Python dependencies
│   ├── .env                         # Environment variables (API keys)
│   ├── models/                      # Pydantic data models
│   │   ├── __init__.py
│   │   └── schemas.py               # Request/response schemas
│   ├── services/                    # Business logic services
│   │   ├── __init__.py
│   │   ├── bubble_agent.py          # Bubble risk calculation & personality
│   │   ├── openai_service.py        # OpenAI GPT-4 integration
│   │   └── elevenlabs_service.py    # ElevenLabs voice AI integration
│   ├── utils/                       # Helper utilities
│   │   ├── __init__.py
│   │   └── prompt_builder.py        # AI prompt construction
│   └── data/                        # Data persistence (JSON files)
│       ├── market_bubble.json       # Market consensus bubble state
│       └── personal_user_bubble.json # User custom bubble state
│
├── frontend/                         # React Frontend
│   └── bubble-advisor/
│       ├── package.json             # npm dependencies
│       ├── vite.config.ts           # Vite configuration
│       ├── tsconfig.json            # TypeScript config
│       ├── tailwind.config.ts       # Tailwind CSS config
│       ├── .env                     # Frontend environment variables
│       ├── index.html               # HTML entry point
│       ├── public/                  # Static assets
│       └── src/
│           ├── main.tsx             # App entry point
│           ├── App.tsx              # Root component with routing
│           ├── index.css            # Global styles
│           │
│           ├── api/                 # Backend API integration
│           │   └── client.ts        # API client with all endpoints
│           │
│           ├── components/          # React components
│           │   ├── ui/              # shadcn/ui components
│           │   ├── BubbleVisualization.tsx  # 3D bubble rendering
│           │   ├── CategoryControls.tsx     # Metric sliders
│           │   ├── VoiceAgent.tsx           # Voice chat interface
│           │   └── BubbleTrendChart.tsx     # Historical trend chart
│           │
│           ├── hooks/               # Custom React hooks
│           │   ├── useBubbleState.ts        # Bubble state management
│           │   └── useVoiceAgent.ts         # Voice recording/playback
│           │
│           ├── pages/               # Page components
│           │   ├── Index.tsx        # Landing page
│           │   ├── MarketConsensus.tsx      # Market analysis page
│           │   └── UserAnalysis.tsx         # User custom page
│           │
│           ├── types/               # TypeScript types
│           │   ├── bubble.ts        # Bubble data models
│           │   └── api.ts           # API request/response types
│           │
│           └── utils/               # Utility functions
│               └── dataMapper.ts    # Frontend ↔ Backend data mapping
│
├── venv/                            # Python virtual environment (gitignored)
├── .git/                            # Git repository
├── .gitignore                       # Git ignore rules
├── README.md                        # This file
└── INTEGRATION_README.md            # Integration guide
```

---

## Technical Details

### Bubble Risk Calculation Algorithm

The bubble risk score (0-100) is calculated using a weighted average across 5 economic categories:

```python
risk_score = Σ (category_score × category_weight / 100) / num_categories

where:
  category_score = Σ (index_value × index_weight) / Σ (index_weight)
  category_weight = user-defined importance (0-100)
  index_value = economic indicator value (0-100)
```

**Categories and Weights:**

1. **Market Valuation (Weight: 20%)**
   - P/E Ratios
   - Price-to-Sales Multiples
   - Market Cap / GDP
   - Growth Premium

2. **Sentiment & Hype (Weight: 15%)**
   - Media Mentions
   - Social Media Sentiment
   - Search Trends
   - Analyst Ratings
   - IPO Activity

3. **Positioning & Flows (Weight: 25%)**
   - Fund Flows
   - Institutional Holdings
   - Retail Interest
   - Options Volume

4. **Macro & Liquidity (Weight: 20%)**
   - Interest Rates
   - Market Liquidity (M2)
   - VIX (Fear Index)
   - Put/Call Ratio

5. **AI Fundamentals (Weight: 20%)**
   - Revenue Growth
   - Profit Margins
   - CapEx Cycle
   - Enterprise Adoption
   - Competitive Intensity

### Personality State Machine

The bubble's personality adapts based on risk score:

| Risk Score | Risk Level | Personality Traits | Voice Tone |
|-----------|------------|-------------------|------------|
| 0-33 | LOW | Confident, euphoric, inflated, dismissive of concerns | Upbeat, energetic |
| 34-66 | MEDIUM | Anxious, uncertain, wobbly, acknowledging risks | Nervous, wavering |
| 67-100 | HIGH | Panicked, fragile, about to pop, desperate | Stressed, fearful |

**AI Prompt Engineering:**

The system constructs dynamic prompts for GPT-4:

```
You are a personification of the AI economic bubble.

Current State:
- Risk Score: {risk_score}/100 ({risk_level})
- Personality: {personality_description}

Economic Metrics:
{metrics_summary}

Your personality reflects your current state. Respond to the user's question
while embodying your emotional state. Be conversational and engaging.

Conversation History:
{previous_messages}

User: {user_message}
Assistant:
```

### Data Persistence

**Backend Storage:**
- JSON files in `backend/data/`
- Each bubble (market, personal_user) has its own file
- Auto-saves on every state update
- Enables server restart without data loss

**Frontend Storage:**
- localStorage for user preferences
- Key: `userCategories`
- Persists user-adjusted weights and values
- Restores on page reload

### Voice Processing Pipeline

**Speech-to-Text (STT):**
1. Browser captures audio via MediaRecorder API
2. Audio → Blob → Base64 encoding
3. POST to backend with base64 string
4. Backend decodes → ElevenLabs STT API
5. Returns transcript text

**Text-to-Speech (TTS):**
1. GPT-4 generates text response
2. Text → ElevenLabs TTS API
3. Receives audio stream
4. Audio → Base64 encoding
5. Returns to frontend
6. Frontend decodes → plays via Audio API

### Error Handling Strategy

**Backend:**
- Try-catch blocks around external API calls
- Graceful fallbacks when services unavailable
- Detailed error logging
- User-friendly error messages

**Frontend:**
- TanStack Query automatic retries
- Loading states during API calls
- Toast notifications for errors
- Fallback to local calculations if backend offline

### Security Considerations

**Current Implementation:**
- CORS restricted to frontend origin
- Environment variables for API keys
- No authentication (development only)

**Production Recommendations:**
- Implement JWT authentication
- Add rate limiting (per IP/user)
- Use HTTPS for all endpoints
- Sanitize user inputs
- Add API key rotation
- Monitor API usage costs
- Implement request logging
- Add CSRF protection

---

## Data Model

### Category Structure

```typescript
interface Category {
  id: string;                    // Unique identifier (e.g., "valuation")
  name: string;                  // Display name (e.g., "Market Valuation")
  description: string;           // Short description
  explanation: string;           // Detailed explanation of significance
  indexes: Index[];              // Array of economic indicators
  userWeight: number;            // User-defined importance (0-100)
  marketWeight: number;          // Market consensus importance (0-100)
}
```

### Index Structure

```typescript
interface Index {
  id: string;                    // Unique identifier (e.g., "pe-ratio")
  name: string;                  // Display name (e.g., "P/E Ratio")
  description: string;           // Short description
  explanation: string;           // Why this metric matters
  value: number;                 // Market consensus value (0-100)
  userValue?: number;            // User custom value (0-100)
  marketWeight: number;          // Relative importance within category
}
```

### Bubble State

```typescript
interface BubbleState {
  bubble_id: string;             // "market" or "personal_user"
  risk_score: number;            // Calculated risk (0-100)
  risk_level: "low" | "medium" | "high";
  personality_description: string; // Current emotional state
  metrics_summary: string;       // Summary of key metrics
  categories: Category[];        // Full category data
}
```

---

## Testing

### Manual Testing Checklist

#### Backend Tests

```bash
# 1. Health check
curl http://localhost:8000/api/health

# 2. Initialize market bubble
curl -X POST http://localhost:8000/api/initialize \
  -H "Content-Type: application/json" \
  -d '{"bubble_id": "market", "categories": [...]}'

# 3. Get bubble status
curl http://localhost:8000/api/bubble-status/market

# 4. Test with invalid bubble ID (should return 404)
curl http://localhost:8000/api/bubble-status/nonexistent
```

#### Frontend Tests

**Visual Tests:**
- [ ] Landing page loads without errors
- [ ] Both bubbles render correctly
- [ ] Clicking bubbles navigates to correct pages
- [ ] Market Consensus displays backend risk score
- [ ] User Analysis sliders are responsive
- [ ] Bubble size changes with risk score
- [ ] Bubble color transitions smoothly
- [ ] Trend chart displays historical data

**Interaction Tests:**
- [ ] Category weight sliders update bubble
- [ ] Expanding categories shows individual indexes
- [ ] Index sliders update in real-time
- [ ] Reset button restores market defaults
- [ ] Explanations toggle on info icon click
- [ ] Voice recording starts/stops correctly
- [ ] Audio response plays automatically
- [ ] Transcripts display correctly

**Integration Tests:**
- [ ] Backend score matches frontend calculation
- [ ] Personality description appears from backend
- [ ] Risk level (LOW/MEDIUM/HIGH) is accurate
- [ ] Voice agent maintains conversation context
- [ ] localStorage persists user adjustments
- [ ] Page refresh restores user settings

### Automated Testing (Future Enhancement)

**Backend:**
```bash
# Install pytest
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

**Frontend:**
```bash
# Install testing libraries
npm install --save-dev @testing-library/react @testing-library/jest-dom vitest

# Run tests
npm run test
```

---

## Troubleshooting

### Common Issues

#### Backend won't start

**Symptom:** `ModuleNotFoundError` or `ImportError`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt

# Verify installations
pip list
```

---

**Symptom:** `OpenAI API key not found`

**Solution:**
```bash
# Check .env file exists in backend directory
cat backend/.env

# Verify key format (should start with sk-)
# Re-create .env if needed
```

---

**Symptom:** `Port 8000 already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port in main.py:
# uvicorn.run(app, host="0.0.0.0", port=8001)
```

---

#### Frontend can't connect to backend

**Symptom:** API calls fail with network errors

**Solution:**
```bash
# 1. Verify backend is running
curl http://localhost:8000/api/health

# 2. Check CORS settings in backend/config.py
# Should include: "http://localhost:8080"

# 3. Verify frontend .env
cat frontend/bubble-advisor/.env
# Should be: VITE_API_URL=http://localhost:8000

# 4. Restart frontend dev server
npm run dev
```

---

#### Voice agent not working

**Symptom:** Microphone button doesn't record or no audio response

**Solution:**

1. **Check browser permissions:**
   - Chrome: Settings → Privacy → Microphone → Allow localhost
   - Firefox: Click lock icon → Permissions → Microphone

2. **Verify API keys:**
   ```bash
   # Test OpenAI connection
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"

   # Test ElevenLabs connection
   curl https://api.elevenlabs.io/v1/voices \
     -H "xi-api-key: $ELEVENLABS_API_KEY"
   ```

3. **Check browser console for errors:**
   - Open Developer Tools (F12)
   - Look for red error messages
   - Common issues: MediaRecorder not supported, HTTPS required

4. **Verify sufficient API credits:**
   - OpenAI: https://platform.openai.com/account/usage
   - ElevenLabs: https://elevenlabs.io/subscription

---

#### Bubble not updating when sliders change

**Symptom:** Moving sliders doesn't affect bubble visualization

**Solution:**

1. **Check browser console for errors**
2. **Verify backend is receiving updates:**
   ```bash
   # Check backend logs
   # Should see POST /api/initialize requests
   ```
3. **Clear localStorage:**
   ```javascript
   // In browser console:
   localStorage.clear();
   location.reload();
   ```

---

### Performance Issues

**Symptom:** Slow API responses or high latency

**Optimization:**
- Reduce API calls by debouncing slider changes
- Implement caching for bubble state
- Use WebSocket for real-time updates (future enhancement)
- Optimize GPT-4 prompts to reduce token usage
- Consider upgrading ElevenLabs plan for faster TTS

---

### Production Deployment Checklist

Before deploying to production:

- [ ] Update `VITE_API_URL` to production backend URL
- [ ] Update `CORS_ORIGINS` in `config.py` to production frontend URL
- [ ] Enable HTTPS for both frontend and backend
- [ ] Implement authentication and authorization
- [ ] Add rate limiting to prevent abuse
- [ ] Set up monitoring and logging (e.g., Sentry)
- [ ] Configure environment variables on hosting platform
- [ ] Test all features in production environment
- [ ] Set up automatic backups for data files
- [ ] Configure CDN for frontend assets
- [ ] Implement API usage monitoring and alerting
- [ ] Review and minimize API key permissions
- [ ] Add health check monitoring

---

## License

**Hackathon Project**

This project was developed as part of a hackathon. All rights reserved.

### Third-Party Services

- **OpenAI GPT-4**: Subject to OpenAI Terms of Service
- **ElevenLabs**: Subject to ElevenLabs Terms of Service

### Dependencies

See `package.json` and `requirements.txt` for full list of open-source dependencies and their licenses.

---

## Contact & Support

For questions, issues, or feedback:

- **Project Repository**: [GitHub URL]
- **Issues**: [GitHub Issues URL]
- **Documentation**: This README + inline code comments

---

## Acknowledgments

**Built with:**
- FastAPI web framework
- React & TypeScript
- OpenAI GPT-4
- ElevenLabs Voice AI
- shadcn/ui component library
- Tailwind CSS

**Special thanks to:**
- Anthropic Claude for development assistance
- Open source community for excellent tools and libraries

---

**Version:** 1.0.0
**Last Updated:** November 2025
**Status:** ✅ Ready for Demonstration and Evaluation
