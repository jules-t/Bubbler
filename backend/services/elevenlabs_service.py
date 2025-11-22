import base64
import io
from elevenlabs import ElevenLabs
from config import config


class ElevenLabsService:
    """Service for speech-to-text and text-to-speech using ElevenLabs API"""

    def __init__(self):
        self.client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
        self.voice_id = config.ELEVENLABS_VOICE_ID
        self.model_id = config.ELEVENLABS_MODEL_ID

    def speech_to_text(self, audio_base64: str) -> str:
        """
        Convert audio (base64 encoded) to text using ElevenLabs STT.

        Args:
            audio_base64: Base64 encoded audio data

        Returns:
            Transcribed text
        """
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_base64)

            # Create a file-like object from bytes
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.mp3"  # ElevenLabs needs a filename

            # Use ElevenLabs speech-to-text
            # Note: ElevenLabs STT API might differ - adjust based on their docs
            # This is a placeholder for the actual implementation
            result = self.client.speech_to_text.convert(audio=audio_file)

            return result.text if hasattr(result, 'text') else str(result)

        except Exception as e:
            raise Exception(f"Speech-to-text conversion failed: {str(e)}")

    def text_to_speech(self, text: str) -> str:
        """
        Convert text to speech using ElevenLabs TTS.

        Args:
            text: Text to convert to speech

        Returns:
            Base64 encoded audio data
        """
        try:
            # Generate audio using ElevenLabs
            audio_generator = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id=self.model_id,
                output_format="mp3_44100_128"
            )

            # Collect audio chunks
            audio_bytes = b""
            for chunk in audio_generator:
                if chunk:
                    audio_bytes += chunk

            # Encode to base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

            return audio_base64

        except Exception as e:
            raise Exception(f"Text-to-speech conversion failed: {str(e)}")

    def test_connection(self) -> bool:
        """Test if ElevenLabs API is accessible"""
        try:
            # Try to get voices to test connection
            self.client.voices.get_all()
            return True
        except Exception:
            return False


# Global service instance
elevenlabs_service = ElevenLabsService()
