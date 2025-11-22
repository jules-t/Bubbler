import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for API keys and settings"""

    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    VLYU_API_KEY = os.getenv("VLYU_API_KEY")

    # OpenAI Settings
    OPENAI_MODEL = "gpt-4o-mini"
    OPENAI_TEMPERATURE = 0.8  # Higher temperature for more personality
    OPENAI_MAX_TOKENS = 500

    # ElevenLabs Settings
    ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Default voice (Rachel)
    ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"

    # Application Settings
    CORS_ORIGINS = ["http://localhost:8080"]  # Frontend dev server
    DEBUG = True

    @classmethod
    def validate(cls):
        """Validate that required API keys are present"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        if not cls.ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY not found in environment variables")

config = Config()
