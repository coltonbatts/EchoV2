import anthropic
import asyncio
from typing import Dict, Any, List, AsyncGenerator, Optional
from ..models.base import (
    AbstractAIProvider, ChatRequest, ChatResponse, ProviderStatus, 
    ChatMessage, StreamingChunk, PluginMetadata, PluginCapability, AIModelType
)
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class AnthropicProvider(AbstractAIProvider):
    """Anthropic API provider implementation with streaming support."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.anthropic.com")
        self.default_model = config.get("default_model", "claude-3-sonnet-20240229")
        self.timeout = config.get("timeout", 60)
        self.max_tokens = config.get("max_tokens", 4096)
        
        self.client: Optional[anthropic.AsyncAnthropic] = None
        
        # Supported models
        self._supported_models = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229", 
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2"
        ]
    
    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="Anthropic Provider",
            version="1.0.0",
            description="Anthropic API provider with Claude models support",
            author="EchoV2 Team",
            capabilities=[
                PluginCapability.STREAMING,
                PluginCapability.VISION,  # Claude 3 models support vision
                PluginCapability.MULTIMODAL
            ],
            supported_model_types=[
                AIModelType.CHAT,
                AIModelType.TEXT_GENERATION,
                AIModelType.CODE_GENERATION,
                AIModelType.MULTIMODAL
            ],
            dependencies=["anthropic>=0.8.0"],
            min_python_version="3.8",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    async def initialize(self) -> None:
        """Initialize the Anthropic client."""
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        
        self.client = anthropic.AsyncAnthropic(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )
        
        logger.info("Anthropic provider initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown the provider."""
        if self.client:
            await self.client.close()
            self.client = None
        logger.info("Anthropic provider shutdown completed")
    
    async def reload(self, new_config: Dict[str, Any]) -> None:
        """Reload the provider with new configuration."""
        await self.shutdown()
        self.config = new_config
        self.api_key = new_config.get("api_key")
        self.base_url = new_config.get("base_url", "https://api.anthropic.com")
        self.default_model = new_config.get("default_model", "claude-3-sonnet-20240229")
        self.timeout = new_config.get("timeout", 60)
        self.max_tokens = new_config.get("max_tokens", 4096)
        await self.initialize()
        logger.info("Anthropic provider reloaded successfully")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate the provided configuration."""
        required_fields = ["api_key"]
        
        for field in required_fields:
            if field not in config or not config[field]:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate model if specified
        model = config.get("default_model")
        if model and model not in self._supported_models:
            logger.warning(f"Model {model} may not be supported")
        
        return True
    
    def _convert_messages_to_anthropic_format(self, messages: List[ChatMessage]) -> tuple[Optional[str], List[Dict[str, str]]]:
        """Convert messages to Anthropic format (system prompt separate from messages)."""
        system_prompt = None
        anthropic_messages = []
        
        for msg in messages:
            if msg.role == "system":
                # Anthropic handles system messages differently
                system_prompt = msg.content
            else:
                # Map assistant to assistant, user to user
                role = "assistant" if msg.role == "assistant" else "user"
                anthropic_messages.append({
                    "role": role,
                    "content": msg.content
                })
        
        return system_prompt, anthropic_messages
    
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Generate a chat completion response."""
        await self._ensure_initialized()
        
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")
        
        model = request.model or self.default_model
        
        # Convert messages to Anthropic format
        system_prompt, messages = self._convert_messages_to_anthropic_format(request.messages)
        
        if not messages:
            raise ValueError("At least one non-system message is required")
        
        # Build request parameters
        params = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens or self.max_tokens
        }
        
        # Add system prompt if present
        if system_prompt:
            params["system"] = system_prompt
        
        # Add optional parameters
        if request.temperature is not None:
            params["temperature"] = request.temperature
        if request.top_p is not None:
            params["top_p"] = request.top_p
        if request.stop is not None:
            # Anthropic uses "stop_sequences"
            params["stop_sequences"] = request.stop if isinstance(request.stop, list) else [request.stop]
        
        try:
            start_time = time.time()
            response = await self.client.messages.create(**params)
            end_time = time.time()
            
            # Extract content from response
            content = ""
            if response.content:
                # Claude returns content as a list of content blocks
                content = "".join([
                    block.text if hasattr(block, 'text') else str(block)
                    for block in response.content
                ])
            
            return ChatResponse(
                content=content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                    "completion_tokens": response.usage.output_tokens if response.usage else 0,
                    "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0
                },
                metadata={
                    "provider": "anthropic",
                    "response_time_ms": round((end_time - start_time) * 1000, 2),
                    "stop_reason": response.stop_reason
                },
                finish_reason=response.stop_reason
            )
            
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise Exception(f"Anthropic API error: {e}")
        except Exception as e:
            logger.error(f"Anthropic completion failed: {e}")
            raise
    
    async def chat_completion_stream(self, request: ChatRequest) -> AsyncGenerator[StreamingChunk, None]:
        """Generate a streaming chat completion response."""
        await self._ensure_initialized()
        
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")
        
        model = request.model or self.default_model
        
        # Convert messages to Anthropic format
        system_prompt, messages = self._convert_messages_to_anthropic_format(request.messages)
        
        if not messages:
            raise ValueError("At least one non-system message is required")
        
        # Build request parameters
        params = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens or self.max_tokens,
            "stream": True
        }
        
        # Add system prompt if present
        if system_prompt:
            params["system"] = system_prompt
        
        # Add optional parameters
        if request.temperature is not None:
            params["temperature"] = request.temperature
        if request.top_p is not None:
            params["top_p"] = request.top_p
        if request.stop is not None:
            params["stop_sequences"] = request.stop if isinstance(request.stop, list) else [request.stop]
        
        try:
            stream = await self.client.messages.create(**params)
            
            async for event in stream:
                if event.type == "content_block_delta":
                    if hasattr(event.delta, 'text'):
                        yield StreamingChunk(
                            content=event.delta.text,
                            is_final=False,
                            metadata={
                                "provider": "anthropic",
                                "model": model,
                                "event_type": event.type
                            }
                        )
                elif event.type == "message_stop":
                    yield StreamingChunk(
                        content="",
                        is_final=True,
                        metadata={
                            "provider": "anthropic",
                            "model": model,
                            "event_type": event.type
                        }
                    )
                    break
            
        except anthropic.APIError as e:
            logger.error(f"Anthropic streaming API error: {e}")
            raise Exception(f"Anthropic streaming API error: {e}")
        except Exception as e:
            logger.error(f"Anthropic streaming failed: {e}")
            raise
    
    async def health_check(self) -> ProviderStatus:
        """Check if Anthropic is healthy and return available models."""
        try:
            await self._ensure_initialized()
            
            if not self.client:
                return ProviderStatus(
                    available=False,
                    models=[],
                    capabilities=self.get_capabilities(),
                    error="Client not initialized",
                    last_check=datetime.now()
                )
            
            start_time = time.time()
            
            # Test with a simple completion
            test_response = await self.client.messages.create(
                model=self.default_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            
            end_time = time.time()
            response_time_ms = round((end_time - start_time) * 1000, 2)
            
            if test_response:
                return ProviderStatus(
                    available=True,
                    models=self._supported_models,
                    capabilities=self.get_capabilities(),
                    last_check=datetime.now(),
                    response_time_ms=response_time_ms
                )
            
        except anthropic.APIError as e:
            return ProviderStatus(
                available=False,
                models=[],
                capabilities=self.get_capabilities(),
                error=f"Anthropic API error: {e}",
                last_check=datetime.now()
            )
        except Exception as e:
            logger.error(f"Anthropic health check failed: {e}")
            return ProviderStatus(
                available=False,
                models=[],
                capabilities=self.get_capabilities(),
                error=str(e),
                last_check=datetime.now()
            )
        
        return ProviderStatus(
            available=False,
            models=[],
            capabilities=self.get_capabilities(),
            error="Unknown error",
            last_check=datetime.now()
        )
    
    def get_supported_models(self) -> List[str]:
        """Return list of supported models."""
        return self._supported_models.copy()
    
    def get_default_model(self) -> str:
        """Return the default model for Anthropic."""
        return self.default_model
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Return the configuration schema for this provider."""
        return {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "Anthropic API key",
                    "required": True
                },
                "base_url": {
                    "type": "string",
                    "description": "Anthropic API base URL",
                    "default": "https://api.anthropic.com"
                },
                "default_model": {
                    "type": "string",
                    "description": "Default model to use",
                    "default": "claude-3-sonnet-20240229",
                    "enum": self._supported_models
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "default": 60,
                    "minimum": 1
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum tokens for completion",
                    "default": 4096,
                    "minimum": 1,
                    "maximum": 100000
                }
            },
            "required": ["api_key"]
        }
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Return information about a specific model."""
        model_info = {
            "claude-3-opus-20240229": {
                "context_length": 200000,
                "training_data": "Up to April 2024",
                "capabilities": ["text", "vision", "multimodal"],
                "performance": "highest"
            },
            "claude-3-sonnet-20240229": {
                "context_length": 200000,
                "training_data": "Up to April 2024",
                "capabilities": ["text", "vision", "multimodal"],
                "performance": "balanced"
            },
            "claude-3-haiku-20240307": {
                "context_length": 200000,
                "training_data": "Up to April 2024",
                "capabilities": ["text", "vision", "multimodal"],
                "performance": "fastest"
            },
            "claude-2.1": {
                "context_length": 200000,
                "training_data": "Up to April 2023",
                "capabilities": ["text"],
                "performance": "high"
            },
            "claude-2.0": {
                "context_length": 100000,
                "training_data": "Up to April 2023",
                "capabilities": ["text"],
                "performance": "high"
            },
            "claude-instant-1.2": {
                "context_length": 100000,
                "training_data": "Up to April 2023",
                "capabilities": ["text"],
                "performance": "fast"
            }
        }
        
        return model_info.get(model_name)