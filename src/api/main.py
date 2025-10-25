"""
Enhanced FastAPI main module with real-time monitoring capabilities.
This extends the existing API with WebSocket and real-time agent monitoring.
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException, WebSocket, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Try to import MLflow, but don't fail if it's not available
try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

from ..models.schemas import AgentTestRequest, HallucinationReport
from ..judges.ensemble_judge import EnsembleJudge
from .websocket import websocket_endpoint
from ..demo.realtime_monitor import get_realtime_monitor
from .mcp import router as mcp_router
from .streams import router as streams_router
from .parental_controls import router as parental_router
from .model_hosting import router as model_hosting_router
from .prompt_injection import router as prompt_injection_router
from .pii_protection import router as pii_protection_router
from .multi_model_consensus import router as multi_model_router
from .rag_security import router as rag_security_router
from .multimodal_detection import router as multimodal_router
from .bias_auditing import router as bias_router
from .red_teaming import router as redteam_router
from .compliance import router as compliance_router

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import production readiness utilities
from ..utils.environment_validator import validate_environment
from ..utils.health_monitor import get_health_status
from ..utils.sentry_integration import get_sentry_monitor
from ..utils.alert_manager import get_alert_manager

# Initialize monitoring (P0-Critical)
sentry_monitor = get_sentry_monitor()
alert_manager = get_alert_manager()

# Validate environment on startup (P0-Critical)
try:
    validate_environment()
    logger.info("Environment validation passed")
except Exception as e:
    logger.critical(f"Environment validation failed: {e}")
    alert_manager.alert_api_down("AgentGuard API", str(e))
    # In production, this should exit, but we'll allow degraded mode for now
    logger.warning("Continuing in degraded mode - some features may not work")

# Configure MLflow (optional)
if MLFLOW_AVAILABLE:
    try:
        mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "agentguard_prototype"))
        logger.info("MLflow experiment tracking enabled")
    except Exception as e:
        logger.warning(f"MLflow configuration failed: {e}")
else:
    logger.warning("MLflow not available - experiment tracking disabled")


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
            "name": "mcp_gateway",
            "description": "Model Control Plane (MCP) Gateway for real-time interventions"
        },
        {
            "name": "stream_handling",
            "description": "Dynamic data source handling for real-time streams"
        },
        {
            "name": "parental_controls",
            "description": "Family-friendly content filtering and age prediction"
        },
        {
            "name": "model_hosting",
            "description": "Model hosting platform for deploying and scaling AI models"
        },
        {
            "name": "prompt_injection",
            "description": "Real-time prompt injection detection and prevention"
        },
        {
            "name": "pii_protection",
            "description": "PII detection and redaction for HIPAA/GDPR/CCPA compliance"
        },
        {
            "name": "multi_model_consensus",
            "description": "Multi-model ensemble voting for improved accuracy"
        },
        {
            "name": "rag_security",
            "description": "RAG security for protecting retrieval-augmented generation systems"
        },
        {
            "name": "multimodal",
            "description": "Multimodal hallucination detection (image, video, audio)"
        },
        {
            "name": "bias-fairness",
            "description": "Bias detection and fairness auditing"
        },
        {
            "name": "red-teaming",
            "description": "Automated adversarial testing and vulnerability assessment"
        },
        {
            "name": "compliance",
            "description": "Regulatory compliance reporting (EU AI Act, NIST, OWASP, GDPR)"
        },
        {
            "name": "monitoring",
            "description": "Health check and system status"
        }
    ]
)

# Include routers
app.include_router(mcp_router)
app.include_router(streams_router)
app.include_router(parental_router)
app.include_router(model_hosting_router)
app.include_router(prompt_injection_router)
app.include_router(pii_protection_router)
app.include_router(multi_model_router)
app.include_router(rag_security_router)

# New routers (Phase 1 Upgrades - October 2025)
app.include_router(multimodal_router)
app.include_router(bias_router)
app.include_router(redteam_router)
app.include_router(compliance_router)

# CORS middleware for cross-origin requests
# Monorepo deployment on Render - frontend and backend on same domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Same origin deployment on Render
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "company": "Mothership AI",
        "product_url": "https://watcher.mothership-ai.com",
        "company_url": "https://mothership-ai.com",
        "contact": "info@mothership-ai.com",
        "version": "1.0.0",
        "status": "operational",
        "description": "Enterprise AI Safety Platform - Real-time Hallucination Detection & Prevention",
        "investment": {
            "slots_available": 50,
            "funding_goal": 500000,
            "deadline": "2025-11-30",
            "launch_date": "2026-01-01"
        },
        "endpoints": {
            "test_agent": "/test-agent",
            "websocket_monitor": "/ws/monitor",
            "start_monitoring": "/monitor/start",
            "stop_monitoring": "/monitor/stop",
            "health": "/health",
            "docs": "/docs",
            "api_documentation": "https://watcher-api.onrender.com/docs"
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
    Comprehensive health check endpoint for monitoring.
    Returns detailed status of all system components.
    
    P0-Critical: Production-grade health monitoring
    """
    try:
        # Get comprehensive health status
        health_status = get_health_status()
        
        # Add additional system info
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        monitor = get_realtime_monitor(claude_api_key) if claude_api_key else None
        
        health_status["system_info"] = {
            "model": "claude-sonnet-4-5-20250929",
            "statistical_model": "distilbert-base-uncased",
            "ensemble_weights": {"claude": 0.6, "statistical": 0.4},
            "uncertainty_threshold": 0.3,
            "realtime_monitoring": {
                "available": monitor is not None,
                "active": monitor.is_active() if monitor else False
            },
            "mlflow_available": MLFLOW_AVAILABLE
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
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
    if not MLFLOW_AVAILABLE:
        return {
            "message": "MLflow not available",
            "experiment_tracking": "disabled"
        }
    
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


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
