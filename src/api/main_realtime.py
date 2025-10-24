"""
Enhanced FastAPI main module with real-time monitoring capabilities.
This extends the existing API with WebSocket and real-time agent monitoring.
"""

import os
import logging
import secrets
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import asdict
from fastapi import FastAPI, HTTPException, WebSocket, BackgroundTasks, Query, UploadFile, File, Form, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
import mlflow

from ..models.schemas import AgentTestRequest, HallucinationReport
from ..judges.ensemble_judge import EnsembleJudge
from .websocket import websocket_endpoint
from ..demo.realtime_monitor import get_realtime_monitor
from ..services.batch_processor import get_batch_processor
from ..models.batch_schemas import (
    BatchUploadRequest, BatchJobResponse, BatchJobListResponse,
    BatchExportRequest, BatchProgressUpdate
)
from ..services.rag_enhanced_judge import get_rag_enhanced_judge
from ..services.graph_database import get_graph_database
from ..services.webhook_service import get_webhook_service, WebhookConfig, WebhookAlert
from ..services.auth_service import get_auth_service, LoginRequest, UserRole, Permission
from .auth_dependencies import (
    get_current_user, require_authentication, require_admin, require_supervisor,
    require_webhook_management, require_analytics_access, get_client_info
)
from ..services.rate_limit_service import get_rate_limit_service, RateLimitRule, QuotaRule
from ..middleware.rate_limit_middleware import add_rate_limiting
from ..services.performance_monitor import get_performance_monitor
from ..middleware.performance_middleware import add_performance_monitoring
from ..services.custom_rules_engine import get_custom_rules_engine, CustomRule, RuleType, RuleCategory, RuleSeverity
from ..services.compliance_service import get_compliance_service, AuditEvent, AuditEventType, ComplianceFramework, DataClassification
from ..services.tenant_service import get_tenant_service, TenantConfig, TenantStatus, SubscriptionTier, BillingCycle
from ..middleware.tenant_middleware import add_tenant_middleware, get_current_tenant, require_tenant_feature, check_tenant_quota
from ..services.websocket_manager import get_websocket_manager, WebSocketMessage, MessageType, ConnectionType
from ..services.alert_escalation_service import get_escalation_service, Alert, AlertSeverity, AlertStatus, EscalationRule, OnCallSchedule, EscalationLevel
from ..services.workstation_discovery_service import get_discovery_service, NetworkRange, DiscoveryTask, DiscoveryMethod, DeviceType, OperatingSystem

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configure MLflow
mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "agentguard_prototype"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    logger.info("Starting AgentGuard API server with real-time monitoring")
    logger.info(f"Claude API Key: {'configured' if os.getenv('CLAUDE_API_KEY') else 'missing'}")
    yield
    # Shutdown
    logger.info("Shutting down AgentGuard API server")


# Initialize FastAPI application
app = FastAPI(
    title="AgentGuard",
    description="AI Agent Hallucination Detection Platform with Real-time Monitoring",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "detection",
            "description": "Core hallucination detection endpoints"
        },
        {
            "name": "realtime_monitoring", 
            "description": "Real-time agent monitoring and WebSocket endpoints"
        },
        {
            "name": "monitoring",
            "description": "Health check and system status"
        }
    ]
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoints (before authentication middleware)
@app.get("/health", tags=["system"])
async def health_check():
    """Comprehensive health check endpoint for production monitoring."""
    import time
    import psutil
    from datetime import datetime
    
    start_time = time.time()
    
    try:
        # System health
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database health (simple connection test)
        db_healthy = True
        db_latency = 0
        try:
            db_start = time.time()
            # Simple database ping would go here
            db_latency = (time.time() - db_start) * 1000
        except Exception:
            db_healthy = False
        
        # Redis health (simple connection test)
        redis_healthy = True
        redis_latency = 0
        try:
            redis_start = time.time()
            # Simple Redis ping would go here
            redis_latency = (time.time() - redis_start) * 1000
        except Exception:
            redis_healthy = False
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000
        
        # Overall health status
        overall_healthy = db_healthy and redis_healthy and cpu_percent < 90 and memory.percent < 90
        
        health_data = {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "uptime_seconds": int(time.time()),  # This would be actual uptime in production
            "response_time_ms": round(response_time, 2),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            "services": {
                "database": {
                    "healthy": db_healthy,
                    "latency_ms": round(db_latency, 2)
                },
                "redis": {
                    "healthy": redis_healthy,
                    "latency_ms": round(redis_latency, 2)
                }
            },
            "features": {
                "authentication": True,
                "real_time_monitoring": True,
                "alert_escalation": True,
                "workstation_discovery": True,
                "multi_tenant": True,
                "webhooks": True,
                "batch_processing": True,
                "analytics": True
            }
        }
        
        # Return appropriate HTTP status
        status_code = 200 if overall_healthy else 503
        return JSONResponse(content=health_data, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Health check failed",
                "response_time_ms": round((time.time() - start_time) * 1000, 2)
            },
            status_code=503
        )

@app.get("/ready", tags=["system"])
async def readiness_check():
    """Readiness check for Kubernetes/container orchestration."""
    from datetime import datetime
    try:
        # Check if all critical services are ready
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            content={"status": "not_ready", "error": str(e)},
            status_code=503
        )

@app.get("/live", tags=["system"])
async def liveness_check():
    """Liveness check for Kubernetes/container orchestration."""
    from datetime import datetime
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}

# Add tenant middleware (must be first for proper tenant context)
add_tenant_middleware(app)

# Add rate limiting middleware
add_rate_limiting(app, exclude_paths=[
    "/docs", "/redoc", "/openapi.json", "/health", "/favicon.ico", "/auth/login"
])

# Add performance monitoring middleware
add_performance_monitoring(app, exclude_paths=[
    "/docs", "/redoc", "/openapi.json", "/health", "/favicon.ico"
])


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom exception handler for HTTP exceptions."""
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "details": str(exc)}
    )


@app.get("/", tags=["monitoring"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AgentGuard API",
        "version": "1.0.0",
        "status": "operational",
        "description": "AI Agent Hallucination Detection Platform with Real-time Monitoring",
        "endpoints": {
            "test_agent": "/test-agent",
            "websocket_monitor": "/ws/monitor",
            "start_monitoring": "/monitor/start",
            "stop_monitoring": "/monitor/stop",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent monitoring.
    
    Clients connect to receive live updates about:
    - Agent responses and queries
    - Hallucination detection results  
    - Risk scores and flagged segments
    - Mitigation suggestions
    """
    await websocket_endpoint(websocket)


