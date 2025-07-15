import requests
import asyncio
import json
import aiohttp
from typing import Dict, Any, List, AsyncGenerator, Optional
from ..models.base import (
    AbstractAIProvider, ChatRequest, ChatResponse, ProviderStatus, 
    ChatMessage, StreamingChunk, PluginMetadata, PluginCapability, AIModelType
)
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class OllamaProvider(AbstractAIProvider):
    """Ollama AI provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.default_model = config.get("default_model", "mistral")
        self.timeout = config.get("timeout", 60)
        self.api_endpoints = config.get("api_endpoints", {
            "generate": "/api/generate",
            "tags": "/api/tags",
            "chat": "/api/chat"
        })
        self._session: Optional[aiohttp.ClientSession] = None
    
    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="Ollama Provider",
            version="1.0.0",
            description="Ollama local AI provider with multiple model support",
            author="EchoV2 Team",
            capabilities=[
                PluginCapability.STREAMING,
                PluginCapability.EMBEDDINGS
            ],
            supported_model_types=[
                AIModelType.CHAT,
                AIModelType.TEXT_GENERATION,
                AIModelType.CODE_GENERATION,
                AIModelType.EMBEDDING
            ],
            dependencies=["aiohttp", "requests"],
            min_python_version="3.8",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    async def initialize(self) -> None:
        """Initialize the Ollama provider."""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        logger.info("Ollama provider initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown the provider."""
        if self._session:
            await self._session.close()
            self._session = None
        logger.info("Ollama provider shutdown completed")
    
    async def reload(self, new_config: Dict[str, Any]) -> None:
        """Reload the provider with new configuration."""
        await self.shutdown()
        self.config = new_config
        self.base_url = new_config.get("base_url", "http://localhost:11434")
        self.default_model = new_config.get("default_model", "mistral")
        self.timeout = new_config.get("timeout", 60)
        self.api_endpoints = new_config.get("api_endpoints", {
            "generate": "/api/generate",
            "tags": "/api/tags",
            "chat": "/api/chat"
        })
        await self.initialize()
        logger.info("Ollama provider reloaded successfully")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate the provided configuration."""
        base_url = config.get("base_url", "http://localhost:11434")
        if not base_url.startswith(("http://", "https://")):
            logger.error("base_url must start with http:// or https://")
            return False
        
        timeout = config.get("timeout", 60)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            logger.error("timeout must be a positive number")
            return False
        
        return True
    
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Generate a chat completion using Ollama."""
        await self._ensure_initialized()
        
        model = request.model or self.default_model
        
        # Convert ChatMessage objects to Ollama format
        if len(request.messages) == 1 and request.messages[0].role == "user":
            # Use legacy generate endpoint for simple prompts
            return await self._generate_completion(request.messages[0].content, model, request)
        else:
            # Use chat endpoint for conversation
            return await self._chat_completion(request.messages, model, request)
    
    async def chat_completion_stream(self, request: ChatRequest) -> AsyncGenerator[StreamingChunk, None]:
        """Generate a streaming chat completion response."""
        await self._ensure_initialized()
        
        model = request.model or self.default_model
        
        if len(request.messages) == 1 and request.messages[0].role == "user":
            # Use legacy generate endpoint for simple prompts
            async for chunk in self._generate_completion_stream(request.messages[0].content, model, request):
                yield chunk
        else:
            # Use chat endpoint for conversation
            async for chunk in self._chat_completion_stream(request.messages, model, request):
                yield chunk
    
    async def _generate_completion(self, prompt: str, model: str, request: ChatRequest) -> ChatResponse:
        """Use Ollama's generate endpoint for simple prompts."""
        if not self._session:
            raise RuntimeError("Ollama session not initialized")
        
        url = f"{self.base_url}{self.api_endpoints['generate']}"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        # Add optional parameters
        if request.temperature is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["temperature"] = request.temperature
        
        try:
            start_time = time.time()
            async with self._session.post(url, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"Ollama API error: {response.status} - {text}")
                
                result = await response.json()
                end_time = time.time()
                
                return ChatResponse(
                    content=result.get("response", "No response from model"),
                    model=model,
                    metadata={
                        "provider": "ollama", 
                        "endpoint": "generate",
                        "response_time_ms": round((end_time - start_time) * 1000, 2)
                    }
                )
            
        except aiohttp.ClientConnectorError:
            raise Exception("Cannot connect to Ollama. Make sure Ollama is running.")
        except asyncio.TimeoutError:
            raise Exception("Request to Ollama timed out")
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    async def _generate_completion_stream(self, prompt: str, model: str, request: ChatRequest) -> AsyncGenerator[StreamingChunk, None]:
        """Use Ollama's generate endpoint for streaming simple prompts."""
        if not self._session:
            raise RuntimeError("Ollama session not initialized")
        
        url = f"{self.base_url}{self.api_endpoints['generate']}"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True
        }
        
        # Add optional parameters
        if request.temperature is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["temperature"] = request.temperature
        
        try:
            async with self._session.post(url, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"Ollama API error: {response.status} - {text}")
                
                async for line in response.content:
                    if line:
                        try:
                            chunk_data = json.loads(line)
                            content = chunk_data.get("response", "")
                            is_final = chunk_data.get("done", False)
                            
                            if content or is_final:
                                yield StreamingChunk(
                                    content=content,
                                    is_final=is_final,
                                    metadata={
                                        "provider": "ollama",
                                        "model": model,
                                        "endpoint": "generate"
                                    }
                                )
                            
                            if is_final:
                                break
                                
                        except json.JSONDecodeError:
                            continue
            
        except aiohttp.ClientConnectorError:
            raise Exception("Cannot connect to Ollama. Make sure Ollama is running.")
        except asyncio.TimeoutError:
            raise Exception("Request to Ollama timed out")
        except Exception as e:
            logger.error(f"Ollama streaming generation failed: {e}")
            raise
    
    async def _chat_completion(self, messages: List[ChatMessage], model: str, request: ChatRequest) -> ChatResponse:
        """Use Ollama's chat endpoint for conversations."""
        if not self._session:
            raise RuntimeError("Ollama session not initialized")
        
        url = f"{self.base_url}{self.api_endpoints['chat']}"
        
        # Convert to Ollama chat format
        ollama_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": False
        }
        
        # Add optional parameters
        if request.temperature is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["temperature"] = request.temperature
        
        try:
            start_time = time.time()
            async with self._session.post(url, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"Ollama API error: {response.status} - {text}")
                
                result = await response.json()
                message = result.get("message", {})
                end_time = time.time()
                
                return ChatResponse(
                    content=message.get("content", "No response from model"),
                    model=model,
                    metadata={
                        "provider": "ollama", 
                        "endpoint": "chat",
                        "response_time_ms": round((end_time - start_time) * 1000, 2)
                    }
                )
            
        except aiohttp.ClientConnectorError:
            raise Exception("Cannot connect to Ollama. Make sure Ollama is running.")
        except asyncio.TimeoutError:
            raise Exception("Request to Ollama timed out")
        except Exception as e:
            logger.error(f"Ollama chat completion failed: {e}")
            raise
    
    async def _chat_completion_stream(self, messages: List[ChatMessage], model: str, request: ChatRequest) -> AsyncGenerator[StreamingChunk, None]:
        """Use Ollama's chat endpoint for streaming conversations."""
        if not self._session:
            raise RuntimeError("Ollama session not initialized")
        
        url = f"{self.base_url}{self.api_endpoints['chat']}"
        
        # Convert to Ollama chat format
        ollama_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": True
        }
        
        # Add optional parameters
        if request.temperature is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["temperature"] = request.temperature
        
        try:
            async with self._session.post(url, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"Ollama API error: {response.status} - {text}")
                
                async for line in response.content:
                    if line:
                        try:
                            chunk_data = json.loads(line)
                            message = chunk_data.get("message", {})
                            content = message.get("content", "")
                            is_final = chunk_data.get("done", False)
                            
                            if content or is_final:
                                yield StreamingChunk(
                                    content=content,
                                    is_final=is_final,
                                    metadata={
                                        "provider": "ollama",
                                        "model": model,
                                        "endpoint": "chat"
                                    }
                                )
                            
                            if is_final:
                                break
                                
                        except json.JSONDecodeError:
                            continue
            
        except aiohttp.ClientConnectorError:
            raise Exception("Cannot connect to Ollama. Make sure Ollama is running.")
        except asyncio.TimeoutError:
            raise Exception("Request to Ollama timed out")
        except Exception as e:
            logger.error(f"Ollama streaming chat completion failed: {e}")
            raise
    
    async def health_check(self) -> ProviderStatus:
        """Check if Ollama is healthy and return available models."""
        try:
            if not self._session:
                # Create a temporary session for health check
                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(timeout=timeout) as temp_session:
                    return await self._perform_health_check(temp_session)
            else:
                return await self._perform_health_check(self._session)
                
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return ProviderStatus(
                available=False,
                models=[],
                capabilities=self.get_capabilities(),
                error=str(e),
                last_check=datetime.now()
            )
    
    async def _perform_health_check(self, session: aiohttp.ClientSession) -> ProviderStatus:
        """Perform the actual health check with a session."""
        url = f"{self.base_url}{self.api_endpoints['tags']}"
        
        try:
            start_time = time.time()
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    end_time = time.time()
                    response_time_ms = round((end_time - start_time) * 1000, 2)
                    
                    return ProviderStatus(
                        available=True,
                        models=models,
                        capabilities=self.get_capabilities(),
                        last_check=datetime.now(),
                        response_time_ms=response_time_ms
                    )
                else:
                    text = await response.text()
                    return ProviderStatus(
                        available=False,
                        models=[],
                        capabilities=self.get_capabilities(),
                        error=f"HTTP {response.status}: {text}",
                        last_check=datetime.now()
                    )
                    
        except aiohttp.ClientConnectorError:
            return ProviderStatus(
                available=False,
                models=[],
                capabilities=self.get_capabilities(),
                error="Cannot connect to Ollama",
                last_check=datetime.now()
            )
        except asyncio.TimeoutError:
            return ProviderStatus(
                available=False,
                models=[],
                capabilities=self.get_capabilities(),
                error="Health check timed out",
                last_check=datetime.now()
            )
    
    def get_supported_models(self) -> List[str]:
        """Return list of supported models (requires health check for live data)."""
        # This returns a static list; use health_check() for live model list
        return [self.default_model, "llama2", "codellama", "mistral", "neural-chat", "llama3", "gemma"]
    
    def get_default_model(self) -> str:
        """Return the default model for Ollama."""
        return self.default_model
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Return the configuration schema for this provider."""
        return {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string",
                    "description": "Ollama server base URL",
                    "default": "http://localhost:11434",
                    "pattern": "^https?://"
                },
                "default_model": {
                    "type": "string",
                    "description": "Default model to use",
                    "default": "mistral"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "default": 60,
                    "minimum": 1
                },
                "api_endpoints": {
                    "type": "object",
                    "description": "API endpoint paths",
                    "properties": {
                        "generate": {"type": "string", "default": "/api/generate"},
                        "tags": {"type": "string", "default": "/api/tags"},
                        "chat": {"type": "string", "default": "/api/chat"}
                    }
                }
            }
        }
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Return information about a specific model."""
        # Basic model info - in a real implementation, this could query Ollama for detailed model info
        model_info = {
            "mistral": {
                "description": "Mistral 7B model optimized for instruction following",
                "size": "7B parameters",
                "capabilities": ["text", "chat", "code"]
            },
            "llama2": {
                "description": "Llama 2 model from Meta",
                "size": "7B parameters",
                "capabilities": ["text", "chat"]
            },
            "codellama": {
                "description": "Code Llama model specialized for code generation",
                "size": "7B parameters", 
                "capabilities": ["code", "text"]
            },
            "llama3": {
                "description": "Llama 3 model from Meta with improved performance",
                "size": "8B parameters",
                "capabilities": ["text", "chat", "reasoning"]
            },
            "gemma": {
                "description": "Gemma model from Google",
                "size": "7B parameters",
                "capabilities": ["text", "chat"]
            }
        }
        
        return model_info.get(model_name)