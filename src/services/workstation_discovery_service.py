"""
Workstation Discovery Service
Intelligent network discovery system for automatic workstation identification and registration.
"""

import os
import json
import logging
import asyncio
import socket
import struct
import subprocess
import platform
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import sqlite3
import secrets
import ipaddress
import concurrent.futures
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class DiscoveryMethod(Enum):
    """Discovery method enumeration."""
    NETWORK_SCAN = "network_scan"
    ACTIVE_DIRECTORY = "active_directory"
    SNMP = "snmp"
    DHCP_LOGS = "dhcp_logs"
    DNS_LOOKUP = "dns_lookup"
    MANUAL = "manual"


class DeviceType(Enum):
    """Device type enumeration."""
    WORKSTATION = "workstation"
    SERVER = "server"
    LAPTOP = "laptop"
    MOBILE = "mobile"
    PRINTER = "printer"
    NETWORK_DEVICE = "network_device"
    IOT_DEVICE = "iot_device"
    UNKNOWN = "unknown"


class OperatingSystem(Enum):
    """Operating system enumeration."""
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNIX = "unix"
    ANDROID = "android"
    IOS = "ios"
    UNKNOWN = "unknown"


@dataclass
class NetworkRange:
    """Network range for discovery."""
    range_id: str
    name: str
    cidr: str
    description: str
    enabled: bool = True
    scan_frequency: int = 3600  # seconds
    last_scan: Optional[datetime] = None
    discovered_devices: int = 0
    
    def __post_init__(self):
        if not self.range_id:
            self.range_id = f"range_{secrets.token_urlsafe(8)}"


@dataclass
class DiscoveredDevice:
    """Discovered device information."""
    device_id: str
    ip_address: str
    mac_address: Optional[str] = None
    hostname: Optional[str] = None
    device_type: DeviceType = DeviceType.UNKNOWN
    operating_system: OperatingSystem = OperatingSystem.UNKNOWN
    os_version: Optional[str] = None
    
    # Discovery information
    discovery_method: DiscoveryMethod = DiscoveryMethod.NETWORK_SCAN
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    
    # Network information
    open_ports: List[int] = field(default_factory=list)
    services: Dict[int, str] = field(default_factory=dict)
    network_range_id: Optional[str] = None
    
    # Hardware information
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    
    # Software information
    installed_software: List[str] = field(default_factory=list)
    running_processes: List[str] = field(default_factory=list)
    
    # Security information
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    security_score: Optional[float] = None
    
    # Agent information
    agent_installed: bool = False
    agent_version: Optional[str] = None
    agent_status: Optional[str] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.device_id:
            # Generate device ID based on IP and MAC
            identifier = f"{self.ip_address}_{self.mac_address or 'unknown'}"
            self.device_id = hashlib.md5(identifier.encode()).hexdigest()[:16]


@dataclass
class DiscoveryTask:
    """Discovery task definition."""
    task_id: str
    name: str
    description: str
    network_ranges: List[str]  # range_ids
    discovery_methods: List[DiscoveryMethod]
    enabled: bool = True
    
    # Scheduling
    schedule_type: str = "interval"  # interval, cron, manual
    interval_seconds: int = 3600
    cron_expression: Optional[str] = None
    
    # Configuration
    port_scan_enabled: bool = True
    service_detection_enabled: bool = True
    os_detection_enabled: bool = True
    vulnerability_scan_enabled: bool = False
    
    # Limits
    max_concurrent_scans: int = 50
    scan_timeout: int = 30
    
    # Status
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    devices_discovered: int = 0
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.task_id:
            self.task_id = f"task_{secrets.token_urlsafe(8)}"


