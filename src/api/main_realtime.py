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


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
