import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
sys.path.append('.')

from services.chat_service import ChatService
from core.models.base import ChatRequest, ChatResponse, ChatMessage


class TestChatService:
    """Test cases for ChatService."""

    @pytest.mark.asyncio
    async def test_send_message_success(self, chat_service, mock_conversation_service, sample_chat_response, mock_conversation):
        """Test successful message sending."""
        # Setup mocks - create response with provider attribute for service compatibility
        mock_response = MagicMock()
        mock_response.content = "I'm doing well, thank you!"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.provider = "openai"
        mock_response.usage = {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18}
        chat_service.model_manager.chat_completion.return_value = mock_response
        
        with patch('services.chat_service.ConversationService', mock_conversation_service):
            mock_conversation_service.get_or_create_conversation.return_value = mock_conversation
            
            # Execute
            response, conv_id = await chat_service.send_message(
                prompt="Hello, how are you?",
                model="gpt-3.5-turbo",
                provider="openai"
            )
            
            # Assertions
            assert response.content == "I'm doing well, thank you!"
            assert response.model == "gpt-3.5-turbo"
            assert response.provider == "openai"
            assert conv_id == 1
            
            # Verify service calls
            mock_conversation_service.get_or_create_conversation.assert_called_once_with(None)
            assert mock_conversation_service.add_message.call_count == 2  # User + assistant messages
            chat_service.model_manager.chat_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_with_conversation_id(self, chat_service, mock_conversation_service, mock_conversation):
        """Test sending message with existing conversation ID."""
        mock_response = MagicMock()
        mock_response.content = "Follow-up response"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.provider = "openai"
        chat_service.model_manager.chat_completion.return_value = mock_response
        
        with patch('services.chat_service.ConversationService', mock_conversation_service):
            mock_conversation_service.get_or_create_conversation.return_value = mock_conversation
            
            response, conv_id = await chat_service.send_message(
                prompt="Follow-up question",
                conversation_id=123
            )
            
            assert conv_id == 1
            mock_conversation_service.get_or_create_conversation.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_send_message_ai_provider_error(self, chat_service, mock_conversation_service, mock_conversation):
        """Test handling AI provider errors."""
        # Setup error
        chat_service.model_manager.chat_completion.side_effect = Exception("AI provider error")
        
        with patch('services.chat_service.ConversationService', mock_conversation_service):
            mock_conversation_service.get_or_create_conversation.return_value = mock_conversation
            
            # Execute and assert
            with pytest.raises(Exception) as exc_info:
                await chat_service.send_message("Hello")
            
            assert "AI provider error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_message_database_error(self, chat_service, mock_conversation_service):
        """Test handling database errors."""
        # Setup error
        mock_conversation_service.get_or_create_conversation.side_effect = Exception("Database error")
        
        with patch('services.chat_service.ConversationService', mock_conversation_service):
            # Execute and assert
            with pytest.raises(Exception) as exc_info:
                await chat_service.send_message("Hello")
            
            assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_message_generates_title_for_new_conversation(self, chat_service, mock_conversation_service):
        """Test that conversation title is generated for new conversations."""
        # Setup
        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_conversation.title = None  # New conversation
        
        mock_response = MagicMock()
        mock_response.content = "I'm doing well, thank you!"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.provider = "openai"
        chat_service.model_manager.chat_completion.return_value = mock_response
        
        with patch('services.chat_service.ConversationService', mock_conversation_service):
            mock_conversation_service.get_or_create_conversation.return_value = mock_conversation
            mock_conversation_service.generate_conversation_title.return_value = "Generated Title"
            
            await chat_service.send_message("Hello")
            
            # Verify title generation was called
            mock_conversation_service.generate_conversation_title.assert_called_once_with(1)
            mock_conversation_service.update_conversation_title.assert_called_once_with(1, "Generated Title")

    @pytest.mark.asyncio
    async def test_send_message_skips_title_for_existing_conversation(self, chat_service, mock_conversation_service):
        """Test that title generation is skipped for existing conversations."""
        # Setup
        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_conversation.title = "Existing Title"  # Has title
        
        mock_response = MagicMock()
        mock_response.content = "I'm doing well, thank you!"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.provider = "openai"
        chat_service.model_manager.chat_completion.return_value = mock_response
        
        with patch('services.chat_service.ConversationService', mock_conversation_service):
            mock_conversation_service.get_or_create_conversation.return_value = mock_conversation
            
            await chat_service.send_message("Hello")
            
            # Verify title generation was NOT called
            mock_conversation_service.generate_conversation_title.assert_not_called()
            mock_conversation_service.update_conversation_title.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_conversation_success(self, chat_service, mock_conversation_service, mock_conversation):
        """Test successful conversation sending with multiple messages."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        mock_response = MagicMock()
        mock_response.content = "I'm doing well, thank you!"
        mock_response.model = "gpt-4"
        mock_response.provider = "openai"
        chat_service.model_manager.chat_completion.return_value = mock_response
        
        with patch('services.chat_service.ConversationService', mock_conversation_service):
            mock_conversation_service.get_or_create_conversation.return_value = mock_conversation
            
            response, conv_id = await chat_service.send_conversation(
                messages=messages,
                model="gpt-4",
                provider="openai"
            )
            
            assert response.content == "I'm doing well, thank you!"
            assert conv_id == 1
            
            # Verify all messages were saved (3 input + 1 response)
            assert mock_conversation_service.add_message.call_count == 4

    def test_list_available_providers(self, chat_service):
        """Test listing available providers."""
        providers = chat_service.list_available_providers()
        assert providers == ["openai", "anthropic", "ollama"]
        chat_service.model_manager.list_providers.assert_called_once()

    def test_get_provider_models(self, chat_service):
        """Test getting models for a provider."""
        models = chat_service.get_provider_models("openai")
        assert models == ["gpt-3.5-turbo", "gpt-4"]
        chat_service.model_manager.get_provider_models.assert_called_once_with("openai")

    def test_get_default_provider(self, chat_service):
        """Test getting default provider."""
        provider = chat_service.get_default_provider()
        assert provider == "openai"
        chat_service.model_manager.get_default_provider.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_empty_prompt(self, chat_service, mock_conversation_service, mock_conversation):
        """Test sending message with empty prompt."""
        with patch('services.chat_service.ConversationService', mock_conversation_service):
            mock_conversation_service.get_or_create_conversation.return_value = mock_conversation
            
            # Should still process empty prompts (up to AI provider to handle)
            mock_response = MagicMock()
            mock_response.content = "I received an empty message."
            mock_response.model = "gpt-3.5-turbo"
            mock_response.provider = "openai"
            chat_service.model_manager.chat_completion.return_value = mock_response
            
            response, conv_id = await chat_service.send_message("")
            assert response.content == "I received an empty message."

    @pytest.mark.asyncio
    async def test_send_message_special_characters(self, chat_service, mock_conversation_service, mock_conversation):
        """Test sending message with special characters and potential injection attempts."""
        special_prompt = "Hello! <script>alert('xss')</script> How are you? 🤔"
        
        mock_response = MagicMock()
        mock_response.content = "I received your message"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.provider = "openai"
        chat_service.model_manager.chat_completion.return_value = mock_response
        
        with patch('services.chat_service.ConversationService', mock_conversation_service):
            mock_conversation_service.get_or_create_conversation.return_value = mock_conversation
            
            response, conv_id = await chat_service.send_message(special_prompt)
            
            # Verify the prompt was passed through (sanitization should happen elsewhere)
            chat_request = chat_service.model_manager.chat_completion.call_args[0][0]
            assert chat_request.messages[0].content == special_prompt