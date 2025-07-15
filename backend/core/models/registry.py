from typing import Dict, Type, List, Optional
from .base import AbstractAIProvider, ProviderStatus
import logging

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry for AI provider plugins."""
    
    def __init__(self):
        self._providers: Dict[str, Type[AbstractAIProvider]] = {}
        self._instances: Dict[str, AbstractAIProvider] = {}
    
    def register(self, provider_class: Type[AbstractAIProvider], name: Optional[str] = None):
        """Register a new AI provider class."""
        provider_name = name or provider_class.__name__.lower().replace("provider", "")
        self._providers[provider_name] = provider_class
        logger.info(f"Registered AI provider: {provider_name}")
    
    def create_instance(self, provider_name: str, config: Dict) -> AbstractAIProvider:
        """Create an instance of a registered provider."""
        if provider_name not in self._providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        if provider_name not in self._instances:
            provider_class = self._providers[provider_name]
            self._instances[provider_name] = provider_class(config)
            logger.info(f"Created instance of provider: {provider_name}")
        
        return self._instances[provider_name]
    
    def get_instance(self, provider_name: str) -> Optional[AbstractAIProvider]:
        """Get an existing provider instance."""
        return self._instances.get(provider_name)
    
    def list_providers(self) -> List[str]:
        """List all registered provider names."""
        return list(self._providers.keys())
    
    def list_instances(self) -> List[str]:
        """List all instantiated provider names."""
        return list(self._instances.keys())
    
    async def health_check_all(self) -> Dict[str, ProviderStatus]:
        """Run health check on all instantiated providers."""
        results = {}
        for name, provider in self._instances.items():
            try:
                results[name] = await provider.health_check()
            except Exception as e:
                logger.error(f"Health check failed for provider {name}: {e}")
                results[name] = ProviderStatus(
                    available=False,
                    models=[],
                    error=str(e)
                )
        return results


# Global registry instance
registry = ProviderRegistry()