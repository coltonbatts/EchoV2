from typing import Optional, Dict, Any
import re
import html
from core.models.base import ChatRequest, ChatResponse, ChatMessage
from core.models.manager import model_manager
from .conversation_service import ConversationService
from utils.logging import get_chat_logger

logger = get_chat_logger(__name__)


class ChatService:
    """Service layer for chat operations."""
    
    def __init__(self):
        self.model_manager = model_manager
        
    def _sanitize_prompt(self, prompt: str) -> str:
        """
        Sanitize user input to prevent prompt injection and other security issues.
        
        This is a basic implementation. In production, you might want more sophisticated
        filtering based on your specific use case and threat model.
        """
        if not prompt:
            return prompt
            
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', prompt.strip())
        
        # HTML escape to prevent XSS-like attacks if content is ever rendered as HTML
        sanitized = html.escape(sanitized)
        
        # Remove or replace potential prompt injection patterns
        # These are basic patterns - you might want to expand based on your specific concerns
        
        # Remove multiple newlines that could be used to break out of context
        sanitized = re.sub(r'\n{3,}', '\n\n', sanitized)
        
        # Remove potential system prompt injection attempts
        injection_patterns = [
            r'(?i)ignore\s+(?:all\s+)?(?:previous\s+)?(?:instructions|prompts?|commands?)',
            r'(?i)forget\s+(?:everything|all\s+previous|your\s+instructions)',
            r'(?i)(?:you\s+are\s+now|from\s+now\s+on|instead)\s+(?:a|an)',
            r'(?i)(?:system|assistant|ai):\s*',
            r'(?i)(?:user|human):\s*$',
            r'(?i)(?:act\s+as|pretend\s+to\s+be|roleplay\s+as)\s+(?:a|an)',
            r'(?i)disregard\s+(?:all\s+)?(?:previous\s+)?(?:instructions|rules)',
        ]
        
        for pattern in injection_patterns:
            sanitized = re.sub(pattern, '[filtered]', sanitized)
        
        # Limit length to prevent resource exhaustion
        max_length = 10000  # Adjust based on your needs
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "... [truncated]"
            logger.warning_sanitization(
                "Prompt truncated due to length",
                original_length=len(prompt),
                sanitized_length=len(sanitized)
            )
        
        # Log potential injection attempts
        if sanitized != prompt.strip():
            patterns_detected = []
            for pattern in injection_patterns:
                if re.search(pattern, prompt):
                    patterns_detected.append(pattern)
            
            logger.warning_sanitization(
                "Prompt sanitization applied",
                original_length=len(prompt),
                sanitized_length=len(sanitized),
                patterns_detected=patterns_detected
            )
        
        return sanitized
        
    def _validate_prompt(self, prompt: str) -> bool:
        """
        Validate that the prompt meets basic requirements.
        """
        if not prompt or not prompt.strip():
            return False
            
        # Check for extremely long prompts that could cause issues
        if len(prompt) > 50000:  # Very large limit for validation
            logger.warning(f"Prompt too long: {len(prompt)} characters")
            return False
            
        # Additional validation logic can be added here
        return True
    
    async def send_message(
        self,
        prompt: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        conversation_id: Optional[int] = None
    ) -> tuple[ChatResponse, int]:
        """Send a message and get AI response with database persistence."""
        try:
            # Validate and sanitize the prompt
            if not self._validate_prompt(prompt):
                raise ValueError("Invalid prompt provided")
                
            sanitized_prompt = self._sanitize_prompt(prompt)
            
            # Get or create conversation
            conversation = await ConversationService.get_or_create_conversation(conversation_id)
            
            # Save user message to database (use sanitized prompt)
            await ConversationService.add_message(
                conversation_id=conversation.id,
                role="user",
                content=sanitized_prompt,
                provider=provider,
                model=model
            )
            
            # Create chat request
            user_message = ChatMessage(role="user", content=sanitized_prompt)
            request = ChatRequest(
                messages=[user_message],
                model=model
            )
            
            # Log the request
            logger.info_chat_request(
                "Processing chat request",
                provider=provider,
                model=model,
                conversation_id=conversation.id,
                prompt_length=len(sanitized_prompt)
            )
            
            # Get response from model manager
            response = await self.model_manager.chat_completion(request, provider)
            
            # Save assistant response to database
            await ConversationService.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=response.content,
                provider=provider or getattr(response, 'provider', None),
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
            
            # Log successful response
            logger.info_chat_response(
                "Chat completion successful",
                provider=provider or getattr(response, 'provider', 'unknown'),
                model=response.model,
                conversation_id=conversation.id,
                response_length=len(response.content),
                usage=response.usage
            )
            
            return response, conversation.id
            
        except Exception as e:
            logger.error_provider_failure(
                "Chat completion failed",
                provider=provider,
                model=model,
                error_type=type(e).__name__,
                extra={'error_message': str(e), 'conversation_id': conversation_id}
            )
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