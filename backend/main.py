from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config import config
from models.schemas import (
    InitializeRequest,
    VoiceConversationRequest,
    ConversationResponse,
    HealthResponse,
    BubbleState,
    ErrorResponse
)
from services.bubble_agent import bubble_agent
from services.openai_service import openai_service
from services.elevenlabs_service import elevenlabs_service
from utils.prompt_builder import PromptBuilder

# Initialize FastAPI app
app = FastAPI(
    title="Bubble Agent API",
    description="AI Economic Bubble Agent - Voice-based conversational AI that personifies the AI bubble",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Bubble Agent API",
        "status": "online",
        "endpoints": {
            "health": "/api/health",
            "initialize": "POST /api/initialize",
            "chat": "POST /api/chat/voice",
            "status": "/api/bubble-status"
        }
    }


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    try:
        # Test service connections
        openai_status = openai_service.test_connection()
        elevenlabs_status = elevenlabs_service.test_connection()

        return HealthResponse(
            status="healthy" if all([openai_status, elevenlabs_status]) else "degraded",
            agent_initialized=bubble_agent.is_initialized(),
            services_available={
                "openai": openai_status,
                "elevenlabs": elevenlabs_status
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/initialize", response_model=BubbleState, tags=["Agent"])
async def initialize_agent(request: InitializeRequest):
    """
    Initialize the bubble agent with economic metrics.
    This should be called by the data collection service when new metrics are available.
    """
    try:
        bubble_state = bubble_agent.initialize_with_metrics(request.metrics)
        return bubble_state
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize agent: {str(e)}")


@app.get("/api/bubble-status", response_model=BubbleState, tags=["Agent"])
async def get_bubble_status():
    """Get current bubble risk level and personality state"""
    if not bubble_agent.is_initialized():
        raise HTTPException(
            status_code=400,
            detail="Agent not initialized. Please call /api/initialize first."
        )

    state = bubble_agent.get_current_state()
    return state


@app.post("/api/chat/voice", response_model=ConversationResponse, tags=["Conversation"])
async def voice_conversation(request: VoiceConversationRequest):
    """
    Main conversation endpoint for voice interaction.

    Flow:
    1. Receives base64 encoded audio from user
    2. Converts speech to text (STT)
    3. Generates response using OpenAI with bubble personality
    4. Converts response to speech (TTS)
    5. Returns audio response + metadata
    """
    try:
        # Check if agent is initialized
        if not bubble_agent.is_initialized():
            raise HTTPException(
                status_code=400,
                detail="Agent not initialized. Please call /api/initialize with metrics first."
            )

        # Step 1: Speech to Text
        try:
            user_text = elevenlabs_service.speech_to_text(request.audio_base64)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Speech-to-text failed: {str(e)}"
            )

        # Step 2: Generate system prompt based on current bubble state
        bubble_state = bubble_agent.get_current_state()
        system_prompt = PromptBuilder.build_system_prompt(bubble_state)

        # Step 3: Generate AI response
        try:
            agent_text, conversation_id = openai_service.generate_response(
                user_message=user_text,
                system_prompt=system_prompt,
                conversation_id=request.conversation_id
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"AI response generation failed: {str(e)}"
            )

        # Step 4: Text to Speech
        try:
            response_audio = elevenlabs_service.text_to_speech(agent_text)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Text-to-speech failed: {str(e)}"
            )

        # Step 5: Return response
        return ConversationResponse(
            audio_base64=response_audio,
            transcript_user=user_text,
            transcript_agent=agent_text,
            bubble_state=bubble_state,
            conversation_id=conversation_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if config.DEBUG else None
        ).dict()
    )


if __name__ == "__main__":
    # Validate configuration on startup
    try:
        config.validate()
        print("✓ Configuration validated")
        print(f"✓ Starting Bubble Agent API on http://localhost:8000")
        print(f"✓ API docs available at http://localhost:8000/docs")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("Please check your .env file and ensure all required API keys are set.")
        exit(1)

    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG
    )
