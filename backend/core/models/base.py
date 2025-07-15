from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from enum import Enum


class AIModelType(str, Enum):
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    EMBEDDING = "embedding"
    CODE_GENERATION = "code_generation"


class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: bool = False


class ChatResponse(BaseModel):
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class ProviderStatus(BaseModel):
    available: bool
    models: List[str]
    error: Optional[str] = None


class AbstractAIProvider(ABC):
    """Abstract base class for AI model providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__.lower().replace("provider", "")
    
    @abstractmethod
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Generate a chat completion response."""
        pass
    
    @abstractmethod
    async def health_check(self) -> ProviderStatus:
        """Check if the provider is healthy and return available models."""
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """Return list of supported models."""
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Return the default model for this provider."""
        pass
    
    def get_provider_name(self) -> str:
        """Return the name of this provider."""
        return self.name
    
    def supports_streaming(self) -> bool:
        """Return whether this provider supports streaming responses."""
        return False