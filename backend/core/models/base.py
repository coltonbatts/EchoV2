from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import inspect


class AIModelType(str, Enum):
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    EMBEDDING = "embedding"
    CODE_GENERATION = "code_generation"
    IMAGE_GENERATION = "image_generation"
    MULTIMODAL = "multimodal"


class PluginCapability(str, Enum):
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    EMBEDDINGS = "embeddings"
    FINE_TUNING = "fine_tuning"
    BATCH_PROCESSING = "batch_processing"


class PluginMetadata(BaseModel):
    name: str
    version: str
    description: str
    author: str
    capabilities: List[PluginCapability] = []
    supported_model_types: List[AIModelType] = []
    dependencies: List[str] = []
    min_python_version: str = "3.8"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    stream: bool = False
    stop: Optional[Union[str, List[str]]] = None
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[Union[str, Dict[str, Any]]] = None


class StreamingChunk(BaseModel):
    content: str
    is_final: bool = False
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    function_call: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None


class ProviderStatus(BaseModel):
    available: bool
    models: List[str]
    capabilities: List[PluginCapability] = []
    error: Optional[str] = None
    last_check: Optional[datetime] = None
    response_time_ms: Optional[float] = None


class AbstractAIProvider(ABC):
    """Abstract base class for AI model providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__.lower().replace("provider", "")
        self._metadata: Optional[PluginMetadata] = None
        self._initialized = False
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider. Called once during startup."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the provider. Called during graceful shutdown."""
        pass
    
    @abstractmethod
    async def reload(self, new_config: Dict[str, Any]) -> None:
        """Reload the provider with new configuration."""
        pass
    
    @abstractmethod
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Generate a chat completion response."""
        pass
    
    @abstractmethod
    async def chat_completion_stream(self, request: ChatRequest) -> AsyncGenerator[StreamingChunk, None]:
        """Generate a streaming chat completion response."""
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
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate the provided configuration."""
        pass
    
    def get_provider_name(self) -> str:
        """Return the name of this provider."""
        return self.name
    
    def get_capabilities(self) -> List[PluginCapability]:
        """Return the capabilities of this provider."""
        return self.metadata.capabilities
    
    def supports_streaming(self) -> bool:
        """Return whether this provider supports streaming responses."""
        return PluginCapability.STREAMING in self.get_capabilities()
    
    def supports_function_calling(self) -> bool:
        """Return whether this provider supports function calling."""
        return PluginCapability.FUNCTION_CALLING in self.get_capabilities()
    
    def supports_vision(self) -> bool:
        """Return whether this provider supports vision/image understanding."""
        return PluginCapability.VISION in self.get_capabilities()
    
    async def _ensure_initialized(self) -> None:
        """Ensure the provider is initialized."""
        if not self._initialized:
            await self.initialize()
            self._initialized = True
    
    def get_config_schema(self) -> Optional[Dict[str, Any]]:
        """Return the configuration schema for this provider."""
        return None
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Return information about a specific model."""
        return None