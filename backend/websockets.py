from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages WebSocket connections for real-time notifications.
    Handles user-to-device logout notifications and device conflict alerts.
    """
    
    def __init__(self):
        # Dictionary to store active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Dictionary to store device_id for each connection (for targeted notifications)
        self.connection_devices: Dict[WebSocket, str] = {}
        # Dictionary to store user_id for each connection
        self.connection_users: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, device_id: str = None):
        """
        Accept a new WebSocket connection and register it for a user.
        
        Args:
            websocket: WebSocket connection object
            user_id: Auth0 user ID
            device_id: Optional device identifier for targeted notifications
        """
        await websocket.accept()
        
        # Initialize user connection list if not exists
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        # Add connection to user's set
        self.active_connections[user_id].add(websocket)
        
        # Store connection metadata
        self.connection_users[websocket] = user_id
        if device_id:
            self.connection_devices[websocket] = device_id
        
        logger.info(f"WebSocket connected for user {user_id}, device {device_id}")
        
        # Send connection confirmation
        await self.send_personal_message(websocket, {
            "type": "connection_established",
            "user_id": user_id,
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "WebSocket connection established"
        })
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """
        Remove a WebSocket connection when client disconnects.
        
        Args:
            websocket: WebSocket connection object
            user_id: Auth0 user ID
        """
        # Remove from user's connections
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Clean up empty user entries
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # Clean up connection metadata
        self.connection_users.pop(websocket, None)
        device_id = self.connection_devices.pop(websocket, None)
        
        logger.info(f"WebSocket disconnected for user {user_id}, device {device_id}")
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """
        Send a message to a specific WebSocket connection.
        
        Args:
            websocket: Target WebSocket connection
            message: Message dictionary to send
        """
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to WebSocket: {e}")
            # Connection might be closed, remove it
            user_id = self.connection_users.get(websocket)
            if user_id:
                self.disconnect(websocket, user_id)
    
    async def send_to_user(self, user_id: str, message: dict):
        """
        Send a message to all connections for a specific user.
        
        Args:
            user_id: Auth0 user ID
            message: Message dictionary to send
        """
        if user_id not in self.active_connections:
            logger.warning(f"No active connections for user {user_id}")
            return
        
        # Send to all user's connections
        connections_to_remove = []
        for websocket in self.active_connections[user_id].copy():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                connections_to_remove.append(websocket)
        
        # Clean up failed connections
        for websocket in connections_to_remove:
            self.disconnect(websocket, user_id)
    
    async def send_to_device(self, user_id: str, device_id: str, message: dict):
        """
        Send a message to a specific device for a user.
        
        Args:
            user_id: Auth0 user ID
            device_id: Target device identifier
            message: Message dictionary to send
        """
        if user_id not in self.active_connections:
            logger.warning(f"No active connections for user {user_id}")
            return
        
        # Find connections for the specific device
        target_connections = []
        for websocket in self.active_connections[user_id]:
            if self.connection_devices.get(websocket) == device_id:
                target_connections.append(websocket)
        
        if not target_connections:
            logger.warning(f"No connections found for user {user_id}, device {device_id}")
            return
        
        # Send to target device connections
        connections_to_remove = []
        for websocket in target_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to device {device_id}: {e}")
                connections_to_remove.append(websocket)
        
        # Clean up failed connections
        for websocket in connections_to_remove:
            self.disconnect(websocket, user_id)
    
    async def send_logout_notification(
        self,
        user_id: str,
        device_id: str = None,
        reason: str = "force_logout",
        message: str = None
    ):
        """
        Send logout notification to user's devices.
        
        Args:
            user_id: Auth0 user ID
            device_id: Optional specific device to target
            reason: Reason for logout (force_logout, session_expired, etc.)
            message: Optional custom message
        """
        logout_message = {
            "type": "logout_notification",
            "reason": reason,
            "user_id": user_id,
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": message or self._get_logout_message(reason),
            "action_required": True
        }
        
        if device_id:
            # Send to specific device
            await self.send_to_device(user_id, device_id, logout_message)
        else:
            # Send to all user's devices
            await self.send_to_user(user_id, logout_message)
    
    async def send_device_conflict_notification(
        self,
        user_id: str,
        conflicting_device_info: dict,
        current_sessions: list
    ):
        """
        Send device conflict notification when device limit is reached.
        
        Args:
            user_id: Auth0 user ID
            conflicting_device_info: Information about the new device trying to login
            current_sessions: List of current active sessions
        """
        conflict_message = {
            "type": "device_conflict",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "New device attempting to login - device limit reached",
            "conflicting_device": conflicting_device_info,
            "current_sessions": current_sessions,
            "action_required": False  # This is just informational for existing devices
        }
        
        await self.send_to_user(user_id, conflict_message)
    
    async def send_session_heartbeat_response(self, websocket: WebSocket):
        """
        Send heartbeat response to maintain connection.
        
        Args:
            websocket: WebSocket connection to respond to
        """
        heartbeat_message = {
            "type": "heartbeat_response",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "alive"
        }
        
        await self.send_personal_message(websocket, heartbeat_message)
    
    async def broadcast_system_message(self, message: dict):
        """
        Broadcast a system message to all connected users.
        
        Args:
            message: System message dictionary
        """
        system_message = {
            "type": "system_message",
            "timestamp": datetime.utcnow().isoformat(),
            **message
        }
        
        # Send to all active connections
        for user_id, connections in self.active_connections.items():
            for websocket in connections.copy():
                try:
                    await websocket.send_text(json.dumps(system_message))
                except Exception as e:
                    logger.error(f"Failed to send system message to user {user_id}: {e}")
                    self.disconnect(websocket, user_id)
    
    def get_connection_stats(self) -> dict:
        """
        Get statistics about active WebSocket connections.
        
        Returns:
            dict: Connection statistics
        """
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        
        return {
            "total_users_connected": len(self.active_connections),
            "total_connections": total_connections,
            "users_with_multiple_connections": len([
                user_id for user_id, connections in self.active_connections.items()
                if len(connections) > 1
            ]),
            "connection_details": {
                user_id: len(connections)
                for user_id, connections in self.active_connections.items()
            }
        }
    
    def _get_logout_message(self, reason: str) -> str:
        """
        Get user-friendly logout message based on reason.
        
        Args:
            reason: Logout reason code
            
        Returns:
            str: User-friendly message
        """
        messages = {
            "force_logout": "You have been logged out because this account was accessed from a new device.",
            "session_expired": "Your session has expired. Please log in again.",
            "admin_logout": "You have been logged out by an administrator.",
            "security_logout": "You have been logged out for security reasons.",
            "device_limit": "You have been logged out due to device limit enforcement."
        }
        
        return messages.get(reason, "You have been logged out.")
    
    async def cleanup_stale_connections(self):
        """
        Cleanup connections that are no longer active.
        This can be called periodically to maintain connection health.
        """
        stale_connections = []
        
        for user_id, connections in self.active_connections.items():
            for websocket in connections.copy():
                try:
                    # Send a ping to test connection
                    await websocket.ping()
                except Exception:
                    # Connection is stale
                    stale_connections.append((websocket, user_id))
        
        # Remove stale connections
        for websocket, user_id in stale_connections:
            self.disconnect(websocket, user_id)
        
        logger.info(f"Cleaned up {len(stale_connections)} stale WebSocket connections")
        
        return len(stale_connections)

# Global connection manager instance
connection_manager = ConnectionManager()

# WebSocket event handlers
async def handle_websocket_message(websocket: WebSocket, message: str, user_id: str):
    """
    Handle incoming WebSocket messages from clients.
    
    Args:
        websocket: WebSocket connection
        message: Received message string
        user_id: User ID for the connection
    """
    try:
        data = json.loads(message)
        message_type = data.get("type")
        
        if message_type == "heartbeat":
            await connection_manager.send_session_heartbeat_response(websocket)
        
        elif message_type == "device_registration":
            device_id = data.get("device_id")
            if device_id:
                connection_manager.connection_devices[websocket] = device_id
                logger.info(f"Device ID {device_id} registered for user {user_id}")
        
        elif message_type == "ping":
            await connection_manager.send_personal_message(websocket, {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        else:
            logger.warning(f"Unknown message type: {message_type}")
            
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON message from user {user_id}: {message}")
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")