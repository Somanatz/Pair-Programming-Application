"""
Pair Programming Application Package
====================================
A real-time collaborative coding platform with WebSocket support.
"""

__version__ = "1.0.0"
__author__ = "Your Name"

# Package-level imports for easier access
from .models import (
    RoomCreateRequest,
    RoomCreateResponse,
    AutocompleteRequest,
    AutocompleteResponse
)
from .database import get_db, init_database, Room

__all__ = [
    "Room",
    "RoomCreateRequest",
    "RoomCreateResponse",
    "AutocompleteRequest",
    "AutocompleteResponse",
    "get_db",
    "init_database"
]
