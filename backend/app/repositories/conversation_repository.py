"""
Conversation repository - PostgreSQL queries for conversation and message data access.
Provides a clean abstraction layer over the database for chat functionality.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import UUID, uuid4
import asyncpg

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Repository for conversation-related database operations using PostgreSQL."""
    
    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize repository with connection pool.
        
        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool
    
    # ==================== Conversation Operations ====================
    
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
            conversation_id: UUID string for the new conversation
        """
        conversation_id = uuid4()
        now = datetime.now(timezone.utc)
        
        query = """
            INSERT INTO conversations (
                conversation_id, user_id, course_id, lecture_id,
                title, notes, message_count, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, '', 0, $6, $7)
            RETURNING conversation_id
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                conversation_id,
                user_id,
                course_id,
                lecture_id,
                title,
                now,
                now
            )
            
            result_id = str(row["conversation_id"])
            logger.info(f"Created conversation {result_id} for user {user_id}")
            return result_id
    
    async def get_user_conversations(
        self,
        user_id: str,
        course_id: Optional[str] = None,
        lecture_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
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
        base_query = """
            SELECT 
                conversation_id, title, course_id, lecture_id,
                created_at, updated_at, message_count
            FROM conversations
            WHERE user_id = $1
        """
        
        params = [user_id]
        param_idx = 2
        
        if course_id:
            base_query += f" AND course_id = ${param_idx}"
            params.append(course_id)
            param_idx += 1
        
        if lecture_id:
            base_query += f" AND lecture_id = ${param_idx}"
            params.append(lecture_id)
            param_idx += 1
        
        base_query += f" ORDER BY updated_at DESC LIMIT ${param_idx}"
        params.append(limit)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(base_query, *params)
            
            conversations = []
            for row in rows:
                conversations.append({
                    "conversation_id": str(row["conversation_id"]),
                    "title": row["title"],
                    "course_id": row["course_id"],
                    "lecture_id": row["lecture_id"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "message_count": row["message_count"]
                })
            
            logger.info(f"Retrieved {len(conversations)} conversations for user {user_id}")
            return conversations
    
    async def get_conversation_by_id(
        self,
        conversation_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a conversation by ID (with user authorization check).
        
        Args:
            conversation_id: Conversation UUID string
            user_id: Firebase UID (for authorization)
            
        Returns:
            Conversation dict or None if not found/unauthorized
        """
        query = """
            SELECT 
                conversation_id, user_id, course_id, lecture_id,
                title, notes, message_count, created_at, updated_at
            FROM conversations
            WHERE conversation_id = $1 AND user_id = $2
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, UUID(conversation_id), user_id)
            
            if not row:
                return None
            
            return {
                "conversation_id": str(row["conversation_id"]),
                "user_id": row["user_id"],
                "course_id": row["course_id"],
                "lecture_id": row["lecture_id"],
                "title": row["title"],
                "notes": row["notes"],
                "message_count": row["message_count"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
    
    async def get_conversation_with_messages(
        self,
        conversation_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a conversation with all its messages.
        
        Args:
            conversation_id: Conversation UUID string
            user_id: Firebase UID (for authorization)
            
        Returns:
            Conversation with messages, or None if not found/unauthorized
        """
        # Get conversation metadata
        conversation = await self.get_conversation_by_id(conversation_id, user_id)
        
        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found for user {user_id}")
            return None
        
        # Get all messages
        messages = await self.get_messages(conversation_id)
        
        conversation["messages"] = messages
        
        logger.info(f"Retrieved conversation {conversation_id} with {len(messages)} messages")
        return conversation
    
    async def update_conversation_title(
        self,
        conversation_id: str,
        user_id: str,
        title: str
    ) -> bool:
        """
        Update a conversation's title.
        
        Args:
            conversation_id: Conversation UUID string
            user_id: Firebase UID (for authorization)
            title: New title
            
        Returns:
            True if successful, False otherwise
        """
        query = """
            UPDATE conversations
            SET title = $3, updated_at = $4
            WHERE conversation_id = $1 AND user_id = $2
            RETURNING id
        """
        
        now = datetime.now(timezone.utc)
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, UUID(conversation_id), user_id, title, now)
            
            if row:
                logger.info(f"Updated title for conversation {conversation_id}")
                return True
            return False
    
    async def update_conversation_notes(
        self,
        conversation_id: str,
        user_id: str,
        notes: str
    ) -> bool:
        """
        Update a conversation's notes.
        
        Args:
            conversation_id: Conversation UUID string
            user_id: Firebase UID (for authorization)
            notes: New notes content
            
        Returns:
            True if successful, False otherwise
        """
        query = """
            UPDATE conversations
            SET notes = $3, updated_at = $4
            WHERE conversation_id = $1 AND user_id = $2
            RETURNING id
        """
        
        now = datetime.now(timezone.utc)
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, UUID(conversation_id), user_id, notes, now)
            
            if row:
                logger.info(f"Updated notes for conversation {conversation_id}")
                return True
            return False
    
    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a conversation and all its messages.
        
        Args:
            conversation_id: Conversation UUID string
            user_id: Firebase UID (for authorization)
            
        Returns:
            True if successful, False otherwise
        """
        # Messages are deleted automatically via CASCADE
        query = """
            DELETE FROM conversations
            WHERE conversation_id = $1 AND user_id = $2
            RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, UUID(conversation_id), user_id)
            
            if row:
                logger.info(f"Deleted conversation {conversation_id}")
                return True
            return False
    
    # ==================== Message Operations ====================
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ) -> int:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation UUID string
            role: 'user' or 'assistant'
            content: Message content
            
        Returns:
            message_id: ID of the created message
        """
        now = datetime.now(timezone.utc)
        
        # Insert message
        insert_query = """
            INSERT INTO messages (conversation_id, role, content, timestamp)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """
        
        # Update conversation metadata
        update_query = """
            UPDATE conversations
            SET updated_at = $2, message_count = message_count + 1
            WHERE conversation_id = $1
        """
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Insert message
                row = await conn.fetchrow(
                    insert_query,
                    UUID(conversation_id),
                    role,
                    content,
                    now
                )
                
                # Update conversation
                await conn.execute(update_query, UUID(conversation_id), now)
                
                message_id = row["id"]
                logger.info(f"Added {role} message to conversation {conversation_id}")
                return message_id
    
    async def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all messages for a conversation.
        
        Args:
            conversation_id: Conversation UUID string
            limit: Optional limit on number of messages
            
        Returns:
            List of messages ordered by timestamp
        """
        query = """
            SELECT id, role, content, timestamp
            FROM messages
            WHERE conversation_id = $1
            ORDER BY timestamp ASC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, UUID(conversation_id))
            
            messages = []
            for row in rows:
                messages.append({
                    "id": row["id"],
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"].isoformat()
                })
            
            return messages
    
    async def get_messages_for_rag(
        self,
        conversation_id: str
    ) -> List[Dict[str, str]]:
        """
        Get messages in format suitable for RAG backend.
        
        Args:
            conversation_id: Conversation UUID string
            
        Returns:
            List of messages in {'role': ..., 'content': ...} format
        """
        query = """
            SELECT role, content
            FROM messages
            WHERE conversation_id = $1
            ORDER BY timestamp ASC
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, UUID(conversation_id))
            
            return [{"role": row["role"], "content": row["content"]} for row in rows]



