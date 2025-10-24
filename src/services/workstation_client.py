"""
Workstation Agent Client
Lightweight client that runs on workstations to monitor local AI agents and connect to Watcher-AI.
"""

import os
import json
import logging
import asyncio
import aiohttp
import websockets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import psutil
import platform
import socket
from pathlib import Path
import threading
import time

logger = logging.getLogger(__name__)


class WorkstationStatus(Enum):
    """Workstation status enumeration."""
    ONLINE = "online"
    OFFLINE = "offline"
    MONITORING = "monitoring"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AgentStatus(Enum):
    """Agent status enumeration."""
    ACTIVE = "active"
    IDLE = "idle"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class WorkstationInfo:
    """Workstation system information."""
    workstation_id: str
    hostname: str
    platform: str
    platform_version: str
    cpu_count: int
    memory_total_gb: float
    disk_total_gb: float
    ip_address: str
    mac_address: str
    user: str
    python_version: str
    watcher_client_version: str = "1.0.0"
    
    @classmethod
    def collect_system_info(cls, workstation_id: str = None) -> 'WorkstationInfo':
        """Collect current system information."""
        if not workstation_id:
            workstation_id = f"ws_{socket.gethostname()}_{uuid.uuid4().hex[:8]}"
        
        # Get network info
        hostname = socket.gethostname()
        try:
            ip_address = socket.gethostbyname(hostname)
        except:
            ip_address = "127.0.0.1"
        
        # Get MAC address
        import uuid as uuid_module
        mac_address = ':'.join(['{:02x}'.format((uuid_module.getnode() >> elements) & 0xff) 
                               for elements in range(0, 2*6, 2)][::-1])
        
        # Get system info
        memory_bytes = psutil.virtual_memory().total
        disk_bytes = psutil.disk_usage('/').total
        
        return cls(
            workstation_id=workstation_id,
            hostname=hostname,
            platform=platform.system(),
            platform_version=platform.platform(),
            cpu_count=psutil.cpu_count(),
            memory_total_gb=round(memory_bytes / (1024**3), 2),
            disk_total_gb=round(disk_bytes / (1024**3), 2),
            ip_address=ip_address,
            mac_address=mac_address,
            user=os.getenv('USER', os.getenv('USERNAME', 'unknown')),
            python_version=platform.python_version()
        )


@dataclass
class AgentInfo:
    """Local AI agent information."""
    agent_id: str
    name: str
    type: str  # "chatbot", "assistant", "analyzer", etc.
    status: AgentStatus
    pid: Optional[int] = None
    port: Optional[int] = None
    endpoint: Optional[str] = None
    last_activity: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()