class WorkstationDiscoveryService:
    """
    Comprehensive workstation discovery service with network scanning,
    device fingerprinting, and automated registration.
    """
    
    def __init__(self, db_path: str = "workstation_discovery.db"):
        self.db_path = db_path
        
        # In-memory storage
        self.network_ranges: Dict[str, NetworkRange] = {}
        self.discovered_devices: Dict[str, DiscoveredDevice] = {}
        self.discovery_tasks: Dict[str, DiscoveryTask] = {}
        
        # Background tasks
        self._background_tasks: Set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()
        
        # Scanning state
        self.active_scans: Set[str] = set()
        self.scan_semaphore = asyncio.Semaphore(10)  # Limit concurrent scans
        
        # Initialize database
        self._init_database()
        
        # Load existing data
        self._load_data()
        
        # Start background tasks
        asyncio.create_task(self._start_background_tasks())
    
    def _init_database(self):
        """Initialize discovery database."""
        with sqlite3.connect(self.db_path) as conn:
            # Network ranges table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS network_ranges (
                    range_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    cidr TEXT NOT NULL,
                    description TEXT,
                    enabled BOOLEAN DEFAULT TRUE,
                    scan_frequency INTEGER DEFAULT 3600,
                    last_scan TIMESTAMP,
                    discovered_devices INTEGER DEFAULT 0
                )
            """)
            
            # Discovered devices table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS discovered_devices (
                    device_id TEXT PRIMARY KEY,
                    ip_address TEXT NOT NULL,
                    mac_address TEXT,
                    hostname TEXT,
                    device_type TEXT DEFAULT 'unknown',
                    operating_system TEXT DEFAULT 'unknown',
                    os_version TEXT,
                    discovery_method TEXT DEFAULT 'network_scan',
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    open_ports TEXT DEFAULT '[]',
                    services TEXT DEFAULT '{}',
                    network_range_id TEXT,
                    manufacturer TEXT,
                    model TEXT,
                    serial_number TEXT,
                    installed_software TEXT DEFAULT '[]',
                    running_processes TEXT DEFAULT '[]',
                    vulnerabilities TEXT DEFAULT '[]',
                    security_score REAL,
                    agent_installed BOOLEAN DEFAULT FALSE,
                    agent_version TEXT,
                    agent_status TEXT,
                    tags TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Discovery tasks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS discovery_tasks (
                    task_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    network_ranges TEXT DEFAULT '[]',
                    discovery_methods TEXT DEFAULT '[]',
                    enabled BOOLEAN DEFAULT TRUE,
                    schedule_type TEXT DEFAULT 'interval',
                    interval_seconds INTEGER DEFAULT 3600,
                    cron_expression TEXT,
                    port_scan_enabled BOOLEAN DEFAULT TRUE,
                    service_detection_enabled BOOLEAN DEFAULT TRUE,
                    os_detection_enabled BOOLEAN DEFAULT TRUE,
                    vulnerability_scan_enabled BOOLEAN DEFAULT FALSE,
                    max_concurrent_scans INTEGER DEFAULT 50,
                    scan_timeout INTEGER DEFAULT 30,
                    last_run TIMESTAMP,
                    next_run TIMESTAMP,
                    devices_discovered INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Discovery history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS discovery_history (
                    scan_id TEXT PRIMARY KEY,
                    task_id TEXT,
                    network_range_id TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    devices_found INTEGER DEFAULT 0,
                    new_devices INTEGER DEFAULT 0,
                    updated_devices INTEGER DEFAULT 0,
                    scan_duration_seconds INTEGER,
                    status TEXT DEFAULT 'running',
                    error_message TEXT
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_devices_ip ON discovered_devices(ip_address)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_devices_mac ON discovered_devices(mac_address)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_devices_hostname ON discovered_devices(hostname)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON discovered_devices(last_seen)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_history_task ON discovery_history(task_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_history_started ON discovery_history(started_at)")
            
            conn.commit()
    
    def _load_data(self):
        """Load existing data from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Load network ranges
                cursor = conn.execute("SELECT * FROM network_ranges")
                for row in cursor.fetchall():
                    range_obj = NetworkRange(
                        range_id=row['range_id'],
                        name=row['name'],
                        cidr=row['cidr'],
                        description=row['description'],
                        enabled=bool(row['enabled']),
                        scan_frequency=row['scan_frequency'],
                        last_scan=datetime.fromisoformat(row['last_scan']) if row['last_scan'] else None,
                        discovered_devices=row['discovered_devices']
                    )
                    self.network_ranges[range_obj.range_id] = range_obj
                
                # Load discovered devices
                cursor = conn.execute("SELECT * FROM discovered_devices")
                for row in cursor.fetchall():
                    device = DiscoveredDevice(
                        device_id=row['device_id'],
                        ip_address=row['ip_address'],
                        mac_address=row['mac_address'],
                        hostname=row['hostname'],
                        device_type=DeviceType(row['device_type']),
                        operating_system=OperatingSystem(row['operating_system']),
                        os_version=row['os_version'],
                        discovery_method=DiscoveryMethod(row['discovery_method']),
                        discovered_at=datetime.fromisoformat(row['discovered_at']),
                        last_seen=datetime.fromisoformat(row['last_seen']),
                        open_ports=json.loads(row['open_ports']) if row['open_ports'] else [],
                        services=json.loads(row['services']) if row['services'] else {},
                        network_range_id=row['network_range_id'],
                        manufacturer=row['manufacturer'],
                        model=row['model'],
                        serial_number=row['serial_number'],
                        installed_software=json.loads(row['installed_software']) if row['installed_software'] else [],
                        running_processes=json.loads(row['running_processes']) if row['running_processes'] else [],
                        vulnerabilities=json.loads(row['vulnerabilities']) if row['vulnerabilities'] else [],
                        security_score=row['security_score'],
                        agent_installed=bool(row['agent_installed']),
                        agent_version=row['agent_version'],
                        agent_status=row['agent_status'],
                        tags=json.loads(row['tags']) if row['tags'] else [],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    )
                    self.discovered_devices[device.device_id] = device
                
                # Load discovery tasks
                cursor = conn.execute("SELECT * FROM discovery_tasks WHERE enabled = TRUE")
                for row in cursor.fetchall():
                    task = DiscoveryTask(
                        task_id=row['task_id'],
                        name=row['name'],
                        description=row['description'],
                        network_ranges=json.loads(row['network_ranges']) if row['network_ranges'] else [],
                        discovery_methods=[DiscoveryMethod(m) for m in json.loads(row['discovery_methods'])] if row['discovery_methods'] else [],
                        enabled=bool(row['enabled']),
                        schedule_type=row['schedule_type'],
                        interval_seconds=row['interval_seconds'],
                        cron_expression=row['cron_expression'],
                        port_scan_enabled=bool(row['port_scan_enabled']),
                        service_detection_enabled=bool(row['service_detection_enabled']),
                        os_detection_enabled=bool(row['os_detection_enabled']),
                        vulnerability_scan_enabled=bool(row['vulnerability_scan_enabled']),
                        max_concurrent_scans=row['max_concurrent_scans'],
                        scan_timeout=row['scan_timeout'],
                        last_run=datetime.fromisoformat(row['last_run']) if row['last_run'] else None,
                        next_run=datetime.fromisoformat(row['next_run']) if row['next_run'] else None,
                        devices_discovered=row['devices_discovered'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    )
                    self.discovery_tasks[task.task_id] = task
                
            logger.info(f"Loaded {len(self.network_ranges)} ranges, {len(self.discovered_devices)} devices, {len(self.discovery_tasks)} tasks")
            
        except Exception as e:
            logger.error(f"Error loading discovery data: {e}")
    
    async def _start_background_tasks(self):
        """Start background discovery tasks."""
        tasks = [
            self._discovery_scheduler(),
            self._device_monitor(),
            self._cleanup_old_devices()
        ]
        
        for task_coro in tasks:
            task = asyncio.create_task(task_coro)
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
    
    async def add_network_range(self, network_range: NetworkRange) -> str:
        """Add a network range for discovery."""
        try:
            # Validate CIDR
            ipaddress.ip_network(network_range.cidr, strict=False)
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO network_ranges (
                        range_id, name, cidr, description, enabled, scan_frequency
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    network_range.range_id, network_range.name, network_range.cidr,
                    network_range.description, network_range.enabled, network_range.scan_frequency
                ))
                conn.commit()
            
            # Store in memory
            self.network_ranges[network_range.range_id] = network_range
            
            logger.info(f"Added network range: {network_range.name} ({network_range.cidr})")
            return network_range.range_id
            
        except Exception as e:
            logger.error(f"Error adding network range: {e}")
            raise
    
    async def create_discovery_task(self, task: DiscoveryTask) -> str:
        """Create a new discovery task."""
        try:
            # Calculate next run time
            if task.schedule_type == "interval":
                task.next_run = datetime.utcnow() + timedelta(seconds=task.interval_seconds)
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO discovery_tasks (
                        task_id, name, description, network_ranges, discovery_methods,
                        enabled, schedule_type, interval_seconds, cron_expression,
                        port_scan_enabled, service_detection_enabled, os_detection_enabled,
                        vulnerability_scan_enabled, max_concurrent_scans, scan_timeout,
                        next_run, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task.task_id, task.name, task.description,
                    json.dumps(task.network_ranges),
                    json.dumps([m.value for m in task.discovery_methods]),
                    task.enabled, task.schedule_type, task.interval_seconds, task.cron_expression,
                    task.port_scan_enabled, task.service_detection_enabled, task.os_detection_enabled,
                    task.vulnerability_scan_enabled, task.max_concurrent_scans, task.scan_timeout,
                    task.next_run, task.created_at, task.updated_at
                ))
                conn.commit()
            
            # Store in memory
            self.discovery_tasks[task.task_id] = task
            
            logger.info(f"Created discovery task: {task.name}")
            return task.task_id
            
        except Exception as e:
            logger.error(f"Error creating discovery task: {e}")
            raise
    
    async def run_discovery_task(self, task_id: str) -> Dict[str, Any]:
        """Run a discovery task manually."""
        if task_id not in self.discovery_tasks:
            raise ValueError(f"Discovery task not found: {task_id}")
        
        task = self.discovery_tasks[task_id]
        
        if task_id in self.active_scans:
            raise ValueError(f"Discovery task already running: {task_id}")
        
        try:
            self.active_scans.add(task_id)
            
            # Create scan record
            scan_id = f"scan_{secrets.token_urlsafe(8)}"
            start_time = datetime.utcnow()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO discovery_history (
                        scan_id, task_id, started_at, status
                    ) VALUES (?, ?, ?, ?)
                """, (scan_id, task_id, start_time, "running"))
                conn.commit()
            
            # Run discovery
            results = await self._execute_discovery_task(task, scan_id)
            
            # Update scan record
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE discovery_history SET
                        completed_at = ?, devices_found = ?, new_devices = ?,
                        updated_devices = ?, scan_duration_seconds = ?, status = ?
                    WHERE scan_id = ?
                """, (
                    end_time, results['devices_found'], results['new_devices'],
                    results['updated_devices'], duration, "completed", scan_id
                ))
                
                # Update task
                conn.execute("""
                    UPDATE discovery_tasks SET
                        last_run = ?, devices_discovered = devices_discovered + ?
                    WHERE task_id = ?
                """, (start_time, results['new_devices'], task_id))
                
                conn.commit()
            
            # Update task in memory
            task.last_run = start_time
            task.devices_discovered += results['new_devices']
            
            logger.info(f"Discovery task completed: {task_id} - {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error running discovery task: {e}")
            
            # Update scan record with error
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE discovery_history SET
                        completed_at = ?, status = ?, error_message = ?
                    WHERE scan_id = ?
                """, (datetime.utcnow(), "failed", str(e), scan_id))
                conn.commit()
            
            raise
        
        finally:
            self.active_scans.discard(task_id)
    
    async def _execute_discovery_task(self, task: DiscoveryTask, scan_id: str) -> Dict[str, Any]:
        """Execute a discovery task."""
        devices_found = 0
        new_devices = 0
        updated_devices = 0
        
        # Process each network range
        for range_id in task.network_ranges:
            if range_id not in self.network_ranges:
                continue
            
            network_range = self.network_ranges[range_id]
            
            # Scan network range
            range_results = await self._scan_network_range(network_range, task)
            
            devices_found += range_results['devices_found']
            new_devices += range_results['new_devices']
            updated_devices += range_results['updated_devices']
        
        return {
            'devices_found': devices_found,
            'new_devices': new_devices,
            'updated_devices': updated_devices
        }
    
    async def _scan_network_range(self, network_range: NetworkRange, task: DiscoveryTask) -> Dict[str, Any]:
        """Scan a specific network range."""
        try:
            network = ipaddress.ip_network(network_range.cidr, strict=False)
            
            devices_found = 0
            new_devices = 0
            updated_devices = 0
            
            # Create semaphore for concurrent scanning
            semaphore = asyncio.Semaphore(task.max_concurrent_scans)
            
            # Scan each IP in the network
            scan_tasks = []
            for ip in network.hosts():
                if len(scan_tasks) >= 1000:  # Limit to prevent memory issues
                    break
                
                scan_task = self._scan_single_host(str(ip), network_range, task, semaphore)
                scan_tasks.append(scan_task)
            
            # Execute scans concurrently
            results = await asyncio.gather(*scan_tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Scan error: {result}")
                    continue
                
                if result:
                    devices_found += 1
                    if result['is_new']:
                        new_devices += 1
                    else:
                        updated_devices += 1
            
            # Update network range
            network_range.last_scan = datetime.utcnow()
            network_range.discovered_devices = devices_found
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE network_ranges SET
                        last_scan = ?, discovered_devices = ?
                    WHERE range_id = ?
                """, (network_range.last_scan, network_range.discovered_devices, network_range.range_id))
                conn.commit()
            
            logger.info(f"Scanned network range {network_range.cidr}: {devices_found} devices found")
            
            return {
                'devices_found': devices_found,
                'new_devices': new_devices,
                'updated_devices': updated_devices
            }
            
        except Exception as e:
            logger.error(f"Error scanning network range {network_range.cidr}: {e}")
            return {'devices_found': 0, 'new_devices': 0, 'updated_devices': 0}
    
    async def _scan_single_host(self, ip_address: str, network_range: NetworkRange, 
                               task: DiscoveryTask, semaphore: asyncio.Semaphore) -> Optional[Dict[str, Any]]:
        """Scan a single host."""
        async with semaphore:
            try:
                # Check if host is alive
                if not await self._ping_host(ip_address, task.scan_timeout):
                    return None
                
                # Get existing device or create new one
                existing_device = None
                for device in self.discovered_devices.values():
                    if device.ip_address == ip_address:
                        existing_device = device
                        break
                
                is_new = existing_device is None
                
                if existing_device:
                    device = existing_device
                    device.last_seen = datetime.utcnow()
                else:
                    device = DiscoveredDevice(
                        device_id="",  # Will be generated
                        ip_address=ip_address,
                        network_range_id=network_range.range_id
                    )
                
                # Perform discovery methods
                if DiscoveryMethod.NETWORK_SCAN in task.discovery_methods:
                    await self._network_scan_device(device, task)
                
                # Store/update device
                await self._store_device(device)
                
                return {'device': device, 'is_new': is_new}
                
            except Exception as e:
                logger.debug(f"Error scanning host {ip_address}: {e}")
                return None
    
    async def _ping_host(self, ip_address: str, timeout: int = 5) -> bool:
        """Check if a host is alive using ping."""
        try:
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip_address]
            else:
                cmd = ["ping", "-c", "1", "-W", str(timeout), ip_address]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            await asyncio.wait_for(process.wait(), timeout=timeout + 5)
            return process.returncode == 0
            
        except Exception:
            return False
    
    async def _network_scan_device(self, device: DiscoveredDevice, task: DiscoveryTask):
        """Perform network scanning on a device."""
        try:
            # Port scanning
            if task.port_scan_enabled:
                device.open_ports = await self._scan_ports(device.ip_address, task.scan_timeout)
            
            # Service detection
            if task.service_detection_enabled and device.open_ports:
                device.services = await self._detect_services(device.ip_address, device.open_ports)
            
            # OS detection
            if task.os_detection_enabled:
                os_info = await self._detect_os(device.ip_address, device.open_ports)
                if os_info:
                    device.operating_system = os_info.get('os', OperatingSystem.UNKNOWN)
                    device.os_version = os_info.get('version')
            
            # Hostname resolution
            try:
                hostname = socket.gethostbyaddr(device.ip_address)[0]
                device.hostname = hostname
            except:
                pass
            
            # Device type detection
            device.device_type = self._classify_device_type(device)
            
        except Exception as e:
            logger.debug(f"Error in network scan for {device.ip_address}: {e}")
    
    async def _scan_ports(self, ip_address: str, timeout: int) -> List[int]:
        """Scan common ports on a host."""
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 1433, 3306, 3389, 5432, 5900, 8080]
        open_ports = []
        
        async def scan_port(port: int) -> bool:
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip_address, port),
                    timeout=timeout
                )
                writer.close()
                await writer.wait_closed()
                return True
            except:
                return False
        
        # Scan ports concurrently
        tasks = [scan_port(port) for port in common_ports]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for port, result in zip(common_ports, results):
            if result is True:
                open_ports.append(port)
        
        return open_ports
    
    async def _detect_services(self, ip_address: str, open_ports: List[int]) -> Dict[int, str]:
        """Detect services running on open ports."""
        services = {}
        
        # Common service mappings
        service_map = {
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            143: "IMAP",
            443: "HTTPS",
            993: "IMAPS",
            995: "POP3S",
            1433: "MSSQL",
            3306: "MySQL",
            3389: "RDP",
            5432: "PostgreSQL",
            5900: "VNC",
            8080: "HTTP-Alt"
        }
        
        for port in open_ports:
            if port in service_map:
                services[port] = service_map[port]
            else:
                services[port] = "Unknown"
        
        return services
    
    async def _detect_os(self, ip_address: str, open_ports: List[int]) -> Optional[Dict[str, Any]]:
        """Detect operating system based on open ports and behavior."""
        # Simple OS detection based on common port patterns
        if 3389 in open_ports:  # RDP
            return {'os': OperatingSystem.WINDOWS, 'version': None}
        elif 22 in open_ports and 80 in open_ports:  # SSH + HTTP
            return {'os': OperatingSystem.LINUX, 'version': None}
        elif 22 in open_ports:  # SSH only
            return {'os': OperatingSystem.UNIX, 'version': None}
        
        return None
    
    def _classify_device_type(self, device: DiscoveredDevice) -> DeviceType:
        """Classify device type based on discovered information."""
        # Classification based on open ports and services
        if 3389 in device.open_ports:  # RDP
            return DeviceType.WORKSTATION
        elif 80 in device.open_ports or 443 in device.open_ports:  # Web services
            if 22 in device.open_ports:  # SSH
                return DeviceType.SERVER
            else:
                return DeviceType.WORKSTATION
        elif 22 in device.open_ports:  # SSH only
            return DeviceType.SERVER
        elif device.hostname and 'printer' in device.hostname.lower():
            return DeviceType.PRINTER
        
        return DeviceType.UNKNOWN
    
    async def _store_device(self, device: DiscoveredDevice):
        """Store or update a discovered device."""
        try:
            # Check if device exists
            existing = device.device_id in self.discovered_devices
            
            if existing:
                # Update existing device
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE discovered_devices SET
                            hostname = ?, device_type = ?, operating_system = ?, os_version = ?,
                            last_seen = ?, open_ports = ?, services = ?, manufacturer = ?,
                            model = ?, agent_installed = ?, agent_version = ?, agent_status = ?,
                            tags = ?, metadata = ?
                        WHERE device_id = ?
                    """, (
                        device.hostname, device.device_type.value, device.operating_system.value,
                        device.os_version, device.last_seen, json.dumps(device.open_ports),
                        json.dumps(device.services), device.manufacturer, device.model,
                        device.agent_installed, device.agent_version, device.agent_status,
                        json.dumps(device.tags), json.dumps(device.metadata), device.device_id
                    ))
                    conn.commit()
            else:
                # Insert new device
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO discovered_devices (
                            device_id, ip_address, mac_address, hostname, device_type,
                            operating_system, os_version, discovery_method, discovered_at,
                            last_seen, open_ports, services, network_range_id, manufacturer,
                            model, serial_number, installed_software, running_processes,
                            vulnerabilities, security_score, agent_installed, agent_version,
                            agent_status, tags, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        device.device_id, device.ip_address, device.mac_address, device.hostname,
                        device.device_type.value, device.operating_system.value, device.os_version,
                        device.discovery_method.value, device.discovered_at, device.last_seen,
                        json.dumps(device.open_ports), json.dumps(device.services),
                        device.network_range_id, device.manufacturer, device.model,
                        device.serial_number, json.dumps(device.installed_software),
                        json.dumps(device.running_processes), json.dumps(device.vulnerabilities),
                        device.security_score, device.agent_installed, device.agent_version,
                        device.agent_status, json.dumps(device.tags), json.dumps(device.metadata)
                    ))
                    conn.commit()
            
            # Store in memory
            self.discovered_devices[device.device_id] = device
            
        except Exception as e:
            logger.error(f"Error storing device {device.device_id}: {e}")
    
    async def _discovery_scheduler(self):
        """Background task scheduler for discovery tasks."""
        while not self._shutdown_event.is_set():
            try:
                now = datetime.utcnow()
                
                # Check for tasks that need to run
                for task in self.discovery_tasks.values():
                    if (task.enabled and 
                        task.next_run and 
                        task.next_run <= now and 
                        task.task_id not in self.active_scans):
                        
                        # Schedule next run
                        if task.schedule_type == "interval":
                            task.next_run = now + timedelta(seconds=task.interval_seconds)
                        
                        # Run task in background
                        asyncio.create_task(self.run_discovery_task(task.task_id))
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in discovery scheduler: {e}")
                await asyncio.sleep(60)
    
    async def _device_monitor(self):
        """Monitor discovered devices for changes."""
        while not self._shutdown_event.is_set():
            try:
                # Check for devices that haven't been seen recently
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                offline_devices = []
                for device in self.discovered_devices.values():
                    if device.last_seen < cutoff_time:
                        offline_devices.append(device.device_id)
                
                if offline_devices:
                    logger.info(f"Found {len(offline_devices)} potentially offline devices")
                
                await asyncio.sleep(3600)  # Check hourly
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in device monitor: {e}")
                await asyncio.sleep(3600)
    
    async def _cleanup_old_devices(self):
        """Clean up old device records."""
        while not self._shutdown_event.is_set():
            try:
                # Remove devices not seen for 30 days
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        DELETE FROM discovered_devices 
                        WHERE last_seen < ? AND agent_installed = FALSE
                    """, (cutoff_date,))
                    
                    if cursor.rowcount > 0:
                        logger.info(f"Cleaned up {cursor.rowcount} old device records")
                    
                    conn.commit()
                
                await asyncio.sleep(86400)  # Check daily
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in device cleanup: {e}")
                await asyncio.sleep(86400)
    
    async def get_discovery_statistics(self) -> Dict[str, Any]:
        """Get discovery statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Total devices
                cursor = conn.execute("SELECT COUNT(*) as total FROM discovered_devices")
                total_devices = cursor.fetchone()['total']
                
                # Devices by type
                cursor = conn.execute("""
                    SELECT device_type, COUNT(*) as count 
                    FROM discovered_devices 
                    GROUP BY device_type
                """)
                devices_by_type = {row['device_type']: row['count'] for row in cursor.fetchall()}
                
                # Devices by OS
                cursor = conn.execute("""
                    SELECT operating_system, COUNT(*) as count 
                    FROM discovered_devices 
                    GROUP BY operating_system
                """)
                devices_by_os = {row['operating_system']: row['count'] for row in cursor.fetchall()}
                
                # Recent discoveries
                recent_cutoff = datetime.utcnow() - timedelta(days=7)
                cursor = conn.execute("""
                    SELECT COUNT(*) as recent 
                    FROM discovered_devices 
                    WHERE discovered_at >= ?
                """, (recent_cutoff,))
                recent_discoveries = cursor.fetchone()['recent']
                
                # Active scans
                active_scans = len(self.active_scans)
                
                return {
                    "total_devices": total_devices,
                    "devices_by_type": devices_by_type,
                    "devices_by_os": devices_by_os,
                    "recent_discoveries": recent_discoveries,
                    "active_scans": active_scans,
                    "network_ranges": len(self.network_ranges),
                    "discovery_tasks": len(self.discovery_tasks)
                }
                
        except Exception as e:
            logger.error(f"Error getting discovery statistics: {e}")
            return {}
    
    async def get_discovered_devices(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get discovered devices with pagination."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute("""
                    SELECT * FROM discovered_devices 
                    ORDER BY last_seen DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                devices = []
                for row in cursor.fetchall():
                    device_dict = dict(row)
                    # Parse JSON fields
                    device_dict['open_ports'] = json.loads(device_dict['open_ports']) if device_dict['open_ports'] else []
                    device_dict['services'] = json.loads(device_dict['services']) if device_dict['services'] else {}
                    device_dict['tags'] = json.loads(device_dict['tags']) if device_dict['tags'] else []
                    device_dict['metadata'] = json.loads(device_dict['metadata']) if device_dict['metadata'] else {}
                    devices.append(device_dict)
                
                return devices
                
        except Exception as e:
            logger.error(f"Error getting discovered devices: {e}")
            return []
    
    async def shutdown(self):
        """Gracefully shutdown the discovery service."""
        logger.info("Shutting down workstation discovery service...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        logger.info("Workstation discovery service shutdown complete")


# Global discovery service instance
_discovery_service: Optional[WorkstationDiscoveryService] = None

def get_discovery_service() -> WorkstationDiscoveryService:
    """Get or create discovery service instance."""
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = WorkstationDiscoveryService()
    return _discovery_service
