from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, AsyncGenerator
from services.chat_service import chat_service
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequestModel(BaseModel):
    prompt: str
    model: Optional[str] = None
    provider: Optional[str] = None
    conversation_id: Optional[int] = None


class ConversationMessage(BaseModel):
    role: str
    content: str


class ConversationRequestModel(BaseModel):
    messages: List[ConversationMessage]
    model: Optional[str] = None
    provider: Optional[str] = None
    conversation_id: Optional[int] = None


class ChatResponseModel(BaseModel):
    response: str
    model: str
    provider: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    conversation_id: Optional[int] = None


async def create_sse_stream(generator: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
    """Convert a response generator to SSE format."""
    try:
        async for chunk in generator:
            # Format as Server-Sent Events
            yield f"data: {json.dumps({'chunk': chunk, 'type': 'content'})}\n\n"
        
        # Send completion signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except Exception as e:
        # Send error signal
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@router.post("/")
async def chat_completion(request: ChatRequestModel):
    """Send a single message to the AI and get a streaming response."""
    try:
        # Always return streaming response
        generator = chat_service.send_message_stream(
            prompt=request.prompt,
            model=request.model,
            provider=request.provider,
            conversation_id=request.conversation_id
        )
        
        return StreamingResponse(
            create_sse_stream(generator),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        
        if "Cannot connect" in str(e):
            raise HTTPException(status_code=503, detail=str(e))
        elif "timed out" in str(e):
            raise HTTPException(status_code=504, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/conversation", response_model=ChatResponseModel)
async def conversation_completion(request: ConversationRequestModel):
    """Send a conversation with multiple messages to the AI."""
    try:
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        response, conversation_id = await chat_service.send_conversation(
            messages=messages,
            model=request.model,
            provider=request.provider,
            conversation_id=request.conversation_id
        )
        
        return ChatResponseModel(
            response=response.content,
            model=response.model,
            provider=request.provider,
            metadata=response.metadata,
            conversation_id=conversation_id
        )
        
    except Exception as e:
        logger.error(f"Conversation completion failed: {e}")
        
        if "Cannot connect" in str(e):
            raise HTTPException(status_code=503, detail=str(e))
        elif "timed out" in str(e):
            raise HTTPException(status_code=504, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/providers")
async def list_providers():
    """List all available AI providers."""
    try:
        providers = chat_service.list_available_providers()
        default_provider = chat_service.get_default_provider()
        
        return {
            "providers": providers,
            "default": default_provider
        }
        
    except Exception as e:
        logger.error(f"Failed to list providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/{provider_name}/models")
async def list_provider_models(provider_name: str):
    """List available models for a specific provider."""
    try:
        models = chat_service.get_provider_models(provider_name)
        
        return {
            "provider": provider_name,
            "models": models
        }
        
    except Exception as e:
        logger.error(f"Failed to list models for {provider_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))