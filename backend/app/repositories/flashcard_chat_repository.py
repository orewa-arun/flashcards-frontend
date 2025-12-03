"""
Flashcard Chat repository - PostgreSQL queries for flashcard-specific chat functionality.
This is separate from the AI Tutor conversations to provide focused chat per flashcard.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import UUID, uuid4
import asyncpg

logger = logging.getLogger(__name__)


class FlashcardChatRepository:
    """Repository for flashcard chat database operations using PostgreSQL."""
    
    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize repository with connection pool.
        
        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool
    
    # ==================== Chat Operations ====================
    
    async def create_chat(
        self,
        user_id: str,
        course_id: str,
        lecture_id: str,
        flashcard_id: str,
        flashcard_context: Dict[str, Any]
    ) -> str:
        """
        Create a new flashcard chat session.
        
        Args:
            user_id: Firebase UID of the user
            course_id: Course identifier
            lecture_id: Lecture identifier
            flashcard_id: Flashcard identifier
            flashcard_context: The flashcard content at chat creation time
            
        Returns:
            chat_id: UUID string for the new chat
        """
        chat_id = uuid4()
        now = datetime.now(timezone.utc)
        
        query = """
            INSERT INTO flashcard_chats (
                chat_id, user_id, course_id, lecture_id, flashcard_id,
                flashcard_context, message_count, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, 0, $7, $8)
            RETURNING chat_id
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                chat_id,
                user_id,
                course_id,
                lecture_id,
                flashcard_id,
                json.dumps(flashcard_context),
                now,
                now
            )
            
            result_id = str(row["chat_id"])
            logger.info(f"Created flashcard chat {result_id} for user {user_id}, flashcard {flashcard_id}")
            return result_id
    
    async def get_chat_by_flashcard_id(
        self,
        user_id: str,
        flashcard_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a chat by user and flashcard ID.
        
        Args:
            user_id: Firebase UID
            flashcard_id: Flashcard identifier
            
        Returns:
            Chat dict or None if not found
        """
        query = """
            SELECT 
                chat_id, user_id, course_id, lecture_id, flashcard_id,
                flashcard_context, message_count, created_at, updated_at
            FROM flashcard_chats
            WHERE user_id = $1 AND flashcard_id = $2
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, flashcard_id)
            
            if not row:
                return None
            
            return {
                "chat_id": str(row["chat_id"]),
                "user_id": row["user_id"],
                "course_id": row["course_id"],
                "lecture_id": row["lecture_id"],
                "flashcard_id": row["flashcard_id"],
                "flashcard_context": json.loads(row["flashcard_context"]) if row["flashcard_context"] else {},
                "message_count": row["message_count"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
    
    async def get_chat_by_id(
        self,
        chat_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a chat by ID (with user authorization check).
        
        Args:
            chat_id: Chat UUID string
            user_id: Firebase UID (for authorization)
            
        Returns:
            Chat dict or None if not found/unauthorized
        """
        query = """
            SELECT 
                chat_id, user_id, course_id, lecture_id, flashcard_id,
                flashcard_context, message_count, created_at, updated_at
            FROM flashcard_chats
            WHERE chat_id = $1 AND user_id = $2
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, UUID(chat_id), user_id)
            
            if not row:
                return None
            
            return {
                "chat_id": str(row["chat_id"]),
                "user_id": row["user_id"],
                "course_id": row["course_id"],
                "lecture_id": row["lecture_id"],
                "flashcard_id": row["flashcard_id"],
                "flashcard_context": json.loads(row["flashcard_context"]) if row["flashcard_context"] else {},
                "message_count": row["message_count"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
    
    async def get_chat_with_messages(
        self,
        user_id: str,
        flashcard_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a chat with all its messages by flashcard ID.
        
        Args:
            user_id: Firebase UID
            flashcard_id: Flashcard identifier
            
        Returns:
            Chat with messages, or None if not found
        """
        # Get chat metadata
        chat = await self.get_chat_by_flashcard_id(user_id, flashcard_id)
        
        if not chat:
            return None
        
        # Get all messages
        messages = await self.get_messages(chat["chat_id"])
        
        chat["messages"] = messages
        
        logger.info(f"Retrieved flashcard chat with {len(messages)} messages")
        return chat
    
    async def delete_chat(
        self,
        user_id: str,
        flashcard_id: str
    ) -> bool:
        """
        Delete a flashcard chat and all its messages.
        
        Args:
            user_id: Firebase UID (for authorization)
            flashcard_id: Flashcard identifier
            
        Returns:
            True if successful, False otherwise
        """
        # Messages are deleted automatically via CASCADE
        query = """
            DELETE FROM flashcard_chats
            WHERE user_id = $1 AND flashcard_id = $2
            RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, flashcard_id)
            
            if row:
                logger.info(f"Deleted flashcard chat for user {user_id}, flashcard {flashcard_id}")
                return True
            return False
    
    async def get_user_flashcard_chats(
        self,
        user_id: str,
        course_id: Optional[str] = None,
        lecture_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all flashcard chats for a user, optionally filtered.
        
        Args:
            user_id: Firebase UID
            course_id: Optional course filter
            lecture_id: Optional lecture filter
            limit: Maximum number of chats to return
            
        Returns:
            List of chat summaries, ordered by most recent first
        """
        base_query = """
            SELECT 
                chat_id, flashcard_id, course_id, lecture_id,
                flashcard_context, created_at, updated_at, message_count
            FROM flashcard_chats
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
            
            chats = []
            for row in rows:
                chats.append({
                    "chat_id": str(row["chat_id"]),
                    "flashcard_id": row["flashcard_id"],
                    "course_id": row["course_id"],
                    "lecture_id": row["lecture_id"],
                    "flashcard_context": json.loads(row["flashcard_context"]) if row["flashcard_context"] else {},
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "message_count": row["message_count"]
                })
            
            logger.info(f"Retrieved {len(chats)} flashcard chats for user {user_id}")
            return chats
    
    # ==================== Message Operations ====================
    
    async def add_message(
        self,
        chat_id: str,
        role: str,
        content: str
    ) -> int:
        """
        Add a message to a flashcard chat.
        
        Args:
            chat_id: Chat UUID string
            role: 'user' or 'assistant'
            content: Message content
            
        Returns:
            message_id: ID of the created message
        """
        now = datetime.now(timezone.utc)
        
        # Insert message
        insert_query = """
            INSERT INTO flashcard_chat_messages (chat_id, role, content, timestamp)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """
        
        # Update chat metadata
        update_query = """
            UPDATE flashcard_chats
            SET updated_at = $2, message_count = message_count + 1
            WHERE chat_id = $1
        """
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Insert message
                row = await conn.fetchrow(
                    insert_query,
                    UUID(chat_id),
                    role,
                    content,
                    now
                )
                
                # Update chat
                await conn.execute(update_query, UUID(chat_id), now)
                
                message_id = row["id"]
                logger.info(f"Added {role} message to flashcard chat {chat_id}")
                return message_id
    
    async def get_messages(
        self,
        chat_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all messages for a flashcard chat.
        
        Args:
            chat_id: Chat UUID string
            limit: Optional limit on number of messages
            
        Returns:
            List of messages ordered by timestamp
        """
        query = """
            SELECT id, role, content, timestamp
            FROM flashcard_chat_messages
            WHERE chat_id = $1
            ORDER BY timestamp ASC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, UUID(chat_id))
            
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
        chat_id: str
    ) -> List[Dict[str, str]]:
        """
        Get messages in format suitable for RAG backend.
        
        Args:
            chat_id: Chat UUID string
            
        Returns:
            List of messages in {'role': ..., 'content': ...} format
        """
        query = """
            SELECT role, content
            FROM flashcard_chat_messages
            WHERE chat_id = $1
            ORDER BY timestamp ASC
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, UUID(chat_id))
            
            return [{"role": row["role"], "content": row["content"]} for row in rows]