@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_processes: int
    load_average: Optional[float] = None
    
    @classmethod
    def collect_current_metrics(cls) -> 'SystemMetrics':
        """Collect current system metrics."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        # Load average (Unix only)
        load_avg = None
        try:
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()[0]
        except:
            pass
        
        return cls(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=(disk.used / disk.total) * 100,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            active_processes=len(psutil.pids()),
            load_average=load_avg
        )


class WorkstationClient:
    """
    Lightweight workstation client for monitoring local AI agents.
    Connects to Watcher-AI via WebSocket for real-time monitoring.
    """
    
    def __init__(self, server_url: str, api_key: str, workstation_id: str = None,
                 config_file: str = None):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.workstation_info = WorkstationInfo.collect_system_info(workstation_id)
        self.workstation_id = self.workstation_info.workstation_id
        
        # Configuration
        self.config_file = config_file or "watcher_client_config.json"
        self.config = self._load_config()
        
        # Connection management
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.status = WorkstationStatus.OFFLINE
        self.connected = False
        self.reconnect_interval = 5  # seconds
        self.heartbeat_interval = 30  # seconds
        
        # Agent monitoring
        self.agents: Dict[str, AgentInfo] = {}
        self.agent_monitors: Dict[str, threading.Thread] = {}
        
        # Metrics collection
        self.metrics_interval = 60  # seconds
        self.metrics_history: List[SystemMetrics] = []
        self.max_metrics_history = 1440  # 24 hours at 1-minute intervals
        
        # Background tasks
        self._tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Message handlers
        self.message_handlers: Dict[str, Callable] = {
            "heartbeat_request": self._handle_heartbeat_request,
            "agent_query": self._handle_agent_query,
            "system_command": self._handle_system_command,
            "config_update": self._handle_config_update,
            "detection_request": self._handle_detection_request
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        default_config = {
            "monitoring_enabled": True,
            "metrics_collection": True,
            "auto_discovery": True,
            "agent_endpoints": [],
            "excluded_processes": ["watcher_client"],
            "alert_thresholds": {
                "cpu_percent": 90,
                "memory_percent": 90,
                "disk_percent": 95
            },
            "detection_settings": {
                "auto_detect_agents": True,
                "monitor_outputs": True,
                "sample_rate": 0.1  # Sample 10% of outputs
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
        
        return default_config
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    async def start(self):
        """Start the workstation client."""
        logger.info(f"Starting Watcher-AI workstation client: {self.workstation_id}")
        
        # Register workstation
        await self._register_workstation()
        
        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._websocket_connection_manager()),
            asyncio.create_task(self._metrics_collector()),
            asyncio.create_task(self._agent_discovery()),
            asyncio.create_task(self._heartbeat_sender())
        ]
        
        # Wait for shutdown
        await self._shutdown_event.wait()
        
        # Cleanup
        await self._cleanup()
    
    async def stop(self):
        """Stop the workstation client."""
        logger.info("Stopping workstation client...")
        self._shutdown_event.set()
    
    async def _register_workstation(self):
        """Register workstation with Watcher-AI server."""
        try:
            url = f"{self.server_url}/api/workstations/register"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            registration_data = {
                "workstation_info": asdict(self.workstation_info),
                "config": self.config,
                "status": WorkstationStatus.ONLINE.value
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=registration_data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Workstation registered successfully: {result}")
                    else:
                        logger.error(f"Failed to register workstation: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error registering workstation: {e}")
    
    async def _websocket_connection_manager(self):
        """Manage WebSocket connection with automatic reconnection."""
        while not self._shutdown_event.is_set():
            try:
                # Build WebSocket URL
                ws_url = self.server_url.replace('http', 'ws') + "/ws/workstation"
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                logger.info(f"Connecting to WebSocket: {ws_url}")
                
                async with websockets.connect(
                    ws_url,
                    extra_headers=headers,
                    ping_interval=20,
                    ping_timeout=10
                ) as websocket:
                    self.websocket = websocket
                    self.connected = True
                    self.status = WorkstationStatus.MONITORING
                    
                    logger.info("WebSocket connected successfully")
                    
                    # Send initial status
                    await self._send_status_update()
                    
                    # Listen for messages
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            await self._handle_message(data)
                        except Exception as e:
                            logger.error(f"Error handling message: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
            
            # Connection lost
            self.connected = False
            self.status = WorkstationStatus.OFFLINE
            
            if not self._shutdown_event.is_set():
                logger.info(f"Reconnecting in {self.reconnect_interval} seconds...")
                await asyncio.sleep(self.reconnect_interval)
    
    async def _handle_message(self, data: Dict[str, Any]):
        """Handle incoming WebSocket message."""
        message_type = data.get("message_type")
        
        if message_type in self.message_handlers:
            try:
                await self.message_handlers[message_type](data)
            except Exception as e:
                logger.error(f"Error handling {message_type}: {e}")
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def _handle_heartbeat_request(self, data: Dict[str, Any]):
        """Handle heartbeat request from server."""
        response = {
            "message_type": "heartbeat_response",
            "workstation_id": self.workstation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": self.status.value,
            "metrics": asdict(SystemMetrics.collect_current_metrics())
        }
        
        await self._send_message(response)
    
    async def _handle_agent_query(self, data: Dict[str, Any]):
        """Handle agent information query."""
        response = {
            "message_type": "agent_info_response",
            "workstation_id": self.workstation_id,
            "agents": [asdict(agent) for agent in self.agents.values()],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._send_message(response)
    
    async def _handle_system_command(self, data: Dict[str, Any]):
        """Handle system command from server."""
        command = data.get("command")
        
        if command == "restart_monitoring":
            await self._restart_agent_monitoring()
        elif command == "update_config":
            self.config.update(data.get("config", {}))
            self._save_config()
        elif command == "collect_metrics":
            metrics = SystemMetrics.collect_current_metrics()
            await self._send_metrics_update(metrics)
        
        # Send acknowledgment
        response = {
            "message_type": "command_response",
            "workstation_id": self.workstation_id,
            "command": command,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._send_message(response)
    
    async def _handle_config_update(self, data: Dict[str, Any]):
        """Handle configuration update from server."""
        new_config = data.get("config", {})
        self.config.update(new_config)
        self._save_config()
        
        logger.info("Configuration updated from server")
    
    async def _handle_detection_request(self, data: Dict[str, Any]):
        """Handle detection request for agent output."""
        agent_id = data.get("agent_id")
        output_text = data.get("output_text")
        
        if agent_id in self.agents:
            # Send to Watcher-AI for detection
            detection_result = await self._request_detection(agent_id, output_text)
            
            response = {
                "message_type": "detection_result",
                "workstation_id": self.workstation_id,
                "agent_id": agent_id,
                "output_text": output_text,
                "detection_result": detection_result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self._send_message(response)
    
    async def _send_message(self, data: Dict[str, Any]):
        """Send message via WebSocket."""
        if self.websocket and self.connected:
            try:
                message = json.dumps(data)
                await self.websocket.send(message)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
    
    async def _send_status_update(self):
        """Send workstation status update."""
        status_data = {
            "message_type": "status_update",
            "workstation_id": self.workstation_id,
            "status": self.status.value,
            "workstation_info": asdict(self.workstation_info),
            "agents": [asdict(agent) for agent in self.agents.values()],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._send_message(status_data)
    
    async def _send_metrics_update(self, metrics: SystemMetrics):
        """Send system metrics update."""
        metrics_data = {
            "message_type": "metrics_update",
            "workstation_id": self.workstation_id,
            "metrics": asdict(metrics),
            "timestamp": metrics.timestamp.isoformat()
        }
        
        await self._send_message(metrics_data)
    
    async def _metrics_collector(self):
        """Collect and send system metrics periodically."""
        while not self._shutdown_event.is_set():
            try:
                if self.config.get("metrics_collection", True):
                    metrics = SystemMetrics.collect_current_metrics()
                    
                    # Store in history
                    self.metrics_history.append(metrics)
                    if len(self.metrics_history) > self.max_metrics_history:
                        self.metrics_history.pop(0)
                    
                    # Send to server
                    if self.connected:
                        await self._send_metrics_update(metrics)
                    
                    # Check alert thresholds
                    await self._check_alert_thresholds(metrics)
                
                await asyncio.sleep(self.metrics_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collector: {e}")
                await asyncio.sleep(10)
    
    async def _check_alert_thresholds(self, metrics: SystemMetrics):
        """Check if metrics exceed alert thresholds."""
        thresholds = self.config.get("alert_thresholds", {})
        
        alerts = []
        
        if metrics.cpu_percent > thresholds.get("cpu_percent", 90):
            alerts.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > thresholds.get("memory_percent", 90):
            alerts.append(f"High memory usage: {metrics.memory_percent:.1f}%")
        
        if metrics.disk_percent > thresholds.get("disk_percent", 95):
            alerts.append(f"High disk usage: {metrics.disk_percent:.1f}%")
        
        if alerts and self.connected:
            alert_data = {
                "message_type": "system_alert",
                "workstation_id": self.workstation_id,
                "alerts": alerts,
                "metrics": asdict(metrics),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self._send_message(alert_data)
    
    async def _agent_discovery(self):
        """Discover and monitor local AI agents."""
        while not self._shutdown_event.is_set():
            try:
                if self.config.get("auto_discovery", True):
                    await self._discover_agents()
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in agent discovery: {e}")
                await asyncio.sleep(30)
    
    async def _discover_agents(self):
        """Discover running AI agents on the system."""
        # This is a simplified discovery - in practice, you'd implement
        # more sophisticated detection based on process names, ports, etc.
        
        discovered_agents = {}
        
        # Check configured endpoints
        for endpoint_config in self.config.get("agent_endpoints", []):
            agent_id = endpoint_config.get("agent_id")
            if agent_id and await self._check_agent_health(endpoint_config):
                agent = AgentInfo(
                    agent_id=agent_id,
                    name=endpoint_config.get("name", agent_id),
                    type=endpoint_config.get("type", "unknown"),
                    status=AgentStatus.ACTIVE,
                    endpoint=endpoint_config.get("endpoint"),
                    port=endpoint_config.get("port")
                )
                discovered_agents[agent_id] = agent
        
        # Update agents list
        self.agents = discovered_agents
        
        if self.connected:
            await self._send_status_update()
    
    async def _check_agent_health(self, endpoint_config: Dict[str, Any]) -> bool:
        """Check if an agent endpoint is healthy."""
        try:
            endpoint = endpoint_config.get("endpoint")
            if endpoint:
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint, timeout=5) as response:
                        return response.status == 200
        except:
            pass
        
        return False
    
    async def _heartbeat_sender(self):
        """Send periodic heartbeats to server."""
        while not self._shutdown_event.is_set():
            try:
                if self.connected:
                    heartbeat_data = {
                        "message_type": "heartbeat",
                        "workstation_id": self.workstation_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": self.status.value
                    }
                    
                    await self._send_message(heartbeat_data)
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
                await asyncio.sleep(10)
    
    async def _request_detection(self, agent_id: str, output_text: str) -> Dict[str, Any]:
        """Request hallucination detection from Watcher-AI server."""
        try:
            url = f"{self.server_url}/api/test-agent"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            detection_data = {
                "agent_output": output_text,
                "agent_id": agent_id,
                "workstation_id": self.workstation_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=detection_data, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"Detection request failed: {response.status}"}
                        
        except Exception as e:
            return {"error": f"Detection request error: {str(e)}"}
    
    async def _restart_agent_monitoring(self):
        """Restart agent monitoring."""
        logger.info("Restarting agent monitoring...")
        
        # Stop existing monitors
        for thread in self.agent_monitors.values():
            if thread.is_alive():
                # In a real implementation, you'd have a proper stop mechanism
                pass
        
        self.agent_monitors.clear()
        
        # Rediscover agents
        await self._discover_agents()
        
        logger.info("Agent monitoring restarted")
    
    async def _cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up workstation client...")
        
        # Cancel tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Close WebSocket
        if self.websocket:
            await self.websocket.close()
        
        logger.info("Workstation client cleanup complete")


async def main():
    """Main entry point for workstation client."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Watcher-AI Workstation Client")
    parser.add_argument("--server", required=True, help="Watcher-AI server URL")
    parser.add_argument("--api-key", required=True, help="API key for authentication")
    parser.add_argument("--workstation-id", help="Workstation ID (auto-generated if not provided)")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start client
    client = WorkstationClient(
        server_url=args.server,
        api_key=args.api_key,
        workstation_id=args.workstation_id,
        config_file=args.config
    )
    
    try:
        await client.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
