"""Service for managing flashcard-specific chat functionality using PostgreSQL."""

import logging
from typing import List, Optional, Dict, Any
import asyncpg

from app.repositories.flashcard_chat_repository import FlashcardChatRepository

logger = logging.getLogger(__name__)


class FlashcardChatService:
    """Service for managing flashcard chats and messages using PostgreSQL."""
    
    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize service with PostgreSQL connection pool.
        
        Args:
            pool: AsyncPG connection pool
        """
        self.repository = FlashcardChatRepository(pool)
    
    async def get_or_create_chat(
        self,
        user_id: str,
        flashcard_id: str,
        course_id: str,
        lecture_id: str,
        flashcard_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get existing chat for a flashcard or create a new one.
        On first message, the flashcard_context is stored permanently.
        
        Args:
            user_id: Firebase UID of the user
            flashcard_id: Flashcard identifier
            course_id: Course identifier
            lecture_id: Lecture identifier
            flashcard_context: The flashcard content (only stored on creation)
            
        Returns:
            Chat data including chat_id
        """
        # Check if chat already exists
        existing_chat = await self.repository.get_chat_by_flashcard_id(
            user_id=user_id,
            flashcard_id=flashcard_id
        )
        
        if existing_chat:
            logger.info(f"Found existing chat for flashcard {flashcard_id}")
            return existing_chat
        
        # Create new chat with context stored
        chat_id = await self.repository.create_chat(
            user_id=user_id,
            course_id=course_id,
            lecture_id=lecture_id,
            flashcard_id=flashcard_id,
            flashcard_context=flashcard_context
        )
        
        logger.info(f"Created new chat {chat_id} for flashcard {flashcard_id}")
        
        return {
            "chat_id": chat_id,
            "user_id": user_id,
            "course_id": course_id,
            "lecture_id": lecture_id,
            "flashcard_id": flashcard_id,
            "flashcard_context": flashcard_context,
            "message_count": 0,
            "messages": []
        }
    
    async def get_chat_with_messages(
        self,
        user_id: str,
        flashcard_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a flashcard chat with all its messages.
        
        Args:
            user_id: Firebase UID
            flashcard_id: Flashcard identifier
            
        Returns:
            Chat with messages, or None if not found
        """
        chat_data = await self.repository.get_chat_with_messages(
            user_id=user_id,
            flashcard_id=flashcard_id
        )
        
        if not chat_data:
            logger.info(f"No chat found for flashcard {flashcard_id}")
            return None
        
        logger.info(f"Retrieved chat with {len(chat_data.get('messages', []))} messages")
        return chat_data
    
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
        message_id = await self.repository.add_message(
            chat_id=chat_id,
            role=role,
            content=content
        )
        
        logger.info(f"Added {role} message to flashcard chat {chat_id}")
        return message_id
    
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
        success = await self.repository.delete_chat(
            user_id=user_id,
            flashcard_id=flashcard_id
        )
        
        if success:
            logger.info(f"Deleted chat for flashcard {flashcard_id}")
        return success
    
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
        return await self.repository.get_messages_for_rag(chat_id)
    
    async def get_flashcard_context(
        self,
        user_id: str,
        flashcard_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the stored flashcard context for a chat.
        
        Args:
            user_id: Firebase UID
            flashcard_id: Flashcard identifier
            
        Returns:
            Flashcard context dict or None if chat doesn't exist
        """
        chat = await self.repository.get_chat_by_flashcard_id(
            user_id=user_id,
            flashcard_id=flashcard_id
        )
        
        if chat:
            return chat.get("flashcard_context")
        return None
    
    async def get_user_flashcard_chats(
        self,
        user_id: str,
        course_id: Optional[str] = None,
        lecture_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all flashcard chats for a user.
        
        Args:
            user_id: Firebase UID
            course_id: Optional course filter
            lecture_id: Optional lecture filter
            limit: Maximum number of chats to return
            
        Returns:
            List of chat summaries
        """
        chats = await self.repository.get_user_flashcard_chats(
            user_id=user_id,
            course_id=course_id,
            lecture_id=lecture_id,
            limit=limit
        )
        
        logger.info(f"Retrieved {len(chats)} flashcard chats for user {user_id}")
        return chats
    
    def build_system_prompt_with_flashcard_context(
        self,
        flashcard_context: Dict[str, Any]
    ) -> str:
        """
        Build system prompt that includes flashcard context for RAG.
        
        Args:
            flashcard_context: The stored flashcard content
            
        Returns:
            System prompt string to prepend to RAG requests
        """
        question = flashcard_context.get("question", "")
        concise = flashcard_context.get("concise", "")
        detailed = flashcard_context.get("detailed", "")
        eli5 = flashcard_context.get("eli5", "")
        examples = flashcard_context.get("examples", "")
        
        prompt_parts = [
            "The user is studying a flashcard with the following content:\n",
            f"QUESTION: {question}\n\n",
            "ANSWERS:"
        ]
        
        if concise:
            prompt_parts.append(f"\n- Concise: {concise}")
        if detailed:
            prompt_parts.append(f"\n- Detailed: {detailed}")
        if eli5:
            prompt_parts.append(f"\n- ELI5: {eli5}")
        if examples:
            prompt_parts.append(f"\n- Examples: {examples}")
        
        prompt_parts.append(
            "\n\nAnswer the user's questions based on this flashcard "
            "and the broader lecture materials. Provide clear, helpful explanations."
        )
        
        return "".join(prompt_parts)


def get_flashcard_chat_service(pool: asyncpg.Pool) -> FlashcardChatService:
    """
    Factory function to create FlashcardChatService.
    
    Args:
        pool: AsyncPG connection pool
        
    Returns:
        FlashcardChatService instance
    """
    return FlashcardChatService(pool)

