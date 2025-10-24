"""
WebSocket endpoint for real-time agent monitoring.
Handles live streaming of agent outputs and detection results.
"""

from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time monitoring."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, data: dict):
        """Broadcast data to all connected clients."""
        if not self.active_connections:
            return
        
        message = json.dumps(data)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_to_client(self, websocket: WebSocket, data: dict):
        """Send data to a specific client."""
        try:
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.warning(f"Failed to send message to client: {e}")
            self.disconnect(websocket)


# Global connection manager instance
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time monitoring.
    
    Clients connect to receive live agent monitoring data including:
    - Agent responses
    - Hallucination detection results
    - Risk scores and flagged segments
    - Mitigation suggestions
    """
    await manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await manager.send_to_client(websocket, {
            "type": "connection_established",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to AgentGuard live monitoring"
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (e.g., ping/pong, configuration)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)
                
                # Handle client messages
                if message.get("type") == "ping":
                    await manager.send_to_client(websocket, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
            except asyncio.TimeoutError:
                # Send keepalive ping
                await manager.send_to_client(websocket, {
                    "type": "keepalive",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON from client")
            except Exception as e:
                logger.error(f"Error handling client message: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    return manager
