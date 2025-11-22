# Bubble Advisor - Frontend/Backend Integration Guide

## Overview

Your Bubble Advisor application now has full integration between the React frontend and FastAPI backend, including:

- ✅ Real-time bubble state synchronization
- ✅ Voice conversation with bubble personality
- ✅ Dynamic risk score calculations
- ✅ User customization with backend persistence
- ✅ Market consensus analysis

## Architecture

### Frontend (Port 8080)
- **Framework**: React 18 + TypeScript + Vite
- **State Management**: TanStack Query + localStorage
- **API Client**: `/src/api/client.ts`
- **Pages**:
  - Market Consensus (`/market-consensus`) - "market" bubble
  - User Analysis (`/user-analysis`) - "personal_user" bubble

### Backend (Port 8000)
- **Framework**: FastAPI + Uvicorn
- **Services**: OpenAI (GPT-4) + ElevenLabs (Voice)
- **Endpoints**:
  - `POST /api/initialize` - Initialize bubble with metrics
  - `GET /api/bubble-status/{id}` - Get bubble state
  - `POST /api/chat/voice` - Voice conversation

## Setup Instructions

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (if not already created)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API keys
cat > .env << EOF
OPENAI_API_KEY=your_openai_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
EOF

# Start the backend server
python main.py
```

The backend will run on `http://localhost:8000`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend/bubble-advisor

# Install dependencies
npm install

# The .env file is already created with:
# VITE_API_URL=http://localhost:8000

# Start the frontend dev server
npm run dev
```

The frontend will run on `http://localhost:8080`

### 3. Verify Integration

1. **Health Check**: Visit `http://localhost:8000/api/health` to verify backend is running
2. **Frontend**: Visit `http://localhost:8080` to see the landing page
3. **Test Flow**:
   - Click "Market Consensus" bubble → Should initialize "market" bubble
   - Click "Your Analysis" bubble → Should initialize "personal_user" bubble
   - Adjust sliders in User Analysis → Backend updates automatically
   - Click microphone icon → Record voice → Get AI response with audio

## Integration Details

### Data Flow

1. **Page Load**:
   ```
   Frontend Page → initializeBubble() → Backend /api/initialize
   Backend calculates risk score → Returns BubbleState
   Frontend displays score & personality
   ```

2. **User Adjusts Categories**:
   ```
   User moves slider → React state updates
   → useEffect triggers → initializeBubble() with new metrics
   Backend recalculates → Frontend updates visualization
   ```

3. **Voice Conversation**:
   ```
   User records audio → Base64 encoding
   → POST /api/chat/voice with audio_base64
   Backend: STT → GPT-4 Response → TTS
   → Returns transcript + audio
   Frontend plays audio & shows transcript
   ```

### Key Files Created

**Frontend:**
- `src/api/client.ts` - API client with all backend endpoints
- `src/types/api.ts` - TypeScript types matching backend schemas
- `src/utils/dataMapper.ts` - Transform frontend categories to backend metrics
- `src/hooks/useBubbleState.ts` - React Query hooks for bubble state
- `src/hooks/useVoiceAgent.ts` - Updated with real API integration
- `.env` - Environment configuration

**Backend:**
- `config.py` - Updated CORS to allow `http://localhost:8080`

### Data Mapping

Frontend categories map to backend metrics as follows:

| Frontend Category | Backend Field | Indexes Mapped |
|-------------------|---------------|----------------|
| Market Valuation | category_1_valuation | P/E, P/S, Market Cap/GDP, Growth Premium |
| Sentiment & Hype | category_2_sentiment | Media, Social, Search, Analyst Ratings |
| Positioning & Flows | category_3_positioning | Fund Flows, Institutional, Retail, Options |
| Macro & Liquidity | category_4_macro | Interest Rates, Liquidity, VIX, Put/Call |
| AI Fundamentals | category_5_fundamentals | Revenue Growth, Margins, CapEx, Adoption |

## Features

### 1. Dual Bubble System

- **Market Bubble** (bubble_id: "market"): Uses market consensus values
- **Personal Bubble** (bubble_id: "personal_user"): Uses user-adjusted values

### 2. Real-time Synchronization

- Frontend calculates client-side score for instant feedback
- Backend calculates authoritative score with AI personality
- Displays backend score when available, falls back to client score

### 3. Voice Agent

- Records audio via browser MediaRecorder API
- Sends to backend for Speech-to-Text (ElevenLabs)
- GPT-4 generates personality-driven response
- Text-to-Speech converts to audio (ElevenLabs)
- Plays audio response automatically

### 4. Error Handling

- Backend offline → Toast notification + local calculation
- API errors → User-friendly error messages
- Network issues → Graceful degradation

## Testing Checklist

- [ ] Backend server starts without errors
- [ ] Frontend dev server starts on port 8080
- [ ] `/api/health` returns healthy status
- [ ] Market Consensus page loads and displays score
- [ ] User Analysis page loads and displays score
- [ ] Adjusting sliders updates the bubble visualization
- [ ] Backend personality description appears below bubble
- [ ] Risk level (LOW/MEDIUM/HIGH) displays correctly
- [ ] Voice recording → processing → audio response works
- [ ] Conversation maintains context across multiple messages
- [ ] localStorage persists user adjustments on refresh

## Troubleshooting

### Backend won't start
```bash
# Check if API keys are set
cat backend/.env

# Verify dependencies
pip install -r backend/requirements.txt

# Check port 8000 is available
lsof -i :8000
```

### Frontend can't connect to backend
```bash
# Verify backend is running
curl http://localhost:8000/api/health

# Check CORS settings in backend/config.py
# Should be: CORS_ORIGINS = ["http://localhost:8080"]

# Check frontend .env
cat frontend/bubble-advisor/.env
# Should contain: VITE_API_URL=http://localhost:8000
```

### Voice agent not working
- Ensure OpenAI API key is valid and has GPT-4 access
- Ensure ElevenLabs API key is valid
- Check browser permissions for microphone access
- Check browser console for errors

## Next Steps

### Production Deployment

1. **Update CORS**: Change `backend/config.py` to production frontend URL
2. **Environment Variables**: Set production API keys securely
3. **Frontend Build**: Run `npm run build` in frontend
4. **Backend Deployment**: Deploy FastAPI with production WSGI server (e.g., Gunicorn)
5. **Update API URL**: Change `VITE_API_URL` to production backend URL

### Enhancements

- Add authentication/user accounts
- Persist conversation history to database
- Add more bubble personalities based on risk levels
- Export/share custom bubble configurations
- Real-time market data integration
- Historical trend analysis with backend calculations

## Support

If you encounter issues:
1. Check both backend and frontend logs
2. Verify all environment variables are set
3. Ensure API keys are valid and have sufficient credits
4. Check CORS configuration matches your setup

---

**Status**: ✅ Integration Complete

All core features are implemented and ready for testing!
