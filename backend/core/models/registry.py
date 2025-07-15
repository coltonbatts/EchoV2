from typing import Dict, Type, List, Optional, Any
from .base import AbstractAIProvider, ProviderStatus, PluginMetadata
import logging
import importlib
import importlib.util
import sys
import asyncio
from pathlib import Path
import traceback

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry for AI provider plugins with hot-swapping support."""
    
    def __init__(self):
        self._providers: Dict[str, Type[AbstractAIProvider]] = {}
        self._instances: Dict[str, AbstractAIProvider] = {}
        self._plugin_modules: Dict[str, str] = {}  # provider_name -> module_path
        self._plugin_metadata: Dict[str, PluginMetadata] = {}
        self._config_cache: Dict[str, Dict[str, Any]] = {}
    
    def register(self, provider_class: Type[AbstractAIProvider], name: Optional[str] = None, module_path: Optional[str] = None):
        """Register a new AI provider class."""
        provider_name = name or provider_class.__name__.lower().replace("provider", "")
        self._providers[provider_name] = provider_class
        
        if module_path:
            self._plugin_modules[provider_name] = module_path
        
        logger.info(f"Registered AI provider: {provider_name}")
    
    async def create_instance(self, provider_name: str, config: Dict[str, Any]) -> AbstractAIProvider:
        """Create an instance of a registered provider."""
        if provider_name not in self._providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        if provider_name not in self._instances:
            provider_class = self._providers[provider_name]
            
            # Validate config if provider supports it
            try:
                temp_instance = provider_class(config)
                if hasattr(temp_instance, 'validate_config'):
                    if not temp_instance.validate_config(config):
                        raise ValueError(f"Invalid configuration for provider: {provider_name}")
            except Exception as e:
                logger.error(f"Configuration validation failed for {provider_name}: {e}")
                raise
            
            instance = provider_class(config)
            await instance.initialize()
            self._instances[provider_name] = instance
            self._config_cache[provider_name] = config.copy()
            
            # Cache metadata
            if hasattr(instance, 'metadata'):
                self._plugin_metadata[provider_name] = instance.metadata
            
            logger.info(f"Created instance of provider: {provider_name}")
        
        return self._instances[provider_name]
    
    async def reload_provider(self, provider_name: str, new_config: Optional[Dict[str, Any]] = None) -> bool:
        """Hot-reload a provider with optional new configuration."""
        try:
            if provider_name not in self._providers:
                logger.error(f"Provider {provider_name} not registered")
                return False
            
            # Get existing instance and config
            existing_instance = self._instances.get(provider_name)
            config = new_config or self._config_cache.get(provider_name, {})
            
            # If we have a module path, reload the module
            if provider_name in self._plugin_modules:
                module_path = self._plugin_modules[provider_name]
                await self._reload_module(module_path, provider_name)
            
            # Shutdown existing instance
            if existing_instance:
                try:
                    await existing_instance.shutdown()
                except Exception as e:
                    logger.warning(f"Error shutting down provider {provider_name}: {e}")
                
                del self._instances[provider_name]
            
            # Create new instance
            await self.create_instance(provider_name, config)
            logger.info(f"Successfully reloaded provider: {provider_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload provider {provider_name}: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def _reload_module(self, module_path: str, provider_name: str):
        """Reload a Python module dynamically."""
        try:
            if module_path in sys.modules:
                # Reload existing module
                module = sys.modules[module_path]
                importlib.reload(module)
                logger.info(f"Reloaded module: {module_path}")
            else:
                # Import new module
                spec = importlib.util.spec_from_file_location(module_path, module_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_path] = module
                    spec.loader.exec_module(module)
                    logger.info(f"Loaded new module: {module_path}")
        except Exception as e:
            logger.error(f"Failed to reload module {module_path}: {e}")
            raise
    
    async def update_provider_config(self, provider_name: str, new_config: Dict[str, Any]) -> bool:
        """Update provider configuration without full reload."""
        try:
            instance = self._instances.get(provider_name)
            if not instance:
                logger.error(f"Provider {provider_name} not found")
                return False
            
            # Validate new config
            if hasattr(instance, 'validate_config'):
                if not instance.validate_config(new_config):
                    logger.error(f"Invalid configuration for provider: {provider_name}")
                    return False
            
            # Reload with new config
            await instance.reload(new_config)
            self._config_cache[provider_name] = new_config.copy()
            
            logger.info(f"Updated configuration for provider: {provider_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update config for provider {provider_name}: {e}")
            return False
    
    async def unregister_provider(self, provider_name: str) -> bool:
        """Unregister and shutdown a provider."""
        try:
            # Shutdown instance
            instance = self._instances.get(provider_name)
            if instance:
                await instance.shutdown()
                del self._instances[provider_name]
            
            # Remove from registry
            if provider_name in self._providers:
                del self._providers[provider_name]
            
            if provider_name in self._plugin_modules:
                del self._plugin_modules[provider_name]
            
            if provider_name in self._plugin_metadata:
                del self._plugin_metadata[provider_name]
            
            if provider_name in self._config_cache:
                del self._config_cache[provider_name]
            
            logger.info(f"Unregistered provider: {provider_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister provider {provider_name}: {e}")
            return False
    
    def get_instance(self, provider_name: str) -> Optional[AbstractAIProvider]:
        """Get an existing provider instance."""
        return self._instances.get(provider_name)
    
    def list_providers(self) -> List[str]:
        """List all registered provider names."""
        return list(self._providers.keys())
    
    def list_instances(self) -> List[str]:
        """List all instantiated provider names."""
        return list(self._instances.keys())
    
    def get_provider_metadata(self, provider_name: str) -> Optional[PluginMetadata]:
        """Get metadata for a specific provider."""
        return self._plugin_metadata.get(provider_name)
    
    def get_all_metadata(self) -> Dict[str, PluginMetadata]:
        """Get metadata for all providers."""
        return self._plugin_metadata.copy()
    
    async def health_check_all(self) -> Dict[str, ProviderStatus]:
        """Run health check on all instantiated providers."""
        results = {}
        for name, provider in self._instances.items():
            try:
                await provider._ensure_initialized()
                results[name] = await provider.health_check()
            except Exception as e:
                logger.error(f"Health check failed for provider {name}: {e}")
                results[name] = ProviderStatus(
                    available=False,
                    models=[],
                    error=str(e)
                )
        return results
    
    async def discover_plugins(self, plugin_directory: Path) -> List[str]:
        """Discover and load plugins from a directory."""
        discovered = []
        
        if not plugin_directory.exists():
            logger.warning(f"Plugin directory does not exist: {plugin_directory}")
            return discovered
        
        for plugin_file in plugin_directory.glob("*_provider.py"):
            try:
                module_name = plugin_file.stem
                spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Look for provider classes
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, AbstractAIProvider) and 
                            attr != AbstractAIProvider):
                            
                            provider_name = attr_name.lower().replace("provider", "")
                            self.register(attr, provider_name, str(plugin_file))
                            discovered.append(provider_name)
                            logger.info(f"Discovered plugin: {provider_name} from {plugin_file}")
                            
            except Exception as e:
                logger.error(f"Failed to load plugin from {plugin_file}: {e}")
        
        return discovered
    
    async def shutdown_all(self):
        """Shutdown all provider instances."""
        for name, instance in self._instances.items():
            try:
                await instance.shutdown()
                logger.info(f"Shutdown provider: {name}")
            except Exception as e:
                logger.error(f"Error shutting down provider {name}: {e}")
        
        self._instances.clear()


# Global registry instance
registry = ProviderRegistry()