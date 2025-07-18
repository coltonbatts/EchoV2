import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import json
import sys
sys.path.append('.')

from main import create_app
from core.models.base import ChatResponse


@pytest.fixture
def test_app():
    """Create test FastAPI application."""
    return create_app()


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture
def mock_chat_service():
    """Mock chat service for API testing."""
    service = MagicMock()
    service.send_message = AsyncMock()
    service.list_available_providers = MagicMock(return_value=["openai", "anthropic"])
    service.get_provider_models = MagicMock(return_value=["gpt-3.5-turbo", "gpt-4"])
    service.get_default_provider = MagicMock(return_value="openai")
    return service


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check_success(self, client):
        """Test successful health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestChatEndpoint:
    """Test chat endpoints."""
    
    @patch('api.routes.chat.chat_service')
    def test_send_message_success(self, mock_service, client):
        """Test successful message sending via API."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.content = "Hello! How can I help you?"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.metadata = {"usage": {"prompt_tokens": 5, "completion_tokens": 8, "total_tokens": 13}}
        mock_service.send_message = AsyncMock(return_value=(mock_response, 123))
        
        # Make request
        payload = {
            "prompt": "Hello",
            "model": "gpt-3.5-turbo",
            "provider": "openai"
        }
        
        response = client.post("/chat", json=payload)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Hello! How can I help you?"
        assert data["model"] == "gpt-3.5-turbo"
        assert data["provider"] == "openai"
        assert data["conversation_id"] == 123
        assert data["metadata"] is not None
        
        # Verify service was called correctly
        mock_service.send_message.assert_called_once_with(
            prompt="Hello",
            model="gpt-3.5-turbo", 
            provider="openai",
            conversation_id=None
        )
    
    @patch('api.routes.chat.chat_service')
    def test_send_message_with_conversation_id(self, mock_service, client):
        """Test sending message with existing conversation ID."""
        mock_response = ChatResponse(
            content="Follow-up response",
            model="gpt-4",
            provider="openai"
        )
        mock_service.send_message.return_value = (mock_response, 456)
        
        payload = {
            "prompt": "Follow-up question",
            "conversation_id": 456
        }
        
        response = client.post("/chat", json=payload)
        assert response.status_code == 200
        
        mock_service.send_message.assert_called_once_with(
            prompt="Follow-up question",
            model=None,
            provider=None,
            conversation_id=456
        )
    
    @patch('api.routes.chat.chat_service')
    def test_send_message_missing_prompt(self, mock_service, client):
        """Test API validation for missing prompt."""
        payload = {
            "model": "gpt-3.5-turbo"
        }
        
        response = client.post("/chat", json=payload)
        assert response.status_code == 422  # Validation error
    
    @patch('api.routes.chat.chat_service')
    def test_send_message_empty_prompt(self, mock_service, client):
        """Test sending empty prompt."""
        mock_response = ChatResponse(
            content="I received an empty message.",
            model="gpt-3.5-turbo",
            provider="openai"
        )
        mock_service.send_message.return_value = (mock_response, 789)
        
        payload = {"prompt": ""}
        response = client.post("/chat", json=payload)
        
        assert response.status_code == 200
        mock_service.send_message.assert_called_once()
    
    @patch('api.routes.chat.chat_service')
    def test_send_message_service_error(self, mock_service, client):
        """Test handling service errors."""
        mock_service.send_message.side_effect = Exception("AI service unavailable")
        
        payload = {"prompt": "Hello"}
        response = client.post("/chat", json=payload)
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "AI service unavailable" in data["error"]
    
    @patch('api.routes.chat.chat_service')
    def test_send_message_long_prompt(self, mock_service, client):
        """Test sending very long prompt."""
        long_prompt = "x" * 10000  # 10k characters
        
        mock_response = ChatResponse(
            content="Processed long message",
            model="gpt-3.5-turbo",
            provider="openai"
        )
        mock_service.send_message.return_value = (mock_response, 999)
        
        payload = {"prompt": long_prompt}
        response = client.post("/chat", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Processed long message"


class TestPluginsEndpoint:
    """Test plugin/provider endpoints."""
    
    @patch('api.routes.plugins.chat_service')
    def test_list_providers(self, mock_service, client):
        """Test listing available providers."""
        mock_service.list_available_providers.return_value = ["openai", "anthropic", "ollama"]
        
        response = client.get("/plugins/providers")
        
        assert response.status_code == 200
        data = response.json()
        assert data["providers"] == ["openai", "anthropic", "ollama"]
        mock_service.list_available_providers.assert_called_once()
    
    @patch('api.routes.plugins.chat_service')
    def test_get_provider_models(self, mock_service, client):
        """Test getting models for a specific provider."""
        mock_service.get_provider_models.return_value = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
        
        response = client.get("/plugins/providers/openai/models")
        
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "openai"
        assert data["models"] == ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
        mock_service.get_provider_models.assert_called_once_with("openai")
    
    @patch('api.routes.plugins.chat_service')
    def test_get_default_provider(self, mock_service, client):
        """Test getting default provider."""
        mock_service.get_default_provider.return_value = "openai"
        
        response = client.get("/plugins/default")
        
        assert response.status_code == 200
        data = response.json()
        assert data["default_provider"] == "openai"
        mock_service.get_default_provider.assert_called_once()
    
    @patch('api.routes.plugins.chat_service')
    def test_get_provider_models_invalid_provider(self, mock_service, client):
        """Test getting models for non-existent provider."""
        mock_service.get_provider_models.side_effect = ValueError("Provider not found")
        
        response = client.get("/plugins/providers/invalid/models")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data


class TestCORS:
    """Test CORS configuration."""
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses."""
        response = client.options("/health")
        
        # Should include CORS headers for preflight requests
        assert "access-control-allow-origin" in [h.lower() for h in response.headers.keys()]
    
    def test_cors_allows_frontend_origin(self, client):
        """Test that frontend origin is allowed."""
        headers = {"Origin": "http://localhost:1420"}
        response = client.get("/health", headers=headers)
        
        assert response.status_code == 200
        # The actual CORS header checking depends on FastAPI middleware configuration


class TestRequestValidation:
    """Test request validation and security."""
    
    def test_invalid_json_payload(self, client):
        """Test handling of malformed JSON."""
        response = client.post(
            "/chat", 
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_large_payload_handling(self, client):
        """Test handling of very large payloads."""
        # This would test payload size limits if configured
        large_payload = {"prompt": "x" * 1000000}  # 1MB prompt
        
        response = client.post("/chat", json=large_payload)
        # Response depends on server configuration - could be 413 (too large) or processed
        assert response.status_code in [200, 413, 422]
    
    @patch('api.routes.chat.chat_service')
    def test_special_characters_in_prompt(self, mock_service, client):
        """Test handling of special characters and potential injection attempts."""
        mock_response = ChatResponse(
            content="Processed special characters",
            model="gpt-3.5-turbo",
            provider="openai"
        )
        mock_service.send_message.return_value = (mock_response, 123)
        
        special_chars = {
            "prompt": "Hello! <script>alert('xss')</script> 你好 🚀 'quotes' \"double\" `backticks`"
        }
        
        response = client.post("/chat", json=special_chars)
        assert response.status_code == 200
        
        # Verify service received the prompt as-is
        call_args = mock_service.send_message.call_args
        assert call_args[1]["prompt"] == special_chars["prompt"]