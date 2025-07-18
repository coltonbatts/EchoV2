from typing import Dict, Optional, List
from .base import AbstractAIProvider, ChatRequest, ChatResponse, ProviderStatus
from .registry import registry
from config.settings import get_settings
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages AI model providers and routing."""
    
    def __init__(self):
        self.settings = get_settings()
        self.default_provider = self.settings.ai_providers.get("default", "ollama")
        self._initialized = False
    
    async def initialize_providers(self):
        """Initialize all configured providers asynchronously."""
        if self._initialized:
            return
        
        ai_config = self.settings.ai_providers
        
        for provider_name, config in ai_config.items():
            if provider_name == "default":
                continue
                
            try:
                await registry.create_instance(provider_name, config)
                logger.info(f"Initialized provider: {provider_name}")
            except Exception as e:
                logger.error(f"Failed to initialize provider {provider_name}: {e}")
        
        self._initialized = True
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
        reraise=True
    )
    async def _chat_completion_with_retry(
        self,
        provider: AbstractAIProvider,
        request: ChatRequest,
        provider_name: str
    ) -> ChatResponse:
        """Execute chat completion with retry logic for transient failures."""
        logger.info(f"Attempting chat completion with {provider_name} (model: {request.model})")
        return await provider.chat_completion(request)
    
    async def chat_completion(
        self, 
        request: ChatRequest, 
        provider_name: Optional[str] = None
    ) -> ChatResponse:
        """Route chat completion request to appropriate provider with retry logic."""
        await self.initialize_providers()
        
        provider_name = provider_name or self.default_provider
        provider = registry.get_instance(provider_name)
        
        if not provider:
            raise ValueError(f"Provider not available: {provider_name}")
        
        # Use provider's default model if none specified
        if not request.model:
            request.model = provider.get_default_model()
        
        try:
            return await self._chat_completion_with_retry(provider, request, provider_name)
        except Exception as e:
            logger.error(f"Chat completion failed after retries for {provider_name}: {e}")
            
            # Provide more specific error messages
            if "authentication" in str(e).lower() or "api key" in str(e).lower():
                raise ValueError(f"Authentication failed for {provider_name}. Please check your API key.")
            elif "rate limit" in str(e).lower() or "quota" in str(e).lower():
                raise ValueError(f"Rate limit exceeded for {provider_name}. Please try again later.")
            elif "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise ConnectionError(f"Connection failed to {provider_name}. Please check your internet connection.")
            elif "model" in str(e).lower() and "not found" in str(e).lower():
                raise ValueError(f"Model '{request.model}' not available for {provider_name}.")
            else:
                raise ValueError(f"Request failed for {provider_name}: {str(e)}")
    
    async def health_check(self, provider_name: Optional[str] = None) -> Dict[str, ProviderStatus]:
        """Check health of specified provider or all providers."""
        if provider_name:
            provider = registry.get_instance(provider_name)
            if not provider:
                return {provider_name: ProviderStatus(available=False, models=[], error="Provider not found")}
            
            try:
                status = await provider.health_check()
                return {provider_name: status}
            except Exception as e:
                return {provider_name: ProviderStatus(available=False, models=[], error=str(e))}
        
        return await registry.health_check_all()
    
    def list_providers(self) -> List[str]:
        """List all available providers."""
        return registry.list_instances()
    
    def get_provider_models(self, provider_name: str) -> List[str]:
        """Get supported models for a provider."""
        provider = registry.get_instance(provider_name)
        if not provider:
            return []
        return provider.get_supported_models()
    
    def get_default_provider(self) -> str:
        """Get the name of the default provider."""
        return self.default_provider


# Global model manager instance
model_manager = ModelManager()