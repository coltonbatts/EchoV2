import openai
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


class OpenAIProvider(AbstractAIProvider):
    """OpenAI API provider implementation with streaming support."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.organization = config.get("organization")
        self.default_model = config.get("default_model", "gpt-3.5-turbo")
        self.timeout = config.get("timeout", 60)
        self.max_retries = config.get("max_retries", 3)
        
        self.client: Optional[openai.AsyncOpenAI] = None
        
        # Supported models
        self._supported_models = [
            "gpt-4-turbo-preview", "gpt-4", "gpt-4-32k",
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k",
            "gpt-3.5-turbo-0125", "gpt-4-0125-preview"
        ]
    
    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="OpenAI Provider",
            version="1.0.0",
            description="OpenAI API provider with GPT models support",
            author="EchoV2 Team",
            capabilities=[
                PluginCapability.STREAMING,
                PluginCapability.FUNCTION_CALLING,
                PluginCapability.VISION
            ],
            supported_model_types=[
                AIModelType.CHAT,
                AIModelType.TEXT_GENERATION,
                AIModelType.CODE_GENERATION
            ],
            dependencies=["openai>=1.3.0"],
            min_python_version="3.8",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            organization=self.organization,
            timeout=self.timeout,
            max_retries=self.max_retries
        )
        
        logger.info("OpenAI provider initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown the provider."""
        if self.client:
            await self.client.close()
            self.client = None
        logger.info("OpenAI provider shutdown completed")
    
    async def reload(self, new_config: Dict[str, Any]) -> None:
        """Reload the provider with new configuration."""
        await self.shutdown()
        self.config = new_config
        self.api_key = new_config.get("api_key")
        self.base_url = new_config.get("base_url", "https://api.openai.com/v1")
        self.organization = new_config.get("organization")
        self.default_model = new_config.get("default_model", "gpt-3.5-turbo")
        self.timeout = new_config.get("timeout", 60)
        self.max_retries = new_config.get("max_retries", 3)
        await self.initialize()
        logger.info("OpenAI provider reloaded successfully")
    
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
    
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Generate a chat completion response."""
        await self._ensure_initialized()
        
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
        
        model = request.model or self.default_model
        
        # Convert messages to OpenAI format
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Build request parameters
        params = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        # Add optional parameters
        if request.temperature is not None:
            params["temperature"] = request.temperature
        if request.max_tokens is not None:
            params["max_tokens"] = request.max_tokens
        if request.top_p is not None:
            params["top_p"] = request.top_p
        if request.frequency_penalty is not None:
            params["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty is not None:
            params["presence_penalty"] = request.presence_penalty
        if request.stop is not None:
            params["stop"] = request.stop
        if request.functions is not None:
            params["functions"] = request.functions
        if request.function_call is not None:
            params["function_call"] = request.function_call
        
        try:
            start_time = time.time()
            response = await self.client.chat.completions.create(**params)
            end_time = time.time()
            
            choice = response.choices[0]
            message = choice.message
            
            # Extract function call if present
            function_call = None
            if hasattr(message, 'function_call') and message.function_call:
                function_call = {
                    "name": message.function_call.name,
                    "arguments": message.function_call.arguments
                }
            
            return ChatResponse(
                content=message.content or "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                metadata={
                    "provider": "openai",
                    "response_time_ms": round((end_time - start_time) * 1000, 2),
                    "finish_reason": choice.finish_reason
                },
                function_call=function_call,
                finish_reason=choice.finish_reason
            )
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"OpenAI completion failed: {e}")
            raise
    
    async def chat_completion_stream(self, request: ChatRequest) -> AsyncGenerator[StreamingChunk, None]:
        """Generate a streaming chat completion response."""
        await self._ensure_initialized()
        
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
        
        model = request.model or self.default_model
        
        # Convert messages to OpenAI format
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Build request parameters
        params = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        
        # Add optional parameters
        if request.temperature is not None:
            params["temperature"] = request.temperature
        if request.max_tokens is not None:
            params["max_tokens"] = request.max_tokens
        if request.top_p is not None:
            params["top_p"] = request.top_p
        if request.frequency_penalty is not None:
            params["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty is not None:
            params["presence_penalty"] = request.presence_penalty
        if request.stop is not None:
            params["stop"] = request.stop
        
        try:
            stream = await self.client.chat.completions.create(**params)
            
            async for chunk in stream:
                if chunk.choices:
                    choice = chunk.choices[0]
                    delta = choice.delta
                    
                    if delta.content:
                        yield StreamingChunk(
                            content=delta.content,
                            is_final=choice.finish_reason is not None,
                            metadata={
                                "provider": "openai",
                                "model": model,
                                "finish_reason": choice.finish_reason
                            }
                        )
                    
                    # Final chunk
                    if choice.finish_reason is not None:
                        yield StreamingChunk(
                            content="",
                            is_final=True,
                            metadata={
                                "provider": "openai",
                                "model": model,
                                "finish_reason": choice.finish_reason
                            }
                        )
                        break
            
        except openai.APIError as e:
            logger.error(f"OpenAI streaming API error: {e}")
            raise Exception(f"OpenAI streaming API error: {e}")
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            raise
    
    async def health_check(self) -> ProviderStatus:
        """Check if OpenAI is healthy and return available models."""
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
            test_response = await self.client.chat.completions.create(
                model=self.default_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
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
            
        except openai.APIError as e:
            return ProviderStatus(
                available=False,
                models=[],
                capabilities=self.get_capabilities(),
                error=f"OpenAI API error: {e}",
                last_check=datetime.now()
            )
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
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
        """Return the default model for OpenAI."""
        return self.default_model
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Return the configuration schema for this provider."""
        return {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "OpenAI API key",
                    "required": True
                },
                "base_url": {
                    "type": "string",
                    "description": "OpenAI API base URL",
                    "default": "https://api.openai.com/v1"
                },
                "organization": {
                    "type": "string",
                    "description": "OpenAI organization ID (optional)"
                },
                "default_model": {
                    "type": "string",
                    "description": "Default model to use",
                    "default": "gpt-3.5-turbo",
                    "enum": self._supported_models
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "default": 60,
                    "minimum": 1
                },
                "max_retries": {
                    "type": "integer",
                    "description": "Maximum number of retries",
                    "default": 3,
                    "minimum": 0
                }
            },
            "required": ["api_key"]
        }
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Return information about a specific model."""
        model_info = {
            "gpt-4-turbo-preview": {
                "context_length": 128000,
                "training_data": "Up to April 2023",
                "capabilities": ["text", "function_calling"]
            },
            "gpt-4": {
                "context_length": 8192,
                "training_data": "Up to September 2021",
                "capabilities": ["text", "function_calling"]
            },
            "gpt-4-32k": {
                "context_length": 32768,
                "training_data": "Up to September 2021",
                "capabilities": ["text", "function_calling"]
            },
            "gpt-3.5-turbo": {
                "context_length": 4096,
                "training_data": "Up to September 2021",
                "capabilities": ["text", "function_calling"]
            },
            "gpt-3.5-turbo-16k": {
                "context_length": 16384,
                "training_data": "Up to September 2021",
                "capabilities": ["text", "function_calling"]
            }
        }
        
        return model_info.get(model_name)