"""
WebSocket Connection Handler
=============================
Manages real-time bidirectional communication between clients.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import logging
from .database import SessionLocal, get_room, update_room_code

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create WebSocket router
router = APIRouter(tags=["WebSocket"])


# ==================== CONNECTION MANAGER ====================

class ConnectionManager:
    """
    Manages WebSocket connections for collaborative coding
    
    - Maintains active connections per room
    - Handles message broadcasting
    - Manages connection lifecycle
    """
    
    def __init__(self):
        # Dictionary: room_id -> List[WebSocket connections]
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str):
        """
        Accept new WebSocket connection and add to room
        
        Args:
            websocket: WebSocket connection object
            room_id: Room to join
        """
        await websocket.accept()
        
        # Initialize room connection list if needed
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        
        # Add connection to room
        self.active_connections[room_id].append(websocket)
        
        logger.info(f"✓ Client connected to room '{room_id}' | Total: {len(self.active_connections[room_id])}")
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        """
        Remove connection from room
        
        Args:
            websocket: WebSocket connection to remove
            room_id: Room to leave
        """
        if room_id in self.active_connections:
            try:
                self.active_connections[room_id].remove(websocket)
                logger.info(f"✗ Client disconnected from room '{room_id}' | Remaining: {len(self.active_connections[room_id])}")
                
                # Clean up empty rooms
                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]
                    logger.info(f"Room '{room_id}' is now empty - cleaned up")
            except ValueError:
                pass  # Connection already removed
    
    async def broadcast(self, room_id: str, message: dict, sender: WebSocket = None):
        """
        Broadcast message to all clients in room (except sender)
        
        Args:
            room_id: Target room
            message: Message dictionary to send
            sender: WebSocket of sender (excluded from broadcast)
        """
        if room_id not in self.active_connections:
            return
        
        # Send to all connections except sender
        disconnected = []
        for connection in self.active_connections[room_id]:
            if connection != sender:  # Don't echo back to sender
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn, room_id)
    
    async def broadcast_to_all(self, room_id: str, message: dict):
        """
        Broadcast message to ALL clients in room (including sender)
        
        Args:
            room_id: Target room
            message: Message dictionary to send
        """
        if room_id not in self.active_connections:
            return
        
        # Send to all connections
        disconnected = []
        for connection in self.active_connections[room_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn, room_id)
    
    def get_room_user_count(self, room_id: str) -> int:
        """Get number of active users in room"""
        return len(self.active_connections.get(room_id, []))


# Global connection manager instance
manager = ConnectionManager()


# ==================== WEBSOCKET ENDPOINT ====================

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """
    WebSocket endpoint for real-time collaboration
    
    Protocol:
        Client -> Server:
            {"type": "code_update", "code": "...", "cursorPosition": 10}
            {"type": "cursor_move", "cursorPosition": 15}
            {"type": "code_output", "output": "...", "error": null}
        
        Server -> Client:
            {"type": "init", "code": "...", "roomId": "..."}
            {"type": "code_update", "code": "...", "cursorPosition": 10}
            {"type": "code_output", "output": "...", "error": null}
            {"type": "user_count", "count": 2}
    
    Args:
        websocket: WebSocket connection
        room_id: Room identifier to join
    """
    
    db = SessionLocal()
    
    try:
        # Verify room exists
        room = get_room(db, room_id)
        if not room:
            await websocket.close(code=4004, reason="Room not found")
            logger.warning(f"Connection rejected - Room '{room_id}' not found")
            return
        
        # Accept connection
        await manager.connect(websocket, room_id)
        
        # Send initial state to new client
        await websocket.send_json({
            "type": "init",
            "code": room.code,
            "roomId": room_id,
            "language": room.language
        })
        
        # Broadcast user count update to all users
        user_count = manager.get_room_user_count(room_id)
        await manager.broadcast_to_all(room_id, {
            "type": "user_count",
            "count": user_count
        })
        
        # Message handling loop
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            # Handle code update
            if message_type == "code_update":
                code = message.get("code", "")
                cursor_position = message.get("cursorPosition", 0)
                
                # Persist to database
                update_room_code(db, room_id, code)
                
                # Broadcast to other users
                await manager.broadcast(room_id, {
                    "type": "code_update",
                    "code": code,
                    "cursorPosition": cursor_position
                }, sender=websocket)
                
                logger.debug(f"Code updated in room '{room_id}' | Length: {len(code)} chars")
            
            # Handle cursor movement (optional feature)
            elif message_type == "cursor_move":
                cursor_position = message.get("cursorPosition", 0)
                
                await manager.broadcast(room_id, {
                    "type": "cursor_move",
                    "cursorPosition": cursor_position
                }, sender=websocket)
            
            # Handle code output (NEW - for synchronized output)
            elif message_type == "code_output":
                output = message.get("output")
                error = message.get("error")
                execution_status = message.get("status", "running")
                
                # Broadcast output to ALL users (including sender)
                await manager.broadcast_to_all(room_id, {
                    "type": "code_output",
                    "output": output,
                    "error": error,
                    "status": execution_status
                })
                
                logger.info(f"Code output broadcasted in room '{room_id}'")
    
    except WebSocketDisconnect:
        # Client disconnected normally
        manager.disconnect(websocket, room_id)
        
        # Broadcast updated user count
        user_count = manager.get_room_user_count(room_id)
        await manager.broadcast_to_all(room_id, {
            "type": "user_count",
            "count": user_count
        })
    
    except Exception as e:
        # Unexpected error
        logger.error(f"WebSocket error in room '{room_id}': {e}")
        manager.disconnect(websocket, room_id)
    
    finally:
        db.close()
