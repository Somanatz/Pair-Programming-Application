"""
REST API Endpoints
==================
Handles HTTP requests for room creation and autocomplete.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .database import get_db, create_room as db_create_room, get_room
from .models import (
    RoomCreateRequest, 
    RoomCreateResponse,
    AutocompleteRequest, 
    AutocompleteResponse,
    get_mock_autocomplete
)

# Create API router
router = APIRouter(prefix="/api", tags=["API"])


# ==================== ROOM ENDPOINTS ====================

@router.post(
    "/rooms",
    response_model=RoomCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Room",
    description="Creates a new collaborative coding room with a unique ID"
)
async def create_new_room(
    request: RoomCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new coding room
    
    - Generates unique 8-character room ID
    - Initializes empty code editor
    - Persists room to database
    
    Returns:
        RoomCreateResponse with roomId
    """
    try:
        room_id = db_create_room(db, request.language)
        return RoomCreateResponse(
            roomId=room_id,
            message=f"Room '{room_id}' created successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create room: {str(e)}"
        )


@router.get(
    "/rooms/{room_id}",
    summary="Get Room Details",
    description="Retrieve room information by ID"
)
async def get_room_details(
    room_id: str,
    db: Session = Depends(get_db)
):
    """
    Get room details by ID
    
    Args:
        room_id: 8-character room identifier
        
    Returns:
        Room details including current code and metadata
    """
    room = get_room(db, room_id)
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room '{room_id}' not found"
        )
    
    return {
        "roomId": room.room_id,
        "language": room.language,
        "code": room.code,
        "createdAt": room.created_at.isoformat(),
        "updatedAt": room.updated_at.isoformat()
    }


# ==================== AUTOCOMPLETE ENDPOINT ====================

@router.post(
    "/autocomplete",
    response_model=AutocompleteResponse,
    summary="Get Code Suggestions",
    description="Returns AI-powered code completion suggestions (mocked for prototype)"
)
async def get_autocomplete(request: AutocompleteRequest):
    """
    Get autocomplete suggestions for current code
    
    - Analyzes code context at cursor position
    - Returns relevant code snippet suggestions
    - Mock implementation (production would use OpenAI Codex/Copilot)
    
    Args:
        request: AutocompleteRequest with code and cursor position
        
    Returns:
        AutocompleteResponse with suggestion and confidence
    """
    try:
        result = get_mock_autocomplete(
            request.code,
            request.cursorPosition,
            request.language
        )
        return AutocompleteResponse(**result)
    
    except Exception as e:
        # Return empty suggestion on error
        return AutocompleteResponse(
            suggestion="",
            confidence=0.0
        )


# ==================== HEALTH CHECK ====================

@router.get(
    "/health",
    summary="Health Check",
    description="Check if API is running"
)
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "service": "Pair Programming API",
        "version": "1.0.0"
    }
