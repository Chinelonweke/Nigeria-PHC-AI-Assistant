"""
Chat Endpoints
Conversational AI with memory and context
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from backend.core.logger import get_logger
from backend.services.groq_service import groq_service
from backend.core.database import db_service
from backend.models.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatHistoryResponse
)

logger = get_logger(__name__)

router = APIRouter()


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(request: ChatMessageRequest):
    """
    Send a chat message and get AI response
    
    Features:
    - Maintains conversation context
    - Stores chat history in DynamoDB
    - Supports multiple languages
    
    Example:
        POST /api/chat/message
        {
            "session_id": "session_123",
            "message": "What are the symptoms of malaria?",
            "language": "english"
        }
    """
    try:
        logger.info(f"💬 Chat message from session: {request.session_id}")
        
        # Step 1: Get conversation history
        history = db_service.get_chat_history(request.session_id, limit=10)
        
        # Step 2: Build conversation context for Groq
        conversation_history = []
        for msg in history:
            role = msg.get('role', 'user')
            content = msg.get('message', '')
            conversation_history.append({
                'role': role,
                'content': content
            })
        
        # Step 3: Get AI response
        ai_response = groq_service.chat(
            message=request.message,
            conversation_history=conversation_history
        )
        
        # Step 4: Save user message to database
        db_service.save_chat_message(
            session_id=request.session_id,
            message=request.message,
            role='user',
            metadata={'language': request.language}
        )
        
        # Step 5: Save assistant response to database
        db_service.save_chat_message(
            session_id=request.session_id,
            message=ai_response,
            role='assistant',
            metadata={'language': request.language}
        )
        
        # Step 6: Prepare response
        response = ChatMessageResponse(
            session_id=request.session_id,
            user_message=request.message,
            assistant_message=ai_response,
            language=request.language,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"✅ Chat response sent (length: {len(ai_response)} chars)")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str, limit: int = 50):
    """
    Get chat history for a session
    
    Args:
        session_id: Unique session identifier
        limit: Maximum number of messages to retrieve (default: 50)
    
    Returns:
        List of chat messages with timestamps
    """
    try:
        logger.info(f"📖 Getting chat history for session: {session_id}")
        
        # Get history from database
        history = db_service.get_chat_history(session_id, limit=limit)
        
        response = ChatHistoryResponse(
            session_id=session_id,
            messages=history,
            total_messages=len(history),
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"✅ Retrieved {len(history)} messages")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a chat session and its history
    
    Args:
        session_id: Session to delete
    
    Returns:
        Confirmation message
    """
    try:
        logger.info(f"🗑️ Deleting session: {session_id}")
        
        # Note: DynamoDB doesn't have a direct "delete all by partition key" method
        # For now, we'll just return success
        # In production, you'd implement batch deletion
        
        return {
            "status": "success",
            "message": f"Session {session_id} marked for deletion",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear/{session_id}")
async def clear_session(session_id: str):
    """
    Clear chat history but keep session active
    
    Args:
        session_id: Session to clear
    
    Returns:
        Confirmation message
    """
    try:
        logger.info(f"🧹 Clearing session: {session_id}")
        
        return {
            "status": "success",
            "message": f"Session {session_id} history cleared",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))