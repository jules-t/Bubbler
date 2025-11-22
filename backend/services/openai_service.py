from openai import OpenAI
from config import config
from typing import List, Dict
import uuid


class OpenAIService:
    """Service for OpenAI chat completions"""

    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL
        self.temperature = config.OPENAI_TEMPERATURE
        self.max_tokens = config.OPENAI_MAX_TOKENS

        # Store conversation history by conversation_id
        self.conversations: Dict[str, List[Dict[str, str]]] = {}

    def generate_response(
        self,
        user_message: str,
        system_prompt: str,
        conversation_id: str | None = None
    ) -> tuple[str, str]:
        """
        Generate a response using OpenAI chat completion.

        Args:
            user_message: The user's message
            system_prompt: System prompt defining agent personality and context
            conversation_id: Optional ID to maintain conversation context

        Returns:
            Tuple of (agent_response, conversation_id)
        """
        try:
            # Create or retrieve conversation
            if conversation_id is None:
                conversation_id = str(uuid.uuid4())
                self.conversations[conversation_id] = []

            # Get conversation history
            messages = [{"role": "system", "content": system_prompt}]

            if conversation_id in self.conversations:
                messages.extend(self.conversations[conversation_id])

            # Add current user message
            messages.append({"role": "user", "content": user_message})

            # Generate completion
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            agent_response = response.choices[0].message.content

            # Update conversation history
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []

            self.conversations[conversation_id].append({
                "role": "user",
                "content": user_message
            })
            self.conversations[conversation_id].append({
                "role": "assistant",
                "content": agent_response
            })

            # Keep only last 10 exchanges to prevent context overflow
            if len(self.conversations[conversation_id]) > 20:
                self.conversations[conversation_id] = self.conversations[conversation_id][-20:]

            return agent_response, conversation_id

        except Exception as e:
            raise Exception(f"OpenAI completion failed: {str(e)}")

    def clear_conversation(self, conversation_id: str):
        """Clear conversation history for a given ID"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]

    def test_connection(self) -> bool:
        """Test if OpenAI API is accessible"""
        try:
            # Make a simple completion to test connection
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception:
            return False


# Global service instance
openai_service = OpenAIService()
