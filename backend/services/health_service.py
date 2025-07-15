from typing import Dict, Any
from ..core.models.manager import model_manager
import logging

logger = logging.getLogger(__name__)


class HealthService:
    """Service layer for health check operations."""
    
    def __init__(self):
        self.model_manager = model_manager
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health including all providers."""
        try:
            provider_status = await self.model_manager.health_check()
            
            # Calculate overall system health
            total_providers = len(provider_status)
            healthy_providers = sum(1 for status in provider_status.values() if status.available)
            
            overall_status = "healthy" if healthy_providers > 0 else "unhealthy"
            
            return {
                "status": overall_status,
                "providers": {
                    name: {
                        "available": status.available,
                        "models": status.models,
                        "error": status.error
                    }
                    for name, status in provider_status.items()
                },
                "summary": {
                    "total_providers": total_providers,
                    "healthy_providers": healthy_providers,
                    "default_provider": self.model_manager.get_default_provider()
                }
            }
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "providers": {},
                "summary": {
                    "total_providers": 0,
                    "healthy_providers": 0,
                    "default_provider": "unknown"
                }
            }
    
    async def check_provider_health(self, provider_name: str) -> Dict[str, Any]:
        """Check health of a specific provider."""
        try:
            provider_status = await self.model_manager.health_check(provider_name)
            
            if provider_name in provider_status:
                status = provider_status[provider_name]
                return {
                    "provider": provider_name,
                    "available": status.available,
                    "models": status.models,
                    "error": status.error
                }
            else:
                return {
                    "provider": provider_name,
                    "available": False,
                    "models": [],
                    "error": "Provider not found"
                }
                
        except Exception as e:
            logger.error(f"Provider health check failed for {provider_name}: {e}")
            return {
                "provider": provider_name,
                "available": False,
                "models": [],
                "error": str(e)
            }


# Global service instance
health_service = HealthService()