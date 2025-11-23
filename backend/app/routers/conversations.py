"""API endpoints for AI Tutor conversation management."""

import logging
import httpx
import json
from typing import List, Dict, Any, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.firebase_auth import get_current_user
from app.services.conversation_service import ConversationService
from app.models.conversation import (
    CreateConversationRequest,
    SendMessageRequest,
    SendMessageResponse,
    ConversationSummary,
    ConversationWithMessages
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tutor/conversations", tags=["conversations"])


def get_conversation_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ConversationService:
    """Dependency to get conversation service."""
    return ConversationService(db)


@router.post("", response_model=Dict[str, str])
async def create_conversation(
    request: CreateConversationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service)
):
    """
    Create a new conversation.
    
    Returns the conversation_id of the newly created conversation.
    """
    try:
        user_id = current_user.get("uid")
        conversation_id = await service.create_conversation(
            user_id=user_id,
            course_id=request.course_id,
            lecture_id=request.lecture_id
        )
        
        return {"conversation_id": conversation_id}
    
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[ConversationSummary])
async def get_conversations(
    course_id: str = Query(None, description="Filter by course ID"),
    lecture_id: str = Query(None, description="Filter by lecture ID"),
    limit: int = Query(50, description="Maximum number of conversations to return"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service)
):
    """
    Get all conversations for the current user.
    
    Can be filtered by course_id and/or lecture_id.
    Returns conversations ordered by most recent first.
    """
    try:
        user_id = current_user.get("uid")
        conversations = await service.get_user_conversations(
            user_id=user_id,
            course_id=course_id,
            lecture_id=lecture_id,
            limit=limit
        )
        
        return conversations
    
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service)
):
    """
    Get a specific conversation with all its messages.
    
    Returns 404 if conversation not found or user is not authorized.
    """
    try:
        user_id = current_user.get("uid")
        conversation = await service.get_conversation_with_messages(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found or unauthorized"
            )
        
        return conversation
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service)
):
    """
    Delete a conversation and all its messages.
    
    Returns 404 if conversation not found or user is not authorized.
    """
    try:
        user_id = current_user.get("uid")
        success = await service.delete_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found or unauthorized"
            )
        
        return {"message": "Conversation deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: str,
    request: Dict[str, str],
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service)
):
    """
    Update a conversation's title.
    
    Request body: {"title": "New Title"}
    """
    try:
        user_id = current_user.get("uid")
        title = request.get("title", "").strip()
        
        if not title:
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        
        success = await service.update_conversation_title(
            conversation_id=conversation_id,
            user_id=user_id,
            title=title
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found or unauthorized"
            )
        
        return {"message": "Title updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation title: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{conversation_id}/notes")
async def update_conversation_notes(
    conversation_id: str,
    request: Dict[str, str],
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service)
):
    """
    Update a conversation's notes.
    """
    try:
        user_id = current_user.get("uid")
        notes = request.get("notes")

        if notes is None:
            raise HTTPException(status_code=400, detail="Notes content is required")

        success = await service.update_conversation_notes(
            conversation_id=conversation_id,
            user_id=user_id,
            notes=notes
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found or unauthorized"
            )

        return {"message": "Notes updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/stream")
async def stream_message(
    conversation_id: str,
    request: Dict[str, str],
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service)
):
    """
    Send a message and stream the AI response chunk by chunk.
    """
    try:
        user_id = current_user.get("uid")
        message_text = request.get("message", "").strip()
        
        if not message_text:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get conversation
        conversation = await service.get_conversation_with_messages(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Save user message first
        await service.add_message(
            conversation_id=conversation_id,
            role="user",
            content=message_text
        )
        
        # Define generator for streaming
        async def response_generator() -> AsyncGenerator[bytes, None]:
            full_response = ""
            base_url = settings.RAG_API_BASE_URL.rstrip('/')
            
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream(
                        "POST",
                        f"{base_url}/chat/{conversation.course_id}/stream",
                        json={
                            "message": message_text,
                            "session_id": conversation_id
                        }
                    ) as response:
                        response.raise_for_status()
                        async for chunk in response.aiter_bytes():
                            # Accumulate full response for saving later
                            text_chunk = chunk.decode("utf-8")
                            full_response += text_chunk
                            yield chunk
                            
                # Save the full AI response to database after streaming is done
                # Note: We need a new service instance or context here if the generator runs after the request scope
                # But since we are inside the endpoint, we can use 'service'
                await service.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response
                )
                
                # Auto-generate title if needed
                if len(conversation.messages) == 0:
                    auto_title = message_text[:50] + ("..." if len(message_text) > 50 else "")
                    await service.update_conversation_title(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        title=auto_title
                    )
                    
            except Exception as e:
                logger.error(f"Error during streaming: {e}")
                yield f"\n[Error: {str(e)}]".encode("utf-8")

        return StreamingResponse(response_generator(), media_type="text/plain")

    except Exception as e:
        logger.error(f"Error setting up stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/messages", response_model=SendMessageResponse)
async def send_message(
    conversation_id: str,
    request: Dict[str, str],
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service)
):
    """
    Send a message in a conversation and get AI response.
    
    This endpoint:
    1. Verifies the user owns the conversation
    2. Saves the user's message
    3. Calls the RAG backend to get AI response
    4. Saves the AI's response
    5. Auto-generates a title if this is the first message
    
    Request body: {"message": "User's question"}
    """
    try:
        user_id = current_user.get("uid")
        message_text = request.get("message", "").strip()
        
        if not message_text:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get conversation to verify ownership and get course/lecture info
        conversation = await service.get_conversation_with_messages(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found or unauthorized"
            )
        
        # Save user message
        user_message_id = await service.add_message(
            conversation_id=conversation_id,
            role="user",
            content=message_text
        )
        
        # Call RAG backend
        try:
            # Strip trailing slash from base URL to avoid double slashes
            base_url = settings.RAG_API_BASE_URL.rstrip('/')
            async with httpx.AsyncClient(timeout=60.0) as client:
                rag_response = await client.post(
                    f"{base_url}/chat/{conversation.course_id}",
                    json={
                        "message": message_text,
                        "session_id": conversation_id  # Use conversation_id as session_id
                    }
                )
                rag_response.raise_for_status()
                rag_data = rag_response.json()
                ai_answer = rag_data.get("answer", "")
        
        except httpx.HTTPError as e:
            logger.error(f"Error calling RAG backend: {e}")
            # Delete the user message since we couldn't get a response
            await service.messages_collection.delete_one({"_id": user_message_id})
            raise HTTPException(
                status_code=500,
                detail="Failed to get AI response. Please try again."
            )
        
        # Save AI response
        await service.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=ai_answer
        )
        
        # Auto-generate title if this is the first user message
        # conversation.messages contains the messages BEFORE we added the new ones
        if len(conversation.messages) == 0:
            # Use first 50 characters of user message as title
            auto_title = message_text[:50] + ("..." if len(message_text) > 50 else "")
            await service.update_conversation_title(
                conversation_id=conversation_id,
                user_id=user_id,
                title=auto_title
            )
        
        return SendMessageResponse(
            conversation_id=conversation_id,
            message_id=user_message_id,
            answer=ai_answer
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

