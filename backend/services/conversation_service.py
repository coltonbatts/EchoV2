from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, desc
import logging

from core.models.database import Conversation, Message
from core.models.base import ChatMessage
from core.database import get_db_session

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations and messages in the database."""
    
    @staticmethod
    async def create_conversation(title: Optional[str] = None) -> Conversation:
        """Create a new conversation."""
        async with get_db_session() as session:
            conversation = Conversation(title=title)
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            return conversation
    
    @staticmethod
    async def get_conversation(conversation_id: int) -> Optional[Conversation]:
        """Get a conversation by ID with its messages."""
        async with get_db_session() as session:
            stmt = select(Conversation).options(selectinload(Conversation.messages)).where(Conversation.id == conversation_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_conversations(limit: int = 50, offset: int = 0) -> List[Conversation]:
        """Get all conversations ordered by most recent."""
        async with get_db_session() as session:
            stmt = select(Conversation).order_by(desc(Conversation.updated_at)).limit(limit).offset(offset)
            result = await session.execute(stmt)
            return result.scalars().all()
    
    @staticmethod
    async def add_message(
        conversation_id: int,
        role: str,
        content: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        message_metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add a message to a conversation."""
        async with get_db_session() as session:
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                provider=provider,
                model=model,
                message_metadata=message_metadata
            )
            session.add(message)
            
            # Update conversation's updated_at timestamp
            conversation = await session.get(Conversation, conversation_id)
            if conversation:
                conversation.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(message)
            return message
    
    @staticmethod
    async def get_or_create_conversation(conversation_id: Optional[int] = None) -> Conversation:
        """Get an existing conversation or create a new one."""
        if conversation_id:
            conversation = await ConversationService.get_conversation(conversation_id)
            if conversation:
                return conversation
        
        # Create new conversation if not found or no ID provided
        return await ConversationService.create_conversation()
    
    @staticmethod
    async def generate_conversation_title(conversation_id: int) -> Optional[str]:
        """Generate a title for a conversation based on its first message."""
        async with get_db_session() as session:
            stmt = select(Message).where(
                Message.conversation_id == conversation_id,
                Message.role == "user"
            ).order_by(Message.timestamp).limit(1)
            
            result = await session.execute(stmt)
            first_message = result.scalar_one_or_none()
            
            if first_message:
                # Generate a title from the first 50 characters of the first user message
                title = first_message.content[:50].strip()
                if len(first_message.content) > 50:
                    title += "..."
                return title
            
            return None
    
    @staticmethod
    async def update_conversation_title(conversation_id: int, title: str) -> bool:
        """Update a conversation's title."""
        async with get_db_session() as session:
            conversation = await session.get(Conversation, conversation_id)
            if conversation:
                conversation.title = title
                await session.commit()
                return True
            return False
    
    @staticmethod
    async def delete_conversation(conversation_id: int) -> bool:
        """Delete a conversation and all its messages."""
        async with get_db_session() as session:
            conversation = await session.get(Conversation, conversation_id)
            if conversation:
                await session.delete(conversation)
                await session.commit()
                return True
            return False
    
    @staticmethod
    async def get_conversation_messages(conversation_id: int) -> List[Message]:
        """Get all messages for a conversation."""
        async with get_db_session() as session:
            stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.timestamp)
            result = await session.execute(stmt)
            return result.scalars().all()
    
    @staticmethod
    def message_to_chat_message(message: Message) -> ChatMessage:
        """Convert a database Message to a ChatMessage."""
        return ChatMessage(
            role=message.role,
            content=message.content
        )
    
    @staticmethod
    def messages_to_chat_messages(messages: List[Message]) -> List[ChatMessage]:
        """Convert a list of database Messages to ChatMessages."""
        return [ConversationService.message_to_chat_message(msg) for msg in messages]