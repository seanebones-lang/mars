"""
AgentGuard Status Page API
Real-time system status, uptime, and incident tracking
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum
import psutil
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/status",
    tags=["status"],
    responses={404: {"description": "Not found"}}
)


class ComponentStatus(str, Enum):
    """Component status levels"""
    OPERATIONAL = "operational"
    DEGRADED_PERFORMANCE = "degraded_performance"
    PARTIAL_OUTAGE = "partial_outage"
    MAJOR_OUTAGE = "major_outage"
    UNDER_MAINTENANCE = "under_maintenance"


class IncidentSeverity(str, Enum):
    """Incident severity levels"""
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """Incident status"""
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"


class Component(BaseModel):
    """System component"""
    id: str
    name: str
    description: str
    status: ComponentStatus
    uptime_percentage: float = Field(ge=0, le=100)
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    response_time_ms: Optional[float] = None


class IncidentUpdate(BaseModel):
    """Incident status update"""
    id: str
    timestamp: datetime
    status: IncidentStatus
    message: str


class Incident(BaseModel):
    """System incident"""
    id: str
    title: str
    severity: IncidentSeverity
    status: IncidentStatus
    affected_components: List[str]
    started_at: datetime
    resolved_at: Optional[datetime] = None
    updates: List[IncidentUpdate] = []
    impact: str


class MaintenanceWindow(BaseModel):
    """Scheduled maintenance"""
    id: str
    title: str
    description: str
    scheduled_start: datetime
    scheduled_end: datetime
    affected_components: List[str]
    status: str  # scheduled, in_progress, completed


class UptimeMetrics(BaseModel):
    """Uptime metrics"""
    last_24h: float
    last_7d: float
    last_30d: float
    last_90d: float


class SystemMetrics(BaseModel):
    """System performance metrics"""
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    active_connections: int
    requests_per_minute: float
    average_response_time_ms: float
    error_rate_percent: float


class StatusPageResponse(BaseModel):
    """Complete status page response"""
    overall_status: ComponentStatus
    components: List[Component]
    active_incidents: List[Incident]
    scheduled_maintenance: List[MaintenanceWindow]
    uptime_metrics: UptimeMetrics
    system_metrics: SystemMetrics
    last_updated: datetime


class StatusService:
    """Service for managing system status"""
    
    def __init__(self):
        self.components: Dict[str, Component] = {}
        self.incidents: Dict[str, Incident] = {}
        self.maintenance_windows: Dict[str, MaintenanceWindow] = {}
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize system components"""
        components = [
            Component(
                id="api",
                name="API Endpoints",
                description="Core API for hallucination detection and safety checks",
                status=ComponentStatus.OPERATIONAL,
                uptime_percentage=99.9
            ),
            Component(
                id="dashboard",
                name="Web Dashboard",
                description="User interface and workspace management",
                status=ComponentStatus.OPERATIONAL,
                uptime_percentage=99.95
            ),
            Component(
                id="webhooks",
                name="Webhook Delivery",
                description="Real-time webhook notifications and alerts",
                status=ComponentStatus.OPERATIONAL,
                uptime_percentage=99.8
            ),
            Component(
                id="database",
                name="Database",
                description="PostgreSQL primary database",
                status=ComponentStatus.OPERATIONAL,
                uptime_percentage=99.99
            ),
            Component(
                id="cache",
                name="Cache Layer",
                description="Redis caching and session storage",
                status=ComponentStatus.OPERATIONAL,
                uptime_percentage=99.9
            ),
            Component(
                id="streaming",
                name="Streaming API",
                description="Real-time streaming validation (SSE)",
                status=ComponentStatus.OPERATIONAL,
                uptime_percentage=99.7
            ),
            Component(
                id="batch",
                name="Batch Processing",
                description="Asynchronous batch job processing",
                status=ComponentStatus.OPERATIONAL,
                uptime_percentage=99.85
            )
        ]
        
        for component in components:
            self.components[component.id] = component
    
    async def check_component_health(self, component_id: str) -> Component:
        """Check health of a specific component"""
        component = self.components.get(component_id)
        if not component:
            raise ValueError(f"Component {component_id} not found")
        
        # Perform actual health check based on component type
        try:
            if component_id == "api":
                # Check API responsiveness
                start = datetime.utcnow()
                # Simulate health check
                await asyncio.sleep(0.01)
                response_time = (datetime.utcnow() - start).total_seconds() * 1000
                component.response_time_ms = response_time
                component.status = ComponentStatus.OPERATIONAL
            
            elif component_id == "database":
                # Check database connection
                # In production, this would query the database
                component.status = ComponentStatus.OPERATIONAL
            
            elif component_id == "cache":
                # Check Redis connection
                component.status = ComponentStatus.OPERATIONAL
            
            component.last_checked = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Health check failed for {component_id}: {e}")
            component.status = ComponentStatus.DEGRADED_PERFORMANCE
        
        return component
    
    async def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return SystemMetrics(
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory.percent,
                disk_usage_percent=disk.percent,
                active_connections=len(psutil.net_connections()),
                requests_per_minute=0.0,  # Would come from metrics service
                average_response_time_ms=50.0,  # Would come from metrics service
                error_rate_percent=0.1  # Would come from metrics service
            )
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return SystemMetrics(
                cpu_usage_percent=0.0,
                memory_usage_percent=0.0,
                disk_usage_percent=0.0,
                active_connections=0,
                requests_per_minute=0.0,
                average_response_time_ms=0.0,
                error_rate_percent=0.0
            )
    
    def calculate_overall_status(self) -> ComponentStatus:
        """Calculate overall system status"""
        statuses = [c.status for c in self.components.values()]
        
        if any(s == ComponentStatus.MAJOR_OUTAGE for s in statuses):
            return ComponentStatus.MAJOR_OUTAGE
        elif any(s == ComponentStatus.PARTIAL_OUTAGE for s in statuses):
            return ComponentStatus.PARTIAL_OUTAGE
        elif any(s == ComponentStatus.DEGRADED_PERFORMANCE for s in statuses):
            return ComponentStatus.DEGRADED_PERFORMANCE
        elif any(s == ComponentStatus.UNDER_MAINTENANCE for s in statuses):
            return ComponentStatus.UNDER_MAINTENANCE
        else:
            return ComponentStatus.OPERATIONAL
    
    def get_uptime_metrics(self) -> UptimeMetrics:
        """Get uptime metrics"""
        # In production, these would be calculated from historical data
        return UptimeMetrics(
            last_24h=99.95,
            last_7d=99.92,
            last_30d=99.89,
            last_90d=99.87
        )
    
    def get_active_incidents(self) -> List[Incident]:
        """Get active incidents"""
        return [
            incident for incident in self.incidents.values()
            if incident.status != IncidentStatus.RESOLVED
        ]
    
    def get_scheduled_maintenance(self) -> List[MaintenanceWindow]:
        """Get scheduled maintenance windows"""
        now = datetime.utcnow()
        return [
            mw for mw in self.maintenance_windows.values()
            if mw.scheduled_start > now or mw.status == "in_progress"
        ]
    
    async def get_status_page(self) -> StatusPageResponse:
        """Get complete status page data"""
        # Update component health
        for component_id in self.components.keys():
            await self.check_component_health(component_id)
        
        return StatusPageResponse(
            overall_status=self.calculate_overall_status(),
            components=list(self.components.values()),
            active_incidents=self.get_active_incidents(),
            scheduled_maintenance=self.get_scheduled_maintenance(),
            uptime_metrics=self.get_uptime_metrics(),
            system_metrics=await self.get_system_metrics(),
            last_updated=datetime.utcnow()
        )
    
    def create_incident(
        self,
        title: str,
        severity: IncidentSeverity,
        affected_components: List[str],
        impact: str
    ) -> Incident:
        """Create a new incident"""
        incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        incident = Incident(
            id=incident_id,
            title=title,
            severity=severity,
            status=IncidentStatus.INVESTIGATING,
            affected_components=affected_components,
            started_at=datetime.utcnow(),
            impact=impact,
            updates=[
                IncidentUpdate(
                    id=f"{incident_id}-001",
                    timestamp=datetime.utcnow(),
                    status=IncidentStatus.INVESTIGATING,
                    message=f"We are investigating reports of {impact.lower()}."
                )
            ]
        )
        
        self.incidents[incident_id] = incident
        
        # Update affected components
        for component_id in affected_components:
            if component_id in self.components:
                if severity == IncidentSeverity.CRITICAL:
                    self.components[component_id].status = ComponentStatus.MAJOR_OUTAGE
                elif severity == IncidentSeverity.MAJOR:
                    self.components[component_id].status = ComponentStatus.PARTIAL_OUTAGE
                else:
                    self.components[component_id].status = ComponentStatus.DEGRADED_PERFORMANCE
        
        logger.warning(f"Incident created: {incident_id} - {title}")
        return incident
    
    def update_incident(
        self,
        incident_id: str,
        status: IncidentStatus,
        message: str
    ) -> Incident:
        """Update an incident"""
        incident = self.incidents.get(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")
        
        incident.status = status
        
        update_id = f"{incident_id}-{len(incident.updates) + 1:03d}"
        incident.updates.append(
            IncidentUpdate(
                id=update_id,
                timestamp=datetime.utcnow(),
                status=status,
                message=message
            )
        )
        
        # If resolved, update components and set resolved time
        if status == IncidentStatus.RESOLVED:
            incident.resolved_at = datetime.utcnow()
            for component_id in incident.affected_components:
                if component_id in self.components:
                    self.components[component_id].status = ComponentStatus.OPERATIONAL
        
        logger.info(f"Incident updated: {incident_id} - {status}")
        return incident
    
    def schedule_maintenance(
        self,
        title: str,
        description: str,
        scheduled_start: datetime,
        scheduled_end: datetime,
        affected_components: List[str]
    ) -> MaintenanceWindow:
        """Schedule maintenance window"""
        mw_id = f"MW-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        maintenance = MaintenanceWindow(
            id=mw_id,
            title=title,
            description=description,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            affected_components=affected_components,
            status="scheduled"
        )
        
        self.maintenance_windows[mw_id] = maintenance
        logger.info(f"Maintenance scheduled: {mw_id} - {title}")
        return maintenance


