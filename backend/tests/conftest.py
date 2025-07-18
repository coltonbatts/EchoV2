import pytest
import asyncio
import tempfile
import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import sys
sys.path.append('.')

from core.models.base import ChatRequest, ChatResponse, ChatMessage
from core.models.manager import ModelManager
from services.chat_service import ChatService
from services.conversation_service import ConversationService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_model_manager():
    """Mock model manager for testing."""
    manager = MagicMock(spec=ModelManager)
    manager.chat_completion = AsyncMock()
    manager.list_providers = MagicMock(return_value=["openai", "anthropic", "ollama"])
    manager.get_provider_models = MagicMock(return_value=["gpt-3.5-turbo", "gpt-4"])
    manager.get_default_provider = MagicMock(return_value="openai")
    return manager


@pytest.fixture
def mock_conversation_service():
    """Mock conversation service for testing."""
    service = MagicMock(spec=ConversationService)
    service.get_or_create_conversation = AsyncMock()
    service.add_message = AsyncMock()
    service.generate_conversation_title = AsyncMock(return_value="Test Conversation")
    service.update_conversation_title = AsyncMock()
    return service


@pytest.fixture
def chat_service(mock_model_manager):
    """Create a chat service instance with mocked dependencies."""
    service = ChatService()
    service.model_manager = mock_model_manager
    return service


@pytest.fixture
def sample_chat_request():
    """Sample chat request for testing."""
    return ChatRequest(
        messages=[ChatMessage(role="user", content="Hello, how are you?")],
        model="gpt-3.5-turbo"
    )


@pytest.fixture
def sample_chat_response():
    """Sample chat response for testing."""
    return ChatResponse(
        content="I'm doing well, thank you!",
        model="gpt-3.5-turbo",
        usage={"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18}
    )


@pytest.fixture
def mock_conversation():
    """Mock conversation object."""
    conversation = MagicMock()
    conversation.id = 1
    conversation.title = None
    return conversation


@pytest.fixture
async def temp_database():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    # Set environment variable for test database
    original_db = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    
    try:
        yield db_path
    finally:
        # Cleanup
        if original_db:
            os.environ["DATABASE_URL"] = original_db
        else:
            os.environ.pop("DATABASE_URL", None)
        
        try:
            os.unlink(db_path)
        except FileNotFoundError:
            pass