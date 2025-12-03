"""API endpoints for flashcard-specific chat functionality using PostgreSQL."""

import logging
import httpx
from typing import List, Dict, Any, Optional, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncpg

from app.db.postgres import get_postgres_pool
from app.firebase_auth import get_current_user
from app.services.flashcard_chat_service import FlashcardChatService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/flashcard-chat", tags=["flashcard-chat"])


# ==================== Pydantic Models ====================

class FlashcardContext(BaseModel):
    """Flashcard content for context."""
    question: str
    concise: Optional[str] = None
    detailed: Optional[str] = None
    eli5: Optional[str] = None
    examples: Optional[str] = None


class SendMessageRequest(BaseModel):
    """Request to send a message in a flashcard chat."""
    flashcard_id: str
    course_id: str
    lecture_id: str
    message: str
    flashcard_context: Optional[FlashcardContext] = None


class ChatResponse(BaseModel):
    """Response containing chat details."""
    chat_id: str
    flashcard_id: str
    course_id: str
    lecture_id: str
    flashcard_context: Dict[str, Any]
    message_count: int
    messages: List[Dict[str, Any]]


class MessageResponse(BaseModel):
    """Response after sending a message."""
    chat_id: str
    message_id: int
    answer: str


# ==================== Dependencies ====================

async def get_flashcard_chat_service() -> FlashcardChatService:
    """Dependency to get flashcard chat service with PostgreSQL pool."""
    pool = await get_postgres_pool()
    return FlashcardChatService(pool)


# ==================== Endpoints ====================

@router.get("/{flashcard_id}", response_model=Optional[ChatResponse])
async def get_flashcard_chat(
    flashcard_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: FlashcardChatService = Depends(get_flashcard_chat_service)
):
    """
    Get existing chat for a flashcard.
    
    Returns null if no chat exists for this flashcard.
    """
    try:
        user_id = current_user.get("uid")
        chat = await service.get_chat_with_messages(
            user_id=user_id,
            flashcard_id=flashcard_id
        )
        
        if not chat:
            return None
        
        return ChatResponse(
            chat_id=chat["chat_id"],
            flashcard_id=chat["flashcard_id"],
            course_id=chat["course_id"],
            lecture_id=chat["lecture_id"],
            flashcard_context=chat.get("flashcard_context", {}),
            message_count=chat.get("message_count", 0),
            messages=chat.get("messages", [])
        )
    
    except Exception as e:
        logger.error(f"Error getting flashcard chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send", response_model=MessageResponse)
