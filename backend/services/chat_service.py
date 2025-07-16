from typing import Optional, Dict, Any
from core.models.base import ChatRequest, ChatResponse, ChatMessage
from core.models.manager import model_manager
from .conversation_service import ConversationService
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
        conversation_id: Optional[int] = None
    ) -> tuple[ChatResponse, int]:
        """Send a message and get AI response with database persistence."""
        try:
            # Get or create conversation
            conversation = await ConversationService.get_or_create_conversation(conversation_id)
            
            # Save user message to database
            await ConversationService.add_message(
                conversation_id=conversation.id,
                role="user",
                content=prompt,
                provider=provider,
                model=model
            )
            
            # Create chat request
            user_message = ChatMessage(role="user", content=prompt)
            request = ChatRequest(
                messages=[user_message],
                model=model
            )
            
            # Get response from model manager
            response = await self.model_manager.chat_completion(request, provider)
            
            # Save assistant response to database
            await ConversationService.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=response.content,
                provider=provider or response.provider,
                model=response.model,
                message_metadata={
                    "usage": response.usage,
                    "finish_reason": response.finish_reason if hasattr(response, 'finish_reason') else None
                }
            )
            
            # Update conversation title if it's the first message
            if not conversation.title:
                title = await ConversationService.generate_conversation_title(conversation.id)
                if title:
                    await ConversationService.update_conversation_title(conversation.id, title)
            
            logger.info(f"Chat completion successful - Model: {response.model}, Provider: {provider or 'default'}, Conversation: {conversation.id}")
            return response, conversation.id
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise
    
    async def send_conversation(
        self,
        messages: list,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        conversation_id: Optional[int] = None
    ) -> tuple[ChatResponse, int]:
        """Send a conversation with multiple messages with database persistence."""
        try:
            # Get or create conversation
            conversation = await ConversationService.get_or_create_conversation(conversation_id)
            
            # Convert to ChatMessage objects and save to database if new
            chat_messages = []
            for msg in messages:
                chat_message = ChatMessage(
                    role=msg.get("role", "user"),
                    content=msg.get("content", "")
                )
                chat_messages.append(chat_message)
                
                # Save message to database (skip if it's already persisted)
                await ConversationService.add_message(
                    conversation_id=conversation.id,
                    role=chat_message.role,
                    content=chat_message.content,
                    provider=provider,
                    model=model
                )
            
            request = ChatRequest(
                messages=chat_messages,
                model=model
            )
            
            response = await self.model_manager.chat_completion(request, provider)
            
            # Save assistant response to database
            await ConversationService.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=response.content,
                provider=provider or response.provider,
                model=response.model,
                message_metadata={
                    "usage": response.usage,
                    "finish_reason": response.finish_reason if hasattr(response, 'finish_reason') else None
                }
            )
            
            # Update conversation title if it's the first message
            if not conversation.title:
                title = await ConversationService.generate_conversation_title(conversation.id)
                if title:
                    await ConversationService.update_conversation_title(conversation.id, title)
            
            logger.info(f"Conversation completion successful - Messages: {len(messages)}, Conversation: {conversation.id}")
            return response, conversation.id
            
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