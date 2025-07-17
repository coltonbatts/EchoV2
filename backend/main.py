from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from contextlib import asynccontextmanager

# Import configuration and routes
import sys
sys.path.append('.')
from config.settings import get_settings
from api.routes.health import router as health_router
from api.routes.chat import router as chat_router
from api.routes.plugins import router as plugins_router
from api.routes.conversations import router as conversations_router

# Import and register providers
from core.models.registry import registry
from core.plugins.ollama_provider import OllamaProvider
from core.plugins.openai_provider import OpenAIProvider
from core.plugins.anthropic_provider import AnthropicProvider

# Import database
from core.database import init_database, close_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logging.info("Starting EchoV2 Backend...")
    
    # Initialize database
    await init_database()
    logging.info("Database initialized")
    
    # Register AI providers
    registry.register(OllamaProvider, "ollama")
    registry.register(OpenAIProvider, "openai")
    registry.register(AnthropicProvider, "anthropic")
    logging.info("Registered AI providers")
    
    # Initialize model manager (this will create provider instances)
    from core.models.manager import model_manager
    await model_manager.initialize_providers()
    logging.info("Initialized model manager")
    
    yield
    
    # Shutdown
    logging.info("Shutting down EchoV2 Backend...")
    await registry.shutdown_all()
    await close_database()
    logging.info("Database connection closed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.logging.level),
        format=settings.logging.format
    )
    
    # Create FastAPI app
    app = FastAPI(
        title="EchoV2 Backend",
        version="0.2.0",
        description="Modular AI chat backend with pluggable providers",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allowed_origins,
        allow_credentials=settings.cors.allow_credentials,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
    )
    
    # Include routers
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(plugins_router)
    app.include_router(conversations_router)
    
    return app


# Create the app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)