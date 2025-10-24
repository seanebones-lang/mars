"""
Simplified FastAPI main module for local development.
This version includes core functionality without complex dependencies.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from ..models.schemas import AgentTestRequest, HallucinationReport

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    logger.info("Starting AgentGuard API server (simplified version)")
    logger.info(f"Claude API Key: {'configured' if os.getenv('CLAUDE_API_KEY') else 'missing'}")
    yield
    # Shutdown
    logger.info("Shutting down AgentGuard API server")

# Initialize FastAPI application
app = FastAPI(
    title="AgentGuard",
    description="AI Agent Hallucination Detection Platform",
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
            "name": "monitoring",
            "description": "Health check and system status"
        },
        {
            "name": "authentication",
            "description": "User authentication and profile management"
        },
        {
            "name": "workstations",
            "description": "Workstation management and monitoring"
        },
        {
            "name": "analytics",
            "description": "Analytics and business intelligence"
        }
    ]
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoints
@app.get("/health", tags=["monitoring"])
async def health_check():
    """Comprehensive health check endpoint for production monitoring."""
    import time
    
    start_time = time.time()
    
    try:
        # Basic system health
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "services": {
                "api": "healthy",
                "database": "healthy",  # Simplified for demo
                "redis": "healthy"      # Simplified for demo
            },
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }
        
        return JSONResponse(content=health_data, status_code=200)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            },
            status_code=503
        )

@app.get("/ready", tags=["monitoring"])
async def readiness_check():
    """Readiness check for Kubernetes deployments."""
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}

@app.get("/live", tags=["monitoring"])
async def liveness_check():
    """Liveness check for Kubernetes deployments."""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}

@app.get("/", tags=["monitoring"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AgentGuard API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "timestamp": datetime.utcnow().isoformat()
    }

# Core detection endpoint
@app.post("/test-agent", response_model=HallucinationReport, tags=["detection"])
async def test_agent_output(request: AgentTestRequest):
    """
    Test agent output for hallucinations using simplified detection.
    """
    try:
        # Simplified detection logic for demo
        import random
        
        # Mock detection results
        risk_score = random.uniform(0.1, 0.9)
        confidence = random.uniform(0.7, 0.95)
        
        # Simple heuristics
        text_length = len(request.agent_output)
        if text_length < 50:
            risk_score *= 0.5  # Short texts are less risky
        elif text_length > 500:
            risk_score *= 1.2  # Long texts might have more issues
            
        # Check for common hallucination indicators
        suspicious_phrases = ["I'm certain", "definitely", "100% sure", "without a doubt"]
        if any(phrase in request.agent_output.lower() for phrase in suspicious_phrases):
            risk_score *= 1.3
            
        risk_score = min(risk_score, 1.0)  # Cap at 1.0
        
        report = HallucinationReport(
            hallucination_risk=risk_score,
            confidence=confidence,
            explanation=f"Simplified analysis: Risk score {risk_score:.2f} based on text patterns and length analysis.",
            statistical_score=risk_score * 0.8,
            claude_score=risk_score * 1.1,
            uncertainty=1.0 - confidence,
            requires_human_review=risk_score > 0.7,
            processing_time_ms=random.uniform(50, 150),
            metadata={
                "model": "simplified_demo",
                "text_length": text_length,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Agent test completed: risk={risk_score:.2f}, confidence={confidence:.2f}")
        return report
        
    except Exception as e:
        logger.error(f"Agent testing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

# Mock workstation endpoints
@app.get("/workstations", tags=["workstations"])
async def list_workstations(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List workstations with mock data."""
    mock_workstations = [
        {
            "id": f"ws_{i}",
            "name": f"Workstation-{i:03d}",
            "ip_address": f"192.168.1.{i+10}",
            "status": "online" if i % 3 != 0 else "offline",
            "last_seen": datetime.utcnow().isoformat(),
            "agent_count": random.randint(1, 5),
            "risk_score": random.uniform(0.1, 0.8)
        }
        for i in range(offset, min(offset + limit, 50))
    ]
    
    if status:
        mock_workstations = [ws for ws in mock_workstations if ws["status"] == status]
    
    return {
        "workstations": mock_workstations,
        "total": len(mock_workstations),
        "limit": limit,
        "offset": offset
    }

