import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import mlflow

from ..models.schemas import AgentTestRequest, HallucinationReport
from ..judges.ensemble_judge import EnsembleJudge

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
    logger.info("Starting AgentGuard API server")
    logger.info(f"Claude API Key: {'configured' if os.getenv('CLAUDE_API_KEY') else 'missing'}")
    yield
    # Shutdown
    logger.info("Shutting down AgentGuard API server")


# Initialize FastAPI application
app = FastAPI(
    title="AgentGuard",
    description="AI Agent Hallucination Detection Platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
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


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AgentGuard API",
        "version": "0.1.0",
        "status": "operational",
        "description": "AI Agent Hallucination Detection Platform",
        "endpoints": {
            "test_agent": "/test-agent",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health", tags=["monitoring"])
async def health_check():
    """
    Health check endpoint for monitoring.
    Returns API status and configuration details.
    """
    claude_api_configured = bool(os.getenv("CLAUDE_API_KEY"))
    
    return {
        "status": "healthy" if claude_api_configured else "degraded",
        "model": "claude-sonnet-4-5-20250929",
        "claude_api": "configured" if claude_api_configured else "not configured",
        "statistical_model": "distilbert-base-uncased",
        "ensemble_weights": {"claude": 0.6, "statistical": 0.4},
        "uncertainty_threshold": 0.3
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


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

