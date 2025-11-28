"""Service for managing AI Tutor conversations using PostgreSQL."""

import logging
from typing import List, Optional, Dict, Any
import asyncpg

from app.repositories.conversation_repository import ConversationRepository
from app.models.conversation import (
    ConversationSummary,
    ConversationWithMessages
)

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations and messages using PostgreSQL."""
    
    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize service with PostgreSQL connection pool.
        
        Args:
            pool: AsyncPG connection pool
        """
        self.repository = ConversationRepository(pool)
    
    async def create_conversation(
        self,
        user_id: str,
        course_id: str,
        lecture_id: str,
        title: str = "New Chat"
    ) -> str:
        """
        Create a new conversation.
        
        Args:
            user_id: Firebase UID of the user
            course_id: Course identifier
            lecture_id: Lecture identifier
            title: Initial title for the conversation
            
        Returns:
            conversation_id: Unique ID for the new conversation
        """
        conversation_id = await self.repository.create_conversation(
            user_id=user_id,
            course_id=course_id,
            lecture_id=lecture_id,
            title=title
        )
        
        logger.info(f"Created conversation {conversation_id} for user {user_id}")
        return conversation_id
    
    async def get_user_conversations(
        self,
        user_id: str,
        course_id: Optional[str] = None,
        lecture_id: Optional[str] = None,
        limit: int = 50
    ) -> List[ConversationSummary]:
        """
        Get all conversations for a user, optionally filtered by course/lecture.
        
        Args:
            user_id: Firebase UID
            course_id: Optional course filter
            lecture_id: Optional lecture filter
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation summaries, ordered by most recent first
        """
        conversations_data = await self.repository.get_user_conversations(
            user_id=user_id,
            course_id=course_id,
            lecture_id=lecture_id,
            limit=limit
        )
        
        conversations = [
            ConversationSummary(
                conversation_id=conv["conversation_id"],
                title=conv["title"],
                course_id=conv["course_id"],
                lecture_id=conv["lecture_id"],
                created_at=conv["created_at"],
                updated_at=conv["updated_at"],
                message_count=conv["message_count"]
            )
            for conv in conversations_data
        ]
        
        logger.info(f"Retrieved {len(conversations)} conversations for user {user_id}")
        return conversations
    
    async def get_conversation_with_messages(
        self,
        conversation_id: str,
        user_id: str
    ) -> Optional[ConversationWithMessages]:
        """
        Get a conversation with all its messages.
        
        Args:
            conversation_id: Conversation ID
            user_id: Firebase UID (for authorization)
            
        Returns:
            Conversation with messages, or None if not found or unauthorized
        """
        conversation_data = await self.repository.get_conversation_with_messages(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not conversation_data:
            logger.warning(f"Conversation {conversation_id} not found for user {user_id}")
            return None
        
        logger.info(f"Retrieved conversation {conversation_id} with {len(conversation_data['messages'])} messages")
        
        return ConversationWithMessages(
            conversation_id=conversation_data["conversation_id"],
            title=conversation_data["title"],
            course_id=conversation_data["course_id"],
            lecture_id=conversation_data["lecture_id"],
            created_at=conversation_data["created_at"],
            updated_at=conversation_data["updated_at"],
            messages=conversation_data["messages"],
            notes=conversation_data.get("notes", "")
        )
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ) -> str:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation ID
            role: 'user' or 'assistant'
            content: Message content
            
        Returns:
            message_id: ID of the created message (as string)
        """
        message_id = await self.repository.add_message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        
        logger.info(f"Added {role} message to conversation {conversation_id}")
        return str(message_id)
    
    async def update_conversation_title(
        self,
        conversation_id: str,
        user_id: str,
        title: str
    ) -> bool:
        """
        Update a conversation's title.
        
        Args:
            conversation_id: Conversation ID
            user_id: Firebase UID (for authorization)
            title: New title
            
        Returns:
            True if successful, False otherwise
        """
        success = await self.repository.update_conversation_title(
            conversation_id=conversation_id,
            user_id=user_id,
            title=title
        )
        
        if success:
            logger.info(f"Updated title for conversation {conversation_id}")
        return success
    
    async def update_conversation_notes(
        self,
        conversation_id: str,
        user_id: str,
        notes: str
    ) -> bool:
        """
        Update a conversation's notes field.
        
        Args:
            conversation_id: Conversation ID
            user_id: Firebase UID (for authorization)
            notes: New notes content
            
        Returns:
            True if successful, False otherwise
        """
        success = await self.repository.update_conversation_notes(
            conversation_id=conversation_id,
            user_id=user_id,
            notes=notes
        )
        
        if success:
            logger.info(f"Updated notes for conversation {conversation_id}")
        return success
    
    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a conversation and all its messages.
        
        Args:
            conversation_id: Conversation ID
            user_id: Firebase UID (for authorization)
            
        Returns:
            True if successful, False otherwise
        """
        success = await self.repository.delete_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if success:
            logger.info(f"Deleted conversation {conversation_id}")
        return success
    
    async def get_conversation_messages_for_rag(
        self,
        conversation_id: str
    ) -> List[Dict[str, str]]:
        """
        Get messages in format suitable for RAG backend.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of messages in {'role': ..., 'content': ...} format
        """
        return await self.repository.get_messages_for_rag(conversation_id)


def get_conversation_service(pool: asyncpg.Pool) -> ConversationService:
    """
    Factory function to create ConversationService.
    
    Args:
        pool: AsyncPG connection pool
        
    Returns:
        ConversationService instance
    """
    return ConversationService(pool)