@app.get("/workstations/{workstation_id}", tags=["workstations"])
async def get_workstation_details(workstation_id: str):
    """Get detailed workstation information."""
    return {
        "id": workstation_id,
        "name": f"Workstation-{workstation_id}",
        "ip_address": "192.168.1.100",
        "status": "online",
        "last_seen": datetime.utcnow().isoformat(),
        "agents": [
            {
                "id": f"agent_{i}",
                "name": f"Agent {i}",
                "status": "active",
                "last_test": datetime.utcnow().isoformat(),
                "risk_score": random.uniform(0.1, 0.7)
            }
            for i in range(1, 4)
        ],
        "metrics": {
            "cpu_usage": random.uniform(20, 80),
            "memory_usage": random.uniform(30, 70),
            "disk_usage": random.uniform(40, 60)
        }
    }

# Mock analytics endpoints
@app.get("/analytics/insights", tags=["analytics"])
async def get_analytics_insights(days: int = Query(30, ge=1, le=365)):
    """Get analytics insights with mock data."""
    return {
        "period_days": days,
        "total_tests": random.randint(1000, 5000),
        "average_risk_score": random.uniform(0.2, 0.6),
        "high_risk_detections": random.randint(50, 200),
        "accuracy_rate": random.uniform(0.92, 0.98),
        "trends": {
            "risk_trend": "decreasing",
            "volume_trend": "increasing",
            "accuracy_trend": "stable"
        },
        "top_risk_categories": [
            {"category": "Medical Claims", "count": random.randint(10, 50)},
            {"category": "Financial Advice", "count": random.randint(5, 30)},
            {"category": "Technical Specs", "count": random.randint(8, 25)}
        ]
    }

# Mock authentication endpoints
@app.post("/auth/register", tags=["authentication"])
async def register_user(request: dict):
    """Mock user registration."""
    return {
        "message": "User registered successfully",
        "user_id": f"user_{random.randint(1000, 9999)}",
        "email": request.get("email", "demo@example.com")
    }

@app.post("/auth/login", tags=["authentication"])
async def login_user(request: dict):
    """Mock user login."""
    return {
        "access_token": f"mock_token_{random.randint(10000, 99999)}",
        "token_type": "bearer",
        "expires_in": 3600,
        "user": {
            "id": f"user_{random.randint(1000, 9999)}",
            "email": request.get("email", "demo@example.com"),
            "role": "pro"
        }
    }

@app.get("/auth/profile", tags=["authentication"])
async def get_user_profile():
    """Mock user profile."""
    return {
        "user": {
            "id": "user_demo",
            "email": "demo@example.com",
            "full_name": "Demo User",
            "role": "pro",
            "created_at": datetime.utcnow().isoformat(),
            "last_login": datetime.utcnow().isoformat()
        },
        "usage_stats": {
            "queries_this_month": random.randint(10, 100),
            "queries_total": random.randint(100, 1000),
            "agents_created": random.randint(1, 10),
            "api_calls_this_month": random.randint(50, 500)
        },
        "api_tokens": []
    }

# System metrics endpoint
@app.get("/metrics", tags=["monitoring"])
async def get_system_metrics():
    """Get system performance metrics."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "requests_per_minute": random.randint(50, 200),
        "average_response_time_ms": random.uniform(80, 120),
        "error_rate": random.uniform(0.01, 0.05),
        "active_connections": random.randint(10, 100),
        "system": {
            "cpu_usage": random.uniform(20, 60),
            "memory_usage": random.uniform(30, 70),
            "disk_usage": random.uniform(40, 80)
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run(
        "src.api.main_simple:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