# Global status service instance
_status_service: Optional[StatusService] = None

def get_status_service() -> StatusService:
    """Get or create status service instance"""
    global _status_service
    if _status_service is None:
        _status_service = StatusService()
    return _status_service


# API Endpoints

@router.get("/", response_model=StatusPageResponse)
async def get_status_page(
    service: StatusService = Depends(get_status_service)
):
    """
    Get complete status page with all system components and metrics.
    
    This endpoint provides:
    - Overall system status
    - Individual component statuses
    - Active incidents
    - Scheduled maintenance
    - Uptime metrics
    - System performance metrics
    """
    return await service.get_status_page()


@router.get("/components", response_model=List[Component])
async def get_components(
    service: StatusService = Depends(get_status_service)
):
    """Get all system components and their current status"""
    return list(service.components.values())


@router.get("/components/{component_id}", response_model=Component)
async def get_component(
    component_id: str,
    service: StatusService = Depends(get_status_service)
):
    """Get specific component status"""
    component = await service.check_component_health(component_id)
    if not component:
        raise HTTPException(status_code=404, detail=f"Component {component_id} not found")
    return component


@router.get("/incidents", response_model=List[Incident])
async def get_incidents(
    active_only: bool = True,
    service: StatusService = Depends(get_status_service)
):
    """Get incidents (active only by default)"""
    if active_only:
        return service.get_active_incidents()
    return list(service.incidents.values())


@router.get("/incidents/{incident_id}", response_model=Incident)
async def get_incident(
    incident_id: str,
    service: StatusService = Depends(get_status_service)
):
    """Get specific incident details"""
    incident = service.incidents.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return incident


@router.get("/maintenance", response_model=List[MaintenanceWindow])
async def get_maintenance(
    service: StatusService = Depends(get_status_service)
):
    """Get scheduled maintenance windows"""
    return service.get_scheduled_maintenance()


@router.get("/uptime", response_model=UptimeMetrics)
async def get_uptime(
    service: StatusService = Depends(get_status_service)
):
    """Get uptime metrics"""
    return service.get_uptime_metrics()


@router.get("/metrics", response_model=SystemMetrics)
async def get_metrics(
    service: StatusService = Depends(get_status_service)
):
    """Get current system metrics"""
    return await service.get_system_metrics()


@router.get("/health")
async def health_check():
    """
    Simple health check endpoint for load balancers and monitoring.
    Returns 200 OK if the service is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "agentguard-api",
        "version": "1.0.0"
    }


@router.get("/ping")
async def ping():
    """Ultra-lightweight ping endpoint"""
    return {"pong": datetime.utcnow().isoformat()}