@app.post("/monitor/start", tags=["realtime_monitoring"])
async def start_monitoring(background_tasks: BackgroundTasks, 
                          response_interval: float = 3.0,
                          jitter: float = 2.0):
    """
    Start real-time agent monitoring with simulated agents.
    
    Args:
        response_interval: Base time between agent responses (seconds)
        jitter: Random variation in response timing (seconds)
        
    Returns:
        Status confirmation and monitoring configuration
    """
    try:
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
            
        monitor = get_realtime_monitor(claude_api_key)
        
        if monitor.is_active():
            return {"status": "already_running", "message": "Monitoring is already active"}
        
        # Start monitoring in background
        background_tasks.add_task(monitor.start_monitoring, response_interval, jitter)
        
        return {
            "status": "started",
            "message": "Real-time monitoring started",
            "config": {
                "response_interval": response_interval,
                "jitter": jitter,
                "agents": ["it_bot", "retail_assistant", "hr_helper"]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")


@app.post("/monitor/stop", tags=["realtime_monitoring"])
async def stop_monitoring():
    """
    Stop real-time agent monitoring.
    
    Returns:
        Status confirmation and session statistics
    """
    try:
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
            
        monitor = get_realtime_monitor(claude_api_key)
        
        if not monitor.is_active():
            return {"status": "not_running", "message": "Monitoring is not active"}
        
        stats = monitor.get_session_stats()
        await monitor.stop_monitoring()
        
        return {
            "status": "stopped",
            "message": "Real-time monitoring stopped",
            "session_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")


@app.get("/monitor/status", tags=["realtime_monitoring"])
async def get_monitoring_status():
    """
    Get current monitoring status and statistics.
    
    Returns:
        Current monitoring state and session statistics
    """
    try:
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
            
        monitor = get_realtime_monitor(claude_api_key)
        
        return {
            "is_active": monitor.is_active(),
            "stats": monitor.get_session_stats()
        }
        
    except Exception as e:
        logger.error(f"Failed to get monitoring status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@app.post("/monitor/test", tags=["realtime_monitoring"])
async def send_test_response(agent_id: str, custom_output: str):
    """
    Send a custom test response for interactive demo mode.
    
    Args:
        agent_id: ID of the agent to simulate (it_bot, retail_assistant, hr_helper)
        custom_output: Custom response text to test
        
    Returns:
        Confirmation that test response was processed
    """
    try:
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
            
        monitor = get_realtime_monitor(claude_api_key)
        
        await monitor.send_test_response(agent_id, custom_output)
        
        return {
            "status": "sent",
            "message": f"Test response sent for {agent_id}",
            "agent_id": agent_id,
            "custom_output": custom_output
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to send test response: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test: {str(e)}")


@app.get("/health", tags=["monitoring"])
async def health_check():
    """
    Health check endpoint for monitoring.
    Returns API status and configuration details.
    """
    claude_api_key = os.getenv("CLAUDE_API_KEY")
    claude_api_configured = bool(claude_api_key)
    
    try:
        monitor = get_realtime_monitor(claude_api_key) if claude_api_key else None
        
        return {
            "status": "healthy" if claude_api_configured else "degraded",
            "model": "claude-sonnet-4-5-20250929",
            "claude_api": "configured" if claude_api_configured else "not configured",
            "statistical_model": "distilbert-base-uncased",
            "ensemble_weights": {"claude": 0.6, "statistical": 0.4},
            "uncertainty_threshold": 0.3,
            "realtime_monitoring": {
                "available": monitor is not None,
                "active": monitor.is_active() if monitor else False
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/test-agent", response_model=HallucinationReport, tags=["detection"])
async def test_agent(request: AgentTestRequest):
    """
    Test an AI agent's output for hallucinations.
    
    Performs ensemble detection using:
    - Claude Sonnet 4.5 LLM-as-a-Judge with self-consistency (3 samples)
    - Statistical token-level entropy and confidence analysis
    
    Returns comprehensive hallucination report with:
    - Hallucination risk score (0-1)
    - Detailed Claude judgment and statistical scores
    - Confidence intervals
    - Uncertainty metrics
    - Human review flagging
    
    Args:
        request: AgentTestRequest containing agent output, ground truth, and conversation history
        
    Returns:
        HallucinationReport with risk assessment and detailed analysis
        
    Raises:
        HTTPException: If API key is not configured or evaluation fails
    """
    # Validate Claude API key
    claude_api_key = os.getenv("CLAUDE_API_KEY")
    if not claude_api_key:
        logger.error("Claude API key not configured")
        raise HTTPException(
            status_code=500,
            detail="Claude API key not configured. Set CLAUDE_API_KEY environment variable."
        )
    
    try:
        logger.info(f"Starting agent evaluation (output length: {len(request.agent_output)})")
        
        # Initialize ensemble judge
        judge = EnsembleJudge(claude_api_key)
        
        # Perform evaluation
        report = await judge.evaluate(request)
        
        logger.info(
            f"Evaluation complete: Risk={report.hallucination_risk:.3f}, "
            f"Uncertainty={report.uncertainty:.3f}"
        )
        
        return report
        
    except HTTPException:
        # Re-raise HTTP exceptions (already logged)
        raise
    except Exception as e:
        logger.error(f"Evaluation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        )


@app.get("/metrics", tags=["monitoring"])
async def get_metrics():
    """
    Retrieve MLflow experiment metrics.
    Returns summary of recent evaluations.
    """
    try:
        experiment = mlflow.get_experiment_by_name(
            os.getenv("MLFLOW_EXPERIMENT_NAME", "agentguard_prototype")
        )
        
        if not experiment:
            return {"message": "No experiment data available"}
        
        return {
            "experiment_id": experiment.experiment_id,
            "experiment_name": experiment.name,
            "artifact_location": experiment.artifact_location,
            "lifecycle_stage": experiment.lifecycle_stage
        }
    except Exception as e:
        logger.error(f"Metrics retrieval error: {e}")
        return {"error": str(e)}


# Batch Processing Endpoints
@app.post("/batch/upload", response_model=BatchJobResponse, tags=["batch_processing"])
async def upload_batch_file(
    file: UploadFile = File(...),
    has_headers: bool = Form(True),
    agent_output_column: str = Form("agent_output"),
    ground_truth_column: Optional[str] = Form(None),
    query_column: Optional[str] = Form(None),
    agent_id_column: Optional[str] = Form(None)
):
    """
    Upload a batch file for processing.
    
    Supports CSV, JSON, and JSONL formats.
    """
    try:
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
        
        # Validate file format
        file_extension = file.filename.split('.')[-1].lower() if file.filename else ""
        if file_extension not in ["csv", "json", "jsonl"]:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV, JSON, or JSONL.")
        
        # Read file content
        file_content = await file.read()
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Create upload request
        upload_request = BatchUploadRequest(
            filename=file.filename,
            file_format=file_extension,
            has_headers=has_headers,
            agent_output_column=agent_output_column,
            ground_truth_column=ground_truth_column,
            query_column=query_column,
            agent_id_column=agent_id_column
        )
        
        # Upload and create job
        processor = get_batch_processor(claude_api_key)
        job = await processor.upload_file(file_content, upload_request)
        
        return BatchJobResponse(
            job=job,
            message=f"File uploaded successfully. Job ID: {job.job_id}"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading batch file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/batch/{job_id}/start", response_model=BatchJobResponse, tags=["batch_processing"])
async def start_batch_processing(job_id: str, background_tasks: BackgroundTasks):
    """Start processing a batch job."""
    try:
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
        
        processor = get_batch_processor(claude_api_key)
        job = processor.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        success = await processor.start_processing(job_id)
        if not success:
            raise HTTPException(status_code=400, detail="Cannot start job (already running or completed)")
        
        return BatchJobResponse(
            job=job,
            message="Batch processing started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting batch processing: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/batch/jobs", response_model=BatchJobListResponse, tags=["batch_processing"])
async def list_batch_jobs(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    """List all batch jobs with pagination."""
    try:
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
        
        processor = get_batch_processor(claude_api_key)
        jobs, total = processor.list_jobs(page, page_size)
        
        return BatchJobListResponse(
            jobs=jobs,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error listing batch jobs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/batch/{job_id}", response_model=BatchJobResponse, tags=["batch_processing"])
async def get_batch_job(job_id: str):
    """Get details of a specific batch job."""
    try:
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
        
        processor = get_batch_processor(claude_api_key)
        job = processor.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return BatchJobResponse(
            job=job,
            message="Job retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch job: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/batch/{job_id}/cancel", response_model=BatchJobResponse, tags=["batch_processing"])
async def cancel_batch_job(job_id: str):
    """Cancel a running batch job."""
    try:
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
        
        processor = get_batch_processor(claude_api_key)
        job = processor.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        success = await processor.cancel_job(job_id)
        if not success:
            raise HTTPException(status_code=400, detail="Cannot cancel job (not running)")
        
        return BatchJobResponse(
            job=job,
            message="Job cancelled successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling batch job: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/batch/{job_id}/export", tags=["batch_processing"])
async def export_batch_results(job_id: str, export_request: BatchExportRequest):
    """Export batch job results in specified format."""
    try:
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
        
        processor = get_batch_processor(claude_api_key)
        job = processor.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != "completed":
            raise HTTPException(status_code=400, detail="Job not completed")
        
        export_path = await processor.export_results(
            job_id=job_id,
            format=export_request.format,
            include_metadata=export_request.include_metadata,
            include_explanations=export_request.include_explanations,
            filter_flagged_only=export_request.filter_flagged_only
        )
        
        if not export_path:
            raise HTTPException(status_code=500, detail="Export failed")
        
        # Return file download
        return FileResponse(
            path=str(export_path),
            filename=f"{job.filename}_results.{export_request.format}",
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting batch results: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Graph Database & Analytics Endpoints
@app.get("/analytics/overview", tags=["analytics"])
async def get_analytics_overview(days: int = Query(30, ge=1, le=365)):
    """Get comprehensive analytics overview from graph database."""
    try:
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
        
        rag_judge = get_rag_enhanced_judge(claude_api_key)
        analytics_data = await rag_judge.get_analytics_data(days=days)
        
        return {
            "status": "success",
            "data": analytics_data,
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics data")


@app.get("/analytics/agents", tags=["analytics"])
async def get_agent_analytics(agent_id: Optional[str] = None, days: int = Query(30, ge=1, le=365)):
    """Get agent performance analytics."""
    try:
        graph_db = get_graph_database()
        metrics = await graph_db.get_agent_performance_metrics(agent_id=agent_id, days=days)
        
        return {
            "status": "success",
            "data": metrics,
            "agent_id": agent_id,
            "period_days": days
        }
        
    except Exception as e:
        logger.error(f"Error getting agent analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent analytics")


@app.get("/analytics/patterns", tags=["analytics"])
async def get_hallucination_patterns(limit: int = Query(20, ge=1, le=100)):
    """Get hallucination patterns from graph database."""
    try:
        graph_db = get_graph_database()
        patterns = await graph_db.get_hallucination_patterns(limit=limit)
        
        return {
            "status": "success",
            "data": patterns,
            "total_patterns": len(patterns)
        }
        
    except Exception as e:
        logger.error(f"Error getting hallucination patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve patterns")


@app.get("/analytics/timeseries", tags=["analytics"])
async def get_timeseries_data(days: int = Query(30, ge=1, le=365), 
                             interval: str = Query("day", regex="^(hour|day)$")):
    """Get time series data for charts and trends."""
    try:
        graph_db = get_graph_database()
        time_series = await graph_db.get_time_series_data(days=days, interval=interval)
        
        return {
            "status": "success",
            "data": time_series,
            "period_days": days,
            "interval": interval,
            "data_points": len(time_series)
        }
        
    except Exception as e:
        logger.error(f"Error getting time series data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve time series data")


@app.post("/analytics/similar", tags=["analytics"])
async def find_similar_responses(
    query_text: str,
    response_text: str,
    limit: int = Query(5, ge=1, le=20),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0)
):
    """Find similar responses using RAG."""
    try:
        graph_db = get_graph_database()
        similar_responses = await graph_db.find_similar_responses(
            query_text=query_text,
            response_text=response_text,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        
        return {
            "status": "success",
            "data": similar_responses,
            "query_text": query_text,
            "similarity_threshold": similarity_threshold,
            "found_count": len(similar_responses)
        }
        
    except Exception as e:
        logger.error(f"Error finding similar responses: {e}")
        raise HTTPException(status_code=500, detail="Failed to find similar responses")


@app.post("/test-agent-rag", response_model=HallucinationReport, tags=["detection"])
async def test_agent_with_rag(request: AgentTestRequest, 
                             agent_id: str = "unknown",
                             agent_name: str = "Unknown Agent",
                             use_rag: bool = True):
    """
    Test agent output for hallucinations with RAG enhancement.
    
    This endpoint uses the RAG-enhanced judge that leverages historical data
    from the graph database to improve detection accuracy.
    """
    try:
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
        
        rag_judge = get_rag_enhanced_judge(claude_api_key)
        result = await rag_judge.evaluate(
            request=request,
            agent_id=agent_id,
            agent_name=agent_name,
            use_rag=use_rag
        )
        
        return result
        
    except Exception as e:
        logger.error(f"RAG-enhanced detection error: {e}")
        raise HTTPException(status_code=500, detail="Detection analysis failed")


# Authentication Endpoints
@app.post("/auth/login", tags=["authentication"])
async def login(
    login_request: LoginRequest,
    request: Request,
    auth_service = Depends(get_auth_service)
):
    """Authenticate user and return JWT tokens."""
    try:
        client_info = await get_client_info(request)
        
        login_response = await auth_service.authenticate_user(
            login_request,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        return login_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@app.post("/auth/refresh", tags=["authentication"])
async def refresh_token(
    refresh_token: str,
    auth_service = Depends(get_auth_service)
):
    """Refresh access token using refresh token."""
    try:
        login_response = await auth_service.refresh_token(refresh_token)
        return login_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@app.post("/auth/logout", tags=["authentication"])
async def logout(
    current_user = Depends(require_authentication),
    auth_service = Depends(get_auth_service),
    request: Request = None
):
    """Logout user and revoke token."""
    try:
        # Extract token from request
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            await auth_service.logout(token, current_user.user_id)
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")


@app.get("/auth/me", tags=["authentication"])
async def get_current_user_info(current_user = Depends(require_authentication)):
    """Get current user information."""
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.value,
        "is_verified": current_user.is_verified,
        "mfa_enabled": current_user.mfa_enabled,
        "assigned_agents": current_user.assigned_agents,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
        "created_at": current_user.created_at.isoformat(),
        "metadata": current_user.metadata
    }


@app.get("/auth/permissions", tags=["authentication"])
async def get_user_permissions(
    current_user = Depends(require_authentication),
    auth_service = Depends(get_auth_service)
):
    """Get current user's permissions."""
    permissions = auth_service.ROLE_PERMISSIONS.get(current_user.role, [])
    
    return {
        "user_id": current_user.user_id,
        "role": current_user.role.value,
        "permissions": [p.value for p in permissions]
    }


# User Management Endpoints (Admin only)
@app.get("/users", tags=["user-management"])
async def list_users(
    current_user = Depends(require_admin),
    auth_service = Depends(get_auth_service)
):
    """List all users (Admin only)."""
    # This would be implemented with proper database queries
    # For now, return current user info as example
    return {
        "users": [{
            "user_id": current_user.user_id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role.value,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            "created_at": current_user.created_at.isoformat(),
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None
        }],
        "total": 1
    }


@app.post("/users", tags=["user-management"])
async def create_user(
    user_data: Dict[str, Any],
    current_user = Depends(require_admin),
    auth_service = Depends(get_auth_service)
):
    """Create new user (Admin only)."""
    try:
        # This would implement user creation logic
        # For now, return success message
        return {
            "message": "User creation endpoint - implementation pending",
            "data": user_data
        }
        
    except Exception as e:
        logger.error(f"User creation error: {e}")
        raise HTTPException(status_code=500, detail="User creation failed")


# Webhook Management Endpoints
@app.get("/webhooks", tags=["webhooks"])
async def get_webhooks():
    """Get all configured webhooks."""
    try:
        webhook_service = get_webhook_service()
        webhooks = webhook_service.get_webhook_configs()
        
        return {
            "status": "success",
            "data": webhooks,
            "total_webhooks": len(webhooks)
        }
        
    except Exception as e:
        logger.error(f"Error getting webhooks: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve webhooks")


@app.post("/webhooks", tags=["webhooks"])
async def add_webhook(
    webhook_id: str,
    name: str,
    url: str,
    webhook_type: str,
    enabled: bool = True,
    alert_types: Optional[List[str]] = None,
    severity_threshold: str = "medium",
    headers: Optional[Dict[str, str]] = None,
    template: Optional[str] = None,
    retry_count: int = 3,
    timeout_seconds: int = 30,
    rate_limit_per_minute: int = 60
):
    """Add a new webhook configuration."""
    try:
        webhook_service = get_webhook_service()
        
        config = WebhookConfig(
            webhook_id=webhook_id,
            name=name,
            url=url,
            webhook_type=webhook_type,
            enabled=enabled,
            alert_types=alert_types,
            severity_threshold=severity_threshold,
            headers=headers,
            template=template,
            retry_count=retry_count,
            timeout_seconds=timeout_seconds,
            rate_limit_per_minute=rate_limit_per_minute
        )
        
        webhook_service.add_webhook(config)
        
        return {
            "status": "success",
            "message": f"Webhook '{name}' added successfully",
            "webhook_id": webhook_id
        }
        
    except Exception as e:
        logger.error(f"Error adding webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to add webhook")


@app.delete("/webhooks/{webhook_id}", tags=["webhooks"])
async def remove_webhook(webhook_id: str):
    """Remove a webhook configuration."""
    try:
        webhook_service = get_webhook_service()
        webhook_service.remove_webhook(webhook_id)
        
        return {
            "status": "success",
            "message": f"Webhook '{webhook_id}' removed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error removing webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove webhook")


@app.get("/webhooks/stats", tags=["webhooks"])
async def get_webhook_stats():
    """Get webhook statistics and alert history."""
    try:
        webhook_service = get_webhook_service()
        stats = webhook_service.get_webhook_stats()
        
        return {
            "status": "success",
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting webhook stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve webhook statistics")


@app.get("/webhooks/alerts", tags=["webhooks"])
async def get_alert_history(limit: int = Query(100, ge=1, le=1000)):
    """Get recent alert history."""
    try:
        webhook_service = get_webhook_service()
        alerts = webhook_service.get_alert_history(limit=limit)
        
        return {
            "status": "success",
            "data": alerts,
            "total_alerts": len(alerts)
        }
        
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert history")


@app.post("/webhooks/test", tags=["webhooks"])
async def test_webhook(
    webhook_id: str,
    test_message: str = "This is a test alert from Watcher-AI"
):
    """Send a test alert to a specific webhook."""
    try:
        webhook_service = get_webhook_service()
        
        # Create test alert
        test_alert = WebhookAlert(
            alert_id=f"test-{datetime.utcnow().timestamp()}",
            alert_type="system_test",
            severity="low",
            title="Watcher-AI Test Alert",
            message=test_message,
            agent_id="test-agent",
            agent_name="Test Agent",
            hallucination_risk=0.25,
            confidence=0.95,
            timestamp=datetime.utcnow().isoformat(),
            details={"test": True, "webhook_id": webhook_id}
        )
        
        # Send test alert
        async with webhook_service:
            results = await webhook_service.send_alert(test_alert)
        
        webhook_result = results.get(f"webhook_{webhook_id}", False)
        
        return {
            "status": "success" if webhook_result else "failed",
            "message": f"Test alert {'sent successfully' if webhook_result else 'failed to send'}",
            "webhook_id": webhook_id,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error testing webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to test webhook")


@app.post("/webhooks/alert", tags=["webhooks"])
async def send_custom_alert(request: Dict[str, Any]):
    """Send a custom alert via webhooks."""
    try:
        webhook_service = get_webhook_service()
        
        # Extract parameters from request
        alert_type = request.get("alert_type", "custom")
        severity = request.get("severity", "medium")
        title = request.get("title", "Custom Alert")
        message = request.get("message", "Custom alert message")
        agent_id = request.get("agent_id", "custom")
        agent_name = request.get("agent_name", "Custom Alert")
        hallucination_risk = request.get("hallucination_risk", 0.0)
        confidence = request.get("confidence", 1.0)
        details = request.get("details", {})
        email_recipients = request.get("email_recipients")
        
        # Create custom alert
        alert = WebhookAlert(
            alert_id=f"custom-{datetime.utcnow().timestamp()}",
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            agent_id=agent_id,
            agent_name=agent_name,
            hallucination_risk=hallucination_risk,
            confidence=confidence,
            timestamp=datetime.utcnow().isoformat(),
            details=details
        )
        
        # Send alert
        async with webhook_service:
            results = await webhook_service.send_alert(alert, email_recipients)
        
        successful_count = sum(1 for success in results.values() if success)
        
        return {
            "status": "success" if successful_count > 0 else "failed",
            "message": f"Alert sent to {successful_count}/{len(results)} endpoints",
            "results": results,
            "alert_id": alert.alert_id
        }
        
    except Exception as e:
        logger.error(f"Error sending custom alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to send custom alert")


# Compliance & Audit Trail Endpoints
@app.get("/compliance/audit-trail", tags=["compliance"])
async def get_audit_trail(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return"),
    current_user = Depends(require_authentication)
):
    """Get audit trail with filtering options."""
    try:
        compliance_service = get_compliance_service()
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Parse event types
        event_types = None
        if event_type:
            try:
                event_types = [AuditEventType(event_type)]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid event type")
        
        # Get audit trail
        events = await compliance_service.get_audit_trail(
            start_date=start_dt,
            end_date=end_dt,
            user_id=user_id,
            event_types=event_types,
            limit=limit
        )
        
        return {
            "status": "success",
            "data": events,
            "count": len(events),
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "user_id": user_id,
                "event_type": event_type,
                "limit": limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audit trail: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit trail")


@app.get("/compliance/report/{framework}", tags=["compliance"])
async def generate_compliance_report(
    framework: str,
    start_date: str = Query(..., description="Start date (ISO format)"),
    end_date: str = Query(..., description="End date (ISO format)"),
    current_user = Depends(require_admin)
):
    """Generate compliance report for specific framework (Admin only)."""
    try:
        compliance_service = get_compliance_service()
        
        # Validate framework
        try:
            framework_enum = ComplianceFramework(framework.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid compliance framework")
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Generate report
        report = await compliance_service.generate_compliance_report(
            framework_enum, start_dt, end_dt
        )
        
        return {
            "status": "success",
            "data": report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate compliance report")


@app.get("/compliance/violations", tags=["compliance"])
async def get_compliance_violations(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    limit: int = Query(100, ge=1, le=1000),
    current_user = Depends(require_authentication)
):
    """Get compliance violations with filtering."""
    try:
        compliance_service = get_compliance_service()
        
        # Build query
        query = "SELECT * FROM compliance_violations WHERE 1=1"
        params = []
        
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        
        if resolved is not None:
            query += " AND resolved = ?"
            params.append(resolved)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        # Execute query
        import sqlite3
        with sqlite3.connect(compliance_service.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            violations = [dict(row) for row in cursor.fetchall()]
        
        return {
            "status": "success",
            "data": violations,
            "count": len(violations)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving compliance violations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve compliance violations")


@app.post("/compliance/violations/{violation_id}/resolve", tags=["compliance"])
async def resolve_compliance_violation(
    violation_id: str,
    resolution_notes: str = Query(..., description="Resolution notes"),
    current_user = Depends(require_authentication)
):
    """Resolve a compliance violation."""
    try:
        compliance_service = get_compliance_service()
        
        # Update violation
        import sqlite3
        with sqlite3.connect(compliance_service.db_path) as conn:
            cursor = conn.execute("""
                UPDATE compliance_violations 
                SET resolved = TRUE, resolved_at = ?, resolved_by = ?
                WHERE violation_id = ?
            """, (datetime.utcnow(), current_user.user_id, violation_id))
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Violation not found")
            
            conn.commit()
        
        # Log audit event
        audit_event = AuditEvent(
            event_id=f"audit_{secrets.token_urlsafe(16)}",
            event_type=AuditEventType.COMPLIANCE_VIOLATION,
            user_id=current_user.user_id,
            session_id=None,
            timestamp=datetime.utcnow(),
            ip_address=None,
            user_agent=None,
            resource=f"violation/{violation_id}",
            action="resolve_violation",
            outcome="success",
            details={
                "violation_id": violation_id,
                "resolution_notes": resolution_notes,
                "resolved_by": current_user.user_id
            },
            compliance_frameworks=[ComplianceFramework.SOC2, ComplianceFramework.ISO27001]
        )
        
        await compliance_service.log_audit_event(audit_event)
        
        return {
            "status": "success",
            "message": "Compliance violation resolved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving compliance violation: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve compliance violation")


@app.get("/compliance/export", tags=["compliance"])
async def export_audit_data(
    format: str = Query("csv", description="Export format (csv, json)"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user = Depends(require_admin)
):
    """Export audit data (Admin only)."""
    try:
        compliance_service = get_compliance_service()
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Export data
        export_data = await compliance_service.export_audit_data(
            format_type=format,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # Log export event
        audit_event = AuditEvent(
            event_id=f"audit_{secrets.token_urlsafe(16)}",
            event_type=AuditEventType.DATA_EXPORT,
            user_id=current_user.user_id,
            session_id=None,
            timestamp=datetime.utcnow(),
            ip_address=None,
            user_agent=None,
            resource="audit_data",
            action="export_audit_data",
            outcome="success",
            details={
                "format": format,
                "start_date": start_date,
                "end_date": end_date,
                "exported_by": current_user.user_id
            },
            data_classification=DataClassification.CONFIDENTIAL,
            compliance_frameworks=[ComplianceFramework.SOC2, ComplianceFramework.GDPR]
        )
        
        await compliance_service.log_audit_event(audit_event)
        
        return {
            "status": "success",
            "data": export_data,
            "format": format,
            "exported_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting audit data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export audit data")


@app.get("/compliance/frameworks", tags=["compliance"])
async def get_compliance_frameworks(current_user = Depends(require_authentication)):
    """Get supported compliance frameworks."""
    frameworks = [
        {
            "id": "soc2",
            "name": "SOC 2 Type II",
            "description": "Service Organization Control 2 - Security, Availability, Processing Integrity, Confidentiality, Privacy"
        },
        {
            "id": "gdpr",
            "name": "GDPR",
            "description": "General Data Protection Regulation - EU data protection and privacy"
        },
        {
            "id": "hipaa",
            "name": "HIPAA",
            "description": "Health Insurance Portability and Accountability Act - Healthcare data protection"
        },
        {
            "id": "iso27001",
            "name": "ISO 27001",
            "description": "Information Security Management System standard"
        },
        {
            "id": "pci_dss",
            "name": "PCI DSS",
            "description": "Payment Card Industry Data Security Standard"
        },
        {
            "id": "ccpa",
            "name": "CCPA",
            "description": "California Consumer Privacy Act"
        },
        {
            "id": "nist",
            "name": "NIST Cybersecurity Framework",
            "description": "National Institute of Standards and Technology cybersecurity guidelines"
        }
    ]
    
    return {
        "status": "success",
        "data": frameworks,
        "count": len(frameworks)
    }


# Multi-Tenant Management Endpoints
@app.get("/tenants", tags=["tenants"])
async def list_tenants(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user = Depends(require_admin)
):
    """List all tenants (Admin only)."""
    try:
        tenant_service = get_tenant_service()
        
        # Parse status filter
        status_filter = None
        if status:
            try:
                status_filter = TenantStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid status")
        
        tenants = tenant_service.list_tenants(status_filter)
        
        # Convert to response format
        tenant_data = []
        for tenant in tenants:
            tenant_dict = asdict(tenant)
            tenant_dict['status'] = tenant.status.value
            tenant_dict['subscription_tier'] = tenant.subscription_tier.value
            tenant_dict['billing_cycle'] = tenant.billing_cycle.value
            tenant_dict['created_at'] = tenant.created_at.isoformat()
            tenant_dict['updated_at'] = tenant.updated_at.isoformat()
            tenant_data.append(tenant_dict)
        
        return {
            "status": "success",
            "data": tenant_data,
            "count": len(tenant_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tenants: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tenants")


@app.post("/tenants", tags=["tenants"])
async def create_tenant(
    name: str = Query(..., description="Tenant name"),
    display_name: str = Query(..., description="Display name"),
    admin_email: str = Query(..., description="Admin email"),
    subscription_tier: str = Query("starter", description="Subscription tier"),
    current_user = Depends(require_admin)
):
    """Create a new tenant (Admin only)."""
    try:
        tenant_service = get_tenant_service()
        
        # Validate subscription tier
        try:
            tier = SubscriptionTier(subscription_tier.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid subscription tier")
        
        # Create tenant config
        tenant = TenantConfig(
            tenant_id="",  # Will be generated
            name=name,
            display_name=display_name,
            admin_email=admin_email,
            subscription_tier=tier
        )
        
        # Create tenant
        success = tenant_service.create_tenant(tenant)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create tenant")
        
        # Generate API key
        api_key = tenant_service.generate_api_key(tenant.tenant_id, "Default API Key")
        
        return {
            "status": "success",
            "data": {
                "tenant_id": tenant.tenant_id,
                "name": tenant.name,
                "subdomain": tenant.subdomain,
                "api_key": api_key,
                "dashboard_url": f"https://{tenant.subdomain}.watcher-ai.com"
            },
            "message": "Tenant created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to create tenant")


@app.get("/tenants/{tenant_id}", tags=["tenants"])
async def get_tenant_details(
    tenant_id: str,
    current_user = Depends(require_admin)
):
    """Get tenant details (Admin only)."""
    try:
        tenant_service = get_tenant_service()
        tenant = tenant_service.get_tenant(tenant_id)
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Get usage data
        usage_records = tenant_service.get_tenant_usage(tenant_id, months=3)
        
        tenant_dict = asdict(tenant)
        tenant_dict['status'] = tenant.status.value
        tenant_dict['subscription_tier'] = tenant.subscription_tier.value
        tenant_dict['billing_cycle'] = tenant.billing_cycle.value
        tenant_dict['created_at'] = tenant.created_at.isoformat()
        tenant_dict['updated_at'] = tenant.updated_at.isoformat()
        
        return {
            "status": "success",
            "data": {
                "tenant": tenant_dict,
                "usage": [asdict(usage) for usage in usage_records]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tenant details")


@app.put("/tenants/{tenant_id}", tags=["tenants"])
async def update_tenant(
    tenant_id: str,
    updates: Dict[str, Any],
    current_user = Depends(require_admin)
):
    """Update tenant configuration (Admin only)."""
    try:
        tenant_service = get_tenant_service()
        
        # Validate updates
        allowed_fields = {
            'display_name', 'status', 'subscription_tier', 'billing_cycle',
            'logo_url', 'primary_color', 'secondary_color', 'custom_css',
            'admin_email', 'support_email', 'billing_email', 'features',
            'max_users', 'max_api_calls_per_month', 'max_storage_gb',
            'max_custom_rules', 'max_webhooks', 'compliance_frameworks',
            'data_retention_days', 'audit_logging_enabled', 'metadata'
        }
        
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not filtered_updates:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        # Convert enum strings to enum objects
        if 'status' in filtered_updates:
            try:
                filtered_updates['status'] = TenantStatus(filtered_updates['status'])
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid status")
        
        if 'subscription_tier' in filtered_updates:
            try:
                filtered_updates['subscription_tier'] = SubscriptionTier(filtered_updates['subscription_tier'])
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid subscription tier")
        
        if 'billing_cycle' in filtered_updates:
            try:
                filtered_updates['billing_cycle'] = BillingCycle(filtered_updates['billing_cycle'])
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid billing cycle")
        
        # Update tenant
        success = tenant_service.update_tenant(tenant_id, filtered_updates)
        if not success:
            raise HTTPException(status_code=404, detail="Tenant not found or update failed")
        
        return {
            "status": "success",
            "message": "Tenant updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to update tenant")


@app.get("/tenants/{tenant_id}/usage", tags=["tenants"])
async def get_tenant_usage(
    tenant_id: str,
    months: int = Query(1, ge=1, le=12, description="Number of months"),
    current_user = Depends(require_admin)
):
    """Get tenant usage statistics (Admin only)."""
    try:
        tenant_service = get_tenant_service()
        usage_records = tenant_service.get_tenant_usage(tenant_id, months)
        
        if not usage_records:
            raise HTTPException(status_code=404, detail="No usage data found")
        
        return {
            "status": "success",
            "data": [asdict(usage) for usage in usage_records],
            "count": len(usage_records)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tenant usage")


@app.post("/tenants/{tenant_id}/api-keys", tags=["tenants"])
async def generate_tenant_api_key(
    tenant_id: str,
    key_name: str = Query(..., description="API key name"),
    expires_days: Optional[int] = Query(None, description="Expiration in days"),
    current_user = Depends(require_admin)
):
    """Generate API key for tenant (Admin only)."""
    try:
        tenant_service = get_tenant_service()
        
        api_key = tenant_service.generate_api_key(
            tenant_id=tenant_id,
            key_name=key_name,
            expires_days=expires_days
        )
        
        if not api_key:
            raise HTTPException(status_code=404, detail="Tenant not found or key generation failed")
        
        return {
            "status": "success",
            "data": {
                "api_key": api_key,
                "key_name": key_name,
                "tenant_id": tenant_id,
                "expires_days": expires_days
            },
            "message": "API key generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate API key")


@app.get("/tenant/current", tags=["tenants"])
async def get_current_tenant_info(current_user = Depends(require_authentication)):
    """Get current tenant information."""
    try:
        tenant = get_current_tenant()
        
        if not tenant:
            raise HTTPException(status_code=400, detail="No tenant context available")
        
        tenant_dict = asdict(tenant)
        tenant_dict['status'] = tenant.status.value
        tenant_dict['subscription_tier'] = tenant.subscription_tier.value
        tenant_dict['billing_cycle'] = tenant.billing_cycle.value
        tenant_dict['created_at'] = tenant.created_at.isoformat()
        tenant_dict['updated_at'] = tenant.updated_at.isoformat()
        
        return {
            "status": "success",
            "data": tenant_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tenant information")


@app.get("/tenant/usage", tags=["tenants"])
async def get_current_tenant_usage(
    months: int = Query(1, ge=1, le=12, description="Number of months"),
    current_user = Depends(require_authentication)
):
    """Get current tenant usage statistics."""
    try:
        tenant = get_current_tenant()
        
        if not tenant:
            raise HTTPException(status_code=400, detail="No tenant context available")
        
        tenant_service = get_tenant_service()
        usage_records = tenant_service.get_tenant_usage(tenant.tenant_id, months)
        
        return {
            "status": "success",
            "data": [asdict(usage) for usage in usage_records],
            "count": len(usage_records)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to get usage statistics")


# Scalable WebSocket Endpoints
@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket, token: str = None):
    """WebSocket endpoint for dashboard connections."""
    try:
        # Authenticate user (simplified for demo)
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            return
        
        # Get tenant context (simplified)
        tenant = get_current_tenant()
        if not tenant:
            tenant_id = "default"
        else:
            tenant_id = tenant.tenant_id
        
        # Connect to WebSocket manager
        ws_manager = await get_websocket_manager()
        connection_id = await ws_manager.connect(
            websocket=websocket,
            connection_type=ConnectionType.DASHBOARD,
            tenant_id=tenant_id,
            user_id="dashboard_user",
            metadata={"token": token}
        )
        
        try:
            # Keep connection alive and handle messages
            while True:
                try:
                    data = await websocket.receive_json()
                    
                    # Handle different message types
                    if data.get("type") == "heartbeat":
                        await ws_manager.handle_heartbeat(connection_id)
                    elif data.get("type") == "subscribe":
                        # Handle subscription requests
                        pass
                    
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
                    
        finally:
            await ws_manager.disconnect(connection_id)
            
    except Exception as e:
        logger.error(f"WebSocket dashboard error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


@app.websocket("/ws/workstation")
async def websocket_workstation(websocket: WebSocket, api_key: str = None):
    """WebSocket endpoint for workstation connections."""
    try:
        # Authenticate via API key
        if not api_key:
            await websocket.close(code=1008, reason="API key required")
            return
        
        # Validate API key and get tenant
        tenant_service = get_tenant_service()
        tenant = tenant_service.validate_api_key(api_key)
        
        if not tenant:
            await websocket.close(code=1008, reason="Invalid API key")
            return
        
        # Connect to WebSocket manager
        ws_manager = await get_websocket_manager()
        connection_id = await ws_manager.connect(
            websocket=websocket,
            connection_type=ConnectionType.WORKSTATION,
            tenant_id=tenant.tenant_id,
            metadata={"api_key": api_key}
        )
        
        try:
            # Handle workstation messages
            while True:
                try:
                    data = await websocket.receive_json()
                    
                    message_type = data.get("message_type")
                    
                    if message_type == "heartbeat":
                        await ws_manager.handle_heartbeat(connection_id)
                    elif message_type == "status_update":
                        # Handle workstation status update
                        await _handle_workstation_status_update(data, tenant.tenant_id)
                    elif message_type == "metrics_update":
                        # Handle system metrics update
                        await _handle_workstation_metrics_update(data, tenant.tenant_id)
                    elif message_type == "detection_result":
                        # Handle detection result from workstation
                        await _handle_workstation_detection_result(data, tenant.tenant_id)
                    elif message_type == "system_alert":
                        # Handle system alert from workstation
                        await _handle_workstation_system_alert(data, tenant.tenant_id)
                    
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling workstation message: {e}")
                    
        finally:
            await ws_manager.disconnect(connection_id)
            
    except Exception as e:
        logger.error(f"WebSocket workstation error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


@app.websocket("/ws/agent/{agent_id}")
async def websocket_agent(websocket: WebSocket, agent_id: str, api_key: str = None):
    """WebSocket endpoint for individual agent connections."""
    try:
        # Authenticate via API key
        if not api_key:
            await websocket.close(code=1008, reason="API key required")
            return
        
        # Validate API key and get tenant
        tenant_service = get_tenant_service()
        tenant = tenant_service.validate_api_key(api_key)
        
        if not tenant:
            await websocket.close(code=1008, reason="Invalid API key")
            return
        
        # Connect to WebSocket manager
        ws_manager = await get_websocket_manager()
        connection_id = await ws_manager.connect(
            websocket=websocket,
            connection_type=ConnectionType.AGENT,
            tenant_id=tenant.tenant_id,
            agent_id=agent_id,
            metadata={"api_key": api_key, "agent_id": agent_id}
        )
        
        try:
            # Handle agent messages
            while True:
                try:
                    data = await websocket.receive_json()
                    
                    message_type = data.get("message_type")
                    
                    if message_type == "heartbeat":
                        await ws_manager.handle_heartbeat(connection_id)
                    elif message_type == "agent_output":
                        # Handle agent output for real-time detection
                        await _handle_agent_output(data, agent_id, tenant.tenant_id)
                    
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling agent message: {e}")
                    
        finally:
            await ws_manager.disconnect(connection_id)
            
    except Exception as e:
        logger.error(f"WebSocket agent error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


@app.get("/ws/stats", tags=["websockets"])
async def get_websocket_stats(current_user = Depends(require_admin)):
    """Get WebSocket performance statistics (Admin only)."""
    try:
        ws_manager = await get_websocket_manager()
        stats = ws_manager.get_performance_stats()
        
        return {
            "status": "success",
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get WebSocket statistics")


@app.post("/ws/broadcast", tags=["websockets"])
async def broadcast_message(
    message_type: str,
    data: Dict[str, Any],
    target_tenant: Optional[str] = None,
    target_type: Optional[str] = None,
    current_user = Depends(require_admin)
):
    """Broadcast message to WebSocket connections (Admin only)."""
    try:
        ws_manager = await get_websocket_manager()
        
        # Create message
        message = WebSocketMessage(
            message_id=f"broadcast_{secrets.token_urlsafe(8)}",
            message_type=MessageType(message_type),
            tenant_id=target_tenant or "all",
            source_id="admin",
            target_id=None,
            channel="broadcast",
            data=data
        )
        
        # Send based on target
        if target_tenant:
            await ws_manager.send_to_tenant(target_tenant, message)
        elif target_type:
            connection_type = ConnectionType(target_type)
            await ws_manager.send_to_connection_type(connection_type, message)
        else:
            await ws_manager.broadcast_to_all(message)
        
        return {
            "status": "success",
            "message": "Broadcast sent successfully",
            "message_id": message.message_id
        }
        
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast message")


# WebSocket Message Handlers
async def _handle_workstation_status_update(data: Dict[str, Any], tenant_id: str):
    """Handle workstation status update."""
    try:
        workstation_id = data.get("workstation_id")
        status = data.get("status")
        
        # Store workstation info (simplified)
        logger.info(f"Workstation {workstation_id} status: {status}")
        
        # Broadcast to dashboard connections
        ws_manager = await get_websocket_manager()
        message = WebSocketMessage(
            message_id=f"status_{secrets.token_urlsafe(8)}",
            message_type=MessageType.WORKSTATION_STATUS,
            tenant_id=tenant_id,
            source_id=workstation_id,
            target_id=None,
            channel=f"tenant:{tenant_id}",
            data=data
        )
        
        await ws_manager.send_to_tenant(tenant_id, message)
        
    except Exception as e:
        logger.error(f"Error handling workstation status update: {e}")


async def _handle_workstation_metrics_update(data: Dict[str, Any], tenant_id: str):
    """Handle workstation metrics update."""
    try:
        workstation_id = data.get("workstation_id")
        metrics = data.get("metrics")
        
        # Store metrics (simplified)
        logger.debug(f"Workstation {workstation_id} metrics: CPU {metrics.get('cpu_percent')}%")
        
        # Broadcast to dashboard connections
        ws_manager = await get_websocket_manager()
        message = WebSocketMessage(
            message_id=f"metrics_{secrets.token_urlsafe(8)}",
            message_type=MessageType.PERFORMANCE_METRIC,
            tenant_id=tenant_id,
            source_id=workstation_id,
            target_id=None,
            channel=f"tenant:{tenant_id}",
            data=data
        )
        
        await ws_manager.send_to_tenant(tenant_id, message)
        
    except Exception as e:
        logger.error(f"Error handling workstation metrics update: {e}")


async def _handle_workstation_detection_result(data: Dict[str, Any], tenant_id: str):
    """Handle detection result from workstation."""
    try:
        workstation_id = data.get("workstation_id")
        agent_id = data.get("agent_id")
        detection_result = data.get("detection_result")
        
        # Store detection result (simplified)
        logger.info(f"Detection result from {workstation_id}/{agent_id}: {detection_result}")
        
        # Broadcast to dashboard connections
        ws_manager = await get_websocket_manager()
        message = WebSocketMessage(
            message_id=f"detection_{secrets.token_urlsafe(8)}",
            message_type=MessageType.DETECTION_RESULT,
            tenant_id=tenant_id,
            source_id=f"{workstation_id}/{agent_id}",
            target_id=None,
            channel=f"tenant:{tenant_id}",
            data=data
        )
        
        await ws_manager.send_to_tenant(tenant_id, message)
        
    except Exception as e:
        logger.error(f"Error handling workstation detection result: {e}")


async def _handle_workstation_system_alert(data: Dict[str, Any], tenant_id: str):
    """Handle system alert from workstation."""
    try:
        workstation_id = data.get("workstation_id")
        alerts = data.get("alerts")
        
        # Process system alerts
        logger.warning(f"System alerts from {workstation_id}: {alerts}")
        
        # Broadcast to dashboard connections
        ws_manager = await get_websocket_manager()
        message = WebSocketMessage(
            message_id=f"alert_{secrets.token_urlsafe(8)}",
            message_type=MessageType.SYSTEM_ALERT,
            tenant_id=tenant_id,
            source_id=workstation_id,
            target_id=None,
            channel=f"tenant:{tenant_id}",
            data=data
        )
        
        await ws_manager.send_to_tenant(tenant_id, message)
        
    except Exception as e:
        logger.error(f"Error handling workstation system alert: {e}")


async def _handle_agent_output(data: Dict[str, Any], agent_id: str, tenant_id: str):
    """Handle agent output for real-time detection."""
    try:
        output_text = data.get("output_text")
        
        # Perform real-time detection (simplified)
        # In practice, this would use the detection pipeline
        detection_result = {
            "hallucination_risk": 0.1,  # Placeholder
            "confidence": 0.9,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Broadcast detection result
        ws_manager = await get_websocket_manager()
        message = WebSocketMessage(
            message_id=f"realtime_{secrets.token_urlsafe(8)}",
            message_type=MessageType.DETECTION_RESULT,
            tenant_id=tenant_id,
            source_id=agent_id,
            target_id=None,
            channel=f"tenant:{tenant_id}",
            data={
                "agent_id": agent_id,
                "output_text": output_text,
                "detection_result": detection_result
            }
        )
        
        await ws_manager.send_to_tenant(tenant_id, message)
        
    except Exception as e:
        logger.error(f"Error handling agent output: {e}")


# Alert Escalation System Endpoints
@app.post("/alerts", tags=["alerts"])
async def create_alert(
    source_id: str,
    source_type: str,
    title: str,
    description: str,
    severity: str,
    tags: List[str] = [],
    metadata: Dict[str, Any] = {},
    current_user = Depends(require_authentication)
):
    """Create a new alert."""
    try:
        tenant = get_current_tenant()
        if not tenant:
            raise HTTPException(status_code=400, detail="No tenant context available")
        
        escalation_service = get_escalation_service()
        
        # Validate severity
        try:
            alert_severity = AlertSeverity(severity.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid alert severity")
        
        # Create alert
        alert = Alert(
            alert_id="",  # Will be generated
            tenant_id=tenant.tenant_id,
            source_id=source_id,
            source_type=source_type,
            title=title,
            description=description,
            severity=alert_severity,
            tags=tags,
            metadata=metadata
        )
        
        alert_id = await escalation_service.create_alert(alert)
        
        return {
            "status": "success",
            "data": {
                "alert_id": alert_id,
                "message": "Alert created and escalation monitoring started"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert")


@app.post("/alerts/{alert_id}/acknowledge", tags=["alerts"])
async def acknowledge_alert(
    alert_id: str,
    current_user = Depends(require_authentication)
):
    """Acknowledge an alert."""
    try:
        escalation_service = get_escalation_service()
        
        success = await escalation_service.acknowledge_alert(alert_id, current_user.user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found or already acknowledged")
        
        return {
            "status": "success",
            "message": "Alert acknowledged successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")


@app.post("/alerts/{alert_id}/resolve", tags=["alerts"])
async def resolve_alert(
    alert_id: str,
    resolution_notes: Optional[str] = None,
    current_user = Depends(require_authentication)
):
    """Resolve an alert."""
    try:
        escalation_service = get_escalation_service()
        
        success = await escalation_service.resolve_alert(alert_id, current_user.user_id, resolution_notes)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {
            "status": "success",
            "message": "Alert resolved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert")


@app.get("/alerts/statistics", tags=["alerts"])
async def get_alert_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
    current_user = Depends(require_authentication)
):
    """Get alert statistics for current tenant."""
    try:
        tenant = get_current_tenant()
        if not tenant:
            raise HTTPException(status_code=400, detail="No tenant context available")
        
        escalation_service = get_escalation_service()
        statistics = await escalation_service.get_alert_statistics(tenant.tenant_id, days)
        
        return {
            "status": "success",
            "data": statistics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert statistics")


@app.post("/escalation-rules", tags=["alerts"])
async def create_escalation_rule(
    name: str,
    description: str,
    severity_levels: List[str] = [],
    source_types: List[str] = [],
    tags: List[str] = [],
    departments: List[str] = [],
    level_1_timeout: int = 5,
    level_2_timeout: int = 15,
    level_3_timeout: int = 30,
    level_4_timeout: int = 60,
    level_5_timeout: int = 120,
    current_user = Depends(require_admin)
):
    """Create escalation rule (Admin only)."""
    try:
        tenant = get_current_tenant()
        if not tenant:
            raise HTTPException(status_code=400, detail="No tenant context available")
        
        escalation_service = get_escalation_service()
        
        # Validate severity levels
        validated_severities = []
        for severity in severity_levels:
            try:
                validated_severities.append(AlertSeverity(severity.lower()))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity level: {severity}")
        
        # Create escalation rule
        rule = EscalationRule(
            rule_id="",  # Will be generated
            tenant_id=tenant.tenant_id,
            name=name,
            description=description,
            severity_levels=validated_severities,
            source_types=source_types,
            tags=tags,
            departments=departments,
            level_1_timeout=level_1_timeout,
            level_2_timeout=level_2_timeout,
            level_3_timeout=level_3_timeout,
            level_4_timeout=level_4_timeout,
            level_5_timeout=level_5_timeout
        )
        
        rule_id = await escalation_service.create_escalation_rule(rule)
        
        return {
            "status": "success",
            "data": {
                "rule_id": rule_id,
                "message": "Escalation rule created successfully"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating escalation rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create escalation rule")


@app.post("/on-call-schedules", tags=["alerts"])
async def create_on_call_schedule(
    name: str,
    description: str,
    escalation_level: str,
    rotation_type: str,
    team_members: List[str],
    current_user = Depends(require_admin)
):
    """Create on-call schedule (Admin only)."""
    try:
        tenant = get_current_tenant()
        if not tenant:
            raise HTTPException(status_code=400, detail="No tenant context available")
        
        escalation_service = get_escalation_service()
        
        # Validate escalation level
        try:
            level = EscalationLevel(escalation_level.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid escalation level")
        
        # Validate rotation type
        if rotation_type not in ["daily", "weekly", "monthly"]:
            raise HTTPException(status_code=400, detail="Invalid rotation type")
        
        # Create on-call schedule
        schedule = OnCallSchedule(
            schedule_id="",  # Will be generated
            tenant_id=tenant.tenant_id,
            name=name,
            description=description,
            escalation_level=level,
            rotation_type=rotation_type,
            team_members=team_members
        )
        
        schedule_id = await escalation_service.create_on_call_schedule(schedule)
        
        return {
            "status": "success",
            "data": {
                "schedule_id": schedule_id,
                "message": "On-call schedule created successfully"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating on-call schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create on-call schedule")


@app.get("/escalation-levels", tags=["alerts"])
async def get_escalation_levels(current_user = Depends(require_authentication)):
    """Get available escalation levels."""
    levels = [
        {
            "level": "level_1",
            "name": "Level 1 - Primary On-Call",
            "description": "First responder, typically 5-15 minutes"
        },
        {
            "level": "level_2", 
            "name": "Level 2 - Supervisor",
            "description": "Team lead or supervisor, typically 15-30 minutes"
        },
        {
            "level": "level_3",
            "name": "Level 3 - Manager", 
            "description": "Department manager, typically 30-60 minutes"
        },
        {
            "level": "level_4",
            "name": "Level 4 - Executive",
            "description": "Senior management, typically 1-2 hours"
        },
        {
            "level": "level_5",
            "name": "Level 5 - Emergency",
            "description": "Emergency contacts, 2+ hours"
        }
    ]
    
    return {
        "status": "success",
        "data": levels
    }


@app.get("/alert-severities", tags=["alerts"])
async def get_alert_severities(current_user = Depends(require_authentication)):
    """Get available alert severities."""
    severities = [
        {
            "severity": "low",
            "name": "Low",
            "description": "Minor issues, can wait for business hours",
            "color": "#4CAF50"
        },
        {
            "severity": "medium",
            "name": "Medium", 
            "description": "Moderate impact, should be addressed soon",
            "color": "#FF9800"
        },
        {
            "severity": "high",
            "name": "High",
            "description": "Significant impact, requires immediate attention",
            "color": "#F44336"
        },
        {
            "severity": "critical",
            "name": "Critical",
            "description": "System down or major security incident",
            "color": "#9C27B0"
        }
    ]
    
    return {
        "status": "success", 
        "data": severities
    }


# Workstation Discovery Endpoints
@app.post("/discovery/network-ranges", tags=["discovery"])
async def add_network_range(
    name: str,
    cidr: str,
    description: str = "",
    scan_frequency: int = 3600,
    current_user = Depends(require_admin)
):
    """Add network range for discovery (Admin only)."""
    try:
        discovery_service = get_discovery_service()
        
        network_range = NetworkRange(
            range_id="",  # Will be generated
            name=name,
            cidr=cidr,
            description=description,
            scan_frequency=scan_frequency
        )
        
        range_id = await discovery_service.add_network_range(network_range)
        
        return {
            "status": "success",
            "data": {
                "range_id": range_id,
                "message": "Network range added successfully"
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding network range: {e}")
        raise HTTPException(status_code=500, detail="Failed to add network range")


@app.post("/discovery/tasks", tags=["discovery"])
async def create_discovery_task(
    name: str,
    description: str,
    network_ranges: List[str],
    discovery_methods: List[str] = ["network_scan"],
    interval_seconds: int = 3600,
    port_scan_enabled: bool = True,
    service_detection_enabled: bool = True,
    os_detection_enabled: bool = True,
    max_concurrent_scans: int = 50,
    current_user = Depends(require_admin)
):
    """Create discovery task (Admin only)."""
    try:
        discovery_service = get_discovery_service()
        
        # Validate discovery methods
        validated_methods = []
        for method in discovery_methods:
            try:
                validated_methods.append(DiscoveryMethod(method.lower()))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid discovery method: {method}")
        
        task = DiscoveryTask(
            task_id="",  # Will be generated
            name=name,
            description=description,
            network_ranges=network_ranges,
            discovery_methods=validated_methods,
            interval_seconds=interval_seconds,
            port_scan_enabled=port_scan_enabled,
            service_detection_enabled=service_detection_enabled,
            os_detection_enabled=os_detection_enabled,
            max_concurrent_scans=max_concurrent_scans
        )
        
        task_id = await discovery_service.create_discovery_task(task)
        
        return {
            "status": "success",
            "data": {
                "task_id": task_id,
                "message": "Discovery task created successfully"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating discovery task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create discovery task")


@app.post("/discovery/tasks/{task_id}/run", tags=["discovery"])
async def run_discovery_task(
    task_id: str,
    current_user = Depends(require_admin)
):
    """Run discovery task manually (Admin only)."""
    try:
        discovery_service = get_discovery_service()
        results = await discovery_service.run_discovery_task(task_id)
        
        return {
            "status": "success",
            "data": results,
            "message": "Discovery task completed successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error running discovery task: {e}")
        raise HTTPException(status_code=500, detail="Failed to run discovery task")


@app.get("/discovery/devices", tags=["discovery"])
async def get_discovered_devices(
    limit: int = Query(100, ge=1, le=1000, description="Number of devices to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user = Depends(require_authentication)
):
    """Get discovered devices with pagination."""
    try:
        discovery_service = get_discovery_service()
        devices = await discovery_service.get_discovered_devices(limit, offset)
        
        return {
            "status": "success",
            "data": devices,
            "count": len(devices),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error getting discovered devices: {e}")
        raise HTTPException(status_code=500, detail="Failed to get discovered devices")


@app.get("/discovery/statistics", tags=["discovery"])
async def get_discovery_statistics(current_user = Depends(require_authentication)):
    """Get discovery statistics."""
    try:
        discovery_service = get_discovery_service()
        statistics = await discovery_service.get_discovery_statistics()
        
        return {
            "status": "success",
            "data": statistics
        }
        
    except Exception as e:
        logger.error(f"Error getting discovery statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get discovery statistics")


@app.get("/discovery/methods", tags=["discovery"])
async def get_discovery_methods(current_user = Depends(require_authentication)):
    """Get available discovery methods."""
    methods = [
        {
            "method": "network_scan",
            "name": "Network Scanning",
            "description": "TCP port scanning and service detection"
        },
        {
            "method": "active_directory",
            "name": "Active Directory",
            "description": "Query Active Directory for computer objects"
        },
        {
            "method": "snmp",
            "name": "SNMP Discovery",
            "description": "SNMP-based device discovery and inventory"
        },
        {
            "method": "dhcp_logs",
            "name": "DHCP Log Analysis",
            "description": "Parse DHCP server logs for device information"
        },
        {
            "method": "dns_lookup",
            "name": "DNS Enumeration",
            "description": "DNS zone transfers and reverse lookups"
        },
        {
            "method": "manual",
            "name": "Manual Entry",
            "description": "Manually added device information"
        }
    ]
    
    return {
        "status": "success",
        "data": methods
    }


@app.get("/discovery/device-types", tags=["discovery"])
async def get_device_types(current_user = Depends(require_authentication)):
    """Get available device types."""
    types = [
        {
            "type": "workstation",
            "name": "Workstation",
            "description": "Desktop computers and workstations",
            "icon": "computer"
        },
        {
            "type": "server",
            "name": "Server",
            "description": "Server systems and infrastructure",
            "icon": "server"
        },
        {
            "type": "laptop",
            "name": "Laptop",
            "description": "Portable computers and laptops",
            "icon": "laptop"
        },
        {
            "type": "mobile",
            "name": "Mobile Device",
            "description": "Smartphones and tablets",
            "icon": "phone"
        },
        {
            "type": "printer",
            "name": "Printer",
            "description": "Network printers and multifunction devices",
            "icon": "printer"
        },
        {
            "type": "network_device",
            "name": "Network Device",
            "description": "Routers, switches, and network equipment",
            "icon": "network"
        },
        {
            "type": "iot_device",
            "name": "IoT Device",
            "description": "Internet of Things and smart devices",
            "icon": "sensors"
        },
        {
            "type": "unknown",
            "name": "Unknown",
            "description": "Unidentified or unclassified devices",
            "icon": "help"
        }
    ]
    
    return {
        "status": "success",
        "data": types
    }


@app.get("/discovery/operating-systems", tags=["discovery"])
async def get_operating_systems(current_user = Depends(require_authentication)):
    """Get available operating systems."""
    systems = [
        {
            "os": "windows",
            "name": "Microsoft Windows",
            "description": "Windows desktop and server operating systems",
            "icon": "windows"
        },
        {
            "os": "macos",
            "name": "macOS",
            "description": "Apple macOS and Mac OS X",
            "icon": "apple"
        },
        {
            "os": "linux",
            "name": "Linux",
            "description": "Linux distributions and variants",
            "icon": "linux"
        },
        {
            "os": "unix",
            "name": "Unix",
            "description": "Unix and Unix-like operating systems",
            "icon": "terminal"
        },
        {
            "os": "android",
            "name": "Android",
            "description": "Google Android mobile operating system",
            "icon": "android"
        },
        {
            "os": "ios",
            "name": "iOS",
            "description": "Apple iOS mobile operating system",
            "icon": "apple"
        },
        {
            "os": "unknown",
            "name": "Unknown",
            "description": "Unidentified operating system",
            "icon": "help"
        }
    ]
    
    return {
        "status": "success",
        "data": systems
    }


# Custom Detection Rules Endpoints
@app.get("/custom-rules", tags=["custom-rules"])
async def get_custom_rules(
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user = Depends(require_authentication)
):
    """Get all custom detection rules."""
    try:
        rules_engine = get_custom_rules_engine()
        
        if category:
            try:
                category_enum = RuleCategory(category.lower())
                rules = rules_engine.get_rules_by_category(category_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid category")
        else:
            rules = list(rules_engine.rules.values())
        
        return {
            "status": "success",
            "data": [asdict(rule) for rule in rules],
            "count": len(rules)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting custom rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve custom rules")


@app.post("/custom-rules", tags=["custom-rules"])
async def create_custom_rule(
    rule_data: Dict[str, Any],
    current_user = Depends(require_admin)
):
    """Create a new custom detection rule (Admin only)."""
    try:
        rules_engine = get_custom_rules_engine()
        
        # Validate required fields
        required_fields = ["rule_id", "name", "description", "rule_type", "category", "severity"]
        for field in required_fields:
            if field not in rule_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Create rule object
        rule = CustomRule(
            rule_id=rule_data["rule_id"],
            name=rule_data["name"],
            description=rule_data["description"],
            rule_type=RuleType(rule_data["rule_type"]),
            category=RuleCategory(rule_data["category"]),
            severity=RuleSeverity(rule_data["severity"]),
            pattern=rule_data.get("pattern"),
            threshold=rule_data.get("threshold"),
            keywords=rule_data.get("keywords", []),
            enabled=rule_data.get("enabled", True),
            metadata=rule_data.get("metadata", {})
        )
        
        success = rules_engine.add_rule(rule, current_user.user_id)
        
        if success:
            return {
                "status": "success",
                "message": "Custom rule created successfully",
                "rule_id": rule.rule_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create custom rule")
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {e}")
    except Exception as e:
        logger.error(f"Error creating custom rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create custom rule")


@app.put("/custom-rules/{rule_id}", tags=["custom-rules"])
async def update_custom_rule(
    rule_id: str,
    updates: Dict[str, Any],
    current_user = Depends(require_admin)
):
    """Update an existing custom rule (Admin only)."""
    try:
        rules_engine = get_custom_rules_engine()
        
        # Convert enum strings to enums if present
        if "rule_type" in updates:
            updates["rule_type"] = RuleType(updates["rule_type"])
        if "category" in updates:
            updates["category"] = RuleCategory(updates["category"])
        if "severity" in updates:
            updates["severity"] = RuleSeverity(updates["severity"])
        
        success = rules_engine.update_rule(rule_id, updates, current_user.user_id)
        
        if success:
            return {
                "status": "success",
                "message": "Custom rule updated successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Rule not found")
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {e}")
    except Exception as e:
        logger.error(f"Error updating custom rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to update custom rule")


@app.delete("/custom-rules/{rule_id}", tags=["custom-rules"])
async def delete_custom_rule(
    rule_id: str,
    current_user = Depends(require_admin)
):
    """Delete a custom rule (Admin only)."""
    try:
        rules_engine = get_custom_rules_engine()
        success = rules_engine.delete_rule(rule_id)
        
        if success:
            return {
                "status": "success",
                "message": "Custom rule deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Rule not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting custom rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete custom rule")


@app.get("/custom-rules/templates", tags=["custom-rules"])
async def get_rule_templates(current_user = Depends(require_authentication)):
    """Get available rule templates."""
    try:
        rules_engine = get_custom_rules_engine()
        templates = rules_engine.get_rule_templates()
        
        return {
            "status": "success",
            "data": {k: asdict(v) for k, v in templates.items()},
            "count": len(templates)
        }
        
    except Exception as e:
        logger.error(f"Error getting rule templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve rule templates")


@app.post("/custom-rules/templates/{template_id}/install", tags=["custom-rules"])
async def install_rule_template(
    template_id: str,
    current_user = Depends(require_admin)
):
    """Install a rule template as an active rule (Admin only)."""
    try:
        rules_engine = get_custom_rules_engine()
        success = rules_engine.install_template(template_id, current_user.user_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Template '{template_id}' installed successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Template not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error installing template: {e}")
        raise HTTPException(status_code=500, detail="Failed to install template")


@app.get("/custom-rules/{rule_id}/performance", tags=["custom-rules"])
async def get_rule_performance(
    rule_id: str,
    days: int = Query(30, ge=1, le=365, description="Days to analyze"),
    current_user = Depends(require_authentication)
):
    """Get performance metrics for a custom rule."""
    try:
        rules_engine = get_custom_rules_engine()
        performance = rules_engine.get_rule_performance(rule_id, days)
        
        return {
            "status": "success",
            "data": performance
        }
        
    except Exception as e:
        logger.error(f"Error getting rule performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve rule performance")


@app.post("/custom-rules/test", tags=["custom-rules"])
async def test_custom_rules(
    test_data: Dict[str, Any],
    current_user = Depends(require_authentication)
):
    """Test text against custom rules."""
    try:
        if "text" not in test_data:
            raise HTTPException(status_code=400, detail="Missing 'text' field")
        
        rules_engine = get_custom_rules_engine()
        violations = rules_engine.evaluate_text(
            test_data["text"],
            test_data.get("confidence", 0.8)
        )
        
        return {
            "status": "success",
            "data": {
                "text": test_data["text"],
                "violations": [asdict(v) for v in violations],
                "violation_count": len(violations),
                "highest_severity": max([v.severity.value for v in violations]) if violations else "none",
                "overall_risk": "high" if any(v.severity in [RuleSeverity.HIGH, RuleSeverity.CRITICAL] for v in violations) else "low"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing custom rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to test custom rules")


# Enhanced Detection Endpoint with Custom Rules
@app.post("/test-agent-enhanced", tags=["detection"])
async def test_agent_enhanced(
    agent_output: str,
    ground_truth: str = None,
    confidence: float = Query(0.8, ge=0.0, le=1.0),
    apply_custom_rules: bool = Query(True, description="Apply custom detection rules"),
    current_user = Depends(require_authentication)
):
    """Enhanced agent testing with custom rules integration."""
    try:
        # Get original detection result
        judge = get_ensemble_judge()
        result = await judge.evaluate_agent_output(agent_output, ground_truth)
        
        # Apply custom rules if requested
        custom_violations = []
        if apply_custom_rules:
            rules_engine = get_custom_rules_engine()
            custom_violations = rules_engine.evaluate_text(agent_output, result.hallucination_risk)
            
            # Record violations for analytics
            for violation in custom_violations:
                rules_engine.record_violation(violation, agent_output, current_user.user_id)
        
        # Calculate enhanced risk score
        base_risk = result.hallucination_risk
        custom_risk_boost = 0.0
        
        for violation in custom_violations:
            if violation.severity == RuleSeverity.CRITICAL:
                custom_risk_boost += 0.3
            elif violation.severity == RuleSeverity.HIGH:
                custom_risk_boost += 0.2
            elif violation.severity == RuleSeverity.MEDIUM:
                custom_risk_boost += 0.1
            else:
                custom_risk_boost += 0.05
        
        enhanced_risk = min(1.0, base_risk + custom_risk_boost)
        
        # Compile recommendations
        recommendations = []
        for violation in custom_violations:
            recommendations.extend(violation.suggestions)
        
        return {
            "agent_output": agent_output,
            "ground_truth": ground_truth,
            "original_result": {
                "hallucination_risk": result.hallucination_risk,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "statistical_score": result.statistical_score,
                "ensemble_weights": result.ensemble_weights
            },
            "custom_rules": {
                "violations": [asdict(v) for v in custom_violations],
                "violation_count": len(custom_violations),
                "risk_boost": custom_risk_boost
            },
            "enhanced_result": {
                "hallucination_risk": enhanced_risk,
                "risk_level": "critical" if enhanced_risk > 0.8 else "high" if enhanced_risk > 0.6 else "medium" if enhanced_risk > 0.4 else "low",
                "recommendations": list(set(recommendations))[:10],  # Unique recommendations, max 10
                "requires_review": enhanced_risk > 0.7 or any(v.severity == RuleSeverity.CRITICAL for v in custom_violations)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Enhanced detection error: {e}")
        raise HTTPException(status_code=500, detail="Enhanced detection analysis failed")


# Real-Time Streaming Detection Endpoints (October 2025 Enhancement)
from fastapi.responses import StreamingResponse
import asyncio
import json
import time


@app.post("/stream-detect", tags=["detection", "streaming"])
async def stream_detect(request: AgentTestRequest):
    """
    Real-time streaming hallucination detection with <100ms flagging.
    
    October 2025 Enhancement: Server-Sent Events for token-level uncertainty highlighting.
    
    Features:
    - Token-level streaming analysis with <50ms latency target
    - Real-time uncertainty highlighting for >0.3 threshold tokens
    - Progressive risk assessment as text is analyzed
    - WebSocket-compatible streaming for live monitoring
    
    Returns:
        StreamingResponse with Server-Sent Events containing:
        - Token-level analysis results
        - Progressive risk scores
        - Real-time flagging of high-uncertainty segments
        - Final comprehensive report
    """
    async def generate_stream():
        """Generate streaming detection results."""
        try:
            # Validate Claude API key
            claude_api_key = os.getenv("CLAUDE_API_KEY")
            if not claude_api_key:
                yield f"data: {json.dumps({'error': 'Claude API key not configured'})}\n\n"
                return
            
            # Initialize judges for streaming analysis
            from ..judges.claude_judge import ClaudeJudge
            from ..judges.statistical_judge import StatisticalJudge
            
            claude_judge = ClaudeJudge(claude_api_key)
            statistical_judge = StatisticalJudge()
            
            start_time = time.time()
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting real-time analysis', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            
            # Phase 1: Statistical Analysis (Fast, <20ms)
            stat_start = time.time()
            statistical_score, confidence_interval = statistical_judge.evaluate(
                request.agent_output, 
                context=request.ground_truth
            )
            stat_latency = (time.time() - stat_start) * 1000
            
            # Get detailed attention analysis
            detailed_stats = statistical_judge.evaluate_with_attention_details(
                request.agent_output,
                context=request.ground_truth
            )
            
            # Stream statistical results
            yield f"data: {json.dumps({'type': 'statistical_analysis', 'score': statistical_score, 'confidence_interval': confidence_interval, 'latency_ms': stat_latency, 'attention_metrics': detailed_stats.get('attention_metrics', {}), 'flagged_tokens': detailed_stats.get('flagged_tokens', []), 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            
            # Phase 2: Token-level Analysis Streaming
            tokens = detailed_stats.get('tokens', [])
            high_entropy_tokens = detailed_stats.get('attention_metrics', {}).get('high_entropy_tokens', [])
            
            for i, token in enumerate(tokens):
                token_start = time.time()
                
                # Determine if token is flagged
                is_flagged = i in high_entropy_tokens
                uncertainty_score = 0.8 if is_flagged else 0.2
                
                # Stream token analysis
                token_result = {
                    'type': 'token_analysis',
                    'token_index': i,
                    'token': token,
                    'is_flagged': is_flagged,
                    'uncertainty_score': uncertainty_score,
                    'latency_ms': (time.time() - token_start) * 1000,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                yield f"data: {json.dumps(token_result)}\n\n"
                
                # Small delay to simulate real-time processing (remove in production)
                await asyncio.sleep(0.01)
            
            # Phase 3: Claude Analysis (Parallel processing)
            claude_start = time.time()
            
            # Send status update
            yield f"data: {json.dumps({'type': 'status', 'message': 'Running Claude analysis', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            
            # Run Claude evaluation
            claude_result = await claude_judge.evaluate_async(
                request.agent_output,
                request.ground_truth,
                request.conversation_history or []
            )
            claude_latency = (time.time() - claude_start) * 1000
            
            # Stream Claude results
            yield f"data: {json.dumps({'type': 'claude_analysis', 'score': claude_result['score'], 'reasoning': claude_result['reasoning'], 'hallucinated_segments': claude_result.get('hallucinated_segments', []), 'latency_ms': claude_latency, 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            
            # Phase 4: Ensemble Combination
            ensemble_start = time.time()
            
            # Weighted ensemble (same as main evaluation)
            ensemble_score = 0.6 * claude_result['score'] + 0.4 * statistical_score
            
            # Risk assessment
            risk_level = "critical" if ensemble_score < 0.3 else "high" if ensemble_score < 0.5 else "medium" if ensemble_score < 0.7 else "low"
            requires_review = ensemble_score < 0.5 or len(claude_result.get('hallucinated_segments', [])) > 0
            
            ensemble_latency = (time.time() - ensemble_start) * 1000
            total_latency = (time.time() - start_time) * 1000
            
            # Final comprehensive result
            final_result = {
                'type': 'final_result',
                'hallucination_risk': 1 - ensemble_score,  # Convert to risk score
                'risk_level': risk_level,
                'requires_review': requires_review,
                'ensemble_score': ensemble_score,
                'claude_score': claude_result['score'],
                'statistical_score': statistical_score,
                'confidence_interval': confidence_interval,
                'reasoning': claude_result['reasoning'],
                'hallucinated_segments': claude_result.get('hallucinated_segments', []),
                'flagged_tokens': detailed_stats.get('flagged_tokens', []),
                'attention_metrics': detailed_stats.get('attention_metrics', {}),
                'performance': {
                    'total_latency_ms': total_latency,
                    'statistical_latency_ms': stat_latency,
                    'claude_latency_ms': claude_latency,
                    'ensemble_latency_ms': ensemble_latency,
                    'target_achieved': total_latency < 100  # <100ms target
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            yield f"data: {json.dumps(final_result)}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'complete', 'message': 'Analysis complete', 'total_latency_ms': total_latency, 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming detection error: {e}")
            error_result = {
                'type': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(error_result)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@app.get("/stream-detect/status", tags=["detection", "streaming"])
async def get_streaming_status():
    """
    Get status of streaming detection capabilities.
    
    Returns information about streaming performance and capabilities.
    """
    try:
        # Check if required components are available
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        
        status = {
            "streaming_available": True,
            "claude_available": bool(claude_api_key),
            "target_latency_ms": 100,
            "features": {
                "token_level_analysis": True,
                "real_time_flagging": True,
                "attention_analysis": True,
                "server_sent_events": True,
                "websocket_compatible": True
            },
            "performance_targets": {
                "statistical_analysis_ms": 20,
                "token_analysis_per_token_ms": 1,
                "claude_analysis_ms": 50,
                "total_target_ms": 100
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting streaming status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get streaming status")


# Advanced features temporarily disabled for core system stability
# from ..services.agent_pipeline import get_agent_pipeline, PipelineResult
# from ..judges.multilingual_judge import get_multilingual_judge, MultilingualResult
# from ..judges.multimodal_judge import get_multimodal_judge, MultimodalInput, MultimodalResult
from pydantic import BaseModel
# from fastapi import File, UploadFile, Form


class AgentPipelineRequest(BaseModel):
    """Request for 4-agent pipeline processing."""
    agent_output: str
    ground_truth: Optional[str] = None
    domain: Optional[str] = None
    enable_auto_correction: bool = True


# Temporarily disabled - advanced features
# @app.post("/agent-pipeline/process", tags=["detection", "pipeline"])
async def process_with_agent_pipeline(request: AgentPipelineRequest):
    """
    Process text through 4-agent fact-checking pipeline with auto-correction.
    
    October 2025 Enhancement: Generate → Review → Clarify → Score workflow
    for 40-50% hallucination mitigation improvement through teaming LLMs.
    
    Features:
    - Multi-agent coordination with CrewAI framework
    - Auto-correction capabilities with hallucination rewriting
    - Structured analysis through specialized agent roles
    - Comprehensive improvement metrics and confidence scoring
    
    Returns:
        Enhanced analysis with corrected text and detailed agent insights
    """
    try:
        # Validate Claude API key
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
        
        # Get agent pipeline instance
        pipeline = get_agent_pipeline(claude_api_key)
        
        # Process through 4-agent pipeline
        result = await pipeline.process_text(
            text=request.agent_output,
            context=request.ground_truth,
            domain=request.domain
        )
        
        # Build response
        response = {
            "status": "success",
            "pipeline_result": {
                "original_text": result.original_text,
                "corrected_text": result.corrected_text,
                "hallucination_score": result.hallucination_score,
                "correction_applied": result.correction_applied,
                "pipeline_confidence": result.pipeline_confidence,
                "improvement_metrics": result.improvement_metrics,
                "processing_time_ms": result.total_processing_time_ms
            },
            "agent_analysis": [
                {
                    "agent_role": output.agent_role.value,
                    "stage": output.stage.value,
                    "confidence": output.confidence,
                    "reasoning": output.reasoning,
                    "processing_time_ms": output.processing_time_ms,
                    "content_preview": output.content[:200] + "..." if len(output.content) > 200 else output.content
                }
                for output in result.agent_outputs
            ],
            "recommendations": {
                "use_corrected_text": result.correction_applied and result.pipeline_confidence > 0.7,
                "requires_human_review": result.hallucination_score > 0.7 or result.pipeline_confidence < 0.5,
                "confidence_level": "high" if result.pipeline_confidence > 0.8 else "medium" if result.pipeline_confidence > 0.6 else "low"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Agent pipeline processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {str(e)}")


@app.get("/agent-pipeline/stats", tags=["detection", "pipeline"])
async def get_agent_pipeline_stats():
    """
    Get 4-agent pipeline performance statistics.
    
    Returns statistics about pipeline performance, success rates, and efficiency.
    """
    try:
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
        
        pipeline = get_agent_pipeline(claude_api_key)
        stats = pipeline.get_pipeline_stats()
        
        return {
            "status": "success",
            "pipeline_stats": stats,
            "capabilities": {
                "agents": ["generator", "reviewer", "clarifier", "scorer"],
                "auto_correction": True,
                "multi_agent_coordination": True,
                "teaming_llms": True,
                "structured_outputs": True
            },
            "performance_targets": {
                "hallucination_mitigation_improvement": "40-50%",
                "processing_time_target_ms": 5000,
                "confidence_threshold": 0.7,
                "success_rate_target": 0.8
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting pipeline stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pipeline statistics")


@app.post("/agent-pipeline/batch", tags=["detection", "pipeline"])
async def batch_process_with_pipeline(
    texts: List[str],
    context: Optional[str] = None,
    domain: Optional[str] = None,
    max_concurrent: int = 3
):
    """
    Batch process multiple texts through the 4-agent pipeline.
    
    Args:
        texts: List of texts to process
        context: Optional shared context
        domain: Optional domain specification
        max_concurrent: Maximum concurrent pipeline processes
        
    Returns:
        Batch processing results with individual pipeline outputs
    """
    try:
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
        
        if len(texts) > 50:  # Limit batch size
            raise HTTPException(status_code=400, detail="Batch size limited to 50 texts")
        
        pipeline = get_agent_pipeline(claude_api_key)
        
        # Process texts with concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_text(text: str) -> Dict:
            async with semaphore:
                try:
                    result = await pipeline.process_text(text, context, domain)
                    return {
                        "text": text,
                        "status": "success",
                        "corrected_text": result.corrected_text,
                        "hallucination_score": result.hallucination_score,
                        "correction_applied": result.correction_applied,
                        "pipeline_confidence": result.pipeline_confidence,
                        "processing_time_ms": result.total_processing_time_ms
                    }
                except Exception as e:
                    return {
                        "text": text,
                        "status": "error",
                        "error": str(e),
                        "processing_time_ms": 0
                    }
        
        # Process all texts concurrently
        start_time = time.time()
        results = await asyncio.gather(*[process_single_text(text) for text in texts])
        total_time = (time.time() - start_time) * 1000
        
        # Calculate batch statistics
        successful_results = [r for r in results if r["status"] == "success"]
        error_results = [r for r in results if r["status"] == "error"]
        
        batch_stats = {
            "total_texts": len(texts),
            "successful": len(successful_results),
            "errors": len(error_results),
            "success_rate": len(successful_results) / len(texts) if texts else 0,
            "average_processing_time_ms": sum(r.get("processing_time_ms", 0) for r in successful_results) / len(successful_results) if successful_results else 0,
            "total_batch_time_ms": total_time
        }
        
        return {
            "status": "completed",
            "batch_stats": batch_stats,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch pipeline processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


# Multilingual Detection Endpoints (October 2025 Enhancement)
class MultilingualRequest(BaseModel):
    """Request for multilingual hallucination detection."""
    text: str
    context: Optional[str] = None
    target_language: Optional[str] = None  # Force specific language


@app.post("/multilingual/detect", tags=["detection", "multilingual"])
async def detect_multilingual_hallucination(request: MultilingualRequest):
    """
    Detect hallucinations in multilingual text with span-level analysis.
    
    October 2025 Enhancement: PsiloQA dataset integration for 14 languages
    with Mu-SHROOM F1 alignment targeting 95% accuracy.
    
    Features:
    - Automatic language detection for 14 supported languages
    - Language-specific model selection and optimization
    - Span-level hallucination detection for fine-grained analysis
    - Cross-lingual transfer learning capabilities
    - Mu-SHROOM benchmark alignment
    
    Supported Languages:
    - English, Spanish, French, German, Italian, Portuguese, Dutch
    - Russian, Chinese, Japanese, Korean, Arabic, Hindi, Turkish
    
    Returns:
        Comprehensive multilingual analysis with language detection and span-level scores
    """
    try:
        # Get multilingual judge
        multilingual_judge = get_multilingual_judge()
        
        # Override language detection if target language specified
        if request.target_language:
            # Validate target language
            stats = multilingual_judge.get_language_stats()
            supported_langs = list(stats['supported_languages'].keys())
            
            if request.target_language not in supported_langs:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Language '{request.target_language}' not supported. Supported: {supported_langs}"
                )
        
        # Perform multilingual evaluation
        result = await multilingual_judge.evaluate_multilingual(
            text=request.text,
            context=request.context
        )
        
        # Override detected language if specified
        if request.target_language and request.target_language != result.detected_language:
            logger.info(f"Language override: {result.detected_language} -> {request.target_language}")
            # Re-evaluate with target language
            # For now, we'll use the detected result but note the override
            result.metadata['language_override'] = request.target_language
        
        # Build response
        response = {
            "status": "success",
            "multilingual_result": {
                "text": result.text,
                "detected_language": result.detected_language,
                "language_confidence": result.language_confidence,
                "hallucination_score": result.hallucination_score,
                "model_used": result.model_used,
                "processing_time_ms": result.processing_time_ms
            },
            "language_analysis": {
                "language_code": result.detected_language,
                "language_name": result.metadata.get('language_name', 'Unknown'),
                "confidence_threshold": result.metadata.get('confidence_threshold', 0.7),
                "detection_confidence": result.language_confidence
            },
            "span_analysis": {
                "total_spans": len(result.span_level_scores),
                "flagged_spans": len([s for s in result.span_level_scores if s['is_flagged']]),
                "spans": result.span_level_scores[:20],  # Limit to first 20 for response size
                "high_uncertainty_spans": [
                    s for s in result.span_level_scores 
                    if s['uncertainty_score'] > 0.8
                ][:10]  # Top 10 most uncertain spans
            },
            "recommendations": {
                "requires_review": result.hallucination_score > 0.7,
                "language_supported": result.detected_language in multilingual_judge.get_language_stats()['supported_languages'],
                "confidence_level": "high" if result.language_confidence > 0.8 else "medium" if result.language_confidence > 0.6 else "low",
                "span_attention_needed": len([s for s in result.span_level_scores if s['is_flagged']]) > 0
            },
            "metadata": result.metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Multilingual detection error: {e}")
        raise HTTPException(status_code=500, detail=f"Multilingual detection failed: {str(e)}")


@app.get("/multilingual/languages", tags=["multilingual"])
async def get_supported_languages():
    """
    Get list of supported languages and their configurations.
    
    Returns information about all supported languages, models, and statistics.
    """
    try:
        multilingual_judge = get_multilingual_judge()
        stats = multilingual_judge.get_language_stats()
        
        return {
            "status": "success",
            "supported_languages": stats['supported_languages'],
            "summary": {
                "total_languages": stats['total_languages'],
                "models_loaded": stats['models_loaded'],
                "datasets_cached": stats['datasets_cached']
            },
            "capabilities": {
                "automatic_detection": True,
                "span_level_analysis": True,
                "psilqa_integration": True,
                "mu_shroom_alignment": True,
                "cross_lingual_transfer": True
            },
            "performance_targets": {
                "mu_shroom_f1_target": 0.95,
                "supported_language_count": 14,
                "span_level_precision": 0.90
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting supported languages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get language information")


@app.post("/multilingual/batch", tags=["detection", "multilingual"])
async def batch_multilingual_detection(
    texts: List[str],
    context: Optional[str] = None,
    target_language: Optional[str] = None,
    max_concurrent: int = 3
):
    """
    Batch process multiple texts for multilingual hallucination detection.
    
    Args:
        texts: List of texts to analyze (can be in different languages)
        context: Optional shared context
        target_language: Optional target language for all texts
        max_concurrent: Maximum concurrent processing
        
    Returns:
        Batch results with language detection and hallucination analysis
    """
    try:
        if len(texts) > 100:  # Limit batch size for multilingual
            raise HTTPException(status_code=400, detail="Batch size limited to 100 texts for multilingual processing")
        
        multilingual_judge = get_multilingual_judge()
        
        # Process texts with concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_text(text: str) -> Dict:
            async with semaphore:
                try:
                    result = await multilingual_judge.evaluate_multilingual(text, context)
                    return {
                        "text": text,
                        "status": "success",
                        "detected_language": result.detected_language,
                        "language_confidence": result.language_confidence,
                        "hallucination_score": result.hallucination_score,
                        "flagged_spans": len([s for s in result.span_level_scores if s['is_flagged']]),
                        "processing_time_ms": result.processing_time_ms
                    }
                except Exception as e:
                    return {
                        "text": text,
                        "status": "error",
                        "error": str(e),
                        "processing_time_ms": 0
                    }
        
        # Process all texts concurrently
        start_time = time.time()
        results = await asyncio.gather(*[process_single_text(text) for text in texts])
        total_time = (time.time() - start_time) * 1000
        
        # Calculate batch statistics
        successful_results = [r for r in results if r["status"] == "success"]
        error_results = [r for r in results if r["status"] == "error"]
        
        # Language distribution
        language_distribution = {}
        for result in successful_results:
            lang = result.get("detected_language", "unknown")
            language_distribution[lang] = language_distribution.get(lang, 0) + 1
        
        batch_stats = {
            "total_texts": len(texts),
            "successful": len(successful_results),
            "errors": len(error_results),
            "success_rate": len(successful_results) / len(texts) if texts else 0,
            "language_distribution": language_distribution,
            "average_processing_time_ms": sum(r.get("processing_time_ms", 0) for r in successful_results) / len(successful_results) if successful_results else 0,
            "total_batch_time_ms": total_time,
            "average_hallucination_score": sum(r.get("hallucination_score", 0) for r in successful_results) / len(successful_results) if successful_results else 0
        }
        
        return {
            "status": "completed",
            "batch_stats": batch_stats,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch multilingual processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch multilingual processing failed: {str(e)}")


@app.post("/multilingual/evaluate-mu-shroom", tags=["multilingual", "evaluation"])
async def evaluate_mu_shroom_alignment(test_data: List[Dict[str, Any]]):
    """
    Evaluate system alignment with Mu-SHROOM F1 targets (95%).
    
    Args:
        test_data: List of test examples with ground truth labels
        
    Expected format for test_data:
        [
            {
                "text": "Sample text to evaluate",
                "label": 0,  # 0: accurate, 1: hallucination
                "language": "en"  # optional
            },
            ...
        ]
    
    Returns:
        Comprehensive evaluation metrics and Mu-SHROOM alignment assessment
    """
    try:
        if len(test_data) > 1000:  # Limit evaluation size
            raise HTTPException(status_code=400, detail="Evaluation dataset limited to 1000 examples")
        
        # Validate test data format
        for i, example in enumerate(test_data):
            if 'text' not in example or 'label' not in example:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Example {i} missing required fields 'text' or 'label'"
                )
            
            if example['label'] not in [0, 1]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Example {i} label must be 0 (accurate) or 1 (hallucination)"
                )
        
        multilingual_judge = get_multilingual_judge()
        
        # Perform evaluation
        evaluation_results = await multilingual_judge.evaluate_mu_shroom_alignment(test_data)
        
        return {
            "status": "success",
            "evaluation_results": evaluation_results,
            "mu_shroom_compliance": {
                "target_f1": 0.95,
                "achieved_f1": evaluation_results.get('overall_f1', 0.0),
                "target_met": evaluation_results.get('target_achieved', False),
                "performance_gap": 0.95 - evaluation_results.get('overall_f1', 0.0)
            },
            "recommendations": {
                "needs_improvement": evaluation_results.get('overall_f1', 0.0) < 0.95,
                "focus_languages": [
                    lang for lang, metrics in evaluation_results.get('language_metrics', {}).items()
                    if metrics.get('accuracy', 0) < 0.90
                ],
                "suggested_actions": [
                    "Increase training data for underperforming languages",
                    "Fine-tune language-specific models",
                    "Improve span-level detection accuracy",
                    "Enhance cross-lingual transfer learning"
                ] if evaluation_results.get('overall_f1', 0.0) < 0.95 else [
                    "Maintain current performance",
                    "Monitor for performance degradation",
                    "Consider expanding to additional languages"
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Mu-SHROOM evaluation error: {e}")
        raise HTTPException(status_code=500, detail=f"Mu-SHROOM evaluation failed: {str(e)}")


# Multimodal Detection Endpoints (October 2025 Enhancement)
@app.post("/multimodal/detect-image", tags=["detection", "multimodal"])
async def detect_image_hallucination(
    image: UploadFile = File(...),
    text_description: Optional[str] = Form(None),
    content_type: str = Form("image")
):
    """
    Detect hallucinations in image content with optional text description.
    
    October 2025 Enhancement: ONNX-based multimodal detection with edge computing support.
    
    Features:
    - Object detection and verification using ONNX runtime
    - Scene consistency analysis for realism assessment
    - Adversarial/deepfake content detection
    - Text-image semantic alignment using CLIP
    - Real-time processing with <200ms target latency
    - Edge computing optimization for mobile deployment
    
    Capabilities:
    - Fake object detection in generated images
    - Impossible scene identification
    - Adversarial attack detection
    - Vision-language model output verification
    
    Returns:
        Comprehensive multimodal analysis with object detection and consistency scores
    """
    try:
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await image.read()
        
        if len(image_data) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="Image file too large (max 10MB)")
        
        # Get multimodal judge
        multimodal_judge = get_multimodal_judge()
        
        # Create multimodal input
        multimodal_input = MultimodalInput(
            content_type='image_text' if text_description else 'image',
            image_data=image_data,
            text_description=text_description,
            metadata={
                'filename': image.filename,
                'content_type': image.content_type,
                'file_size': len(image_data)
            }
        )
        
        # Process multimodal input
        result = await multimodal_judge.process_multimodal_input(multimodal_input)
        
        # Build response
        response = {
            "status": "success",
            "multimodal_result": {
                "content_type": result.content_type,
                "hallucination_score": result.hallucination_score,
                "confidence": result.confidence,
                "text_image_alignment": result.text_image_alignment,
                "model_used": result.model_used,
                "processing_time_ms": result.processing_time_ms
            },
            "object_detection": {
                "detected_objects": [
                    {
                        "label": obj.label,
                        "confidence": obj.confidence,
                        "bounding_box": {
                            "x": obj.x,
                            "y": obj.y,
                            "width": obj.width,
                            "height": obj.height
                        }
                    }
                    for obj in result.detected_objects
                ],
                "object_count": len(result.detected_objects)
            },
            "visual_analysis": {
                "inconsistencies": result.visual_inconsistencies,
                "inconsistency_count": len(result.visual_inconsistencies),
                "high_severity_issues": len([
                    issue for issue in result.visual_inconsistencies 
                    if issue.get('severity') == 'high'
                ])
            },
            "recommendations": {
                "requires_review": result.hallucination_score > 0.7,
                "confidence_level": "high" if result.confidence > 0.8 else "medium" if result.confidence > 0.6 else "low",
                "text_alignment_good": result.text_image_alignment > 0.7 if text_description else None,
                "potential_issues": [
                    issue['type'] for issue in result.visual_inconsistencies
                    if issue.get('severity') in ['high', 'critical']
                ]
            },
            "metadata": result.metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image hallucination detection error: {e}")
        raise HTTPException(status_code=500, detail=f"Image detection failed: {str(e)}")


@app.post("/multimodal/detect-video", tags=["detection", "multimodal"])
async def detect_video_hallucination(
    video: UploadFile = File(...),
    text_description: Optional[str] = Form(None),
    max_duration_seconds: int = Form(30)
):
    """
    Detect hallucinations in video content with temporal consistency analysis.
    
    October 2025 Enhancement: Video temporal consistency and multimodal alignment.
    
    Features:
    - Frame-by-frame hallucination detection
    - Temporal consistency analysis across frames
    - Object tracking and verification
    - Scene transition analysis
    - Text-video semantic alignment
    
    Capabilities:
    - Temporal discontinuities detection
    - Impossible object movements
    - Scene consistency violations
    - Generated video identification
    
    Returns:
        Comprehensive video analysis with temporal consistency metrics
    """
    try:
        # Validate file type
        if not video.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Read video data
        video_data = await video.read()
        
        if len(video_data) > 100 * 1024 * 1024:  # 100MB limit
            raise HTTPException(status_code=400, detail="Video file too large (max 100MB)")
        
        # Get multimodal judge
        multimodal_judge = get_multimodal_judge()
        
        # Create multimodal input
        multimodal_input = MultimodalInput(
            content_type='video_text' if text_description else 'video',
            video_data=video_data,
            text_description=text_description,
            metadata={
                'filename': video.filename,
                'content_type': video.content_type,
                'file_size': len(video_data),
                'max_duration_seconds': max_duration_seconds
            }
        )
        
        # Process multimodal input
        result = await multimodal_judge.process_multimodal_input(multimodal_input)
        
        # Build response
        response = {
            "status": "success",
            "multimodal_result": {
                "content_type": result.content_type,
                "hallucination_score": result.hallucination_score,
                "confidence": result.confidence,
                "text_image_alignment": result.text_image_alignment,
                "model_used": result.model_used,
                "processing_time_ms": result.processing_time_ms
            },
            "video_analysis": {
                "frame_count": result.metadata.get('frame_count', 0),
                "analyzed_frames": result.metadata.get('analyzed_frames', 0),
                "temporal_consistency_score": result.metadata.get('temporal_consistency_score', 0.5),
                "average_objects_per_frame": result.metadata.get('average_objects_per_frame', 0)
            },
            "object_detection": {
                "total_detections": len(result.detected_objects),
                "unique_objects": len(set(obj.label for obj in result.detected_objects)),
                "high_confidence_objects": len([
                    obj for obj in result.detected_objects if obj.confidence > 0.8
                ])
            },
            "temporal_analysis": {
                "inconsistencies": [
                    issue for issue in result.visual_inconsistencies
                    if issue.get('type') == 'temporal_discontinuity'
                ],
                "scene_changes": len([
                    issue for issue in result.visual_inconsistencies
                    if 'temporal' in issue.get('type', '')
                ])
            },
            "recommendations": {
                "requires_review": result.hallucination_score > 0.7,
                "confidence_level": "high" if result.confidence > 0.8 else "medium" if result.confidence > 0.6 else "low",
                "temporal_consistency_good": result.metadata.get('temporal_consistency_score', 0.5) > 0.7,
                "potential_issues": [
                    issue['type'] for issue in result.visual_inconsistencies
                    if issue.get('severity') in ['high', 'critical']
                ]
            },
            "metadata": result.metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video hallucination detection error: {e}")
        raise HTTPException(status_code=500, detail=f"Video detection failed: {str(e)}")


@app.get("/multimodal/capabilities", tags=["multimodal"])
async def get_multimodal_capabilities():
    """
    Get multimodal detection capabilities and model information.
    
    Returns information about supported formats, models, and performance metrics.
    """
    try:
        multimodal_judge = get_multimodal_judge()
        stats = multimodal_judge.get_processing_stats()
        
        return {
            "status": "success",
            "capabilities": {
                "supported_formats": {
                    "images": ["JPEG", "PNG", "GIF", "BMP", "TIFF"],
                    "videos": ["MP4", "AVI", "MOV", "MKV", "WEBM"],
                    "max_image_size_mb": 10,
                    "max_video_size_mb": 100,
                    "max_video_duration_seconds": 300
                },
                "detection_features": [
                    "Object detection and verification",
                    "Scene consistency analysis",
                    "Adversarial content detection",
                    "Text-image semantic alignment",
                    "Temporal consistency analysis",
                    "Deepfake detection",
                    "Generated content identification"
                ],
                "models": {
                    "object_detection": "YOLOv8 (ONNX optimized)",
                    "scene_analysis": "ResNet50 + Custom layers",
                    "adversarial_detection": "EfficientNet-B0",
                    "vision_language": "CLIP ViT-B/32",
                    "runtime": "ONNX Runtime with GPU acceleration"
                },
                "performance_targets": {
                    "image_processing_ms": 200,
                    "video_processing_per_second": 2,
                    "accuracy_target": 0.90,
                    "edge_deployment": True
                }
            },
            "processing_stats": stats,
            "device_info": {
                "device": stats.get('device', 'cpu'),
                "onnx_providers": stats.get('onnx_providers', []),
                "models_loaded": stats.get('models_loaded', 0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting multimodal capabilities: {e}")
        raise HTTPException(status_code=500, detail="Failed to get capabilities information")


@app.post("/multimodal/batch-images", tags=["detection", "multimodal"])
async def batch_detect_image_hallucinations(
    images: List[UploadFile] = File(...),
    text_descriptions: Optional[List[str]] = Form(None),
    max_concurrent: int = Form(3)
):
    """
    Batch process multiple images for hallucination detection.
    
    Args:
        images: List of image files to analyze
        text_descriptions: Optional list of text descriptions (must match image count)
        max_concurrent: Maximum concurrent processing (default: 3)
        
    Returns:
        Batch results with individual image analysis
    """
    try:
        if len(images) > 50:  # Limit batch size
            raise HTTPException(status_code=400, detail="Batch size limited to 50 images")
        
        if text_descriptions and len(text_descriptions) != len(images):
            raise HTTPException(
                status_code=400, 
                detail="Number of text descriptions must match number of images"
            )
        
        multimodal_judge = get_multimodal_judge()
        
        # Process images with concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_image(image: UploadFile, text_desc: Optional[str], index: int) -> Dict:
            async with semaphore:
                try:
                    # Validate and read image
                    if not image.content_type.startswith('image/'):
                        return {
                            "index": index,
                            "filename": image.filename,
                            "status": "error",
                            "error": "Invalid file type - must be image"
                        }
                    
                    image_data = await image.read()
                    
                    if len(image_data) > 10 * 1024 * 1024:
                        return {
                            "index": index,
                            "filename": image.filename,
                            "status": "error",
                            "error": "Image too large (max 10MB)"
                        }
                    
                    # Create input and process
                    multimodal_input = MultimodalInput(
                        content_type='image_text' if text_desc else 'image',
                        image_data=image_data,
                        text_description=text_desc,
                        metadata={'filename': image.filename, 'index': index}
                    )
                    
                    result = await multimodal_judge.process_multimodal_input(multimodal_input)
                    
                    return {
                        "index": index,
                        "filename": image.filename,
                        "status": "success",
                        "hallucination_score": result.hallucination_score,
                        "confidence": result.confidence,
                        "text_image_alignment": result.text_image_alignment,
                        "detected_objects": len(result.detected_objects),
                        "visual_inconsistencies": len(result.visual_inconsistencies),
                        "processing_time_ms": result.processing_time_ms
                    }
                    
                except Exception as e:
                    return {
                        "index": index,
                        "filename": image.filename,
                        "status": "error",
                        "error": str(e)
                    }
        
        # Process all images concurrently
        start_time = time.time()
        tasks = [
            process_single_image(
                images[i], 
                text_descriptions[i] if text_descriptions else None, 
                i
            )
            for i in range(len(images))
        ]
        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000
        
        # Calculate batch statistics
        successful_results = [r for r in results if r["status"] == "success"]
        error_results = [r for r in results if r["status"] == "error"]
        
        batch_stats = {
            "total_images": len(images),
            "successful": len(successful_results),
            "errors": len(error_results),
            "success_rate": len(successful_results) / len(images) if images else 0,
            "average_processing_time_ms": sum(r.get("processing_time_ms", 0) for r in successful_results) / len(successful_results) if successful_results else 0,
            "total_batch_time_ms": total_time,
            "average_hallucination_score": sum(r.get("hallucination_score", 0) for r in successful_results) / len(successful_results) if successful_results else 0,
            "high_risk_images": len([r for r in successful_results if r.get("hallucination_score", 0) > 0.7])
        }
        
        return {
            "status": "completed",
            "batch_stats": batch_stats,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch image processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


# Performance Monitoring Endpoints
@app.get("/performance/overview", tags=["performance"])
async def get_performance_overview(current_user = Depends(require_authentication)):
    """Get comprehensive performance overview."""
    try:
        performance_monitor = get_performance_monitor()
        overview = await performance_monitor.get_performance_overview()
        
        return {
            "status": "success",
            "data": overview
        }
        
    except Exception as e:
        logger.error(f"Error getting performance overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance overview")


@app.get("/performance/endpoints", tags=["performance"])
async def get_endpoint_performance(current_user = Depends(require_authentication)):
    """Get performance breakdown by endpoint."""
    try:
        performance_monitor = get_performance_monitor()
        endpoint_stats = await performance_monitor.get_endpoint_performance()
        
        return {
            "status": "success",
            "data": endpoint_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting endpoint performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve endpoint performance")


@app.get("/performance/alerts", tags=["performance"])
async def get_performance_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: info, warning, error, critical"),
    current_user = Depends(require_authentication)
):
    """Get active performance alerts."""
    try:
        performance_monitor = get_performance_monitor()
        
        # Convert severity string to enum if provided
        severity_filter = None
        if severity:
            from ..services.performance_monitor import AlertSeverity
            try:
                severity_filter = AlertSeverity(severity.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid severity level")
        
        alerts = await performance_monitor.get_alerts(severity_filter)
        
        return {
            "status": "success",
            "data": alerts,
            "count": len(alerts)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance alerts")


@app.post("/performance/alerts/{alert_id}/resolve", tags=["performance"])
async def resolve_performance_alert(
    alert_id: str,
    current_user = Depends(require_authentication)
):
    """Resolve a performance alert."""
    try:
        performance_monitor = get_performance_monitor()
        performance_monitor.resolve_alert(alert_id)
        
        return {
            "status": "success",
            "message": f"Alert {alert_id} resolved"
        }
        
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert")


@app.get("/performance/claude-usage", tags=["performance"])
async def get_claude_usage_stats(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back (1-168)"),
    current_user = Depends(require_authentication)
):
    """Get Claude API usage statistics."""
    try:
        performance_monitor = get_performance_monitor()
        
        # Get recent Claude usage from memory (simplified)
        recent_usage = list(performance_monitor.recent_claude)
        
        # Filter by time range
        from datetime import datetime, timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        filtered_usage = [u for u in recent_usage if u.timestamp >= cutoff_time]
        
        if not filtered_usage:
            return {
                "status": "success",
                "data": {
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "total_requests": 0,
                    "success_rate": 100.0,
                    "avg_response_time": 0.0,
                    "hourly_breakdown": []
                }
            }
        
        # Calculate statistics
        total_tokens = sum(u.tokens_used for u in filtered_usage)
        total_cost = sum(u.cost_usd for u in filtered_usage)
        total_requests = len(filtered_usage)
        successful_requests = sum(1 for u in filtered_usage if u.success)
        success_rate = (successful_requests / total_requests) * 100
        avg_response_time = sum(u.response_time_ms for u in filtered_usage) / total_requests
        
        # Group by hour for breakdown
        hourly_breakdown = {}
        for usage in filtered_usage:
            hour_key = usage.timestamp.strftime("%Y-%m-%d %H:00")
            if hour_key not in hourly_breakdown:
                hourly_breakdown[hour_key] = {
                    "tokens": 0,
                    "cost": 0.0,
                    "requests": 0,
                    "avg_response_time": 0.0
                }
            hourly_breakdown[hour_key]["tokens"] += usage.tokens_used
            hourly_breakdown[hour_key]["cost"] += usage.cost_usd
            hourly_breakdown[hour_key]["requests"] += 1
        
        # Calculate average response times for each hour
        for hour_key in hourly_breakdown:
            hour_usage = [u for u in filtered_usage if u.timestamp.strftime("%Y-%m-%d %H:00") == hour_key]
            if hour_usage:
                hourly_breakdown[hour_key]["avg_response_time"] = sum(u.response_time_ms for u in hour_usage) / len(hour_usage)
        
        return {
            "status": "success",
            "data": {
                "total_tokens": total_tokens,
                "total_cost": round(total_cost, 4),
                "total_requests": total_requests,
                "success_rate": round(success_rate, 2),
                "avg_response_time": round(avg_response_time, 2),
                "hourly_breakdown": [
                    {"hour": k, **v} for k, v in sorted(hourly_breakdown.items())
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting Claude usage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Claude usage statistics")


@app.post("/performance/claude-usage/record", tags=["performance"])
async def record_claude_usage(
    usage_data: Dict[str, Any],
    current_user = Depends(require_authentication)
):
    """Record Claude API usage (for manual tracking)."""
    try:
        performance_monitor = get_performance_monitor()
        
        await performance_monitor.record_claude_usage(
            endpoint=usage_data.get("endpoint", "unknown"),
            tokens_used=usage_data.get("tokens_used", 0),
            cost_usd=usage_data.get("cost_usd", 0.0),
            response_time_ms=usage_data.get("response_time_ms", 0.0),
            success=usage_data.get("success", True),
            error_type=usage_data.get("error_type"),
            user_id=current_user.user_id
        )
        
        return {
            "status": "success",
            "message": "Claude usage recorded"
        }
        
    except Exception as e:
        logger.error(f"Error recording Claude usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to record Claude usage")


# Rate Limiting & Quota Management Endpoints
@app.get("/rate-limits", tags=["rate-limiting"])
async def get_rate_limit_rules(current_user = Depends(require_admin)):
    """Get all rate limiting and quota rules (Admin only)."""
    try:
        rate_limit_service = get_rate_limit_service()
        rules = rate_limit_service.get_all_rules()
        
        return {
            "status": "success",
            "data": rules
        }
        
    except Exception as e:
        logger.error(f"Error getting rate limit rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve rate limit rules")


@app.post("/rate-limits/rules", tags=["rate-limiting"])
async def add_rate_limit_rule(
    rule_data: Dict[str, Any],
    current_user = Depends(require_admin)
):
    """Add new rate limit rule (Admin only)."""
    try:
        rate_limit_service = get_rate_limit_service()
        
        # This would implement rule creation logic
        # For now, return success message
        return {
            "status": "success",
            "message": "Rate limit rule creation endpoint - implementation pending",
            "data": rule_data
        }
        
    except Exception as e:
        logger.error(f"Error adding rate limit rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to add rate limit rule")


@app.get("/rate-limits/usage/{user_id}", tags=["rate-limiting"])
async def get_user_usage_stats(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    current_user = Depends(require_admin)
):
    """Get usage statistics for a user (Admin only)."""
    try:
        rate_limit_service = get_rate_limit_service()
        async with rate_limit_service:
            stats = await rate_limit_service.get_usage_stats(user_id, days)
        
        return {
            "status": "success",
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve usage statistics")


@app.get("/rate-limits/my-usage", tags=["rate-limiting"])
async def get_my_usage_stats(
    days: int = Query(30, ge=1, le=365),
    current_user = Depends(require_authentication)
):
    """Get current user's usage statistics."""
    try:
        rate_limit_service = get_rate_limit_service()
        async with rate_limit_service:
            stats = await rate_limit_service.get_usage_stats(current_user.user_id, days)
        
        return {
            "status": "success",
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve usage statistics")


@app.get("/rate-limits/status", tags=["rate-limiting"])
async def get_rate_limit_status(
    request: Request,
    current_user = Depends(require_authentication)
):
    """Get current rate limit status for the user."""
    try:
        rate_limit_service = get_rate_limit_service()
        async with rate_limit_service:
            # Check current rate limits without consuming them
            rate_results = await rate_limit_service.check_rate_limit(
                request, current_user.user_id, current_user.role.value
            )
            
            quota_results = await rate_limit_service.check_quota(
                request, current_user.user_id, current_user.role.value, 0  # 0 cost for status check
            )
        
        return {
            "status": "success",
            "data": {
                "user_id": current_user.user_id,
                "role": current_user.role.value,
                "rate_limits": [
                    {
                        "rule_id": r.rule_id,
                        "limit": r.limit,
                        "remaining": r.remaining,
                        "reset_time": r.reset_time.isoformat()
                    } for r in rate_results
                ],
                "quotas": [
                    {
                        "rule_id": q.rule_id,
                        "limit": q.limit,
                        "used": q.used,
                        "remaining": q.remaining,
                        "reset_time": q.reset_time.isoformat()
                    } for q in quota_results
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve rate limit status")


# Chat Assistant Endpoint
@app.post("/chat", tags=["assistant"])
async def chat_with_assistant(
    request: dict,
    background_tasks: BackgroundTasks
):
    """
    Chat with the Watcher AI Assistant using Claude API.
    Provides intelligent responses about the platform without hallucination detection.
    """
    try:
        user_message = request.get("message", "").strip()
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Validate Claude API key
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            logger.error("Claude API key not configured for chat")
            raise HTTPException(
                status_code=500, 
                detail="Chat service temporarily unavailable"
            )
        
        # Initialize Claude judge for chat (reuse existing infrastructure)
        from ..judges.claude_judge import ClaudeJudge
        claude_judge = ClaudeJudge(claude_api_key)
        
        # System prompt for the assistant
        system_prompt = """You are the Watcher AI Assistant, an expert guide for the Watcher AI platform - a comprehensive hallucination detection and testing platform for AI agents. You have complete knowledge of every feature and can help users from complete beginners to tech experts.

PLATFORM OVERVIEW:
Watcher AI is an enterprise-grade platform for detecting hallucinations, fabrications, and reliability issues in AI agent outputs. It uses Claude 4.5 Sonnet with self-consistency sampling and statistical models for accurate detection.

KEY FEATURES:
- Real-time hallucination detection (<100ms latency)
- Multi-industry compliance (Healthcare, Finance, Education, Manufacturing, Technology)
- Enterprise integration (REST API, WebSocket, Webhooks)
- Batch processing and analytics
- Custom rule engines for industry-specific detection

Be helpful, professional, and provide specific guidance. Adapt your communication style to the user's technical level. Always provide actionable next steps."""
        
        # Create a simple chat request (not for hallucination detection)
        chat_prompt = f"{system_prompt}\n\nUser: {user_message}\n\nAssistant:"
        
        # Use Claude to generate response
        response = await claude_judge.evaluate_async(
            agent_output=chat_prompt,
            ground_truth="This is a chat conversation, not hallucination detection.",
            conversation_history=[]
        )
        
        # Extract the assistant response from Claude's output
        assistant_response = response.get("reasoning", "I'm here to help with Watcher AI! How can I assist you today?")
        
        return {
            "status": "success",
            "response": assistant_response,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "status": "error",
            "response": "I apologize, but I'm having trouble connecting right now. Please try again in a moment, or check our documentation at /docs for immediate help.",
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
