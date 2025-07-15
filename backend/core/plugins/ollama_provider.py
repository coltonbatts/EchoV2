import requests
import asyncio
from typing import Dict, Any, List
from ..models.base import AbstractAIProvider, ChatRequest, ChatResponse, ProviderStatus, ChatMessage
import logging

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
    
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Generate a chat completion using Ollama."""
        model = request.model or self.default_model
        
        # Convert ChatMessage objects to Ollama format
        if len(request.messages) == 1 and request.messages[0].role == "user":
            # Use legacy generate endpoint for simple prompts
            return await self._generate_completion(request.messages[0].content, model)
        else:
            # Use chat endpoint for conversation
            return await self._chat_completion(request.messages, model)
    
    async def _generate_completion(self, prompt: str, model: str) -> ChatResponse:
        """Use Ollama's generate endpoint for simple prompts."""
        url = f"{self.base_url}{self.api_endpoints['generate']}"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(url, json=payload, timeout=self.timeout)
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return ChatResponse(
                content=result.get("response", "No response from model"),
                model=model,
                metadata={"provider": "ollama", "endpoint": "generate"}
            )
            
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to Ollama. Make sure Ollama is running.")
        except requests.exceptions.Timeout:
            raise Exception("Request to Ollama timed out")
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    async def _chat_completion(self, messages: List[ChatMessage], model: str) -> ChatResponse:
        """Use Ollama's chat endpoint for conversations."""
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
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(url, json=payload, timeout=self.timeout)
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            message = result.get("message", {})
            
            return ChatResponse(
                content=message.get("content", "No response from model"),
                model=model,
                metadata={"provider": "ollama", "endpoint": "chat"}
            )
            
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to Ollama. Make sure Ollama is running.")
        except requests.exceptions.Timeout:
            raise Exception("Request to Ollama timed out")
        except Exception as e:
            logger.error(f"Ollama chat completion failed: {e}")
            raise
    
    async def health_check(self) -> ProviderStatus:
        """Check if Ollama is healthy and return available models."""
        try:
            url = f"{self.base_url}{self.api_endpoints['tags']}"
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, timeout=5)
            )
            
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                return ProviderStatus(available=True, models=models)
            else:
                return ProviderStatus(
                    available=False,
                    models=[],
                    error=f"HTTP {response.status_code}"
                )
                
        except requests.exceptions.ConnectionError:
            return ProviderStatus(
                available=False,
                models=[],
                error="Cannot connect to Ollama"
            )
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return ProviderStatus(
                available=False,
                models=[],
                error=str(e)
            )
    
    def get_supported_models(self) -> List[str]:
        """Return list of supported models (requires health check for live data)."""
        # This returns a static list; use health_check() for live model list
        return [self.default_model, "llama2", "codellama", "mistral", "neural-chat"]
    
    def get_default_model(self) -> str:
        """Return the default model for Ollama."""
        return self.default_model
    
    def supports_streaming(self) -> bool:
        """Ollama supports streaming responses."""
        return True