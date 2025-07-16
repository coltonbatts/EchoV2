from fastapi import APIRouter, HTTPException
from typing import Optional
from services.health_service import health_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    """Root endpoint returning basic API information."""
    return {"message": "EchoV2 Backend is running", "version": "0.2.0"}


@router.get("/health")
async def health_check():
    """Check overall system health including all AI providers."""
    try:
        health_status = await health_service.check_system_health()
        
        # Return appropriate HTTP status based on health
        if health_status["status"] == "healthy":
            return health_status
        elif health_status["status"] == "unhealthy":
            raise HTTPException(status_code=503, detail=health_status)
        else:
            raise HTTPException(status_code=500, detail=health_status)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail={"status": "error", "error": str(e)})


@router.get("/health/{provider_name}")
async def provider_health_check(provider_name: str):
    """Check health of a specific AI provider."""
    try:
        health_status = await health_service.check_provider_health(provider_name)
        
        if health_status["available"]:
            return health_status
        else:
            raise HTTPException(status_code=503, detail=health_status)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Provider health check failed for {provider_name}: {e}")
        raise HTTPException(status_code=500, detail={
            "provider": provider_name,
            "available": False,
            "error": str(e)
        })