"""
Scalable WebSocket Manager
Handles thousands of concurrent WebSocket connections with Redis pub/sub for horizontal scaling.
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect
import uuid
import weakref
from collections import defaultdict, deque

from ..middleware.tenant_middleware import get_current_tenant

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """WebSocket connection types."""
    DASHBOARD = "dashboard"
    WORKSTATION = "workstation"
    AGENT = "agent"
    MONITOR = "monitor"
    ADMIN = "admin"


class MessageType(Enum):
    """WebSocket message types."""
    HEARTBEAT = "heartbeat"
    DETECTION_RESULT = "detection_result"
    SYSTEM_ALERT = "system_alert"
    WORKSTATION_STATUS = "workstation_status"
    AGENT_OUTPUT = "agent_output"
    PERFORMANCE_METRIC = "performance_metric"
    COMPLIANCE_VIOLATION = "compliance_violation"
    TENANT_NOTIFICATION = "tenant_notification"
    BROADCAST = "broadcast"


@dataclass
class WebSocketConnection:
    """WebSocket connection metadata."""
    connection_id: str
    websocket: WebSocket
    tenant_id: str
    user_id: Optional[str]
    connection_type: ConnectionType
    workstation_id: Optional[str] = None
    agent_id: Optional[str] = None
    connected_at: datetime = None
    last_heartbeat: datetime = None
    subscriptions: Set[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.connected_at is None:
            self.connected_at = datetime.utcnow()
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.utcnow()
        if self.subscriptions is None:
            self.subscriptions = set()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class WebSocketMessage:
    """WebSocket message structure."""
    message_id: str
    message_type: MessageType
    tenant_id: str
    source_id: Optional[str]
    target_id: Optional[str]
    channel: str
    data: Dict[str, Any]
    timestamp: datetime = None
    ttl_seconds: Optional[int] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "tenant_id": self.tenant_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "channel": self.channel,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "ttl_seconds": self.ttl_seconds
        }


class WebSocketManager:
    """
    Scalable WebSocket manager with Redis pub/sub for horizontal scaling.
    Supports thousands of concurrent connections across multiple server instances.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        
        # Connection management
        self.connections: Dict[str, WebSocketConnection] = {}
        self.tenant_connections: Dict[str, Set[str]] = defaultdict(set)
        self.workstation_connections: Dict[str, Set[str]] = defaultdict(set)
        self.agent_connections: Dict[str, Set[str]] = defaultdict(set)
        self.channel_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        
        # Performance tracking
        self.message_queue: deque = deque(maxlen=10000)
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "heartbeats_processed": 0,
            "disconnections": 0
        }
        
        # Background tasks
        self._background_tasks: Set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()
        
        # Message handlers
        self.message_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)
        
        # Connection cleanup
        self.heartbeat_timeout = 60  # seconds
        self.cleanup_interval = 30   # seconds
    
    async def initialize(self):
        """Initialize Redis connections and background tasks."""
        try:
            # Initialize Redis client
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            
            # Initialize pub/sub
            self.pubsub = self.redis_client.pubsub()
            
            # Start background tasks
            await self._start_background_tasks()
            
            logger.info("WebSocket manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket manager: {e}")
            raise
    
    async def _start_background_tasks(self):
        """Start background maintenance tasks."""
        tasks = [
            self._redis_message_listener(),
            self._heartbeat_monitor(),
            self._connection_cleanup(),
            self._performance_monitor()
        ]
        
        for task_coro in tasks:
            task = asyncio.create_task(task_coro)
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
    
    async def connect(self, websocket: WebSocket, connection_type: ConnectionType,
                     tenant_id: str, user_id: str = None, workstation_id: str = None,
                     agent_id: str = None, metadata: Dict[str, Any] = None) -> str:
        """Accept and register a new WebSocket connection."""
        try:
            await websocket.accept()
            
            # Generate connection ID
            connection_id = f"{connection_type.value}_{tenant_id}_{uuid.uuid4().hex[:8]}"
            
            # Create connection object
            connection = WebSocketConnection(
                connection_id=connection_id,
                websocket=websocket,
                tenant_id=tenant_id,
                user_id=user_id,
                connection_type=connection_type,
                workstation_id=workstation_id,
                agent_id=agent_id,
                metadata=metadata or {}
            )
            
            # Register connection
            self.connections[connection_id] = connection
            self.tenant_connections[tenant_id].add(connection_id)
            
            if workstation_id:
                self.workstation_connections[workstation_id].add(connection_id)
            
            if agent_id:
                self.agent_connections[agent_id].add(connection_id)
            
            # Subscribe to tenant channel
            tenant_channel = f"tenant:{tenant_id}"
            await self._subscribe_to_channel(connection_id, tenant_channel)
            
            # Subscribe to connection type channel
            type_channel = f"type:{connection_type.value}"
            await self._subscribe_to_channel(connection_id, type_channel)
            
            # Update stats
            self.connection_stats["total_connections"] += 1
            self.connection_stats["active_connections"] = len(self.connections)
            
            # Send welcome message
            welcome_msg = WebSocketMessage(
                message_id=f"welcome_{uuid.uuid4().hex[:8]}",
                message_type=MessageType.SYSTEM_ALERT,
                tenant_id=tenant_id,
                source_id="system",
                target_id=connection_id,
                channel=tenant_channel,
                data={
                    "type": "connection_established",
                    "connection_id": connection_id,
                    "server_time": datetime.utcnow().isoformat(),
                    "capabilities": ["heartbeat", "real_time_monitoring", "alerts"]
                }
            )
            
            await self._send_to_connection(connection_id, welcome_msg)
            
            logger.info(f"WebSocket connected: {connection_id} ({connection_type.value}) for tenant {tenant_id}")
            return connection_id
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            raise
    
    async def disconnect(self, connection_id: str, code: int = 1000):
        """Disconnect and cleanup a WebSocket connection."""
        if connection_id not in self.connections:
            return
        
        try:
            connection = self.connections[connection_id]
            
            # Remove from all tracking structures
            self.tenant_connections[connection.tenant_id].discard(connection_id)
            
            if connection.workstation_id:
                self.workstation_connections[connection.workstation_id].discard(connection_id)
            
            if connection.agent_id:
                self.agent_connections[connection.agent_id].discard(connection_id)
            
            # Unsubscribe from channels
            for channel in list(connection.subscriptions):
                await self._unsubscribe_from_channel(connection_id, channel)
            
            # Close WebSocket
            try:
                await connection.websocket.close(code)
            except:
                pass  # Connection might already be closed
            
            # Remove connection
            del self.connections[connection_id]
            
            # Update stats
            self.connection_stats["disconnections"] += 1
            self.connection_stats["active_connections"] = len(self.connections)
            
            logger.info(f"WebSocket disconnected: {connection_id}")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    async def send_message(self, message: WebSocketMessage):
        """Send message through Redis pub/sub for horizontal scaling."""
        try:
            # Publish to Redis channel
            channel_key = f"websocket:{message.channel}"
            message_data = json.dumps(message.to_dict())
            
            await self.redis_client.publish(channel_key, message_data)
            
            self.connection_stats["messages_sent"] += 1
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def send_to_tenant(self, tenant_id: str, message: WebSocketMessage):
        """Send message to all connections for a specific tenant."""
        message.channel = f"tenant:{tenant_id}"
        await self.send_message(message)
    
    async def send_to_workstation(self, workstation_id: str, message: WebSocketMessage):
        """Send message to all connections for a specific workstation."""
        message.channel = f"workstation:{workstation_id}"
        await self.send_message(message)
    
    async def send_to_connection_type(self, connection_type: ConnectionType, message: WebSocketMessage):
        """Send message to all connections of a specific type."""
        message.channel = f"type:{connection_type.value}"
        await self.send_message(message)
    
    async def broadcast_to_all(self, message: WebSocketMessage):
        """Broadcast message to all connections."""
        message.channel = "broadcast"
        await self.send_message(message)
    
    async def _subscribe_to_channel(self, connection_id: str, channel: str):
        """Subscribe connection to a channel."""
        if connection_id in self.connections:
            self.connections[connection_id].subscriptions.add(channel)
            self.channel_subscriptions[channel].add(connection_id)
            
            # Subscribe to Redis channel if not already subscribed
            redis_channel = f"websocket:{channel}"
            if redis_channel not in self.pubsub.channels:
                await self.pubsub.subscribe(redis_channel)
    
    async def _unsubscribe_from_channel(self, connection_id: str, channel: str):
        """Unsubscribe connection from a channel."""
        if connection_id in self.connections:
            self.connections[connection_id].subscriptions.discard(channel)
            self.channel_subscriptions[channel].discard(connection_id)
            
            # Unsubscribe from Redis if no more local connections
            if not self.channel_subscriptions[channel]:
                redis_channel = f"websocket:{channel}"
                try:
                    await self.pubsub.unsubscribe(redis_channel)
                except:
                    pass
    
    async def _redis_message_listener(self):
        """Listen for messages from Redis pub/sub."""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        # Parse message
                        message_data = json.loads(message["data"])
                        ws_message = WebSocketMessage(
                            message_id=message_data["message_id"],
                            message_type=MessageType(message_data["message_type"]),
                            tenant_id=message_data["tenant_id"],
                            source_id=message_data.get("source_id"),
                            target_id=message_data.get("target_id"),
                            channel=message_data["channel"],
                            data=message_data["data"],
                            timestamp=datetime.fromisoformat(message_data["timestamp"]),
                            ttl_seconds=message_data.get("ttl_seconds")
                        )
                        
                        # Check TTL
                        if ws_message.ttl_seconds:
                            age = (datetime.utcnow() - ws_message.timestamp).total_seconds()
                            if age > ws_message.ttl_seconds:
                                continue  # Message expired
                        
                        # Route message to appropriate connections
                        await self._route_message(ws_message)
                        
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
                        
        except asyncio.CancelledError:
            logger.info("Redis message listener cancelled")
        except Exception as e:
            logger.error(f"Redis message listener error: {e}")
    
    async def _route_message(self, message: WebSocketMessage):
        """Route message to appropriate local connections."""
        target_connections = set()
        
        # Route based on target_id
        if message.target_id and message.target_id in self.connections:
            target_connections.add(message.target_id)
        
        # Route based on channel
        elif message.channel in self.channel_subscriptions:
            target_connections.update(self.channel_subscriptions[message.channel])
        
        # Send to target connections
        for connection_id in target_connections:
            await self._send_to_connection(connection_id, message)
    
    async def _send_to_connection(self, connection_id: str, message: WebSocketMessage):
        """Send message to a specific connection."""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        try:
            message_dict = message.to_dict()
            await connection.websocket.send_json(message_dict)
            
            # Call message handlers
            for handler in self.message_handlers[message.message_type]:
                try:
                    await handler(connection, message)
                except Exception as e:
                    logger.error(f"Message handler error: {e}")
            
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
        except Exception as e:
            logger.error(f"Error sending to connection {connection_id}: {e}")
            await self.disconnect(connection_id)
    
    async def _heartbeat_monitor(self):
        """Monitor connection heartbeats and cleanup stale connections."""
        while not self._shutdown_event.is_set():
            try:
                now = datetime.utcnow()
                stale_connections = []
                
                for connection_id, connection in self.connections.items():
                    time_since_heartbeat = (now - connection.last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > self.heartbeat_timeout:
                        stale_connections.append(connection_id)
                
                # Cleanup stale connections
                for connection_id in stale_connections:
                    logger.warning(f"Cleaning up stale connection: {connection_id}")
                    await self.disconnect(connection_id, code=1001)
                
                await asyncio.sleep(self.cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                await asyncio.sleep(5)
    
    async def _connection_cleanup(self):
        """Periodic cleanup of connection tracking structures."""
        while not self._shutdown_event.is_set():
            try:
                # Clean empty sets from tracking dictionaries
                for tenant_id in list(self.tenant_connections.keys()):
                    if not self.tenant_connections[tenant_id]:
                        del self.tenant_connections[tenant_id]
                
                for workstation_id in list(self.workstation_connections.keys()):
                    if not self.workstation_connections[workstation_id]:
                        del self.workstation_connections[workstation_id]
                
                for agent_id in list(self.agent_connections.keys()):
                    if not self.agent_connections[agent_id]:
                        del self.agent_connections[agent_id]
                
                for channel in list(self.channel_subscriptions.keys()):
                    if not self.channel_subscriptions[channel]:
                        del self.channel_subscriptions[channel]
                
                await asyncio.sleep(300)  # Clean every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Connection cleanup error: {e}")
                await asyncio.sleep(60)
    
    async def _performance_monitor(self):
        """Monitor and log performance metrics."""
        while not self._shutdown_event.is_set():
            try:
                # Log performance stats
                stats = self.get_performance_stats()
                logger.info(f"WebSocket Performance: {stats}")
                
                # Store metrics in Redis for monitoring
                await self.redis_client.hset(
                    "websocket:performance",
                    mapping={
                        "timestamp": datetime.utcnow().isoformat(),
                        **{k: str(v) for k, v in stats.items()}
                    }
                )
                
                await asyncio.sleep(60)  # Log every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance monitor error: {e}")
                await asyncio.sleep(60)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        return {
            **self.connection_stats,
            "tenant_count": len(self.tenant_connections),
            "workstation_count": len(self.workstation_connections),
            "agent_count": len(self.agent_connections),
            "channel_count": len(self.channel_subscriptions),
            "message_queue_size": len(self.message_queue)
        }
    
    def add_message_handler(self, message_type: MessageType, handler: Callable):
        """Add a message handler for specific message types."""
        self.message_handlers[message_type].append(handler)
    
    async def handle_heartbeat(self, connection_id: str):
        """Handle heartbeat from connection."""
        if connection_id in self.connections:
            self.connections[connection_id].last_heartbeat = datetime.utcnow()
            self.connection_stats["heartbeats_processed"] += 1
    
    async def shutdown(self):
        """Gracefully shutdown the WebSocket manager."""
        logger.info("Shutting down WebSocket manager...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Close all connections
        for connection_id in list(self.connections.keys()):
            await self.disconnect(connection_id)
        
        # Close Redis connections
        if self.pubsub:
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("WebSocket manager shutdown complete")


# Global WebSocket manager instance
_websocket_manager: Optional[WebSocketManager] = None

async def get_websocket_manager() -> WebSocketManager:
    """Get or create WebSocket manager instance."""
    global _websocket_manager
    if _websocket_manager is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _websocket_manager = WebSocketManager(redis_url)
        await _websocket_manager.initialize()
    return _websocket_manager
