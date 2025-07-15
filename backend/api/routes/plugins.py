from fastapi import APIRouter, HTTPException, status
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from core.models.registry import registry
from core.models.base import PluginMetadata, ProviderStatus
from config.settings import get_settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plugins", tags=["plugins"])


class PluginConfigRequest(BaseModel):
    provider_name: str
    config: Dict[str, Any]


class PluginReloadRequest(BaseModel):
    provider_name: str
    config: Optional[Dict[str, Any]] = None


class PluginStatusResponse(BaseModel):
    provider_name: str
    available: bool
    metadata: Optional[PluginMetadata] = None
    status: Optional[ProviderStatus] = None
    error: Optional[str] = None


@router.get("/", response_model=List[str])
async def list_providers():
    """List all registered providers."""
    try:
        return registry.list_providers()
    except Exception as e:
        logger.error(f"Failed to list providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list providers: {str(e)}"
        )


@router.get("/instances", response_model=List[str])
async def list_instances():
    """List all instantiated providers."""
    try:
        return registry.list_instances()
    except Exception as e:
        logger.error(f"Failed to list instances: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list instances: {str(e)}"
        )


@router.get("/metadata", response_model=Dict[str, PluginMetadata])
async def get_all_metadata():
    """Get metadata for all providers."""
    try:
        return registry.get_all_metadata()
    except Exception as e:
        logger.error(f"Failed to get metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metadata: {str(e)}"
        )


@router.get("/{provider_name}/metadata", response_model=PluginMetadata)
async def get_provider_metadata(provider_name: str):
    """Get metadata for a specific provider."""
    try:
        metadata = registry.get_provider_metadata(provider_name)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider {provider_name} not found"
            )
        return metadata
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metadata for {provider_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metadata: {str(e)}"
        )


@router.get("/{provider_name}/status", response_model=PluginStatusResponse)
async def get_provider_status(provider_name: str):
    """Get status and health information for a specific provider."""
    try:
        instance = registry.get_instance(provider_name)
        if not instance:
            return PluginStatusResponse(
                provider_name=provider_name,
                available=False,
                error="Provider not instantiated"
            )
        
        metadata = registry.get_provider_metadata(provider_name)
        status_result = await instance.health_check()
        
        return PluginStatusResponse(
            provider_name=provider_name,
            available=status_result.available,
            metadata=metadata,
            status=status_result
        )
        
    except Exception as e:
        logger.error(f"Failed to get status for {provider_name}: {e}")
        return PluginStatusResponse(
            provider_name=provider_name,
            available=False,
            error=str(e)
        )


@router.get("/{provider_name}/config-schema", response_model=Dict[str, Any])
async def get_provider_config_schema(provider_name: str):
    """Get configuration schema for a specific provider."""
    try:
        instance = registry.get_instance(provider_name)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider {provider_name} not found"
            )
        
        schema = instance.get_config_schema()
        if not schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No configuration schema available for {provider_name}"
            )
        
        return schema
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get config schema for {provider_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration schema: {str(e)}"
        )


@router.get("/{provider_name}/models", response_model=List[str])
async def get_provider_models(provider_name: str):
    """Get supported models for a specific provider."""
    try:
        instance = registry.get_instance(provider_name)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider {provider_name} not found"
            )
        
        return instance.get_supported_models()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get models for {provider_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get models: {str(e)}"
        )


@router.get("/{provider_name}/models/{model_name}", response_model=Dict[str, Any])
async def get_model_info(provider_name: str, model_name: str):
    """Get information about a specific model."""
    try:
        instance = registry.get_instance(provider_name)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider {provider_name} not found"
            )
        
        model_info = instance.get_model_info(model_name)
        if not model_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_name} not found for provider {provider_name}"
            )
        
        return model_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model info for {provider_name}/{model_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model information: {str(e)}"
        )


@router.post("/{provider_name}/reload")
async def reload_provider(provider_name: str, request: PluginReloadRequest):
    """Hot-reload a provider with optional new configuration."""
    try:
        if request.provider_name != provider_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provider name in URL and request body must match"
            )
        
        success = await registry.reload_provider(provider_name, request.config)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to reload provider {provider_name}"
            )
        
        return {"message": f"Provider {provider_name} reloaded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reload provider {provider_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload provider: {str(e)}"
        )


@router.put("/{provider_name}/config")
async def update_provider_config(provider_name: str, config: Dict[str, Any]):
    """Update provider configuration without full reload."""
    try:
        success = await registry.update_provider_config(provider_name, config)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update configuration for provider {provider_name}"
            )
        
        return {"message": f"Configuration updated for provider {provider_name}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update config for provider {provider_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.delete("/{provider_name}")
async def unregister_provider(provider_name: str):
    """Unregister and shutdown a provider."""
    try:
        success = await registry.unregister_provider(provider_name)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to unregister provider {provider_name}"
            )
        
        return {"message": f"Provider {provider_name} unregistered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unregister provider {provider_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unregister provider: {str(e)}"
        )


@router.post("/discover")
async def discover_plugins(plugin_directory: Optional[str] = None):
    """Discover and load plugins from a directory."""
    try:
        from pathlib import Path
        
        if plugin_directory:
            plugin_path = Path(plugin_directory)
        else:
            # Default plugin directory
            plugin_path = Path(__file__).parent.parent.parent / "core" / "plugins"
        
        discovered = await registry.discover_plugins(plugin_path)
        
        return {
            "message": f"Plugin discovery completed",
            "discovered_plugins": discovered,
            "plugin_directory": str(plugin_path)
        }
        
    except Exception as e:
        logger.error(f"Failed to discover plugins: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover plugins: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, ProviderStatus])
async def health_check_all():
    """Run health check on all providers."""
    try:
        return await registry.health_check_all()
    except Exception as e:
        logger.error(f"Failed to run health checks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run health checks: {str(e)}"
        )