async def send_message(
    request: SendMessageRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: FlashcardChatService = Depends(get_flashcard_chat_service)
):
    """
    Send a message in a flashcard chat.
    
    If no chat exists, creates one and stores the flashcard context.
    Subsequent messages use the stored context.
    
    This is the non-streaming version.
    """
    try:
        user_id = current_user.get("uid")
        message_text = request.message.strip()
        
        if not message_text:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get or create chat
        flashcard_context_dict = {}
        if request.flashcard_context:
            flashcard_context_dict = request.flashcard_context.model_dump()
        
        chat = await service.get_or_create_chat(
            user_id=user_id,
            flashcard_id=request.flashcard_id,
            course_id=request.course_id,
            lecture_id=request.lecture_id,
            flashcard_context=flashcard_context_dict
        )
        
        chat_id = chat["chat_id"]
        stored_context = chat.get("flashcard_context", {})
        
        # Save user message
        await service.add_message(
            chat_id=chat_id,
            role="user",
            content=message_text
        )
        
        # Build system prompt with flashcard context
        system_prompt = service.build_system_prompt_with_flashcard_context(stored_context)
        
        # Call RAG backend
        try:
            base_url = settings.RAG_API_BASE_URL.rstrip('/')
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Build a session_id that encodes user and flashcard
                session_id = f"{user_id}_flashcard_{request.flashcard_id}"
                
                rag_response = await client.post(
                    f"{base_url}/chat/{request.course_id}",
                    json={
                        "message": f"{system_prompt}\n\nUser question: {message_text}",
                        "session_id": session_id
                    }
                )
                rag_response.raise_for_status()
                rag_data = rag_response.json()
                ai_answer = rag_data.get("answer", "")
        
        except httpx.HTTPError as e:
            logger.error(f"Error calling RAG backend: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to get AI response. Please try again."
            )
        
        # Save AI response
        message_id = await service.add_message(
            chat_id=chat_id,
            role="assistant",
            content=ai_answer
        )
        
        return MessageResponse(
            chat_id=chat_id,
            message_id=message_id,
            answer=ai_answer
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_message(
    request: SendMessageRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: FlashcardChatService = Depends(get_flashcard_chat_service)
):
    """
    Send a message and stream the AI response chunk by chunk.
    
    If no chat exists, creates one and stores the flashcard context.
    """
    try:
        user_id = current_user.get("uid")
        message_text = request.message.strip()
        
        if not message_text:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get or create chat
        flashcard_context_dict = {}
        if request.flashcard_context:
            flashcard_context_dict = request.flashcard_context.model_dump()
        
        chat = await service.get_or_create_chat(
            user_id=user_id,
            flashcard_id=request.flashcard_id,
            course_id=request.course_id,
            lecture_id=request.lecture_id,
            flashcard_context=flashcard_context_dict
        )
        
        chat_id = chat["chat_id"]
        stored_context = chat.get("flashcard_context", {})
        
        # Save user message before streaming
        await service.add_message(
            chat_id=chat_id,
            role="user",
            content=message_text
        )
        
        # Build system prompt with flashcard context
        system_prompt = service.build_system_prompt_with_flashcard_context(stored_context)
        
        # Define generator for streaming
        async def response_generator() -> AsyncGenerator[bytes, None]:
            full_response = ""
            base_url = settings.RAG_API_BASE_URL.rstrip('/')
            
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    session_id = f"{user_id}_flashcard_{request.flashcard_id}"
                    
                    async with client.stream(
                        "POST",
                        f"{base_url}/chat/{request.course_id}/stream",
                        json={
                            "message": f"{system_prompt}\n\nUser question: {message_text}",
                            "session_id": session_id
                        }
                    ) as response:
                        response.raise_for_status()
                        async for chunk in response.aiter_bytes():
                            text_chunk = chunk.decode("utf-8")
                            full_response += text_chunk
                            yield chunk
                
                # Save the full AI response after streaming is done
                await service.add_message(
                    chat_id=chat_id,
                    role="assistant",
                    content=full_response
                )
                
            except Exception as e:
                logger.error(f"Error during streaming: {e}")
                yield f"\n[Error: {str(e)}]".encode("utf-8")
        
        return StreamingResponse(response_generator(), media_type="text/plain")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{flashcard_id}")
async def delete_flashcard_chat(
    flashcard_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: FlashcardChatService = Depends(get_flashcard_chat_service)
):
    """
    Delete a flashcard chat and all its messages.
    
    This allows the user to start fresh with new context.
    """
    try:
        user_id = current_user.get("uid")
        success = await service.delete_chat(
            user_id=user_id,
            flashcard_id=flashcard_id
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Chat not found or unauthorized"
            )
        
        return {"message": "Chat deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting flashcard chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/chats")
async def get_user_flashcard_chats(
    course_id: str = Query(None, description="Filter by course ID"),
    lecture_id: str = Query(None, description="Filter by lecture ID"),
    limit: int = Query(50, description="Maximum number of chats to return"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: FlashcardChatService = Depends(get_flashcard_chat_service)
):
    """
    Get all flashcard chats for the current user.
    
    Can be filtered by course_id and/or lecture_id.
    Returns chats ordered by most recent first.
    """
    try:
        user_id = current_user.get("uid")
        chats = await service.get_user_flashcard_chats(
            user_id=user_id,
            course_id=course_id,
            lecture_id=lecture_id,
            limit=limit
        )
        
        return chats
    
    except Exception as e:
        logger.error(f"Error getting user flashcard chats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

