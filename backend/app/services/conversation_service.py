"""Service for managing AI Tutor conversations."""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.models.conversation import (
    Conversation,
    Message,
    ConversationSummary,
    ConversationWithMessages
)

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations and messages."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.conversations_collection = database.tutor_conversations
        self.messages_collection = database.tutor_messages
    
    async def initialize_indexes(self):
        """Create necessary indexes for efficient querying."""
        # Conversation indexes
        await self.conversations_collection.create_index(
            [("conversation_id", 1)], 
            unique=True
        )
        await self.conversations_collection.create_index(
            [("user_id", 1), ("updated_at", -1)]
        )
        await self.conversations_collection.create_index(
            [("user_id", 1), ("course_id", 1), ("lecture_id", 1)]
        )
        
        # Message indexes
        await self.messages_collection.create_index(
            [("conversation_id", 1), ("timestamp", 1)]
        )
        
        logger.info("✅ Conversation indexes created")
    
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
        conversation_id = str(uuid4())
        
        conversation = Conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            course_id=course_id,
            lecture_id=lecture_id,
            title=title,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            message_count=0
        )
        
        try:
            await self.conversations_collection.insert_one(
                conversation.model_dump(by_alias=True, exclude={"id"})
            )
            logger.info(f"✅ Created conversation {conversation_id} for user {user_id}")
            return conversation_id
        except DuplicateKeyError:
            logger.error(f"❌ Conversation {conversation_id} already exists")
            raise ValueError("Conversation ID already exists")
    
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
        query = {"user_id": user_id}
        
        if course_id:
            query["course_id"] = course_id
        if lecture_id:
            query["lecture_id"] = lecture_id
        
        cursor = self.conversations_collection.find(query).sort(
            "updated_at", -1
        ).limit(limit)
        
        conversations = []
        async for doc in cursor:
            conversations.append(ConversationSummary(
                conversation_id=doc["conversation_id"],
                title=doc["title"],
                course_id=doc["course_id"],
                lecture_id=doc["lecture_id"],
                created_at=doc["created_at"],
                updated_at=doc["updated_at"],
                message_count=doc.get("message_count", 0)
            ))
        
        logger.info(f"📚 Retrieved {len(conversations)} conversations for user {user_id}")
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
        # Get conversation metadata
        conversation_doc = await self.conversations_collection.find_one({
            "conversation_id": conversation_id,
            "user_id": user_id
        })
        
        if not conversation_doc:
            logger.warning(f"⚠️ Conversation {conversation_id} not found for user {user_id}")
            return None
        
        # Get all messages for this conversation
        messages_cursor = self.messages_collection.find({
            "conversation_id": conversation_id
        }).sort("timestamp", 1)
        
        messages = []
        async for msg in messages_cursor:
            messages.append({
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"].isoformat()
            })
        
        logger.info(f"💬 Retrieved conversation {conversation_id} with {len(messages)} messages")
        
        return ConversationWithMessages(
            conversation_id=conversation_doc["conversation_id"],
            title=conversation_doc["title"],
            course_id=conversation_doc["course_id"],
            lecture_id=conversation_doc["lecture_id"],
            created_at=conversation_doc["created_at"],
            updated_at=conversation_doc["updated_at"],
            messages=messages
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
            message_id: ID of the created message
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc)
        )
        
        result = await self.messages_collection.insert_one(
            message.model_dump(by_alias=True, exclude={"id"})
        )
        
        # Update conversation's updated_at and message_count
        await self.conversations_collection.update_one(
            {"conversation_id": conversation_id},
            {
                "$set": {"updated_at": datetime.now(timezone.utc)},
                "$inc": {"message_count": 1}
            }
        )
        
        message_id = str(result.inserted_id)
        logger.info(f"💬 Added {role} message to conversation {conversation_id}")
        return message_id
    
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
        result = await self.conversations_collection.update_one(
            {"conversation_id": conversation_id, "user_id": user_id},
            {"$set": {"title": title, "updated_at": datetime.now(timezone.utc)}}
        )
        
        if result.modified_count > 0:
            logger.info(f"✏️ Updated title for conversation {conversation_id}")
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
            conversation_id: Conversation ID
            user_id: Firebase UID (for authorization)
            
        Returns:
            True if successful, False otherwise
        """
        # Delete all messages
        await self.messages_collection.delete_many({
            "conversation_id": conversation_id
        })
        
        # Delete conversation
        result = await self.conversations_collection.delete_one({
            "conversation_id": conversation_id,
            "user_id": user_id
        })
        
        if result.deleted_count > 0:
            logger.info(f"🗑️ Deleted conversation {conversation_id}")
            return True
        return False
    
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
        messages_cursor = self.messages_collection.find({
            "conversation_id": conversation_id
        }).sort("timestamp", 1)
        
        messages = []
        async for msg in messages_cursor:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return messages

