from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from services.conversation_service import ConversationService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationSummary(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message_preview: Optional[str] = None


class MessageDetail(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime
    provider: Optional[str] = None
    model: Optional[str] = None
    message_metadata: Optional[Dict[str, Any]] = None


class ConversationDetail(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageDetail]


class UpdateTitleRequest(BaseModel):
    title: str


@router.get("/", response_model=List[ConversationSummary])
async def list_conversations(limit: int = 50, offset: int = 0):
    """Get list of conversations with metadata"""
    try:
        conversations = await ConversationService.get_conversations(limit=limit, offset=offset)
        
        summaries = []
        for conv in conversations:
            # Count messages for this conversation
            messages = await ConversationService.get_conversation_messages(conv.id)
            message_count = len(messages)
            
            # Get last message preview
            last_message_preview = None
            if messages:
                last_msg = messages[-1]
                preview = last_msg.content[:100].strip()
                if len(last_msg.content) > 100:
                    preview += "..."
                last_message_preview = preview
            
            summaries.append(ConversationSummary(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=message_count,
                last_message_preview=last_message_preview
            ))
        
        return summaries
        
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: int):
    """Get full conversation with all messages"""
    try:
        conversation = await ConversationService.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Convert messages to detail format
        message_details = []
        for msg in conversation.messages:
            message_details.append(MessageDetail(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                provider=msg.provider,
                model=msg.model,
                message_metadata=msg.message_metadata
            ))
        
        return ConversationDetail(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=message_details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: int):
    """Delete a conversation"""
    try:
        success = await ConversationService.delete_conversation(conversation_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{conversation_id}/title")
async def update_conversation_title(conversation_id: int, request: UpdateTitleRequest):
    """Update conversation title"""
    try:
        success = await ConversationService.update_conversation_title(
            conversation_id, request.title
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"message": "Conversation title updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update conversation {conversation_id} title: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/generate-title")
async def generate_conversation_title(conversation_id: int):
    """Generate and set a title for a conversation based on its first message"""
    try:
        # Check if conversation exists
        conversation = await ConversationService.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Generate title
        title = await ConversationService.generate_conversation_title(conversation_id)
        
        if not title:
            raise HTTPException(status_code=400, detail="Could not generate title - no user messages found")
        
        # Update the conversation with the generated title
        success = await ConversationService.update_conversation_title(conversation_id, title)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update conversation title")
        
        return {"title": title, "message": "Title generated and updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate title for conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))