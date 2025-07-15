from typing import Optional, Dict, Any
from ..core.models.base import ChatRequest, ChatResponse, ChatMessage
from ..core.models.manager import model_manager
import logging

logger = logging.getLogger(__name__)


class ChatService:
    """Service layer for chat operations."""
    
    def __init__(self):
        self.model_manager = model_manager
    
    async def send_message(
        self,
        prompt: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> ChatResponse:
        """Send a message and get AI response."""
        try:
            # Create chat request
            user_message = ChatMessage(role="user", content=prompt)
            request = ChatRequest(
                messages=[user_message],
                model=model
            )
            
            # Get response from model manager
            response = await self.model_manager.chat_completion(request, provider)
            
            logger.info(f"Chat completion successful - Model: {response.model}, Provider: {provider or 'default'}")
            return response
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise
    
    async def send_conversation(
        self,
        messages: list,
        model: Optional[str] = None,
        provider: Optional[str] = None
    ) -> ChatResponse:
        """Send a conversation with multiple messages."""
        try:
            # Convert to ChatMessage objects
            chat_messages = []
            for msg in messages:
                chat_messages.append(ChatMessage(
                    role=msg.get("role", "user"),
                    content=msg.get("content", "")
                ))
            
            request = ChatRequest(
                messages=chat_messages,
                model=model
            )
            
            response = await self.model_manager.chat_completion(request, provider)
            
            logger.info(f"Conversation completion successful - Messages: {len(messages)}")
            return response
            
        except Exception as e:
            logger.error(f"Conversation completion failed: {e}")
            raise
    
    def list_available_providers(self) -> list:
        """List all available AI providers."""
        return self.model_manager.list_providers()
    
    def get_provider_models(self, provider: str) -> list:
        """Get available models for a provider."""
        return self.model_manager.get_provider_models(provider)
    
    def get_default_provider(self) -> str:
        """Get the default provider name."""
        return self.model_manager.get_default_provider()


# Global service instance
chat_service = ChatService()